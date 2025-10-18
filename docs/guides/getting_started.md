# Getting Started with LLM Queue

This guide will help you get started with the LLM Queue package.

## Installation

```bash
pip install llm-queue
```

For development:
```bash
pip install llm-queue[dev]
```

## Basic Concepts

### 1. Queue Manager

The `QueueManager` is a singleton that manages multiple queues for different models.

```python
from llm_queue import QueueManager

manager = QueueManager()
```

### 2. Model Configuration

Each model needs configuration specifying its rate limits:

```python
from llm_queue import ModelConfig, RateLimiterMode

config = ModelConfig(
    model_id="gpt-4",
    rate_limit=10,  # 10 requests per minute
    rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
    time_period=60  # 60 seconds
)
```

### 3. Processor Function

Define how to process requests for your LLM (now with type safety!):

```python
from llm_queue import QueueRequest

async def process_request(request: QueueRequest[dict]) -> dict:
    """Process an LLM request."""
    # Access parameters from request.params (not metadata!)
    prompt = request.params.get("prompt", "Hello")
    # Your API call logic here
    return {"response": f"Processed: {prompt}"}
```

### 4. Register and Use

Register your model and submit requests:

```python
# Register (now with type hints!)
manager: QueueManager[dict, dict] = QueueManager()
await manager.register_queue(config, process_request)

# Submit request (now with params!)
request = QueueRequest(
    model_id="gpt-4",
    params={"prompt": "Hello, world!"}  # NEW: params instead of metadata
)
response = await manager.submit_request(request)

print(response.result)  # {"response": "Processed: Hello, world!"}
```

## Rate Limiting Modes

### Requests Per Period

Limit the number of requests within a time window:

```python
ModelConfig(
    model_id="model-a",
    rate_limit=10,      # 10 requests
    time_period=60,     # per 60 seconds
    rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD
)
```

**Use case**: API providers with rate limits like "10 requests per minute"

### Concurrent Requests

Limit the number of simultaneous requests:

```python
ModelConfig(
    model_id="model-b",
    rate_limit=5,       # Max 5 concurrent
    rate_limiter_mode=RateLimiterMode.CONCURRENT_REQUESTS
)
```

**Use case**: Managing resource usage or connection pools

## Complete Example

```python
import asyncio
from llm_queue import QueueManager, ModelConfig, QueueRequest, RateLimiterMode

async def my_llm_processor(request: QueueRequest[dict]) -> dict:
    """Process LLM requests."""
    # Access parameters from request.params
    prompt = request.params.get("prompt", "Hello")
    # Simulate API call
    await asyncio.sleep(0.1)
    return {
        "response": f"Processed: {prompt}",
        "model": request.model_id,
        "request_id": request.id
    }

async def main():
    # Setup (now with type hints!)
    manager: QueueManager[dict, dict] = QueueManager()
    
    config = ModelConfig(
        model_id="my-model",
        rate_limit=5,
        rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
        time_period=10
    )
    
    await manager.register_queue(config, my_llm_processor)
    
    # Use (now with params!)
    request = QueueRequest(
        model_id="my-model",
        params={"prompt": "Hello, LLM Queue!"}
    )
    response = await manager.submit_request(request)
    
    print(f"Status: {response.status}")
    print(f"Result: {response.result}")
    
    # Cleanup
    await manager.shutdown_all()

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- Check out the [examples](../examples/) directory
- Read the [API documentation](../docs/api/)
- Learn about [advanced features](../README.md#advanced-usage)

## Common Patterns

### Multiple Models

```python
models = [
    ModelConfig(model_id="gpt-4", rate_limit=10, time_period=60),
    ModelConfig(model_id="claude-3", rate_limit=5, time_period=60),
]

await manager.register_all_queues(models, processor)
```

### Error Handling

```python
response = await manager.submit_request(request)

if response.status == "completed":
    print(response.result)
else:
    print(f"Error: {response.error}")
```

### Monitoring

```python
# Get queue info
info = manager.get_queue_info("gpt-4")
print(f"Queue size: {info['queue_size']}")
print(f"Usage: {info['rate_limiter_usage']}/{info['rate_limit']}")
```

## Troubleshooting

### Requests timing out?
- Check your rate limits
- Verify processor function works correctly
- Monitor queue sizes

### High memory usage?
- Reduce queue sizes
- Implement proper cleanup
- Check for memory leaks in processor

### Rate limits not working?
- Verify configuration
- Check time_period units (seconds)
- Test with simple examples first

## Getting Help

- [GitHub Issues](https://github.com/yourusername/llm-queue/issues)
- [Examples Directory](../examples/)
- [API Documentation](../docs/api/)
