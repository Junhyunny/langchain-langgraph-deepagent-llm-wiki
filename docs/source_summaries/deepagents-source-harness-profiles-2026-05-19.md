---
type: source_summary
source_id: deepagents-source-harness-profiles-2026-05-19
framework: Deep Agents
retrieved_at: "2026-05-19"
status: complete
confidence: high
---

# Source Summary: Deep Agents — harness_profiles.py

## Source Info
- **Source ID:** `deepagents-source-harness-profiles-2026-05-19`
- **Type:** source_code
- **URL:** https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/deepagents/profiles/harness/harness_profiles.py
- **Retrieved At:** 2026-05-19 (fetched live 2026-05-23)
- **Version / Commit:** main branch (no pinned SHA)

---

## Key Facts

### HarnessProfile (frozen dataclass) — 7개 필드

| 필드 | 타입 | 기본값 | 역할 |
|------|------|--------|------|
| `base_system_prompt` | `str \| None` | `None` | CUSTOM 슬롯 — BASE_AGENT_PROMPT 전체 교체 |
| `system_prompt_suffix` | `str \| None` | `None` | SUFFIX 슬롯 — 조립된 프롬프트 끝에 항상 추가 |
| `tool_description_overrides` | `Mapping[str, str]` | `{}` | tool 이름 → 설명 교체; `__post_init__`에서 MappingProxyType으로 freeze |
| `excluded_tools` | `frozenset[str]` | `frozenset()` | 이 profile이 적용될 때 숨길 tool 이름 목록 |
| `excluded_middleware` | `frozenset[type[AgentMiddleware] \| str]` | `frozenset()` | 제거할 middleware — class 또는 AgentMiddleware.name 문자열 |
| `extra_middleware` | `Sequence[AgentMiddleware] \| Callable[[], Sequence[AgentMiddleware]]` | `()` | 모든 stack에 추가할 middleware. factory 지원 |
| `general_purpose_subagent` | `GeneralPurposeSubagentProfile \| None` | `None` | auto-added GP 서브에이전트 설정 재정의 |

- `extra_middleware`는 main agent, auto-added GP subagent, declarative sync subagents에 적용됨
- `extra_middleware`는 `CompiledSubAgent`(pre-built)와 `AsyncSubAgent`(remote)에는 **적용되지 않음**
- `tool_description_overrides`: 프로필 생성 후 수정 불가(MappingProxyType). 레지스트리는 별도 방어적 복사본 보관

### GeneralPurposeSubagentProfile (frozen dataclass) — 3개 필드

| 필드 | 타입 | 기본값 | 의미 |
|------|------|--------|------|
| `enabled` | `bool \| None` | `None` | None=inherit/기본 on, True=강제 포함, False=비활성화 |
| `description` | `str \| None` | `None` | 기본 description 재정의 |
| `system_prompt` | `str \| None` | `None` | GP subagent 전용 system prompt 재정의 |

- `system_prompt` 설정 시 `HarnessProfile.base_system_prompt`보다 **우선** (GP subagent 한정)
- `enabled=False` + sync subagents 없음 → `task` tool 자동 제거

### HarnessProfileConfig — 파일 친화적 선언형 버전

- `HarnessProfile`과 동일한 필드를 가지되 `extra_middleware` **없음** (런타임 전용)
- `excluded_middleware`는 string name만 허용 (class 불가)
- `register_harness_profile`에 직접 전달 가능 → 자동으로 `HarnessProfile`로 변환
- `to_dict()` / `from_dict()`: YAML/JSON 라운드트립 지원
- `HarnessProfile`에서 변환 시 `extra_middleware`가 있으면 `ValueError`

### register_harness_profile — 등록 및 merge

```python
register_harness_profile(key: str, profile: HarnessProfile | HarnessProfileConfig) -> None
```

- `key` 형식: `"provider"` (provider-wide) 또는 `"provider:model"` (model-level)
- **Additive merge**: 기존 등록이 있으면 새 profile을 위에 겹침 (교체 아님)
- 등록 전 `_ensure_harness_profiles_loaded()` 호출 (lazy bootstrap)

### _merge_profiles — per-field merge semantics

| 필드 | merge 방식 |
|------|-----------|
| `base_system_prompt` | override 값이 non-None이면 override 우선, 아니면 base |
| `system_prompt_suffix` | 동일 |
| `tool_description_overrides` | dict union, 같은 key는 override 우선 |
| `excluded_tools` | set union (`base \| override`) |
| `excluded_middleware` | set union (`base \| override`) |
| `extra_middleware` | class 기준 merge — override가 base의 같은 class 교체, 새 class는 뒤에 추가 |
| `general_purpose_subagent` | field-wise: enabled/description/system_prompt 각각 (override non-None 우선) |

### _get_harness_profile — lookup 우선순위

```
1. exact match(spec)
2. provider prefix(spec의 ':' 앞)
3. exact + provider 둘 다 있으면 → merge(provider=base, exact=override)
4. 없으면 → None
```

- 빈 문자열, `:` 2개 이상, `:` 앞뒤 중 하나가 빈 문자열 → None 반환
- provider만 매칭 시 debug log 발생

### _harness_profile_for_model — pre-built model 지원

- `spec` 제공 시: `_get_harness_profile(spec)` 사용
- `spec` 없음 (pre-built model): `provider:identifier` → `identifier` (`:` 포함 시) → `provider` 순서
- bare identifier는 레지스트리에 조회하지 않음 (provider key와 우발적 매칭 방지)
- 매칭 없음 → 빈 `HarnessProfile()` 반환
- 사용자 등록 profile이 있는데 매칭 안 되면 WARNING 로그

### 제약 및 유효성 검사

**Scaffolding 제외 불가:**
- `FilesystemMiddleware`, `SubAgentMiddleware`는 `excluded_middleware`로 제외 시 생성 시점에 `ValueError`
- `task` tool 제거 방법: `GeneralPurposeSubagentProfile(enabled=False)` + sync subagents 없음

**excluded_middleware string grammar (생성 시점 검사):**
- 비어있거나 공백만 있으면 `ValueError`
- `:` 포함 불가 (class-path 미지원)
- `_` 시작 불가 (private middleware)

**task tool description override 주의:**
- `{available_agents}` placeholder를 포함하지 않으면 모델이 subagent 목록을 볼 수 없음

---

## Important Terms

- [[Agent Harness]] — HarnessProfile이 적용되는 레이어
- [[Subagents]] — GeneralPurposeSubagentProfile이 제어하는 대상
- [[Context Engineering]] — base_system_prompt / system_prompt_suffix의 조립 위치

---

## Interpretation

- `HarnessProfile`은 model이 생성된 **이후** 런타임 동작을 tuning하는 객체다. model 생성 단계는 `ProviderProfile`이 담당한다.
- Additive merge 설계는 "기존 built-in profile에 사용자 설정을 겹쳐 쌓는" 방식을 의도한다. 완전히 초기화(override)하려면 동일 key에 재등록해도 기존 값이 남아 있으므로, 빈 profile 기반에서 새로 등록해야 한다.
- `extra_middleware` factory 지원은 stack마다 독립적인 middleware instance가 필요할 때 사용한다 (state를 가지는 middleware).
- `HarnessProfileConfig`는 YAML/JSON 기반 배포용, `HarnessProfile`은 코드 기반 런타임 설정용으로 역할이 분리되어 있다.

---

## Implications for My AI Agent Project

- 모델 별로 system prompt suffix를 추가하거나 특정 tool을 비활성화할 때는 `register_harness_profile`을 활용한다.
- YAML config 파일로 profile을 관리하려면 `HarnessProfileConfig.from_dict(yaml.safe_load(f))`를 사용한다.
- `task` tool을 완전히 제거하고 싶다면 `excluded_middleware`가 아닌 `GeneralPurposeSubagentProfile(enabled=False)` 경로를 써야 한다.
- `extra_middleware`에 상태를 가지는 middleware를 쓸 때는 factory 형태(`Callable[[], Sequence[AgentMiddleware]]`)로 전달해야 각 stack이 독립적인 instance를 가진다.

---

## Open Questions

- 빌트인 프로필(`_builtin_profiles`)에는 어떤 모델에 어떤 profile이 등록되어 있는가?
- `_BOOTSTRAP_HARNESS_KEYS`는 어떤 키 목록인가? (built-in profiles vs user-registered profiles 구분용)
- `serialized_name: ClassVar[str]`을 가지는 공식 middleware는 어떤 것들이 있는가? (예: `SummarizationMiddleware`)
- `excluded_middleware`에 매칭되지 않는 entry가 있을 때 rejection이 언제 발생하는가? (생성 시점인가, 조립 시점인가?)
- `CompiledSubAgent`에 extra_middleware를 적용하려면 어떻게 해야 하는가?

---

## Used By

- [[Agent Harness]]
- [[Deep Agents]]
- [[Subagents]]

---

## Notes

- 이 파일은 `main` 브랜치 기준으로 fetch됨. 특정 commit SHA 미확인.
- Beta API — 마이너 변경 가능성 있음 (`deepagents.profiles` 모듈 전체가 beta)
