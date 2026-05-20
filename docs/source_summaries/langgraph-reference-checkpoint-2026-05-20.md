---
type: source_summary
source_id: langgraph-reference-checkpoint-2026-05-20
title: "LangGraph — checkpoint API reference"
framework: LangGraph
retrieved_at: 2026-05-20
status: verified
confidence: high
---

# Source Summary: LangGraph — Checkpoint API Reference

## Source Info
- **Source ID:** `langgraph-reference-checkpoint-2026-05-20`
- **Type:** official_reference
- **URL:** https://reference.langchain.com/python/langgraph.checkpoint
- **Retrieved At:** 2026-05-20
- **Version / Commit:** `langgraph-checkpoint` reference reports v4.0.3 on related `BaseCheckpointSaver` pages.

---

## Key Facts
- `langgraph.checkpoint` defines the base interface for LangGraph checkpointers.
- Checkpointers provide the persistence layer for LangGraph and save a checkpoint of graph state at every super-step.
- A `Checkpoint` is a snapshot of graph state at a point in time.
- A `CheckpointTuple` contains checkpoint data plus associated config, metadata, and pending writes.
- A `Thread` is a unique ID assigned to a series of checkpoints; graph execution with a checkpointer requires `thread_id` and can optionally specify `checkpoint_id`.
- Pending writes preserve writes from successful nodes when another node fails in the same super-step, so successful nodes do not need to be re-run during resume.
- The accessible checkpoint reference page lists `BaseCheckpointSaver` methods including `.put`, `.put_writes`, `.get_tuple`, `.list`, `.delete_thread`, and `.get_next_version`.
- Async graph execution requires async versions such as `.aput`, `.aput_writes`, `.aget_tuple`, and `.alist`.
- `put_writes` stores intermediate writes linked to a checkpoint with `config`, `writes`, `task_id`, and optional `task_path`.
- The Checkpointing reference describes checkpoints as including channel values, channel versions, and version tracking per node.
- The reference lists `InMemorySaver`, SQLite, Postgres, and other saver implementations.

---

## Important Terms
- [[Checkpointing]] — persistence layer implemented by `BaseCheckpointSaver` implementations.
- `BaseCheckpointSaver` — abstract saver interface for storing and retrieving graph checkpoints.
- `CheckpointTuple` — loaded checkpoint plus config, metadata, and pending writes.
- `put` — stores a full checkpoint with config and metadata.
- `put_writes` — stores task-level writes linked to a checkpoint.
- `get_tuple` — retrieves a checkpoint tuple for a config.
- `list` — lists checkpoints matching a config/filter.

---

## Interpretation
- The runtime separates durable full checkpoints from intermediate task writes. This explains why failure recovery can avoid re-running successful parallel work even before a complete super-step checkpoint has been committed.
- Channel versioning is central to checkpoint correctness. A checkpoint is more than plain state values; it also tracks versions needed by the graph runtime.
- Custom checkpointers should be treated as runtime infrastructure, not just simple key-value stores, because they must preserve config, metadata, writes, versions, and async behavior when needed.

---

## Implications for My AI Agent Project
- A local reproduction should inspect `get_state_history()` first, then inspect saver internals only if needed.
- If building a custom saver later, start from the required `BaseCheckpointSaver` interface and validate sync/async requirements separately.
- For PR hunting, checkpoint saver docs/examples may be a good area because the conceptual model has multiple layers: checkpoint, thread, pending writes, and store.

---

## Open Questions
- Which tests define the canonical behavior for pending writes recovery?
- How does `InMemorySaver` store checkpoints and pending writes internally in LangGraph 1.2.x / `langgraph-checkpoint` 4.x?
- Do newer reference pages expose additional saver methods such as pruning, run deletion, thread copying, or delta channel history? Version alignment needs confirmation.

---

## Used By
- [[Checkpointing]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

---

## Notes
- The StateGraph compile reference page reports `StateGraph.compile` as v1.1.10, while the GitHub repository page showed `langgraph==1.2.0` as the latest release on 2026-05-20. Version alignment should be confirmed before PR work.
