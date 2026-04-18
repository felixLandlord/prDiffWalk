import io
import tarfile
import urllib.error
from unittest.mock import MagicMock, patch
import pytest
from pathlib import Path


class TestGitHubClient:
    def test_init(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        client = GitHubClient(token="test_token")
        assert client.token == "test_token"
        assert client._base_url == "https://api.github.com"

    def test_headers(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        client = GitHubClient(token="test_token")
        headers = client._headers("application/json")

        assert "Authorization" in headers
        assert "Bearer test_token" in headers["Authorization"]
        assert headers["User-Agent"] == "pr-diff-walk"

    def test_request_json_success(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b'{"title": "Test PR", "number": 123}'

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitHubClient(token="test_token")
            result = client._request_json("https://api.github.com/repos/owner/repo/pulls/1")

            assert result == {"title": "Test PR", "number": 123}

    def test_request_json_http_error(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        error = urllib.error.HTTPError(
            url="https://api.github.com/repos/owner/repo/pulls/1",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(b'{"message": "Not Found"}'),
        )

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(side_effect=error)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitHubClient(token="test_token")
            with pytest.raises(RuntimeError, match="GitHub API error 404"):
                client._request_json("https://api.github.com/repos/owner/repo/pulls/1")

    def test_request_json_url_error(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
            client = GitHubClient(token="test_token")
            with pytest.raises(RuntimeError, match="Network error"):
                client._request_json("https://api.github.com/repos/owner/repo/pulls/1")

    def test_request_bytes_success(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b"fake tarball data"

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitHubClient(token="test_token")
            result = client._request_bytes("https://api.github.com/repos/owner/repo/tarball/sha123")

            assert result == b"fake tarball data"

    def test_request_bytes_http_error(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        error = urllib.error.HTTPError(
            url="https://api.github.com/repos/owner/repo/tarball/sha123",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=io.BytesIO(b'{"message": "Forbidden"}'),
        )

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(side_effect=error)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitHubClient(token="test_token")
            with pytest.raises(RuntimeError, match="GitHub API error 403"):
                client._request_bytes("https://api.github.com/repos/owner/repo/tarball/sha123")

    def test_request_bytes_url_error(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
            client = GitHubClient(token="test_token")
            with pytest.raises(RuntimeError, match="Network error"):
                client._request_bytes("https://api.github.com/repos/owner/repo/tarball/sha123")

    def test_get_pr(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b'{"title": "Test PR", "number": 42, "state": "open"}'

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitHubClient(token="test_token")
            result = client.get_pr("myorg/myrepo", 42)

            assert result == {"title": "Test PR", "number": 42, "state": "open"}

    def test_get_pr_files_single_page(self):
        from pr_diff_walk.git_clients.github import GitHubClient
        import json

        mock_files = [
            {"filename": "src/main.py", "status": "modified"},
            {"filename": "tests/test_main.py", "status": "added"},
        ]
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = json.dumps(mock_files).encode()

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitHubClient(token="test_token")
            result = client.get_pr_files("owner/repo", 1)

            assert len(result) == 2
            assert result[0]["filename"] == "src/main.py"

    def test_get_pr_files_pagination(self):
        from pr_diff_walk.git_clients.github import GitHubClient
        import json

        page1 = [{"filename": f"file_{i}.py"} for i in range(100)]
        page2 = [{"filename": "file_extra.py"}]

        call_count = [0]

        def mock_urlopen(url, timeout=None):
            call_count[0] += 1
            mock_resp = MagicMock()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            url_str = url.full_url if hasattr(url, "full_url") else str(url)
            if call_count[0] == 1:
                mock_resp.read.return_value = json.dumps(page1).encode()
            else:
                mock_resp.read.return_value = json.dumps(page2).encode()
            return mock_resp

        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            client = GitHubClient(token="test_token")
            result = client.get_pr_files("owner/repo", 1)

            assert len(result) == 101
            assert result[-1]["filename"] == "file_extra.py"
            assert call_count[0] == 2

    def test_get_pr_files_empty(self):
        from pr_diff_walk.git_clients.github import GitHubClient

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b"[]"

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitHubClient(token="test_token")
            result = client.get_pr_files("owner/repo", 1)

            assert result == []

    def test_download_head_snapshot(self, tmp_path):
        from pr_diff_walk.git_clients.github import GitHubClient

        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tf:
            info = tarfile.TarInfo(name="repo-abc123/src/main.py")
            content = b"print('hello')"
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))

        tar_buffer.seek(0)
        tar_bytes = tar_buffer.read()
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = tar_bytes

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitHubClient(token="test_token")
            result = client.download_head_snapshot("owner/repo", "abc123", tmp_path)

            assert result.exists()
            assert (result / "src" / "main.py").exists()


class TestGitLabClient:
    def test_init(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        client = GitLabClient(token="test_token")
        assert client.token == "test_token"
        assert client._base_url == "https://gitlab.com"

    def test_init_custom_url(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        client = GitLabClient(token="test_token", base_url="https://gitlab.mycompany.com")
        assert client._base_url == "https://gitlab.mycompany.com"
        assert client._api_url == "https://gitlab.mycompany.com/api/v4"

    def test_headers(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        client = GitLabClient(token="test_token")
        headers = client._headers()

        assert "PRIVATE-TOKEN" in headers
        assert headers["PRIVATE-TOKEN"] == "test_token"

    def test_encode_repo(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        client = GitLabClient(token="test_token")
        assert client._encode_repo("group/project") == "group%2Fproject"

    def test_request_json_success(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b'{"title": "Test MR", "number": 123}'

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitLabClient(token="test_token")
            result = client._request_json("https://gitlab.com/api/v4/projects/1")

            assert result == {"title": "Test MR", "number": 123}

    def test_request_json_http_error(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        error = urllib.error.HTTPError(
            url="https://gitlab.com/api/v4/projects/1",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(b'{"message": "Not Found"}'),
        )

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(side_effect=error)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitLabClient(token="test_token")
            with pytest.raises(RuntimeError, match="GitLab API error 404"):
                client._request_json("https://gitlab.com/api/v4/projects/1")

    def test_request_json_url_error(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
            client = GitLabClient(token="test_token")
            with pytest.raises(RuntimeError, match="Network error"):
                client._request_json("https://gitlab.com/api/v4/projects/1")

    def test_request_bytes_success(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b"fake archive data"

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitLabClient(token="test_token")
            result = client._request_bytes("https://gitlab.com/api/v4/archive")

            assert result == b"fake archive data"

    def test_request_bytes_http_error(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        error = urllib.error.HTTPError(
            url="https://gitlab.com/api/v4/archive",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=io.BytesIO(b'{"message": "Forbidden"}'),
        )

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(side_effect=error)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitLabClient(token="test_token")
            with pytest.raises(RuntimeError, match="GitLab API error 403"):
                client._request_bytes("https://gitlab.com/api/v4/archive")

    def test_request_bytes_url_error(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
            client = GitLabClient(token="test_token")
            with pytest.raises(RuntimeError, match="Network error"):
                client._request_bytes("https://gitlab.com/api/v4/archive")

    def test_get_pr(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b'{"title": "Test MR", "number": 42, "state": "opened"}'

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitLabClient(token="test_token")
            result = client.get_pr("owner/repo", 42)

            assert result == {"title": "Test MR", "number": 42, "state": "opened"}

    def test_get_pr_files(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        mock_changes = {"changes": [
            {"new_path": "src/main.py", "old_path": "src/main.py", "diff": "@@ -1,3 +1,4 @@"},
            {"new_path": "tests/test_main.py", "old_path": "", "diff": "@@ -0,0 +1,3 @@"},
        ]}
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = str(mock_changes).replace("'", '"').encode()

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitLabClient(token="test_token")
            result = client.get_pr_files("owner/repo", 1)

            assert len(result) == 2
            assert result[0]["new_path"] == "src/main.py"

    def test_get_pr_files_no_changes(self):
        from pr_diff_walk.git_clients.gitlab import GitLabClient

        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = b'{"changes": []}'

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitLabClient(token="test_token")
            result = client.get_pr_files("owner/repo", 1)

            assert result == []

    def test_download_head_snapshot(self, tmp_path):
        from pr_diff_walk.git_clients.gitlab import GitLabClient
        import zipfile

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("repo-abc123/src/main.py", "print('hello')")

        zip_buffer.seek(0)
        zip_bytes = zip_buffer.read()
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.read.return_value = zip_bytes

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = GitLabClient(token="test_token")
            result = client.download_head_snapshot("owner/repo", "abc123", tmp_path)

            assert result.exists()
            assert (result / "src" / "main.py").exists()


class TestTokenResolver:
    def test_resolve_token_from_arg(self):
        from pr_diff_walk.git_clients.token_resolver import resolve_token

        token = resolve_token("github", arg_token="my_token")
        assert token == "my_token"

    def test_resolve_token_from_env(self, monkeypatch):
        from pr_diff_walk.git_clients.token_resolver import resolve_token

        monkeypatch.setenv("GITHUB_TOKEN", "env_token")
        token = resolve_token("github")
        assert token == "env_token"

    def test_resolve_token_gitlab_env(self, monkeypatch):
        from pr_diff_walk.git_clients.token_resolver import resolve_token

        monkeypatch.setenv("GITLAB_TOKEN", "gitlab_env_token")
        token = resolve_token("gitlab")
        assert token == "gitlab_env_token"

    def test_resolve_token_not_found(self):
        from pr_diff_walk.git_clients.token_resolver import resolve_token

        with pytest.raises(ValueError, match="Token not found"):
            resolve_token("github", arg_token=None)


class TestGetGitClient:
    def test_get_github_client(self):
        from pr_diff_walk.git_clients import get_git_client, GitHubClient

        client = get_git_client("github", "test_token")
        assert isinstance(client, GitHubClient)

    def test_get_gitlab_client(self):
        from pr_diff_walk.git_clients import get_git_client, GitLabClient

        client = get_git_client("gitlab", "test_token")
        assert isinstance(client, GitLabClient)

    def test_get_unknown_provider(self):
        from pr_diff_walk.git_clients import get_git_client

        with pytest.raises(ValueError, match="Unknown provider"):
            get_git_client("bitbucket", "test_token")
