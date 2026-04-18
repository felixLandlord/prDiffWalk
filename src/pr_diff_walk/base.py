import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .schemas import (
    ChangedEntity,
    EntityDef,
    EntityRef,
    Hop,
    ImportEdge,
    LanguageConfig,
    RepositoryFiles,
)


class LanguageIntegration(ABC):
    def __init__(self, config: LanguageConfig):
        self.config = config

    @abstractmethod
    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        pass

    @abstractmethod
    def parse_imports(
        self, file_path: str, lines: List[str], repo_files: Set[str]
    ) -> List[ImportEdge]:
        pass

    @abstractmethod
    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        pass

    @abstractmethod
    def resolve_import_to_file(
        self, current_file: str, spec: str, repo_files: Set[str]
    ) -> Optional[str]:
        pass

    def infer_top_level_variable(
        self, lines: List[str], line_no: int
    ) -> Optional[EntityDef]:
        return None

    def find_usage_lines(
        self, lines: List[str], alias: str, import_line: int, entity_name: Optional[str]
    ) -> List[int]:
        out: List[int] = []
        if entity_name:
            pattern = re.compile(
                rf"\b{re.escape(alias)}\s*\.\s*{re.escape(entity_name)}\b"
            )
        else:
            pattern = re.compile(rf"\b{re.escape(alias)}\b")
        for i, line in enumerate(lines, start=1):
            if i == import_line:
                continue
            if pattern.search(line):
                out.append(i)
        if out:
            return out
        pattern2 = re.compile(rf"\b{re.escape(alias)}\b")
        for i, line in enumerate(lines, start=1):
            if i == import_line:
                continue
            if pattern2.search(line):
                out.append(i)
        return out

    def smallest_enclosing_entity(
        self, entities: List[EntityDef], line_no: int
    ) -> Optional[EntityDef]:
        candidates = [e for e in entities if e.start <= line_no <= e.end]
        if not candidates:
            return None
        return sorted(candidates, key=lambda x: (x.end - x.start, x.start))[0]

    def extract_snippet(
        self, lines: List[str], start: int, end: int, context_lines: int = 0
    ) -> str:
        start_i = max(1, start - context_lines)
        end_i = min(len(lines), end + context_lines)
        return "\n".join(f"{i:>5} | {lines[i - 1]}" for i in range(start_i, end_i + 1))

    def extract_changed_line_numbers_from_patch(self, patch: str) -> List[int]:
        lines: List[int] = []
        if not patch:
            return lines
        new_line_no = 0
        for line in patch.splitlines():
            if line.startswith("@@"):
                m = re.search(r"\+(\d+)(?:,\d+)?", line)
                if m:
                    new_line_no = int(m.group(1))
                continue
            if line.startswith("+") and not line.startswith("+++"):
                lines.append(new_line_no)
                new_line_no += 1
                continue
            if not line.startswith("-"):
                new_line_no += 1
        return sorted(set(lines))

    def changed_entities_from_patch(
        self, file_path: str, patch_lines: List[int], entities: List[EntityDef]
    ) -> List[ChangedEntity]:
        out: Dict[Tuple[str, str], ChangedEntity] = {}
        for ln in patch_lines:
            e = self.smallest_enclosing_entity(entities, ln)
            if e:
                key = (e.name, e.kind)
                if key not in out:
                    out[key] = ChangedEntity(
                        entity=EntityRef(file_path, e.name, e.kind),
                        from_patch_lines=[ln],
                    )
                else:
                    out[key].from_patch_lines.append(ln)
            else:
                key = ("<module>", "module")
                if key not in out:
                    out[key] = ChangedEntity(
                        entity=EntityRef(file_path, "<module>", "module"),
                        from_patch_lines=[ln],
                    )
                else:
                    out[key].from_patch_lines.append(ln)
        return list(out.values())

    def trace_dependency_chain(
        self,
        files_lines: Dict[str, List[str]],
        files_entities: Dict[str, List[EntityDef]],
        imports_by_source: Dict[str, List[ImportEdge]],
        seed: EntityRef,
        max_depth: int,
    ) -> Tuple[List[Hop], List[EntityRef]]:
        hops: List[Hop] = []
        terminal_entries: List[EntityRef] = []
        frontier: List[Tuple[EntityRef, int]] = [(seed, 0)]
        visited: Set[Tuple[str, str, str]] = set()

        while frontier:
            current, depth = frontier.pop(0)
            if depth >= max_depth:
                terminal_entries.append(current)
                continue
            key = (current.file_path, current.name, current.kind)
            if key in visited:
                continue
            visited.add(key)

            importer_edges = imports_by_source.get(current.file_path, [])
            if not importer_edges:
                ext = Path(current.file_path).suffix.lower()
                if ext in self.config.extensions or self._is_module_file(ext):
                    module_ref = EntityRef(current.file_path, "<module>", "module")
                    if (module_ref.file_path, module_ref.name, module_ref.kind) not in visited:
                        frontier.append((module_ref, depth + 1))
                    else:
                        terminal_entries.append(current)
                else:
                    terminal_entries.append(current)
                continue

            expanded = False
            for edge in importer_edges:
                importer_lines = files_lines.get(edge.importer_file, [])
                importer_entities = files_entities.get(edge.importer_file, [])

                usage_lines = self.find_usage_lines(
                    importer_lines, edge.alias, edge.line_no, None
                )
                if not usage_lines:
                    usage_lines = [edge.line_no]

                for uln in usage_lines[:20]:
                    ctx = self.smallest_enclosing_entity(importer_entities, uln)
                    if ctx:
                        next_entity = EntityRef(edge.importer_file, ctx.name, ctx.kind)
                        snippet = self.extract_snippet(importer_lines, ctx.start, ctx.end)
                        hop = Hop(
                            depth=depth + 1,
                            from_entity=current,
                            importer_file=edge.importer_file,
                            imported_as=edge.alias,
                            line_no=uln,
                            context_name=ctx.name,
                            context_kind=ctx.kind,
                            snippet=snippet,
                            snippet_start=ctx.start,
                            snippet_end=ctx.end,
                            next_entity=next_entity,
                        )
                    else:
                        v = self.infer_top_level_variable(importer_lines, uln)
                        if v:
                            next_entity = EntityRef(edge.importer_file, v.name, v.kind)
                            snippet = self.extract_snippet(importer_lines, v.start, v.end)
                            hop = Hop(
                                depth=depth + 1,
                                from_entity=current,
                                importer_file=edge.importer_file,
                                imported_as=edge.alias,
                                line_no=uln,
                                context_name=v.name,
                                context_kind=v.kind,
                                snippet=snippet,
                                snippet_start=v.start,
                                snippet_end=v.end,
                                next_entity=next_entity,
                            )
                        else:
                            next_entity = EntityRef(edge.importer_file, "<module>", "module")
                            s = max(1, uln - 3)
                            e = min(len(importer_lines), uln + 3)
                            hop = Hop(
                                depth=depth + 1,
                                from_entity=current,
                                importer_file=edge.importer_file,
                                imported_as=edge.alias,
                                line_no=uln,
                                context_name="<module>",
                                context_kind="module",
                                snippet=self.extract_snippet(importer_lines, s, e),
                                snippet_start=s,
                                snippet_end=e,
                                next_entity=next_entity,
                            )
                    hops.append(hop)
                    frontier.append((hop.next_entity, depth + 1))
                    expanded = True

            if not expanded:
                ext = Path(current.file_path).suffix.lower()
                if ext in self.config.extensions or self._is_module_file(ext):
                    module_ref = EntityRef(current.file_path, "<module>", "module")
                    if (module_ref.file_path, module_ref.name, module_ref.kind) not in visited:
                        frontier.append((module_ref, depth + 1))
                    else:
                        terminal_entries.append(current)
                else:
                    terminal_entries.append(current)

        return hops, terminal_entries

    def _is_module_file(self, ext: str) -> bool:
        return ext in {".py", ".rs", ".go", ".js", ".ts", ".jsx", ".tsx"}
