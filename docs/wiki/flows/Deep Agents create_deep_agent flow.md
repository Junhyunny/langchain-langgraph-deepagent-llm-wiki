---
type: flow
framework: Deep Agents
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# Deep Agents create_deep_agent flow

## Summary

This page traces the execution flow of `create_deep_agent()` in Deep Agents.

*Status: Draft stub. No source code has been read yet. Repository location is unverified. All content is hypothesis.*

## Entry Point

```python
# Hypothetical — needs source
from deepagents import create_deep_agent

agent = create_deep_agent(
    llm=...,
    tools=...,
    subagents=...,
)
result = agent.invoke({"input": "..."})
```

*Needs source: Actual API signature unknown.*

## Call Path (Hypothesis — Unverified)

1. `create_deep_agent(llm, tools, subagents, ...)`
   - Builds orchestrator agent
   - Registers subagents (possibly as tools)
   - Constructs execution graph (LangGraph-based?)

2. `agent.invoke(input)`
   - Orchestrator receives input
   - Plans task decomposition
   - Delegates subtasks to subagents
   - Collects and aggregates results
   - Returns final output

## Files to Read

- TBD: Need to locate the actual repository first

## Tests Found

- TBD

## Open Questions

- What is the actual repository URL?
- What is the function signature of `create_deep_agent`?
- Does it use LangGraph internally?
- How are subagents represented (as tools? as nodes? as separate graphs)?
- How is context passed to subagents?
- How are results aggregated?

## Related Pages

- [[Deep Agents]]
- [[Deep Agents Code Map]]
- [[Subagents]]
- [[LangGraph]]
- [[Tool Calling]]

## Sources

*None yet.*
