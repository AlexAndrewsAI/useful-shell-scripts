# Agent Instructions: useful-shell-scripts

## Quick Start
1. **Setup:** Run `uv sync --dev` before major work sessions
2. **Activate:** Ensure `.venv` is active; run `uv venv` if missing
3. **Code:** Use `python3` or `uv run python`; always add type hints and tests for Python code

## Tech Stack
| Component | Tool |
|-----------|------|
| Environment & Dependencies | uv |
| Testing | pytest |
| Linting & Formatting | ruff |
| Type Checking | mypy |
| Security Audit | pip-audit |
| Git Hooks | prek |
| Shell Script Linting | pureshellcheck |

## Project Structure
```
bash/                      # Shell scripts for various utilities
  ├── bashrc-dev.sh        # Development bash configuration
  ├── bashrc-extra.sh      # Main bash utilities
  ├── bashrc-files.sh      # File operation utilities
  ├── bashrc-processes.sh  # Process management utilities
  ├── git-copy-bare.sh     # Git repository copying
  ├── git2linksremote.sh   # Git to markdown links
  ├── git2markdown.sh      # Git to markdown formatting
  ├── ports-in-use.sh      # Network port monitoring
  └── psfind.sh            # Process finding utility
tests/                     # Pytest suite for Python and shell script validation
pyproject.toml             # Dependencies & tool config
.pre-commit-config.yaml    # Pre-commit hooks configuration
setup.sh                   # Setup script for bash integration
```

## Essential Directives

### Code Standards
- **Type Hints:** Required on ALL Python function signatures and class members. Enforce strictly with mypy. Avoid using `# type: ignore` comments to suppress mypy errors; fix the underlying type issues instead.
- **Docstrings:** Google-style format for all public Python APIs.
- **Logging:** Use `logging` module only; never `print()`.
- **Relative Paths:** Never use absolute paths in code.
- **Shell Scripts:** Follow bash best practices; use pureshellcheck for validation.
- **YAML Files:** Always use `.yaml` extension for YAML files. Never use `.yml`.

### Dependency & Configuration Management
- **Adding/Removing Dependencies:** Use `uv add` / `uv remove` commands.
- **Editing pyproject.toml:** Avoid manual edits during development. Only update `pyproject.toml` as the **final change** after all work is tested and finalized.
- **Before Major Work:** Always run `uv sync --dev` first.

### Testing & Quality
- **Test Coverage:** Every Python code change requires corresponding tests in `tests/`.
- **Shell Script Testing:** Shell scripts are validated using pureshellcheck in test_shellcheck.py.
- **Validation Before Commit:** Run the full suite: `uv run pytest`, `uv run ruff check .`, `uv run mypy .`, `uv run pip-audit`.
- **Pre-commit Hooks:** Use `uv run prek install` to set up Git hooks that automatically run these checks on commits.

### Operational Constraints
- **No Interactive Prompts:** Mock or bypass any interactive commands.
- **Staging & Commit Protocol:** When you have completed work and updated files, stage the changes with `git add` and then display a suggested commit message for the user's review. DO NOT actually commit - only stage and display the message.
- **Code Review Mode:** Analyze only; record findings in `./REVIEW.md` without making modifications. At the top of the review, identify the reviewer including the name of the IDE/CLI used and the primary model that performed the review.

### File Maintenance
- **Keep Instructions Current:** Update "Tech Stack," "Project Structure," and "Workflow Commands" if `pyproject.toml`, structure, or core logic changes.
- **Pre-commit Config:** Keep `.pre-commit-config.yaml` in sync with CI workflow when test requirements change.

## Workflow Commands
```bash
uv sync --dev                           # Install/sync all dependencies
uv run pytest                           # Run tests
uv run ruff check .                     # Lint
uv run ruff format .                    # Auto-format
uv run mypy .                           # Type check
uv run pip-audit                        # Security audit
uv run prek install                     # Install pre-commit Git hooks
uv run prek run --all-files             # Run all pre-commit hooks manually
```

## Repository-Specific Notes

This repository focuses on shell scripts for system administration and development workflows. Python code is primarily used for:
- Testing shell scripts via pureshellcheck
- Configuration validation
- Development utilities

When working with shell scripts:
- Maintain bash compatibility (target bash 4.0+)
- Use meaningful variable names
- Add comments for complex logic
- Ensure scripts have proper shebangs
- Test scripts across different scenarios when possible
