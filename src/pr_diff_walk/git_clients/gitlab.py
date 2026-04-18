import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from .base import GitClient


class GitLabClient(GitClient):
    def __init__(self, token: str, base_url: str = "https://gitlab.com"):
        self.token = token
        self._base_url = base_url.rstrip("/")
        self._api_url = f"{self._base_url}/api/v4"

    def _headers(self) -> Dict[str, str]:
        return {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json",
        }

    def _request_json(self, url: str) -> Any:
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitLab API error {e.code} for {url}: {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error while calling GitLab API: {e}") from e

    def _request_bytes(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitLab API error {e.code} for {url}: {body}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error while downloading archive: {e}") from e

    def _encode_repo(self, repo_name: str) -> str:
        return urllib.request.quote(repo_name, safe="")

    def get_pr(self, repo_name: str, pr_num: int) -> Dict[str, Any]:
        encoded = self._encode_repo(repo_name)
        return self._request_json(f"{self._api_url}/projects/{encoded}/merge_requests/{pr_num}")

    def get_pr_files(self, repo_name: str, pr_num: int) -> List[Dict[str, Any]]:
        encoded = self._encode_repo(repo_name)
        changes = self._request_json(
            f"{self._api_url}/projects/{encoded}/merge_requests/{pr_num}/changes"
        )
        if "changes" in changes:
            return changes["changes"]
        return []

    def download_head_snapshot(self, repo_name: str, head_sha: str, temp_dir: Path) -> Path:
        encoded = self._encode_repo(repo_name)
        url = f"{self._api_url}/projects/{encoded}/repository/archive.zip?sha={head_sha}"
        blob = self._request_bytes(url)
        archive = temp_dir / "head.zip"
        archive.write_bytes(blob)
        extract_root = temp_dir / "repo"
        extract_root.mkdir(parents=True, exist_ok=True)
        import zipfile
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(path=extract_root)
        roots = [p for p in extract_root.iterdir() if p.is_dir()]
        if not roots:
            raise RuntimeError("Downloaded archive did not contain project files.")
        return roots[0]