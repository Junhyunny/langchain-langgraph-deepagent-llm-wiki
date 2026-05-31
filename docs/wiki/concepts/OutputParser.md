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

# OutputParser

## Summary

`OutputParser`는 LLM이 생성한 텍스트를 구조화된 Python 객체로 변환하는 [[Runnable]] 구현체다. LCEL 체인 끝에 연결해 사용한다. provider 독립적이어서 tool calling 미지원 모델에도 사용할 수 있다.

## Why It Matters

`with_structured_output`이 provider API에 의존하는 반면, `OutputParser`는 순수 텍스트 파싱이므로 어떤 LLM과도 사용 가능하다. Pydantic 스키마를 프롬프트에 주입하고, LLM 출력 텍스트를 Pydantic 인스턴스로 검증하는 흐름을 이해하면 structured output의 두 전략 모두를 이해하게 된다.

## Key Concepts

- `BaseOutputParser` → `JsonOutputParser` → `PydanticOutputParser` 상속 계층
- `get_format_instructions()` — 스키마를 프롬프트 텍스트로 변환
- `parse()` — LLM 텍스트 출력 → Python 객체
- streaming: `partial=True` 시 불완전 JSON → `None` (예외 없음)
- vs `with_structured_output` → [[StructuredOutput]]

## Details

### 상속 계층

```
BaseOutputParser(Runnable)
  └── BaseCumulativeTransformOutputParser
        └── JsonOutputParser          ← JSON 텍스트 → dict
              └── PydanticOutputParser ← JSON 텍스트 → Pydantic 인스턴스
```

`SimpleJsonOutputParser = JsonOutputParser` — 하위 호환 alias.

### JsonOutputParser

LLM 텍스트를 dict로 변환:

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()
result = parser.invoke('{"name": "Alice", "age": 30}')
# → {"name": "Alice", "age": 30}
```

- `parse_result()`: 텍스트 공백 제거 → `parse_json_markdown()` 적용
- streaming: `partial=True` 시 불완전 JSON → `None` (예외 없음)
- `diff=True` 시: `jsonpatch.make_patch()`로 JSONPatch 연산 스트림 생성

### PydanticOutputParser

LLM 텍스트를 Pydantic 인스턴스로 변환:

```python
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

class Answer(BaseModel):
    name: str
    score: int

parser = PydanticOutputParser(pydantic_object=Answer)
```

**`get_format_instructions()` 동작:**

1. Pydantic 모델의 JSON schema 추출
2. `"title"`, `"type"` 등 불필요한 필드 제거
3. 아래 형식 텍스트로 래핑:

```
The output should be formatted as a JSON instance that conforms to the JSON schema below.
<schema>
{"properties": {"name": ..., "score": ...}, "required": [...]}
</schema>
```

→ 이 텍스트를 `{format_instructions}` 변수로 프롬프트에 주입한다.

**파싱 파이프라인:**

```
LLM 텍스트 출력
    ↓ parse()
parse_json_markdown() → dict
    ↓ _parse_obj()
model.model_validate(dict)   ← Pydantic v2
model.parse_obj(dict)        ← Pydantic v1
    ↓
Pydantic 인스턴스 반환
```

- 실패 시: `OutputParserException` raise
- `partial=True` 시: 파싱 실패 → `None` 반환 (예외 없음)

### LCEL 체인에서의 사용 패턴

```python
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class Joke(BaseModel):
    setup: str = Field(description="질문 부분")
    punchline: str = Field(description="펀치라인")

parser = PydanticOutputParser(pydantic_object=Joke)

prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 농담 생성기입니다.\n{format_instructions}"),
    ("human", "{topic}에 대한 농담을 만들어주세요"),
]).partial(format_instructions=parser.get_format_instructions())

chain = prompt | llm | parser

result = chain.invoke({"topic": "프로그래머"})
# result.setup, result.punchline → Pydantic 인스턴스
```

### StrOutputParser

가장 단순한 파서. AIMessage에서 텍스트 내용만 추출:

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | llm | StrOutputParser()
result = chain.invoke(...)  # → str
```

### OutputParser vs with_structured_output

| | `OutputParser` | `with_structured_output` |
|--|----------------|--------------------------|
| 방식 | 수동: format instructions → 프롬프트 주입 → 텍스트 파싱 | 자동: provider가 tool calling/JSON mode 전략 선택 |
| 사용 위치 | LCEL 체인 끝: `prompt \| llm \| parser` | 모델에 직접: `llm.with_structured_output(schema)` |
| provider 의존성 | 없음 (순수 텍스트 파싱) | 있음 (각 provider override 필요) |
| 권장 상황 | tool calling 미지원 모델 | OpenAI, Anthropic 등 지원 provider |

자세한 내용 → [[StructuredOutput]]

## Source Code References

- Repo: `https://github.com/langchain-ai/langchain`
- Commit: UNKNOWN (master branch)
- Files:
  - `libs/core/langchain_core/output_parsers/pydantic.py`
  - `libs/core/langchain_core/output_parsers/json.py`

## Tests

- TBD — Needs Source

## Related Pages

- [[Runnable]]
- [[PromptTemplate]]
- [[StructuredOutput]]
- [[Tool Calling]]
- [[LangChain]]

## Open Questions

- `PydanticToolsParser`와 `PydanticOutputParser`의 구체적 구현 차이는? — Needs Source
- Anthropic `with_structured_output`은 어떤 전략을 사용하는가? (tool use vs extended thinking?) — Needs Source
- `method="json_schema"` + `strict=True` 조합이 일부 모델에서 미지원되는 이유는? — Needs Source
- streaming 시 부분 Pydantic 인스턴스를 받으려면 어떻게 해야 하는가? — Needs Source

## Sources

- `langchain-source-output-parsers-2026-05-23`
