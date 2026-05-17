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

# Tool Calling

## Summary

Tool calling is the mechanism by which an LLM selects and invokes external functions (tools) during inference. The LLM outputs a structured tool call request; the runtime executes the tool and returns the result as a message.

*Status: Draft stub. Needs source verification.*

## Why It Matters

Tool calling is the primary way LLM agents interact with external systems. Understanding it is essential for building agents, debugging unexpected behavior, and tracing the call path from model output to tool execution.

## Key Concepts

- Tool definition (name, description, schema)
- Tool invocation (structured output from LLM)
- Tool execution (runtime calling the function)
- Tool result (returned as `ToolMessage`)
- Tool registry (collection of available tools)

## Framework-Specific Behavior

### LangChain

- Tools are passed to `create_react_agent()` or bound to a model via `.bind_tools()`
- `AgentExecutor` handles the tool call loop
- *Needs source.*

### LangGraph

- Tools are typically nodes in a `StateGraph`
- Or handled via `ToolNode` from `langgraph.prebuilt`
- *Needs source.*

### Deep Agents

- TBD — tool registry and tool delegation mechanism unclear
- *Needs source.*

## Implementation Notes

- Tool schemas are typically JSON Schema
- LLM must support function/tool calling natively (e.g., OpenAI, Anthropic)
- Parallel tool calls: multiple tools can be called in one LLM step

## Open Questions

- How does each framework handle parallel tool calls internally?
- What happens when a tool raises an exception?
- How are tool schemas validated?

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[StateGraph]]
- [[Subagents]]

## Sources

*None yet.*
