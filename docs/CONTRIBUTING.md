# Contributing to pr-diff-walk

Thank you for your interest in contributing to pr-diff-walk! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip or uv for package management
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/felixLandlord/prDiffWalk.git
cd prDiffWalk

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests to verify setup
pytest
```

## Project Structure

```
prDiffWalk/
├── src/pr_diff_walk/      # Main source code
│   ├── cli.py              # CLI entry point
│   ├── service.py          # Core analysis service
│   ├── base.py             # Base integration class
│   ├── schemas.py          # Data models
│   ├── git_clients/        # Git provider clients
│   └── integrations/        # Language-specific parsers
├── tests/                  # Test suite
│   ├── test_*.py           # Unit tests
│   └── integrations/       # Integration tests
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── README.md               # Main documentation
└── pyproject.toml          # Package configuration
```

## Making Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-you-are-fixing
```

### 2. Make Your Changes

- Follow the existing code style and conventions
- Write clean, readable code with appropriate type hints
- Add comments only when necessary for clarity

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/pr_diff_walk --cov-report=html

# Run specific test file
pytest tests/test_service.py -v

# Run linting
ruff check src/
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add support for new language integration"
```

### Commit Message Format

Use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

## Adding a New Language Integration

Language integrations are in `src/pr_diff_walk/integrations/`. To add support for a new language:

### 1. Create Integration File

Create `src/pr_diff_walk/integrations/your_lang.py`:

```python
import re
from pathlib import Path
from typing import Iterable, List, Optional, Set

from ..base import LanguageIntegration
from ..schemas import EntityDef, EntityRef, ImportEdge, LanguageConfig, RepositoryFiles

YOUR_LANG_EXTENSIONS = {".ext"}

def _your_lang_config() -> LanguageConfig:
    return LanguageConfig(
        name="your_lang",
        extensions=YOUR_LANG_EXTENSIONS,
        file_patterns=["*.ext"],
        module_marker="module.json",
        package_indicator="package.json",
        import_patterns={
            "import": r"^import\s+['\"](.+)['\"]",
        },
        entity_kinds={"function", "class", "variable"},
    )

class YourLangIntegration(LanguageIntegration):
    def __init__(self):
        super().__init__(_your_lang_config())

    def iter_code_files(self, root: Path, repo: RepositoryFiles) -> Iterable[Path]:
        # Iterate over files with your language extension
        ...

    def parse_imports(self, file_path: str, lines: List[str], repo_files: Set[str]) -> List[ImportEdge]:
        # Parse import statements and return ImportEdge objects
        ...

    def parse_entities(self, file_path: str, lines: List[str]) -> List[EntityDef]:
        # Parse entity definitions (functions, classes, etc.)
        ...

    def resolve_import_to_file(self, current_file: str, spec: str, repo_files: Set[str]) -> Optional[str]:
        # Convert import spec to file path
        ...
```

### 2. Register Integration

Update `src/pr_diff_walk/integrations/__init__.py`:
1. Import your integration class
2. Add to `AVAILABLE_INTEGRATIONS` dict
3. Add to `LANGUAGE_TO_INTEGRATION` and `EXTENSION_TO_INTEGRATION` mappings

### 3. Add Tests

Create `tests/integrations/test_your_lang.py`:

```python
import pytest
from pr_diff_walk.integrations.your_lang import YourLangIntegration

class TestYourLangIntegration:
    def test_parse_entities(self):
        integration = YourLangIntegration()
        code = "function hello() {}"
        entities = integration.parse_entities("test.ext", code.splitlines())
        assert len(entities) == 1
        assert entities[0].name == "hello"

    def test_parse_imports(self):
        integration = YourLangIntegration()
        code = 'import "module"'
        edges = integration.parse_imports("test.ext", code.splitlines(), set())
        assert len(edges) == 1
```

### 4. Update Documentation

- Add to CLI `list` command descriptions
- Update README.md integration table
- Add language-specific example if helpful

## Code Style Guidelines

- Use type hints for all function parameters and return values
- Follow PEP 8 with 100 character line length
- Use descriptive variable names
- Keep functions focused and small
- Write docstrings for public APIs

## Reporting Issues

When reporting bugs:
1. Include your Python version
2. Include the pr-diff-walk version (`pip show pr-diff-walk`)
3. Provide a minimal reproducible example
4. Include any relevant error messages

## Questions?

Feel free to open an issue for questions or discussions about the project.