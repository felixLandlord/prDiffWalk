import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

JAVA_EXTENSIONS = {".java"}


def _java_config() -> LanguageConfig:
    return LanguageConfig(
        name="java",
        extensions=JAVA_EXTENSIONS,
        file_patterns=["*.java"],
        module_marker="package-info.java",
        package_indicator="package",
        import_patterns={
            "import": r"^\s*import\s+(?:static\s+)?([^;]+);",
        },
        entity_kinds={"class", "interface", "enum", "record", "method", "field", "constructor"},
    )


class JavaIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_java_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in JAVA_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        parts = spec.split(".")
        class_name = parts[-1]
        package_path = "/".join(parts[:-1])
        
        candidates = [
            f"{package_path}/{class_name}.java",
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
            
            if m := re.match(r"^\s*import\s+(?:static\s+)?([\w.]+);", s):
                full_spec = m.group(1)
                parts = full_spec.split(".")
                name = parts[-1]
                src_file = self.resolve_import_to_file(file_path, full_spec, repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, name, name, i, "java"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        class_stack: List[str] = []
        brace_depth = 0
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?\s*class\s+([A-Za-z_]\w*)", s):
                class_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="class", start=i, end=i))
            
            if m := re.match(r"^\s*(?:public|private|protected)?\s*interface\s+([A-Za-z_]\w*)", s):
                class_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="interface", start=i, end=i))
            
            if m := re.match(r"^\s*(?:public|private|protected)?\s*enum\s+([A-Za-z_]\w*)", s):
                class_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
            
            if m := re.match(r"^\s*record\s+([A-Za-z_]\w*)", s):
                class_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="record", start=i, end=i))
            
            if m := re.match(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?\s*[\w<>,\s]+\s+([A-Za-z_]\w*)\s*\([^)]*\)\s*\{?\s*(?:throws[^{]+)?$", s):
                if m.group(1) not in {"if", "for", "while", "switch", "catch", "synchronized"}:
                    parent = class_stack[-1] if class_stack else None
                    out.append(EntityDef(name=m.group(1), kind="method", start=i, end=i, parent=parent))
            
            if m := re.match(r"^\s*([A-Za-z_]\w*)\s+([A-Za-z_]\w*)\s*;", s):
                if m.group(2) not in {"class", "interface", "enum", "extends", "implements", "static", "final", "void", "int", "long", "double", "float", "boolean", "char", "byte", "short", "public", "private", "protected"}:
                    parent = class_stack[-1] if class_stack else None
                    out.append(EntityDef(name=m.group(2), kind="field", start=i, end=i, parent=parent))
            
            brace_depth += s.count("{") - s.count("}")
            if s == "}" and class_stack:
                class_stack.pop()
        
        return out
