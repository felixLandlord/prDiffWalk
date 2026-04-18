import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

HTML_EXTENSIONS = {".html"}


def _html_config() -> LanguageConfig:
    return LanguageConfig(
        name="html",
        extensions=HTML_EXTENSIONS,
        file_patterns=["*.html"],
        module_marker="<module>",
        package_indicator="",
        import_patterns={
            "script": r'<script[^>]+src=["\']([^"\']+)["\']',
            "link": r'<link[^>]+href=["\']([^"\']+\.css)["\']',
        },
        entity_kinds={"id", "class", "tag"},
    )


class HtmlIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_html_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        excluded = repo.excluded_dirs | {
            ".templatecache",
        }
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in excluded]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in HTML_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        cur = Path(current_file)
        base_path = (cur.parent / spec).as_posix()
        candidates = [
            base_path,
            base_path + ".html",
            base_path + ".js",
            base_path + "/index.html",
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
        content = "\n".join(lines)
        for spec in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE):
            src_file = self.resolve_import_to_file(file_path, spec, repo_files)
            if src_file:
                edges.append(ImportEdge(file_path, src_file, None, spec, 0, "html"))
        for spec in re.findall(r'<link[^>]+href=["\']([^"\']+\.css)["\']', content, re.IGNORECASE):
            src_file = self.resolve_import_to_file(file_path, spec, repo_files)
            if src_file:
                edges.append(ImportEdge(file_path, src_file, None, spec, 0, "html"))
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        content = "\n".join(lines)
        for m_id in re.findall(r'id=["\']([^"\']+)["\']', content):
            line_no = 1
            for i, line in enumerate(lines, start=1):
                if f'id="{m_id}' in line or f"id='{m_id}" in line:
                    line_no = i
                    break
            out.append(EntityDef(name=m_id, kind="id", start=line_no, end=line_no))
        for m_class in re.findall(r'class=["\']([^"\']+)["\']', content):
            for cls in m_class.split():
                if cls:
                    line_no = 1
                    for i, line in enumerate(lines, start=1):
                        if cls in line:
                            line_no = i
                            break
                    out.append(EntityDef(name=cls, kind="class", start=line_no, end=line_no))
        return out
