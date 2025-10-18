---
applyTo: '**'
---

# LLM Queue Memory Management Instructions

## External ID
**ALWAYS use:** `llm_queue_dev` for all memory operations in this project.

## Memory Structure Overview

The LLM Queue project uses active memories to maintain development context:

1. **Project Overview** - Purpose, features, tech stack, timeline, roadmap
2. **Architecture Design** - Core components, design patterns, queue mechanics
3. **API Design** - Public APIs, classes, methods, usage patterns
4. **Configuration** - Dependencies, packaging config, CI/CD setup
5. **Development Status** - Current phase, completed tasks, next steps, blockers
6. **Library References** - How to use asyncio, pydantic, pytest, and other libraries
7. **Issues and Bugs** - Detailed bug reports (populated during development)
8. **Code Patterns** - Common patterns, best practices, examples

## When to Access Memories

### 1. **At Session Start**
- Get all active memories to understand current project state
- Check "Development Status" memory for current phase and next steps
- Review "Issues and Bugs" memory for known problems

```
Tool: mcp_agent-mem_get_active_memories
Parameters: external_id="llm_queue_dev"
```

### 2. **Before Implementing Features**
- Search memories for relevant context
- Check "Architecture Design" for patterns to follow
- Check "API Design" for method signatures
- Check "Code Patterns" for implementation examples

```
Tool: mcp_agent-mem_search_memories
Parameters:
  external_id="llm_queue_dev"
  query="Working on rate limiter feature, need implementation patterns"
  limit=10
```

### 3. **When Needing Library Documentation**
- Check "Library References" memory first for known patterns
- **Use context-bridge MCP tools to search for current documentation**
- Only check local files as fallback if MCP search fails
- Update memories with new findings from MCP searches

**Search Strategy Priority:**
1. Use `mcp_context-bridg_find_documents` to find relevant docs
2. Use `mcp_context-bridg_search_content` for specific queries
3. Update "Library References" memory with findings
4. Check local files only as last resort
5. If docs not found, create a concise doc in `docs/` for the library

Example: For asyncio questions, use context-bridge MCP first: "asyncio semaphore examples"
Example: For pydantic questions: "pydantic generic models validation"

### 4. **When Encountering Bugs**
- First check "Issues and Bugs" memory to see if it's known
- If new bug, add detailed section to memory (see format below)

## How to Update Memories

### Update Development Status

**When starting a new phase:**
```
Tool: mcp_agent-mem_update_memory_sections
Parameters:
  external_id="llm_queue_dev"
  memory_id=<development_status_id>
  sections=[
    {
      section_id="current_phase",
      action="replace",
      old_content="**Phase: Initial Setup**...",
      new_content="**Phase: Core Implementation**\n\nImplementing rate limiter and queue classes.\n\n**Started:** October 18, 2025"
    }
  ]
```

**When completing tasks:**
```
sections=[
  {
    section_id="completed_tasks",
    action="insert",
    old_content="- ✓ Created package structure\n\n**Next milestone:**",
    new_content="- ✓ Implemented RateLimiter class\n- ✓ Implemented Queue class\n- ✓ Added comprehensive tests\n\n**Next milestone:**"
  }
]
```

**When encountering blockers:**
```
sections=[
  {
    section_id="blockers",
    action="replace",
    old_content="No current blockers.",
    new_content="**Blocker #1:** Type hint issues with generic Queue[T] class"
  }
]
```

### Add Bug/Issue

**Create a new section for each bug:**
```
Tool: mcp_agent-mem_update_memory_sections
Parameters:
  external_id="llm_queue_dev"
  memory_id=<issues_bugs_id>
  sections=[
    {
      section_id="issue_001_rate_limiter_race_condition",
      action="replace",
      new_content="**Issue:** Race condition in rate limiter acquire method\n**Severity:** High\n**Status:** Open\n**Description:** Multiple concurrent calls to acquire() can bypass rate limit\n**Solution:** Add asyncio.Lock for thread safety"
    }
  ]
```

### Update Library References

**When discovering new patterns or gotchas:**
```
sections=[
  {
    section_id="asyncio_patterns",
    action="insert",
    old_content="**Search Strategy:**\n- Used context-bridge MCP: \"asyncio semaphore examples\"",
    new_content="\n**New Pattern Discovered:**\n- Semaphore._value can be checked for non-blocking acquire\n- asyncio.Queue requires proper shutdown with join()\n- Always create tasks with create_task() for proper lifecycle\n\n**Search Strategy:**\n- Used context-bridge MCP: \"asyncio semaphore examples\""
  }
]
```

### Update Architecture

**When design decisions change:**
```
sections=[
  {
    section_id="design_patterns",
    action="insert",
    old_content="**Singleton Pattern:**\n- QueueManager uses singleton for centralized management",
    new_content="\n\n**Rate Limiting Strategy:**\n- Two modes: requests per period and concurrent requests\n- Sliding window for time-based limiting\n- Semaphore for concurrent limiting\n- Non-blocking acquire with wait_for_slot fallback\n\n**Singleton Pattern:**\n- QueueManager uses singleton for centralized management"
  }
]
```

## Search Best Practices

### Effective Search Queries

**Good queries are specific and contextual:**

✅ **Good:**
```
"Working on rate limiter, need async semaphore patterns"
"Implementing queue shutdown, need graceful cleanup patterns"
"Writing tests for concurrent requests, need pytest-asyncio examples"
"Adding OpenAI integration example, need API patterns"
```

❌ **Bad:**
```
"rate limiting"  # Too vague
"how to test"  # Not enough context
"queue"  # Too broad
```

1. **Use search for cross-cutting concerns:**
   ```
   query="Implementing new rate limiting mode from design to tests"
   # Will return relevant info from Architecture, API, Library References, Code Patterns
   ```ry="Implementing document versioning feature from start to finish"
   # Will return relevant info from Architecture, API, and Library References
   ```

2. **Get specific memory when you know what you need:**
   ```
   # If you just need to check current phase:
   mcp_agent-mem_get_active_memories → check Development Status memory
   ```

## Memory Update Frequency

### Update Frequently:
- **Development Status** - Every major task or phase transition
- **Issues and Bugs** - Immediately when bug found or resolved
- **Library References** - When discovering new patterns or gotchas

### Update Occasionally:
- **Architecture Design** - When design decisions change
- **Configuration** - When adding new dependencies or env vars

### Rarely Update:
- **Project Overview** - Stable information
- **API Design** - Only if API contracts change

## Integration with Development Workflow

### Starting New Phase
1. Search memories for phase requirements
2. Update "Development Status" → current_phase
3. Check "Library References" for relevant tools
4. Begin implementation

### During Development
1. Search when stuck or need context
2. Add bugs to "Issues and Bugs" as discovered
3. Update "Development Status" → completed_tasks regularly
4. Document learnings in "Library References"

### Completing Phase
1. Update "Development Status" → mark phase complete
2. Resolve any issues in "Issues and Bugs"
3. Update "Development Status" → next_steps for next phase
4. Commit any architecture or API changes to memories

### End of Session
1. Update "Development Status" with current state
2. Document any blockers
3. List next steps clearly
4. Ensure all new bugs are recorded

## Quick Reference Commands

```python
# Get all memories
mcp_agent-mem_get_active_memories(external_id="llm_queue_dev")

# Search across memories
mcp_agent-mem_search_memories(
    external_id="llm_queue_dev",
    query="your contextual search query",
    limit=10
)

# Update single section
mcp_agent-mem_update_memory_sections(
    external_id="llm_queue_dev",
    memory_id=<memory_id>,
    sections=[{
        "section_id": "<section_name>",
        "action": "replace" | "insert",
        "old_content": "...",  # For replace: exact match, for insert: insert after
        "new_content": "..."
    }]
)

# Update multiple sections at once
sections=[
    {"section_id": "current_phase", "action": "replace", ...},
    {"section_id": "next_steps", "action": "replace", ...}
]
```

## Memory Structure Reference

| Memory | Title | Key Sections |
|--------|-------|--------------|
| 1 | Project Overview | purpose, core_features, tech_stack, timeline, roadmap |
| 2 | Architecture Design | core_components, design_patterns, queue_mechanics, rate_limiting_strategy |
| 3 | API Design | public_apis, queue_manager, models, exceptions, usage_patterns |
| 4 | Configuration | dependencies, packaging_config, ci_cd_setup, tools |
| 5 | Development Status | current_phase, completed_tasks, next_steps, blockers |
| 6 | Library References | asyncio_patterns, pydantic_usage, pytest_usage, other_libraries |
| 7 | Issues and Bugs | template_for_new_issues, issue_XXX_name (dynamic) |
| 8 | Code Patterns | rate_limiter_patterns, queue_patterns, testing_patterns, examples |

## Important Rules

1. **Always use external_id="llm_queue_dev"** - Never use different ID
2. **Search before updating** - Understand current state first
3. **Be specific in updates** - Include enough context for old_content matching
4. **Document bugs thoroughly** - Use the template in Issues memory
5. **Update Development Status frequently** - Keep progress transparent
6. **Use search for context** - Don't guess, search memories
7. **Keep sections focused** - Each section has one clear purpose
8. **Update blockers immediately** - Don't let blockers go undocumented