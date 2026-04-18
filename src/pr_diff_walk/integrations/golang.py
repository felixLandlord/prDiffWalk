import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

GO_EXTENSIONS = {".go"}


def _go_config() -> LanguageConfig:
    return LanguageConfig(
        name="go",
        extensions=GO_EXTENSIONS,
        file_patterns=["*.go"],
        module_marker="go.mod",
        package_indicator="package",
        import_patterns={
            "import": r"^\s*\"([^\"]+)\"",
        },
        entity_kinds={"function", "method", "type", "struct", "interface", "const", "var"},
    )


class GoIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_go_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in GO_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        cur = Path(current_file)
        base = cur.parent / spec.replace("/", ".")
        
        candidates = [
            (cur.parent / spec.replace("/", "/")).as_posix(),
            (base.parent / (base.stem + ".go")).as_posix(),
        ]
        
        for c in candidates:
            if c in repo_files:
                return c
        return None

    def parse_imports(
        self, file_path: str, lines: List[str], repo_files: Set[str]
    ) -> List[ImportEdge]:
        edges: List[ImportEdge] = []
        in_import_block = False
        import_specs: List[str] = []
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r'^import\s+"([^"]+)"', s):
                import_specs.append(m.group(1))
                src_file = self.resolve_import_to_file(file_path, m.group(1), repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, None, m.group(1).split("/")[-1], i, "go"))
                continue
            
            if s.startswith("import ("):
                in_import_block = True
                continue
            
            if in_import_block:
                if s == ")":
                    in_import_block = False
                    continue
                if m := re.match(r'^\s*"([^"]+)"', s):
                    src_file = self.resolve_import_to_file(file_path, m.group(1), repo_files)
                    if src_file:
                        edges.append(ImportEdge(file_path, src_file, None, m.group(1).split("/")[-1], i, "go"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        type_stack: List[str] = []
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^(?:func|func)\s+(\([^(]+\))\s*([A-Za-z_]\w*)", s):
                type_stack.append(m.group(2))
                out.append(EntityDef(name=m.group(2), kind="method", start=i, end=i))
            
            if m := re.match(r"^func\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="function", start=i, end=i))
            
            if m := re.match(r"^type\s+([A-Za-z_]\w*)\s+struct", s):
                out.append(EntityDef(name=m.group(1), kind="struct", start=i, end=i))
            
            if m := re.match(r"^type\s+([A-Za-z_]\w*)\s+interface", s):
                out.append(EntityDef(name=m.group(1), kind="interface", start=i, end=i))
            
            if m := re.match(r"^type\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="type", start=i, end=i))
            
            if m := re.match(r"^const\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="const", start=i, end=i))
            
            if m := re.match(r"^var\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="var", start=i, end=i))
            
            if s == "}":
                if type_stack:
                    type_stack.pop()
        
        return out
