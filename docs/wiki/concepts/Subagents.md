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

# Subagents

## Summary

Subagents are agents that are invoked by a parent (orchestrating) agent as part of a larger workflow. Each subagent may have its own tools, state, and prompts.

*Status: Draft stub. Needs source verification.*

## Why It Matters

Subagent orchestration is the core pattern behind complex multi-agent systems. Understanding how parent agents delegate to subagents, how context is passed, and how results are collected is essential for building scalable agent pipelines.

## Key Concepts

- **Orchestrator** — top-level agent that plans and delegates
- **Subagent** — specialized agent receiving a subtask
- **Delegation** — passing a task or context from parent to subagent
- **Aggregation** — collecting and merging results from multiple subagents
- **Handoff** — transferring control between agents

## Framework-Specific Behavior

### LangChain

- Subagents can be wrapped as tools and invoked via [[Tool Calling]]
- *Needs source.*

### LangGraph

- Subagents can be separate `StateGraph` instances invoked as nodes
- Or implemented via `Send` for parallel dispatch
- *Needs source.*

### Deep Agents

- Subagent orchestration is a core design pattern
- `create_deep_agent` likely encapsulates subagent management
- *Needs source: Unverified.*

## Open Questions

- How does each framework pass context from orchestrator to subagent?
- How are results aggregated?
- What happens if a subagent fails?
- Is subagent state isolated or shared?

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[StateGraph]]
- [[Context Engineering]]
- [[Deep Agents create_deep_agent flow]]

## Sources

*None yet.*
