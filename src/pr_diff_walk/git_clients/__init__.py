from pr_diff_walk.git_clients.base import GitClient
from pr_diff_walk.git_clients.github import GitHubClient
from pr_diff_walk.git_clients.gitlab import GitLabClient

PROVIDERS = {
    "github": GitHubClient,
    "gitlab": GitLabClient,
}


def get_git_client(provider: str, token: str, **kwargs) -> GitClient:
    provider = provider.lower()
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[provider](token, **kwargs)


__all__ = ["GitClient", "GitHubClient", "GitLabClient", "get_git_client", "PROVIDERS"]