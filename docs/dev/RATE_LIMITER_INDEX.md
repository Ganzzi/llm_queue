# Rate Limiter Chain Documentation Index

This directory contains comprehensive documentation explaining how the RateLimiterChain works and how it supports all 7 rate limiter types with proper input/output/total token distinction.

## 📋 Documents

### 0. **ASCII_DIAGRAMS.md** (Visual Reference)
**Best for:** Visual learners who want ASCII diagrams

**Contains:**
- Architecture diagram of RateLimiterChain
- Request processing flow diagram
- Token distinction flowchart
- Limiter blocking scenario
- The 3 limiter classes diagram
- Token correction process
- Decision tree for token calculation
- Sequential acquisition diagram
- Concurrency slot lifecycle
- Multi-model architecture

**Read this if:** You're a visual learner and want ASCII diagrams

---

### 1. **DIRECT_ANSWERS.md** ⭐ START HERE
**Best for:** Getting quick, direct answers to your specific questions

**Contains:**
- Direct answer to: "How does the rate limiter chain work?"
- Direct answer to: "How does it support the 7 rate limiters?"
- Direct answer to: "Does it distinguish input vs output vs total tokens?"
- Code examples for each answer
- Real-world scenarios
- Summary table

**Read this if:** You want concise, focused answers with code examples

---

### 2. **CHAIN_VISUAL_SUMMARY.md**
**Best for:** Understanding the flow with visual diagrams and walkthroughs

**Contains:**
- Quick answer boxes for each question
- Visual flow diagrams
- Step-by-step processing timeline
- Multi-limiter scenario walkthrough
- What happens if a limit is reached (2 scenarios)
- Summary diagram of the architecture

**Read this if:** You're a visual learner and want to see examples play out

---

### 3. **RATE_LIMITER_CHAIN_EXPLAINED.md**
**Best for:** Comprehensive, detailed explanation with theory

**Contains:**
- Overview of the rate limiter chain concept
- Deep dive into each of the 7 rate limiter types
- How the chain is created from configuration
- Request processing flow with detailed explanation
- Complete multi-request scenario walkthrough
- Token overage/underage handling
- Key design principles
- Token correction example
- Architecture reference tables

**Read this if:** You want complete technical understanding and theory

---

### 4. **CHAIN_CODE_REFERENCE.md**
**Best for:** Detailed code implementation and implementation patterns

**Contains:**
- Complete factory.py code with comments
- Complete chain.py code with all methods
- The 3 limiter classes implementation (RequestRateLimiter, TokenRateLimiter, ConcurrentRateLimiter)
- Integration in Queue._process_queue()
- Request flow with token tracking code
- Line-by-line code walkthrough

**Read this if:** You're diving deep into the code implementation

---

## 🎯 Quick Navigation by Question

### **"How does the rate limiter chain work?"**
- **Quick answer** → DIRECT_ANSWERS.md (Q1)
- **Visual flow** → CHAIN_VISUAL_SUMMARY.md (Quick Answer section)
- **Detailed explanation** → RATE_LIMITER_CHAIN_EXPLAINED.md (How the Chain Works section)
- **Implementation details** → CHAIN_CODE_REFERENCE.md (Integration in Queue section)

### **"How does it support 7 rate limiters (RPM, RPD, TPM, TPD, ITPM, OTPM, CONCURRENT)?"**
- **Quick answer** → DIRECT_ANSWERS.md (Q2)
- **Visual overview** → CHAIN_VISUAL_SUMMARY.md (Architecture diagram)
- **Category breakdown** → RATE_LIMITER_CHAIN_EXPLAINED.md (The 7 Rate Limiter Types)
- **Code creation** → CHAIN_CODE_REFERENCE.md (factory.py section)

### **"Does it distinguish input tokens, output tokens, and total tokens?"**
- **Direct answer** → DIRECT_ANSWERS.md (Q3)
- **Visual example** → CHAIN_VISUAL_SUMMARY.md (Token Distinction table)
- **Complete explanation** → RATE_LIMITER_CHAIN_EXPLAINED.md (Token Calculation section)
- **Code implementation** → CHAIN_CODE_REFERENCE.md (_get_tokens_for_limiter method)

### **"Why doesn't my request process? (Rate limiting)"**
- → CHAIN_VISUAL_SUMMARY.md (What if a Limiter Blocks section)
- → DIRECT_ANSWERS.md (Q1 Example Scenario)

### **"How are tokens corrected after processing?"**
- → RATE_LIMITER_CHAIN_EXPLAINED.md (Token Overage/Underage Handling)
- → CHAIN_CODE_REFERENCE.md (update_token_usage code)
- → DIRECT_ANSWERS.md (Q3 Token Correction section)

---

## 🔑 Key Concepts Explained in Each Document

### RateLimiterChain.wait_for_all()
| Document | Content |
|----------|---------|
| DIRECT_ANSWERS | How it's called and what it returns |
| CHAIN_VISUAL_SUMMARY | Visual flow of wait_for_all() |
| RATE_LIMITER_CHAIN_EXPLAINED | Detailed step-by-step behavior |
| CHAIN_CODE_REFERENCE | Full method code with comments |

### The 7 Rate Limiter Types
| Document | Content |
|----------|---------|
| DIRECT_ANSWERS | Why 7 types, how factory creates them |
| CHAIN_VISUAL_SUMMARY | Category breakdown |
| RATE_LIMITER_CHAIN_EXPLAINED | Deep dive into each type |
| CHAIN_CODE_REFERENCE | Implementation of each class |

### Token Distinction (Input vs Output vs Total)
| Document | Content |
|----------|---------|
| DIRECT_ANSWERS | How distinction happens with code |
| CHAIN_VISUAL_SUMMARY | Table showing token counts |
| RATE_LIMITER_CHAIN_EXPLAINED | _get_tokens_for_limiter() logic |
| CHAIN_CODE_REFERENCE | Full method implementation |

### Request Lifecycle
| Document | Content |
|----------|---------|
| DIRECT_ANSWERS | Example scenario in queue |
| CHAIN_VISUAL_SUMMARY | Visual timeline of processing |
| RATE_LIMITER_CHAIN_EXPLAINED | Request flow diagram |
| CHAIN_CODE_REFERENCE | Queue._process_queue() code |

---

## 📊 Document Complexity Level

```
Complexity ↑
    │
    │   CHAIN_CODE_REFERENCE.md
    │   (Deep implementation details)
    │
    │   RATE_LIMITER_CHAIN_EXPLAINED.md
    │   (Complete technical explanation)
    │
    │   CHAIN_VISUAL_SUMMARY.md
    │   (Visual flows and walkthroughs)
    │
    │   DIRECT_ANSWERS.md ⭐
    │   (Focused, concise answers)
    │
    └─────────────────────────→ Complexity
```

---

## 🚀 Recommended Reading Order

### **For Quick Understanding (5 minutes)**
1. Read DIRECT_ANSWERS.md completely

### **For Visual Understanding (15 minutes)**
1. DIRECT_ANSWERS.md (quick reference)
2. CHAIN_VISUAL_SUMMARY.md (see flows)
3. CHAIN_VISUAL_SUMMARY.md Multi-Limiter walkthrough

### **For Complete Understanding (30 minutes)**
1. DIRECT_ANSWERS.md (questions answered)
2. CHAIN_VISUAL_SUMMARY.md (visual reinforcement)
3. RATE_LIMITER_CHAIN_EXPLAINED.md (full details)

### **For Implementation Details (45 minutes)**
1. CHAIN_CODE_REFERENCE.md (code overview)
2. Review actual source files:
   - `src/llm_queue/rate_limiters/chain.py`
   - `src/llm_queue/rate_limiters/factory.py`
   - `src/llm_queue/queue.py`

---

## 💡 Key Takeaways

### About wait_for_all()
✅ Sequentially waits for each limiter  
✅ If any blocks, request stays in queue  
✅ All limiters must pass before processing  
✅ Returns when ALL are ready  

### About 7 Rate Limiters
✅ 3 classes (Request, Token, Concurrent)  
✅ Factory creates appropriate class  
✅ Chain treats all identically  
✅ Type info stored for token calculation  

### About Token Distinction
✅ YES - fully distinguished  
✅ TPM/TPD = input + output  
✅ ITPM = input only  
✅ OTPM = output only  
✅ Calculated per limiter in _get_tokens_for_limiter()  

### About Queue Behavior
✅ Request blocks if any limiter unavailable  
✅ Stays in queue (not lost)  
✅ Retried after window resets  
✅ Atomic - all limiters or none  

---

## 🔗 Related Files in Source Code

```
src/llm_queue/
├── rate_limiters/
│   ├── __init__.py
│   ├── base.py              ← Interface (BaseRateLimiter)
│   ├── chain.py             ← RateLimiterChain (main orchestrator)
│   ├── factory.py           ← Creates limiters from config
│   ├── request_limiter.py   ← RequestRateLimiter class
│   ├── token_limiter.py     ← TokenRateLimiter class
│   └── concurrent_limiter.py ← ConcurrentRateLimiter class
├── queue.py                 ← Queue uses chain via wait_for_all()
├── manager.py               ← QueueManager creates queues
├── models.py                ← RateLimiterConfig, QueueRequest
└── ...
```

---

## 🎓 Learning Path

```
Start Here
    ↓
DIRECT_ANSWERS.md
├─ Understand Q1, Q2, Q3
├─ See code examples
└─ Review scenario examples
    ↓
CHAIN_VISUAL_SUMMARY.md
├─ See visual flows
├─ Review timeline walkthrough
└─ Understand queue blocking
    ↓
RATE_LIMITER_CHAIN_EXPLAINED.md
├─ Deep dive into types
├─ Token calculation logic
└─ Design principles
    ↓
CHAIN_CODE_REFERENCE.md
├─ Review actual code
├─ See method signatures
└─ Understand integration
    ↓
Source Code Review
├─ src/llm_queue/rate_limiters/chain.py
├─ src/llm_queue/queue.py
└─ Experiment with the code
```

---

## ❓ FAQ

**Q: Is the code distinguishing input vs output vs total tokens?**
A: YES! See DIRECT_ANSWERS.md (Q3) for the complete answer with code.

**Q: Why does my request stay in the queue?**
A: One of its limiters doesn't have capacity. See CHAIN_VISUAL_SUMMARY.md "What Happens If a Limit Is Reached".

**Q: How does RPM differ from ITPM?**
A: RPM counts requests, ITPM counts input tokens. See RATE_LIMITER_CHAIN_EXPLAINED.md "The 7 Rate Limiter Types".

**Q: When are tokens released?**
A: CONCURRENT slots are released in release_all(). See CHAIN_CODE_REFERENCE.md "Integration in Queue".

**Q: How are overestimated tokens handled?**
A: Via release() call in update_token_usage(). See RATE_LIMITER_CHAIN_EXPLAINED.md "Token Overage/Underage Handling".

---

## 📝 Document Statistics

| Document | Length | Read Time |
|----------|--------|-----------|
| DIRECT_ANSWERS.md | ~200 lines | 5-10 min |
| CHAIN_VISUAL_SUMMARY.md | ~250 lines | 10-15 min |
| RATE_LIMITER_CHAIN_EXPLAINED.md | ~300 lines | 15-20 min |
| CHAIN_CODE_REFERENCE.md | ~350 lines | 20-30 min |

**Total comprehensive documentation: ~1100 lines**

---

Last updated: December 13, 2025
