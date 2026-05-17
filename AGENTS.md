# AGENTS.md

This repository is an LLM-maintained learning and contribution wiki for studying AI agent frameworks deeply enough to understand internals, trace architecture, run experiments, and eventually make high-quality PRs.

Primary focus areas:
- LangChain
- LangGraph
- Deep Agents
- AI agent architecture
- Tool calling
- State management
- Checkpointing
- Memory
- Context engineering
- Subagents
- Evaluation
- Open-source contribution workflows

The purpose of this repository is not to collect random notes.  
The purpose is to build a durable knowledge base that connects:
- official documentation
- source code
- examples
- experiments
- failures
- design decisions
- issues
- tests
- PR candidates

## Intended AI assistants

This repository may be edited or inspected by:
- Codex
- Claude Code
- GitHub Copilot
- other coding or writing agents

All agents must follow the rules in this file.

---

# Core Philosophy

Treat this repository as a learning-oriented LLM Wiki.

The wiki should help answer questions like:
- How does this framework work internally?
- Which public API maps to which internal implementation?
- Which files are involved in a behavior?
- Which tests define the expected behavior?
- What did I already learn or try?
- What failed?
- What is still unclear?
- What could become a good PR?

Do not optimize for producing many documents.  
Optimize for producing accurate, source-grounded, reusable knowledge.

---

# Repository Structure

```text
.
├── AGENTS.md
├── README.md
├── docs/
│   ├── raw/
│   ├── raw_manifest.yml
│   ├── source_summaries/
│   └── wiki/
│       ├── _index.md
│       ├── _roadmap.md
│       ├── _open_questions.md
│       ├── frameworks/
│       ├── concepts/
│       ├── comparisons/
│       ├── codebase/
│       ├── flows/
│       ├── tests/
│       ├── experiments/
│       ├── failures/
│       ├── decisions/
│       ├── issues/
│       └── prs/
├── examples/
├── reproductions/
├── evals/
└── scripts/
```

If the actual repository differs from this structure, preserve the existing structure and adapt the same principles.

---

# Folder Responsibilities

## docs/raw/

Raw source material.

Examples:
- official documentation snapshots
- copied excerpts from docs
- issue notes
- PR discussion notes
- experiment logs
- local code reading notes
- benchmark outputs
- model traces
- reproduction logs

Rules:
- Raw files are evidence, not polished knowledge.
- Do not rewrite raw files unless explicitly asked.
- Prefer appending or adding new raw files over modifying existing ones.
- Do not store secrets, API keys, tokens, private credentials, or sensitive personal data.
- Do not blindly scrape large websites or entire documentation trees.
- Collect raw materials only when they are relevant to a concrete study topic, experiment, bug, issue, or PR candidate.

## docs/raw_manifest.yml

Source registry.

Every meaningful raw source should be listed here.

Use this file to track:
- source ID
- title
- type
- URL
- repository
- commit SHA if applicable
- local raw path
- retrieval date
- license / sharing notes if relevant
- whether the source is public, private, generated, or local-only

If a source influenced a wiki page, the wiki page should reference the source ID.

## docs/source_summaries/

One source summary per important source.

Use this for:
- official docs summary
- issue summary
- PR discussion summary
- source file summary
- paper/article summary

A source summary should be factual and close to the source.
It should not over-synthesize across many sources.

## docs/wiki/

The curated knowledge base.

This is the main LLM Wiki.

The wiki should contain:
- framework pages
- concept pages
- comparison pages
- architecture maps
- execution flows
- test maps
- experiment reports
- failure cases
- decision records
- issue triage
- PR plans

Wiki pages should be concise, structured, and link-rich.

## examples/

Runnable learning examples.

Examples should demonstrate one concept at a time where possible.

## reproductions/

Minimal reproductions for bugs, confusing behavior, or PR candidates.

A reproduction should be small, runnable, and documented.

## evals/

Evaluation cases and results.

Use this for comparing framework behavior, agent quality, regression tests, and repeated experiments.

## scripts/

Automation scripts.

Examples:
- fetch selected raw sources
- verify raw source hashes
- generate source summaries
- scan broken wiki links
- build an index
- find stale pages

---

# Raw Source Collection Policy

Do not collect raw sources blindly.

**Bad:**
- Download all LangChain docs.
- Download all LangGraph docs.
- Download all Deep Agents docs.
- Scrape everything just in case.

**Good:**
- I am studying LangGraph checkpointing today.
- Collect the official checkpointing docs, relevant source files, relevant tests, and one or two related issues.

Raw collection should be triggered by one of these:
1. A concrete study topic
2. A concrete experiment
3. A confusing behavior
4. A source-code reading session
5. A bug reproduction
6. A potential PR
7. A decision that needs evidence

Before adding raw material, ask:
- Why is this source needed?
- Which wiki page will use it?
- Is it public or private?
- Is it small enough to store in Git?
- Can it be re-fetched instead of stored?
- Does it have a stable URL or commit SHA?

---

# Source Manifest Format

Use `docs/raw_manifest.yml`.

Recommended format:

```yaml
sources:
  - id: langgraph-docs-checkpointing-2026-05-18
    title: LangGraph checkpointing documentation
    type: official_docs
    framework: LangGraph
    url: "https://..."
    local_path: "docs/raw/langgraph/checkpointing.md"
    retrieved_at: "2026-05-18"
    status: public
    used_by:
      - "docs/wiki/concepts/Checkpointing.md"
      - "docs/wiki/frameworks/LangGraph.md"
    notes: "Official documentation snapshot used for checkpointing study."

  - id: deepagents-source-create-deep-agent-2026-05-18
    title: Deep Agents create_deep_agent source reading
    type: source_code
    framework: Deep Agents
    repo: "https://github.com/langchain-ai/deepagents"
    commit: "UNKNOWN"
    local_path: "docs/raw/deepagents/create_deep_agent_source_notes.md"
    retrieved_at: "2026-05-18"
    status: public
    used_by:
      - "docs/wiki/flows/Deep Agents create_deep_agent flow.md"
    notes: "Update commit SHA when known."
```

Rules:
- Every source must have a stable `id`.
- Prefer lowercase kebab-case IDs.
- Include `retrieved_at`.
- Include `url` or `repo` when applicable.
- Include `commit` when referencing source code.
- Include `local_path` when a local raw file exists.
- Include `used_by` when a wiki page depends on the source.
- Use `UNKNOWN` rather than inventing missing metadata.

---

# Citation and Evidence Rules

All non-trivial factual claims in wiki pages should be traceable.

For wiki pages, use a Sources section:

```markdown
## Sources
- `langgraph-docs-checkpointing-2026-05-18`
- `langgraph-source-checkpoint-saver-2026-05-18`
```

When discussing source code, include file paths and, when possible, commit SHA:

```markdown
## Source Code References
- Repo: langgraph
- Commit: UNKNOWN
- Files:
  - `libs/langgraph/...`
  - `libs/checkpoint/...`
```

Do not pretend that a source was checked if it was not checked.

Use these labels:
- **Verified**
- **Partially verified**
- **Hypothesis**
- **Unverified**
- **Needs source**
- **Outdated**

When uncertain, say so explicitly.

---

# Wiki Page Standards

Every major wiki page should follow this structure unless there is a good reason not to.

```markdown
# Page Title

## Summary
Brief explanation.

## Why It Matters
Why this topic matters for AI agent development or contribution.

## Key Concepts
- [[Concept A]]
- [[Concept B]]

## Details
Main content.

## Source Code References
- TBD if unknown.

## Tests
- TBD if unknown.

## Related Pages
- [[Related Page]]

## Open Questions
- Question 1
- Question 2

## Sources
- `source-id`
```

Do not create long, unfocused pages.  
If a page becomes too large, split it into concept, flow, test, and decision pages.

---

# Wikilink Rules

Use Obsidian-style wikilinks for important reusable concepts:

```
[[LangChain]]
[[LangGraph]]
[[Deep Agents]]
[[Tool Calling]]
[[Checkpointing]]
[[StateGraph]]
[[Subagents]]
[[Context Engineering]]
```

Good links explain the relationship:

> [[Planner]] uses [[Tool Registry]] to select only available tools.

Bad links are just keyword dumps:

> [[Planner]] [[Tool]] [[State]] [[Agent]]

Use links to make knowledge navigable, not decorative.

---

# Page Types

## Framework Page

Example: `docs/wiki/frameworks/LangGraph.md`

Should include:
- summary
- when to use
- core abstractions
- public APIs
- internal implementation map
- related tests
- related examples
- open questions
- sources

## Concept Page

Example: `docs/wiki/concepts/Checkpointing.md`

Should include:
- definition
- why it matters
- where it appears
- framework-specific behavior
- implementation notes
- tests
- related pages
- sources

## Comparison Page

Example: `docs/wiki/comparisons/LangChain vs LangGraph vs Deep Agents.md`

Should include:
- short decision rule
- comparison table
- trade-offs
- example use cases
- experiments
- decision implications
- sources

## Code Map

Example: `docs/wiki/codebase/LangGraph Code Map.md`

Should include:
- repo purpose
- major packages/directories
- important entry points
- source files to read
- tests to read
- unclear areas
- sources

## Execution Flow

Example: `docs/wiki/flows/Deep Agents create_deep_agent flow.md`

Should include:
- entry point
- call path
- state/message flow
- files read
- tests found
- diagrams if useful
- open questions
- sources

## Experiment Report

Example: `docs/wiki/experiments/2026-05-18 same research agent in three frameworks.md`

Should include:
- goal
- setup
- code links
- expected behavior
- actual behavior
- observations
- takeaways
- related concepts
- sources

## Failure Case

Example: `docs/wiki/failures/LangGraph checkpoint resume confusion.md`

Should include:
- problem
- expected behavior
- actual behavior
- reproduction
- suspected cause
- confirmed cause if known
- related concepts
- next actions
- status
- sources

## Decision Record

Example: `docs/wiki/decisions/Use LangGraph for core orchestration.md`

Should include:
- decision
- context
- options considered
- trade-offs
- reason
- consequences
- revisit criteria
- sources

## PR Candidate

Example: `docs/wiki/prs/Deep Agents filesystem docs PR candidate.md`

Should include:
- problem
- source evidence
- reproduction if applicable
- suspected root cause
- proposed change
- test plan
- risk
- status

---

# Learning Workflow

When studying a topic:

1. Identify the study question.
2. Collect only relevant sources.
3. Add or update `docs/raw_manifest.yml`.
4. Create source summaries for important sources.
5. Update or create wiki pages.
6. Add wikilinks to related concepts.
7. Add open questions.
8. If code was studied, add source file paths.
9. If behavior was tested, add experiment or reproduction notes.
10. Update `_index.md` when adding major pages.

Example study question:

> How does LangGraph checkpointing work internally?

Expected outputs:
- `docs/source_summaries/langgraph-checkpointing.md`
- `docs/wiki/concepts/Checkpointing.md`
- `docs/wiki/flows/LangGraph checkpointing flow.md`
- `docs/wiki/frameworks/LangGraph.md`
- `docs/wiki/_open_questions.md`

---

# Code Reading Workflow

When reading source code:

1. Start from a public API or observed behavior.
2. Trace definitions using the editor.
3. Record entry points.
4. Record files read.
5. Record key classes/functions.
6. Find related tests.
7. Note what is verified vs still unclear.
8. Update the relevant flow or code map page.

Never claim to understand an internal flow unless source files or tests were inspected.

Use this format:

```markdown
## Files Read
- `path/to/file.py`
  - Purpose:
  - Important functions/classes:
  - Notes:

## Call Path
1. `public_api()`
2. `internal_function()`
3. `runtime_step()`

## Verified
- ...

## Still Unclear
- ...
```

---

# Experiment Workflow

When running experiments:

1. Create a small example or reproduction.
2. Write down the expected behavior.
3. Run the code.
4. Save the result.
5. Summarize observations in `docs/wiki/experiments/`.
6. Link related concepts and framework pages.
7. If the result suggests a bug, create or update a failure case.
8. If the issue may be upstream, add a PR candidate.

Do not store huge raw logs in Git.  
Summarize them and store only minimal reproductions.

---

# PR Preparation Workflow

The goal is to eventually make small, high-quality PRs.

**Good first PR candidates:**
- docs mismatch
- unclear example
- missing edge case test
- small bug with clear reproduction
- better error message
- type hint or docstring improvement
- regression test for an issue

**Avoid early PRs that involve:**
- large refactors
- new core abstractions
- public API changes
- new dependencies
- broad generated documentation
- unverified behavior changes

Before drafting a PR:

1. Search existing issues and PRs.
2. Confirm the behavior.
3. Create a minimal reproduction.
4. Find related tests.
5. Add or update a failing test when behavior changes.
6. Make the smallest reasonable fix.
7. Run targeted tests.
8. Update docs if needed.
9. Write a clear PR note.

PR note structure:

```markdown
## Problem
## Root Cause
## Fix
## Tests
## Risk
## Related Issue
```

---

# AI Assistant Behavior Rules

When acting as an AI assistant in this repo:

**Do:**
- Be source-grounded.
- Prefer official docs, source code, tests, issues, and PRs.
- Use explicit uncertainty.
- Keep pages structured.
- Add wikilinks for important concepts.
- Update related pages when a new concept affects them.
- Keep raw and wiki separate.
- Preserve user-written notes unless asked to rewrite.
- Prefer small, reviewable changes.
- Ask for clarification only when the task is truly ambiguous and cannot be reasonably attempted.

**Do Not:**
- Do not invent sources.
- Do not claim source code was inspected if it was not.
- Do not bulk scrape documentation without a study purpose.
- Do not silently delete notes.
- Do not overwrite raw files unnecessarily.
- Do not make large refactors unless explicitly asked.
- Do not add secrets or credentials.
- Do not submit or prepare large PRs from unreviewed generated content.
- Do not treat Obsidian graph view as a graph database.
- Do not treat vector DB search as ontology.
- Do not confuse source summaries with synthesized wiki pages.

---

# Obsidian Usage

Obsidian is used as a Markdown knowledge browser.

Obsidian provides:
- note browsing
- backlinks
- graph view
- local search
- properties
- optional Bases views

Obsidian does not automatically create a real graph database or ontology.

Use Obsidian links to make knowledge navigable:

> [[LangGraph]] provides runtime capabilities such as [[Checkpointing]] and [[Human in the Loop]].

For AI assistants, the important part is not Obsidian's UI.  
The important part is the Markdown structure, links, metadata, and source references.

---

# Ontology-lite Rules

This wiki may use lightweight ontology patterns.

Use explicit page types:

```yaml
---
type: concept
framework:
  - LangGraph
status: draft
confidence: medium
last_reviewed: 2026-05-18
sources:
  - langgraph-docs-checkpointing-2026-05-18
---
```

Useful `type` values:
- `framework`
- `concept`
- `comparison`
- `code_map`
- `flow`
- `experiment`
- `failure`
- `decision`
- `issue`
- `pr_candidate`
- `source_summary`

Useful `status` values:
- `draft`
- `in_review`
- `verified`
- `outdated`
- `needs_source`

Useful `confidence` values:
- `low`
- `medium`
- `high`

---

# Index Maintenance

Maintain:
- `docs/wiki/_index.md`
- `docs/wiki/_roadmap.md`
- `docs/wiki/_open_questions.md`

## _index.md

Should list major pages by category.

## _roadmap.md

Should track learning goals and next study areas.

## _open_questions.md

Should collect unresolved questions.

When adding a major page, update `_index.md`.  
When discovering an uncertainty, update `_open_questions.md`.

---

# Recommended Initial Pages

If missing, create these first:

```
docs/wiki/_index.md
docs/wiki/_roadmap.md
docs/wiki/_open_questions.md
docs/wiki/frameworks/LangChain.md
docs/wiki/frameworks/LangGraph.md
docs/wiki/frameworks/Deep Agents.md
docs/wiki/comparisons/LangChain vs LangGraph vs Deep Agents.md
docs/wiki/concepts/Tool Calling.md
docs/wiki/concepts/StateGraph.md
docs/wiki/concepts/Checkpointing.md
docs/wiki/concepts/Subagents.md
docs/wiki/concepts/Context Engineering.md
docs/wiki/concepts/Memory.md
docs/wiki/concepts/Evaluation.md
docs/wiki/codebase/LangChain Code Map.md
docs/wiki/codebase/LangGraph Code Map.md
docs/wiki/codebase/Deep Agents Code Map.md
docs/wiki/flows/LangChain create_agent flow.md
docs/wiki/flows/LangGraph StateGraph compile invoke flow.md
docs/wiki/flows/Deep Agents create_deep_agent flow.md
```

---

# Raw Sync and Git Policy

The recommended default is:

```
Git tracks:
- docs/wiki/
- docs/source_summaries/
- docs/raw_manifest.yml
- examples/
- reproductions/
- evals/
- scripts/

Git does not track by default:
- docs/raw/*
- large logs
- generated traces
- local caches
- vector indexes
- databases
- private notes
```

If a raw file is small, public, and important for reproducibility, it may be committed intentionally.  
If a raw file is large, private, copyrighted, generated, or easy to re-fetch, do not commit it.  
Record it in `docs/raw_manifest.yml` instead.

---

# Quality Bar

A good wiki update should make future work easier.

Before finishing a change, check:
- Did I add sources?
- Did I distinguish facts from interpretation?
- Did I link related pages?
- Did I update the index if needed?
- Did I record open questions?
- Did I avoid unnecessary raw collection?
- Did I avoid unverified claims?
- Did I keep the change small and reviewable?

---

# Current Learning Goal

The current goal is to understand LangChain, LangGraph, and Deep Agents deeply enough to:

1. explain their architecture,
2. compare their trade-offs,
3. trace public APIs into internal implementation,
4. run meaningful experiments,
5. understand tests,
6. reproduce issues,
7. identify small PR opportunities,
8. eventually submit high-quality upstream contributions.

Prefer depth, traceability, and correctness over speed.
