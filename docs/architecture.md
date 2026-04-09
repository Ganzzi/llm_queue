# Architecture

## Overview

The LLM Queue library provides a high-performance system for managing LLM API calls with intelligent rate limiting and queueing. The architecture is designed around async-first principles and supports multiple rate limiting strategies.

## Core Components

### QueueManager (Singleton)
- Central coordinator for all queues
- Ensures only one instance exists across the application
- Manages registration and coordination of multiple model queues
- Provides unified interface for submitting requests

### Queue (Per-Model)
- Individual queue for each registered model
- Contains rate limiting logic specific to the model
- Handles request processing with the provided processor function
- Tracks request status and metrics

### Rate Limiter Chain
- Composes multiple rate limiters together
- Supports different types of rate limiting (requests, tokens, concurrency)
- Implements rollback mechanism when any limiter fails
- Provides atomic acquisition across all limiters

### Supported Rate Limiter Types
- **Request Rate Limiters**: RPM (requests per minute), RPD (requests per day)
- **Token Rate Limiters**: TPM (tokens per minute), TPD (tokens per day), ITPM (input tokens), OTPM (output tokens)
- **Concurrency Limiters**: Maximum concurrent requests

## Data Flow

1. **Request Submission**: Client submits `QueueRequest` to `QueueManager`
2. **Queue Selection**: Manager routes to appropriate `Queue` based on `model_id`
3. **Rate Limit Check**: Queue validates against `RateLimiterChain`
4. **Queue Processing**: Request is processed by registered processor function
5. **Response Handling**: Result is returned to client or stored for later retrieval

## Patterns Used

- **Singleton Pattern**: `QueueManager` ensures single point of coordination
- **Chain of Responsibility**: `RateLimiterChain` handles multiple limiters
- **Strategy Pattern**: Different rate limiter implementations
- **Async Generics**: Type-safe request/response handling
- **Producer-Consumer**: Queue processes requests asynchronously

## Configuration

Models are configured with `ModelConfig` which defines:
- Model identifier
- List of rate limiter configurations
- Each rate limiter has type, limit, and time period

## Thread Safety

All components are designed to be thread-safe using asyncio locks where necessary:
- Rate limiters use async locks for safe concurrent access
- Queue state is protected during operations
- Singleton manager maintains thread-safe state