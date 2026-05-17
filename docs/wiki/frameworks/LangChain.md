---
type: framework
framework: LangChain
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangChain

## Summary

LangChain is a framework for building LLM-powered applications. It provides abstractions for chains, agents, tools, memory, and document loaders.

*Status: Needs source. This page is a draft stub.*

## Why It Matters

LangChain is the foundational framework in this ecosystem. Understanding it is necessary before understanding LangGraph and Deep Agents, both of which build on LangChain abstractions.

## Core Abstractions

- `Runnable` — base interface for all composable components
- `Chain` — sequence of operations
- `AgentExecutor` — runtime that runs an agent in a loop
- `Tool` — external capability exposed to an LLM
- `BaseChatModel` — base class for all LLM integrations
- `BaseMemory` — base class for memory systems
- `BaseRetriever` — base class for document retrieval

## Public APIs

- `create_react_agent()`
- `AgentExecutor`
- `ChatPromptTemplate`
- `RunnableSequence` / LCEL pipe `|`

*Needs source: Verify which module each lives in.*

## Internal Implementation Map

- TBD: Trace `create_react_agent` → [[LangChain create_agent flow]]

## Related Tests

- Needs source.

## Related Examples

- `examples/` — to be added.

## Open Questions

- How does `AgentExecutor` decide when to stop the tool-call loop?
- What is the difference between `create_react_agent` and `create_openai_functions_agent`?
- Where is message history managed internally?

## Related Pages

- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[Memory]]
- [[LangChain Code Map]]
- [[LangChain create_agent flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## Sources

*None yet.*
