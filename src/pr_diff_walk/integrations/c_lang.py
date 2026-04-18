import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

C_EXTENSIONS = {".c", ".h"}


def _c_config() -> LanguageConfig:
    return LanguageConfig(
        name="c",
        extensions=C_EXTENSIONS,
        file_patterns=["*.c", "*.h"],
        module_marker="CMakeLists.txt",
        package_indicator="",
        import_patterns={
            "include": r"^\s*#include\s+[<\"]([^>\"]+)[>\"]",
        },
        entity_kinds={"function", "struct", "union", "enum", "typedef", "variable", "macro"},
    )


class CIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_c_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in C_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        cur = Path(current_file)
        
        candidates = [
            (cur.parent / spec).as_posix(),
            (cur.parent / spec.replace(".h", ".c")).as_posix(),
            (cur.parent / (spec.replace(".h", "").replace(".", "_") + ".h")).as_posix(),
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
            
            m = re.match(r'^\s*#include\s+[<"]([^>"]+)[>"]', s)
            if m:
                spec = m.group(1)
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                name = spec.split("/")[-1]
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, None, name, i, "c"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        typedef_stack: List[str] = []
        brace_depth = 0
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^\s*#define\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="macro", start=i, end=i))
            
            if m := re.match(r"^\s*typedef\s+(?:struct|union|enum)", s):
                typedef_match = re.search(r"([A-Za-z_]\w*)\s*;", s)
                if typedef_match:
                    out.append(EntityDef(name=typedef_match.group(1), kind="typedef", start=i, end=i))
            
            if m := re.match(r"^\s*typedef\s+([\w\s*]+)\s+([A-Za-z_]\w*)\s*;", s):
                out.append(EntityDef(name=m.group(2), kind="typedef", start=i, end=i))
            
            if m := re.match(r"^\s*(?:static\s+)?[\w*\s]+\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{?\s*$", s):
                if m.group(1) not in {"if", "for", "while", "switch", "return"}:
                    out.append(EntityDef(name=m.group(1), kind="function", start=i, end=i))
            
            if m := re.match(r"^\s*struct\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="struct", start=i, end=i))
                typedef_stack.append(m.group(1))
            
            if m := re.match(r"^\s*union\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="union", start=i, end=i))
                typedef_stack.append(m.group(1))
            
            if m := re.match(r"^\s*enum\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
                typedef_stack.append(m.group(1))
            
            brace_depth += s.count("{") - s.count("}")
            if s == "}" and typedef_stack:
                typedef_stack.pop()
        
        return out
