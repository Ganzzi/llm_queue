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
