from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class GitClient(ABC):
    @abstractmethod
    def get_pr(self, repo_name: str, pr_num: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_pr_files(self, repo_name: str, pr_num: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def download_head_snapshot(self, repo_name: str, head_sha: str, temp_dir: Path) -> Path:
        pass