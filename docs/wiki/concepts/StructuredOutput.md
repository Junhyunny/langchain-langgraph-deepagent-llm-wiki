---
type: concept
framework:
  - LangChain
status: verified
confidence: high
last_reviewed: 2026-05-31
sources:
  - langchain-source-output-parsers-2026-05-23
---

# StructuredOutput

## Summary

`with_structured_output`은 `BaseChatModel`의 메서드로, LLM이 지정한 스키마에 맞는 구조화된 객체를 반환하도록 체인을 구성한다. provider가 내부적으로 tool calling 또는 JSON mode 전략을 선택하며, [[OutputParser]]처럼 프롬프트에 format instructions를 수동으로 주입할 필요가 없다.

## Why It Matters

`OutputParser` 방식은 LLM 텍스트를 후처리로 파싱하므로 파싱 실패 가능성이 있다. `with_structured_output`은 provider API 수준에서 출력 형식을 강제하므로 더 안정적이다. Pydantic 클래스를 쓰면 타입 검증까지 자동으로 이루어진다.

## Key Concepts

- `BaseChatModel.with_structured_output(schema)` → `Runnable` 반환
- 4가지 입력 타입: Pydantic / TypedDict / JSON schema / OpenAI function schema
- Pydantic만 검증됨 — 나머지는 dict 반환, 검증 없음
- `include_raw=True` — 원본 + 파싱 결과 + 에러를 dict로 반환
- provider마다 내부 전략이 다름 (OpenAI: 3가지 method)

## Details

### 시그니처

```python
def with_structured_output(
    self,
    schema: dict[str, Any] | type,
    *,
    include_raw: bool = False,
    **kwargs: Any,
) -> Runnable[LanguageModelInput, dict[str, Any] | BaseModel]:
```

`BaseChatModel`에서는 `NotImplementedError` — 각 provider가 반드시 override해야 한다.

### 4가지 입력 타입

| 타입 | 예시 | 출력 타입 | 검증 |
|------|------|----------|------|
| Pydantic `BaseModel` 클래스 | `class Answer(BaseModel): ...` | Pydantic 인스턴스 | ✅ 검증됨 |
| `TypedDict` 클래스 | `class Answer(TypedDict): ...` | `dict` | ❌ 없음 |
| JSON schema dict | `{"properties": {...}, "required": [...]}` | `dict` | ❌ 없음 |
| OpenAI function/tool schema | `{"name": ..., "parameters": {...}}` | `dict` | ❌ 없음 |

**Pydantic 권장:** 타입 검증 + IDE 자동완성 + `include_raw` 에러 처리까지 가능하다.

### 기본 사용법

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class Joke(BaseModel):
    setup: str = Field(description="질문 부분")
    punchline: str = Field(description="펀치라인")

llm = ChatOpenAI(model="gpt-4o")
structured_llm = llm.with_structured_output(Joke)

result = structured_llm.invoke("프로그래머 농담 하나 해줘")
# result.setup → str
# result.punchline → str
```

`structured_llm`은 `Runnable`이므로 LCEL 체인에 바로 연결할 수 있다:

```python
chain = prompt | llm.with_structured_output(Joke)
result = chain.invoke({"topic": "프로그래머"})
```

### include_raw=True — 파싱 실패 핸들링

```python
structured_llm = llm.with_structured_output(Joke, include_raw=True)
result = structured_llm.invoke("농담 해줘")

# result 구조
{
    "raw": BaseMessage,           # 원본 LLM 응답 (항상 있음)
    "parsed": Joke | None,        # 파싱 성공 시 Pydantic 인스턴스, 실패 시 None
    "parsing_error": Exception | None  # 파싱 실패 시 예외 객체
}
```

파싱 실패율이 높은 복잡한 스키마에서 `include_raw=True`로 디버깅하거나 fallback 처리할 때 사용한다.

### OpenAI provider의 3가지 method

OpenAI는 `method` 파라미터로 내부 전략을 선택할 수 있다:

| method | Pydantic 입력 시 파이프라인 | dict 입력 시 파이프라인 |
|--------|---------------------------|----------------------|
| `"function_calling"` (기본값) | `bind_tools([schema]) → PydanticToolsParser` | `bind_tools([schema]) → JsonOutputKeyToolsParser` |
| `"json_mode"` | `bind(response_format={"type":"json_object"}) → PydanticOutputParser` | `bind(...) → JsonOutputParser` |
| `"json_schema"` | `bind(response_format=_convert_to_openai_response_format()) → RunnableLambda` | `bind(...) → JsonOutputParser` |

```python
# json_schema 방식 — strict=True로 더 강한 형식 강제
structured_llm = llm.with_structured_output(Joke, method="json_schema", strict=True)
```

**핵심 차이:**
- `function_calling`: tool calling 메커니즘 경유 → `PydanticToolsParser` (별개 클래스)
- `json_mode`: 순수 텍스트 JSON 파싱 → `PydanticOutputParser` 내부 사용
- `json_schema`: OpenAI `response_format` API 사용 → 가장 엄격

### OutputParser와의 비교

| | [[OutputParser]] | `with_structured_output` |
|--|-----------------|--------------------------|
| 방식 | format instructions → 프롬프트 주입 → 텍스트 파싱 | provider API로 출력 형식 강제 |
| provider 의존성 | 없음 — 어떤 LLM이나 가능 | 있음 — 각 provider override 필요 |
| 안정성 | 상대적으로 낮음 (파싱 실패 가능) | 높음 (API 수준 강제) |
| 권장 상황 | tool calling 미지원 모델 | OpenAI, Anthropic 등 지원 provider |

## Source Code References

- Repo: `https://github.com/langchain-ai/langchain`
- Commit: UNKNOWN (master branch)
- Files:
  - `libs/core/langchain_core/language_models/chat_models.py` — `BaseChatModel.with_structured_output` (추상)
  - `libs/partners/openai/langchain_openai/chat_models/base.py` — OpenAI 구현 (3가지 method)

## Tests

- TBD — Needs Source

## Related Pages

- [[OutputParser]]
- [[Tool Calling]]
- [[Runnable]]
- [[PromptTemplate]]
- [[LangChain]]

## Open Questions

- Anthropic `with_structured_output` 구현은 어떤 전략을 사용하는가? (tool use vs extended thinking?) — Needs Source
- `PydanticToolsParser`와 `PydanticOutputParser`의 구체적 구현 차이는? — Needs Source
- `method="json_schema"` + `strict=True`가 일부 모델에서 미지원되는 이유는? — Needs Source
- TypedDict 입력 시 검증이 없다고 했는데, 런타임 타입 오류가 발생하는 경우는? — Needs Verification

## Sources

- `langchain-source-output-parsers-2026-05-23`
