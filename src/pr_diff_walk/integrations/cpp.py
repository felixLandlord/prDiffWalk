import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

CPP_EXTENSIONS = {".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx", ".h"}


def _cpp_config() -> LanguageConfig:
    return LanguageConfig(
        name="cpp",
        extensions=CPP_EXTENSIONS,
        file_patterns=["*.cpp", "*.cc", "*.cxx", "*.hpp", "*.hh", "*.hxx", "*.h"],
        module_marker="CMakeLists.txt",
        package_indicator="",
        import_patterns={
            "include": r"^\s*#include\s+[<\"]([^>\"]+)[>\"]",
        },
        entity_kinds={"class", "struct", "enum", "union", "namespace", "function", "template", "typedef", "using", "macro"},
    )


class CppIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_cpp_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in CPP_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        cur = Path(current_file)
        
        candidates = [
            (cur.parent / spec).as_posix(),
            (cur.parent / spec.replace(".hpp", ".cpp")).as_posix(),
            (cur.parent / spec.replace(".h", ".cpp")).as_posix(),
            (cur.parent / spec.replace(".hxx", ".cpp")).as_posix(),
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
                    edges.append(ImportEdge(file_path, src_file, None, name, i, "cpp"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        class_stack: List[str] = []
        namespace_stack: List[str] = []
        brace_depth = 0
        in_template = False
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^\s*#define\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="macro", start=i, end=i))
            
            if m := re.match(r"^\s*namespace\s+([A-Za-z_]\w*)", s):
                namespace_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="namespace", start=i, end=i))
            
            if s.startswith("template"):
                in_template = True
            
            if m := re.match(r"^\s*(?:template\s+)?(?:class|struct)\s+([A-Za-z_]\w*)", s):
                class_stack.append(m.group(1))
                kind = "struct" if "struct" in s else "class"
                out.append(EntityDef(name=m.group(1), kind=kind, start=i, end=i))
            
            if m := re.match(r"^\s*enum\s+(?:class\s+)?([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
            
            if m := re.match(r"^\s*union\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="union", start=i, end=i))
            
            if m := re.match(r"^\s*using\s+([A-Za-z_]\w*)\s*=", s):
                out.append(EntityDef(name=m.group(1), kind="using", start=i, end=i))
            
            if m := re.match(r"^\s*typedef\s+([\w\s*]+)\s+([A-Za-z_]\w*)\s*;", s):
                out.append(EntityDef(name=m.group(2), kind="typedef", start=i, end=i))
            
            if m := re.match(r"^\s*(?:virtual\s+)?[\w*\s&]+\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*(?:const)?\s*\{?\s*(?:override)?\s*$", s):
                if m.group(1) not in {"if", "for", "while", "switch", "return", "try", "catch"}:
                    parent = class_stack[-1] if class_stack else None
                    out.append(EntityDef(name=m.group(1), kind="function", start=i, end=i, parent=parent))
            
            if ">" in s:
                in_template = False
            
            brace_depth += s.count("{") - s.count("}")
            if s == "}":
                if class_stack:
                    class_stack.pop()
                if namespace_stack:
                    namespace_stack.pop()
        
        return out
