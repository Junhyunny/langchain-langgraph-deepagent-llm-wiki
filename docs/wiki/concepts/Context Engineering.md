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

# Context Engineering

## Summary

Context engineering is the practice of deliberately constructing the context (system prompt, conversation history, tool descriptions, injected data) passed to an LLM in order to maximize the quality and reliability of its output.

*Status: Draft stub. Needs source verification.*

## Why It Matters

Context is the primary input to the LLM. Poor context construction leads to poor agent behavior. Understanding how frameworks build context is essential for diagnosing agent failures and improving agent quality.

## Key Concepts

- **System prompt** — top-level instructions to the LLM
- **Message history** — prior conversation turns
- **Tool schema injection** — tool descriptions added to context
- **RAG injection** — retrieved documents added to context
- **Context window** — maximum tokens the LLM can process
- **Context compression** — reducing history to fit within context window

## Framework-Specific Behavior

### LangChain

- `ChatPromptTemplate` constructs prompts
- Message history managed via `BaseChatMessageHistory`
- *Needs source.*

### LangGraph

- State messages list is passed to the LLM node
- Prompt is often constructed inside the node function
- *Needs source.*

### Deep Agents

- Context passing to subagents is a key concern
- *Needs source.*

## Open Questions

- How does each framework handle context window overflow?
- What compression or summarization strategies are built-in?
- How are tool descriptions formatted and injected?

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Memory]]
- [[Subagents]]
- [[Tool Calling]]

## Sources

*None yet.*
