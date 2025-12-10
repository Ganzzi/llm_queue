"""Example of using multi-rate limiters."""

import asyncio
from llm_queue import (
    QueueManager,
    ModelConfig,
    QueueRequest,
    RateLimiterConfig,
    RateLimiterType,
)


async def process_request(request: QueueRequest[dict]) -> dict:
    """Mock processor."""
    await asyncio.sleep(0.1)
    return {"response": "Processed"}


async def main():
    manager = QueueManager()

    # Configure with multiple rate limiters
    config = ModelConfig(
        model_id="gpt-4",
        rate_limiters=[
            RateLimiterConfig(type=RateLimiterType.RPM, limit=10),
            RateLimiterConfig(type=RateLimiterType.TPM, limit=1000),
        ],
    )
    await manager.register_queue(config, process_request)

    # Submit request with token estimates
    req = QueueRequest(
        model_id="gpt-4",
        params={"prompt": "Hello"},
        estimated_input_tokens=50,
        estimated_output_tokens=20,
    )

    print("Submitting request...")
    response = await manager.submit_request(req)
    print(f"Status: {response.status}")

    # Update actual usage
    print("Updating token usage...")
    await manager.update_token_usage(
        model_id="gpt-4", request_id=req.id, input_tokens=45, output_tokens=15
    )

    # Check status
    status = await manager.get_status("gpt-4", req.id)
    print(f"Input tokens used: {status.input_tokens_used}")
    print(f"Output tokens used: {status.output_tokens_used}")

    await manager.shutdown_all()


if __name__ == "__main__":
    asyncio.run(main())
