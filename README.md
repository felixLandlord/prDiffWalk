# pr-diff-walk

**PR dependency chain analysis with multi-language ecosystem support**

`pr-diff-walk` analyzes pull requests and merge requests to trace how changed code entities ripple through your codebase. It identifies which files and entities depend on what was modified, helping developers understand the full impact of their changes before merging.

## Features

- **Multi-language support**: JavaScript, TypeScript, Python, Rust, Go, Java, C#, Dart, Swift, Kotlin, C, C++, Zig, PHP, HTML, CSS
- **Multi-provider support**: GitHub PRs and GitLab MRs
- **Smart detection**: Automatically detects which language integrations to use based on PR files
- **Chain tracing**: Follows import/export relationships to find all dependents of changed code
- **Flexible output**: Markdown reports, JSON data, or structured analysis results
- **Local repo mode**: Analyze PRs using a locally cloned repository

## Installation

### From PyPI (planned release)

```bash
pip install pr-diff-walk
```

### From Source

```bash
# Clone the repository
git clone https://github.com/felixLandlord/prDiffWalk.git
cd prDiffWalk

# Install in development mode
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/felixLandlord/prDiffWalk.git
cd prDiffWalk
pip install -e ".[dev]"
```

## Requirements

- Python 3.10 or higher
- A GitHub or GitLab token for API access (see [Authentication](#authentication))

## Quick Start

```bash
# Analyze a GitHub PR (will auto-detect integrations)
pr-diff-walk analyze owner/repo 123

# With explicit integrations
pr-diff-walk analyze owner/repo 123 --integration python,javascript

# GitLab merge request
pr-diff-walk analyze owner/repo 456 --provider gitlab --gitlab-url https://gitlab.example.com
```

## CLI Commands

### `analyze`

The main command for analyzing pull requests and merge requests.

```bash
pr-diff-walk analyze <repo> <pr_number> [OPTIONS]
```

**Arguments:**
- `repo` - Repository in format `owner/repo`
- `pr_number` - PR/MR number to analyze

**Options:**

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--token` | `-t` | Git provider API token | From env/`.env` |
| `--local` | `-l` | Local repository path | Use remote API |
| `--depth` | `-d` | Maximum dependency chain depth | 8 |
| `--integration` | `-i` | Language integrations (comma/space sep) | Auto-detect |
| `--provider` | `-p` | Git provider: `github`, `gitlab` | `github` |
| `--gitlab-url` | | GitLab instance URL (for self-hosted) | `https://gitlab.com` |
| `--output` | `-o` | Output file path | stdout |
| `--format` | `-f` | Output format: `report`, `json`, `data` | `report` |

**Examples:**

```bash
# Basic analysis with markdown report output
pr-diff-walk analyze octocat/Hello-World 42

# JSON output for programmatic use
pr-diff-walk analyze owner/repo 123 --format json --output analysis.json

# Using local repository (faster for repeated analysis)
pr-diff-walk analyze owner/repo 123 --local ./my-repo

# Limit chain depth for faster analysis
pr-diff-walk analyze owner/repo 123 --depth 4

# Explicit language integrations
pr-diff-walk analyze owner/repo 123 --integration python rust

# GitLab merge request
pr-diff-walk analyze group/project 789 --provider gitlab
```

### `list`

Lists all available language integrations.

```bash
pr-diff-walk list
```

**Output:**
```
+--------------------+----------------------+----------------------------+
| Name               | Languages            | Extensions                 |
+--------------------+----------------------+----------------------------+
| javascript         | JavaScript           | .js, .jsx                  |
| typescript         | TypeScript           | .ts, .tsx                  |
| python             | Python               | .py                        |
| rust               | Rust                 | .rs                        |
| golang             | Go                   | .go                        |
| java               | Java                 | .java                      |
| csharp             | C#                   | .cs                        |
| dart               | Dart/Flutter         | .dart                      |
| swift              | Swift                | .swift                     |
| kotlin             | Kotlin               | .kt, .kts                  |
| c                  | C                    | .c, .h                     |
| cpp                | C++                  | .cpp, .cc, .cxx, .hpp, .h  |
| zig                | Zig                  | .zig                       |
| php                | PHP                  | .php                       |
| html               | HTML                 | .html                      |
| css                | CSS                  | .css                       |
+--------------------+----------------------+----------------------------+
```

### `report`

Generates a detailed markdown report (alias for `analyze` with `--format report`).

```bash
pr-diff-walk report <repo> <pr_number> [OPTIONS]
```

### `quick`

Provides a quick summary table of dependency chains.

```bash
pr-diff-walk quick <repo> <pr_number> [OPTIONS]
```

**Example output:**
```
           Dependency Chains Summary
+------+------------------+----------------------+-----+
| Chain | Seed Entity     | File                 | Hops|
+------+------------------+----------------------+-----+
| 1    | validate (func)  | auth/validators.py   | 5   |
| 2    | User (class)     | models/user.py       | 3   |
+------+------------------+----------------------+-----+

Total chains: 2
Integrations: python,javascript
```

## Authentication

### GitHub Token

Set via one of:

1. **Command line**: `--token YOUR_TOKEN`
2. **Environment variable**: `GITHUB_TOKEN` or `GH_TOKEN`
3. **`.env` file**: Add `GITHUB_TOKEN=YOUR_TOKEN` in project root or local repo

Generate a token at: https://github.com/settings/tokens

Required scopes: `repo` (for private repos) or `public_repo` (for public repos)

### GitLab Token

Set via one of:

1. **Command line**: `--token YOUR_TOKEN`
2. **Environment variable**: `GITLAB_TOKEN` or `GL_TOKEN`
3. **`.env` file**: Add `GITLAB_TOKEN=YOUR_TOKEN`

Generate a token at: https://gitlab.com/-/profile/personal_access_tokens

Required scopes: `api` (for private repos) or `read_api` (for public repos)

## Output Formats

### `report` (Default)

Detailed markdown report containing:
- PR metadata (repository, PR number, branches)
- Full diff content
- Dependency chains with code snippets
- Cross-references between changed files

### `json`

Structured JSON output for programmatic processing:

```json
{
  "repo_name": "owner/repo",
  "pr_num": 123,
  "head_ref": "feature-branch",
  "base_ref": "main",
  "provider": "github",
  "integrations": "python,javascript",
  "chains": [
    {
      "seed": {"file": "auth/validators.py", "name": "validate", "kind": "function"},
      "hops": [
        {
          "depth": 1,
          "from": {"file": "auth/routes.py", "name": "validate"},
          "importer": "auth/routes.py",
          "imported_as": "validate",
          "line": 15,
          "context": "login"
        }
      ]
    }
  ]
}
```

### `data`

Summary data with chain count:

```json
{
  "repo_name": "owner/repo",
  "pr_num": 123,
  "head_ref": "feature-branch",
  "base_ref": "main",
  "provider": "github",
  "integrations": "python,javascript",
  "chain_count": 5
}
```

## Using as a Python Library

### Basic Usage

```python
from pr_diff_walk import DiffChainService, analyze_pr

# Simple function call
result = analyze_pr("owner/repo", 123, github_token="ghp_xxx")

print(result["data"].chains)
print(result["report"])
```

### Advanced Usage

```python
from pr_diff_walk import DiffChainService, get_integration

# Create service with custom configuration
service = DiffChainService(
    repo_name="owner/repo",
    pr_num=123,
    github_token="ghp_xxx",           # Or set GITHUB_TOKEN env var
    local_repo_path="./my-repo",       # Use local clone for speed
    max_depth=10,                      # Increase depth for deeper analysis
    integrations=["python", "javascript"],
    provider="github",                # or "gitlab"
    gitlab_url="https://gitlab.example.com",  # For GitLab self-hosted
)

# Run analysis
result = service.analyze()

# Access results
print(f"Found {len(result.chains)} dependency chains")

for chain in result.chains:
    print(f"Seed: {chain.seed.name} in {chain.seed.file_path}")
    for hop in chain.hops:
        print(f"  -> {hop.next_entity.name} in {hop.next_entity.file_path}")

# Generate report
report = service.generate_report(result)
print(report)
```

### Accessing Individual Components

```python
from pr_diff_walk import (
    get_git_client,
    get_integration,
    GitHubClient,
)

# Direct git client usage
client = GitHubClient(token="ghp_xxx")
pr = client.get_pr("owner/repo", 123)
files = client.get_pr_files("owner/repo", 123)

# Get specific language integration
python_integration = get_integration("python")
```

## Core Logic

### Overview

`pr-diff-walk` works by analyzing how code entities in a PR interact with the rest of the codebase through import/export relationships.

### Analysis Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Fetch PR   │────>│  Download    │────>│  Load Repo     │
│  metadata   │     │  snapshot    │     │  files         │
└─────────────┘     └──────────────┘     └────────────────┘
                                                │
                                                v
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Output     │<────│  Generate    │<────│  Trace         │
│  report     │     │  chains      │     │  dependencies  │
└─────────────┘     └──────────────┘     └────────────────┘
```

### Step 1: Fetch PR Metadata

The tool retrieves PR/MR information from the git provider API:
- PR title, description, and metadata
- List of changed files
- Diff patches for each file
- Branch information (head and base)

### Step 2: Load Repository

The full repository snapshot is downloaded (or read from local path):
- Files are scanned based on detected language integrations
- Each integration knows which file extensions to look for
- Common build/generated directories are excluded (e.g., `node_modules`, `dist`, `target`)

### Step 3: Parse Entities and Imports

For each file in the repository:

1. **Entity Detection**: Language-specific parsers identify defined entities (functions, classes, variables, etc.) with their line ranges

2. **Import Analysis**: Parsers extract import statements and map them to source files

Example for Python:
```python
# Entity: validate() function at lines 10-25
def validate(data):
    ...

# Import: uses validate from auth.validators
from auth.validators import validate
```

### Step 4: Extract Changed Entities

The diff patch is analyzed to find which lines changed:
1. Parse the unified diff format to extract added/modified line numbers
2. Map line numbers to the smallest enclosing entity (function, class, etc.)
3. These become the "seed" entities for chain tracing

### Step 5: Trace Dependency Chains

Starting from each changed entity (seed):

1. **Find dependents**: Look for files that import this entity
2. **Breadth-first traversal**: Follow the dependency graph up to `max_depth`
3. **Collect hops**: Record each step in the chain with context (line number, calling code)

The chain tracer uses a queue-based breadth-first search:

```
Seed: validate() in auth/validators.py
  Hop 1: imported by auth/routes.py (login function, line 15)
    Hop 2: imported by api/middleware.py (auth check, line 42)
      Hop 3: imported by app.py (main entry, line 100)
```

### Supported Entity Types

Each language integration recognizes different entity kinds:

| Language | Entity Kinds |
|----------|--------------|
| Python | class, function, method, variable, async_function |
| JavaScript | function, const, let, var, class |
| TypeScript | Same as JS + interface, type, enum |
| Rust | fn, struct, enum, impl, trait, const, static |
| Go | func, type, const, var |
| Java | class, interface, enum, method, field |
| C# | class, interface, struct, enum, method, property |
| Dart | class, function, method, variable |
| Swift | class, struct, enum, func, let, var |
| Kotlin | class, fun, val, var, object |
| C/C++ | function, struct, union, enum, typedef |
| Zig | fn, const, var, struct, enum |
| PHP | function, class, interface, trait |
| HTML | element, id, class, attribute |
| CSS | selector, property, at-rule |

## Supported Providers

### GitHub

- Public and private repositories
- Personal access tokens (classic and fine-grained)
- Requires `repo` scope for private repos

### GitLab

- GitLab.com and self-hosted instances
- Personal access tokens
- Requires `api` scope for private projects

## Language Integrations

The tool uses language-specific integrations to parse imports and entities:

| Integration | Extensions | Notes |
|-------------|------------|-------|
| JavaScript | `.js`, `.jsx` | ES6 imports, CommonJS requires |
| TypeScript | `.ts`, `.tsx` | Includes JS support, type imports |
| Python | `.py` | `from` and `import` statements |
| Rust | `.rs` | `use` and `mod` declarations |
| Go | `.go` | `import` and `require` |
| Java | `.java` | `import` declarations |
| C# | `.cs` | `using` statements |
| Dart | `.dart` | `import` and `export` |
| Swift | `.swift` | `import` and `struct`/`class` |
| Kotlin | `.kt`, `.kts` | `import` statements |
| C | `.c`, `.h` | `#include` directives |
| C++ | `.cpp`, `.cc`, `.cxx`, `.hpp`, `.h` | `#include` directives |
| Zig | `.zig` | `const`, `usingnamespace` |
| PHP | `.php` | `use` and `require`/`include` |
| HTML | `.html` | Script/style src references |
| CSS | `.css` | `@import` and url() references |

## Environment Variables

| Variable | Provider | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | GitHub | GitHub personal access token |
| `GH_TOKEN` | GitHub | Alternative GitHub token env var |
| `GITLAB_TOKEN` | GitLab | GitLab personal access token |
| `GL_TOKEN` | GitLab | Alternative GitLab token env var |

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) in the docs folder.
