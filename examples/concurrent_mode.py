"""Example of using concurrent requests mode."""

import asyncio
import time
from llm_queue import QueueManager, ModelConfig, QueueRequest, RateLimiterConfig, RateLimiterType


async def slow_llm_processor(request: QueueRequest[dict]) -> dict:
    """
    Simulate a slow LLM API call.

    This demonstrates the difference between concurrent and per-period limiting.
    """
    print(f"  [START] Request {request.id[:8]} - {time.strftime('%H:%M:%S')}")

    # Simulate API call taking 2 seconds
    await asyncio.sleep(2.0)

    print(f"  [END]   Request {request.id[:8]} - {time.strftime('%H:%M:%S')}")

    return {"request_id": request.id, "response": "Completed", "duration": 2.0}


async def demo_concurrent_mode():
    """Demonstrate concurrent requests limiting."""
    print("\n=== CONCURRENT REQUESTS MODE ===")
    print("Limiting to maximum 3 concurrent requests\n")

    manager: QueueManager[dict, dict] = QueueManager()

    # Configure with concurrent requests mode
    config = ModelConfig(
        model_id="concurrent-model",
        rate_limiters=[
            RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=3),
        ],
    )

    await manager.register_queue(config, slow_llm_processor)

    # Submit 10 requests
    print("Submitting 10 requests (each takes 2 seconds)...")
    print("Expected: Groups of 3 concurrent requests\n")

    start_time = time.time()

    requests = [QueueRequest(model_id="concurrent-model", params={}) for _ in range(10)]
    responses = await asyncio.gather(*[manager.submit_request(req) for req in requests])

    total_time = time.time() - start_time

    print(f"\n✓ All 10 requests completed in {total_time:.1f}s")
    print(f"  (Expected: ~7-8s with 3 concurrent, actual: {total_time:.1f}s)")

    await manager.shutdown_all()
    manager.reset_instance()


async def demo_per_period_mode():
    """Demonstrate requests per period limiting."""
    print("\n\n=== REQUESTS PER PERIOD MODE ===")
    print("Limiting to 5 requests per 10 seconds\n")

    manager: QueueManager[dict, dict] = QueueManager()

    # Configure with per-period mode
    config = ModelConfig(
        model_id="period-model",
        rate_limiters=[
            RateLimiterConfig(type=RateLimiterType.RPM, limit=5, time_period=10),
        ],
    )

    await manager.register_queue(config, slow_llm_processor)

    # Submit 10 requests
    print("Submitting 10 requests (each takes 2 seconds)...")
    print("Expected: First 5 start immediately, next 5 wait for time window\n")

    start_time = time.time()

    requests = [QueueRequest(model_id="period-model", params={}) for _ in range(10)]
    responses = await asyncio.gather(*[manager.submit_request(req) for req in requests])

    total_time = time.time() - start_time

    print(f"\n✓ All 10 requests completed in {total_time:.1f}s")
    print(f"  (Expected: ~12-14s with 5 per 10s, actual: {total_time:.1f}s)")

    await manager.shutdown_all()
    manager.reset_instance()


async def demo_comparison():
    """Compare both modes side by side."""
    print("\n\n=== MODE COMPARISON ===\n")

    manager: QueueManager[dict, dict] = QueueManager()

    # Register both modes
    configs = [
        ModelConfig(
            model_id="concurrent",
            rate_limiters=[
                RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=2),
            ],
        ),
        ModelConfig(
            model_id="per-period",
            rate_limiters=[
                RateLimiterConfig(type=RateLimiterType.RPM, limit=2, time_period=5),
            ],
        ),
    ]

    async def quick_processor(request: QueueRequest[dict]) -> dict:
        await asyncio.sleep(0.5)
        return {"done": True}

    for config in configs:
        await manager.register_queue(config, quick_processor)

    print("Submitting 6 requests to each mode...")

    # Test concurrent mode
    start = time.time()
    concurrent_requests = [QueueRequest(model_id="concurrent", params={}) for _ in range(6)]
    await asyncio.gather(*[manager.submit_request(req) for req in concurrent_requests])
    concurrent_time = time.time() - start

    # Test per-period mode
    start = time.time()
    period_requests = [QueueRequest(model_id="per-period", params={}) for _ in range(6)]
    await asyncio.gather(*[manager.submit_request(req) for req in period_requests])
    period_time = time.time() - start

    print(f"\nResults:")
    print(f"  Concurrent (max 2): {concurrent_time:.2f}s")
    print(f"  Per-period (2/5s): {period_time:.2f}s")

    await manager.shutdown_all()


async def main():
    """Run all demonstrations."""
    print("=" * 60)
    print("  LLM Queue - Concurrent vs Per-Period Rate Limiting")
    print("=" * 60)

    await demo_concurrent_mode()
    await demo_per_period_mode()
    await demo_comparison()

    print("\n" + "=" * 60)
    print("  All demonstrations completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
