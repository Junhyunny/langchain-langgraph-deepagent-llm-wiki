---
type: framework
framework: LangGraph
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangGraph

## Summary

LangGraph is a library for building stateful, multi-actor LLM applications as graphs. It extends LangChain with explicit state management, checkpointing, and graph-based control flow.

*Status: Needs source. This page is a draft stub.*

## Why It Matters

LangGraph is the primary orchestration framework for complex agents requiring persistent state, human-in-the-loop, and structured execution flows. Understanding it is critical for building and contributing to modern AI agents.

## Core Abstractions

- `StateGraph` — defines nodes, edges, and state schema
- `CompiledGraph` — compiled runnable produced by `StateGraph.compile()`
- `BaseCheckpointSaver` — abstract class for persistence
- `MemorySaver` — in-memory checkpointer (non-persistent)
- `interrupt_before` / `interrupt_after` — human-in-the-loop hooks
- `Send` — dynamic edge to route to multiple targets

## Public APIs

- `StateGraph(schema)`
- `graph.add_node(name, fn)`
- `graph.add_edge(from, to)`
- `graph.add_conditional_edges(from, fn, map)`
- `graph.compile(checkpointer=...)`
- `compiled.invoke(input, config)`
- `compiled.stream(input, config)`
- `compiled.astream_events(input, config)`

*Needs source: Verify module paths.*

## Internal Implementation Map

- TBD: Trace `StateGraph.compile()` and `.invoke()` → [[LangGraph StateGraph compile invoke flow]]
- TBD: Trace checkpointing → [[Checkpointing]]

## Related Tests

- Needs source.

## Related Examples

- `examples/` — to be added.

## Open Questions

- How does `StateGraph.compile()` produce a runnable internally?
- How does checkpointing decide what state delta to persist?
- How does `interrupt_before` pause and resume execution?
- What is the difference between `MemorySaver` and a persistent checkpointer?

## Related Pages

- [[LangChain]]
- [[Deep Agents]]
- [[StateGraph]]
- [[Checkpointing]]
- [[Tool Calling]]
- [[Subagents]]
- [[LangGraph Code Map]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## Sources

*None yet.*
