import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

SWIFT_EXTENSIONS = {".swift"}


def _swift_config() -> LanguageConfig:
    return LanguageConfig(
        name="swift",
        extensions=SWIFT_EXTENSIONS,
        file_patterns=["*.swift"],
        module_marker="Package.swift",
        package_indicator="import",
        import_patterns={
            "import": r"^\s*import\s+([\w.]+)",
        },
        entity_kinds={"class", "struct", "enum", "protocol", "extension", "func", "var", "let"},
    )


class SwiftIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_swift_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in SWIFT_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        cur = Path(current_file)
        parts = spec.split("/")
        file_name = parts[-1]
        
        candidates = [
            (cur.parent / spec.replace(".", "/") + ".swift").as_posix(),
            (cur.parent / "/".join(parts[:-1]) / (file_name + ".swift")).as_posix(),
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
            
            if m := re.match(r"^\s*import\s+([\w.]+)", s):
                spec = m.group(1)
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                name = spec.split("/")[-1]
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, name, name, i, "swift"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        type_stack: List[str] = []
        brace_depth = 0
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^\s*(?:public\s+)?(?:class|struct)\s+([A-Za-z_]\w*)", s):
                type_stack.append(m.group(1))
                kind = "struct" if "struct" in s else "class"
                out.append(EntityDef(name=m.group(1), kind=kind, start=i, end=i))
            
            if m := re.match(r"^\s*enum\s+([A-Za-z_]\w*)", s):
                type_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
            
            if m := re.match(r"^\s*protocol\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="protocol", start=i, end=i))
            
            if m := re.match(r"^\s*extension\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="extension", start=i, end=i))
            
            if m := re.match(r"^\s*(?:func|static\s+func)\s+([A-Za-z_]\w*)", s):
                parent = type_stack[-1] if type_stack else None
                out.append(EntityDef(name=m.group(1), kind="func", start=i, end=i, parent=parent))
            
            if m := re.match(r"^\s*(?:var|let)\s+([A-Za-z_]\w*)", s):
                parent = type_stack[-1] if type_stack else None
                kind = "let" if s.startswith("let") else "var"
                out.append(EntityDef(name=m.group(1), kind=kind, start=i, end=i, parent=parent))
            
            brace_depth += s.count("{") - s.count("}")
            if s == "}" and type_stack:
                type_stack.pop()
        
        return out
