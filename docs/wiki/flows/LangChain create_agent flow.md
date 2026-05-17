---
type: flow
framework: LangChain
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangChain create_agent flow

## Summary

This page traces the execution flow of creating and running a LangChain agent, starting from `create_react_agent()`.

*Status: Draft stub. No source code has been read yet. All content below is hypothesis.*

## Entry Point

```python
from langchain.agents import create_react_agent, AgentExecutor
agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "..."})
```

## Call Path (Hypothesis — Unverified)

1. `create_react_agent(llm, tools, prompt)`
   - Binds tools to LLM
   - Constructs agent runnable
2. `AgentExecutor.invoke(input)`
   - Formats input
   - Enters agent loop
3. Agent loop:
   - Calls LLM with current messages
   - Parses tool calls from LLM output
   - Executes tools
   - Appends results to message history
   - Repeats until no tool calls or max iterations reached
4. Returns final output

## Files to Read

- TBD: `langchain/agents/react/base.py` or similar
- TBD: `langchain/agents/agent.py` (`AgentExecutor`)
- TBD: `langchain_core/runnables/`

## Tests Found

- TBD

## Diagrams

```
invoke(input)
    │
    ▼
AgentExecutor
    │
    ▼
format messages
    │
    ▼
LLM call
    │
    ├── no tool calls → return output
    │
    └── tool calls
            │
            ▼
        execute tools
            │
            ▼
        append ToolMessage(s)
            │
            ▼
        LLM call (loop)
```

## Open Questions

- Where exactly is the tool call parsing logic?
- How does `AgentExecutor` handle max iterations?
- Where is message history accumulated?

## Related Pages

- [[LangChain]]
- [[LangChain Code Map]]
- [[Tool Calling]]
- [[LangChain vs LangGraph vs Deep Agents]]

## Sources

*None yet.*
