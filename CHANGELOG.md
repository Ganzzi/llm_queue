# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial package structure
- Core queue and rate limiting functionality
- Support for two rate limiting modes (requests per period, concurrent requests)
- Pydantic models for type safety
- Comprehensive documentation
- Examples for common use cases

## [0.3.0] - 2025-12-10

### Added
- **Multi-Rate Limiter Support**: Configure multiple rate limiters per model (RPM, TPM, RPD, etc.).
- **Token-Based Limiting**: Support for TPM (Tokens Per Minute), TPD, ITPM (Input), OTPM (Output).
- **Token Usage Tracking**: `update_token_usage` method to adjust limits based on actual usage.
- **RateLimiterChain**: Internal component to manage multiple limiters.

### Changed
- **Queue**: Updated to use `RateLimiterChain` internally.
- **ModelConfig**: Added `rate_limiters` field. Legacy `rate_limit` fields are now deprecated but supported.
- **QueueResponse**: Added `input_tokens_used` and `output_tokens_used` fields.

### Deprecated
- `RateLimiterMode` enum is deprecated in favor of `RateLimiterType`.
- `ModelConfig.rate_limit` and `ModelConfig.rate_limiter_mode` are deprecated.

## [0.2.0] - 2025-01-XX

### Added
- **Breaking Change**: Dual-generic type system for better type safety
  - `QueueRequest[P]` now uses `params: P` instead of `metadata: dict`
  - `QueueResponse[T]` returns typed results
  - `QueueManager[P, T]` for fully generic queue management
- **New Feature**: `wait_for_completion` parameter in `QueueRequest`
  - `wait_for_completion=False` enables fire-and-forget requests
  - Returns immediately with `PENDING` status
  - Status can be polled via `get_status()` method
- Enhanced status tracking for asynchronous requests
- New examples demonstrating type-safe usage with Pydantic models
- Additional test coverage for new features

### Changed
- **Breaking Change**: `QueueRequest` constructor now requires `params` instead of `metadata`
- **Breaking Change**: Processor functions now take `QueueRequest[P]` and return `T`
- **Breaking Change**: All generic signatures updated to use dual generics `QueueManager[P, T]`
- Updated all example code to use new API
- Improved documentation with new type-safe patterns

### Fixed
- Status tracking now properly handles asynchronous requests
- Memory cleanup for completed async responses

## [0.1.0] - 2025-10-18

### Added
- Initial release of llm-queue
- `QueueManager` singleton for managing multiple model queues
- `Queue` class for individual model queue management
- `RateLimiter` with dual modes:
  - Requests per time period
  - Concurrent requests
- Type-safe models with Pydantic:
  - `ModelConfig`
  - `QueueRequest[T]`
  - `QueueResponse[T]`
  - `RateLimiterMode`
  - `RequestStatus`
- Custom exceptions for better error handling
- Utility functions for logging and timing
- Comprehensive test suite
- Documentation and examples
- MIT License

[Unreleased]: https://github.com/yourusername/llm-queue/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/llm-queue/releases/tag/v0.1.0
