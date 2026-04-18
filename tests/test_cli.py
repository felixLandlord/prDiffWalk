import pytest
from click.testing import CliRunner
from typer.testing import CliRunner as TyperRunner


class TestCLICommands:
    def test_cli_import(self):
        from pr_diff_walk.cli import app
        assert app is not None

    def test_list_command(self):
        from pr_diff_walk.cli import app

        runner = TyperRunner()
        result = runner.invoke(app, ["list"])

        assert result.exit_code == 0
        assert "Available Language Integrations" in result.output

    def test_list_command_shows_languages(self):
        from pr_diff_walk.cli import app

        runner = TyperRunner()
        result = runner.invoke(app, ["list"])

        assert "JavaScript" in result.output
        assert "Python" in result.output
        assert "Rust" in result.output
        assert "Go" in result.output

    def test_analyze_command_help(self):
        from pr_diff_walk.cli import app

        runner = TyperRunner()
        result = runner.invoke(app, ["analyze", "--help"])

        assert result.exit_code == 0
        assert "Repository" in result.output
        assert "PR/MR" in result.output

    def test_report_command_help(self):
        from pr_diff_walk.cli import app

        runner = TyperRunner()
        result = runner.invoke(app, ["report", "--help"])

        assert result.exit_code == 0

    def test_quick_command_help(self):
        from pr_diff_walk.cli import app

        runner = TyperRunner()
        result = runner.invoke(app, ["quick", "--help"])

        assert result.exit_code == 0


class TestCLIEdgeCases:
    def test_parse_integrations_single(self):
        from pr_diff_walk.cli import parse_integrations

        result = parse_integrations("python")
        assert result == ["python"]

    def test_parse_integrations_multiple_space_separated(self):
        from pr_diff_walk.cli import parse_integrations

        result = parse_integrations("python javascript rust")
        assert result == ["python", "javascript", "rust"]

    def test_parse_integrations_comma_separated(self):
        from pr_diff_walk.cli import parse_integrations

        result = parse_integrations("python,javascript,rust")
        assert result == ["python", "javascript", "rust"]

    def test_parse_integrations_mixed_separators(self):
        from pr_diff_walk.cli import parse_integrations

        result = parse_integrations("python, javascript rust")
        assert result == ["python", "javascript", "rust"]

    def test_parse_integrations_with_spaces(self):
        from pr_diff_walk.cli import parse_integrations

        result = parse_integrations("  python  javascript  ")
        assert result == ["python", "javascript"]

    def test_parse_integrations_none(self):
        from pr_diff_walk.cli import parse_integrations

        result = parse_integrations(None)
        assert result is None

    def test_parse_integrations_empty(self):
        from pr_diff_walk.cli import parse_integrations

        result = parse_integrations("")
        assert result is None

    def test_parse_integrations_case_normalization(self):
        from pr_diff_walk.cli import parse_integrations

        result = parse_integrations("PYTHON JavaScript")
        assert result == ["python", "javascript"]
