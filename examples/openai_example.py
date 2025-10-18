"""Example of using llm-queue with OpenAI API."""

import asyncio
import os
from typing import Optional

from pydantic import BaseModel, Field

from llm_queue import QueueManager, ModelConfig, QueueRequest, RateLimiterMode

# Note: This example requires the openai package
# Install with: pip install openai

try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai package not installed. Install with: pip install openai")


# Define Pydantic models for type safety
class OpenAIParams(BaseModel):
    """Parameters for OpenAI API requests."""

    prompt: str = Field(..., description="The prompt to send to OpenAI")
    max_tokens: int = Field(default=100, ge=1, le=4096, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")


class OpenAIResult(BaseModel):
    """Result from OpenAI API calls."""

    content: str = Field(..., description="Generated content")
    model: str = Field(..., description="Model used")
    usage: dict = Field(..., description="Token usage information")
    finish_reason: str = Field(..., description="Why generation stopped")


class OpenAIProcessor:
    """Processor for OpenAI API calls with llm-queue."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI processor.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is required. Install with: pip install openai")

        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    async def process_request(self, request: QueueRequest[OpenAIParams]) -> OpenAIResult:
        """
        Process an OpenAI API request.

        Args:
            request: Queue request with typed parameters

        Returns:
            Typed response from OpenAI API
        """
        # Extract typed parameters from the request
        params = request.params
        prompt = params.prompt
        max_tokens = params.max_tokens
        temperature = params.temperature

        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=request.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Return typed response
        return OpenAIResult(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=response.choices[0].finish_reason,
        )


async def main():
    """Main example function."""
    if not OPENAI_AVAILABLE:
        print("Please install openai package: pip install openai")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return

    print("=== LLM Queue + OpenAI Example ===\n")

    # Initialize processor and manager with type hints
    processor = OpenAIProcessor()
    manager: QueueManager[OpenAIParams, OpenAIResult] = QueueManager()

    # Configure models with their rate limits
    # OpenAI has different rate limits for different models
    models = [
        ModelConfig(
            model_id="gpt-4",
            rate_limit=10,  # 10 requests per minute
            rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
            time_period=60,
        ),
        ModelConfig(
            model_id="gpt-3.5-turbo",
            rate_limit=50,  # 50 requests per minute
            rate_limiter_mode=RateLimiterMode.REQUESTS_PER_PERIOD,
            time_period=60,
        ),
    ]

    # Register all models
    print("Registering models:")
    for model_config in models:
        await manager.register_queue(model_config, processor.process_request)
        print(f"  ✓ {model_config.model_id} ({model_config.rate_limit} req/min)")

    # Example requests
    prompts = [
        "What is the capital of France?",
        "Explain quantum computing in one sentence.",
        "Write a haiku about programming.",
    ]

    print(f"\n\nSubmitting {len(prompts)} requests to gpt-3.5-turbo...")

    # Create requests with typed parameters
    requests = [
        QueueRequest(model_id="gpt-3.5-turbo", params=OpenAIParams(prompt=prompt, max_tokens=100))
        for prompt in prompts
    ]

    # Submit all requests concurrently
    responses = await asyncio.gather(*[manager.submit_request(req) for req in requests])

    # Display results
    print("\n=== Results ===")
    for i, (prompt, response) in enumerate(zip(prompts, responses), 1):
        print(f"\n{i}. Prompt: {prompt}")
        if response.status == "completed" and response.result:
            # Access typed result with full IDE support
            result: OpenAIResult = response.result
            print(f"   Response: {result.content}")
            print(f"   Tokens: {result.usage['total_tokens']}")
            print(f"   Time: {response.processing_time:.2f}s")
        else:
            print(f"   Error: {response.error}")

    # Show queue statistics
    print("\n\n=== Queue Statistics ===")
    for model_id in manager.get_registered_models():
        info = manager.get_queue_info(model_id)
        print(f"{model_id}:")
        print(f"  Queue size: {info['queue_size']}")
        print(f"  Rate limiter usage: {info['rate_limiter_usage']}/{info['rate_limit']}")

    # Shutdown
    await manager.shutdown_all()
    print("\n✓ Done!")


if __name__ == "__main__":
    asyncio.run(main())
