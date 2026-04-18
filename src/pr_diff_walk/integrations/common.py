from typing import Set

GENERAL_EXCLUDED_DIRS: Set[str] = {
    ".git",
    ".idea",
    ".vscode",
    ".vs",
    ".cache",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".env",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "target",
    "pkg",
    "bin",
    "obj",
    ".gradle",
    ".dart_tool",
    "Pods",
    ".build",
    "vendor",
    ".cargo",
    "vendor/bundle",
}

GENERAL_EXCLUDED_FILES: Set[str] = {
    ".DS_Store",
    "Thumbs.db",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "go.sum",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    "Gemfile.lock",
}

JS_EXCLUDED_DIRS: Set[str] = {
    "coverage",
    ".nyc_output",
    ".test_results",
}

TS_EXCLUDED_DIRS: Set[str] = {
    "coverage",
    ".nyc_output",
    ".test_results",
    "tsconfig.build",
}

HTML_EXCLUDED_DIRS: Set[str] = {
    ".templatecache",
}

CSS_EXCLUDED_DIRS: Set[str] = {
    "coverage",
    ".sass_cache",
}
