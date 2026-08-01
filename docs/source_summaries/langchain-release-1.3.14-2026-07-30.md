---
type: source_summary
framework:
  - LangChain
status: verified
confidence: high
updated_at: 2026-07-30
sources:
  - langchain-pypi-1-3-14-2026-07-30
  - langchain-source-1-3-14-2026-07-30
  - langchain-core-source-1-5-2-2026-07-30
---

# LangChain 1.3.14 release baseline

## Source identity

- Package: `langchain==1.3.14`
- Published: 2026-07-16
- Python requirement: `>=3.10,<4.0`
- LangChain tag commit: `185119f98e6286253a2326d7cf4f59592678023d`
- Resolved core dependency in this repository: `langchain-core==1.5.2`
- Core tag commit: `c1ab807b1f62ad04274c28f2b7d8c3141d8ba1f2`
- Resolved LangGraph dependency: `langgraph==1.2.10`

## Verified release delta

The repository previously used `langchain==1.3.1`. A tag-to-tag source comparison
against 1.3.14 found changes in the v1 agent package, including:

- `create_agent(..., transformers=...)` now accepts
  `Sequence[TransformerFactory] | None`.
- Compiled agents register `ToolCallTransformer`, `SubagentTransformer`,
  middleware-provided transformers, and call-site transformers.
- `AgentMiddleware` exposes a `transformers` factory sequence.
- `ProviderToolSearchMiddleware` was added for provider-native deferred tool
  loading. The tagged implementation supports Anthropic and OpenAI.
- `ToolErrorMiddleware` was added to opt in to converting selected tool
  execution exceptions into `ToolMessage(status="error")`.
- `InputAgentState`, `OutputAgentState`, and `TriggerClause` are exported from
  `langchain.agents.middleware`.
- `SummarizationMiddleware.keep` remains a tagged tuple such as
  `("messages", 10)`, not a bare integer.

## Compatibility check

All Python files in `examples/` and `reproductions/` compile under the resolved
environment. All examples in `examples/langchain_core/`,
`examples/langgraph_core/`, and `examples/deepagents_core/` were executed
successfully on 2026-07-30. The reproduction suite completed with
`8 passed, 4 xfailed`; the xfails preserve the known LangGraph issue #5225
behavior.

## Scope note

This summary records the release baseline and the changes relevant to this wiki.
It is not a complete upstream changelog.

## Sources

- `langchain-pypi-1-3-14-2026-07-30`
- `langchain-source-1-3-14-2026-07-30`
- `langchain-core-source-1-5-2-2026-07-30`
