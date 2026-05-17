---
type: flow
framework: LangGraph
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangGraph StateGraph compile invoke flow

## Summary

This page traces the execution flow from `StateGraph.compile()` through `.invoke()`, covering how the graph is built and how it executes.

*Status: Draft stub. No source code has been read yet. All content below is hypothesis.*

## Entry Point

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(State)
graph.add_node("agent", agent_fn)
graph.add_node("tools", tool_fn)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", route_fn, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")

compiled = graph.compile(checkpointer=MemorySaver())
result = compiled.invoke({"messages": [...]}, config={"configurable": {"thread_id": "1"}})
```

## Call Path (Hypothesis — Unverified)

### compile()

1. `StateGraph.compile(checkpointer)`
   - Validates graph structure
   - Builds internal representation (Pregel-like?)
   - Attaches checkpointer
   - Returns `CompiledStateGraph`

### invoke()

1. `CompiledStateGraph.invoke(input, config)`
   - Loads checkpoint for thread_id if exists
   - Merges input with checkpoint state
   - Enters execution loop

2. Execution loop:
   - Determines next node(s) from current state
   - Executes node function
   - Applies state reducers to merge update
   - Saves checkpoint
   - Checks for `interrupt_before` / `interrupt_after`
   - Repeats until `END`

3. Returns final state

## Files to Read

- TBD: `libs/langgraph/langgraph/graph/state.py` (`StateGraph`, `CompiledStateGraph`)
- TBD: `libs/langgraph/langgraph/pregel/` (execution runtime)
- TBD: `libs/checkpoint/langgraph/checkpoint/base.py`

## Tests Found

- TBD

## Diagrams

```
compile(checkpointer)
    │
    ▼
validate graph
    │
    ▼
build CompiledStateGraph
    │
    ▼
invoke(input, config)
    │
    ▼
load checkpoint (thread_id)
    │
    ▼
merge input + checkpoint state
    │
    ▼
─────── execution loop ───────
    │
    ▼
determine next node
    │
    ▼
execute node fn(state) → update
    │
    ▼
apply state reducers
    │
    ▼
save checkpoint
    │
    ├── interrupt? → pause (return partial state)
    │
    └── continue
            │
            ▼
        more nodes? → loop
            │
        END → return final state
──────────────────────────────
```

## Open Questions

- Is the runtime based on Pregel? Where is this in the code?
- How do state reducers work? Where are they defined and applied?
- How does `interrupt_before` halt execution and serialize state?
- What exactly is stored in each checkpoint?

## Related Pages

- [[LangGraph]]
- [[StateGraph]]
- [[Checkpointing]]
- [[LangGraph Code Map]]

## Sources

*None yet.*
