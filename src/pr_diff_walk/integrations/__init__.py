from typing import Dict, List, Optional, Set, Type

from pr_diff_walk.base import LanguageIntegration
from pr_diff_walk.integrations.common import (
    CSS_EXCLUDED_DIRS,
    GENERAL_EXCLUDED_DIRS,
    GENERAL_EXCLUDED_FILES,
    HTML_EXCLUDED_DIRS,
    JS_EXCLUDED_DIRS,
    TS_EXCLUDED_DIRS,
)
from pr_diff_walk.integrations.c_lang import CIntegration
from pr_diff_walk.integrations.cpp import CppIntegration
from pr_diff_walk.integrations.csharp import CSharpIntegration
from pr_diff_walk.integrations.css import CssIntegration
from pr_diff_walk.integrations.dart import DartIntegration
from pr_diff_walk.integrations.golang import GoIntegration
from pr_diff_walk.integrations.html import HtmlIntegration
from pr_diff_walk.integrations.java import JavaIntegration
from pr_diff_walk.integrations.javascript import JavascriptIntegration
from pr_diff_walk.integrations.kotlin import KotlinIntegration
from pr_diff_walk.integrations.php import PhpIntegration
from pr_diff_walk.integrations.python import PythonIntegration
from pr_diff_walk.integrations.rust import RustIntegration
from pr_diff_walk.integrations.swift import SwiftIntegration
from pr_diff_walk.integrations.typescript import TypescriptIntegration
from pr_diff_walk.integrations.zig import ZigIntegration

AVAILABLE_INTEGRATIONS: Dict[str, Type[LanguageIntegration]] = {
    "javascript": JavascriptIntegration,
    "js": JavascriptIntegration,
    "typescript": TypescriptIntegration,
    "ts": TypescriptIntegration,
    "html": HtmlIntegration,
    "css": CssIntegration,
    "python": PythonIntegration,
    "py": PythonIntegration,
    "rust": RustIntegration,
    "rs": RustIntegration,
    "go": GoIntegration,
    "golang": GoIntegration,
    "java": JavaIntegration,
    "cs": CSharpIntegration,
    "csharp": CSharpIntegration,
    "dart": DartIntegration,
    "flutter": DartIntegration,
    "swift": SwiftIntegration,
    "kotlin": KotlinIntegration,
    "kt": KotlinIntegration,
    "c": CIntegration,
    "cpp": CppIntegration,
    "c++": CppIntegration,
    "zig": ZigIntegration,
    "php": PhpIntegration,
}

LANGUAGE_TO_INTEGRATION: Dict[str, str] = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".py": "python",
    ".rs": "rust",
    ".go": "golang",
    ".java": "java",
    ".cs": "csharp",
    ".dart": "dart",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".zig": "zig",
    ".php": "php",
}

EXTENSION_TO_INTEGRATION: Dict[str, str] = {
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".py": "python",
    ".rs": "rust",
    ".go": "golang",
    ".java": "java",
    ".cs": "csharp",
    ".dart": "dart",
    ".swift": "swift",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".zig": "zig",
    ".php": "php",
}


def get_integration(name: str) -> LanguageIntegration:
    name = name.lower()
    if name in AVAILABLE_INTEGRATIONS:
        return AVAILABLE_INTEGRATIONS[name]()
    if name in LANGUAGE_TO_INTEGRATION:
        return AVAILABLE_INTEGRATIONS[LANGUAGE_TO_INTEGRATION[name]]()
    raise ValueError(f"Unknown integration: {name}. Available: {list(AVAILABLE_INTEGRATIONS.keys())}")


def detect_integrations_from_files(files: List[str]) -> List[str]:
    detected: Set[str] = set()
    for f in files:
        ext = "." + f.rsplit(".", 1)[-1] if "." in f else ""
        if ext in EXTENSION_TO_INTEGRATION:
            detected.add(EXTENSION_TO_INTEGRATION[ext])
    return list(detected)


def detect_integrations_from_extensions(extensions: Set[str]) -> List[str]:
    detected: Set[str] = set()
    for ext in extensions:
        if ext in EXTENSION_TO_INTEGRATION:
            detected.add(EXTENSION_TO_INTEGRATION[ext])
    return list(detected)


__all__ = [
    "AVAILABLE_INTEGRATIONS",
    "LANGUAGE_TO_INTEGRATION",
    "EXTENSION_TO_INTEGRATION",
    "get_integration",
    "detect_integrations_from_files",
    "detect_integrations_from_extensions",
    "GENERAL_EXCLUDED_DIRS",
    "GENERAL_EXCLUDED_FILES",
    "JS_EXCLUDED_DIRS",
    "TS_EXCLUDED_DIRS",
    "HTML_EXCLUDED_DIRS",
    "CSS_EXCLUDED_DIRS",
    "JavascriptIntegration",
    "TypescriptIntegration",
    "HtmlIntegration",
    "CssIntegration",
    "PythonIntegration",
    "RustIntegration",
    "GoIntegration",
    "JavaIntegration",
    "CSharpIntegration",
    "DartIntegration",
    "SwiftIntegration",
    "KotlinIntegration",
    "CIntegration",
    "CppIntegration",
    "ZigIntegration",
    "PhpIntegration",
]
