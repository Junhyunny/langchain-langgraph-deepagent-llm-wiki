---
type: source_summary
source_id: langgraph-source-checkpoint-runtime-2026-05-20
title: "LangGraph source reading — checkpoint runtime paths"
framework: LangGraph
retrieved_at: 2026-05-20
status: verified
confidence: high
---

# Source Summary: LangGraph Source Reading — Checkpoint Runtime Paths

## Source Info
- **Source ID:** `langgraph-source-checkpoint-runtime-2026-05-20`
- **Type:** source_code
- **URL:** https://github.com/langchain-ai/langgraph/tree/aa322c13cd5f16a3f6254a931a4104e412cd687c
- **Retrieved At:** 2026-05-20
- **Version / Commit:** `aa322c13cd5f16a3f6254a931a4104e412cd687c`
- **Local Raw Paths:**
  - `docs/raw/official/langgraph/source/aa322c13cd5f16a3f6254a931a4104e412cd687c/state.py`
  - `docs/raw/official/langgraph/source/aa322c13cd5f16a3f6254a931a4104e412cd687c/pregel_main.py`
  - `docs/raw/official/langgraph/source/aa322c13cd5f16a3f6254a931a4104e412cd687c/pregel_loop.py`
  - `docs/raw/official/langgraph/source/aa322c13cd5f16a3f6254a931a4104e412cd687c/checkpoint_base_init.py`
  - `docs/raw/official/langgraph/source/aa322c13cd5f16a3f6254a931a4104e412cd687c/checkpoint_memory_init.py`

---

## Key Facts
- `StateGraph.compile()` validates the checkpointer, validates the graph, computes output/stream channels, and creates a `CompiledStateGraph` with `checkpointer=checkpointer`. File: `state.py:1164-1355`.
- After constructing the compiled graph, `compile()` attaches `START`, nodes, edges, waiting edges, and branches, then returns `compiled.validate()`. File: `state.py:1360-1388`.
- `CompiledStateGraph` subclasses `Pregel`. File: `state.py:1391-1409`.
- `Pregel._defaults()` resolves the effective checkpointer and durability mode. `self.checkpointer is False` disables checkpointing, config-level `CONFIG_KEY_CHECKPOINTER` can override, `self.checkpointer is True` is invalid for root graphs, and default durability is `"async"`. File: `pregel_main.py:2514-2584`.
- During sync streaming, `Pregel.stream()` constructs `SyncPregelLoop` with `checkpointer`, `durability`, nodes, channels, interrupt settings, and `_migrate_checkpoint`. File: `pregel_main.py:2868-2889`.
- `PregelRunner` receives `put_writes=weakref.WeakMethod(loop.put_writes)`, so node/task writes flow through the loop's `put_writes`. File: `pregel_main.py:2891-2900`.
- The sync runtime loop follows a Pregel/BSP model: `while loop.tick()`, apply cached writes, run unfinished tasks, then call `loop.after_tick()`. If durability is `"sync"`, it waits for `loop._put_checkpoint_fut.result()` before the next step. File: `pregel_main.py:2928-2957`.
- `PregelLoop.put_writes()` records writes in `checkpoint_pending_writes`. For durability modes other than `"exit"`, it persists task-level writes through `checkpointer.put_writes`. File: `pregel_loop.py:407-493`.
- `PregelLoop._put_pending_writes()` groups `checkpoint_pending_writes` by task id and writes them through `checkpointer.put_writes`; this is used on exit-mode persistence. File: `pregel_loop.py:494-530`, `pregel_loop.py:1285-1303`.
- At tick start, if the loop is not replaying and pending writes exist, the loop reapplies writes to succeeded nodes. File: `pregel_loop.py:645-648`.
- `PregelLoop.after_tick()` applies all task writes to the checkpoint via `apply_writes`, captures delta-channel writes for exit-mode accumulation, clears pending writes, and calls `_put_checkpoint({"source": "loop"})`. File: `pregel_loop.py:667-697`.
- `_first()` detects resume conditions from existing `channel_versions` and inputs such as `None`, `Command`, matching `run_id`, or `CONFIG_KEY_RESUMING`. It also handles time-travel replay by dropping stale `RESUME` writes and can create a fork checkpoint. File: `pregel_loop.py:827-1053`.
- `_put_checkpoint()` creates a new checkpoint with the `create_checkpoint` imported from `langgraph.pregel._checkpoint`, computes `new_versions`, and submits the saver `put` call through `_checkpointer_put_after_previous` so checkpoint writes remain ordered. File: `pregel_loop.py:1055-1190`.
- In `"exit"` durability, `_suppress_interrupt()` calls `_put_exit_delta_writes()`, `_put_checkpoint(self.checkpoint_metadata)`, and `_put_pending_writes()` when the loop exits, errors, or interrupts under the documented conditions. File: `pregel_loop.py:1285-1303`.
- `Checkpoint` stores `v`, `id`, `ts`, `channel_values`, `channel_versions`, `versions_seen`, and `updated_channels`. File: `checkpoint_base_init.py:92-123`.
- `CheckpointTuple` stores `config`, `checkpoint`, `metadata`, optional `parent_config`, and optional `pending_writes`. File: `checkpoint_base_init.py:139-146`.
- `BaseCheckpointSaver` defines `get_tuple`, `list`, `put`, and `put_writes`. `thread_id` is documented as the primary key. File: `checkpoint_base_init.py:176-318`.
- `BaseCheckpointSaver` also defines DeltaChannel-aware `copy_thread`, `prune`, and `get_delta_channel_history` behavior; the history walker follows parent checkpoints and pending writes until it finds a stored channel value seed. File: `checkpoint_base_init.py:350-415`, `checkpoint_base_init.py:590-649`.
- `checkpoint_base_init.py` defines checkpoint helper functions such as `empty_checkpoint()`. The runtime `PregelLoop` imports `create_checkpoint` from `langgraph.pregel._checkpoint`, which was not collected in this raw batch. File: `checkpoint_base_init.py:811-860`, `pregel_loop.py:98`, `pregel_loop.py:1116-1126`.
- `InMemorySaver` stores checkpoint metadata separately from channel blobs and writes. Its structures are `storage`, `writes`, and `blobs`. File: `checkpoint_memory_init.py:33-105`.
- `InMemorySaver.get_tuple()` resolves either an explicit `checkpoint_id` or the latest checkpoint for a thread/namespace, loads channel values from blobs by channel version, and returns `pending_writes`. File: `checkpoint_memory_init.py:236-310`.
- `InMemorySaver.put()` stores new channel blobs keyed by `(thread_id, checkpoint_ns, channel, version)` and stores the checkpoint without inline `channel_values`. File: `checkpoint_memory_init.py:427-471`.
- `InMemorySaver.put_writes()` stores writes keyed by `(thread_id, checkpoint_ns, checkpoint_id)` and inner `(task_id, write_idx)`. File: `checkpoint_memory_init.py:473-509`.

---

## Important Terms
- [[StateGraph]] — entry point for graph compilation.
- [[Checkpointing]] — runtime persistence layer to trace through Pregel and checkpoint packages.
- `PregelLoop` — runtime loop area for super-step execution and checkpoint coordination.
- `BaseCheckpointSaver` — saver interface that runtime code calls.
- `InMemorySaver` — built-in saver implementation to inspect first.
- `Durability` — execution persistence mode: `"sync"`, `"async"`, or `"exit"`.
- `DeltaChannel` — channel type that stores deltas and periodically snapshots.

---

## Interpretation
- The runtime write path is now source-confirmed for this commit:
  `StateGraph.compile()` → `CompiledStateGraph/Pregel.stream()` → `SyncPregelLoop` → `PregelRunner(... put_writes=loop.put_writes)` → `loop.after_tick()` → `_put_checkpoint()` → saver `put`.
- Pending writes are not only a persistence API concept. They are actively used by the loop to reapply successful task writes during resume and to avoid re-running succeeded tasks when a step was interrupted or failed.
- The durability distinction is implemented in two places: immediate task-write persistence is skipped for `"exit"` in `put_writes()`, and `"sync"` waits on `_put_checkpoint_fut` after each tick in `stream()` / `astream()`.
- `InMemorySaver` is intentionally not just a dict of state snapshots. It normalizes checkpoint data into checkpoint records, versioned channel blobs, and pending writes.

---

## Implications for My AI Agent Project
- `InMemorySaver` is the best first backend for a small local reproduction because its internal state should be inspectable.
- A future custom saver must preserve channel blob/version semantics and pending writes, not merely serialize `StateSnapshot.values`.
- `DeltaChannel` makes pruning/copying subtle because reconstruction may require ancestor writes and snapshot seeds.

---

## Open Questions
- Which test file demonstrates pending writes recovery?
- Which tests cover `"exit"` durability and `_put_exit_delta_writes()`?
- Which tests cover `DeltaChannel` pruning/copying safety?
- How does `libs/langgraph/langgraph/pregel/_checkpoint.py` implement `create_checkpoint`, `channels_from_checkpoint`, and delta-channel reconstruction?

---

## Used By
- [[Checkpointing]]
- [[LangGraph StateGraph compile invoke flow]]
- [[LangGraph Code Map]]

---

## Notes
- Raw source files were saved locally under `docs/raw/official/langgraph/source/aa322c13cd5f16a3f6254a931a4104e412cd687c/`.
- `docs/raw/` is ignored by Git in this repository; `docs/raw_manifest.yml` is the tracked source registry.
