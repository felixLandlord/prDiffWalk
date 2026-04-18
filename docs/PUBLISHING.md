# Publishing pr-diff-walk to PyPI

This guide covers the process of publishing pr-diff-walk to PyPI (Python Package Index).

## Prerequisites

- Python 3.10 or higher
- A PyPI account at https://pypi.org
- A PyPI Test account at https://test.pypi.org (recommended for testing)
- twine installed: `pip install twine build`

## Preparation

### 1. Update Version Number

Edit `pyproject.toml` and update the version:

```toml
[project]
name = "pr-diff-walk"
version = "0.x.y"  # Update this
```

Or bump using hatch:

```bash
hatch version major   # 0.1.0 -> 1.0.0
hatch version minor   # 0.1.0 -> 0.2.0
hatch version patch   # 0.1.0 -> 0.1.1
```

### 2. Verify pyproject.toml Configuration

Ensure your `pyproject.toml` is properly configured:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pr-diff-walk"
version = "0.1.0"
description = "PR dependency chain analysis with multi-language ecosystem support"
readme = "README.md"           # Must link to README
requires-python = ">=3.10"
license = {text = "Apache-2.0"}
authors = [
    {name = "Your Name", email = "you@example.com"},
]
keywords = ["pull-request", "dependency", "analysis", "github", "gitlab"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "typer>=0.12.0",
    "rich>=13.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.4.0",
]

[project.scripts]
pr-diff-walk = "pr_diff_walk.cli:main"

[project.urls]
Homepage = "https://github.com/yourusername/prDiffWalk"
Documentation = "https://github.com/yourusername/prDiffWalk#readme"
Repository = "https://github.com/yourusername/prDiffWalk"
Issues = "https://github.com/yourusername/prDiffWalk/issues"
```

### 3. Verify README Exists

Make sure `README.md` exists and contains:
- Clear description of the package
- Installation instructions
- Usage examples
- License information

## Testing (Recommended)

### 1. Build the Package

```bash
# Clean any previous builds
rm -rf dist/ build/ *.egg-info

# Build source distribution and wheel
python -m build
```

### 2. Test on TestPyPI

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*
```

### 3. Install and Test from TestPyPI

```bash
# Create a virtual environment
python -m venv test-env
source test-env/bin/activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ pr-diff-walk

# Test the installation
pr-diff-walk --help
pr-diff-walk list
```

### 4. Verify Everything Works

```bash
# Quick test (will need a real token for full functionality)
pr-diff-walk analyze owner/repo 1 --provider github --token test_token
```

## Publishing to PyPI

### 1. Build the Package

```bash
# Clean any previous builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build
```

### 2. Upload to PyPI

```bash
twine upload dist/*
```

### 3. Verify the Release

1. Visit https://pypi.org/project/pr-diff-walk
2. Check that the project page looks correct
3. Verify the download stats

### 4. Test Installation from PyPI

```bash
# Fresh virtual environment
python -m venv prod-test
source prod-test/bin/activate

# Install from PyPI
pip install pr-diff-walk

# Verify
pr-diff-walk --version
```

## Post-Release

### 1. Create a GitHub Release

```bash
# Tag the release
git tag -a v0.x.y -m "Release version 0.x.y"
git push origin main --tags
```

Or create a release through GitHub UI.

### 2. Update Documentation

If there are significant changes:
- Update README.md
- Update any examples
- Update the docs folder

### 3. Announce

Consider announcing on:
- Twitter/X
- LinkedIn
- Python community forums
- Relevant subreddits

## Troubleshooting

### Common Issues

**Build fails with missing dependencies:**
- Ensure all dependencies are listed in `pyproject.toml`
- Use specific version ranges

**Import errors after installation:**
- Check that packages are in `src/pr_diff_walk`
- Verify `packages` configuration in `[tool.hatch.build.targets]`

**twine upload fails:**
- Verify credentials: `cat ~/.pypirc`
- Check that the version hasn't been uploaded before

**Wrong package name on PyPI:**
- Verify `name` field in `[project]` section of `pyproject.toml`

## Automated Publishing (Optional)

### Using GitHub Actions

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
          
      - name: Build package
        run: |
          rm -rf dist/ build/ *.egg-info
          python -m build
          
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
```

Add `PYPI_TOKEN` to your GitHub repository secrets.

## Quick Reference

```bash
# Full release workflow
rm -rf dist/ build/ *.egg-info
python -m build
twine upload --repository testpypi dist/*  # Test first
twine upload dist/*                        # Production
```

## Additional Resources

- [PyPI User Guide](https://packaging.python.org/)
- [hatchling documentation](https://hatch.pypa.io/)
- [twine documentation](https://twine.readthedocs.io/)
