---
type: concept
framework:
  - Deep Agents
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - langchain-docs-products-2026-05-23
  - deepagents-source-harness-profiles-2026-05-19
---

# Agent Harness

## Summary

Agent Harness는 AI agent 개발을 위한 세 가지 제품 범주 중 하나다. **Opinionated, batteries-included** 프레임워크로, 미리 정의된 도구·프롬프트·서브에이전트를 제공한다.

Source: `langchain-docs-products-2026-05-23`

## Why It Matters

- [[LangChain]](Framework)과 [[LangGraph]](Runtime)만으로는 복잡하고 비결정적인 장기 작업을 위해 많은 boilerplate가 필요하다.
- Harness는 그 위에 context engineering, planning, file system, token management를 **미리 조립**해 제공한다.
- "Harness를 쓴다" = Runtime의 낮은 수준 제어를 포기하는 대신 즉시 사용 가능한 에이전트 역량을 얻는 트레이드오프다.

## Key Concepts

- [[Deep Agents]] — 대표적인 Harness 구현체
- [[LangGraph]] — Harness가 올라가는 Runtime 레이어
- [[Subagents]] — Harness의 핵심 기능 중 하나
- [[Context Engineering]] — token management, 히스토리 요약 등
- [[Memory]] — long-term memory 지원

## Harness의 특성 (Verified)

| 기능 | 설명 |
|------|------|
| **Planning capabilities** | to-do list 기반 멀티 태스크 추적 |
| **Task delegation** | subagents로 작업을 위임하고 컨텍스트를 격리 |
| **File system** | pluggable storage backends를 통한 파일 읽기/쓰기 |
| **Token management** | 대화 히스토리 요약 + 대형 tool result eviction |

Source: `langchain-docs-products-2026-05-23`

## 현존하는 Harness 구현체 (Verified)

| 이름 | 제공사 |
|------|--------|
| Deep Agents SDK | LangChain (langchain-ai) |
| Claude Agent SDK | Anthropic |
| Manus | Manus |

Source: `langchain-docs-products-2026-05-23`

## Deep Agents SDK 구체 특성

- [[LangGraph]] 위에 빌드됨 (Runtime의 durable execution 상속)
- LangGraph의 `checkpointer` + `_DeepAgentState` (`DeltaChannel`) 활용
- `create_deep_agent()` 함수로 harness 조립
- middleware 기반 구성: planning, filesystem, permissions, subagents, context, code execution, HITL, profiles

*Source: `deepagents-source-graph-2026-05-19`, `deepagents-docs-harness-2026-05-19`*

## Framework vs Runtime vs Harness 위치

```
Harness (Deep Agents SDK)
    └── Runtime (LangGraph)
Framework (LangChain)
    └── Runtime (LangGraph)
```

- Harness와 Framework 모두 Runtime 위에 올라간다.
- 단, Harness는 Runtime의 낮은 수준 API를 직접 노출하지 않고 opinionated 추상화로 감싼다.

## Related Pages

- [[Deep Agents]]
- [[LangChain]]
- [[LangGraph]]
- [[LangChain vs LangGraph vs Deep Agents]]
- [[Subagents]]
- [[Context Engineering]]
- [[Memory]]

## HarnessProfile 상세 (소스코드 기준)

*Source: `deepagents-source-harness-profiles-2026-05-19`*

### HarnessProfile — 전체 필드 (7개)

| 필드 | 타입 | 기본값 | 역할 |
|------|------|--------|------|
| `base_system_prompt` | `str \| None` | `None` | CUSTOM 슬롯 — BASE_AGENT_PROMPT 전체 교체 |
| `system_prompt_suffix` | `str \| None` | `None` | SUFFIX 슬롯 — 조립 프롬프트 끝에 항상 추가 |
| `tool_description_overrides` | `Mapping[str, str]` | `{}` | tool 이름 → 설명 교체 (생성 후 immutable) |
| `excluded_tools` | `frozenset[str]` | `frozenset()` | 이 profile 적용 시 숨길 tool 이름 |
| `excluded_middleware` | `frozenset[type \| str]` | `frozenset()` | 제거할 middleware — class 또는 `.name` 문자열 |
| `extra_middleware` | `Sequence \| Callable[[], Sequence]` | `()` | 모든 stack에 추가할 middleware (factory 지원) |
| `general_purpose_subagent` | `GeneralPurposeSubagentProfile \| None` | `None` | auto-added GP subagent 설정 재정의 |

### GeneralPurposeSubagentProfile — 전체 필드 (3개)

| 필드 | 타입 | 의미 |
|------|------|------|
| `enabled` | `bool \| None` | `None`=inherit/기본 on, `True`=강제 포함, `False`=비활성화 |
| `description` | `str \| None` | 기본 description 재정의 |
| `system_prompt` | `str \| None` | GP subagent 전용 prompt 재정의 (base_system_prompt보다 우선) |

### merge semantics (_merge_profiles)

| 필드 | merge 방식 |
|------|-----------|
| `base_system_prompt` | override non-None이면 override 우선, 아니면 base |
| `system_prompt_suffix` | 동일 |
| `tool_description_overrides` | dict union, 같은 key는 override 우선 |
| `excluded_tools` | set union (base ∪ override) |
| `excluded_middleware` | set union (base ∪ override) |
| `extra_middleware` | class 기준 merge — override가 같은 class 교체, 새 class는 뒤에 추가 |
| `general_purpose_subagent` | field-wise: 각 필드 non-None이면 override 우선 |

### profile lookup 우선순위 (_get_harness_profile)

```
1. exact match (e.g. "openai:gpt-5.4")
2. provider prefix (e.g. "openai")
3. exact + provider 둘 다 → merge(provider=base, exact=override)
4. 없으면 → None (빈 HarnessProfile() 사용)
```

### 제약 사항

- `FilesystemMiddleware`, `SubAgentMiddleware`는 `excluded_middleware`로 제외 불가 → 생성 시점 `ValueError`
- `task` tool 제거: `GeneralPurposeSubagentProfile(enabled=False)` + sync subagents 없음
- `excluded_middleware` string grammar: 비어있음 / `:` 포함 / `_` 시작 → `ValueError`
- `task` tool description override 시 `{available_agents}` placeholder 필수 (없으면 모델이 subagent 목록 못 봄)
- `extra_middleware`는 `CompiledSubAgent`(pre-built), `AsyncSubAgent`(remote)에는 **미적용**

### HarnessProfileConfig — 파일 친화적 버전

- `HarnessProfile`과 동일하되 `extra_middleware` 없음 (런타임 전용)
- YAML/JSON 로딩 후 `register_harness_profile`에 직접 전달 가능

```python
import yaml
from deepagents import HarnessProfileConfig, register_harness_profile

with open("openai-gpt-5.4.yaml") as f:
    register_harness_profile(
        "openai:gpt-5.4",
        HarnessProfileConfig.from_dict(yaml.safe_load(f)),
    )
```

## Open Questions

- "pluggable storage backends"는 어떤 backend를 지원하는가? (S3, local, memory?)
- Harness 범주에서 Claude Agent SDK와 Deep Agents SDK의 설계 철학 차이는?
- Harness가 Runtime의 `interrupt` / checkpoint를 어떻게 추상화하는가?
- 미래에 새로운 Harness가 LangGraph 없이 다른 Runtime 위에 올라갈 수 있는가?
- 빌트인 profile(`_builtin_profiles`)에는 어떤 모델에 어떤 profile이 등록되어 있는가? — Source: `deepagents-source-harness-profiles-2026-05-19`
- `serialized_name: ClassVar[str]`을 가지는 공식 middleware는 어떤 것들이 있는가? — Source: `deepagents-source-harness-profiles-2026-05-19`

## Sources

- `langchain-docs-products-2026-05-23`
- `deepagents-source-graph-2026-05-19`
- `deepagents-docs-harness-2026-05-19`
- `deepagents-source-harness-profiles-2026-05-19`
