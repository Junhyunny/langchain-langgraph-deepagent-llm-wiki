---
type: concept
framework:
  - LangGraph
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# StateGraph

## Summary

`StateGraph` is the core abstraction in [[LangGraph]] for defining stateful agent graphs. It represents the agent as a directed graph of nodes (functions) and edges (transitions), operating on a shared typed state.

*Status: Draft stub. Needs source verification.*

## Why It Matters

`StateGraph` is the primary way to define complex agents in LangGraph. Understanding its compile and execution model is the foundation for understanding LangGraph internals.

## Key Concepts

- **State schema** — typed dict or dataclass defining the shared state
- **Node** — a Python function `(state) -> state_update`
- **Edge** — unconditional transition from one node to another
- **Conditional edge** — transition determined by a routing function
- **`START` / `END`** — special built-in nodes
- **`compile()`** — produces a `CompiledGraph` runnable
- **`invoke()` / `stream()`** — run the compiled graph

## Details

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class State(TypedDict):
    messages: list

graph = StateGraph(State)
graph.add_node("agent", agent_fn)
graph.add_node("tools", tool_fn)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")
compiled = graph.compile()
result = compiled.invoke({"messages": [...]})
```

*Needs source: Verify exact API.*

## Source Code References

- Repo: langgraph
- Commit: UNKNOWN
- Files: TBD

## Tests

- Needs source.

## Open Questions

- How does `StateGraph.compile()` produce a `CompiledGraph` internally?
- How are conditional edges evaluated at runtime?
- How does the state update merge work (reducers)?

## Related Pages

- [[LangGraph]]
- [[Checkpointing]]
- [[Tool Calling]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

## Sources

*None yet.*
