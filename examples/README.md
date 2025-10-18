# Examples

This directory contains example code demonstrating how to use the `llm-queue` package.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)
Introduction to the core functionality:
- Setting up a queue manager
- Configuring rate limits
- Submitting requests
- Handling responses

```bash
python examples/basic_usage.py
```

### 2. OpenAI Integration (`openai_example.py`)
Real-world integration with OpenAI API:
- Processor implementation for OpenAI
- Multiple model configuration
- Error handling
- Token usage tracking

**Requirements**: `pip install openai`

```bash
export OPENAI_API_KEY="your-api-key"
python examples/openai_example.py
```

### 3. Concurrent Mode (`concurrent_mode.py`)
Demonstrates the difference between rate limiting modes:
- Requests per period limiting
- Concurrent requests limiting
- Performance comparison

```bash
python examples/concurrent_mode.py
```

### 4. Advanced Usage (`advanced_usage.py`)
Advanced features and patterns:
- Error handling and monitoring
- Batch processing across multiple models
- Dynamic model registration
- Custom metrics collection

```bash
python examples/advanced_usage.py
```

## Running the Examples

### Prerequisites

1. Install the package:
```bash
pip install -e .
```

2. For OpenAI example:
```bash
pip install openai
export OPENAI_API_KEY="your-api-key"
```

### Running All Examples

```bash
# Basic usage
python -m examples.basic_usage

# With OpenAI
python -m examples.openai_example

# Concurrent mode demo
python -m examples.concurrent_mode

# Advanced features
python -m examples.advanced_usage
```

## Example Patterns

### Creating a Custom Processor

```python
async def my_processor(request: QueueRequest) -> dict:
    """Custom processor for your LLM API."""
    # Extract data from request
    prompt = request.metadata.get("prompt")
    
    # Call your API
    result = await your_api_call(prompt)
    
    # Return structured result
    return {"response": result}
```

### Configuring Multiple Models

```python
models = [
    ModelConfig(
        model_id="fast-model",
        rate_limit=50,
        time_period=60
    ),
    ModelConfig(
        model_id="slow-model",
        rate_limit=10,
        time_period=60
    ),
]

await manager.register_all_queues(models, processor)
```

### Error Handling

```python
try:
    response = await manager.submit_request(request)
    if response.status == "completed":
        print(response.result)
    else:
        print(f"Error: {response.error}")
except ModelNotRegistered:
    print("Model not found")
```

## Tips

1. **Start with `basic_usage.py`** to understand the core concepts
2. **Use concurrent mode** for I/O-bound operations
3. **Use per-period mode** for API rate limits
4. **Monitor queue metrics** in production
5. **Implement proper error handling** for real applications

## Contributing Examples

Have a great example? Please contribute!

1. Create a new example file
2. Add documentation
3. Update this README
4. Submit a pull request
