---
type: concept
framework:
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-05-26
sources:
  - langchain-source-builtin-middleware-2026-05-25
---

# LLMToolSelectorMiddleware

## Summary

`LLMToolSelectorMiddleware`는 `langchain/agents/middleware/tool_selection.py`에 정의된 빌트인 미들웨어다.
에이전트에 도구가 많을 때, **별도의 작은 LLM이 사용자 쿼리를 보고 관련된 도구만 선별**한 뒤
메인 모델에 전달한다. 토큰 절약 + 메인 모델 집중도 향상이 목적이다.

핵심 메커니즘: `wrap_model_call` 훅에서 작동 → 메인 모델 호출 직전에 `request.tools`를 필터링.

- 파일: `langchain/agents/middleware/tool_selection.py` (358 lines)
- 상속: `AgentMiddleware[AgentState[ResponseT], ContextT, ResponseT]`

---

## 기본 사용법

```python
from langchain.agents import create_agent
from langchain.agents.middleware import LLMToolSelectorMiddleware

# 기본 — 에이전트 모델로 도구 선별
agent = create_agent(
    "openai:gpt-4o",
    tools=[tool1, tool2, tool3, tool4, tool5],
    middleware=[LLMToolSelectorMiddleware(max_tools=3)],
)

# 더 작은 모델로 선별 (비용 절감)
agent = create_agent(
    "openai:gpt-4o",
    tools=[...],
    middleware=[
        LLMToolSelectorMiddleware(
            model="openai:gpt-4o-mini",  # 선별용 모델
            max_tools=3,
            always_include=["search_web"],  # 항상 포함 (max_tools 제한 외)
        )
    ],
)
```

---

## 핵심 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `model` | `None` (에이전트 모델 사용) | 도구 선별용 LLM (str 또는 `BaseChatModel`) |
| `system_prompt` | `"Your goal is to select the most relevant tools..."` | 선별 모델의 인스트럭션 |
| `max_tools` | `None` (제한 없음) | 선별할 최대 도구 수 |
| `always_include` | `[]` | 항상 포함할 도구 이름 목록 (`max_tools` 제한 외) |

---

## 동작 흐름 (wrap_model_call 훅)

```
wrap_model_call(request, handler)
  │
  ├─ 1. _prepare_selection_request(request)
  │      ├─ request.tools 없음 → None 반환 → handler(request) 그대로 호출
  │      ├─ dict 타입 도구 필터 (BaseTool만 선별 대상)
  │      ├─ always_include 도구 존재 검증 (없으면 ValueError)
  │      ├─ always_include 도구를 선별 대상에서 분리
  │      ├─ 선별 가능한 도구가 0개 → None 반환 → 패스스루
  │      ├─ 마지막 HumanMessage 추출 (없으면 AssertionError)
  │      └─ max_tools 있으면 system_prompt에 "first N will be used" 안내 추가
  │
  ├─ 2. _create_tool_selection_response(available_tools)
  │      └─ Union[Annotated[Literal["tool1"], Field(description=...)], ...] 동적 스키마 생성
  │         → TypeAdapter(ToolSelectionResponse)
  │
  ├─ 3. selection_model.with_structured_output(schema).invoke([system, last_user_msg])
  │      → {"tools": ["tool2", "tool4", "tool1"]} 형태의 dict 반환
  │
  ├─ 4. _process_selection_response(response, available_tools, ...)
  │      ├─ 유효하지 않은 tool 이름 → ValueError
  │      ├─ max_tools 초과분 제거 (응답 순서 유지 — 관련성 높은 것 먼저)
  │      ├─ always_include 도구 뒤에 추가
  │      └─ 원래 request의 dict형 provider tool 보존
  │
  └─ 5. handler(request.override(tools=[selected + always + provider]))
         → 필터링된 도구 목록으로 메인 모델 호출
```

---

## 동적 스키마 생성 (핵심 구현)

선별 모델에 **각 도구의 설명이 포함된 Literal Union 스키마**를 넘긴다:

```python
# 예: tools = [tool1(name="search", desc="..."), tool2(name="calc", desc="...")]
Union[
    Annotated[Literal["search"], Field(description="Web search tool")],
    Annotated[Literal["calc"],   Field(description="Calculator tool")],
]

class ToolSelectionResponse(TypedDict):
    tools: Annotated[list[selected_tool_type], Field(description="Tools to use. Place the most relevant tools first.")]
```

→ `model.with_structured_output(schema)` 호출 시 스키마가 JSON Schema로 변환되어 전달됨.
→ LLM은 유효한 도구 이름만 응답 가능 (hallucination 방지).

---

## always_include와 max_tools 상호작용

```python
middleware = LLMToolSelectorMiddleware(
    max_tools=2,
    always_include=["critical_tool"],
)
# 결과: LLM이 2개 선별 + critical_tool 항상 포함 = 최대 3개 도구
```

- `always_include` 도구는 LLM 선별 대상에서 제외
- `always_include` 도구는 `max_tools` 카운트에 포함되지 않음
- 최종 도구 순서: `[선별된 도구] + [always_include 도구] + [provider dict 도구]`

---

## 스킵 조건

다음 경우 선별 없이 `handler(request)` 그대로 호출:

1. `request.tools`가 비어 있거나 없는 경우
2. 모든 도구가 `dict` 타입 (provider-specific tool)인 경우
3. 선별 가능 도구가 0개인 경우 (모두 `always_include`에 포함된 경우)

---

## Provider Tool Dict 보존

```python
# LangChain 도구 이외의 provider-specific 도구 (dict 형태)는 필터링 대상이 아님
# 선별 이후 항상 마지막에 추가됨
provider_tools = [tool for tool in request.tools if isinstance(tool, dict)]
```

---

## wrap_model_call vs before_model

| 구분 | `LLMToolSelectorMiddleware` | `SummarizationMiddleware` |
|------|---------------------------|--------------------------|
| 훅 | `wrap_model_call` | `before_model` |
| 역할 | 모델 호출 자체를 가로채 요청 수정 | 호출 전 상태(메시지) 변환 |
| LLM 추가 호출 | 있음 (선별 모델) | 있음 (요약 모델) |
| 핸들러 위임 | 수정된 request로 `handler()` 호출 | 없음 (상태만 변경 후 반환) |

---

## Source Code References

- Repo: `langchain-ai/langchain`
- Commit: UNKNOWN (.venv에서 읽음)
- File: `langchain/agents/middleware/tool_selection.py` (358 lines)
  - `LLMToolSelectorMiddleware.__init__`: L122
  - `_prepare_selection_request`: L158
  - `_create_tool_selection_response`: L47 (동적 Literal Union 스키마)
  - `_process_selection_response`: L232
  - `wrap_model_call`: L274
  - `awrap_model_call`: L317
  - `DEFAULT_SYSTEM_PROMPT`: L31

---

## Key Concepts

- [[LangChain create_agent flow]] — 미들웨어가 등록되는 시스템
- [[Tool Calling]] — 도구 선별의 목적
- [[Context Engineering]] — 토큰 절약 전략

---

## Open Questions

- `max_tools` 없이 선별 결과가 원래보다 많아질 수 있는가? (LLM이 임의로 모든 도구를 선택하면?)
- 선별 모델이 도구 설명을 잘못 이해해 잘못 선별하는 경우 fallback이 있는가?
- `always_include` 도구가 `request.tools`에 없으면 즉시 `ValueError` — 런타임에서 오류가 나는 시점은?

---

## Sources

- `langchain-source-builtin-middleware-2026-05-25`
