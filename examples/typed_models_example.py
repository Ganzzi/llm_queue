"""Example demonstrating typed models with Pydantic.

This example shows how to use custom Pydantic models for both
request parameters and response results, providing full type safety.
"""

import asyncio
from typing import List

from pydantic import BaseModel, Field

from llm_queue import ModelConfig, QueueManager, QueueRequest, RateLimiterMode


# Define your parameter model
class LLMParams(BaseModel):
    """Parameters for an LLM request."""

    prompt: str = Field(..., description="The prompt to send to the LLM")
    max_tokens: int = Field(default=100, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    system_message: str = Field(
        default="You are a helpful assistant.", description="System message"
    )


# Define your result model
class LLMResult(BaseModel):
    """Result from an LLM request."""

    response: str = Field(..., description="The generated response")
    tokens_used: int = Field(..., description="Number of tokens used")
    model: str = Field(..., description="Model that generated the response")
    finish_reason: str = Field(default="completed", description="Why generation stopped")


# Processor function with proper typing
async def process_llm_request(request: QueueRequest[LLMParams]) -> LLMResult:
    """Process an LLM request.

    Args:
        request: Queue request containing LLMParams

    Returns:
        LLMResult with the generated response
    """
    # Extract typed parameters
    params = request.params
    print(f"Processing request {request.id}")
    print(f"  Prompt: {params.prompt}")
    print(f"  Max tokens: {params.max_tokens}")
    print(f"  Temperature: {params.temperature}")

    # Simulate LLM API call
    await asyncio.sleep(0.5)

    # Create typed result
    result = LLMResult(
        response=f"Response to: {params.prompt[:30]}...",
        tokens_used=42,
        model=request.model_id,
        finish_reason="completed",
    )

    return result


async def main():
    """Demonstrate typed models with llm-queue."""
    print("=" * 60)
    print("Typed Models Example")
    print("=" * 60)

    # Initialize manager with proper typing: QueueManager[LLMParams, LLMResult]
    manager: QueueManager[LLMParams, LLMResult] = QueueManager()

    # Configure model
    config = ModelConfig(
        model_id="gpt-4",
        rate_limit=5,  # 5 requests per minute
        rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
        time_period=60,
    )

    # Register queue with typed processor
    await manager.register_queue(config, process_llm_request)

    print("\n1. Single Request with Type Safety")
    print("-" * 60)

    # Create typed parameters
    params1 = LLMParams(
        prompt="What is the meaning of life?",
        max_tokens=150,
        temperature=0.8,
        system_message="You are a philosopher.",
    )

    # Create typed request
    request1 = QueueRequest[LLMParams](model_id="gpt-4", params=params1)

    # Submit and get typed response
    response1 = await manager.submit_request(request1)

    # Access typed result with full IDE support
    if response1.status == "completed" and response1.result:
        result: LLMResult = response1.result
        print(f"✓ Response: {result.response}")
        print(f"  Tokens used: {result.tokens_used}")
        print(f"  Model: {result.model}")
        print(f"  Finish reason: {result.finish_reason}")
        print(f"  Processing time: {response1.processing_time:.3f}s")
    else:
        print(f"✗ Error: {response1.error}")

    print("\n2. Batch Requests with Different Parameters")
    print("-" * 60)

    # Create multiple requests with different parameters
    prompts = [
        ("Explain quantum computing", 200, 0.5),
        ("Write a haiku about programming", 50, 1.0),
        ("What is machine learning?", 150, 0.7),
    ]

    requests: List[QueueRequest[LLMParams]] = []
    for prompt, max_tokens, temp in prompts:
        params = LLMParams(
            prompt=prompt, max_tokens=max_tokens, temperature=temp, system_message="Be concise."
        )
        req = QueueRequest[LLMParams](model_id="gpt-4", params=params)
        requests.append(req)

    # Submit all requests concurrently
    responses = await asyncio.gather(*[manager.submit_request(req) for req in requests])

    # Process typed responses
    for i, response in enumerate(responses, 1):
        if response.status == "completed" and response.result:
            print(f"\n{i}. {prompts[i-1][0][:40]}...")
            print(f"   Response: {response.result.response}")
            print(f"   Tokens: {response.result.tokens_used}")
        else:
            print(f"\n{i}. Error: {response.error}")

    print("\n3. Fire-and-Forget Request (wait_for_completion=False)")
    print("-" * 60)

    # Create request that returns immediately
    params_async = LLMParams(
        prompt="Background task: summarize quantum mechanics", max_tokens=200, temperature=0.7
    )

    request_async = QueueRequest[LLMParams](
        model_id="gpt-4", params=params_async, wait_for_completion=False
    )

    # Returns immediately with PENDING status
    response_async = await manager.submit_request(request_async)
    print(f"✓ Request submitted: {response_async.request_id}")
    print(f"  Status: {response_async.status}")
    print(f"  (Processing in background)")

    # Poll for status (optional - fire-and-forget requests are cleaned up after completion)
    await asyncio.sleep(1.0)
    status = await manager.get_status("gpt-4", response_async.request_id)
    if status:
        print(f"  Updated status: {status.status}")
    else:
        print("  Request completed and cleaned up (status no longer available)")

    print("\n4. Type Safety Demo")
    print("-" * 60)

    # This demonstrates type safety at development time
    try:
        # Valid: correct parameter types
        valid_params = LLMParams(prompt="Hello", max_tokens=50, temperature=0.5)
        print(f"✓ Valid params created: prompt='{valid_params.prompt}'")

        # Invalid: will raise validation error
        # invalid_params = LLMParams(
        #     prompt="Hello",
        #     max_tokens=10000,  # Too high, max is 4096
        #     temperature=3.0,   # Too high, max is 2.0
        # )
    except Exception as e:
        print(f"✗ Validation error: {e}")

    # Cleanup
    print("\n" + "=" * 60)
    print("Shutting down...")
    await manager.shutdown_all()
    print("✓ Complete!")


if __name__ == "__main__":
    asyncio.run(main())
