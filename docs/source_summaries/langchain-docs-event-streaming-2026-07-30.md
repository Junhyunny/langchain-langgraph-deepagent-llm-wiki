---
type: source_summary
framework:
  - LangChain
  - LangGraph
status: verified
confidence: high
updated_at: 2026-07-30
sources:
  - langchain-docs-event-streaming-2026-07-30
---

# LangChain event streaming documentation

## Source identity

- URL: `https://docs.langchain.com/oss/python/langchain/event-streaming`
- Retrieved: 2026-07-30
- Status: public official documentation

## Verified facts

- For most application and frontend use cases, the documentation recommends
  `stream_events(..., version="v3")`.
- v3 returns a run object with typed projections rather than requiring callers
  to parse Pregel stream-mode tuples.
- LangChain agents share the LangGraph streaming stack because `create_agent`
  produces a compiled LangGraph.
- The lower-level `stream()` / `astream()` APIs remain relevant for Pregel
  modes such as `updates`, `messages`, and `custom`.
- `Runnable.stream_events` in `langchain-core==1.5.2` still defaults to
  `version="v2"`; callers must request v3 explicitly.

## Sources

- `langchain-docs-event-streaming-2026-07-30`
