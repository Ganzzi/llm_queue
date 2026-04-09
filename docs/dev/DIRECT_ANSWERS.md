# Rate Limiter Chain: Direct Answers to Your Questions

## Your 3 Specific Questions

---

## Q1: How does the rate limiter chain work?

### Direct Answer

The `RateLimiterChain` works by **sequentially checking and acquiring capacity from each limiter before allowing a request to be processed**.

### How It Works Step-by-Step

```
Background task: Queue._process_queue()
    │
    ├─ Gets request from queue
    │
    └─ Calls: await rate_limiter_chain.wait_for_all(request)
              │
              ├─ Loop through self.limiters
              │
              ├─ For limiter[0]:
              │  │  Calculate tokens_needed = _get_tokens_for_limiter(limiter[0], request)
              │  │  Call: await limiter[0].wait_for_slot(tokens_needed)
              │  │  ├─ If capacity available → Acquires and returns
              │  │  └─ If NO capacity → BLOCKS here until available
              │  │
              │  └─ Then continues to limiter[1]
              │
              ├─ For limiter[1]:
              │  │  Same process...
              │  │
              │  └─ Blocks if no capacity
              │
              ├─ For limiter[N]:
              │  │  Same process...
              │  │
              │  └─ Blocks if no capacity
              │
              └─ Returns (ALL limiters passed!)
    
    ├─ Now process request
    │  └─ Call: result = await processor_func(request)
    │
    ├─ Release concurrent slots
    │  └─ Call: await rate_limiter_chain.release_all(request)
    │
    └─ Return response to client
```

### The Critical Behavior

**If ANY limiter blocks, the entire request waits in the queue.**

```python
# In chain.py
async def wait_for_all(self, request: QueueRequest) -> None:
    for limiter in self.limiters:
        tokens = self._get_tokens_for_limiter(limiter, request)
        await limiter.wait_for_slot(tokens)  # ← BLOCKS HERE if no capacity
        # Don't continue to next limiter until this one passes!
```

### Example Scenario

```
Queue has [Request A, Request B, Request C]

Processing Request A:
    wait_for_all(A):
        ├─ RequestRateLimiter: 8/10 available ✓ → Acquire
        ├─ TokenRateLimiter(TPM): 80k/90k available ✓ → Acquire
        ├─ TokenRateLimiter(ITPM): 45k/50k available ✓ → Acquire
        └─ ConcurrentRateLimiter: 3/5 available ✓ → Acquire
    
    Request A processes

[Later] Processing Request B:
    wait_for_all(B):
        ├─ RequestRateLimiter: 7/10 available ✓ → Acquire
        ├─ TokenRateLimiter(TPM): capacity available ✓ → Acquire
        ├─ TokenRateLimiter(ITPM): capacity available ✓ → Acquire
        └─ ConcurrentRateLimiter: capacity available ✓ → Acquire
    
    Request B processes

[Later] Processing Request C:
    wait_for_all(C):
        ├─ RequestRateLimiter: 6/10 available ✓ → Acquire
        ├─ TokenRateLimiter(TPM): capacity available ✓ → Acquire
        ├─ TokenRateLimiter(ITPM): BLOCKED (no capacity available)
        └─ Request C stays in queue...
    
[After some time, window resets]
    
    wait_for_all(C) retries:
        ├─ RequestRateLimiter: capacity available ✓
        ├─ TokenRateLimiter(TPM): capacity available ✓
        ├─ TokenRateLimiter(ITPM): capacity available ✓
        └─ ConcurrentRateLimiter: capacity available ✓
    
    Request C finally processes
```

---

## Q2: How does it support the 7 rate limiters (RPM, RPD, TPM, TPD, ITPM, OTPM, CONCURRENT)?

### Direct Answer

It supports 7 rate limiters through **3 different limiter classes** that implement the same interface. The factory creates the appropriate class, and the chain treats them all the same way.

### The 3 Classes

```
RateLimiterChain
    │
    ├─ RequestRateLimiter (handles RPM, RPD)
    │  └─ Tracks request timestamps in sliding window
    │     • RPM: 60s window
    │     • RPD: 86400s (24h) window
    │
    ├─ TokenRateLimiter (handles TPM, TPD, ITPM, OTPM)
    │  └─ Tracks token counts in sliding window
    │     • TPM: 60s window, counts input+output
    │     • TPD: 86400s window, counts input+output
    │     • ITPM: 60s window, counts input only
    │     • OTPM: 60s window, counts output only
    │
    └─ ConcurrentRateLimiter (handles CONCURRENT)
       └─ Uses asyncio.Semaphore
          • Max simultaneous requests
```

### How Factory Creates Each Type

```python
# In factory.py
def create_rate_limiter(config: RateLimiterConfig) -> BaseRateLimiter:
    if config.type in (RateLimiterType.RPM, RateLimiterType.RPD):
        # Create RequestRateLimiter
        time_period = 60 if RPM else 86400
        return RequestRateLimiter(limit=config.limit, time_period=time_period)
    
    elif config.type == RateLimiterType.CONCURRENT:
        # Create ConcurrentRateLimiter
        return ConcurrentRateLimiter(limit=config.limit)
    
    elif config.type in (RateLimiterType.TPM, RateLimiterType.TPD, 
                         RateLimiterType.ITPM, RateLimiterType.OTPM):
        # Create TokenRateLimiter
        time_period = 60 if TPM/ITPM/OTPM else 86400  # TPD
        return TokenRateLimiter(limit=config.limit, time_period=time_period)
    
    # Mark the limiter with its type for later identification
    setattr(limiter, "rate_limiter_type", config.type)
    return limiter
```

### Chain Treats Them All Identically

```python
# In chain.py
async def wait_for_all(self, request: QueueRequest) -> None:
    for limiter in self.limiters:
        # Doesn't matter if it's RequestRateLimiter, TokenRateLimiter, or
        # ConcurrentRateLimiter - they all have wait_for_slot()
        tokens = self._get_tokens_for_limiter(limiter, request)
        await limiter.wait_for_slot(tokens)  # Works with all 3 classes
```

### Each Class Implements BaseRateLimiter Interface

```python
class BaseRateLimiter(ABC):
    @abstractmethod
    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire capacity"""
        pass
    
    @abstractmethod
    async def release(self, tokens: int = 1) -> None:
        """Release capacity"""
        pass
    
    @abstractmethod
    async def wait_for_slot(self, tokens: int = 1) -> None:
        """Block until capacity available"""
        pass
    
    @abstractmethod
    def get_current_usage(self) -> int:
        """Get current usage"""
        pass
    
    @abstractmethod
    def get_available_capacity(self) -> int:
        """Get available capacity"""
        pass

# All 3 classes implement these methods ✓
```

### Configuration Example Supporting All 7 Types

```python
from llm_queue import ModelConfig, RateLimiterConfig, RateLimiterType

config = ModelConfig(
    model_id="gpt-4",
    rate_limiters=[
        # Type 1: RPM (RequestRateLimiter)
        RateLimiterConfig(type=RateLimiterType.RPM, limit=10),
        
        # Type 2: RPD (RequestRateLimiter)
        RateLimiterConfig(type=RateLimiterType.RPD, limit=1000),
        
        # Type 3: TPM (TokenRateLimiter)
        RateLimiterConfig(type=RateLimiterType.TPM, limit=90000),
        
        # Type 4: TPD (TokenRateLimiter)
        RateLimiterConfig(type=RateLimiterType.TPD, limit=1000000),
        
        # Type 5: ITPM (TokenRateLimiter)
        RateLimiterConfig(type=RateLimiterType.ITPM, limit=50000),
        
        # Type 6: OTPM (TokenRateLimiter)
        RateLimiterConfig(type=RateLimiterType.OTPM, limit=40000),
        
        # Type 7: CONCURRENT (ConcurrentRateLimiter)
        RateLimiterConfig(type=RateLimiterType.CONCURRENT, limit=5),
    ]
)

# Result: RateLimiterChain with 7 limiters:
# [
#   RequestRateLimiter,    # RPM
#   RequestRateLimiter,    # RPD
#   TokenRateLimiter,      # TPM
#   TokenRateLimiter,      # TPD
#   TokenRateLimiter,      # ITPM
#   TokenRateLimiter,      # OTPM
#   ConcurrentRateLimiter, # CONCURRENT
# ]
```

---

## Q3: Does the code distinguish input tokens, output tokens, and total tokens?

### Direct Answer

**YES - The code FULLY distinguishes between all three via `_get_tokens_for_limiter()` method.**

### The Distinction Method

```python
# In chain.py
def _get_tokens_for_limiter(self, limiter: BaseRateLimiter, request: QueueRequest) -> int:
    """Calculate required tokens for a specific limiter.
    
    This method distinguishes between:
    - Input tokens only
    - Output tokens only
    - Total tokens (input + output)
    - Request count (for request-based limiters)
    """
    
    limiter_type = getattr(limiter, "rate_limiter_type", None)
    
    # Get estimated tokens from request
    est_input = request.estimated_input_tokens or 0
    est_output = request.estimated_output_tokens or 0

    # Branch based on limiter type
    if limiter_type in (RateLimiterType.TPM, RateLimiterType.TPD):
        # TPM/TPD: Count TOTAL tokens (input + output)
        return est_input + est_output
    
    elif limiter_type == RateLimiterType.ITPM:
        # ITPM: Count INPUT tokens ONLY
        return est_input
    
    elif limiter_type == RateLimiterType.OTPM:
        # OTPM: Count OUTPUT tokens ONLY
        return est_output
    
    else:
        # RPM, RPD, CONCURRENT: Always 1 (not tokens)
        return 1
```

### Concrete Example

Request with:
- `estimated_input_tokens = 200` (prompt tokens)
- `estimated_output_tokens = 800` (completion tokens)

Token counting by limiter type:

```
┌─────────────────────────────────────────────────┐
│ Limiter Type │ Tokens Counted │ Formula         │
├─────────────────────────────────────────────────┤
│ TPM          │ 1000           │ 200 + 800       │
│ TPD          │ 1000           │ 200 + 800       │
│ ITPM         │ 200            │ 200 (input)     │
│ OTPM         │ 800            │ 800 (output)    │
│ RPM          │ 1              │ request count   │
│ RPD          │ 1              │ request count   │
│ CONCURRENT   │ 1              │ slot count      │
└─────────────────────────────────────────────────┘
```

### How They're Used in wait_for_all()

```python
async def wait_for_all(self, request: QueueRequest) -> None:
    for limiter in self.limiters:
        # Get the right token count for THIS limiter type
        tokens = self._get_tokens_for_limiter(limiter, request)
        
        # Check if limiter has capacity for this token count
        await limiter.wait_for_slot(tokens)
```

### Checking Capacity Example

```
Current state:
  TPM limiter: 85,000 / 90,000 tokens used
  ITPM limiter: 48,000 / 50,000 input tokens used
  OTPM limiter: 38,000 / 40,000 output tokens used

Request with 200 input + 800 output:

For TPM limiter:
    tokens_needed = 200 + 800 = 1000
    available = 90,000 - 85,000 = 5,000
    Can acquire? YES (1,000 <= 5,000) ✓

For ITPM limiter:
    tokens_needed = 200 (input only!)
    available = 50,000 - 48,000 = 2,000
    Can acquire? YES (200 <= 2,000) ✓

For OTPM limiter:
    tokens_needed = 800 (output only!)
    available = 40,000 - 38,000 = 2,000
    Can acquire? YES (800 <= 2,000) ✓
```

### Token Correction After Processing

After processor returns, actual tokens are used to adjust:

```python
# Processor returned actual tokens
actual_input = 210  (estimated 200)
actual_output = 790 (estimated 800)

# Chain adjusts each limiter
async def update_token_usage(
    self, 
    request: QueueRequest,
    actual_input: int,
    actual_output: int
) -> None:
    # For TPM limiter
    estimated_tpm = 200 + 800 = 1000
    actual_tpm = 210 + 790 = 1000
    diff = 1000 - 1000 = 0
    → No adjustment needed

    # For ITPM limiter
    estimated_itpm = 200
    actual_itpm = 210
    diff = 200 - 210 = -10  (underestimated)
    → await itpm_limiter.acquire(10)  # Penalize for overage

    # For OTPM limiter
    estimated_otpm = 800
    actual_otpm = 790
    diff = 800 - 790 = 10  (overestimated)
    → await otpm_limiter.release(10)  # Refund unused
```

### Real-World Scenario

```python
# Configuration for OpenAI GPT-4
config = ModelConfig(
    model_id="gpt-4",
    rate_limiters=[
        # OpenAI has different limits for different token types
        RateLimiterConfig(type=RateLimiterType.TPM, limit=90000),   # Total: 90k/min
        RateLimiterConfig(type=RateLimiterType.ITPM, limit=30000),  # Input: 30k/min
        RateLimiterConfig(type=RateLimiterType.OTPM, limit=60000),  # Output: 60k/min
    ]
)

# When a request comes in with 5,000 input tokens:
# - If it's a short response (expected 100 output tokens):
#   TPM limiter uses: 5,000 + 100 = 5,100 tokens
#   ITPM limiter uses: 5,000 tokens (not 5,100!)
#   OTPM limiter uses: 100 tokens (not 5,100!)
#
# - This allows proper enforcement of OpenAI's separate limits
```

---

## Summary Table

| Question | Answer | Implementation |
|----------|--------|-----------------|
| **Q1: How does chain work?** | Sequential gatekeeper via `wait_for_all()` | Each limiter blocks until capacity ready, no partial state |
| **Q2: Support 7 limiters?** | 3 classes (Request, Token, Concurrent) | Factory creates appropriate class, chain uses interface |
| **Q3: Distinguish token types?** | YES via `_get_tokens_for_limiter()` | Returns input/output/total based on limiter type |

---

## Code Files to Review

1. **`src/llm_queue/rate_limiters/chain.py`** - The orchestrator
   - `wait_for_all()` - Main gatekeeper method
   - `_get_tokens_for_limiter()` - Token distinction logic
   - `update_token_usage()` - Token correction

2. **`src/llm_queue/rate_limiters/factory.py`** - Creates limiters
   - `create_rate_limiter()` - Creates appropriate class
   - `create_chain()` - Creates chain from config

3. **`src/llm_queue/rate_limiters/request_limiter.py`** - RequestRateLimiter class
4. **`src/llm_queue/rate_limiters/token_limiter.py`** - TokenRateLimiter class
5. **`src/llm_queue/rate_limiters/concurrent_limiter.py`** - ConcurrentRateLimiter class
6. **`src/llm_queue/queue.py`** - Integration in Queue
   - `_process_queue()` - Calls `wait_for_all()`
   - `update_token_usage()` - Updates after processing
