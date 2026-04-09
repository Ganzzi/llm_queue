# Rate Limiter Chain: Visual Summary

## Quick Answer to Your 3 Questions

### ❓ Question 1: How does the rate limiter chain work?

**Answer:** The `RateLimiterChain.wait_for_all()` method **sequentially** waits for each limiter to have capacity before allowing the request to process.

```
Request submitted
    ↓
Queue._process_queue() gets request
    ↓
Chain.wait_for_all(request) ← GATEKEEPER
    ├─ Limiter 1: Has capacity? 
    │  └─ YES → Acquire & continue
    │  └─ NO → BLOCK (request stays in queue)
    ├─ Limiter 2: Has capacity?
    │  └─ YES → Acquire & continue
    │  └─ NO → BLOCK
    ├─ Limiter 3: Has capacity?
    │  └─ YES → Acquire & continue
    │  └─ NO → BLOCK
    └─ Limiter N: Has capacity?
       └─ YES → Acquire & continue
       └─ NO → BLOCK
    ↓
ALL LIMITERS PASSED → Processor executes
```

---

### ❓ Question 2: How does it support the 7 rate limiters?

**Answer:** The chain manages 3 **different limiter classes**, each implementing the same `BaseRateLimiter` interface:

```
┌─────────────────────────────────────────────────┐
│     RateLimiterChain(limiters=[...])            │
└─────────────────────────────────────────────────┘
         │
         ├─ RequestRateLimiter (RPM, RPD)
         │  └─ Sliding window with timestamps
         │     • RPM: 60s window
         │     • RPD: 86400s window
         │
         ├─ TokenRateLimiter (TPM, TPD, ITPM, OTPM)
         │  └─ Sliding window with token counts
         │     • TPM: total tokens, 60s window
         │     • TPD: total tokens, 86400s window
         │     • ITPM: input tokens, 60s window
         │     • OTPM: output tokens, 60s window
         │
         └─ ConcurrentRateLimiter (CONCURRENT)
            └─ asyncio.Semaphore
               • Max simultaneous requests
```

**Each type handles a different dimension:**

| Dimension | Types | What Gets Limited |
|-----------|-------|------------------|
| **Requests in Time** | RPM, RPD | How many requests in a period |
| **Tokens in Time** | TPM, TPD, ITPM, OTPM | How many tokens in a period |
| **Concurrency** | CONCURRENT | How many simultaneous requests |

---

### ❓ Question 3: Does it distinguish input vs output vs total tokens?

**Answer: YES! Fully distinguished via `_get_tokens_for_limiter()` method**

```python
def _get_tokens_for_limiter(self, limiter, request) -> int:
    """Return the token count for this specific limiter type"""
    
    limiter_type = getattr(limiter, "rate_limiter_type", None)
    est_input = request.estimated_input_tokens or 0
    est_output = request.estimated_output_tokens or 0

    if limiter_type in (RateLimiterType.TPM, RateLimiterType.TPD):
        return est_input + est_output  # ← TOTAL TOKENS
    
    elif limiter_type == RateLimiterType.ITPM:
        return est_input               # ← INPUT TOKENS ONLY
    
    elif limiter_type == RateLimiterType.OTPM:
        return est_output              # ← OUTPUT TOKENS ONLY
    
    return 1  # Request-based and concurrent
```

**Concrete Example:**

Request with:
- `estimated_input_tokens=200`
- `estimated_output_tokens=800`

When checking capacity:

```
TPM Limiter (Total Tokens Per Minute):
    tokens_needed = 200 + 800 = 1000
    ✓ If current_usage + 1000 <= 90000 → Acquire
    ✗ If current_usage + 1000 > 90000  → Block

ITPM Limiter (Input Tokens Per Minute):
    tokens_needed = 200
    ✓ If current_usage + 200 <= 50000 → Acquire
    ✗ If current_usage + 200 > 50000  → Block

OTPM Limiter (Output Tokens Per Minute):
    tokens_needed = 800
    ✓ If current_usage + 800 <= 40000 → Acquire
    ✗ If current_usage + 800 > 40000  → Block
```

---

## Multi-Limiter Scenario Walkthrough

### Setup

```python
# Model: gpt-4 with 4 rate limiters
config = ModelConfig(
    model_id="gpt-4",
    rate_limiters=[
        RateLimiterConfig(type=RateLimiterType.RPM, limit=10),        # Max 10 req/min
        RateLimiterConfig(type=RateLimiterType.TPM, limit=90000),     # Max 90k tokens/min
        RateLimiterConfig(type=RateLimiterType.ITPM, limit=50000),    # Max 50k input/min
        RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=5),  # Max 5 concurrent
    ]
)
```

### Submit 3 Requests

```python
# Request 1: Short prompt, long response
req1 = QueueRequest(
    model_id="gpt-4",
    params={"prompt": "Hello"},
    estimated_input_tokens=100,
    estimated_output_tokens=2000,
)

# Request 2: Medium prompt, medium response  
req2 = QueueRequest(
    model_id="gpt-4",
    params={"prompt": "Explain..."},
    estimated_input_tokens=300,
    estimated_output_tokens=1000,
)

# Request 3: Long prompt, short response
req3 = QueueRequest(
    model_id="gpt-4",
    params={"prompt": "Long context..." * 50},
    estimated_input_tokens=10000,
    estimated_output_tokens=200,
)
```

### Processing Timeline

```
Time T0: Process Request 1 (100 input, 2000 output)
    wait_for_all(req1):
        ├─ RPM: 0/10 requests ✓ → Acquire
        ├─ TPM: 0/90000 tokens (100+2000=2100) ✓ → Acquire
        ├─ ITPM: 0/50000 input (100) ✓ → Acquire
        └─ CONCURRENT: 0/5 slots ✓ → Acquire
    
    Processor executes (takes 3 seconds)
    
    Actual used: 110 input, 1990 output
    update_token_usage(110, 1990):
        ├─ TPM: est=2100, actual=2100 ✓ No change
        ├─ ITPM: est=100, actual=110 → Overage of 10 → acquire(10)
        └─ CONCURRENT: Release 1 slot
    
    Status: 1/10 RPM, 2100/90000 TPM, 110/50000 ITPM, 4/5 CONCURRENT

---

Time T3: Process Request 2 (300 input, 1000 output)
    wait_for_all(req2):
        ├─ RPM: 1/10 requests ✓ → Acquire
        ├─ TPM: (2100+1300=) 3400/90000 tokens ✓ → Acquire
        ├─ ITPM: (110+300=) 410/50000 input ✓ → Acquire
        └─ CONCURRENT: 4/5 slots ✓ → Acquire
    
    Processor executes (takes 2 seconds)
    
    Actual used: 305 input, 995 output
    update_token_usage(305, 995):
        ├─ TPM: est=1300, actual=1300 ✓ No change
        ├─ ITPM: est=300, actual=305 → Overage of 5 → acquire(5)
        └─ CONCURRENT: Release 1 slot
    
    Status: 2/10 RPM, 3400/90000 TPM, 415/50000 ITPM, 4/5 CONCURRENT

---

Time T5: Process Request 3 (10000 input, 200 output)
    wait_for_all(req3):
        ├─ RPM: 2/10 requests ✓ → Acquire
        ├─ TPM: (3400+10200=) 13600/90000 tokens ✓ → Acquire
        ├─ ITPM: (415+10000=) 10415/50000 input ✓ → Acquire
        └─ CONCURRENT: 4/5 slots ✓ → Acquire
    
    Processor executes (takes 4 seconds)
    
    Actual used: 9995 input, 205 output
    update_token_usage(9995, 205):
        ├─ TPM: est=10200, actual=10200 ✓ No change
        ├─ ITPM: est=10000, actual=9995 → Underage of 5 → release(5)
        └─ CONCURRENT: Release 1 slot
    
    Status: 3/10 RPM, 13600/90000 TPM, 10415/50000 ITPM, 3/5 CONCURRENT

---

Time T9: All requests complete
    Queue empty, awaiting new requests
    Tokens reset after window expires (60 seconds from first request)
```

---

## What Happens If a Limit Is Reached?

### Scenario: CONCURRENT Limit Hit

```
Time T0: 5 concurrent requests active
    All 5 CONCURRENT slots are taken
    
Time T10: Request 6 arrives
    wait_for_all(req6):
        ├─ RPM: 5/10 requests ✓
        ├─ TPM: capacity available ✓
        ├─ ITPM: capacity available ✓
        └─ CONCURRENT: 5/5 slots ✗ BLOCKED
    
    Request 6 stays in queue, doesn't execute
    
[One concurrent request finishes...]
    
Time T14: CONCURRENT slot freed
    wait_for_all(req6) retries:
        └─ CONCURRENT: 4/5 slots ✓
    
    Request 6 acquires and executes
```

### Scenario: ITPM Limit Hit

```
Time T15: Input tokens at 49,800/50,000 (200 available)
    
Time T16: Request 7 arrives
    Request has 500 estimated_input_tokens
    
    wait_for_all(req7):
        ├─ RPM: capacity ✓
        ├─ TPM: capacity ✓
        ├─ ITPM: current=49800, needed=500
        │         49800 + 500 = 50300 > 50000 ✗ BLOCKED
        └─ Request stays in queue
    
[Time passes, window expires...]
    
Time T76: 60 seconds have passed, oldest tokens expire
    
    wait_for_all(req7) retries:
        └─ ITPM: current=40000 (old ones expired), needed=500
                 40000 + 500 = 40500 <= 50000 ✓
    
    Request 7 acquires and executes
```

---

## Summary Diagram

```
                          ┌─────────────────────────────┐
                          │    QueueManager (singleton)  │
                          └──────────────┬────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
              Queue[gpt-4]          Queue[claude]      Queue[gpt-3.5]
                    │                   │                   │
                    └─ RateLimiterChain └─ RateLimiterChain └─ RateLimiterChain
                       ├─ RequestRateLimiter(RPM)
                       ├─ TokenRateLimiter(TPM)
                       ├─ TokenRateLimiter(ITPM)
                       ├─ TokenRateLimiter(OTPM)
                       └─ ConcurrentLimiter


For each request:
    1. Manager.submit_request(request)
    2. Queue.enqueue(request)
    3. Background task: Queue._process_queue()
    4. Chain.wait_for_all(request)
         ├─ For each limiter:
         │  ├─ Calculate tokens needed (input/output/total per type)
         │  ├─ Check if capacity available
         │  └─ If no: block request in queue
         ├─ All limiters ready:
         │  └─ Acquire from all simultaneously
    5. Processor executes
    6. Chain.release_all() (concurrent slots)
    7. Chain.update_token_usage(actual_input, actual_output)
    8. Response to client
```

---

## Key Takeaways

✅ **Multiple Limiters:** Chain manages 3-7 limiters working together
✅ **Request Blocking:** If ANY limiter blocks, entire request waits
✅ **Token Distinction:** Input/output/total handled per limiter type
✅ **Proper Accounting:** Estimated tokens reserve, actual tokens adjust
✅ **Per-Model Isolation:** Each model has independent limit chains
✅ **No Partial Execution:** Request atomic - all limiters or none

