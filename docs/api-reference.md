# API Reference

## Core Classes

### QueueManager
The main entry point for the library. Manages multiple queues for different models.

```python
from llm_queue import QueueManager

manager = QueueManager()
```

**Methods:**
- `register_queue(config, processor)` - Register a queue for a model
- `register_all_queues(configs, processor)` - Register multiple queues
- `submit_request(request)` - Submit a request to the appropriate queue
- `get_status(model_id, request_id)` - Get status of a request
- `update_token_usage(model_id, request_id, input_tokens, output_tokens)` - Update token usage after processing
- `get_queue_info(model_id)` - Get queue metrics
- `get_all_queues_info()` - Get metrics for all queues
- `shutdown_all()` - Gracefully shut down all queues
- `reset_instance()` - Reset the singleton instance

### Queue
Individual queue for a specific model. Usually accessed through QueueManager.

**Methods:**
- `enqueue(request)` - Add a request to the queue
- `get_status(request_id)` - Get status of a specific request
- `get_queue_size()` - Get current queue size
- `get_rate_limiter_usage()` - Get current rate limiter usage
- `update_token_usage(request_id, input_tokens, output_tokens)` - Update token usage
- `shutdown()` - Shut down the queue

### Models

#### ModelConfig
Configuration for a model and its rate limiters.

```python
from llm_queue import ModelConfig, RateLimiterConfig, RateLimiterType

config = ModelConfig(
    model_id="gpt-4",
    rate_limiters=[
        RateLimiterConfig(type=RateLimiterType.RPM, limit=500),
        RateLimiterConfig(type=RateLimiterType.TPM, limit=30000),
    ]
)
```

#### QueueRequest
Request to be processed by a queue.

```python
from llm_queue import QueueRequest

request = QueueRequest(
    model_id="gpt-4",
    params={"prompt": "Hello"},
    estimated_input_tokens=10,
    estimated_output_tokens=20,
    wait_for_completion=True
)
```

#### QueueResponse
Response from processing a request.

**Attributes:**
- `request_id` - ID of the original request
- `model_id` - ID of the model that processed the request
- `status` - Status of the request (RequestStatus enum)
- `result` - Result of processing
- `error` - Error message if processing failed
- `processing_time` - Time taken to process the request

#### RateLimiterConfig
Configuration for a single rate limiter.

**Attributes:**
- `type` - Rate limiter type (RateLimiterType enum)
- `limit` - Maximum allowed value
- `time_period` - Time period in seconds (default: 60)

#### RateLimiterType
Enum for different types of rate limiters:
- `RPM` - Requests per minute
- `RPD` - Requests per day  
- `TPM` - Total tokens per minute (input + output)
- `TPD` - Total tokens per day
- `ITPM` - Input tokens per minute
- `OTPM` - Output tokens per minute
- `CONCURRENT` - Maximum concurrent requests

#### RequestStatus
Enum for request status:
- `PENDING` - Request is queued
- `PROCESSING` - Request is being processed
- `COMPLETED` - Request completed successfully
- `FAILED` - Request failed during processing
- `TIMEOUT` - Request timed out

### Rate Limiters

#### BaseRateLimiter
Abstract base class for all rate limiters.

#### RequestRateLimiter
Rate limiter for request counts (RPM, RPD).

#### TokenRateLimiter  
Rate limiter for token counts (TPM, TPD, ITPM, OTPM).

#### ConcurrentRateLimiter
Rate limiter for concurrent requests.

#### RateLimiterChain
Manages multiple rate limiters together, ensuring all pass before allowing a request.

### Utilities

#### Timer
Utility for measuring execution time.

#### setup_logging()
Configure logging for the library.

#### get_logger(name)
Get a logger instance for the library.

#### with_timeout(coro, timeout)
Execute a coroutine with a timeout.

## Exceptions

### LLMQueueException
Base exception for all library exceptions.

### RateLimitExceeded
Raised when a rate limit is exceeded.

### QueueTimeout
Raised when a queue operation times out.

### ModelNotRegistered
Raised when trying to use an unregistered model.

### InvalidConfiguration
Raised when configuration is invalid.

### ProcessingError
Raised when request processing fails.

## Functions

### create_chain(limiters)
Create a RateLimiterChain from a list of individual limiters.

### create_rate_limiter(config)
Create a rate limiter from a configuration.