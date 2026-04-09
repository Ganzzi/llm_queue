# Development Guide

## Prerequisites

- Python 3.9+
- uv

## Setup

```bash
uv sync --all-groups --all-extras
```

## Unit Tests (PR Gate)

```bash
uv run pytest -m "not integration and not e2e" -q
```

## Integration / E2E Tests

```bash
uv run pytest -q
uv run pytest -m integration
uv run pytest -m e2e
```

## Coverage

```bash
uv run pytest -m "not integration and not e2e" --cov --cov-report=term-missing
```

## CI Behavior

- PRs are gated on the deterministic unit command.
- Integration and E2E tests are run separately from PR gating.

## Known Issues

- The repository is being standardized to use `pyproject.toml` as the single build configuration.
- Tests are being reorganized into `tests/unit/`, `tests/integration/`, and `tests/e2e/`.
