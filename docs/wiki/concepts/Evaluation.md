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

# Evaluation

## Summary

Evaluation is the process of measuring agent quality, correctness, and behavior. It includes offline benchmarks, online monitoring, and regression testing.

*Status: Draft stub. Needs source verification.*

## Why It Matters

Without evaluation, it is difficult to know whether agent improvements are real or illusory. Evaluation frameworks are also important for contributing upstream, as good PRs include or update tests.

## Key Concepts

- **Offline evaluation** — running test cases before deployment
- **Online evaluation** — monitoring production agent behavior
- **LLM-as-judge** — using an LLM to score agent outputs
- **Trajectory evaluation** — evaluating the sequence of agent steps, not just the final output
- **Regression tests** — ensuring new changes do not break existing behavior
- **LangSmith** — LangChain's tracing and evaluation platform

## Framework-Specific Behavior

### LangChain

- `langchain` has evaluation utilities in `langchain.evaluation`
- *Needs source.*

### LangGraph

- LangGraph apps can be traced via LangSmith
- *Needs source.*

### Deep Agents

- TBD
- *Needs source.*

## Open Questions

- What built-in evaluation utilities exist in each framework?
- How can LangSmith be used for trajectory evaluation?
- What test patterns are used in each framework's test suite?

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[LangChain Code Map]]
- [[LangGraph Code Map]]

## Sources

*None yet.*
