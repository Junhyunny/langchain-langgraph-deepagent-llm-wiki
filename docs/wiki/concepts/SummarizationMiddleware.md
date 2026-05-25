---
type: concept
framework:
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-05-28
sources:
  - langchain-agents-summarization-middleware-2026-05-28
---

# SummarizationMiddleware

## Summary

`SummarizationMiddleware`는 `langchain/agents/middleware/summarization.py`에 정의된 빌트인 미들웨어다.
에이전트 대화 히스토리가 길어져 토큰 한계에 가까워질 때, 오래된 메시지를 LLM으로 요약해 교체함으로써
**컨텍스트 윈도우를 자동으로 관리**한다.

핵심 메커니즘: `before_model` 훅에서 작동 → 모델 호출 직전에 메시지 히스토리를 요약된 HumanMessage로 교체.

- 파일: `langchain/agents/middleware/summarization.py` (678 lines)
- 상속: `AgentMiddleware[AgentState[ResponseT], ContextT, ResponseT]`

---

## 기본 사용법

```python
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware

agent = create_agent(
    model="anthropic:claude-sonnet-4-5",
    tools=[...],
    middleware=[
        SummarizationMiddleware(
            model="anthropic:claude-haiku-4-5",    # 요약용 모델 (가볍게)
            trigger=("tokens", 10_000),             # 10000 토큰 초과 시 요약
            keep=("messages", 20),                  # 최근 20개 메시지 보존
        )
    ],
)
```

---

## 핵심 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `model` | **필수** | 요약 생성에 사용할 LLM |
| `trigger` | `None` (비활성) | 요약 발동 임계값. `None`이면 **요약 안 함** |
| `keep` | `("messages", 20)` | 요약 후 보존할 최근 히스토리 |
| `token_counter` | `count_tokens_approximately` | 토큰 카운팅 함수 |
| `summary_prompt` | 내장 프롬프트 | 요약 생성 프롬프트 |
| `trim_tokens_to_summarize` | `4000` | 요약 대상 메시지 최대 토큰 수 (`None`이면 무제한) |

### ContextSize 타입

```python
ContextSize = ("fraction", 0.8)   # 모델 최대 입력 토큰의 80%
           | ("tokens", 10_000)   # 절대 토큰 수
           | ("messages", 50)     # 절대 메시지 수
```

`trigger`는 list로 여러 조건 제공 가능 (OR 로직):

```python
trigger=[("fraction", 0.8), ("messages", 100)]
# 80% 초과 OR 100개 메시지 중 먼저 달성되면 요약
```

---

## 동작 흐름 (before_model 훅)

```
before_model(state, runtime)
  │
  ├─ 1. _ensure_message_ids(messages)     ← 모든 메시지에 UUID 할당 (없는 경우)
  │
  ├─ 2. total_tokens = token_counter(messages)
  │
  ├─ 3. _should_summarize(messages, total_tokens)?
  │      ├─ trigger_conditions가 없으면 → False (요약 안 함)
  │      ├─ ("messages", n): len(messages) >= n → True
  │      ├─ ("tokens", n): total_tokens >= n → True
  │      ├─ ("fraction", f): total_tokens >= max_input * f → True
  │      └─ AIMessage.usage_metadata.total_tokens 기반도 체크 (provider 보고값)
  │
  ├─ 4. _determine_cutoff_index(messages)
  │      ├─ ("tokens"/"fraction"): 이진 탐색으로 최적 cutoff 찾기
  │      └─ ("messages", n): len(messages) - n = cutoff
  │
  ├─ 5. _find_safe_cutoff_point(messages, cutoff)   ← AIMessage/ToolMessage 쌍 보호
  │      └─ cutoff가 ToolMessage에 걸리면 → 해당 tool_call_id 역추적 → AIMessage 앞으로 이동
  │
  ├─ 6. _partition_messages(messages, cutoff)
  │      ├─ messages_to_summarize = messages[:cutoff]
  │      └─ preserved_messages   = messages[cutoff:]
  │
  ├─ 7. _create_summary(messages_to_summarize)
  │      ├─ _trim_messages_for_summary() → trim_messages(max_tokens=4000, strategy="last")
  │      ├─ get_buffer_string(trimmed_messages) → 텍스트 포맷
  │      └─ model.invoke(summary_prompt.format(messages=...))
  │
  └─ 8. 반환값:
         {"messages": [
             RemoveMessage(id=REMOVE_ALL_MESSAGES),  ← 전체 메시지 삭제
             HumanMessage("Here is a summary..."),   ← 요약 메시지 삽입
             *preserved_messages,                    ← 최근 N개 보존
         ]}
```

---

## AI/Tool 쌍 보호 메커니즘 (중요)

`_find_safe_cutoff_point()`: cutoff 인덱스가 `ToolMessage`에 걸리면 메시지 쌍이 깨진다.
이를 방지하기 위해:

1. cutoff 위치에서 연속된 `ToolMessage`들의 `tool_call_id` 수집
2. 역방향 탐색으로 해당 id를 가진 `AIMessage` 찾기
3. cutoff를 그 `AIMessage` 앞으로 이동

```
[... HumanMsg, AIMsg(tool_calls=[id=X]), ToolMsg(id=X), ToolMsg(id=Y) | HumanMsg(preserved)]
                                                                        ↑ cutoff 원래 위치
→ 역추적으로 AIMsg 찾음
[... HumanMsg | AIMsg(tool_calls=[id=X]), ToolMsg(id=X), ToolMsg(id=Y), HumanMsg(preserved)]
                ↑ 수정된 cutoff (AIMsg와 ToolMsg 쌍이 보존 영역에 함께 들어감)
```

---

## 요약 메시지 포맷

요약 결과는 `HumanMessage`로 삽입됨:

```python
HumanMessage(
    content="Here is a summary of the conversation to date:\n\n{summary}",
    additional_kwargs={"lc_source": "summarization"},
)
```

**주의**: `AIMessage`나 `SystemMessage`가 아닌 **`HumanMessage`**로 삽입된다.
→ 모델에게 "이전 대화 요약"으로 제공됨.

---

## 토큰 카운팅 전략

### 근사 토큰 카운터 (기본값)

```python
# Anthropic: chars_per_token=3.3 (오프라인 실험으로 보정)
count_tokens_approximately(use_usage_metadata_scaling=True, chars_per_token=3.3)

# 기타 모델: 기본 파라미터
count_tokens_approximately(use_usage_metadata_scaling=True)
```

### Provider 보고 토큰 활용

`_should_summarize_based_on_reported_tokens()`: 마지막 `AIMessage.usage_metadata.total_tokens`를
직접 사용 (근사값보다 정확). Provider 불일치 방지를 위해 `_LS_PROVIDER_ALIASES` 매핑 사용.

```python
_LS_PROVIDER_ALIASES = {
    "amazon_bedrock": frozenset({"bedrock", "bedrock_converse"}),
}
```

### 이진 탐색으로 token-based cutoff 찾기

`_find_token_based_cutoff()`: O(log n) 탐색으로 "정확히 target_token_count 이하로 보존할 최소 cutoff" 찾기.

---

## trigger=None 기본값 주의

```python
# ⚠️ 이러면 요약이 절대 안 됨!
middleware = SummarizationMiddleware(model="gpt-4o")  # trigger=None 기본값

# ✅ 반드시 trigger 설정
middleware = SummarizationMiddleware(
    model="gpt-4o-mini",
    trigger=("tokens", 10_000),
)
```

`_should_summarize()`: `trigger_conditions`가 비어 있으면 즉시 `False` 반환.

---

## fraction 타입 사용 시 model.profile 필요

`("fraction", 0.8)` 사용 시 모델의 `max_input_tokens` 정보가 필요:

```python
# model.profile에 max_input_tokens가 없으면 ValueError
SummarizationMiddleware(
    model=ChatOpenAI(model="gpt-4o", profile={"max_input_tokens": 128000}),
    trigger=("fraction", 0.8),
)
```

`__init__`에서 미리 검증 → 런타임 오류 방지.

---

## REMOVE_ALL_MESSAGES 사용

LangGraph의 특수 sentinel `REMOVE_ALL_MESSAGES` (`langgraph.graph.message`)를 사용해
**전체 메시지 히스토리를 한 번에 삭제** 후 교체:

```python
return {
    "messages": [
        RemoveMessage(id=REMOVE_ALL_MESSAGES),  # 기존 메시지 전체 삭제
        *new_messages,                           # 요약 HumanMessage
        *preserved_messages,                    # 최근 N개 보존
    ]
}
```

→ `add_messages` reducer가 `REMOVE_ALL_MESSAGES`를 인식해 처리.

---

## Source Code References

- Repo: `langchain-ai/langchain`
- Commit: UNKNOWN (.venv에서 읽음)
- File: `langchain/agents/middleware/summarization.py` (678 lines)
  - `SummarizationMiddleware.__init__`: L178
  - `before_model`: L309
  - `_should_summarize`: L407
  - `_determine_cutoff_index`: L435
  - `_find_token_based_cutoff`: L447 (이진 탐색)
  - `_find_safe_cutoff_point`: L572 (AI/Tool 쌍 보호)
  - `_create_summary`: L608
  - `DEFAULT_SUMMARY_PROMPT`: L33

---

## Key Concepts

- [[LangChain create_agent flow]] — SummarizationMiddleware가 등록되는 미들웨어 시스템
- [[Context Engineering]] — 컨텍스트 윈도우 관리 전략
- [[Memory]] — 대화 히스토리 관리
- [[Tool Calling]] — AI/Tool 메시지 쌍 보호가 필요한 이유

---

## Open Questions

- `before_model`이 요약을 수행하면 LangSmith 트레이싱에서 어떻게 보이는가?
- `summary_prompt`를 커스터마이징할 때 `{messages}` 외의 변수를 넣을 수 있는가?
- `trim_tokens_to_summarize=None`으로 설정하면 긴 히스토리를 요약할 때 모델 토큰 제한에 걸릴 위험이 있는가?

---

## Sources

- `langchain-agents-summarization-middleware-2026-05-28`
