# LLM Queue API Reference

This document provides a comprehensive API reference for the `llm_queue` package.

## Table of Contents

- [Core Classes](#core-classes)
  - [QueueManager](#queuemanager)
  - [Queue](#queue)
- [Configuration Models](#configuration-models)
  - [ModelConfig](#modelconfig)
  - [RateLimiterConfig](#ratelimiterconfig)
- [Request/Response Models](#requestresponse-models)
  - [QueueRequest](#queuerequest)
  - [QueueResponse](#queueresponse)
- [Enums](#enums)
  - [RateLimiterType](#ratelimitertype)
  - [RateLimiterMode](#ratelimitermode)
  - [RequestStatus](#requeststatus)
- [Exceptions](#exceptions)

---

## Core Classes

### QueueManager

The central singleton manager for multiple model queues.

```python
from llm_queue import QueueManager

manager = QueueManager()
```

#### Methods

| Method | Description |
|--------|-------------|
| `register_queue(model_config, processor_func)` | Register a new model with its queue |
| `register_all_queues(models, processor_func)` | Register multiple models at once |
| `submit_request(request)` | Submit a request to the appropriate queue |
| `update_token_usage(model_id, request_id, input_tokens, output_tokens)` | Update actual token usage for a request |
| `get_status(model_id, request_id)` | Get the status of a specific request |
| `get_registered_models()` | Get list of registered model IDs |
| `get_queue_info(model_id)` | Get information about a specific queue |
| `get_all_queues_info()` | Get information about all registered queues |
| `shutdown_all()` | Gracefully shutdown all queues |
| `reset_instance()` | Reset the singleton instance (testing only) |

---

### Queue

Individual queue for a model with rate limiting.

```python
from llm_queue import Queue

queue = Queue(
    model_id="gpt-4",
    processor_func=my_processor,
    rate_limit=10,
    time_period=60
)
```

#### Methods

| Method | Description |
|--------|-------------|
| `enqueue(request)` | Add a request to the queue |
| `get_status(request_id)` | Get the status of a request |
| `update_token_usage(request_id, input_tokens, output_tokens)` | Update token usage |
| `get_queue_size()` | Get the number of pending requests |
| `get_rate_limiter_usage()` | Get current rate limiter usage |
| `shutdown()` | Gracefully shutdown the queue |

---

## Configuration Models

### ModelConfig

Configuration for a model's queue and rate limiting.

```python
from llm_queue import ModelConfig, RateLimiterConfig, RateLimiterType

# V2 Configuration (recommended)
config = ModelConfig(
    model_id="gpt-4",
    rate_limiters=[
        RateLimiterConfig(type=RateLimiterType.RPM, limit=500),
        RateLimiterConfig(type=RateLimiterType.TPM, limit=30000),
    ]
)

# V1 Configuration (legacy, still supported)
config = ModelConfig(
    model_id="gpt-4",
    rate_limit=10,
    rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
    time_period=60
)
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | `str` | Unique identifier for the model |
| `rate_limiters` | `List[RateLimiterConfig]` | V2: List of rate limiter configurations |
| `rate_limit` | `Optional[int]` | V1 (deprecated): Rate limit value |
| `rate_limiter_mode` | `Optional[RateLimiterMode]` | V1 (deprecated): Rate limiting mode |
| `time_period` | `Optional[int]` | V1 (deprecated): Time period in seconds |

---

### RateLimiterConfig

Configuration for a single rate limiter.

```python
from llm_queue import RateLimiterConfig, RateLimiterType

config = RateLimiterConfig(
    type=RateLimiterType.TPM,
    limit=30000,
    time_period=60  # Optional, defaults based on type
)
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | `RateLimiterType` | Type of rate limiter |
| `limit` | `int` | Maximum limit value |
| `time_period` | `Optional[int]` | Time period in seconds (auto-set based on type) |

---

## Request/Response Models

### QueueRequest

Request to be processed by the queue.

```python
from llm_queue import QueueRequest

request = QueueRequest(
    model_id="gpt-4",
    params={"prompt": "Hello, world!"},
    estimated_input_tokens=10,
    estimated_output_tokens=50,
    wait_for_completion=True
)
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Auto-generated unique request ID |
| `model_id` | `str` | Target model ID |
| `params` | `P` | Generic request parameters |
| `estimated_input_tokens` | `Optional[int]` | Estimated input tokens for token-based limiting |
| `estimated_output_tokens` | `Optional[int]` | Estimated output tokens for token-based limiting |
| `wait_for_completion` | `bool` | Whether to wait for completion (default: `True`) |

---

### QueueResponse

Response from the queue after processing.

```python
response = await manager.submit_request(request)
print(response.status)  # RequestStatus.COMPLETED
print(response.result)  # {"response": "Hello!"}
```

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | `str` | ID of the original request |
| `model_id` | `str` | Model that processed the request |
| `status` | `RequestStatus` | Current status of the request |
| `result` | `Optional[T]` | Generic result from processor |
| `error` | `Optional[str]` | Error message if failed |
| `processing_time` | `Optional[float]` | Processing time in seconds |
| `input_tokens_used` | `Optional[int]` | Actual input tokens used |
| `output_tokens_used` | `Optional[int]` | Actual output tokens used |

---

## Enums

### RateLimiterType

Types of rate limiters available (V2).

| Value | Description |
|-------|-------------|
| `RPM` | Requests per Minute |
| `RPD` | Requests per Day |
| `TPM` | Tokens per Minute (input + output) |
| `TPD` | Tokens per Day (input + output) |
| `ITPM` | Input Tokens per Minute |
| `OTPM` | Output Tokens per Minute |
| `CONCURRENT` | Concurrent Requests |

---

### RateLimiterMode

Rate limiting modes (V1, deprecated).

| Value | Description |
|-------|-------------|
| `REQUESTS_PER_PERIOD` | Limit requests per time period |
| `CONCURRENT_REQUESTS` | Limit concurrent requests |

---

### RequestStatus

Status of a queue request.

| Value | Description |
|-------|-------------|
| `PENDING` | Request is queued |
| `PROCESSING` | Request is being processed |
| `COMPLETED` | Request completed successfully |
| `FAILED` | Request failed with error |

---

## Exceptions

| Exception | Description |
|-----------|-------------|
| `LLMQueueException` | Base exception for all llm_queue errors |
| `RateLimitExceeded` | Rate limit has been exceeded |
| `QueueTimeout` | Queue operation timed out |
| `ModelNotRegistered` | Model ID is not registered |
| `InvalidConfiguration` | Invalid configuration provided |
| `ProcessingError` | Error during request processing |

---

## Usage Examples

### Basic Usage

```python
import asyncio
from llm_queue import QueueManager, ModelConfig, QueueRequest

async def processor(request):
    return {"response": f"Processed: {request.params}"}

async def main():
    manager = QueueManager()
    
    config = ModelConfig(model_id="my-model", rate_limit=10, time_period=60)
    await manager.register_queue(config, processor)
    
    request = QueueRequest(model_id="my-model", params={"text": "Hello"})
    response = await manager.submit_request(request)
    
    print(response.result)
    await manager.shutdown_all()

asyncio.run(main())
```

### Multi-Rate Limiter

```python
from llm_queue import ModelConfig, RateLimiterConfig, RateLimiterType

config = ModelConfig(
    model_id="gpt-4",
    rate_limiters=[
        RateLimiterConfig(type=RateLimiterType.RPM, limit=500),
        RateLimiterConfig(type=RateLimiterType.TPM, limit=30000),
        RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=10),
    ]
)
```

### Token Usage Tracking

```python
# Submit with estimates
request = QueueRequest(
    model_id="gpt-4",
    params={"prompt": "..."},
    estimated_input_tokens=100,
    estimated_output_tokens=50
)
response = await manager.submit_request(request)

# Update with actual usage
await manager.update_token_usage(
    model_id="gpt-4",
    request_id=request.id,
    input_tokens=85,
    output_tokens=42
)
```
