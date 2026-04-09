# Rate Limiter Chain: Code Implementation Reference

## Core Implementation Files

### 1. `factory.py` - Creates Limiters from Config

```python
def create_rate_limiter(config: RateLimiterConfig) -> BaseRateLimiter:
    """Create appropriate limiter based on type"""
    
    if config.type in (RateLimiterType.RPM, RateLimiterType.RPD):
        # Request-based limiter
        time_period = config.time_period
        if time_period is None:
            time_period = 60 if config.type == RateLimiterType.RPM else 86400
        limiter = RequestRateLimiter(limit=config.limit, time_period=time_period)
    
    elif config.type == RateLimiterType.CONCURRENT:
        # Concurrent limiter
        limiter = ConcurrentRateLimiter(limit=config.limit)
    
    elif config.type in (RateLimiterType.TPM, RateLimiterType.TPD, 
                         RateLimiterType.ITPM, RateLimiterType.OTPM):
        # Token-based limiters
        time_period = config.time_period
        if time_period is None:
            time_period = 60 if config.type != RateLimiterType.TPD else 86400
        limiter = TokenRateLimiter(limit=config.limit, time_period=time_period)
    
    # Store the type on the limiter for later identification
    setattr(limiter, "rate_limiter_type", config.type)
    return limiter

def create_chain(configs: List[RateLimiterConfig]) -> RateLimiterChain:
    """Create chain from configuration list"""
    limiters = [create_rate_limiter(config) for config in configs]
    return RateLimiterChain(limiters)
```

### 2. `chain.py` - Orchestrates Multiple Limiters

#### Main Methods

```python
class RateLimiterChain:
    def __init__(self, limiters: List[BaseRateLimiter]):
        self.limiters = limiters

    async def wait_for_all(self, request: QueueRequest) -> None:
        """
        CRITICAL METHOD: Wait until ALL limiters have capacity.
        
        If ANY limiter blocks, request stays in queue until ready.
        """
        for limiter in self.limiters:
            # Calculate tokens needed for THIS specific limiter
            tokens = self._get_tokens_for_limiter(limiter, request)
            
            # Block until this limiter has capacity (and acquire it)
            await limiter.wait_for_slot(tokens)

    async def release_all(self, request: QueueRequest) -> None:
        """Release slots (mainly for CONCURRENT limiter)"""
        for limiter in self.limiters:
            if isinstance(limiter, ConcurrentRateLimiter):
                tokens = self._get_tokens_for_limiter(limiter, request)
                await limiter.release(tokens)

    async def update_token_usage(
        self, 
        request: QueueRequest, 
        actual_input: int, 
        actual_output: int
    ) -> None:
        """
        Adjust for differences between estimated and actual tokens.
        
        Ensures rate limiter accounting stays accurate.
        """
        est_input = request.estimated_input_tokens or 0
        est_output = request.estimated_output_tokens or 0

        for limiter in self.limiters:
            if isinstance(limiter, TokenRateLimiter):
                limiter_type = getattr(limiter, "rate_limiter_type", None)
                
                estimated = 0
                actual = 0

                # Calculate based on limiter type
                if limiter_type in (RateLimiterType.TPM, RateLimiterType.TPD):
                    # Total tokens
                    estimated = est_input + est_output
                    actual = actual_input + actual_output
                
                elif limiter_type == RateLimiterType.ITPM:
                    # Input tokens only
                    estimated = est_input
                    actual = actual_input
                
                elif limiter_type == RateLimiterType.OTPM:
                    # Output tokens only
                    estimated = est_output
                    actual = actual_output
                else:
                    continue

                # Adjust for difference
                diff = estimated - actual
                if diff > 0:
                    # Overestimated - release refund
                    await limiter.release(diff)
                elif diff < 0:
                    # Underestimated - penalize with acquire
                    await limiter.acquire(abs(diff))

    def _get_tokens_for_limiter(
        self, 
        limiter: BaseRateLimiter, 
        request: QueueRequest
    ) -> int:
        """
        KEY METHOD: Distinguish input vs output vs total tokens.
        
        Returns the number of tokens to count for this specific limiter.
        """
        limiter_type = getattr(limiter, "rate_limiter_type", None)
        
        if not limiter_type:
            return 1  # Safe fallback

        # Request-based and concurrent always count 1
        if limiter_type in (RateLimiterType.RPM, RateLimiterType.RPD, 
                           RateLimiterType.CONCURRENT):
            return 1
        
        # Token-based distinguish by type
        est_input = request.estimated_input_tokens or 0
        est_output = request.estimated_output_tokens or 0

        if limiter_type in (RateLimiterType.TPM, RateLimiterType.TPD):
            # TOTAL TOKENS = input + output
            return est_input + est_output
        
        elif limiter_type == RateLimiterType.ITPM:
            # INPUT TOKENS ONLY
            return est_input
        
        elif limiter_type == RateLimiterType.OTPM:
            # OUTPUT TOKENS ONLY
            return est_output
            
        return 1
```

---

## The 3 Limiter Classes

### 1. RequestRateLimiter

```python
class RequestRateLimiter(BaseRateLimiter):
    """Limits requests in a time window using sliding window"""
    
    def __init__(self, limit: int, time_period: int):
        self.limit = limit              # e.g., 10
        self.time_period = time_period  # e.g., 60 (seconds)
        self.timestamps: List[float] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire immediately (non-blocking)"""
        async with self._lock:
            now = time.time()
            self._cleanup(now)
            
            # Can acquire if not at limit
            if len(self.timestamps) + tokens <= self.limit:
                for _ in range(tokens):
                    self.timestamps.append(now)
                return True
            return False
    
    async def wait_for_slot(self, tokens: int = 1) -> None:
        """Block until slot available"""
        while True:
            if await self.acquire(tokens):
                return
            await asyncio.sleep(0.1)  # Wait 100ms before retrying
    
    def _cleanup(self, now: float) -> None:
        """Remove timestamps older than time_period"""
        self.timestamps = [t for t in self.timestamps 
                          if now - t < self.time_period]

# Example: RPM limiter with limit=10, time_period=60
# Allows 10 requests per 60 seconds
```

### 2. TokenRateLimiter

```python
class TokenRateLimiter(BaseRateLimiter):
    """Limits tokens consumed in a time window"""
    
    def __init__(self, limit: int, time_period: int):
        self.limit = limit              # e.g., 90000
        self.time_period = time_period  # e.g., 60 (seconds)
        self.usage_history: List[Tuple[float, int]] = []  # (time, count)
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int) -> bool:
        """Try to acquire immediately (non-blocking)"""
        async with self._lock:
            now = time.time()
            self._cleanup(now)
            
            # Sum current usage
            current_usage = sum(count for _, count in self.usage_history)
            
            # Can acquire if total doesn't exceed limit
            if current_usage + tokens <= self.limit:
                self.usage_history.append((now, tokens))
                return True
            return False
    
    async def release(self, tokens: int) -> None:
        """Release tokens (refund overestimate)"""
        async with self._lock:
            now = time.time()
            # Add negative entry to offset usage
            self.usage_history.append((now, -tokens))
    
    async def wait_for_slot(self, tokens: int) -> None:
        """Block until capacity available"""
        while True:
            if await self.acquire(tokens):
                return
            await asyncio.sleep(0.1)
    
    def _cleanup(self, now: float) -> None:
        """Remove entries older than time_period"""
        self.usage_history = [
            (t, count) for t, count in self.usage_history
            if now - t < self.time_period
        ]

# Examples:
# TPM: limit=90000, time_period=60 (90k tokens per 60 seconds)
# ITPM: limit=50000, time_period=60 (50k input tokens per 60 seconds)
# OTPM: limit=40000, time_period=60 (40k output tokens per 60 seconds)
```

### 3. ConcurrentRateLimiter

```python
class ConcurrentRateLimiter(BaseRateLimiter):
    """Limits simultaneous/concurrent requests using Semaphore"""
    
    def __init__(self, limit: int):
        self.limit = limit
        self._semaphore = asyncio.Semaphore(limit)
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire immediately (non-blocking check)"""
        # Check if enough slots available
        if self._semaphore._value < tokens:
            return False
        
        # Acquire the slots
        for _ in range(tokens):
            await self._semaphore.acquire()
        return True
    
    async def release(self, tokens: int = 1) -> None:
        """Release slots immediately"""
        for _ in range(tokens):
            self._semaphore.release()
    
    async def wait_for_slot(self, tokens: int = 1) -> None:
        """Block until slots available"""
        for _ in range(tokens):
            await self._semaphore.acquire()
    
    def get_current_usage(self) -> int:
        """Get number of slots in use"""
        return max(0, self.limit - self._semaphore._value)
    
    def get_available_capacity(self) -> int:
        """Get number of free slots"""
        return self._semaphore._value

# Example: limit=5 (max 5 concurrent requests)
```

---

## Integration in Queue

```python
class Queue(Generic[P, T]):
    def __init__(
        self,
        model_id: str,
        processor_func: Callable[[QueueRequest[P]], Awaitable[T]],
        rate_limiter_chain: RateLimiterChain,
    ):
        self.model_id = model_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self.processor_func = processor_func
        self.rate_limiter_chain = rate_limiter_chain
        self.requests: Dict[str, QueueRequest[P]] = {}
        self._running = True
        
        # Start background processing task
        self.task = asyncio.create_task(self._process_queue())
    
    async def _process_queue(self) -> None:
        """Background task that processes requests"""
        while self._running or not self.queue.empty():
            try:
                # Get request from queue (with timeout to check _running)
                try:
                    item = await asyncio.wait_for(
                        self.queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                request: QueueRequest[P]
                future: asyncio.Future[QueueResponse[T]]
                request, future = item
                
                # ↓ CRITICAL: Wait for ALL rate limiters
                await self.rate_limiter_chain.wait_for_all(request)
                # ↑ If ANY limiter has no capacity, request stays in queue
                
                # Process the request
                start_time = time.time()
                try:
                    result = await self.processor_func(request)
                    request.status = RequestStatus.COMPLETED
                except Exception as e:
                    request.status = RequestStatus.FAILED
                    request.error = str(e)
                    result = None
                finally:
                    # Release concurrent slots (if any)
                    await self.rate_limiter_chain.release_all(request)
                
                processing_time = time.time() - start_time
                
                # Create response
                response = QueueResponse(
                    request_id=request.id,
                    model_id=request.model_id,
                    status=request.status,
                    result=result,
                    error=request.error,
                    processing_time=processing_time,
                    created_at=request.created_at,
                    input_tokens_used=request.actual_input_tokens,
                    output_tokens_used=request.actual_output_tokens,
                )
                
                # Resolve future so enqueue() returns
                if not future.cancelled():
                    future.set_result(response)
                
                # Move to completed history for token updates
                self.requests.pop(request.id, None)
                self.completed_requests[request.id] = request
                self._cleanup_history()
                
            except Exception as e:
                # Handle unexpected errors
                pass
    
    async def update_token_usage(
        self, 
        request_id: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> None:
        """
        Update actual token usage after processing.
        
        Called from processor function to correct estimates.
        """
        request = (self.requests.get(request_id) or 
                  self.completed_requests.get(request_id))
        if not request:
            return
        
        # Store actual tokens
        request.actual_input_tokens = input_tokens
        request.actual_output_tokens = output_tokens
        
        # Adjust all rate limiters for the difference
        await self.rate_limiter_chain.update_token_usage(
            request, 
            input_tokens, 
            output_tokens
        )
```

---

## Request Flow with Token Tracking

```python
# 1. Processor function receives request with estimates
async def processor(request: QueueRequest[dict]) -> dict:
    # Request has:
    # - estimated_input_tokens: 200
    # - estimated_output_tokens: 800
    
    # Call API (e.g., OpenAI)
    response = await openai.ChatCompletion.create(
        messages=request.params["messages"],
        model="gpt-4",
    )
    
    # Get actual tokens from response
    actual_input = response.usage.prompt_tokens
    actual_output = response.usage.completion_tokens
    
    # 2. Update queue with actual tokens
    queue = manager.queues[request.model_id]
    await queue.update_token_usage(
        request.id,
        actual_input,
        actual_output
    )
    
    # 3. Return result
    return {"response": response.choices[0].message.content}

# Flow in _process_queue:
# 1. wait_for_all(request) 
#    ├─ Uses estimated_input_tokens=200
#    ├─ Uses estimated_output_tokens=800
#    ├─ Reserve 1000 tokens in TPM limiter
#    ├─ Reserve 200 tokens in ITPM limiter
#    ├─ Reserve 800 tokens in OTPM limiter
#    └─ Acquires from all (request blocks if any unavailable)
# 
# 2. result = await processor(request)
#    ├─ Processor calls API
#    ├─ Gets actual: 210 input, 790 output
#    └─ Calls update_token_usage(210, 790)
# 
# 3. update_token_usage adjusts:
#    ├─ TPM: est=1000, actual=1000 → no change
#    ├─ ITPM: est=200, actual=210 → acquire(10) penalty
#    └─ OTPM: est=800, actual=790 → release(10) refund
```

---

## Conclusion

The RateLimiterChain implementation:

1. **Creates limiters** from configuration using factory pattern
2. **Stores type information** on each limiter for identification
3. **Waits sequentially** for each limiter via `wait_for_all()`
4. **Distinguishes token types** via `_get_tokens_for_limiter()` method
5. **Keeps requests in queue** if any limiter blocks
6. **Corrects accounting** via `update_token_usage()` after processing
7. **Releases concurrent slots** via `release_all()` after processing

This ensures:
- ✅ Multiple limits enforced simultaneously
- ✅ All token types properly tracked
- ✅ Requests atomic (all limits or none)
- ✅ Accurate token accounting across requests
