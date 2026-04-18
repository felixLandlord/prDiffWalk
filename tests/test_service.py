import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock


class TestServicePackageUsage:
    def test_import_package(self):
        import pr_diff_walk
        assert hasattr(pr_diff_walk, "DiffChainService")
        assert hasattr(pr_diff_walk, "analyze_pr")

    def test_import_schemas(self):
        from pr_diff_walk import (
            EntityRef,
            EntityDef,
            ImportEdge,
            Hop,
            ChangedEntity,
            DependencyChain,
            AnalysisResult,
            LanguageConfig,
            RepositoryFiles,
        )

        assert EntityRef is not None
        assert EntityDef is not None
        assert ImportEdge is not None

    def test_import_git_clients(self):
        from pr_diff_walk import GitClient, GitHubClient, GitLabClient, get_git_client

        assert GitClient is not None
        assert GitHubClient is not None
        assert GitLabClient is not None

    def test_import_language_integration(self):
        from pr_diff_walk import LanguageIntegration

        assert LanguageIntegration is not None


class TestAnalyzePrFunction:
    def test_analyze_pr_returns_dict(self):
        from pr_diff_walk.service import analyze_pr

        with patch("pr_diff_walk.service.DiffChainService") as MockService:
            mock_instance = Mock()
            mock_instance.analyze.return_value = MagicMock()
            mock_instance.generate_report.return_value = "# Test Report"
            MockService.return_value = mock_instance

            result = analyze_pr(
                repo_name="owner/repo",
                pr_num=1,
                integrations=["javascript"],
                provider="github",
            )

            assert "data" in result or "report" in result


class TestDiffChainServiceInit:
    def test_init_with_integrations(self):
        from pr_diff_walk.service import DiffChainService

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            with patch("pr_diff_walk.service.get_git_client"):
                service = DiffChainService(
                    repo_name="owner/repo",
                    pr_num=1,
                    integrations=["javascript", "python"],
                    provider="github",
                )

                assert service.repo_name == "owner/repo"
                assert service.pr_num == 1
                assert len(service._integrations) == 2

    def test_init_default_provider(self):
        from pr_diff_walk.service import DiffChainService

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            with patch("pr_diff_walk.service.get_git_client"):
                service = DiffChainService(
                    repo_name="owner/repo",
                    pr_num=1,
                )

                assert service.provider == "github"

    def test_init_gitlab(self):
        from pr_diff_walk.service import DiffChainService

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            with patch("pr_diff_walk.service.get_git_client"):
                service = DiffChainService(
                    repo_name="owner/repo",
                    pr_num=1,
                    provider="gitlab",
                    gitlab_url="https://gitlab.mycompany.com",
                )

                assert service.provider == "gitlab"


class TestServiceMethods:
    def test_read_lines(self, temp_repo_dir):
        from pr_diff_walk.service import DiffChainService

        test_file = temp_repo_dir / "test.txt"
        test_file.write_text("line1\nline2\nline3")

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            with patch("pr_diff_walk.service.get_git_client"):
                service = DiffChainService(repo_name="owner/repo", pr_num=1)
                lines = service._read_lines(test_file)

                assert len(lines) == 3
                assert lines[0] == "line1"

    def test_read_lines_missing_file(self, temp_repo_dir):
        from pr_diff_walk.service import DiffChainService

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            with patch("pr_diff_walk.service.get_git_client"):
                service = DiffChainService(repo_name="owner/repo", pr_num=1)
                lines = service._read_lines(temp_repo_dir / "nonexistent.txt")

                assert lines == []

    def test_relpath(self, temp_repo_dir):
        from pr_diff_walk.service import DiffChainService

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            with patch("pr_diff_walk.service.get_git_client"):
                service = DiffChainService(repo_name="owner/repo", pr_num=1)
                result = service._relpath(temp_repo_dir, temp_repo_dir / "src" / "main.js")

                assert result == "src/main.js"

    def test_build_pr_diff_text(self, temp_repo_dir, sample_pr_files):
        from pr_diff_walk.service import DiffChainService

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            with patch("pr_diff_walk.service.get_git_client"):
                service = DiffChainService(repo_name="owner/repo", pr_num=1)
                diff_text = service._build_pr_diff_text(sample_pr_files)

                assert "diff -- src/utils.js" in diff_text
                assert "modified" in diff_text

    def test_format_full_file_content(self, temp_repo_dir):
        from pr_diff_walk.service import DiffChainService

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            with patch("pr_diff_walk.service.get_git_client"):
                service = DiffChainService(repo_name="owner/repo", pr_num=1)
                content = service._format_full_file_content(["line1", "line2"])

                assert "1" in content
                assert "line1" in content

    def test_format_full_file_content_empty(self, temp_repo_dir):
        from pr_diff_walk.service import DiffChainService

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            with patch("pr_diff_walk.service.get_git_client"):
                service = DiffChainService(repo_name="owner/repo", pr_num=1)
                content = service._format_full_file_content([])

                assert "(empty file)" in content


class TestServiceAnalyze:
    def test_analyze_auto_detects_integrations(self, sample_js_files, sample_pr_files, temp_repo_dir):
        from pr_diff_walk.service import DiffChainService

        with patch("pr_diff_walk.service.resolve_token", return_value="test_token"):
            mock_client = MagicMock()
            mock_client.get_pr.return_value = {
                "head": {"sha": "abc123"},
                "base": {"ref": "main"},
            }
            mock_client.get_pr_files.return_value = sample_pr_files
            mock_client.download_head_snapshot.return_value = temp_repo_dir

            with patch("pr_diff_walk.service.get_git_client", return_value=mock_client):
                service = DiffChainService(
                    repo_name="owner/repo",
                    pr_num=1,
                )
                result = service.analyze()

                assert result.repo_name == "owner/repo"
                assert result.pr_num == 1
