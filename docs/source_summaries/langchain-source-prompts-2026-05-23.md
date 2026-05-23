---
type: source_summary
source_id: langchain-source-prompts-2026-05-23
framework: LangChain
retrieved_at: "2026-05-23"
status: complete
confidence: high
---

# Source Summary: LangChain — Prompts Source Code

## Source Info
- **Source ID:** `langchain-source-prompts-2026-05-23`
- **Type:** source_code
- **URL:** https://github.com/langchain-ai/langchain/tree/master/libs/core/langchain_core/prompts
- **Retrieved At:** 2026-05-23
- **Version / Commit:** main branch (SHA 미확인)
- **Files:** `langchain_core/prompts/prompt.py`, `langchain_core/prompts/chat.py`

---

## Key Facts

### PromptTemplate

- `PromptTemplate`은 `StringPromptTemplate`을 상속 → `BasePromptTemplate` → `Runnable` 계층
- `template: str` — 템플릿 문자열 (필수)
- `template_format: PromptTemplateFormat = "f-string"` — 지원: `"f-string"` (기본), `"mustache"`, `"jinja2"`
- `input_variables` — `pre_init_validation`에서 `get_template_variables(template, template_format)`으로 **자동 추출**; `partial_variables`에 있는 변수는 제외됨
- `partial_variables: dict` — 미리 채워진 변수; `input_variables`에서 제외됨
- `format(**kwargs) → str` — `DEFAULT_FORMATTER_MAPPING[template_format](self.template, **kwargs)` 호출
- `from_template(template, *, template_format='f-string', partial_variables=None)` — 권장 생성 방법
- `from_file(template_file, encoding=None)` — 파일에서 로드 후 `from_template` 위임
- `from_examples(examples, suffix, input_variables, example_separator='\n\n', prefix='')` — 예제 리스트로 동적 생성
- `__add__(other: PromptTemplate | str) → PromptTemplate` — 같은 format의 두 템플릿을 연결; partial_variables 중복 시 ValueError

**⚠️ Security:**
- `jinja2`: 신뢰할 수 없는 소스에서 절대 사용 금지. SandboxedEnvironment 적용되나 opt-out 방식 — 보안 완전 보장 아님
- `f-string` 권장

### ChatPromptTemplate

- `messages: list[MessageLike]` — 핵심 필드
- `from_messages(messages, template_format='f-string')` — 권장 생성 방법 (= `cls(messages, ...)`)
- `from_template(template)` — 단일 HumanMessage 템플릿 shortcut
- `format_messages(**kwargs) → list[BaseMessage]` — 각 message_template을 순회하며 포맷

**5가지 message input format:**

| 형식 | 예시 | 변환 결과 |
|------|------|----------|
| `BaseMessagePromptTemplate` | `HumanMessagePromptTemplate(...)` | 그대로 사용 |
| `BaseMessage` | `SystemMessage("You are helpful")` | 그대로 사용 |
| 2-tuple (str role, template) | `("human", "{input}")` | role에 맞는 MessagePromptTemplate |
| 2-tuple (message class, template) | `(HumanMessage, "{input}")` | 클래스 기반 생성 |
| str | `"{input}"` | `("human", template)` shorthand |

**role 문자열 매핑 (`_create_template_from_message_type`):**

| role 문자열 | 결과 |
|-------------|------|
| `"human"` / `"user"` | `HumanMessagePromptTemplate` |
| `"ai"` / `"assistant"` | `AIMessagePromptTemplate` |
| `"system"` | `SystemMessagePromptTemplate` |
| `"placeholder"` | `MessagesPlaceholder(optional=True)` |

- `partial(**kwargs) → ChatPromptTemplate` — 일부 변수 미리 채운 새 인스턴스 반환
- `__add__` — 두 ChatPromptTemplate의 messages 리스트를 이어붙임
- **단일 변수 template**: `input_variables`가 1개이면 dict 대신 값 직접 invoke 가능
- dict 형식: `{"role": ..., "content": ...}` 키 정확히 2개 필수

### MessagesPlaceholder

- `variable_name: str` — kwargs에서 읽을 키 이름
- `optional: bool = False` — `True`이면 변수 없어도 빈 리스트 반환; `False`이면 KeyError
- `n_messages: PositiveInt | None = None` — `None`이면 전체, 값 있으면 **마지막 N개만** (`value[-n:]`)
- shorthand: `("placeholder", "{varname}")` → `MessagesPlaceholder(variable_name="varname", optional=True)`

### HumanMessagePromptTemplate / AIMessagePromptTemplate / SystemMessagePromptTemplate

- 모두 `_StringImageMessagePromptTemplate` 상속
- 차이: `_msg_class` 필드 값 (`HumanMessage`, `AIMessage`, `SystemMessage`)
- `from_template(template, template_format='f-string')` — 공통 생성 메서드

---

## Important Terms

- [[Tool Calling]] — ChatPromptTemplate은 tool call 흐름에서 system prompt 조립에 사용
- [[LangChain]] — 프롬프트 시스템의 소속 프레임워크

---

## Interpretation

- `PromptTemplate`은 단순 문자열 포맷터가 아니라 `Runnable`을 상속하므로 LCEL 체인에 그대로 연결 가능 (`prompt | llm | parser`)
- `ChatPromptTemplate.from_messages`의 5가지 input format은 ergonomic API 설계 — tuple shorthand가 가장 흔히 쓰이는 패턴
- `partial_variables`를 활용하면 프롬프트 재사용성이 높아짐 (e.g. 언어 설정, 날짜 등 고정값 사전 주입)
- `MessagesPlaceholder(optional=True)`가 `("placeholder", "{var}")` shorthand로 자동 변환되는 것은 conversation history 삽입 패턴을 편리하게 하기 위한 설계

---

## Implications for My AI Agent Project

- RAG 체인이나 agent 체인에서 system prompt를 조립할 때 `ChatPromptTemplate.from_messages` + tuple shorthand를 쓰면 간결
- 대화 이력 삽입은 `MessagesPlaceholder("history")` 패턴 사용
- partial_variables로 언어/페르소나 등 고정 설정을 미리 바인딩하면 runtime에 전달해야 할 변수가 줄어듦
- jinja2는 사용자 입력을 template으로 받는 경우 절대 사용 금지

---

## Open Questions

- `FewShotPromptTemplate`과 `ExampleSelector`는 어떻게 동작하는가? (raw에 없음)
- `PipelinePromptTemplate`은 어떻게 여러 템플릿을 연결하는가? (raw에 없음)
- `with_structured_output`과 `OutputParser`의 관계는? 내부 구현은? (raw에 없음)
- `PydanticOutputParser`는 LLM 출력 텍스트를 어떻게 Pydantic 모델로 변환하는가?
- `get_format_instructions()`는 어떻게 프롬프트에 주입되는가?
- `mustache` format의 template_variables 추출은 어떻게 다른가? (`mustache_schema` 함수가 별도로 있음)

---

## Used By

- [[LangChain]]

---

## Source Code References
- Repo: `https://github.com/langchain-ai/langchain`
- Commit: UNKNOWN (main branch)
- Files: `libs/core/langchain_core/prompts/prompt.py`, `libs/core/langchain_core/prompts/chat.py`
