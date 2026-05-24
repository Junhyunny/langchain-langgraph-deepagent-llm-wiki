---
type: code_map
framework: Deep Agents
status: partial
confidence: medium
last_reviewed: 2026-05-24
sources:
  - deepagents-source-graph-2026-05-19
  - deepagents-source-harness-profiles-2026-05-19
  - deepagents-docs-harness-2026-05-19
  - deepagents-venv-read-2026-05-24
---

# Deep Agents Code Map

## 요약

Deep Agents 저장소 구조 탐색 가이드.
`graph.py`, `harness_profiles.py` 두 파일 소스 및 harness 공식 문서 기반 확인. 나머지 middleware 파일들은 미수집.

---

## 저장소

- **저장소:** `https://github.com/langchain-ai/deepagents`
  Source: `deepagents-source-graph-2026-05-19`
- **Commit:** UNKNOWN (main branch, 2026-05-19 기준)

---

## 확인된 디렉터리 / 파일 구조

`.venv` 설치본 직접 읽기로 확인됨 (v0.6.3, 2026-05-24). Source: `deepagents-venv-read-2026-05-24`

```
deepagents/                             (pip install deepagents v0.6.3)
├── graph.py                            ← create_deep_agent 진입점 ✅ 소스 읽음
├── _excluded_middleware.py             ← excluded middleware 로직
├── _messages_reducer.py                ← _messages_delta_reducer 정의
├── _models.py                          ← resolve_model 정의
├── _subagent_transformer.py            ← SubagentTransformer 정의
├── _tools.py                           ← _apply_tool_description_overrides
├── _version.py                         ← __version__
├── _api/
│   └── deprecation.py                 ← deprecated, warn_deprecated
├── backends/
│   ├── __init__.py                    ← StateBackend export
│   ├── composite.py                   ← CompositeBackend
│   ├── context_hub.py
│   ├── filesystem.py                  ← FilesystemBackend
│   ├── langsmith.py                   ← LangSmith 연동
│   ├── local_shell.py
│   ├── protocol.py                    ← BackendFactory, BackendProtocol, SandboxBackendProtocol
│   ├── sandbox.py                     ← SandboxBackend
│   ├── state.py                       ← StateBackend 구현
│   ├── store.py                       ← StoreBackend
│   └── utils.py
├── middleware/
│   ├── _message_eviction.py
│   ├── _overflow_clip.py
│   ├── _tool_exclusion.py             ← _ToolExclusionMiddleware
│   ├── _utils.py
│   ├── async_subagents.py             ← AsyncSubAgent, AsyncSubAgentMiddleware
│   ├── filesystem.py                  ← FilesystemMiddleware, FilesystemPermission
│   ├── memory.py                      ← MemoryMiddleware
│   ├── patch_tool_calls.py            ← PatchToolCallsMiddleware
│   ├── permissions.py
│   ├── skills.py                      ← SkillsMiddleware
│   ├── subagents.py                   ← SubAgent, CompiledSubAgent, SubAgentMiddleware
│   └── summarization.py               ← create_summarization_middleware
└── profiles/
    ├── _builtin_profiles.py           ← 내장 harness profiles
    ├── _keys.py
    ├── harness/
    │   ├── _anthropic_haiku_4_5.py
    │   ├── _anthropic_opus_4_7.py
    │   ├── _anthropic_sonnet_4_6.py   ← Claude Sonnet 4.6 profile
    │   ├── _openai_codex.py
    │   └── harness_profiles.py        ← HarnessProfile, register_harness_profile ✅ 소스 읽음
    └── provider/
        ├── _openai.py
        ├── _openrouter.py
        └── provider_profiles.py
```

Source: `deepagents-source-graph-2026-05-19` (import 분석) + `deepagents-venv-read-2026-05-24` (직접 확인)

---

## 핵심 진입점

| 함수/클래스 | 파일 | 상태 |
|------------|------|------|
| `create_deep_agent` | `deepagents/graph.py` | ✅ 소스 읽음 |
| `_DeepAgentState` | `deepagents/graph.py` | ✅ 소스 읽음 |
| `BASE_AGENT_PROMPT` | `deepagents/graph.py` | ✅ 소스 읽음 |
| `FilesystemMiddleware` | `deepagents/middleware/filesystem.py` | ❌ 미읽음 |
| `SubAgentMiddleware` | `deepagents/middleware/subagents.py` | ❌ 미읽음 |
| `SubagentTransformer` | `deepagents/_subagent_transformer.py` | ❌ 미읽음 |
| `HarnessProfile` | `deepagents/profiles/harness/harness_profiles.py` | ✅ 소스 읽음 |
| `HarnessProfileConfig` | `deepagents/profiles/harness/harness_profiles.py` | ✅ 소스 읽음 |
| `GeneralPurposeSubagentProfile` | `deepagents/profiles/harness/harness_profiles.py` | ✅ 소스 읽음 |
| `register_harness_profile` | `deepagents/profiles/harness/harness_profiles.py` | ✅ 소스 읽음 |
| `StateBackend` | `deepagents/backends/state.py` | ❌ 미읽음 |
| `SandboxBackendProtocol` | `deepagents/backends/protocol.py` | ❌ 미읽음 |

---

## 다음 읽어야 할 파일 (우선순위순)

1. `deepagents/middleware/filesystem.py` — FilesystemMiddleware의 tool 주입 방식, 권한 처리
2. `deepagents/middleware/subagents.py` — SubAgent/SubAgentMiddleware, task tool 구현
3. `deepagents/_subagent_transformer.py` — SubagentTransformer scope 활용 방식
4. `langchain/agents/__init__.py` + `create_agent` — 실제 LangGraph graph 조립 위치
5. `deepagents/middleware/patch_tool_calls.py` — PatchToolCallsMiddleware 동작 확인

---

## 관련 페이지

- [[Deep Agents]]
- [[Deep Agents create_deep_agent flow]]
- [[Subagents]]

---

## 소스

- `deepagents-source-graph-2026-05-19`
- `deepagents-source-harness-profiles-2026-05-19`
- `deepagents-venv-read-2026-05-24`
