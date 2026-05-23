---
type: source_summary
source_id: langchain-source-output-parsers-2026-05-23
title: "LangChain — OutputParser 소스코드 및 with_structured_output 분석"
framework: LangChain
retrieved_at: 2026-05-23
status: verified
confidence: high
---

# Source Summary: LangChain — OutputParser & with_structured_output

## Source Info
- **Source ID:** `langchain-source-output-parsers-2026-05-23`
- **Type:** source_code
- **URLs:**
  - `https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/output_parsers/pydantic.py`
  - `https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/output_parsers/json.py`
  - `https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/core/langchain_core/language_models/chat_models.py`
  - `https://raw.githubusercontent.com/langchain-ai/langchain/master/libs/partners/openai/langchain_openai/chat_models/base.py`
- **Retrieved At:** 2026-05-23
- **Version / Commit:** master branch

---

## Key Facts

### OutputParser 상속 계층

```
BaseOutputParser
  └── BaseCumulativeTransformOutputParser
        └── JsonOutputParser          ← JSON 텍스트 → dict
              └── PydanticOutputParser ← JSON 텍스트 → Pydantic 인스턴스
```

`SimpleJsonOutputParser = JsonOutputParser` — 하위 호환 alias, 기능 동일.

---

### PydanticOutputParser

**역할:** LLM이 생성한 JSON 텍스트를 Pydantic 모델 인스턴스로 변환.

**`get_format_instructions()` 동작:**
1. Pydantic 모델의 JSON schema를 추출
2. `"title"`, `"type"` 등 불필요한 필드 제거
3. 아래 형식의 텍스트로 래핑하여 반환:

```
The output should be formatted as a JSON instance that conforms to the JSON schema below.
<schema>
{"properties": {...}, "required": [...]}
</schema>
Here is the output schema:
...
```

→ 이 텍스트를 `PromptTemplate`의 `partial_variables`나 `{format_instructions}` 변수로 주입.

**파싱 파이프라인:**

```
LLM 텍스트 출력
    ↓ parse()
Generation 래핑
    ↓ parse_result() → JsonOutputParser.parse_result()
parse_json_markdown() → dict
    ↓ _parse_obj()
model.model_validate(dict)  ← Pydantic v2
model.parse_obj(dict)       ← Pydantic v1
    ↓
Pydantic 인스턴스 반환
```

- 실패 시: `OutputParserException` raise
- `partial=True` 시: 파싱 실패 → `None` 반환 (예외 없음)

---

### JsonOutputParser

**역할:** LLM 텍스트 → JSON dict.

- `parse_result()`: 텍스트 공백 제거 → `parse_json_markdown()` 적용
- streaming: `partial=True` 시 불완전 JSON → `None` (예외 없음)
- `diff=True` 시: `jsonpatch.make_patch()`로 JSONPatch 연산 스트림 생성

---

### with_structured_output (BaseChatModel)

**시그니처:**

```python
def with_structured_output(
    self,
    schema: dict[str, Any] | type,
    *,
    include_raw: bool = False,
    **kwargs: Any,
) -> Runnable[LanguageModelInput, dict[str, Any] | BaseModel]:
```

**지원 4가지 타입:**

| 타입 | 예시 | 출력 |
|------|------|------|
| Pydantic BaseModel 클래스 | `class Answer(BaseModel): ...` | Pydantic 인스턴스 (검증됨) |
| TypedDict 클래스 | `class Answer(TypedDict): ...` | dict (검증 없음) |
| JSON schema dict | `{"properties": {...}, "required": [...]}` | dict (검증 없음) |
| OpenAI function/tool schema | `{"name": ..., "parameters": {...}}` | dict (검증 없음) |

- **Pydantic만 검증됨**: Pydantic 클래스 전달 시 모델 출력이 Pydantic 인스턴스로 검증. 나머지는 dict 반환, 검증 없음.
- **추상 메서드**: `BaseChatModel`에서 `NotImplementedError`. 각 provider가 override 필수.

**`include_raw` 파라미터:**

```python
# include_raw=False (기본값) → 파싱 결과만 반환, 실패 시 예외
result = model.with_structured_output(schema).invoke(...)

# include_raw=True → 원본 + 파싱 결과 + 에러 모두 반환
result = {
    "raw": BaseMessage,          # 원본 LLM 응답
    "parsed": output_or_None,   # 파싱 결과
    "parsing_error": exc_or_None # 파싱 예외
}
```

---

### with_structured_output (OpenAI 구현)

OpenAI provider는 `method` 파라미터로 3가지 전략 선택:

| method | 내부 파이프라인 (Pydantic) | 내부 파이프라인 (dict) |
|--------|--------------------------|----------------------|
| `"function_calling"` (기본) | `bind_tools([schema]) → PydanticToolsParser` | `bind_tools([schema]) → JsonOutputKeyToolsParser` |
| `"json_mode"` | `bind(response_format={"type": "json_object"}) → PydanticOutputParser` | `bind(...) → JsonOutputParser` |
| `"json_schema"` | `bind(response_format=_convert_to_openai_response_format()) → RunnableLambda` | `bind(...) → JsonOutputParser` |

**핵심:** `json_mode` 방식만 `PydanticOutputParser`를 내부적으로 사용. `function_calling`은 tool calling 메커니즘을 거치므로 `PydanticToolsParser`(별개 클래스) 사용.

---

### OutputParser vs with_structured_output — 언제 사용?

| | `OutputParser` | `with_structured_output` |
|--|----------------|--------------------------|
| 방식 | 수동: `get_format_instructions()` → 프롬프트 주입 → `parse()` | 자동: provider가 적절한 전략 선택 |
| 사용 위치 | LCEL 체인 끝에 `.pipe(parser)` | 모델에 직접 `.with_structured_output(schema)` |
| provider 의존성 | 없음 (텍스트 파싱이므로 어느 LLM이나 가능) | 있음 (`NotImplementedError` in base) |
| 권장 상황 | provider가 tool calling/structured output 미지원 시 | OpenAI, Anthropic 등 지원 provider 사용 시 |

---

## Important Terms

- [[PromptTemplate]] — `get_format_instructions()` 주입 대상
- [[Tool Calling]] — `function_calling` 방식 내부에서 사용
- [[LangChain]] — OutputParser와 with_structured_output 모두 이 프레임워크 소속

---

## Open Questions

- Anthropic `with_structured_output` 구현은 어떤 전략을 사용하는가? (tool use vs extended thinking?)
- `PydanticToolsParser`와 `PydanticOutputParser`의 구체적 구현 차이는?
- `method="json_schema"` + `strict=True` 조합이 일부 모델에서 미지원되는 이유는?

---

## Used By

- `docs/wiki/concepts/PromptTemplate.md`
- `docs/wiki/frameworks/LangChain.md`
