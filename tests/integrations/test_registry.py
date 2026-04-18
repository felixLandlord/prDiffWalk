import pytest


class TestIntegrationsRegistry:
    def test_get_integration_javascript(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("javascript")
        assert integration.config.name == "javascript"

    def test_get_integration_js_alias(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("js")
        assert integration.config.name == "javascript"

    def test_get_integration_python(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("python")
        assert integration.config.name == "python"

    def test_get_integration_rust(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("rust")
        assert integration.config.name == "rust"

    def test_get_integration_go(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("go")
        assert integration.config.name == "go"

    def test_get_integration_java(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("java")
        assert integration.config.name == "java"

    def test_get_integration_csharp(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("csharp")
        assert integration.config.name == "csharp"

    def test_get_integration_dart(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("dart")
        assert integration.config.name == "dart"

    def test_get_integration_swift(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("swift")
        assert integration.config.name == "swift"

    def test_get_integration_kotlin(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("kotlin")
        assert integration.config.name == "kotlin"

    def test_get_integration_c(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("c")
        assert integration.config.name == "c"

    def test_get_integration_cpp(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("cpp")
        assert integration.config.name == "cpp"

    def test_get_integration_zig(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("zig")
        assert integration.config.name == "zig"

    def test_get_integration_php(self):
        from pr_diff_walk.integrations import get_integration

        integration = get_integration("php")
        assert integration.config.name == "php"

    def test_get_integration_unknown(self):
        from pr_diff_walk.integrations import get_integration

        with pytest.raises(ValueError, match="Unknown integration"):
            get_integration("unknown_lang")

    def test_detect_integrations_from_files(self):
        from pr_diff_walk.integrations import detect_integrations_from_files

        files = ["src/utils.js", "src/main.py", "src/types.ts", "README.md"]
        detected = detect_integrations_from_files(files)

        assert "javascript" in detected
        assert "python" in detected
        assert "typescript" in detected

    def test_detect_integrations_from_extensions(self):
        from pr_diff_walk.integrations import detect_integrations_from_extensions

        extensions = {".js", ".py", ".go"}
        detected = detect_integrations_from_extensions(extensions)

        assert "javascript" in detected
        assert "python" in detected
        assert "go" in detected

    def test_available_integrations(self):
        from pr_diff_walk.integrations import AVAILABLE_INTEGRATIONS

        assert "javascript" in AVAILABLE_INTEGRATIONS
        assert "python" in AVAILABLE_INTEGRATIONS
        assert "rust" in AVAILABLE_INTEGRATIONS
        assert "go" in AVAILABLE_INTEGRATIONS

    def test_extension_to_integration(self):
        from pr_diff_walk.integrations import EXTENSION_TO_INTEGRATION

        assert EXTENSION_TO_INTEGRATION[".js"] == "javascript"
        assert EXTENSION_TO_INTEGRATION[".py"] == "python"
        assert EXTENSION_TO_INTEGRATION[".rs"] == "rust"
        assert EXTENSION_TO_INTEGRATION[".go"] == "go"


class TestMixedLanguageScenario:
    def test_detect_multiple_languages(self, sample_mixed_files):
        from pr_diff_walk.integrations import detect_integrations_from_files

        files = list(sample_mixed_files.keys())
        detected = detect_integrations_from_files(files)

        assert "javascript" in detected
        assert "python" in detected

    def test_iterate_mixed_files(self, sample_mixed_files, temp_repo_dir):
        from pr_diff_walk.integrations.javascript import JavascriptIntegration
        from pr_diff_walk.integrations.python import PythonIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        js_integration = JavascriptIntegration()
        py_integration = PythonIntegration()

        repo = RepositoryFiles(root=temp_repo_dir)

        js_files = list(js_integration.iter_code_files(temp_repo_dir, repo))
        py_files = list(py_integration.iter_code_files(temp_repo_dir, repo))

        assert any("helper.js" in str(f) for f in js_files)
        assert any("utils.py" in str(f) for f in py_files)
