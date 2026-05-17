# Open Questions

Questions collected during study. Move to relevant pages or remove when resolved.

---

## LangChain

- How does the agent executor decide when to stop tool calls?
- What is the difference between `AgentExecutor` and `create_react_agent`?
- Where is the message history managed internally?

## LangGraph

- How does `StateGraph.compile()` produce a runnable?
- How does checkpointing decide what to persist and what to discard?
- How does `interrupt_before` / `interrupt_after` work at the graph level?
- What is the difference between `MemorySaver` and a persistent checkpointer?
- How does streaming work with `astream_events`?

## Deep Agents

- What is the exact role of `create_deep_agent` vs `create_react_agent` in LangChain?
- How does Deep Agents handle subagent orchestration internally?
- What is the call path when a subagent is invoked?
- Where is the tool registry maintained?

## Cross-Framework

- How do the three frameworks compare in handling parallel tool calls?
- Which framework has the best support for human-in-the-loop?
- How does each framework handle context window limits?
- Can checkpoints from one framework be ported to another?

## PR Opportunities

- Are there any documented issues without tests in the three repos?
- Are there missing edge case tests in the checkpointing implementation?
