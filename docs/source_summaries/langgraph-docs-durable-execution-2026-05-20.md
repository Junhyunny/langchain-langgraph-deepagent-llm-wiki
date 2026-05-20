---
type: source_summary
source_id: langgraph-docs-durable-execution-2026-05-20
title: "LangGraph — Durable execution documentation"
framework: LangGraph
retrieved_at: 2026-05-20
status: verified
confidence: high
---

# Source Summary: LangGraph — Durable Execution

## Source Info
- **Source ID:** `langgraph-docs-durable-execution-2026-05-20`
- **Type:** official_docs
- **URL:** https://docs.langchain.com/oss/python/langgraph/durable-execution
- **Retrieved At:** 2026-05-20
- **Version / Commit:** UNKNOWN

---

## Key Facts
- Durable execution allows LangGraph workflows to resume from the last successful checkpoint after interruption or failure.
- Execution progress is saved with a checkpointer and loaded later with the same thread configuration.
- LangGraph supports durability modes: `exit`, `async`, and `sync`.
- `exit` persists changes only when graph execution exits successfully, exits with an error, or exits due to a human-in-the-loop interrupt. It has better performance but cannot recover from mid-execution process crashes.
- `async` persists changes asynchronously while the next step executes. It balances performance and durability but has a small crash-window risk.
- `sync` persists changes synchronously before the next step begins. It provides the strongest durability with more overhead.
- Resume does not continue from the same Python call stack line. LangGraph finds an appropriate starting point and replays execution.
- For the Graph API, execution resumes from the beginning of the node where execution stopped.
- Interrupt resume uses `Command(resume=...)` with the same thread.
- Replay can re-run code after the chosen checkpoint. Side effects after that point can therefore happen again unless code is designed to avoid duplicates.
- The docs recommend making side effects idempotent or using LangGraph task mechanisms so results can be reused during replay.

---

## Important Terms
- [[Checkpointing]] — persistence mechanism used by durable execution.
- `Command(resume=...)` — command used to resume after an interrupt.
- `durability="exit" | "async" | "sync"` — execution method option controlling checkpoint persistence timing.
- deterministic replay — replay behavior that avoids re-running already persisted work where possible.

---

## Interpretation
- Durable execution depends on checkpointing but is not identical to checkpointing. Checkpointing stores runtime state; durable execution describes how the runtime uses that state after interruption or failure.
- Side-effect safety is a design responsibility for graph authors. Checkpoints do not automatically undo or deduplicate external calls.

---

## Implications for My AI Agent Project
- Any resume experiment should count node executions and external side effects separately.
- Human-in-the-loop flows should use stable `thread_id` values and explicit `Command(resume=...)` calls.
- Minimal reproductions should avoid irreversible side effects until replay behavior is fully understood.

---

## Open Questions
- Where are the durability modes implemented in the Pregel runtime?
- Which tests cover Graph API resume from the beginning of the interrupted node?

---

## Used By
- [[Checkpointing]]
- [[LangGraph StateGraph compile invoke flow]]

---

## Notes
- This source was used for resume semantics and side-effect guidance, not for saver implementation details.
