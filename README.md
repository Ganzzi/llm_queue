# LLM Queue

A high-performance Python package for managing LLM API calls with intelligent rate limiting and queueing.

## Installation

```bash
pip install llm-queue
```

For development:
```bash
pip install llm-queue[dev]
```

## Quick Start

```python
import asyncio
from llm_queue import QueueManager, ModelConfig, QueueRequest, RateLimiterConfig, RateLimiterType

# Define your LLM processor function
async def process_llm_request(request: QueueRequest[dict]) -> dict:
    """Process an LLM request - implement your API call here."""
    prompt = request.params.get("prompt", "")
    # Call your LLM API (OpenAI, Anthropic, etc.)
    return {"response": f"Hello from LLM! You said: {prompt}"}

async def main():
    # Initialize the queue manager
    manager: QueueManager[dict, dict] = QueueManager()
    
    # Configure a model with rate limiting
    config = ModelConfig(
        model_id="gpt-4",
        rate_limiters=[
            RateLimiterConfig(type=RateLimiterType.RPM, limit=500),
            RateLimiterConfig(type=RateLimiterType.TPM, limit=30000),
        ]
    )
    
    # Register the model
    await manager.register_queue(config, process_llm_request)
    
    # Submit a request
    request = QueueRequest(
        model_id="gpt-4",
        params={"prompt": "Tell me a joke"}
    )
    response = await manager.submit_request(request)
    
    print(f"Status: {response.status}")
    print(f"Result: {response.result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- Async-first design built on asyncio
- Multiple rate limiting modes: requests per period (RPM/RPD), tokens per period (TPM/TPD), concurrent requests
- Per-model configuration with multiple rate limiters
- Type-safe API with full type hints and Pydantic models
- Generic support for flexible parameter and result types
- Request status tracking and monitoring
- Singleton manager for centralized queue management
- Token usage tracking with estimation and correction

## Rate Limiting Configuration

The package uses a flexible multi-rate limiter system that allows combining multiple rate limiting strategies:

```python
from llm_queue import RateLimiterConfig, RateLimiterType

config = ModelConfig(
    model_id="gpt-4",
    rate_limiters=[
        RateLimiterConfig(type=RateLimiterType.RPM, limit=500),
        RateLimiterConfig(type=RateLimiterType.TPM, limit=30000),
        RateLimiterConfig(type=RateLimiterType.RPD, limit=10000),
    ]
)
```

### Token Usage Tracking

Track estimated and actual token usage:

```python
# Submit with estimates
request = QueueRequest(
    model_id="gpt-4",
    params={"prompt": "..."},
    estimated_input_tokens=100,
    estimated_output_tokens=50
)
response = await manager.submit_request(request)

# Update with actual usage after completion
await manager.update_token_usage(
    model_id="gpt-4",
    request_id=request.id,
    input_tokens=85,
    output_tokens=40
)
```

## API Overview

### Core Classes

- `QueueManager`: Singleton manager for multiple model queues
- `Queue`: Individual queue for a model with rate limiting
- `ModelConfig`: Configuration for a model and its rate limiters
- `QueueRequest`: Request to be processed
- `QueueResponse`: Response from processing
- `RateLimiterConfig`: Configuration for a single rate limiter
- `RateLimiterType`: Enum for rate limiter types (RPM, RPD, TPM, TPD, CONCURRENT)
- `RequestStatus`: Enum for request status (PENDING, PROCESSING, COMPLETED, FAILED, TIMEOUT)

### Exceptions

- `LLMQueueException`: Base exception
- `RateLimitExceeded`: Rate limit exceeded
- `QueueTimeout`: Queue operation timeout
- `ModelNotRegistered`: Model not found in manager
- `InvalidConfiguration`: Invalid configuration provided
- `ProcessingError`: Request processing failed

## Testing

```bash
# PR Gate (unit tests only - no external dependencies)
uv run pytest -m "not integration and not e2e" -q

# Full test suite
uv run pytest -q

# With coverage
uv run pytest -m "not integration and not e2e" --cov --cov-report=term-missing
```

## Configuration

### Rate Limiter Types

- `RPM`: Requests per minute
- `RPD`: Requests per day
- `TPM`: Tokens per minute (input + output)
- `TPD`: Tokens per day
- `ITPM`: Input tokens per minute
- `OTPM`: Output tokens per minute
- `CONCURRENT`: Maximum concurrent requests

### Environment Variables

No environment variables required. All configuration is done through code.

## Documentation

- [Development Guide](docs/development.md) - Setup, testing, and development workflow
- [API Reference](docs/api-reference.md) - Complete API documentation
- [Architecture](docs/architecture.md) - System design and patterns
- [Rate Limiter Chain](docs/dev/RATE_LIMITER_INDEX.md) - Deep dive into rate limiting

## Examples

See the [examples](examples/) directory:

- [basic_usage.py](examples/basic_usage.py) - Simple usage example
- [openai_example.py](examples/openai_example.py) - OpenAI integration
- [anthropic_example.py](examples/anthropic_example.py) - Anthropic integration
- [concurrent_mode.py](examples/concurrent_mode.py) - Concurrent limiting example
- [advanced_usage.py](examples/advanced_usage.py) - Advanced features

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a Pull Request

## License

MIT

## Support

- Issues: [GitHub Issues](https://github.com/Ganzzi/llm-queue/issues)
- Documentation: See [docs](docs/)
