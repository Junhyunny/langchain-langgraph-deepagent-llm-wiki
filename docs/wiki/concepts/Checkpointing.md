---
type: concept
framework:
  - LangGraph
  - LangChain
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# Checkpointing

## Summary

Checkpointing is the mechanism for persisting the state of an agent graph between steps or across sessions. In [[LangGraph]], checkpoints are saved after each node execution and can be resumed from any saved point.

*Status: Draft stub. Needs source verification.*

## Why It Matters

Checkpointing enables:
- Long-running agent workflows that can be paused and resumed
- Human-in-the-loop interactions (pause for approval, resume after)
- Fault tolerance (resume from last checkpoint after failure)
- Debugging (replay from any checkpoint)
- Multi-session continuity (same thread, different sessions)

## Key Concepts

- **Checkpoint** — a snapshot of the graph state at a given step
- **Thread ID** — identifies a conversation or session thread
- **Checkpoint ID** — identifies a specific snapshot within a thread
- **`BaseCheckpointSaver`** — abstract interface for checkpoint storage
- **`MemorySaver`** — in-memory, non-persistent checkpointer
- **Persistent checkpointers** — SQLite, PostgreSQL-backed (Needs source)

## Framework-Specific Behavior

### LangGraph

- `StateGraph.compile(checkpointer=saver)` enables checkpointing
- `config = {"configurable": {"thread_id": "..."}}`
- State delta is persisted after each node execution
- `MemorySaver` for development; persistent saver for production
- *Needs source: Verify exact behavior.*

### LangChain

- Limited native checkpointing support
- *Needs source.*

## Implementation Notes

- Each checkpoint stores: node name, state snapshot, next nodes
- Resuming reloads the last checkpoint and continues execution
- *Needs source.*

## Source Code References

- Repo: langgraph
- Commit: UNKNOWN
- Files: TBD (`libs/langgraph/`, `libs/checkpoint/`)

## Tests

- Needs source.

## Open Questions

- How does LangGraph decide what state delta to persist per step?
- What is stored in each checkpoint exactly?
- How does `interrupt_before` pause execution and what does the checkpoint look like?
- What are the differences between `MemorySaver` and SQLite saver?
- Can checkpoints be migrated across schema versions?

## Related Pages

- [[LangGraph]]
- [[StateGraph]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

## Sources

*None yet.*
