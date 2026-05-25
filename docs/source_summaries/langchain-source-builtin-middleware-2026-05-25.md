# LangChain Built-in Middleware 소스 분석

**Source ID:** `langchain-source-builtin-middleware-2026-05-25`
**Retrieved:** 2026-05-25
**Path:** `/usr/local/lib/python3.11/dist-packages/langchain/agents/middleware/`
**Version:** langchain 1.3.1

---

## 파일 목록

```
__init__.py, types.py
summarization.py       — SummarizationMiddleware
tool_selection.py      — LLMToolSelectorMiddleware
pii.py                 — PIIMiddleware
human_in_the_loop.py
context_editing.py
file_search.py
model_call_limit.py
model_fallback.py
model_retry.py
shell_tool.py
todo.py
tool_call_limit.py
tool_emulator.py
tool_retry.py
_execution.py, _redaction.py, _retry.py
```

---

## SummarizationMiddleware (summarization.py)

**역할:** 대화 히스토리가 임계값에 도달하면 자동으로 요약 후 메시지 교체.

**훅 종류:** `before_model` (+ async 버전)

**파라미터:**
```python
SummarizationMiddleware(
    model: str | BaseChatModel,
    trigger: ContextSize | list[ContextSize] | None = None,
    keep: ContextSize = ("messages", 20),
    token_counter = count_tokens_approximately,
    summary_prompt: str = DEFAULT_SUMMARY_PROMPT,
    trim_tokens_to_summarize: int | None = 4000,
)
```

**ContextSize 타입:**
- `("fraction", 0.8)` — 모델 최대 입력 토큰의 80% 초과 시
- `("tokens", 3000)` — 절대 토큰 수 초과 시
- `("messages", 50)` — 절대 메시지 수 초과 시

**핵심 흐름:**
```
before_model()
  ↓ _should_summarize() — trigger 조건 체크 (multiple trigger 지원)
  ↓ _determine_cutoff_index() — keep 정책에 따라 보존할 메시지 경계 계산
  ↓ _find_safe_cutoff_point() — AI/Tool 메시지 쌍이 분리되지 않게 경계 조정
  ↓ _create_summary() — 요약 모델 호출
  ↓ 반환: {messages: [RemoveMessage(REMOVE_ALL_MESSAGES), HumanMessage(summary), ...preserved]}
```

**AI/Tool 쌍 보호 로직:**
- cutoff 지점이 ToolMessage 중간에 걸리면 역방향으로 대응 AIMessage 검색
- 해당 AIMessage까지 포함해서 요약 대상에 포함 (쌍 분리 방지)

**토큰 카운터:**
- Anthropic 모델: `chars_per_token=3.3` 적용 (오프라인 실험 기반 보정치)
- 기타: `count_tokens_approximately` 기본값

**모델 프로파일 의존:**
- `("fraction", ...)` 사용 시 `model.profile["max_input_tokens"]` 필요
- 없으면 `ValueError` 발생 (생성 시점에 검증)

---

## LLMToolSelectorMiddleware (tool_selection.py)

**역할:** 메인 모델 호출 전에 별도 LLM으로 관련 도구만 선별 → 토큰 절약 + 집중도 향상.

**훅 종류:** `wrap_model_call` (+ async 버전) — `before_model`이 아님

**파라미터:**
```python
LLMToolSelectorMiddleware(
    model: str | BaseChatModel | None = None,  # None이면 agent 메인 모델 사용
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    max_tools: int | None = None,
    always_include: list[str] | None = None,   # 항상 포함할 도구 이름
)
```

**핵심 흐름:**
```
wrap_model_call(request, handler)
  ↓ _prepare_selection_request() — BaseTool만 필터링, 마지막 HumanMessage 추출
  ↓ _create_tool_selection_response(tools) — Union[Literal[name], ...] 동적 스키마 생성
  ↓ model.with_structured_output(schema).invoke([system, last_user_msg])
  ↓ _process_selection_response() — 선택된 도구로 request.override(tools=[...])
  ↓ handler(modified_request) — 필터된 도구로 메인 모델 호출
```

**`wrap_model_call` vs `before_model` 차이:**
- `before_model`: state를 수정하고 모델 호출에 영향
- `wrap_model_call`: 모델 호출 자체를 가로채서 `request` 객체(tools 포함)를 수정 가능 → `handler`에 전달

**always_include 처리:**
- `always_include` 도구는 선택 대상에서 제외 → 선택 모델이 볼 후보 목록에서 빠짐
- 선택 완료 후 결과에 항상 추가됨
- `max_tools` 카운트에 포함되지 않음

**스키마 생성 방식:**
```python
class ToolSelectionResponse(TypedDict):
    tools: Annotated[list[Union[Literal["tool1"], Literal["tool2"]]], Field(...)]
```
— TypeAdapter로 JSON schema 추출 → `with_structured_output(schema)` 전달

---

## PIIMiddleware (pii.py)

**역할:** 대화 중 PII 감지 및 전략적 처리 (block/redact/mask/hash).

**훅 종류:** `before_model` (입력/도구 결과), `after_model` (출력)
- `@hook_config(can_jump_to=["end"])` 데코레이터 — PII 차단 시 end로 점프 가능

**파라미터:**
```python
PIIMiddleware(
    pii_type: Literal["email", "credit_card", "ip", "mac_address", "url"] | str,
    strategy: Literal["block", "redact", "mask", "hash"] = "redact",
    detector: Callable | str | None = None,  # None이면 빌트인 감지기
    apply_to_input: bool = True,
    apply_to_output: bool = False,
    apply_to_tool_results: bool = False,
)
```

**빌트인 감지기 종류:**
- `email` — 이메일 주소
- `credit_card` — Luhn 알고리즘 검증 포함
- `ip` — stdlib ipaddress로 검증
- `mac_address`
- `url` — http/https + bare URL

**커스텀 PII 예시:**
```python
PIIMiddleware("api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block")
```

**처리 범위:**
- `apply_to_input=True` (기본): 마지막 HumanMessage만 처리
- `apply_to_tool_results=True`: 마지막 AIMessage 이후 ToolMessage들 처리
- `apply_to_output=True`: 마지막 AIMessage 처리 (`after_model`)

**`hook_config(can_jump_to=["end"])` 의미:**
- `strategy="block"` + PII 감지 시 `PIIDetectionError` 발생 → `end`로 직접 점프
- `AgentState.jump_to("end")` 패턴과 연결 (types.py의 EphemeralValue)

---

## 훅 선택 패턴 정리

| 미들웨어 | 훅 | 이유 |
|----------|-----|------|
| `SummarizationMiddleware` | `before_model` | state.messages를 수정하여 모델에 전달되는 컨텍스트 교체 |
| `LLMToolSelectorMiddleware` | `wrap_model_call` | `request.tools`를 수정해야 함 (state 수정으로는 불가) |
| `PIIMiddleware` | `before_model` + `after_model` | 입력/출력 양방향 처리 필요 |

**핵심 원칙:**
- state(messages) 변환만 필요 → `before_model` / `after_model`
- 모델 호출 자체의 인자(tools, system_message 등) 수정 필요 → `wrap_model_call`

---

## 관련 Wiki 페이지

- `docs/wiki/concepts/Agent Harness.md`
- `docs/wiki/flows/LangChain create_agent flow.md`
- `docs/wiki/concepts/Context Engineering.md`
