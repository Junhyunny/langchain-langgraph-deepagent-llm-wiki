---
type: comparison
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangChain vs LangGraph vs Deep Agents

## Summary

Quick decision rule:
- Use **LangChain** for simple chains and single-agent patterns with tools.
- Use **LangGraph** when you need persistent state, checkpointing, or complex multi-step control flow.
- Use **Deep Agents** when you need structured multi-agent orchestration with subagents.

*Status: Hypothesis only. All claims need verification.*

## Comparison Table

| Dimension              | LangChain          | LangGraph              | Deep Agents           |
|------------------------|--------------------|------------------------|-----------------------|
| Abstraction level      | Chains, Agents     | Graphs, State          | Multi-agent, Subagents|
| State management       | Basic (memory)     | First-class (StateGraph) | TBD                 |
| Checkpointing          | Limited            | Built-in               | TBD                   |
| Human-in-the-loop      | Limited            | Built-in (interrupt)   | TBD                   |
| Parallelism            | Limited            | Supported              | TBD                   |
| Complexity             | Low                | Medium                 | High                  |
| Primary use case       | Chains, RAG        | Stateful agents        | Multi-agent pipelines |
| Relationship           | Foundation         | Extends LangChain      | Builds on both        |

*Needs source: Most cells are hypothesis or unknown.*

## Trade-offs

### LangChain

**Pros:**
- Simple and well-documented
- Wide ecosystem
- Easy to get started

**Cons:**
- Limited native state management
- Control flow is less explicit
- Less suited for complex, stateful pipelines

### LangGraph

**Pros:**
- Explicit state and control flow
- Built-in checkpointing and resumability
- Strong human-in-the-loop support

**Cons:**
- Higher complexity
- More boilerplate
- Harder to learn initially

### Deep Agents

**Pros:**
- Structured multi-agent orchestration
- Subagent delegation patterns

**Cons:**
- Less documented (Needs source)
- Higher abstraction may obscure internals
- Smaller ecosystem (Needs source)

## Example Use Cases

- **LangChain**: RAG pipeline, single-agent with tools, document summarization
- **LangGraph**: Multi-step research agent with resumable state, customer support bot with human escalation
- **Deep Agents**: Complex multi-agent task decomposition with specialized subagents

## Experiments

*None yet. See `docs/wiki/experiments/` for planned comparisons.*

## Decision Implications

- For this study: start with LangGraph internals as the primary focus, as it has the richest internal architecture to trace.
- LangChain is needed as foundation.
- Deep Agents needs source verification before making strong claims.

## Open Questions

- Can checkpoints from LangGraph be used by a Deep Agents runtime?
- How do the three frameworks compare on parallel tool calls?
- Which framework has the best test coverage for multi-agent scenarios?

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[StateGraph]]
- [[Checkpointing]]
- [[Subagents]]

## Sources

*None yet.*
