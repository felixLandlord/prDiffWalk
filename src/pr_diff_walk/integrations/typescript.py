import re
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from ..base import LanguageIntegration
from ..schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

TS_EXTENSIONS = {".ts", ".tsx"}


def _ts_config() -> LanguageConfig:
    return LanguageConfig(
        name="typescript",
        extensions=TS_EXTENSIONS,
        file_patterns=["*.ts", "*.tsx"],
        module_marker="<module>",
        package_indicator="",
        import_patterns={
            "import": r"^\s*import\s+(.+?)\s+from\s+['\"]([^'\"]+)['\"]",
            "require": r"^\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        },
        entity_kinds={"class", "function", "method", "variable", "module", "interface", "type", "enum"},
    )


class TypescriptIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_ts_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        excluded = repo.excluded_dirs | {
            "coverage",
            ".nyc_output",
            ".test_results",
            "tsconfig.build",
        }
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in excluded]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in TS_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec or not spec.startswith("."):
            return None
        cur = Path(current_file)
        base_path = (cur.parent / spec).as_posix()
        candidates = [
            base_path,
            base_path + ".ts",
            base_path + ".tsx",
            base_path + ".js",
            base_path + ".jsx",
            base_path + "/index.ts",
            base_path + "/index.tsx",
            base_path + "/index.js",
            base_path + "/index.jsx",
        ]
        normed = [Path(c).as_posix().lstrip("./") for c in candidates]
        for c in normed:
            if c in repo_files:
                return c
        return None

    def parse_imports(
        self, file_path: str, lines: List[str], repo_files: Set[str]
    ) -> List[ImportEdge]:
        edges: List[ImportEdge] = []
        for i, line in enumerate(lines, start=1):
            m = re.match(r"^\s*import\s+(.+?)\s+from\s+['\"]([^'\"]+)['\"]", line)
            clause = None
            spec = None
            if not m:
                m = re.match(r"^\s*import\s+['\"]([^'\"]+)['\"]", line)
                if m:
                    spec = m.group(1).strip()
            else:
                clause = m.group(1).strip()
                spec = m.group(2).strip()

            if not m:
                m = re.match(r"^\s*require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", line)
                if m:
                    spec = m.group(1).strip()
                else:
                    continue

            if not spec:
                continue

            src_file = self.resolve_import_to_file(file_path, spec, repo_files)
            if src_file:
                alias = spec.split("/")[-1] if clause is None else (clause.split(",")[0].strip() if clause else spec)
                edges.append(ImportEdge(file_path, src_file, "default", alias, i, "ts"))

        for i, line in enumerate(lines, start=1):
            m = re.match(r"^\s*import\s+(.+?)\s+from\s+['\"]([^'\"]+)['\"]", line)
            if m:
                clause = m.group(1).strip()
                spec = m.group(2).strip()
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                if not src_file:
                    continue
                if "{" not in clause and not clause.startswith("*"):
                    alias = clause.split(",")[0].strip()
                    if alias:
                        edges.append(ImportEdge(file_path, src_file, "default", alias, i, "ts"))
                m_ns = re.match(r"^\*\s+as\s+([A-Za-z_]\w*)$", clause)
                if m_ns:
                    edges.append(ImportEdge(file_path, src_file, None, m_ns.group(1), i, "ts"))
                m_named = re.search(r"\{(.+)\}", clause)
                if m_named:
                    for part in [p.strip() for p in m_named.group(1).split(",")]:
                        if not part:
                            continue
                        ma = re.match(r"^([A-Za-z_]\w*)(?:\s+as\s+([A-Za-z_]\w*))?$", part)
                        if not ma:
                            continue
                        orig = ma.group(1)
                        alias = ma.group(2) or orig
                        edges.append(ImportEdge(file_path, src_file, orig, alias, i, "ts"))
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        class_stack: List[Tuple[str, int, int]] = []
        brace_depth = 0
        pending_class: Optional[Tuple[str, int]] = None
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            if m := re.match(r"^(?:export\s+)?class\s+([A-Za-z_]\w*)", s):
                pending_class = (m.group(1), i)
                out.append(EntityDef(name=m.group(1), kind="class", start=i, end=i))
            if m := re.match(r"^(?:export\s+)?interface\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="interface", start=i, end=i))
            if m := re.match(r"^(?:export\s+)?type\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="type", start=i, end=i))
            if m := re.match(r"^(?:export\s+)?enum\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
            if m := re.match(r"^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)\s*\(", s):
                out.append(EntityDef(name=m.group(1), kind="function", start=i, end=i))
            if m := re.match(r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_]\w*)\s*=\s*(?:async\s*)?(?:\(|[A-Za-z_]\w*\s*=>)", s):
                out.append(EntityDef(name=m.group(1), kind="function", start=i, end=i))
            if m := re.match(r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_]\w*)\s*[=:]", s):
                out.append(EntityDef(name=m.group(1), kind="variable", start=i, end=i))

            opens = line.count("{")
            closes = line.count("}")
            prev_depth = brace_depth
            brace_depth += opens - closes
            if pending_class and opens > 0:
                class_stack.append((pending_class[0], prev_depth + 1, pending_class[1]))
                pending_class = None
            while class_stack and brace_depth < class_stack[-1][1]:
                class_stack.pop()

            if class_stack and (m := re.match(r"^(?:async\s+)?([A-Za-z_]\w*)\s*\([^;]*\)\s*\{?\s*$", s)):
                if m.group(1) not in {"if", "for", "while", "switch", "catch"}:
                    out.append(EntityDef(name=m.group(1), kind="method", start=i, end=i, parent=class_stack[-1][0]))
        return out
