"""Basic usage example of llm-queue package."""

import asyncio
from llm_queue import QueueManager, ModelConfig, QueueRequest, RateLimiterMode


# Define your LLM processor function
async def process_llm_request(request: QueueRequest) -> dict:
    """
    Process an LLM request.

    This is where you would implement your actual LLM API call.
    For this example, we just simulate a response.
    """
    # Simulate some processing time
    await asyncio.sleep(0.1)

    return {
        "request_id": request.id,
        "model": request.model_id,
        "response": f"Hello from {request.model_id}!",
        "tokens_used": 42,
    }


async def main():
    """Main example function."""
    print("=== LLM Queue Basic Example ===\n")

    # Initialize the queue manager (singleton)
    manager = QueueManager()

    # Configure a model with rate limiting
    # This allows 10 requests per 60 seconds
    config = ModelConfig(
        model_id="gpt-4",
        rate_limit=10,
        rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
        time_period=60,
    )

    print(f"Registering model: {config.model_id}")
    print(f"Rate limit: {config.rate_limit} requests per {config.time_period} seconds\n")

    # Register the model with its processor function
    await manager.register_queue(config, process_llm_request)

    # Submit a single request
    print("Submitting a request...")
    request = QueueRequest(model_id="gpt-4")
    response = await manager.submit_request(request)

    print(f"\nResponse received:")
    print(f"  Status: {response.status}")
    print(f"  Result: {response.result}")
    print(f"  Processing time: {response.processing_time:.3f}s")

    # Submit multiple requests concurrently
    print("\n\nSubmitting 5 concurrent requests...")
    requests = [QueueRequest(model_id="gpt-4") for _ in range(5)]

    responses = await asyncio.gather(*[manager.submit_request(req) for req in requests])

    print(f"\nProcessed {len(responses)} requests")
    for i, resp in enumerate(responses, 1):
        print(f"  Request {i}: {resp.status} ({resp.processing_time:.3f}s)")

    # Check queue information
    queue_info = manager.get_queue_info("gpt-4")
    print(f"\nQueue Info:")
    print(f"  Model: {queue_info['model_id']}")
    print(f"  Queue size: {queue_info['queue_size']}")
    print(f"  Rate limiter usage: {queue_info['rate_limiter_usage']}/{queue_info['rate_limit']}")

    # Graceful shutdown
    print("\nShutting down...")
    await manager.shutdown_all()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
