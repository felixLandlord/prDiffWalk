import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from ..base import LanguageIntegration
from ..schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

PHP_EXTENSIONS = {".php"}


def _php_config() -> LanguageConfig:
    return LanguageConfig(
        name="php",
        extensions=PHP_EXTENSIONS,
        file_patterns=["*.php"],
        module_marker="composer.json",
        package_indicator="namespace",
        import_patterns={
            "use": r"^\s*use\s+([\w\\]+);",
            "require": r"^\s*require(_once)?\s+['\"]([^'\"]+)['\"]",
        },
        entity_kinds={"class", "interface", "trait", "enum", "function", "method", "const"},
    )


class PhpIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_php_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in PHP_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        cur = Path(current_file)
        spec_path = spec.replace("\\", "/")
        
        candidates = [
            (cur.parent / spec_path).as_posix() + ".php",
            (cur.parent / (spec_path + ".php")).as_posix(),
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
            
            m = re.match(r"^\s*use\s+([\w\\]+)(?:\s+as\s+([\w\\]+))?;", s)
            if m:
                full_spec = m.group(1)
                alias = m.group(2) or full_spec.split("\\")[-1]
                src_file = self.resolve_import_to_file(file_path, full_spec, repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, full_spec, alias, i, "php"))
            
            m = re.match(r'^\s*require(_once)?\s+[\'"]([^\'"]+)[\'"]', s)
            if m:
                spec = m.group(2)
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, None, spec, i, "php"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        class_stack: List[str] = []
        brace_depth = 0
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^\s*(?:abstract\s+)?class\s+([A-Za-z_]\w*)", s):
                class_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="class", start=i, end=i))
            
            if m := re.match(r"^\s*interface\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="interface", start=i, end=i))
            
            if m := re.match(r"^\s*trait\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="trait", start=i, end=i))
            
            if m := re.match(r"^\s*enum\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
            
            if m := re.match(r"^\s*(?:abstract\s+)?function\s+([A-Za-z_]\w*)", s):
                parent = class_stack[-1] if class_stack else None
                kind = "method" if class_stack else "function"
                out.append(EntityDef(name=m.group(1), kind=kind, start=i, end=i, parent=parent))
            
            if m := re.match(r"^\s*const\s+([A-Za-z_]\w*)", s):
                parent = class_stack[-1] if class_stack else None
                out.append(EntityDef(name=m.group(1), kind="const", start=i, end=i, parent=parent))
            
            brace_depth += s.count("{") - s.count("}")
            if s == "}" and class_stack:
                class_stack.pop()
        
        return out
