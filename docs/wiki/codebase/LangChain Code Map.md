---
type: code_map
framework: LangChain
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangChain Code Map

## Summary

This page maps the LangChain repository structure. Use it as a navigation guide when reading source code.

*Status: Draft stub. Needs source verification from actual repository.*

## Repository

- **Repo:** `https://github.com/langchain-ai/langchain`
- **Commit:** UNKNOWN

## Major Packages / Directories

```
langchain/                    # Main package
langchain_core/               # Core abstractions (Runnable, BaseMessage, etc.)
langchain_community/          # Community integrations
langchain_text_splitters/     # Text splitting utilities
libs/
  langchain/
  langchain_core/
  langchain_community/
```

*Needs source: Verify actual directory structure.*

## Important Entry Points

- `langchain_core.runnables` — `Runnable`, `RunnableSequence`, `RunnableLambda`
- `langchain.agents` — `create_react_agent`, `AgentExecutor`
- `langchain_core.messages` — `HumanMessage`, `AIMessage`, `ToolMessage`
- `langchain_core.tools` — `BaseTool`, `@tool`

*Needs source.*

## Source Files to Read

- TBD: Start from `langchain.agents.create_react_agent` → [[LangChain create_agent flow]]

## Tests to Read

- TBD

## Unclear Areas

- How does LCEL (pipe `|`) compose runnables internally?
- Where is the message type dispatch logic?

## Related Pages

- [[LangChain]]
- [[LangChain create_agent flow]]
- [[Tool Calling]]

## Sources

*None yet.*
