import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.git_clients import get_git_client
from pr_diff_walk.git_clients.token_resolver import resolve_token
from pr_diff_walk.integrations import (
    detect_integrations_from_files,
    get_integration,
)
from pr_diff_walk.schemas import (
    AnalysisResult,
    ChangedEntity,
    DependencyChain,
    Hop,
    RepositoryFiles,
)


class DiffChainService:
    def __init__(
        self,
        repo_name: str,
        pr_num: int,
        github_token: Optional[str] = None,
        local_repo_path: Optional[str] = None,
        max_depth: int = 8,
        integrations: Optional[List[str]] = None,
        provider: str = "github",
        gitlab_url: Optional[str] = None,
    ):
        self.repo_name = repo_name
        self.pr_num = pr_num
        self.local_repo_path = local_repo_path
        self.max_depth = max_depth
        self.provider = provider

        env_dir = Path(local_repo_path).resolve() if local_repo_path else Path.cwd()
        self.token = resolve_token(provider, github_token, env_dir)
        self.git_client = get_git_client(
            provider,
            self.token,
            base_url=gitlab_url if gitlab_url else "https://gitlab.com",
        )

        self._integrations: List[LanguageIntegration] = []
        if integrations:
            self._integrations = [get_integration(i) for i in integrations]
        else:
            self._detected_integrations: List[str] = []

    def _read_lines(self, path: Path) -> List[str]:
        try:
            return path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return []

    def _relpath(self, root: Path, p: Path) -> str:
        return p.relative_to(root).as_posix()

    def _build_pr_diff_text(self, pr_files: List[dict]) -> str:
        out: List[str] = []
        for f in pr_files:
            out.append(f"diff -- {f.get('filename', '')} [{f.get('status', '')}]")
            out.append(f.get("patch", "") or "(No textual patch available from API for this file.)")
            out.append("")
        return "\n".join(out).rstrip()

    def _format_full_file_content(self, lines: List[str]) -> str:
        if not lines:
            return "(empty file)"
        return "\n".join(f"{i:>5} | {line}" for i, line in enumerate(lines, start=1))

    def _load_repository(self, repo_root: Path) -> RepositoryFiles:
        repo = RepositoryFiles(root=repo_root)

        for integration in self._integrations:
            for abs_file in integration.iter_code_files(repo_root, repo):
                rp = self._relpath(repo_root, abs_file)
                if rp not in repo.files_lines:
                    repo.repo_files.add(rp)
                    lines = self._read_lines(abs_file)
                    repo.files_lines[rp] = lines
                    repo.files_entities[rp] = integration.parse_entities(rp, lines)

        for fp, lines in repo.files_lines.items():
            ext = "." + fp.rsplit(".", 1)[-1] if "." in fp else ""
            integration = self._get_integration_for_extension(ext)
            if integration:
                repo.all_import_edges.extend(
                    integration.parse_imports(fp, lines, repo.repo_files)
                )

        for edge in repo.all_import_edges:
            repo.imports_by_source.setdefault(edge.source_file, []).append(edge)

        return repo

    def _get_integration_for_extension(self, ext: str):
        for integration in self._integrations:
            if ext in integration.config.extensions:
                return integration
        return self._integrations[0] if self._integrations else None

    def analyze(self) -> AnalysisResult:
        pr = self.git_client.get_pr(self.repo_name, self.pr_num)
        pr_files = self.git_client.get_pr_files(self.repo_name, self.pr_num)

        pr_file_names = [f.get("filename", "") for f in pr_files]

        if not self._integrations:
            detected = detect_integrations_from_files(pr_file_names)
            self._detected_integrations = detected
            self._integrations = [get_integration(i) for i in detected]

        head_sha = pr.get("sha", "") or pr.get("head", {}).get("sha", "") or ""
        if not head_sha:
            head_sha = pr.get("last_commit", {}).get("id", "")
        if not head_sha:
            raise RuntimeError("Could not resolve PR head SHA.")

        tmp_ctx = None
        if self.local_repo_path:
            repo_root = Path(self.local_repo_path).resolve()
        else:
            tmp_ctx = tempfile.TemporaryDirectory(prefix="pr-diff-walk-")
            repo_root = self.git_client.download_head_snapshot(
                self.repo_name, head_sha, Path(tmp_ctx.name)
            )

        try:
            repo = self._load_repository(repo_root)

            changed_entities: List[ChangedEntity] = []
            for f in pr_files:
                filename = f.get("filename", "")
                patch = f.get("patch", "")
                if not filename or not patch:
                    continue

                ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
                integration = self._get_integration_for_extension(ext)
                if not integration:
                    continue

                if filename not in repo.files_entities:
                    continue

                patch_lines = integration.extract_changed_line_numbers_from_patch(patch)
                changed_entities.extend(
                    integration.changed_entities_from_patch(
                        filename, patch_lines, repo.files_entities[filename]
                    )
                )

            dedup_seeds: Dict[tuple, Hop] = {}
            seeds = []
            for ce in changed_entities:
                key = (ce.entity.file_path, ce.entity.name, ce.entity.kind)
                if key not in dedup_seeds:
                    dedup_seeds[key] = ce.entity
                    seeds.append(ce.entity)

            chains: List[DependencyChain] = []
            for s in seeds:
                for integration in self._integrations:
                    hops, terminals = integration.trace_dependency_chain(
                        files_lines=repo.files_lines,
                        files_entities=repo.files_entities,
                        imports_by_source=repo.imports_by_source,
                        seed=s,
                        max_depth=self.max_depth,
                    )
                    if hops:
                        chains.append(DependencyChain(seed=s, hops=hops, terminals=terminals))
                        break

            integration_names = [i.config.name for i in self._integrations]

            return AnalysisResult(
                repo_name=self.repo_name,
                pr_num=self.pr_num,
                head_ref=pr.get("source_branch", "") or pr.get("head", {}).get("ref", "") or "",
                base_ref=pr.get("target_branch", "") or pr.get("base", {}).get("ref", "") or "",
                pr_diff=self._build_pr_diff_text(pr_files),
                chains=chains,
                files_lines=repo.files_lines,
                integration_name=",".join(integration_names),
            )

        finally:
            if tmp_ctx:
                tmp_ctx.cleanup()

    def generate_report(self, analysis_result: AnalysisResult) -> str:
        lines = []
        lines.append(f"# {analysis_result.integration_name.title()} Context Analysis")
        lines.append("")
        lines.append(f"Repository: {analysis_result.repo_name}")
        lines.append(f"PR/MR: #{analysis_result.pr_num}")
        lines.append(f"Head branch: {analysis_result.head_ref}")
        lines.append(f"Base branch: {analysis_result.base_ref}")
        lines.append(f"Provider: {self.provider}")
        lines.append(f"Integrations: {analysis_result.integration_name}")
        lines.append("")
        lines.append("## Diff Content")
        lines.append("```diff")
        lines.append(analysis_result.pr_diff)
        lines.append("```")
        lines.append("")
        lines.append("## Dependency Chains")

        if not analysis_result.chains:
            lines.append("No changed entities detected.")

        first_file_anchor: Dict[str, str] = {}
        files_lines = analysis_result.files_lines

        for idx, chain in enumerate(analysis_result.chains, start=1):
            seed = chain.seed
            hops: List[Hop] = chain.hops
            lines.append(f"\n### Chain {idx}")
            lines.append(f"- seed: `{seed.file_path}` :: `{seed.name}` ({seed.kind})")

            if not hops:
                lines.append("- no import-based dependents found.")
            else:
                file_order: List[str] = []
                seen_in_chain: set = set()
                for h in hops:
                    fp = h.next_entity.file_path
                    if fp not in seen_in_chain:
                        seen_in_chain.add(fp)
                        file_order.append(fp)

                for fp in file_order:
                    lines.append(f"\n#### File: `{fp}`")
                    lines.append("```text")
                    anchor = f"### Chain {idx} #### File: `{fp}`"
                    if fp in first_file_anchor:
                        lines.append(f"SAME AS [{first_file_anchor[fp]}]")
                    else:
                        first_file_anchor[fp] = anchor
                        lines.append(self._format_full_file_content(files_lines.get(fp, [])))
                    lines.append("```")

        return "\n".join(lines)


def analyze_pr(
    repo_name: str,
    pr_num: int,
    github_token: Optional[str] = None,
    local_repo_path: Optional[str] = None,
    max_depth: int = 8,
    integrations: Optional[List[str]] = None,
    provider: str = "github",
    gitlab_url: Optional[str] = None,
    output_format: str = "report",
) -> Dict:
    service = DiffChainService(
        repo_name=repo_name,
        pr_num=pr_num,
        github_token=github_token,
        local_repo_path=local_repo_path,
        max_depth=max_depth,
        integrations=integrations,
        provider=provider,
        gitlab_url=gitlab_url,
    )
    result = service.analyze()

    if output_format == "report":
        return {"report": service.generate_report(result), "data": result}
    return {"data": result}
