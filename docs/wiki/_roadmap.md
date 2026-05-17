# Roadmap

## Current Goal

Understand LangChain, LangGraph, and Deep Agents deeply enough to:

1. Explain their architecture
2. Compare their trade-offs
3. Trace public APIs into internal implementation
4. Run meaningful experiments
5. Understand tests
6. Reproduce issues
7. Identify small PR opportunities
8. Submit high-quality upstream contributions

## Phase 1 — Architecture Overview (current)

- [ ] Read and understand LangChain core abstractions
- [ ] Read and understand LangGraph core abstractions
- [ ] Read and understand Deep Agents core abstractions
- [ ] Fill in framework pages with verified summaries
- [ ] Draft comparison page with initial trade-offs

## Phase 2 — Internal Tracing

- [ ] Trace LangChain `create_agent` call path from public API to runtime
- [ ] Trace LangGraph `StateGraph.compile()` and `.invoke()` internals
- [ ] Trace Deep Agents `create_deep_agent` call path
- [ ] Fill in flow pages with verified file paths and call paths

## Phase 3 — Concepts Deep Dive

- [ ] Checkpointing: how it works in LangGraph vs LangChain
- [ ] Tool Calling: how tools are registered, resolved, and invoked
- [ ] Memory: short-term vs long-term, framework differences
- [ ] Subagents: orchestration patterns
- [ ] Context Engineering: how context is built and managed

## Phase 4 — Experiments

- [ ] Run same research agent task in LangChain, LangGraph, and Deep Agents
- [ ] Compare behavior, outputs, and internals
- [ ] Document in experiment reports

## Phase 5 — PR Preparation

- [ ] Identify at least one small PR candidate per framework
- [ ] Create minimal reproductions
- [ ] Write PR candidate pages with evidence

## Next Study Area

- LangGraph checkpointing internals
