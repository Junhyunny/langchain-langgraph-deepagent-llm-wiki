---
type: framework
framework: Deep Agents
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# Deep Agents

## Summary

Deep Agents is a framework (part of the LangChain ecosystem) designed for building deeply orchestrated multi-agent systems. It provides structured patterns for subagent creation, tool delegation, and multi-step reasoning.

*Status: Needs source. This page is a draft stub. The exact scope and repo location of "Deep Agents" should be verified.*

## Why It Matters

Deep Agents represents a higher-level abstraction on top of [[LangChain]] and potentially [[LangGraph]], enabling more sophisticated orchestration patterns. Understanding it reveals how complex multi-agent pipelines are composed.

## Core Abstractions

- `create_deep_agent()` — primary entry point (Needs source: exact signature and behavior)
- Subagent orchestration pattern
- Tool registry
- State and context passing between agents

*Needs source: All abstractions here are unverified.*

## Public APIs

- `create_deep_agent()` — Needs source.

## Internal Implementation Map

- TBD: Trace `create_deep_agent` → [[Deep Agents create_deep_agent flow]]

## Related Tests

- Needs source.

## Related Examples

- `examples/` — to be added.

## Open Questions

- What repository does Deep Agents live in? Is it `langchain-ai/deepagents`?
- What is the exact role of `create_deep_agent` vs `create_react_agent`?
- How does it handle subagent orchestration internally?
- What is the call path when a subagent is invoked?
- Where is the tool registry maintained?
- Does it depend on LangGraph for state management?

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Subagents]]
- [[Tool Calling]]
- [[Deep Agents Code Map]]
- [[Deep Agents create_deep_agent flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## Sources

*None yet.*
