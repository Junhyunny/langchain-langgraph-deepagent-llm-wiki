---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# Memory

## Summary

Memory refers to the mechanisms that allow an LLM agent to retain and recall information across turns, sessions, or tasks. Memory can be short-term (within a session) or long-term (across sessions).

*Status: Draft stub. Needs source verification.*

## Why It Matters

Without memory, every agent turn is stateless. Memory enables continuity, personalization, and accumulated knowledge. Understanding how frameworks implement memory helps trace bugs and design better agents.

## Key Concepts

- **Short-term memory** — in-context message history within a session
- **Long-term memory** — external storage recalled across sessions
- **Episodic memory** — specific past events or interactions
- **Semantic memory** — general facts or knowledge
- **Memory store** — external database for long-term memory
- **Memory retrieval** — selecting relevant memories from storage

## Framework-Specific Behavior

### LangChain

- `ConversationBufferMemory`, `ConversationSummaryMemory`, etc.
- Attached to chains or agents
- *Needs source.*

### LangGraph

- State acts as short-term memory within a thread
- Long-term memory via external stores (e.g., `InMemoryStore`, vector stores)
- *Needs source.*

### Deep Agents

- TBD
- *Needs source.*

## Open Questions

- How does LangGraph's `MemorySaver` relate to conversation memory?
- What is the difference between a checkpointer and a memory store in LangGraph?
- How is long-term memory retrieved and injected into context?

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Checkpointing]]
- [[Context Engineering]]

## Sources

*None yet.*
