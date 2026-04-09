# Rate Limiter Chain: ASCII Diagrams

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        QueueManager                         │
│              (Singleton managing all models)                │
└────────────────┬────────────────────────────────────────────┘
                 │
      ┌──────────┼──────────┬──────────┐
      │          │          │          │
      ▼          ▼          ▼          ▼
   Queue     Queue      Queue      Queue
  gpt-4    claude    gpt-3.5    custom
      │          │          │          │
      └──────────┼──────────┴──────────┘
                 │
      ┌──────────▼──────────┐
      │ RateLimiterChain    │
      ├─────────────────────┤
      │ limiters[] =        │
      │ ├─ Request[RPM]     │
      │ ├─ Token[TPM]       │
      │ ├─ Token[ITPM]      │
      │ ├─ Token[OTPM]      │
      │ └─ Concurrent       │
      │                     │
      │ wait_for_all()      │ ← GATEKEEPER
      │ release_all()       │
      │ update_tokens()     │
      └─────────────────────┘
```

---

## Request Processing Flow

```
Request arrives
    │
    ▼
Manager.submit_request(request)
    │
    ├─→ request.estimated_input_tokens = 200
    ├─→ request.estimated_output_tokens = 800
    │
    ▼
Queue.enqueue(request)
    │
    ├─→ Add to asyncio.Queue
    ├─→ Create Future for result
    │
    ▼
Background: Queue._process_queue()
    │
    ├─→ while self._running:
    │       get request from queue
    │
    ▼
┌─────────────────────────────────────────┐
│ Chain.wait_for_all(request)             │ ← CRITICAL POINT
├─────────────────────────────────────────┤
│ For RequestRateLimiter (RPM):           │
│   needed = 1                            │
│   current = 8/10                        │
│   ✓ Can acquire                         │
│                                         │
│ For TokenRateLimiter (TPM):             │
│   needed = 200 + 800 = 1000             │
│   current = 80000/90000                 │
│   ✓ Can acquire                         │
│                                         │
│ For TokenRateLimiter (ITPM):            │
│   needed = 200 (input only!)            │
│   current = 45000/50000                 │
│   ✓ Can acquire                         │
│                                         │
│ For TokenRateLimiter (OTPM):            │
│   needed = 800 (output only!)           │
│   current = 38000/40000                 │
│   ✓ Can acquire                         │
│                                         │
│ For ConcurrentRateLimiter:              │
│   needed = 1                            │
│   current = 3/5 slots available         │
│   ✓ Can acquire                         │
│                                         │
│ ✓ ALL PASSED → Returns                  │
└─────────────────────────────────────────┘
    │
    ▼
Processor executes
    │
    result = await processor_func(request)
    │
    ▼
Chain.release_all(request)
    │
    ├─→ Release concurrent slots
    │
    ▼
Chain.update_token_usage(actual_input, actual_output)
    │
    ├─→ Actual: 210 input, 790 output
    │
    ├─→ For TPM:
    │   est=1000, actual=1000 → no change
    │
    ├─→ For ITPM:
    │   est=200, actual=210 → acquire(10) penalty
    │
    └─→ For OTPM:
        est=800, actual=790 → release(10) refund
    │
    ▼
Response created
    │
    ▼
Client receives response
```

---

## Token Distinction Flowchart

```
Request with estimated_input=200, estimated_output=800
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
      TPM         ITPM        OTPM
     limiter     limiter     limiter
        │           │           │
        ▼           ▼           ▼
   Use formula: Use formula: Use formula:
   input +      input only   output only
   output
        │           │           │
        ▼           ▼           ▼
     1000         200         800
   (total)     (input)     (output)
        │           │           │
        └───────────┼───────────┘
                    │
            All different values!
            Proper enforcement ✓
```

---

## What Happens If a Limiter Blocks

```
Scenario: ITPM limit reached (50,000/50,000)

Request arrives: need 300 input tokens

Chain.wait_for_all():
  │
  ├─ RPM: 8/10 ✓ Acquire
  ├─ TPM: capacity ✓ Acquire
  ├─ ITPM: 50000/50000 ✗ BLOCKED
  │
  └─ Request STUCK HERE

Queue State:
┌─────────────────────────────┐
│ Queue: [Req1, Req2, Req3]   │
│        ↑                    │
│     (blocked at ITPM)       │
└─────────────────────────────┘

[30 seconds later, window resets]

Chain.wait_for_all() retries:
  │
  ├─ RPM: 9/10 (old one expired) ✓ Acquire
  ├─ TPM: capacity ✓ Acquire
  ├─ ITPM: 40000/50000 ✓ Acquire ← NOW has capacity!
  ├─ OTPM: capacity ✓ Acquire
  ├─ CONCURRENT: capacity ✓ Acquire
  │
  └─ ALL PASSED → Process!
```

---

## The 3 Limiter Classes

```
┌─────────────────────────────────────────────────────────┐
│              BaseRateLimiter (Interface)                │
│  ┌────────────────────────────────────────────────────┐ │
│  │ async acquire(tokens) -> bool                       │ │
│  │ async release(tokens)                              │ │
│  │ async wait_for_slot(tokens)                        │ │
│  │ get_current_usage() -> int                         │ │
│  │ get_available_capacity() -> int                    │ │
│  └────────────────────────────────────────────────────┘ │
└──────┬──────────────────┬──────────────────────┬────────┘
       │                  │                      │
       ▼                  ▼                      ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│   Request    │  │    Token     │  │  Concurrent      │
│  Limiter     │  │  Limiter     │  │  Limiter         │
├──────────────┤  ├──────────────┤  ├──────────────────┤
│timestamps[]  │  │usage_history │  │_semaphore        │
│              │  │[(t, count)]  │  │                  │
│Sliding window│  │              │  │asyncio.Semaphore│
│with times    │  │Sliding window│  │                  │
│              │  │with counts   │  │Non-blocking      │
├──────────────┤  ├──────────────┤  │acquire() check   │
│RPM: 60s      │  │TPM: 60s      │  │_value < tokens   │
│RPD: 86400s   │  │TPD: 86400s   │  │                  │
│              │  │ITPM: 60s     │  │CONCURRENT        │
│              │  │OTPM: 60s     │  │max simultaneous  │
└──────────────┘  └──────────────┘  └──────────────────┘
      │                   │                    │
      │ handles           │ handles            │ handles
      │ RPM, RPD          │ TPM, TPD,          │ CONCURRENT
      │                   │ ITPM, OTPM         │
      └───────────────────┴────────────────────┘
              All in RateLimiterChain
```

---

## Token Correction Process

```
Before Processing
┌────────────────────────────────┐
│ Estimated Tokens              │
├────────────────────────────────┤
│ input:  200                    │
│ output: 800                    │
│ total:  1000                   │
└────────────────────────────────┘
          │
          │ Rate limiters reserve based on estimate
          │
          ▼
┌────────────────────────────────┐
│ TPM Limiter reserves: 1000     │
│ ITPM Limiter reserves: 200     │
│ OTPM Limiter reserves: 800     │
└────────────────────────────────┘

During Processing
┌────────────────────────────────┐
│ API call executes...           │
│ (takes 3-5 seconds)            │
└────────────────────────────────┘
          │
          ▼
After Processing
┌────────────────────────────────┐
│ Actual Tokens Used             │
├────────────────────────────────┤
│ input:  210 (vs est 200)       │
│ output: 790 (vs est 800)       │
│ total:  1000 (vs est 1000)     │
└────────────────────────────────┘
          │
          │ Calculate differences
          │
          ▼
┌────────────────────────────────┐
│ TPM: est=1000, actual=1000     │
│      diff=0 → no change        │
│                                │
│ ITPM: est=200, actual=210      │
│       diff=-10 → acquire(10)   │
│       (penalize overage)       │
│                                │
│ OTPM: est=800, actual=790      │
│       diff=10 → release(10)    │
│       (refund unused)          │
└────────────────────────────────┘
          │
          ▼
Limiters Updated
```

---

## Decision Tree: _get_tokens_for_limiter()

```
Get limiter type
    │
    ├─ RPM or RPD?
    │  └─→ return 1 (count request)
    │
    ├─ CONCURRENT?
    │  └─→ return 1 (count slot)
    │
    ├─ TPM or TPD?
    │  └─→ return est_input + est_output
    │      (count TOTAL tokens)
    │
    ├─ ITPM?
    │  └─→ return est_input
    │      (count INPUT tokens only)
    │
    └─ OTPM?
       └─→ return est_output
           (count OUTPUT tokens only)
```

---

## Sequential Acquisition: No Deadlock

```
Chain.wait_for_all(request):
    │
    ├─ Acquire Limiter[0]
    │  ├─ If blocked → wait
    │  └─ If success → continue
    │
    ├─ Acquire Limiter[1]
    │  ├─ If blocked → wait
    │  └─ If success → continue
    │
    ├─ Acquire Limiter[2]
    │  ├─ If blocked → wait
    │  └─ If success → continue
    │
    └─ All acquired → Return (request proceeds)

No circular waits = No deadlock ✓
Sequential = Clear order ✓
```

---

## Concurrency Slot Lifecycle

```
Request starts
    │
    ▼
Chain.wait_for_all() acquires 1 slot
    │
    ├─ Semaphore._value: 5 → 4
    │
    ▼
Processor executes
    │
    ├─ Request is processing
    ├─ Slot is held
    ├─ Other requests blocked if 5 already executing
    │
    ▼
Processing completes
    │
    ▼
Chain.release_all() releases slot
    │
    ├─ Semaphore._value: 4 → 5
    │
    ▼
Next request can acquire if waiting
```

---

## Multiple Models with Independent Chains

```
┌──────────────────────────────────────────┐
│           QueueManager                   │
├──────────────────────────────────────────┤
│                                          │
│  Model: gpt-4                            │
│  └─ Queue                                │
│     └─ RateLimiterChain                  │
│        ├─ RequestRateLimiter(10)         │
│        ├─ TokenRateLimiter(90000)        │
│        └─ ...                            │
│                                          │
│  Model: claude                           │
│  └─ Queue                                │
│     └─ RateLimiterChain (different!)     │
│        ├─ RequestRateLimiter(5)          │
│        ├─ TokenRateLimiter(100000)       │
│        └─ ...                            │
│                                          │
│  Model: gpt-3.5-turbo                    │
│  └─ Queue                                │
│     └─ RateLimiterChain (different!)     │
│        ├─ RequestRateLimiter(20)         │
│        ├─ TokenRateLimiter(90000)        │
│        └─ ...                            │
│                                          │
└──────────────────────────────────────────┘

No interference between models
Each model independent
```

---

## Summary Sequence

```
┌─────┐
│Start│
└────┬┘
     │
     ├─ Submit Request
     │  (with estimated tokens)
     │
     ├─ Queue it
     │
     ├─ wait_for_all()
     │  ├─ Check RPM/RPD
     │  ├─ Check TPM/TPD
     │  ├─ Check ITPM
     │  ├─ Check OTPM
     │  └─ Check CONCURRENT
     │  (BLOCK if any fail)
     │
     ├─ Execute Processor
     │
     ├─ release_all()
     │  (release concurrent slots)
     │
     ├─ update_token_usage()
     │  (correct estimates)
     │
     └─ Return Response
        │
        └─ ✓ Complete
```

These diagrams illustrate:
- The architecture with RateLimiterChain
- The request processing flow
- Token distinction per limiter type
- What happens when limiters block
- The 3 limiter classes
- Token correction mechanism
- Sequential acquisition (no deadlock)
- Slot lifecycle
- Multi-model independence
