import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.schemas import EntityDef, ImportEdge, LanguageConfig, RepositoryFiles

RUST_EXTENSIONS = {".rs"}


def _rust_config() -> LanguageConfig:
    return LanguageConfig(
        name="rust",
        extensions=RUST_EXTENSIONS,
        file_patterns=["*.rs"],
        module_marker="mod.rs",
        package_indicator="Cargo.toml",
        import_patterns={
            "use": r"^\s*use\s+(.+?)(?:\s*;)\s*$",
        },
        entity_kinds={"struct", "enum", "function", "method", "trait", "impl", "const", "static", "module"},
    )


class RustIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_rust_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in RUST_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        cur = Path(current_file)
        parts = spec.split("::")
        base = cur.parent / parts[0].replace(".", "/")
        
        candidates = [
            (base.parent / base.stem / "mod.rs").as_posix(),
            (base.parent / (base.stem + "_reexports") / "mod.rs").as_posix(),
            base.as_posix() + ".rs",
            (base / "mod.rs").as_posix(),
            base.as_posix(),
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
            
            m = re.match(r"^\s*use\s+(.+?)(?:\s*;)\s*$", s)
            if m:
                spec = m.group(1).strip()
                src = spec.rsplit("::", 1)
                module = src[0] if len(src) > 1 else ""
                name = src[-1]
                
                if name == "*":
                    alias = "*"
                elif "as" in spec:
                    parts = spec.split(" as ")
                    name_part = parts[0].rsplit("::", 1)[-1]
                    alias = parts[-1].strip()
                else:
                    alias = name
                
                src_file = self.resolve_import_to_file(file_path, module, repo_files)
                if src_file:
                    edges.append(ImportEdge(file_path, src_file, name, alias, i, "rs"))
                continue
            
            m = re.match(r"^\s*mod\s+([A-Za-z_]\w*)\s*;$", s)
            if m:
                mod_name = m.group(1)
                candidates = [
                    (cur := Path(file_path)).parent / mod_name / "mod.rs",
                    (cur := Path(file_path)).parent / (mod_name + ".rs"),
                ]
                for p in candidates:
                    if p.as_posix() in repo_files:
                        edges.append(ImportEdge(file_path, p.as_posix(), None, mod_name, i, "rs"))
        
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        impl_stack: List[str] = []
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            
            if m := re.match(r"^\s*(?:pub\s+)?struct\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="struct", start=i, end=i))
            
            if m := re.match(r"^\s*(?:pub\s+)?enum\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="enum", start=i, end=i))
            
            if m := re.match(r"^\s*(?:pub\s+)?trait\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="trait", start=i, end=i))
            
            if m := re.match(r"^\s*(?:pub\s+)?impl(?:\s+[^({]+)?\s*\{?\s*$", s):
                impl_stack.append(f"impl_{i}")
            
            if m := re.match(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="function", start=i, end=i, parent=impl_stack[-1] if impl_stack else None))
            
            if m := re.match(r"^\s*(?:pub\s+)?const\s+([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="const", start=i, end=i))
            
            if m := re.match(r"^\s*(?:pub\s+)?static\s+(?:mut\s+)?([A-Za-z_]\w*)", s):
                out.append(EntityDef(name=m.group(1), kind="static", start=i, end=i))
            
            if s == "}":
                if impl_stack:
                    impl_stack.pop()
        
        return out
