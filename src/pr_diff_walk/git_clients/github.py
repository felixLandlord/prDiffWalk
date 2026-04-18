import json
import tarfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from .base import GitClient


class GitHubClient(GitClient):
    def __init__(self, token: str):
        self.token = token
        self._base_url = "https://api.github.com"

    def _headers(self, accept: str) -> Dict[str, str]:
        return {
            "Accept": accept,
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "pr-diff-walk",
        }

    def _request_json(self, url: str, accept: str = "application/vnd.github+json") -> Any:
        req = urllib.request.Request(url, headers=self._headers(accept), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API error {e.code} for {url}: {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error while calling GitHub API: {e}") from e

    def _request_bytes(self, url: str, accept: str = "application/octet-stream") -> bytes:
        req = urllib.request.Request(url, headers=self._headers(accept), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API error {e.code} for {url}: {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error while downloading archive: {e}") from e

    def get_pr(self, repo_name: str, pr_num: int) -> Dict[str, Any]:
        return self._request_json(f"{self._base_url}/repos/{repo_name}/pulls/{pr_num}")

    def get_pr_files(self, repo_name: str, pr_num: int) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        page = 1
        while True:
            data = self._request_json(
                f"{self._base_url}/repos/{repo_name}/pulls/{pr_num}/files?per_page=100&page={page}"
            )
            if not isinstance(data, list) or not data:
                break
            out.extend(data)
            if len(data) < 100:
                break
            page += 1
        return out

    def download_head_snapshot(self, repo_name: str, head_sha: str, temp_dir: Path) -> Path:
        blob = self._request_bytes(
            f"{self._base_url}/repos/{repo_name}/tarball/{head_sha}",
            accept="application/vnd.github+json",
        )
        archive = temp_dir / "head.tar.gz"
        archive.write_bytes(blob)
        extract_root = temp_dir / "repo"
        extract_root.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, mode="r:gz") as tf:
            tf.extractall(path=extract_root, filter="data")
        roots = [p for p in extract_root.iterdir() if p.is_dir()]
        if not roots:
            raise RuntimeError("Downloaded archive did not contain project files.")
        return roots[0]