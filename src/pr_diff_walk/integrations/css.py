import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

CSS_EXTENSIONS = {".css"}


def _css_config() -> LanguageConfig:
    return LanguageConfig(
        name="css",
        extensions=CSS_EXTENSIONS,
        file_patterns=["*.css"],
        module_marker="<module>",
        package_indicator="",
        import_patterns={
            "import": r"@import\s+['\"]([^'\"]+)['\"]",
            "url": r"@import\s+url\(['\"]([^'\"]+)['\"]\)",
        },
        entity_kinds={"class", "id", "tag", "keyframes", "variable"},
    )


class CssIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_css_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        excluded = repo.excluded_dirs | {
            "coverage",
            ".sass_cache",
        }
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in excluded]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in CSS_EXTENSIONS:
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
            base_path + ".css",
            base_path + "/index.css",
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
            m = re.match(r"@import\s+['\"]([^'\"]+)['\"]", line)
            if m:
                spec = m.group(1).strip()
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, None, spec, i, "css"))
            m_url = re.match(r"@import\s+url\(['\"]([^'\"]+)['\"]\)", line)
            if m_url:
                spec = m_url.group(1).strip()
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, None, spec, i, "css"))
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        HTML_TAGS = {
            "div", "span", "p", "a", "ul", "ol", "li", "table", "tr", "td", "th",
            "form", "input", "button", "select", "option", "textarea",
            "header", "footer", "nav", "section", "article", "aside", "main",
            "h1", "h2", "h3", "h4", "h5", "h6",
        }
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            if m := re.match(r"^\.([A-Za-z_-][A-Za-z0-9_-]*)\s*\{", s):
                out.append(EntityDef(name=m.group(1), kind="class", start=i, end=i))
            if m := re.match(r"^#([A-Za-z_-][A-Za-z0-9_-]*)\s*\{", s):
                out.append(EntityDef(name=m.group(1), kind="id", start=i, end=i))
            if m := re.match(r"^([a-z][a-z0-9]*)\s*\{", s, re.IGNORECASE):
                if m.group(1).lower() not in HTML_TAGS:
                    out.append(EntityDef(name=m.group(1), kind="tag", start=i, end=i))
            if m := re.match(r"@keyframes\s+([A-Za-z_-][A-Za-z0-9_-]*)", s):
                out.append(EntityDef(name=m.group(1), kind="keyframes", start=i, end=i))
            if m := re.match(r"--([A-Za-z_-][A-Za-z0-9_-]*)\s*:", s):
                out.append(EntityDef(name=m.group(1), kind="variable", start=i, end=i))
        return out
