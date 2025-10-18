# LLM Queue - Quick Reference

## Installation

```bash
pip install llm-queue
```

## Basic Usage

```python
import asyncio
from llm_queue import QueueManager, ModelConfig, QueueRequest, RateLimiterMode

async def processor(request: QueueRequest) -> dict:
    # Your LLM API call here
    return {"response": "Hello!"}

async def main():
    manager = QueueManager()
    
    config = ModelConfig(
        model_id="gpt-4",
        rate_limit=10,
        time_period=60
    )
    
    await manager.register_queue(config, processor)
    
    request = QueueRequest(model_id="gpt-4")
    response = await manager.submit_request(request)
    
    print(response.result)
    await manager.shutdown_all()

asyncio.run(main())
```

## Rate Limiter Modes

### Requests Per Period
```python
ModelConfig(
    model_id="model",
    rate_limit=10,          # 10 requests
    time_period=60,         # per 60 seconds
    rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD
)
```

### Concurrent Requests
```python
ModelConfig(
    model_id="model",
    rate_limit=5,           # Max 5 concurrent
    rate_limiter_mode=RateLimiterMode.CONCURRENT_REQUESTS
)
```

## Key Classes

### QueueManager
```python
manager = QueueManager()                                    # Get singleton instance
await manager.register_queue(config, processor)             # Register a model
await manager.register_all_queues(configs, processor)       # Register multiple models
response = await manager.submit_request(request)            # Submit request
status = await manager.get_status(model_id, request_id)     # Get status
info = manager.get_queue_info(model_id)                     # Get queue info
models = manager.get_registered_models()                    # List registered models
await manager.shutdown_all()                                # Graceful shutdown
```

### ModelConfig
```python
config = ModelConfig(
    model_id="gpt-4",                                       # Model identifier
    rate_limit=10,                                          # Rate limit value
    rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,  # Mode
    time_period=60                                          # Time period (seconds)
)
```

### QueueRequest
```python
request = QueueRequest(
    model_id="gpt-4",                   # Required: model to use
    metadata={"prompt": "Hello"}        # Optional: custom data
)

# Automatically generated:
# - id: Unique request ID
# - created_at: Timestamp
# - status: Request status
```

### QueueResponse
```python
response = await manager.submit_request(request)

response.request_id         # Original request ID
response.model_id           # Model used
response.status             # "completed" or "failed"
response.result             # Result (if completed)
response.error              # Error message (if failed)
response.processing_time    # Time taken (seconds)
```

## Request Status

- `"pending"`: Waiting in queue
- `"processing"`: Currently being processed
- `"completed"`: Successfully completed
- `"failed"`: Processing failed

## Error Handling

```python
from llm_queue import ModelNotRegistered, ProcessingError

try:
    response = await manager.submit_request(request)
    if response.status == "completed":
        print(response.result)
    else:
        print(f"Failed: {response.error}")
except ModelNotRegistered:
    print("Model not registered")
```

## Monitoring

```python
# Single queue info
info = manager.get_queue_info("gpt-4")
print(f"Queue size: {info['queue_size']}")
print(f"Usage: {info['rate_limiter_usage']}/{info['rate_limit']}")

# All queues
all_info = manager.get_all_queues_info()
for model_id, info in all_info.items():
    print(f"{model_id}: {info['queue_size']} queued")
```

## Utilities

```python
from llm_queue import setup_logging, get_logger, Timer

# Logging
setup_logging(level=logging.INFO)
logger = get_logger("my_app")

# Timing
async with Timer() as timer:
    await some_operation()
print(f"Took {timer.elapsed}s")
```

## Common Patterns

### Multiple Models
```python
models = [
    ModelConfig(model_id="gpt-4", rate_limit=10, time_period=60),
    ModelConfig(model_id="claude", rate_limit=5, time_period=60),
]
await manager.register_all_queues(models, processor)
```

### Batch Processing
```python
requests = [QueueRequest(model_id="gpt-4") for _ in range(10)]
responses = await asyncio.gather(*[
    manager.submit_request(req) for req in requests
])
```

### Custom Metadata
```python
request = QueueRequest(
    model_id="gpt-4",
    metadata={
        "prompt": "Translate to French",
        "max_tokens": 100,
        "temperature": 0.7
    }
)

# Access in processor
async def processor(request: QueueRequest) -> dict:
    prompt = request.metadata["prompt"]
    # ... use metadata
```

## Best Practices

1. **Always shutdown gracefully**: Use `await manager.shutdown_all()`
2. **Handle errors**: Check `response.status` before using `response.result`
3. **Use appropriate mode**: Per-period for API limits, concurrent for resources
4. **Monitor queues**: Check queue sizes and usage regularly
5. **Add metadata**: Include all needed info in request metadata
6. **Type hints**: Use `QueueRequest[YourType]` for type safety

## Example: OpenAI Integration

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def openai_processor(request: QueueRequest) -> dict:
    response = await client.chat.completions.create(
        model=request.model_id,
        messages=[{"role": "user", "content": request.metadata["prompt"]}]
    )
    return {
        "content": response.choices[0].message.content,
        "usage": response.usage.dict()
    }

# Setup
manager = QueueManager()
config = ModelConfig(model_id="gpt-4", rate_limit=10, time_period=60)
await manager.register_queue(config, openai_processor)

# Use
request = QueueRequest(
    model_id="gpt-4",
    metadata={"prompt": "Hello!"}
)
response = await manager.submit_request(request)
print(response.result["content"])
```

## Links

- [Full Documentation](../README.md)
- [Getting Started Guide](../docs/guides/getting_started.md)
- [Examples](../examples/)
- [GitHub Repository](https://github.com/yourusername/llm-queue)
