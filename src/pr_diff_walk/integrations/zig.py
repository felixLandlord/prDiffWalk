import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

ZIG_EXTENSIONS = {".zig"}


def _zig_config() -> LanguageConfig:
    return LanguageConfig(
        name="zig",
        extensions=ZIG_EXTENSIONS,
        file_patterns=["*.zig"],
        module_marker="build.zig",
        package_indicator="const",
        import_patterns={
            "const": r"^\s*const\s+([A-Za-z_]\w*)\s*=\s*@import\s*\(\s*\"([^\"]+)\"\s*\)",
        },
        entity_kinds={"struct", "enum", "union", "error", "fn", "const", "var"},
    )


class ZigIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_zig_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in ZIG_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        cur = Path(current_file)
        base = (cur.parent / spec.replace(".", "/")).as_posix()
        
        candidates = [
            base + ".zig",
            (base.parent / (base.name + ".zig")).as_posix(),
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
            
            m = re.match(r'^\s*const\s+([A-Za-z_]\w*)\s*=\s*@import\s*\(\s*"([^"]+)"\s*\)', s)
            if m:
                alias = m.group(1)
                spec = m.group(2)
                src_file = self.resolve_import_to_file(file_path, spec, repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, spec, alias, i, "zig"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        struct_stack: List[str] = []
        brace_depth = 0
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^\s*pub\s+fn\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="fn", start=i, end=i))
            
            if m := re.match(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)", s):
                parent = struct_stack[-1] if struct_stack else None
                out.append(EntityDef(name=m.group(1), kind="fn", start=i, end=i, parent=parent))
            
            if m := re.match(r"^\s*(?:pub\s+)?struct\s+([A-Za-z_]\w*)", s):
                struct_stack.append(m.group(1))
                out.append(EntityDef(name=m.group(1), kind="struct", start=i, end=i))
            
            if m := re.match(r"^\s*(?:pub\s+)?enum\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
            
            if m := re.match(r"^\s*(?:pub\s+)?union\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="union", start=i, end=i))
            
            if m := re.match(r"^\s*const\s+([A-Za-z_]\w*)", s):
                parent = struct_stack[-1] if struct_stack else None
                out.append(EntityDef(name=m.group(1), kind="const", start=i, end=i, parent=parent))
            
            if m := re.match(r"^\s*var\s+([A-Za-z_]\w*)", s):
                parent = struct_stack[-1] if struct_stack else None
                out.append(EntityDef(name=m.group(1), kind="var", start=i, end=i, parent=parent))
            
            brace_depth += s.count("{") - s.count("}")
            if s == "}" and struct_stack:
                struct_stack.pop()
        
        return out
