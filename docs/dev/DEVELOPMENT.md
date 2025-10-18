# Development Setup Guide

## Prerequisites

- Python 3.9 or higher
- Git
- uv (fast Python package installer)

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Ganzzi/llm_queue.git
cd llm_queue
```

### 2. Create Virtual Environment

**Using uv (recommended):**
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Traditional method:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Unix/MacOS:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Package in Development Mode

**Using uv (recommended):**
```bash
uv pip install -e ".[dev]"
```

**Using pip:**
```bash
pip install -e ".[dev]"
```

This installs:
- The package in editable mode
- All development dependencies (pytest, black, mypy, etc.)

### 4. Install Pre-commit Hooks (Optional but Recommended)

```bash
pre-commit install
```

This will run code quality checks before each commit.

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=llm_queue --cov-report=html

# Run specific test file
pytest tests/test_queue.py

# Run specific test
pytest tests/test_queue.py::TestQueueBasics::test_initialization

# Run only fast tests (exclude slow tests)
pytest -m "not slow"
```

### Code Formatting

```bash
# Format all code
black src/ tests/ examples/

# Sort imports
isort src/ tests/ examples/

# Or run both with pre-commit
pre-commit run --all-files
```

### Linting

```bash
# Run flake8
flake8 src/ tests/ examples/

# Type checking
mypy src/llm_queue
```

### Running Examples

```bash
# Basic usage
python examples/basic_usage.py

# Concurrent mode demo
python examples/concurrent_mode.py

# Advanced features
python examples/advanced_usage.py
```

## Project Structure

```
llm_queue/
├── src/llm_queue/      # Main package code
├── tests/              # Test files
├── examples/           # Example scripts
├── docs/               # Documentation
└── .github/            # GitHub Actions workflows
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Edit code in `src/llm_queue/`
- Add tests in `tests/`
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run tests
pytest

# Check formatting
black --check src/ tests/
isort --check-only src/ tests/

# Run linting
flake8 src/ tests/

# Type check
mypy src/llm_queue
```

### 4. Commit

```bash
git add .
git commit -m "feat: your feature description"
```

Use conventional commit messages:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for refactoring

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Common Tasks

### Adding a New Feature

1. Create tests first (TDD approach)
2. Implement the feature
3. Update documentation
4. Run full test suite
5. Create PR

### Fixing a Bug

1. Write a test that reproduces the bug
2. Fix the bug
3. Verify test passes
4. Create PR

### Adding Tests

1. Create test file in `tests/` (test_*.py)
2. Use fixtures from `conftest.py`
3. Mark slow tests with `@pytest.mark.slow`
4. Run tests: `pytest tests/test_yourfile.py`

### Updating Documentation

1. Update README.md for user-facing changes
2. Update docstrings for API changes
3. Add examples if helpful
4. Update CHANGELOG.md

## Troubleshooting

### Import Errors

Make sure package is installed in editable mode:
```bash
uv pip install -e .  # or: pip install -e .
```

### Test Failures

Check if you have the latest dependencies:
```bash
uv pip install -e ".[dev]" --upgrade  # or: pip install -e ".[dev]" --upgrade
```

### Pre-commit Hook Issues

Update pre-commit hooks:
```bash
pre-commit autoupdate
pre-commit run --all-files
```

### Type Checking Errors

Install type stubs if needed:
```bash
uv pip install types-setuptools  # or: pip install types-setuptools
```

## Building the Package

### Local Build

```bash
# Install build tool
uv pip install build  # or: pip install build

# Build package
python -m build
```

This creates:
- `dist/*.whl` - wheel file
- `dist/*.tar.gz` - source distribution

### Test Installation

```bash
uv pip install dist/llm_queue-0.1.0-py3-none-any.whl  # or: pip install dist/llm_queue-0.1.0-py3-none-any.whl
```

## Release Process

### 1. Update Version

Edit `src/llm_queue/__version__.py`:
```python
__version__ = "0.2.0"
```

### 2. Update Changelog

Add release notes to `CHANGELOG.md`

### 3. Create Git Tag

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

### 4. Create GitHub Release

Go to GitHub → Releases → Create new release

### 5. Publish to PyPI (Automated)

GitHub Actions will automatically publish when a release is created.

## Tips

### VS Code Setup

Install extensions:
- Python
- Pylance
- Black Formatter
- isort

Add to `.vscode/settings.json`:
```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "editor.formatOnSave": true,
    "[python]": {
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
```

### Useful Commands

```bash
# Watch tests (requires pytest-watch)
uv pip install pytest-watch  # or: pip install pytest-watch
ptw

# Generate coverage report
pytest --cov=llm_queue --cov-report=html
open htmlcov/index.html

# Profile tests
pytest --durations=10

# Debug test
pytest -vv -s tests/test_queue.py::test_name
```

## Resources

- [Project Plan](../plan/project_plan.md)
- [Contributing Guidelines](../../CONTRIBUTING.md)
- [Quick Reference](../QUICK_REFERENCE.md)
- [Getting Started Guide](../guides/getting_started.md)

## Getting Help

- Check [Issues](https://github.com/Ganzzi/llm_queue/issues)
- Read [Contributing Guide](../../CONTRIBUTING.md)
- Contact maintainers

---

Happy coding! 🚀
