# Rate Limiter Chain: One-Page Reference

## The 3 Questions Answered

### Q1: How does the rate limiter chain work?

```
Queue._process_queue()
  ↓
Chain.wait_for_all(request)
  ├─ Limiter[0]: Has capacity? → If NO: BLOCK
  ├─ Limiter[1]: Has capacity? → If NO: BLOCK
  ├─ Limiter[N]: Has capacity? → If NO: BLOCK
  ↓ (ALL passed)
Processor executes
  ↓
Chain.release_all()
  ↓
Response to client
```

**Key:** Request blocks in queue if ANY limiter blocks.

---

### Q2: How does it support 7 rate limiters?

```python
RateLimiterChain(limiters=[
    RequestRateLimiter,     # RPM, RPD
    TokenRateLimiter,       # TPM, TPD, ITPM, OTPM
    ConcurrentRateLimiter   # CONCURRENT
])
```

3 classes, 7 types. Factory decides which class for each type.

---

### Q3: Does it distinguish input/output/total tokens?

```python
def _get_tokens_for_limiter(limiter, request):
    if limiter.type in (TPM, TPD):
        return est_input + est_output    # ✓ TOTAL
    elif limiter.type == ITPM:
        return est_input                 # ✓ INPUT only
    elif limiter.type == OTPM:
        return est_output                # ✓ OUTPUT only
    return 1
```

**YES - fully distinguished!**

---

## The 7 Rate Limiters at a Glance

| Type | Class | Window | What's Limited |
|------|-------|--------|----------------|
| RPM | RequestRateLimiter | 60s | Requests |
| RPD | RequestRateLimiter | 86400s | Requests |
| TPM | TokenRateLimiter | 60s | Input + Output tokens |
| TPD | TokenRateLimiter | 86400s | Input + Output tokens |
| ITPM | TokenRateLimiter | 60s | Input tokens only |
| OTPM | TokenRateLimiter | 60s | Output tokens only |
| CONCURRENT | ConcurrentRateLimiter | N/A | Simultaneous requests |

---

## Token Counting Example

Request: 200 input + 800 output tokens

| Limiter | Tokens Counted |
|---------|----------------|
| TPM | 1000 (total) |
| ITPM | 200 (input) |
| OTPM | 800 (output) |

---

## Request Flow

```
1. Manager.submit_request(request)
2. Queue.enqueue(request)
3. _process_queue() picks up request
4. wait_for_all(request)
   - Check limiter[0] capacity
   - Check limiter[1] capacity
   - Check limiter[N] capacity
5. Processor executes
6. release_all() (concurrent slots)
7. update_token_usage() (correct estimates)
8. Response returned
```

---

## Token Correction

After processing:

```python
if estimated < actual:
    await limiter.acquire(diff)      # Penalize overage
elif estimated > actual:
    await limiter.release(diff)      # Refund underage
```

---

## When Request Blocks

```
If ITPM is at 50k/50k (full):
    Request with 200 input tokens arrives
    wait_for_all() tries ITPM
    ITPM has 0 capacity
    Request BLOCKS in queue
    
[Time passes, window resets]
    
    ITPM now has capacity
    Request retries
    ITPM passes
    Other limiters checked
    All pass → Process
```

---

## Configuration Example

```python
ModelConfig(
    model_id="gpt-4",
    rate_limiters=[
        RateLimiterConfig(type=RateLimiterType.RPM, limit=10),
        RateLimiterConfig(type=RateLimiterType.TPM, limit=90000),
        RateLimiterConfig(type=RateLimiterType.ITPM, limit=50000),
        RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=5),
    ]
)
```

Creates chain with 4 limiters.

---

## Code Files

- `rate_limiters/chain.py` - RateLimiterChain (orchestrator)
- `rate_limiters/factory.py` - Creates limiters from config
- `rate_limiters/request_limiter.py` - RPM/RPD limiter
- `rate_limiters/token_limiter.py` - TPM/TPD/ITPM/OTPM limiter
- `rate_limiters/concurrent_limiter.py` - CONCURRENT limiter
- `queue.py` - Calls wait_for_all()

---

## Key Methods

### RateLimiterChain

```python
async def wait_for_all(request)
    # Block until all limiters ready

async def release_all(request)
    # Release concurrent slots

async def update_token_usage(request, actual_input, actual_output)
    # Correct token estimates

def _get_tokens_for_limiter(limiter, request) -> int
    # Calculate tokens needed for this limiter type
```

---

## Implementation Details

### RequestRateLimiter
- Uses list of timestamps
- Removes timestamps older than window
- Allows if count < limit

### TokenRateLimiter
- Uses list of (timestamp, count) tuples
- Removes entries older than window
- Allows if sum(counts) + new <= limit

### ConcurrentRateLimiter
- Uses asyncio.Semaphore
- acquire() takes slot
- release() frees slot

---

## Sequential Acquisition

Wait for each limiter in order:

```
✓ Limiter 1 acquired
✓ Limiter 2 acquired
✗ Limiter 3 blocked
  → REQUEST STAYS IN QUEUE
  
[Later]

✓ Limiter 1 (held)
✓ Limiter 2 (held)
✓ Limiter 3 acquired
→ PROCESS
```

No partial state, no deadlock.

---

## Summary

| Aspect | How |
|--------|-----|
| **Multiple limiters** | Sequential gatekeeper |
| **7 types** | 3 classes via factory |
| **Token distinction** | Per-type calculation |
| **Request blocking** | Stays in queue if any limiter full |
| **Atomic operation** | All limiters or none |
| **Token correction** | Estimated vs actual adjustment |

---

**Start reading:** [RATE_LIMITER_INDEX.md](RATE_LIMITER_INDEX.md)
