import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from ..base import LanguageIntegration
from ..schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

FLUTTER_EXTENSIONS = {".dart"}


def _dart_config() -> LanguageConfig:
    return LanguageConfig(
        name="dart",
        extensions=FLUTTER_EXTENSIONS,
        file_patterns=["*.dart"],
        module_marker="pubspec.yaml",
        package_indicator="library",
        import_patterns={
            "import": r"^\s*import\s+['\"]([^'\"]+)['\"]",
        },
        entity_kinds={"class", "mixin", "extension", "enum", "function", "typedef"},
    )


class DartIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_dart_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in FLUTTER_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        cur = Path(current_file)
        parts = spec.split("/")
        base = "/".join(parts[:-1])
        file_name = parts[-1]
        
        candidates = [
            (cur.parent / spec.replace("package:", "")).as_posix().lstrip("./"),
            (cur.parent / base / file_name.replace(".dart", "")).as_posix().lstrip("./") + ".dart",
            (cur.parent / base / "lib" / file_name.replace(".dart", "")).as_posix().lstrip("./") + ".dart",
        ]
        
        for c in candidates:
            if c in repo_files:
                return c
        return None

    def parse_imports(
        self, file_path: str, lines: List[str], repo_files: Set[str]
    ) -> List[ImportEdge]:
        edges: List[ImportEdge] = []
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            m = re.match(r"^\s*import\s+['\"]([^'\"]+)['\"]", s)
            if m:
                spec = m.group(1)
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                name = spec.split("/")[-1].replace(".dart", "")
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, name, name, i, "dart"))
            
            m = re.match(r"^\s*export\s+['\"]([^'\"]+)['\"]", s)
            if m:
                spec = m.group(1)
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                name = spec.split("/")[-1].replace(".dart", "")
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, name, name, i, "dart"))
            
            m = re.match(r"^\s*part\s+['\"]([^'\"]+)['\"]", s)
            if m:
                spec = m.group(1)
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, None, spec, i, "dart"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        class_stack: List[str] = []
        brace_depth = 0
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^\s*(?:abstract\s+)?(?:class|mixin)\s+([A-Za-z_]\w*)", s):
                class_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind=m.group(2) if "mixin" in s else "class", start=i, end=i))
            
            if m := re.match(r"^\s*extension\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="extension", start=i, end=i))
            
            if m := re.match(r"^\s*enum\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
            
            if m := re.match(r"^\s*typedef\s+[\w<>,]+\s*=\s*[\w<>,]+", s):
                typedef_match = re.search(r"([A-Za-z_]\w*)\s*=", s)
                if typedef_match:
                    out.append(EntityDef(name=typedef_match.group(1), kind="typedef", start=i, end=i))
            
            if m := re.match(r"^\s*(?:static\s+)?\s*[\w<>,]+\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*(?:\{)?\s*$", s):
                if m.group(1) not in {"if", "for", "while", "switch", "catch", "return"}:
                    parent = class_stack[-1] if class_stack else None
                    out.append(EntityDef(name=m.group(1), kind="function", start=i, end=i, parent=parent))
            
            brace_depth += s.count("{") - s.count("}")
            if s == "}" and class_stack:
                class_stack.pop()
        
        return out
