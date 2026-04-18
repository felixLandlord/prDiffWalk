from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class EntityRef:
    file_path: str
    name: str
    kind: str


@dataclass
class EntityDef:
    name: str
    kind: str
    start: int
    end: int
    parent: Optional[str] = None


@dataclass
class ImportEdge:
    importer_file: str
    source_file: str
    imported_name: Optional[str]
    alias: str
    line_no: int
    lang: str


@dataclass
class Hop:
    depth: int
    from_entity: EntityRef
    importer_file: str
    imported_as: str
    line_no: int
    context_name: str
    context_kind: str
    snippet: str
    snippet_start: int
    snippet_end: int
    next_entity: EntityRef


@dataclass
class ChangedEntity:
    entity: EntityRef
    from_patch_lines: List[int]


@dataclass
class DependencyChain:
    seed: EntityRef
    hops: List[Hop]
    terminals: List[EntityRef]


@dataclass
class AnalysisResult:
    repo_name: str
    pr_num: int
    head_ref: str
    base_ref: str
    pr_diff: str
    chains: List[DependencyChain]
    files_lines: Dict[str, List[str]]
    integration_name: str = "unknown"


@dataclass
class RepositoryFiles:
    root: Path
    files_lines: Dict[str, List[str]] = field(default_factory=dict)
    files_entities: Dict[str, List[EntityDef]] = field(default_factory=dict)
    repo_files: Set[str] = field(default_factory=set)
    all_import_edges: List[ImportEdge] = field(default_factory=list)
    imports_by_source: Dict[str, List[ImportEdge]] = field(default_factory=dict)
    excluded_dirs: Set[str] = field(default_factory=lambda: {
        ".git",
        "node_modules",
        "dist",
        "build",
        ".next",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".idea",
        ".vscode",
        "target",
        "pkg",
        "bin",
        "obj",
        ".gradle",
        ".dart_tool",
        "Pods",
        ".build",
        "vendor",
    })


@dataclass
class LanguageConfig:
    name: str
    extensions: Set[str]
    file_patterns: List[str]
    module_marker: str
    package_indicator: str
    import_patterns: Dict[str, str]
    entity_kinds: Set[str]
