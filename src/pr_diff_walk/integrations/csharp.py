import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

CSHARP_EXTENSIONS = {".cs"}


def _csharp_config() -> LanguageConfig:
    return LanguageConfig(
        name="csharp",
        extensions=CSHARP_EXTENSIONS,
        file_patterns=["*.cs"],
        module_marker="AssemblyInfo.cs",
        package_indicator="namespace",
        import_patterns={
            "using": r"^\s*using\s+([\w.]+);",
        },
        entity_kinds={"class", "interface", "struct", "enum", "record", "method", "property", "field", "delegate"},
    )


class CSharpIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_csharp_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in CSHARP_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        parts = spec.split(".")
        class_name = parts[-1]
        namespace_path = "/".join(parts[:-1])
        
        candidates = [
            f"{namespace_path}/{class_name}.cs",
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
            
            if m := re.match(r"^\s*using\s+([\w.]+);", s):
                full_spec = m.group(1)
                parts = full_spec.split(".")
                name = parts[-1]
                src_file = self.resolve_import_to_file(file_path, full_spec, repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, name, name, i, "cs"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        type_stack: List[str] = []
        brace_depth = 0
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^\s*(?:public|private|protected|internal)?\s*(?:abstract\s+)?(?:static\s+)?\s*class\s+([A-Za-z_]\w*)", s):
                type_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="class", start=i, end=i))
            
            if m := re.match(r"^\s*(?:public|private|protected|internal)?\s*interface\s+([A-Za-z_]\w*)", s):
                type_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="interface", start=i, end=i))
            
            if m := re.match(r"^\s*(?:public|private|protected|internal)?\s*struct\s+([A-Za-z_]\w*)", s):
                type_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="struct", start=i, end=i))
            
            if m := re.match(r"^\s*(?:public|private|protected|internal)?\s*enum\s+([A-Za-z_]\w*)", s):
                type_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
            
            if m := re.match(r"^\s*record\s+([A-Za-z_]\w*)", s):
                type_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="record", start=i, end=i))
            
            if m := re.match(r"^\s*delegate\s+[\w<>,]+\s+([A-Za-z_]\w*)\s*\([^)]*\)", s):
                out.append(EntityDef(name=m.group(1), kind="delegate", start=i, end=i, parent=type_stack[-1] if type_stack else None))
            
            if m := re.match(r"^\s*(?:public|private|protected|internal)?\s*(?:static\s+)?\s*[\w<>,]+\s+([A-Za-z_]\w*)\s*\([^)]*\)[\s{]*$", s):
                if m.group(1) not in {"if", "for", "while", "switch", "catch", "using", "lock", "fixed"}:
                    parent = type_stack[-1] if type_stack else None
                    out.append(EntityDef(name=m.group(1), kind="method", start=i, end=i, parent=parent))
            
            brace_depth += s.count("{") - s.count("}")
            if s == "}" and type_stack:
                type_stack.pop()
        
        return out
