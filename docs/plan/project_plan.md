# LLM Queue - Project Plan & Checklist

## Project Overview
A high-performance Python package for managing LLM API calls with intelligent rate limiting and queueing mechanisms.

### Core Features
- ✅ Async-first architecture using asyncio
- ✅ Multiple rate limiting modes (requests per period, concurrent requests)
- ✅ Per-model queue management
- ✅ Type-safe with Pydantic models
- ✅ Generic typing support for flexible result types
- ✅ Request status tracking
- ✅ Automatic retry capabilities
- ✅ Performance monitoring hooks

---

## Package Structure

```
llm_queue/
├── src/
│   └── llm_queue/
│       ├── __init__.py           # Package exports
│       ├── __version__.py        # Version info
│       ├── models.py             # Pydantic models (RequestStatus, QueueRequest, etc.)
│       ├── rate_limiter.py       # RateLimiter class
│       ├── queue.py              # Queue class
│       ├── manager.py            # QueueManager singleton
│       ├── exceptions.py         # Custom exceptions
│       └── utils.py              # Helper utilities
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_rate_limiter.py    # Rate limiter tests
│   ├── test_queue.py            # Queue tests
│   ├── test_manager.py          # Manager tests
│   ├── test_integration.py     # Integration tests
│   └── test_performance.py     # Performance benchmarks
├── examples/
│   ├── basic_usage.py           # Simple example
│   ├── openai_example.py        # OpenAI integration
│   ├── anthropic_example.py     # Anthropic integration
│   ├── concurrent_mode.py       # Concurrent requests mode
│   └── advanced_usage.py        # Advanced features
├── docs/
│   ├── dev/                     # Development docs
│   ├── plan/                    # Planning docs
│   ├── api/                     # API documentation
│   └── guides/                  # User guides
├── .github/
│   └── workflows/
│       ├── test.yml             # Run tests
│       ├── lint.yml             # Code quality
│       └── publish.yml          # PyPI publishing
├── pyproject.toml               # Modern Python packaging
├── setup.py                     # Setup configuration
├── setup.cfg                    # Additional setup config
├── README.md                    # Main documentation
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore rules
├── .pre-commit-config.yaml      # Pre-commit hooks
├── requirements.txt             # Runtime dependencies
├── requirements-dev.txt         # Development dependencies
└── CHANGELOG.md                 # Version history
```

---

## Implementation Checklist

### Phase 1: Package Foundation ✅
- [x] Create package directory structure
- [x] Set up `pyproject.toml` with modern packaging standards
- [x] Create `setup.py` for backward compatibility
- [x] Add `setup.cfg` for tool configurations
- [x] Create comprehensive `README.md`
- [x] Add MIT License
- [x] Create `.gitignore` for Python projects
- [x] Set up `requirements.txt` and `requirements-dev.txt`

### Phase 2: Core Implementation ✅
- [x] **models.py**: Pydantic models
  - [x] `RateLimiterMode` enum
  - [x] `RequestStatus` enum
  - [x] `ModelConfig` model
  - [x] `QueueRequest[T]` generic model
  - [x] `QueueResponse[T]` generic model
  - [x] Add validation and field descriptions

- [x] **rate_limiter.py**: Rate limiting logic
  - [x] `RateLimiter` class with dual modes
  - [x] Requests per period implementation
  - [x] Concurrent requests implementation
  - [ ] Token bucket algorithm option (future)
  - [x] Add performance metrics collection

- [x] **queue.py**: Queue management
  - [x] `Queue[T]` generic class
  - [x] Async queue processing
  - [x] Request lifecycle management
  - [x] Error handling and retry logic
  - [ ] Priority queue support (future)

- [x] **manager.py**: Centralized queue manager
  - [x] `QueueManager[T]` singleton pattern
  - [x] Multi-model registration
  - [x] Request routing
  - [x] Status tracking across queues

- [x] **exceptions.py**: Custom exceptions
  - [x] `RateLimitExceeded`
  - [x] `QueueTimeout`
  - [x] `ModelNotRegistered`
  - [x] `InvalidConfiguration`

- [x] **utils.py**: Helper functions
  - [x] Timing utilities
  - [x] Logging setup
  - [x] Configuration helpers

- [x] **__init__.py**: Package exports
  - [x] Export all public APIs
  - [x] Version information
  - [x] Convenient imports

### Phase 3: Testing Infrastructure ✅
- [x] Set up pytest configuration
- [x] Create pytest fixtures in `conftest.py`
- [x] **test_rate_limiter.py**
  - [x] Test requests per period mode
  - [x] Test concurrent requests mode
  - [x] Test edge cases and boundaries
  - [x] Performance benchmarks

- [x] **test_queue.py**
  - [x] Test queue operations
  - [x] Test async processing
  - [x] Test error handling
  - [x] Test request lifecycle

- [x] **test_manager.py**
  - [x] Test model registration
  - [x] Test request routing
  - [x] Test singleton behavior
  - [x] Test multi-queue scenarios

- [x] **test_integration.py**
  - [x] End-to-end workflows
  - [x] Multi-model scenarios
  - [x] Load testing
  - [x] Concurrent operations

- [x] **test_performance.py**
  - [x] Throughput benchmarks
  - [x] Latency measurements
  - [x] Memory profiling
  - [x] Stress tests

### Phase 4: Documentation ✅
- [x] **README.md**: Comprehensive guide
  - [x] Installation instructions
  - [x] Quick start guide
  - [x] Features overview
  - [x] Usage examples
  - [x] Configuration options
  - [x] Contributing guidelines

- [x] **API Documentation**
  - [x] Class and method docstrings
  - [x] Type hints everywhere
  - [x] Usage examples in docstrings
  - [ ] Sphinx/MkDocs setup (optional)

- [x] **User Guides**
  - [x] Getting started guide
  - [x] Rate limiting modes explained
  - [x] Best practices
  - [x] Performance tuning
  - [x] Troubleshooting

- [x] **CHANGELOG.md**
  - [x] Version history format
  - [x] Keep-a-changelog format

### Phase 5: Examples & Demos ✅
- [x] **basic_usage.py**: Simple example
- [x] **openai_example.py**: OpenAI integration
- [ ] **anthropic_example.py**: Anthropic integration
- [x] **concurrent_mode.py**: Concurrent mode demo
- [x] **advanced_usage.py**: Advanced features
  - [x] Custom error handling
  - [x] Monitoring and metrics
  - [x] Dynamic configuration

### Phase 6: CI/CD & Quality ✅
- [x] **GitHub Actions**
  - [x] `test.yml`: Run tests on multiple Python versions
  - [x] `lint.yml`: Run flake8, black, mypy, isort
  - [x] `publish.yml`: Automated PyPI publishing

- [x] **Pre-commit Hooks**
  - [x] Black formatter
  - [x] isort import sorting
  - [x] flake8 linting
  - [x] mypy type checking

- [x] **Code Quality**
  - [x] 100% type hints coverage
  - [x] >90% test coverage target
  - [x] Documentation coverage
  - [ ] Security scanning (bandit)

### Phase 8: Release Preparation - v0.1.0 ✅
- [x] Version 0.1.0 preparation
- [x] PyPI package metadata
- [x] Initial release complete

### Phase 9: Version 0.2.0 - Stable Release with API Improvements
- [ ] **Breaking Changes: Dual-Generic Type System**
  - [ ] Change `QueueRequest[T]` to `QueueRequest[P]` with `params: P` field
  - [ ] Keep `QueueResponse[T]` with `result: T` field
  - [ ] Update `Queue[P, T]` with dual generics
  - [ ] Update `QueueManager[P, T]` with dual generics
  - [ ] Add `wait_for_completion: bool` parameter to `QueueRequest`

- [ ] **Code Updates**
  - [ ] Refactor `models.py` for dual-generic support
  - [ ] Update `queue.py` for new processor signature and enqueue logic
  - [ ] Update `manager.py` for dual-generic types
  - [ ] Update `__init__.py` exports

- [ ] **Examples**
  - [ ] Create `typed_models_example.py` with Pydantic models for params/results
  - [ ] Update all existing examples for new API
  - [ ] Update examples README

- [ ] **Tests**
  - [ ] Update all test files for new API
  - [ ] Add tests for `wait_for_completion` feature
  - [ ] Ensure 90%+ coverage maintained
  - [ ] Run full test suite

- [ ] **Documentation**
  - [ ] Update README with new API examples
  - [ ] Update Getting Started guide
  - [ ] Update Quick Reference
  - [ ] Update API documentation in docstrings
  - [ ] Document breaking changes in CHANGELOG

- [ ] **Release**
  - [ ] Version bump to 0.2.0
  - [ ] Final validation of all features
  - [ ] Create release notes
  - [ ] Tag and publish

---

## Dependencies

### Runtime Dependencies
- `asyncio` (stdlib) - Async operations
- `pydantic` >= 2.0 - Data validation
- `typing-extensions` - Extended type hints (Python <3.10)

### Development Dependencies
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-benchmark` - Performance testing
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking
- `pre-commit` - Git hooks
- `sphinx` or `mkdocs` - Documentation

---

## Performance Goals

### Targets
- **Throughput**: Handle 1000+ requests/second per queue
- **Latency**: <10ms queue overhead
- **Memory**: <100MB for 10K queued requests
- **Accuracy**: 99.9%+ rate limit compliance

### Benchmarking
- Regular performance regression tests
- Comparison with naive implementations
- Load testing with various configurations

---

## Version Roadmap

### v0.1.0 (Released - October 18, 2025) ✅
- ✅ Core queue and rate limiting functionality
- ✅ Single generic type system
- ✅ Basic examples and documentation
- ✅ Essential test coverage
- ✅ CI/CD pipelines

### v0.2.0 (Stable Release - COMPLETED ✅)
**Focus: API Improvements & Stability**
- ✅ **Dual-generic type system** (`QueueRequest[P]`, `QueueResponse[T]`)
- ✅ **Breaking changes** for better API design
- ✅ **wait_for_completion** feature for fire-and-forget requests
- ✅ **Comprehensive examples** with Pydantic models
- ✅ **Full documentation** covering all features
- ✅ **90%+ test coverage** maintained
- ✅ **Stable API** ready for production

### v1.0.0 (Future - Stable Production Release)
**Focus: Production Hardening**
- Long-term API stability guarantee
- Enhanced error handling and recovery
- Performance optimizations
- Additional LLM provider examples
- Community feedback integration

---

## Success Criteria

### Package Quality
- ✅ Clean, modular code structure
- ✅ Comprehensive type hints
- ✅ >90% test coverage
- ✅ Performance benchmarks passing
- ✅ Documentation complete

### User Experience
- ✅ Simple API for basic usage
- ✅ Powerful API for advanced usage
- ✅ Clear error messages
- ✅ Helpful examples
- ✅ Easy installation

### Community
- ✅ Open source (MIT License)
- ✅ Contributing guidelines
- ✅ Issue templates
- ✅ Active maintenance

---

## Notes

- **v0.2.0 contains breaking changes** - migration guide will be provided
- Follow semantic versioning strictly from v1.0.0 onwards
- Maintain comprehensive changelog
- Regular security updates
- Community feedback integration after v0.2.0 stable release

---

## Version 0.2.0 Detailed Checklist

### Breaking API Changes

#### 1. Dual-Generic Type System
**Current (v0.1.0):**
```python
QueueRequest[T]  # Generic for result type
  - result: Optional[T]  # Stored here

QueueResponse[T]
  - result: Optional[T]
```

**New (v0.2.0):**
```python
QueueRequest[P]  # Generic for parameters type
  - params: P  # User-defined parameters
  - wait_for_completion: bool = True  # New feature

QueueResponse[T]  # Generic for result type
  - result: Optional[T]
```

**Note on `wait_for_completion=False`:** This is truly fire-and-forget. Results are not retrievable via `get_status()` - only completion status is available. Use this for background processing where you don't need the result.

#### 2. Class Signatures
**Before:**
- `Queue[T]`
- `QueueManager[T]`
- `processor_func: Callable[[QueueRequest[T]], Awaitable[T]]`

**After:**
- `Queue[P, T]`
- `QueueManager[P, T]`
- `processor_func: Callable[[QueueRequest[P]], Awaitable[T]]`

### Implementation Checklist

#### Core Changes
- [ ] Update `models.py`:
  - [ ] Change `QueueRequest` to use `P` generic with `params: P` field
  - [ ] Remove `result: Optional[T]` from `QueueRequest`
  - [ ] Add `wait_for_completion: bool = True` to `QueueRequest`
  - [ ] Keep `QueueResponse[T]` with `result: Optional[T]`
  - [ ] Update all type hints and docstrings

- [ ] Update `queue.py`:
  - [ ] Change class to `Queue[P, T]`
  - [ ] Update processor_func signature
  - [ ] Modify `enqueue()` to handle `wait_for_completion`
  - [ ] If `wait_for_completion=False`, return immediately with PENDING status
  - [ ] Update all type hints

- [ ] Update `manager.py`:
  - [ ] Change class to `QueueManager[P, T]`
  - [ ] Update `register_queue()` signature
  - [ ] Update `submit_request()` signature
  - [ ] Update all method type hints
  - [ ] Update docstrings

- [ ] Update `__init__.py`:
  - [ ] Ensure all updated types are exported correctly

#### Examples
- [ ] Create `examples/typed_models_example.py`:
  - [ ] Define `LLMParams` Pydantic model
  - [ ] Define `LLMResult` Pydantic model
  - [ ] Show usage with `QueueRequest[LLMParams]`
  - [ ] Show usage with `QueueResponse[LLMResult]`
  - [ ] Demonstrate type safety

- [ ] Update `examples/basic_usage.py`:
  - [ ] Use `params` field instead of metadata
  - [ ] Update processor to extract from `request.params`

- [ ] Update `examples/openai_example.py`:
  - [ ] Create proper params/result models
  - [ ] Use new API

- [ ] Update `examples/concurrent_mode.py`:
  - [ ] Use new API

- [ ] Update `examples/advanced_usage.py`:
  - [ ] Demonstrate `wait_for_completion=False`
  - [ ] Show polling for status

- [ ] Update `examples/README.md`:
  - [ ] Document new API patterns
  - [ ] Add migration guide

#### Tests
- [ ] Update `tests/test_models.py`:
  - [ ] Test `QueueRequest[P]` with params
  - [ ] Test `wait_for_completion` field
  - [ ] Test validation

- [ ] Update `tests/test_queue.py`:
  - [ ] Update for dual-generic types
  - [ ] Add test for `wait_for_completion=True`
  - [ ] Add test for `wait_for_completion=False`
  - [ ] Verify immediate return behavior

- [ ] Update `tests/test_manager.py`:
  - [ ] Update for dual-generic types
  - [ ] Test with custom Pydantic models

- [ ] Update `tests/test_init.py`:
  - [ ] Verify all exports work with new types

- [ ] Run full test suite:
  - [ ] `pytest` - all tests pass
  - [ ] `pytest --cov` - maintain 90%+ coverage

#### Documentation
- [ ] Update `README.md`:
  - [ ] Update Quick Start with new API
  - [ ] Show `params` field usage
  - [ ] Add example with Pydantic models
  - [ ] Document `wait_for_completion`

- [ ] Update `docs/guides/getting_started.md`:
  - [ ] Complete rewrite for new API
  - [ ] Migration guide from v0.1.0

- [ ] Update `docs/QUICK_REFERENCE.md`:
  - [ ] Update all signatures
  - [ ] Add dual-generic examples

- [ ] Update docstrings:
  - [ ] All classes have updated type parameters
  - [ ] All methods have updated signatures

- [ ] Create `MIGRATION.md`:
  - [ ] Guide for migrating from v0.1.0 to v0.2.0
  - [ ] Before/after code examples

#### Release Preparation
- [x] Update `src/llm_queue/__version__.py`:
  - [x] Change to `__version__ = "0.2.0"`

- [x] Update `pyproject.toml`:
  - [x] Update version to 0.2.0

- [x] Update `setup.py`:
  - [x] Update version to 0.2.0

- [x] Update `CHANGELOG.md`:
  - [x] Document all breaking changes
  - [x] List new features
  - [x] Provide migration instructions

- [x] Final Validation:
  - [x] Run all examples
  - [x] Verify all tests pass
  - [x] Check documentation completeness
  - [x] Test installation: `pip install -e .`
  - [x] Manual smoke testing

- [x] Git & Release:
  - [x] Commit all changes
  - [x] Create tag `v0.2.0`
  - [x] Push to GitHub
  - [x] Create GitHub release with notes
  - [x] Publish to PyPI

### Migration Impact Analysis

**What breaks:**
- ✋ `QueueRequest` no longer has `result` field
- ✋ Must use `params` field for passing data
- ✋ Generic type signatures changed from single to dual
- ✋ Processor function signature changed

**What stays the same:**
- ✅ Rate limiting functionality
- ✅ Queue mechanics
- ✅ Manager singleton pattern
- ✅ Response structure
- ✅ Error handling

**Migration effort:** Medium - requires code changes but straightforward


