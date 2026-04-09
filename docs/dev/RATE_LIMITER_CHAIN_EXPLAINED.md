# Rate Limiter Chain: Complete Explanation

## Overview

The **RateLimiterChain** (`src/llm_queue/rate_limiters/chain.py`) is the core orchestrator that manages **multiple rate limiters simultaneously** for a single model. It ensures that a request respects **ALL configured limits** before being processed.

**Key principle:** A request is only processed when **ALL rate limiters have available capacity**.

---

## The 7 Rate Limiter Types

The system supports 7 different rate limiters organized into 3 categories:

### Category 1: Request-Based Limiters (RequestRateLimiter)

These limit by the **number of requests** in a time period using a **sliding window** with timestamp tracking.

| Type | Time Window | Use Case | Example |
|------|-------------|----------|---------|
| **RPM** | 60 seconds (1 minute) | Requests per Minute | Max 10 requests/min |
| **RPD** | 86400 seconds (1 day) | Requests per Day | Max 1000 requests/day |

**Implementation:** Sliding window with timestamp tracking
```python
class RequestRateLimiter:
    timestamps: List[float] = []  # Records when each request was made
    
    async def acquire(self, tokens: int = 1) -> bool:
        now = time.time()
        # Remove timestamps older than time_period
        self.timestamps = [t for t in self.timestamps 
                          if now - t < self.time_period]
        
        # Can acquire if under limit
        if len(self.timestamps) + tokens <= self.limit:
            self.timestamps.append(now)
            return True
        return False
```

### Category 2: Token-Based Limiters (TokenRateLimiter)

These limit by the **consumption of tokens** in a time period. **This is where input vs output vs total distinction happens.**

| Type | Time Window | What Counts | Use Case | Example |
|------|-------------|-------------|----------|---------|
| **TPM** | 60 seconds | Input + Output | Total Tokens Per Minute | Max 90,000 tokens/min |
| **TPD** | 86400 seconds | Input + Output | Total Tokens Per Day | Max 1,000,000 tokens/day |
| **ITPM** | 60 seconds | Input only | Input Tokens Per Minute | Max 50,000 input tokens/min |
| **OTPM** | 60 seconds | Output only | Output Tokens Per Minute | Max 40,000 output tokens/min |

**Implementation:** Sliding window with token counts
```python
class TokenRateLimiter:
    usage_history: List[Tuple[float, int]] = []  # (timestamp, token_count)
    
    async def acquire(self, tokens: int) -> bool:
        now = time.time()
        # Remove old entries
        self.usage_history = [(t, count) for t, count in self.usage_history 
                             if now - t < self.time_period]
        
        # Sum current usage
        current_usage = sum(count for _, count in self.usage_history)
        
        # Can acquire if total doesn't exceed limit
        if current_usage + tokens <= self.limit:
            self.usage_history.append((now, tokens))
            return True
        return False
```

### Category 3: Concurrency Limiter (ConcurrentRateLimiter)

This limits the **number of simultaneous/concurrent requests** using `asyncio.Semaphore`.

| Type | Mechanism | Use Case | Example |
|------|-----------|----------|---------|
| **CONCURRENT** | Semaphore | Max simultaneous requests | Max 5 concurrent |

**Implementation:** asyncio.Semaphore
```python
class ConcurrentRateLimiter:
    def __init__(self, limit: int):
        self._semaphore = asyncio.Semaphore(limit)
        
    async def acquire(self, tokens: int = 1) -> bool:
        if self._semaphore._value < tokens:
            return False
        for _ in range(tokens):
            await self._semaphore.acquire()
        return True
        
    async def release(self, tokens: int = 1) -> None:
        for _ in range(tokens):
            self._semaphore.release()
```

---

## How the Chain Works

### 1. Chain Creation from Configuration

The `factory.py` creates a chain from `RateLimiterConfig`:

```python
# Configuration
configs = [
    RateLimiterConfig(type=RateLimiterType.RPM, limit=10),
    RateLimiterConfig(type=RateLimiterType.TPM, limit=90000),
    RateLimiterConfig(type=RateLimiterType.ITPM, limit=50000),
    RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=5),
]

# Create chain
chain = create_chain(configs)
# chain.limiters = [RequestRateLimiter, TokenRateLimiter, ...]
```

Each limiter gets the `rate_limiter_type` attribute:
```python
setattr(limiter, "rate_limiter_type", config.type)
```

### 2. Request Processing: wait_for_all()

The critical method that ensures ALL limits are respected:

```python
# In Queue._process_queue()
await self.rate_limiter_chain.wait_for_all(request)

# Implementation in RateLimiterChain
async def wait_for_all(self, request: QueueRequest) -> None:
    """Wait until all limiters have capacity AND acquire them."""
    for limiter in self.limiters:
        tokens = self._get_tokens_for_limiter(limiter, request)
        await limiter.wait_for_slot(tokens)
```

**What this does:**
1. Iterates through each limiter sequentially
2. Calculates tokens needed for that limiter
3. Blocks until that limiter has capacity
4. Automatically acquires the slot
5. Moves to next limiter

**If ANY limiter blocks, the request stays in the queue.**

### 3. Token Calculation: Input vs Output vs Total

The `_get_tokens_for_limiter()` method distinguishes between all token types:

```python
def _get_tokens_for_limiter(self, limiter: BaseRateLimiter, request: QueueRequest) -> int:
    """Calculate required tokens for a specific limiter."""
    limiter_type = getattr(limiter, "rate_limiter_type", None)
    
    # Request/concurrent: always 1
    if limiter_type in (RateLimiterType.RPM, RateLimiterType.RPD, RateLimiterType.CONCURRENT):
        return 1
    
    # Token limiters: distinguish by type
    est_input = request.estimated_input_tokens or 0
    est_output = request.estimated_output_tokens or 0

    if limiter_type in (RateLimiterType.TPM, RateLimiterType.TPD):
        return est_input + est_output  # ✓ TOTAL tokens
    elif limiter_type == RateLimiterType.ITPM:
        return est_input                # ✓ INPUT only
    elif limiter_type == RateLimiterType.OTPM:
        return est_output               # ✓ OUTPUT only
        
    return 1
```

**Yes, the code DOES distinguish between all token types:**

| Limiter Type | Formula | Result |
|--------------|---------|--------|
| TPM/TPD | input + output | **Total tokens** |
| ITPM | input only | **Input tokens** |
| OTPM | output only | **Output tokens** |

---

## Request Lifecycle: Keeping in Queue

Your concern about requests staying in queue is **correct and already implemented**.

### Visual Flow

```
1. Manager.submit_request(request)
     ↓
2. Queue.enqueue(request)
     ├─ Adds to asyncio.Queue
     └─ Creates Future
     ↓
3. Background: Queue._process_queue()
     ├─ Infinite loop
     ├─ Gets request from queue
     └─ ↓ BLOCKS HERE
    
4. Chain.wait_for_all(request)
     ├─ RPM: 8/10 ✓
     ├─ TPM: 80k/90k ✓
     ├─ ITPM: 45k/50k ✓
     ├─ OTPM: 35k/40k ✓
     ├─ CONCURRENT: 3/5 ✓
     └─ ALL PASSED
     ↓
5. Processor executes
     ↓
6. Chain.release_all() (for concurrent)
     ↓
7. Chain.update_token_usage()
     ↓
8. Response returned
```

### If a Limiter Blocks

```
Queue: [Request A, Request B, Request C]

Request A processing:
    wait_for_all(A)
    ├─ RPM: 10/10 ✗ BLOCKED
    └─ Request stays in queue
    
[30 seconds later...]

Queue: [Request A, Request B, Request C]  ← Still there!

Request A processing:
    wait_for_all(A)
    ├─ RPM: 9/10 (oldest expired) ✓
    ├─ Other limits ✓
    └─ Acquires and processes
```

---

## Complete Example

### Configuration

```python
config = ModelConfig(
    model_id="gpt-4",
    rate_limiters=[
        RateLimiterConfig(type=RateLimiterType.RPM, limit=10),
        RateLimiterConfig(type=RateLimiterType.TPM, limit=90000),
        RateLimiterConfig(type=RateLimiterType.ITPM, limit=50000),
        RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=5),
    ]
)
```

### Submit Request

```python
request = QueueRequest(
    model_id="gpt-4",
    params={"prompt": "Hello"},
    estimated_input_tokens=200,
    estimated_output_tokens=800,
)

response = await manager.submit_request(request)
```

### Chain Acquisition

```python
wait_for_all(request):
    ├─ RPM: 1 request needed
    │  └─ Current: 8/10, Can acquire ✓
    │
    ├─ TPM: 1000 tokens needed (200+800)
    │  └─ Current: 80k/90k, Can acquire ✓
    │
    ├─ ITPM: 200 tokens needed (input only)
    │  └─ Current: 45k/50k, Can acquire ✓
    │
    ├─ OTPM: 800 tokens needed (output only)
    │  └─ Current: 35k/40k, Can acquire ✓
    │
    └─ CONCURRENT: 1 slot needed
       └─ Current: 3/5 available, Can acquire ✓

→ All passed! Processor executes
```

### Token Adjustment

```python
# After processing
actual_input = 210  (estimated 200)
actual_output = 790 (estimated 800)

update_token_usage(210, 790):
    ├─ TPM: est=1000, actual=1000
    │  └─ No adjustment
    │
    ├─ ITPM: est=200, actual=210
    │  └─ Overage of 10, acquire(10)
    │
    └─ OTPM: est=800, actual=790
       └─ Underage of 10, release(10)
```

---

## Key Design Points

### 1. Sequential Acquisition
Prevents deadlocks by acquiring limiters in order.

### 2. Request Atomicity
Either ALL acquire or request waits (no partial state).

### 3. Per-Model Isolation
Each model has independent limit chains.

### 4. Token Correction
Estimated tokens reserve capacity, actual tokens adjust accounting.

### 5. Concurrent Lifecycle
Concurrent slots held for entire processing duration.

---

## Summary

| Aspect | How It Works |
|--------|--------------|
| **Multiple Limiters** | `wait_for_all()` sequentially acquires from each |
| **Request Blocking** | Stays in queue while waiting for any limiter |
| **Token Distinction** | `_get_tokens_for_limiter()` returns input/output/total per type |
| **RPM/RPD** | Request count in sliding window |
| **TPM/TPD** | Total tokens (input + output) |
| **ITPM** | Input tokens only |
| **OTPM** | Output tokens only |
| **CONCURRENT** | Semaphore with acquire/release |
