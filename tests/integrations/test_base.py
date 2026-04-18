import pytest


class TestBaseIntegration:
    def test_find_usage_lines(self):
        from pr_diff_walk.base import LanguageIntegration
        from pr_diff_walk.integrations.javascript import JavascriptIntegration

        integration = JavascriptIntegration()
        lines = [
            "export function add(a, b) {",
            "    return a + b;",
            "}",
            "export const result = add(1, 2);",
        ]

        usage = integration.find_usage_lines(lines, "add", 1, None)

        assert 4 in usage

    def test_smallest_enclosing_entity(self):
        from pr_diff_walk.base import LanguageIntegration
        from pr_diff_walk.integrations.javascript import JavascriptIntegration
        from pr_diff_walk.schemas import EntityDef

        integration = JavascriptIntegration()
        entities = [
            EntityDef(name="MyClass", kind="class", start=1, end=10),
            EntityDef(name="method", kind="method", start=3, end=5, parent="MyClass"),
        ]

        result = integration.smallest_enclosing_entity(entities, 4)

        assert result is not None
        assert result.name == "method"

    def test_extract_snippet(self):
        from pr_diff_walk.base import LanguageIntegration
        from pr_diff_walk.integrations.javascript import JavascriptIntegration

        integration = JavascriptIntegration()
        lines = ["line1", "line2", "line3", "line4", "line5"]

        snippet = integration.extract_snippet(lines, 2, 4)
        assert "2" in snippet
        assert "line2" in snippet

    def test_extract_changed_line_numbers_from_patch(self):
        from pr_diff_walk.base import LanguageIntegration
        from pr_diff_walk.integrations.javascript import JavascriptIntegration

        integration = JavascriptIntegration()
        patch = """@@ -1,5 +1,7 @@
 line1
-line2
+new line2
+new line3
 line3
"""

        lines = integration.extract_changed_line_numbers_from_patch(patch)
        assert len(lines) >= 1

    def test_changed_entities_from_patch(self):
        from pr_diff_walk.base import LanguageIntegration
        from pr_diff_walk.integrations.javascript import JavascriptIntegration
        from pr_diff_walk.schemas import EntityDef

        integration = JavascriptIntegration()
        entities = [
            EntityDef(name="add", kind="function", start=1, end=3),
        ]
        patch_lines = [2]

        changed = integration.changed_entities_from_patch("test.js", patch_lines, entities)

        assert len(changed) == 1
        assert changed[0].entity.name == "add"


class TestCommonExclusions:
    def test_general_excluded_dirs(self):
        from pr_diff_walk.integrations.common import GENERAL_EXCLUDED_DIRS

        assert ".git" in GENERAL_EXCLUDED_DIRS
        assert "node_modules" in GENERAL_EXCLUDED_DIRS
        assert ".venv" in GENERAL_EXCLUDED_DIRS

    def test_general_excluded_files(self):
        from pr_diff_walk.integrations.common import GENERAL_EXCLUDED_FILES

        assert ".DS_Store" in GENERAL_EXCLUDED_FILES
        assert "package-lock.json" in GENERAL_EXCLUDED_FILES
        assert "Cargo.lock" in GENERAL_EXCLUDED_FILES

    def test_language_specific_excluded_dirs(self):
        from pr_diff_walk.integrations.common import (
            JS_EXCLUDED_DIRS,
            TS_EXCLUDED_DIRS,
            CSS_EXCLUDED_DIRS,
        )

        assert "coverage" in JS_EXCLUDED_DIRS
        assert "tsconfig.build" in TS_EXCLUDED_DIRS
        assert ".sass_cache" in CSS_EXCLUDED_DIRS
