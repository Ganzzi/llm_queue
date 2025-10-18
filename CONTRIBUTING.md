# Contributing to LLM Queue

Thank you for your interest in contributing to LLM Queue! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and considerate of others. We welcome contributions from everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/llm-queue/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Code samples if applicable

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue describing:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative approaches considered
   - Any implementation details

### Pull Requests

1. **Fork the repository** and create a new branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes**:
   - Write clear, documented code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests and linting**:
   ```bash
   pytest
   black src/ tests/
   isort src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

4. **Commit your changes**:
   ```bash
   git commit -m "Add feature: description"
   ```
   
   Use clear, descriptive commit messages following [Conventional Commits](https://www.conventionalcommits.org/)

5. **Push and create a PR**:
   ```bash
   git push origin feature/my-feature
   ```
   
   Then open a Pull Request with:
   - Clear title and description
   - Link to related issues
   - Summary of changes
   - Any breaking changes noted

## Development Setup

### Prerequisites

- Python 3.9+
- Git

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llm-queue.git
   cd llm-queue
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Code Style

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 100)
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints for all functions
- Write docstrings for all public APIs (Google style)

### Example

```python
async def process_request(
    request: QueueRequest[T],
    timeout: Optional[float] = None
) -> QueueResponse[T]:
    """Process a queue request with optional timeout.
    
    Args:
        request: The request to process
        timeout: Maximum time to wait in seconds
        
    Returns:
        Response with processing result
        
    Raises:
        QueueTimeout: If processing exceeds timeout
    """
    # Implementation here
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=llm_queue --cov-report=html

# Run specific test file
pytest tests/test_queue.py

# Run specific test
pytest tests/test_queue.py::TestQueueBasics::test_initialization
```

### Writing Tests

- Use pytest fixtures from `conftest.py`
- Test both success and failure cases
- Use `@pytest.mark.asyncio` for async tests
- Use `@pytest.mark.slow` for tests taking >1 second
- Aim for >90% code coverage

### Example Test

```python
@pytest.mark.asyncio
async def test_submit_request(queue_manager, sample_model_config, simple_processor):
    """Test submitting a request."""
    await queue_manager.register_queue(sample_model_config, simple_processor)
    
    request = QueueRequest(model_id="test-model")
    response = await queue_manager.submit_request(request)
    
    assert response.status == "completed"
    assert response.result["success"] is True
```

## Documentation

### Code Documentation

- All public classes and functions must have docstrings
- Include type hints
- Provide usage examples in docstrings when helpful

### User Documentation

- Update README.md for user-facing changes
- Add examples to `examples/` directory
- Update docs in `docs/` directory

## Release Process

1. Update version in `src/llm_queue/__version__.py`
2. Update CHANGELOG.md
3. Create a git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
4. Push tag: `git push origin v0.1.0`
5. Create GitHub release
6. Automated workflow will publish to PyPI

## Questions?

- Open an issue for questions
- Start a discussion for broader topics
- Contact maintainers directly if needed

Thank you for contributing! 🎉
