# LangChain / LangGraph / Deep Agents — LLM Wiki

A learning-oriented wiki for studying AI agent frameworks deeply enough to understand internals, trace architecture, run experiments, and eventually make high-quality upstream PRs.

## Primary Focus Areas

- LangChain, LangGraph, Deep Agents
- Tool calling, state management, checkpointing, memory
- Context engineering, subagents, evaluation
- Open-source contribution workflows

## Structure

```
docs/wiki/          # Curated knowledge base (main wiki)
docs/source_summaries/  # One summary per important source
docs/raw/           # Raw source material (git-ignored by default)
docs/raw_manifest.yml   # Source registry
examples/           # Runnable learning examples
reproductions/      # Minimal bug/behavior reproductions
evals/              # Evaluation cases and results
scripts/            # Automation scripts
```

## Getting Started

See [`AGENTS.md`](AGENTS.md) for the full guide — including how to add sources, write wiki pages, and prepare PRs.

See [`docs/wiki/_index.md`](docs/wiki/_index.md) for the wiki index.

See [`docs/wiki/_roadmap.md`](docs/wiki/_roadmap.md) for the current learning roadmap.

## Intended AI Assistants

This repository is designed to be read and edited by Codex, Claude Code, GitHub Copilot, and other coding/writing agents. All agents must follow the rules in `AGENTS.md`.