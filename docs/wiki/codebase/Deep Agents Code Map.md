---
type: code_map
framework: Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-19
sources:
  - deepagents-source-graph-2026-05-19
---

# Deep Agents Code Map

## 요약

Deep Agents 저장소 구조 탐색 가이드.
현재 `graph.py` 한 파일의 소스 기반으로 확인된 내용만 기록. 나머지는 추론 또는 미확인.

---

## 저장소

- **저장소:** `https://github.com/langchain-ai/deepagents`
  Source: `deepagents-source-graph-2026-05-19`
- **Commit:** UNKNOWN (main branch, 2026-05-19 기준)

---

## 확인된 디렉터리 / 파일 구조

```
langchain-ai/deepagents/
└── libs/
    └── deepagents/
        └── deepagents/
            ├── graph.py                        ← create_deep_agent 진입점 ✅ 수집됨
            ├── _messages_reducer.py            ← _messages_delta_reducer 정의 (미수집)
            ├── _models.py                      ← resolve_model 정의 (미수집)
            ├── _subagent_transformer.py        ← SubagentTransformer 정의 (미수집)
            ├── _tools.py                       ← _apply_tool_description_overrides (미수집)
            ├── _version.py                     ← __version__ (미수집)
            ├── _excluded_middleware.py         ← excluded middleware 로직 (미수집)
            ├── _api/
            │   └── deprecation.py             ← deprecated, warn_deprecated (미수집)
            ├── backends/
            │   ├── __init__.py               ← StateBackend export (미수집)
            │   └── protocol.py               ← BackendFactory, BackendProtocol (미수집)
            ├── middleware/
            │   ├── _tool_exclusion.py         ← _ToolExclusionMiddleware (미수집)
            │   ├── async_subagents.py         ← AsyncSubAgent, AsyncSubAgentMiddleware (미수집)
            │   ├── filesystem.py              ← FilesystemMiddleware, FilesystemPermission (미수집)
            │   ├── memory.py                  ← MemoryMiddleware (미수집)
            │   ├── patch_tool_calls.py        ← PatchToolCallsMiddleware (미수집)
            │   ├── skills.py                  ← SkillsMiddleware (미수집)
            │   ├── subagents.py               ← SubAgent, CompiledSubAgent, SubAgentMiddleware (미수집)
            │   └── summarization.py           ← create_summarization_middleware (미수집)
            └── profiles/
                └── harness/
                    └── harness_profiles.py    ← HarnessProfile, GeneralPurposeSubagentProfile (미수집)
```

Source: `deepagents-source-graph-2026-05-19` (import 분석 기반)

---

## 핵심 진입점

| 함수/클래스 | 파일 | 상태 |
|------------|------|------|
| `create_deep_agent` | `deepagents/graph.py` | ✅ 소스 수집됨 |
| `_DeepAgentState` | `deepagents/graph.py` | ✅ 소스 수집됨 |
| `BASE_AGENT_PROMPT` | `deepagents/graph.py` | ✅ 소스 수집됨 |
| `FilesystemMiddleware` | `deepagents/middleware/filesystem.py` | ❌ 미수집 |
| `SubAgentMiddleware` | `deepagents/middleware/subagents.py` | ❌ 미수집 |
| `SubagentTransformer` | `deepagents/_subagent_transformer.py` | ❌ 미수집 |
| `HarnessProfile` | `deepagents/profiles/harness/harness_profiles.py` | ❌ 미수집 |
| `StateBackend` | `deepagents/backends/` | ❌ 미수집 |

---

## 다음 읽어야 할 파일 (우선순위순)

1. `deepagents/middleware/filesystem.py` — FilesystemMiddleware의 tool 주입 방식, 권한 처리
2. `deepagents/middleware/subagents.py` — SubAgent/SubAgentMiddleware, task tool 구현
3. `deepagents/profiles/harness/harness_profiles.py` — HarnessProfile 모델 매핑
4. `deepagents/_subagent_transformer.py` — SubagentTransformer scope 활용 방식
5. `langchain/agents/__init__.py` + `create_agent` — 실제 LangGraph graph 조립 위치

---

## 관련 페이지

- [[Deep Agents]]
- [[Deep Agents create_deep_agent flow]]
- [[Subagents]]

---

## 소스

- `deepagents-source-graph-2026-05-19`
