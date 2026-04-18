from .base import LanguageIntegration
from .schemas import (
    AnalysisResult,
    ChangedEntity,
    DependencyChain,
    EntityDef,
    EntityRef,
    Hop,
    ImportEdge,
    LanguageConfig,
    RepositoryFiles,
)
from .integrations import (
    AVAILABLE_INTEGRATIONS,
    LANGUAGE_TO_INTEGRATION,
    EXTENSION_TO_INTEGRATION,
    get_integration,
    detect_integrations_from_files,
    detect_integrations_from_extensions,
)
from .git_clients import GitClient, GitHubClient, GitLabClient, get_git_client
from .service import DiffChainService, analyze_pr

__version__ = "0.1.0"
__all__ = [
    "DiffChainService",
    "analyze_pr",
    "LanguageIntegration",
    "GitClient",
    "GitHubClient",
    "GitLabClient",
    "get_git_client",
    "AnalysisResult",
    "ChangedEntity",
    "DependencyChain",
    "EntityDef",
    "EntityRef",
    "Hop",
    "ImportEdge",
    "LanguageConfig",
    "RepositoryFiles",
    "AVAILABLE_INTEGRATIONS",
    "LANGUAGE_TO_INTEGRATION",
    "EXTENSION_TO_INTEGRATION",
    "get_integration",
    "detect_integrations_from_files",
    "detect_integrations_from_extensions",
]
