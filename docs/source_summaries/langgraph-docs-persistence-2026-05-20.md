---
type: source_summary
source_id: langgraph-docs-persistence-2026-05-20
title: "LangGraph — Persistence documentation"
framework: LangGraph
retrieved_at: 2026-05-20
status: verified
confidence: high
---

# Source Summary: LangGraph — Persistence

## Source Info
- **Source ID:** `langgraph-docs-persistence-2026-05-20`
- **Type:** official_docs
- **URL:** https://docs.langchain.com/oss/python/langgraph/persistence
- **Retrieved At:** 2026-05-20
- **Version / Commit:** UNKNOWN

---

## Key Facts
- LangGraph has a built-in persistence layer that saves graph state as checkpoints when a graph is compiled with a checkpointer.
- Checkpoints are organized into threads. The checkpointer uses `thread_id` as the primary key for storing and retrieving checkpoints.
- Without `thread_id`, the checkpointer cannot save state or resume after an interrupt.
- A checkpoint is a snapshot of graph state at a particular point in a thread.
- LangGraph creates checkpoints at super-step boundaries. A super-step is one graph tick in which all currently scheduled nodes execute, possibly in parallel.
- By default, LangGraph checkpoints write the full value of every state channel at each super-step.
- For a sequential graph like `START -> A -> B -> END`, the docs show separate checkpoints for the initial empty checkpoint, input, node A output, and node B output.
- LangGraph also persists node/task-level writes within a super-step. These writes support pending-write recovery if one node in the same super-step fails after another node has completed.
- `StateSnapshot` fields include `values`, `next`, `config`, `metadata`, `created_at`, `parent_config`, and `tasks`.
- `metadata` includes `source`, `writes`, and `step`.
- `tasks` include task identifiers, names, errors, interrupts, and optionally subgraph state snapshots.
- `graph.get_state(config)` returns the latest checkpoint for a `thread_id`, or a specific checkpoint if `checkpoint_id` is provided.
- `graph.get_state_history(config)` returns checkpoints for a thread, with the most recent checkpoint first.
- Replay with a prior `checkpoint_id` skips nodes before that checkpoint and re-executes nodes after it.
- `update_state` creates a new checkpoint rather than mutating the original checkpoint.
- Checkpointers save state within a thread. Cross-thread memory belongs to the `Store` interface, not the checkpointer alone.

---

## Important Terms
- [[Checkpointing]] — graph state persistence at super-step boundaries.
- [[StateGraph]] — graph builder whose compiled graph can use a checkpointer.
- [[Memory]] — thread-scoped memory through checkpoints, distinct from cross-thread store memory.
- `thread_id` — primary key used by the checkpointer to store and retrieve a thread's checkpoints.
- `checkpoint_id` — identifier for a specific checkpoint within a thread.
- `StateSnapshot` — public representation of saved graph state.
- `super-step` — execution tick after which a full checkpoint is committed.
- `pending writes` — task-level writes saved before full super-step completion for fault tolerance.

---

## Interpretation
- In LangGraph, checkpointing is not just final-result persistence. It is part of the runtime model: each super-step produces inspectable, resumable state.
- The checkpointer records enough scheduling information (`next`, `tasks`, parent checkpoint config) to continue graph execution from a boundary, not merely reload a dictionary.
- Pending writes are a finer-grained fault-tolerance mechanism than `StateSnapshot` checkpoints. They are durable node outputs linked to an in-progress checkpoint, but time travel still resumes from full checkpoints at super-step boundaries.
- Checkpointing and long-term memory are related but separate. Reusing a `thread_id` gives conversation/session continuity; sharing facts across threads requires a `Store`.

---

## Implications for My AI Agent Project
- Any experiment about durable agents should log `thread_id`, `checkpoint_id`, and `StateSnapshot.next`; otherwise resume behavior is hard to reason about.
- To reduce surprise, node outputs should be small and state schemas should avoid storing large transient data unless that data is intentionally part of the checkpointed state.
- For human-in-the-loop experiments, use `thread_id` as the stable workflow instance id and inspect `tasks[*].interrupts`.
- To test replay safely, isolate external side effects because replay re-executes nodes after the selected checkpoint.

---

## Open Questions
- Which runtime code path commits the full checkpoint after each super-step?
- How do `DeltaChannel` and `BaseCheckpointSaver.get_delta_channel_history` alter or optimize the default full-channel snapshot behavior?
- Where in source are full checkpoint writes separated from pending writes?

---

## Used By
- [[Checkpointing]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

---

## Notes
- The public docs mention both full super-step checkpoints and node/task-level writes. Treat these as separate persistence layers.
