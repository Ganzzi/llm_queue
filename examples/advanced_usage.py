"""Advanced usage examples with error handling, monitoring, and custom features."""

import asyncio
import logging
from typing import Any, Dict
from llm_queue import (
    QueueManager,
    ModelConfig,
    QueueRequest,
    RateLimiterMode,
    setup_logging,
    get_logger,
    Timer,
)


# Set up logging
setup_logging(level=logging.INFO)
logger = get_logger("advanced_example")


class MonitoredProcessor:
    """LLM processor with monitoring and error handling."""

    def __init__(self):
        """Initialize the processor with metrics."""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_processing_time = 0.0

    async def process_request(self, request: QueueRequest) -> Dict[str, Any]:
        """
        Process request with monitoring.

        Args:
            request: Queue request to process

        Returns:
            Processing result

        Raises:
            Exception: If processing fails
        """
        self.total_requests += 1

        # Use timer context manager
        async with Timer() as timer:
            try:
                # Simulate processing
                prompt = request.metadata.get("prompt", "")

                # Simulate potential failure
                if "fail" in prompt.lower():
                    raise ValueError("Simulated failure")

                await asyncio.sleep(0.1)

                result = {
                    "request_id": request.id,
                    "response": f"Processed: {prompt}",
                    "model": request.model_id,
                }

                self.successful_requests += 1
                logger.info(f"Request {request.id[:8]} completed successfully")

                return result

            except Exception as e:
                self.failed_requests += 1
                logger.error(f"Request {request.id[:8]} failed: {e}")
                raise

            finally:
                self.total_processing_time += timer.elapsed

    def get_metrics(self) -> Dict[str, Any]:
        """Get processor metrics."""
        avg_time = (
            self.total_processing_time / self.total_requests if self.total_requests > 0 else 0
        )

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (
                self.successful_requests / self.total_requests * 100
                if self.total_requests > 0
                else 0
            ),
            "average_processing_time": avg_time,
        }


async def demo_error_handling():
    """Demonstrate error handling."""
    print("\n=== Error Handling Demo ===\n")

    processor = MonitoredProcessor()
    manager = QueueManager()

    config = ModelConfig(
        model_id="test-model",
        rate_limit=5,
        rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
        time_period=10,
    )

    await manager.register_queue(config, processor.process_request)

    # Mix of successful and failing requests
    prompts = [
        "Hello world",
        "This will fail",  # Contains "fail"
        "Another success",
        "This will also fail",  # Contains "fail"
        "Final success",
    ]

    print(f"Submitting {len(prompts)} requests (some will fail)...\n")

    for prompt in prompts:
        request = QueueRequest(model_id="test-model", metadata={"prompt": prompt})

        response = await manager.submit_request(request)

        if response.status == "completed":
            print(f"✓ '{prompt}' - Success")
        else:
            print(f"✗ '{prompt}' - Failed: {response.error}")

    # Show metrics
    metrics = processor.get_metrics()
    print(f"\n=== Metrics ===")
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Successful: {metrics['successful_requests']}")
    print(f"Failed: {metrics['failed_requests']}")
    print(f"Success rate: {metrics['success_rate']:.1f}%")
    print(f"Avg processing time: {metrics['average_processing_time']:.3f}s")

    await manager.shutdown_all()
    manager.reset_instance()


async def demo_batch_processing():
    """Demonstrate batch processing multiple models."""
    print("\n\n=== Batch Processing Demo ===\n")

    manager = QueueManager()

    # Register multiple models
    models = [
        ModelConfig(model_id="model-a", rate_limit=5, time_period=10),
        ModelConfig(model_id="model-b", rate_limit=3, time_period=10),
        ModelConfig(
            model_id="model-c", rate_limit=2, rate_limiter_mode=RateLimiterMode.CONCURRENT_REQUESTS
        ),
    ]

    async def simple_processor(request: QueueRequest) -> dict:
        await asyncio.sleep(0.05)
        return {"model": request.model_id, "done": True}

    await manager.register_all_queues(models, simple_processor)

    print(f"Registered {len(models)} models")

    # Submit requests to all models
    all_requests = []
    for model_config in models:
        for i in range(3):
            request = QueueRequest(model_id=model_config.model_id, metadata={"batch_index": i})
            all_requests.append(manager.submit_request(request))

    print(f"Submitting {len(all_requests)} requests across {len(models)} models...")

    responses = await asyncio.gather(*all_requests)

    # Group by model
    by_model = {}
    for response in responses:
        model_id = response.model_id
        if model_id not in by_model:
            by_model[model_id] = []
        by_model[model_id].append(response)

    print("\n=== Results by Model ===")
    for model_id, model_responses in by_model.items():
        completed = sum(1 for r in model_responses if r.status == "completed")
        avg_time = sum(r.processing_time for r in model_responses) / len(model_responses)
        print(
            f"{model_id}: {completed}/{len(model_responses)} completed " f"(avg: {avg_time:.3f}s)"
        )

    # Show queue info
    print("\n=== Queue Information ===")
    all_info = manager.get_all_queues_info()
    for model_id, info in all_info.items():
        print(f"{model_id}:")
        print(f"  Mode: {info['rate_limiter_mode']}")
        print(f"  Limit: {info['rate_limit']}")
        print(f"  Current usage: {info['rate_limiter_usage']}")

    await manager.shutdown_all()
    manager.reset_instance()


async def demo_dynamic_configuration():
    """Demonstrate dynamic model registration."""
    print("\n\n=== Dynamic Configuration Demo ===\n")

    manager = QueueManager()

    async def processor(request: QueueRequest) -> dict:
        await asyncio.sleep(0.05)
        return {"processed": True}

    # Start with one model
    config1 = ModelConfig(model_id="initial-model", rate_limit=5, time_period=10)
    await manager.register_queue(config1, processor)

    print(f"Registered models: {manager.get_registered_models()}")

    # Process some requests
    request = QueueRequest(model_id="initial-model")
    response = await manager.submit_request(request)
    print(f"Request to initial-model: {response.status}")

    # Dynamically add another model
    config2 = ModelConfig(model_id="new-model", rate_limit=3, time_period=10)
    await manager.register_queue(config2, processor)

    print(f"Registered models: {manager.get_registered_models()}")

    # Process requests to both
    requests = [
        QueueRequest(model_id="initial-model"),
        QueueRequest(model_id="new-model"),
    ]

    responses = await asyncio.gather(*[manager.submit_request(req) for req in requests])

    for resp in responses:
        print(f"Request to {resp.model_id}: {resp.status}")

    await manager.shutdown_all()


async def main():
    """Run all advanced examples."""
    print("=" * 60)
    print("  LLM Queue - Advanced Usage Examples")
    print("=" * 60)

    await demo_error_handling()
    await demo_batch_processing()
    await demo_dynamic_configuration()

    print("\n" + "=" * 60)
    print("  All demonstrations completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
