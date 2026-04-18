import pytest


class TestJavascriptIntegration:
    def test_iter_code_files(self, sample_js_files, temp_repo_dir):
        from pr_diff_walk.integrations.javascript import JavascriptIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = JavascriptIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 3

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.javascript import JavascriptIntegration

        integration = JavascriptIntegration()
        lines = ["import { add } from './utils.js';"]
        repo_files = {"src/utils.js", "src/index.js", "src/components/Button.jsx"}

        edges = integration.parse_imports("src/index.js", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.javascript import JavascriptIntegration

        integration = JavascriptIntegration()
        lines = [
            "export function add(a, b) {",
            "    return a + b;",
            "}",
            "export const PI = 3.14;",
        ]

        entities = integration.parse_entities("src/utils.js", lines)
        assert len(entities) >= 1

    def test_resolve_import_to_file(self):
        from pr_diff_walk.integrations.javascript import JavascriptIntegration

        integration = JavascriptIntegration()
        repo_files = {"src/utils.js", "src/index.js", "src/components/Button.jsx"}

        result = integration.resolve_import_to_file("src/index.js", "./utils.js", repo_files)
        assert result == "src/utils.js"

    def test_config(self):
        from pr_diff_walk.integrations.javascript import JavascriptIntegration

        integration = JavascriptIntegration()
        assert integration.config.name == "javascript"
        assert ".js" in integration.config.extensions


class TestTypescriptIntegration:
    def test_iter_code_files(self, sample_ts_files, temp_repo_dir):
        from pr_diff_walk.integrations.typescript import TypescriptIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = TypescriptIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 3

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.typescript import TypescriptIntegration

        integration = TypescriptIntegration()
        lines = ["import { User, Status } from './types';"]
        repo_files = {"src/types.ts", "src/service.ts", "src/app.tsx"}

        edges = integration.parse_imports("src/service.ts", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.typescript import TypescriptIntegration

        integration = TypescriptIntegration()
        lines = [
            "export interface User {",
            "    id: number;",
            "    name: string;",
            "}",
            "export type Status = 'active' | 'inactive';",
        ]

        entities = integration.parse_entities("src/types.ts", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.typescript import TypescriptIntegration

        integration = TypescriptIntegration()
        assert integration.config.name == "typescript"
        assert ".ts" in integration.config.extensions


class TestHtmlIntegration:
    def test_iter_code_files(self, sample_html_files, temp_repo_dir):
        from pr_diff_walk.integrations.html import HtmlIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = HtmlIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 1

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.html import HtmlIntegration

        integration = HtmlIntegration()
        content = '<link rel="stylesheet" href="styles.css">\n<script src="app.js"></script>'
        lines = content.split('\n')
        repo_files = {"index.html", "styles.css", "app.js"}

        edges = integration.parse_imports("index.html", lines, repo_files)
        assert len(edges) >= 0

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.html import HtmlIntegration

        integration = HtmlIntegration()
        content = '<div id="main" class="container"></div>'
        lines = content.split('\n')

        entities = integration.parse_entities("index.html", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.html import HtmlIntegration

        integration = HtmlIntegration()
        assert integration.config.name == "html"


class TestCssIntegration:
    def test_iter_code_files(self, sample_css_files, temp_repo_dir):
        from pr_diff_walk.integrations.css import CssIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = CssIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 2

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.css import CssIntegration

        integration = CssIntegration()
        lines = ['@import "variables.css";', '@import url("mixins.css");']
        repo_files = {"styles.css", "variables.css", "mixins.css"}

        edges = integration.parse_imports("styles.css", lines, repo_files)
        assert len(edges) >= 0

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.css import CssIntegration

        integration = CssIntegration()
        lines = [
            ".class-name {",
            "    color: red;",
            "}",
        ]

        entities = integration.parse_entities("styles.css", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.css import CssIntegration

        integration = CssIntegration()
        assert integration.config.name == "css"


class TestPythonIntegration:
    def test_iter_code_files(self, sample_python_files, temp_repo_dir):
        from pr_diff_walk.integrations.python import PythonIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = PythonIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 4

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.python import PythonIntegration

        integration = PythonIntegration()
        lines = ["from utils import add", "import os"]
        repo_files = {"utils.py", "__init__.py", "src/main.py"}

        edges = integration.parse_imports("src/main.py", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.python import PythonIntegration

        integration = PythonIntegration()
        lines = [
            "class User:",
            "    pass",
            "",
            "def add(a, b):",
            "    return a + b",
            "",
            "PI = 3.14",
        ]

        entities = integration.parse_entities("utils.py", lines)
        assert len(entities) >= 1

    def test_resolve_import_to_file(self):
        from pr_diff_walk.integrations.python import PythonIntegration

        integration = PythonIntegration()
        repo_files = {"utils.py", "src/main.py", "src/__init__.py"}

        result = integration.resolve_import_to_file("src/main.py", "utils", repo_files)
        assert result is not None

    def test_config(self):
        from pr_diff_walk.integrations.python import PythonIntegration

        integration = PythonIntegration()
        assert integration.config.name == "python"


class TestRustIntegration:
    def test_iter_code_files(self, sample_rust_files, temp_repo_dir):
        from pr_diff_walk.integrations.rust import RustIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = RustIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 3

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.rust import RustIntegration

        integration = RustIntegration()
        lines = ["use crate::add;"]
        repo_files = {"src/lib.rs", "src/main.rs", "src/math.rs"}

        edges = integration.parse_imports("src/main.rs", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.rust import RustIntegration

        integration = RustIntegration()
        lines = [
            "pub struct Calculator {",
            "    value: i32,",
            "}",
            "",
            "pub fn add(a: i32, b: i32) -> i32 {",
            "    a + b",
            "}",
            "",
            "pub const PI: f64 = 3.14;",
        ]

        entities = integration.parse_entities("src/lib.rs", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.rust import RustIntegration

        integration = RustIntegration()
        assert integration.config.name == "rust"


class TestGoIntegration:
    def test_iter_code_files(self, sample_go_files, temp_repo_dir):
        from pr_diff_walk.integrations.golang import GoIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = GoIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 3

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.golang import GoIntegration

        integration = GoIntegration()
        lines = ['import "fmt"']

        edges = integration.parse_imports("main.go", lines, set())
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.golang import GoIntegration

        integration = GoIntegration()
        lines = [
            "func Add(a, b int) int {",
            "    return a + b",
            "}",
        ]

        entities = integration.parse_entities("utils.go", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.golang import GoIntegration

        integration = GoIntegration()
        assert integration.config.name == "go"


class TestJavaIntegration:
    def test_iter_code_files(self, sample_java_files, temp_repo_dir):
        from pr_diff_walk.integrations.java import JavaIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = JavaIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 3

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.java import JavaIntegration

        integration = JavaIntegration()
        lines = ["import java.util.List;"]
        repo_files = {"Utils.java", "Main.java"}

        edges = integration.parse_imports("Main.java", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.java import JavaIntegration

        integration = JavaIntegration()
        lines = [
            "public class Utils {",
            "    public static int add(int a, int b) {",
            "        return a + b;",
            "    }",
            "}",
        ]

        entities = integration.parse_entities("Utils.java", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.java import JavaIntegration

        integration = JavaIntegration()
        assert integration.config.name == "java"


class TestCSharpIntegration:
    def test_iter_code_files(self, sample_csharp_files, temp_repo_dir):
        from pr_diff_walk.integrations.csharp import CSharpIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = CSharpIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 2

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.csharp import CSharpIntegration

        integration = CSharpIntegration()
        lines = ["using System;"]
        repo_files = {"Utils.cs", "Program.cs"}

        edges = integration.parse_imports("Program.cs", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.csharp import CSharpIntegration

        integration = CSharpIntegration()
        lines = [
            "namespace Utils {",
            "    public class Math {",
            "        public static int Add(int a, int b) => a + b;",
            "    }",
            "}",
        ]

        entities = integration.parse_entities("Utils.cs", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.csharp import CSharpIntegration

        integration = CSharpIntegration()
        assert integration.config.name == "csharp"


class TestDartIntegration:
    def test_iter_code_files(self, sample_dart_files, temp_repo_dir):
        from pr_diff_walk.integrations.dart import DartIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = DartIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 3

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.dart import DartIntegration

        integration = DartIntegration()
        lines = ["import 'utils.dart';"]
        repo_files = {"lib/utils.dart", "lib/main.dart", "lib/models/user.dart"}

        edges = integration.parse_imports("lib/main.dart", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.dart import DartIntegration

        integration = DartIntegration()
        lines = [
            "int add(int a, int b) => a + b;",
            "",
            "const pi = 3.14;",
            "",
            "class User {",
            "  String name;",
            "  int age;",
            "}",
        ]

        entities = integration.parse_entities("lib/utils.dart", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.dart import DartIntegration

        integration = DartIntegration()
        assert integration.config.name == "dart"


class TestSwiftIntegration:
    def test_iter_code_files(self, sample_swift_files, temp_repo_dir):
        from pr_diff_walk.integrations.swift import SwiftIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = SwiftIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 2

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.swift import SwiftIntegration

        integration = SwiftIntegration()
        lines = ["import Foundation"]
        repo_files = {"Sources/App/main.swift", "Sources/App/utils.swift"}

        edges = integration.parse_imports("Sources/App/main.swift", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.swift import SwiftIntegration

        integration = SwiftIntegration()
        lines = [
            "func add(_ a: Int, _ b: Int) -> Int {",
            "    return a + b",
            "}",
            "",
            "struct Point {",
            "    var x: Int",
            "    var y: Int",
            "}",
        ]

        entities = integration.parse_entities("Sources/App/utils.swift", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.swift import SwiftIntegration

        integration = SwiftIntegration()
        assert integration.config.name == "swift"


class TestKotlinIntegration:
    def test_iter_code_files(self, sample_kotlin_files, temp_repo_dir):
        from pr_diff_walk.integrations.kotlin import KotlinIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = KotlinIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 2

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.kotlin import KotlinIntegration

        integration = KotlinIntegration()
        lines = ["import java.util.List"]
        repo_files = {"Utils.kt", "Main.kt"}

        edges = integration.parse_imports("Main.kt", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.kotlin import KotlinIntegration

        integration = KotlinIntegration()
        lines = [
            "fun add(a: Int, b: Int) = a + b",
            "",
            "val pi = 3.14",
            "",
            "class Calculator {",
            "    fun calculate() = 42",
            "}",
        ]

        entities = integration.parse_entities("Utils.kt", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.kotlin import KotlinIntegration

        integration = KotlinIntegration()
        assert integration.config.name == "kotlin"


class TestCIntegration:
    def test_iter_code_files(self, sample_c_files, temp_repo_dir):
        from pr_diff_walk.integrations.c_lang import CIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = CIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 3

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.c_lang import CIntegration

        integration = CIntegration()
        lines = ['#include "utils.h"']
        repo_files = {"src/utils.h", "src/utils.c", "src/main.c"}

        edges = integration.parse_imports("src/main.c", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.c_lang import CIntegration

        integration = CIntegration()
        lines = [
            "#define PI 3.14",
            "",
            "int add(int a, int b) {",
            "    return a + b;",
            "}",
        ]

        entities = integration.parse_entities("src/utils.c", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.c_lang import CIntegration

        integration = CIntegration()
        assert integration.config.name == "c"


class TestCppIntegration:
    def test_iter_code_files(self, sample_cpp_files, temp_repo_dir):
        from pr_diff_walk.integrations.cpp import CppIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = CppIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 3

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.cpp import CppIntegration

        integration = CppIntegration()
        lines = ['#include "utils.hpp"']
        repo_files = {"include/utils.hpp", "src/main.cpp", "src/math.cpp"}

        edges = integration.parse_imports("src/main.cpp", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.cpp import CppIntegration

        integration = CppIntegration()
        lines = [
            "namespace utils {",
            "    constexpr double PI = 3.14;",
            "}",
        ]

        entities = integration.parse_entities("include/utils.hpp", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.cpp import CppIntegration

        integration = CppIntegration()
        assert integration.config.name == "cpp"


class TestZigIntegration:
    def test_iter_code_files(self, sample_zig_files, temp_repo_dir):
        from pr_diff_walk.integrations.zig import ZigIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = ZigIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 2

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.zig import ZigIntegration

        integration = ZigIntegration()
        lines = ['const std = @import("std");']
        repo_files = {"src/main.zig", "src/math.zig"}

        edges = integration.parse_imports("src/main.zig", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.zig import ZigIntegration

        integration = ZigIntegration()
        lines = [
            "pub fn add(a: i32, b: i32) i32 {",
            "    return a + b;",
            "}",
        ]

        entities = integration.parse_entities("src/main.zig", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.zig import ZigIntegration

        integration = ZigIntegration()
        assert integration.config.name == "zig"


class TestPhpIntegration:
    def test_iter_code_files(self, sample_php_files, temp_repo_dir):
        from pr_diff_walk.integrations.php import PhpIntegration
        from pr_diff_walk.schemas import RepositoryFiles

        integration = PhpIntegration()
        repo = RepositoryFiles(root=temp_repo_dir)
        files = list(integration.iter_code_files(temp_repo_dir, repo))

        assert len(files) == 2

    def test_parse_imports(self, temp_repo_dir):
        from pr_diff_walk.integrations.php import PhpIntegration

        integration = PhpIntegration()
        lines = ["require_once 'Utils.php';"]
        repo_files = {"src/Utils.php", "src/main.php"}

        edges = integration.parse_imports("src/main.php", lines, repo_files)
        assert isinstance(edges, list)

    def test_parse_entities(self, temp_repo_dir):
        from pr_diff_walk.integrations.php import PhpIntegration

        integration = PhpIntegration()
        lines = [
            "namespace App;",
            "",
            "class Utils {",
            "    public static function add($a, $b) {",
            "        return $a + $b;",
            "    }",
            "}",
        ]

        entities = integration.parse_entities("src/Utils.php", lines)
        assert len(entities) >= 1

    def test_config(self):
        from pr_diff_walk.integrations.php import PhpIntegration

        integration = PhpIntegration()
        assert integration.config.name == "php"
