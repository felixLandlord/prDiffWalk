import os
from pathlib import Path
from typing import Dict, Optional


def resolve_token(
    provider: str,
    arg_token: Optional[str] = None,
    env_dir: Optional[Path] = None,
) -> str:
    if arg_token:
        return arg_token

    env_keys = {
        "github": ["GITHUB_TOKEN", "GH_TOKEN"],
        "gitlab": ["GITLAB_TOKEN", "GL_TOKEN"],
    }

    keys = env_keys.get(provider.lower(), [])
    for key in keys:
        if os.environ.get(key):
            return os.environ[key]

    search_dirs = []
    if env_dir:
        search_dirs.append(env_dir)
    search_dirs.append(Path.cwd())

    env_file_map = {
        "github": ["GITHUB_TOKEN", "GH_TOKEN"],
        "gitlab": ["GITLAB_TOKEN", "GL_TOKEN"],
    }

    for directory in search_dirs:
        if directory is None:
            continue
        env_path = directory / ".env"
        if env_path.exists():
            tokens = _parse_env_file(env_path)
            for key in env_file_map.get(provider.lower(), []):
                if tokens.get(key):
                    return tokens[key]

    raise ValueError(
        f"Token not found for {provider}. Provide it as a parameter, set "
        f"{env_file_map.get(provider.lower(), ['TOKEN'])} environment variable, "
        f"or include it in a .env file."
    )


def _parse_env_file(env_path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    try:
        for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return out
