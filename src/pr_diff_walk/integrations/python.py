import re
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from ..base import LanguageIntegration
from ..schemas import EntityDef, EntityRef, ImportEdge, LanguageConfig, RepositoryFiles

PYTHON_EXTENSIONS = {".py"}


def _python_config() -> LanguageConfig:
    return LanguageConfig(
        name="python",
        extensions=PYTHON_EXTENSIONS,
        file_patterns=["*.py"],
        module_marker="__init__.py",
        package_indicator="__init__.py",
        import_patterns={
            "import": r"^(?:from\s+([\w.]+)\s+)?import\s+(.+)$",
        },
        entity_kinds={"class", "function", "method", "variable", "module", "async_function"},
    )


class PythonIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_python_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        import os
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in repo.excluded_dirs]
            base_path = Path(dirpath)
            for name in filenames:
                p = base_path / name
                if p.suffix.lower() in PYTHON_EXTENSIONS:
                    yield p

    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        if not spec:
            return None
        
        cur = Path(current_file)
        parts = spec.split(".")
        base_path = cur.parent / spec.replace(".", "/")
        
        candidates = [
            base_path.as_posix(),
            base_path.as_posix() + ".py",
            (base_path / "__init__.py").as_posix(),
            (spec.split("/")[-1] if "/" in spec else spec) + ".py",
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
            
            m = re.match(r"^from\s+([\w.]+)\s+import\s+(.+)$", s)
            if m:
                module = m.group(1)
                imports = m.group(2).strip()
                src_file = self.resolve_import_to_file(file_path, module, repo_files)
                if src_file:
                    for item in [p.strip() for p in imports.split(",")]:
                        ma = re.match(r"([A-Za-z_]\w*)(?:\s+as\s+([A-Za-z_]\w*))?", item)
                        if ma:
                            orig = ma.group(1)
                            alias = ma.group(2) or orig
                            edges.append(ImportEdge(file_path, src_file, orig, alias, i, "py"))
                continue

            m = re.match(r"^import\s+(.+)$", s)
            if m:
                imports = m.group(1).strip()
                for item in [p.strip() for p in imports.split(",")]:
                    ma = re.match(r"([A-Za-z_]\w*)?(?:\s+as\s+([A-Za-z_]\w*))?", item)
                    if ma:
                        module = ma.group(1)
                        alias = ma.group(2) or module or item
                        src_file = self.resolve_import_to_file(file_path, module, repo_files)
                        if src_file:
                            edges.append(ImportEdge(file_path, src_file, None, alias, i, "py"))
        return edges

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        out: List[EntityDef] = []
        class_stack: List[Tuple[str, int]] = []
        indent_stack: List[int] = []
        brace_depth = 0
        pending_class: Optional[Tuple[str, int]] = None
        
        for i, line in enumerate(lines, start=1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            
            stripped = s
            indent = len(line) - len(line.lstrip())
            
            if m := re.match(r"^(?:abstract\s+)?class\s+([A-Za-z_]\w*).*:$", stripped):
                pending_class = (m.group(1), i)
                out.append(EntityDef(name=m.group(1), kind="class", start=i, end=i))
            
            if m := re.match(r"^(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", stripped):
                kind = "async_function" if stripped.startswith("async") else "function"
                out.append(EntityDef(name=m.group(1), kind=kind, start=i, end=i, parent=class_stack[-1][0] if class_stack else None))
            
            if m := re.match(r"^([A-Za-z_]\w*)\s*:\s*(?:[^=].*)?$", stripped):
                if m.group(1) not in {"if", "for", "while", "try", "with", "except", "else", "elif", "class", "def", "return", "raise", "pass", "break", "continue"}:
                    out.append(EntityDef(name=m.group(1), kind="variable", start=i, end=i))
            
            opens = stripped.count("{")
            closes = stripped.count("}")
            brace_depth += opens - closes
            
            if pending_class:
                class_stack.append((pending_class[0], i))
                pending_class = None
            
            while indent_stack and indent <= indent_stack[-1]:
                popped_indent = indent_stack.pop()
                while class_stack and class_stack[-1][1] == popped_indent:
                    class_stack.pop()
                    if indent_stack:
                        popped_indent = indent_stack[-1]
                    else:
                        break
            
            if stripped.endswith(":"):
                indent_stack.append(indent)
        
        return out

    def infer_top_level_variable(self, lines: List[str], line_no: int) -> Optional[EntityDef]:
        line = lines[line_no - 1] if 1 <= line_no <= len(lines) else ""
        if m := re.match(r"^\s*([A-Za-z_]\w*)\s*=", line.strip()):
            return EntityDef(name=m.group(1), kind="variable", start=line_no, end=line_no)
        return None
