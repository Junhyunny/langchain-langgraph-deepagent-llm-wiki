---
type: concept
framework:
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - langchain-source-prompts-2026-05-23
---

# PromptTemplate

## 요약

LangChain의 프롬프트 시스템은 `PromptTemplate`(단일 문자열)과 `ChatPromptTemplate`(메시지 리스트) 두 축을 중심으로 구성된다. 모두 `Runnable`을 상속하므로 LCEL `|` 체인에 그대로 연결할 수 있다.

## 상속 계층

```
Runnable
  └── BasePromptTemplate
        ├── StringPromptTemplate
        │     └── PromptTemplate          ← 단일 문자열 포맷
        └── BaseChatPromptTemplate
              └── ChatPromptTemplate      ← 메시지 리스트 기반
```

Source: `langchain-source-prompts-2026-05-23`

---

## PromptTemplate

단일 문자열을 포맷하는 프롬프트. `StringPromptTemplate` → `BasePromptTemplate` → `Runnable` 계층.

### 핵심 필드

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `template` | `str` | 필수 | 템플릿 문자열 |
| `template_format` | `"f-string"` \| `"mustache"` \| `"jinja2"` | `"f-string"` | 포맷 엔진 |
| `input_variables` | `list[str]` | 자동 추출 | 런타임에 채워야 할 변수. `pre_init_validation`에서 `get_template_variables()`로 자동 추출됨 |
| `partial_variables` | `dict` | `{}` | 미리 채워진 변수 — `input_variables`에서 제외됨 |

### 생성 방법

```python
from langchain_core.prompts import PromptTemplate

# 권장 방법
pt = PromptTemplate.from_template("Tell me a {adjective} joke about {topic}.")

# 파일에서 로드
pt = PromptTemplate.from_file("prompt.txt")

# 예제 리스트로 동적 생성
pt = PromptTemplate.from_examples(
    examples=["Good joke", "Bad joke"],
    suffix="Input: {input}\nOutput:",
    input_variables=["input"],
)
```

### partial_variables 패턴

```python
from datetime import datetime

# 날짜를 미리 바인딩 → runtime에 전달할 변수 수 감소
pt = PromptTemplate.from_template(
    "Today is {date}. Answer: {question}",
    partial_variables={"date": lambda: datetime.now().strftime("%Y-%m-%d")},
)
result = pt.format(question="What day is it?")
```

### 템플릿 연결

```python
# 같은 format의 두 PromptTemplate 연결 — partial_variables 중복 시 ValueError
pt3 = pt1 + pt2
```

### ⚠️ 보안 주의 — jinja2

- `jinja2` format: `SandboxedEnvironment` 적용되나 opt-out 방식 — 신뢰할 수 없는 소스의 템플릿에 절대 사용 금지
- `f-string` 형식 권장

Source: `langchain-source-prompts-2026-05-23`

---

## ChatPromptTemplate

메시지 리스트 기반의 프롬프트. LLM API에 전달되는 `list[BaseMessage]`를 조립한다.

### 생성 방법

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 권장 방법 — tuple shorthand
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Today is {date}."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])

# 단일 HumanMessage shortcut
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}.")
```

### 5가지 message input format

`from_messages()` 에 전달 가능한 형식:

| 형식 | 예시 | 변환 결과 |
|------|------|----------|
| `BaseMessagePromptTemplate` | `HumanMessagePromptTemplate(...)` | 그대로 사용 |
| `BaseMessage` | `SystemMessage("You are helpful")` | 그대로 사용 |
| 2-tuple (str role, template) | `("human", "{input}")` | role 매핑 → `HumanMessagePromptTemplate` |
| 2-tuple (message class, template) | `(HumanMessage, "{input}")` | 클래스 기반 생성 |
| `str` | `"{input}"` | `("human", template)` shorthand로 처리 |

### role 문자열 매핑

| role 문자열 | 결과 타입 |
|-------------|----------|
| `"human"` / `"user"` | `HumanMessagePromptTemplate` |
| `"ai"` / `"assistant"` | `AIMessagePromptTemplate` |
| `"system"` | `SystemMessagePromptTemplate` |
| `"placeholder"` | `MessagesPlaceholder(optional=True)` |

Source: `langchain-source-prompts-2026-05-23`

### 주요 메서드

```python
# 메시지 리스트 포맷
messages: list[BaseMessage] = prompt.format_messages(
    date="2026-05-23", history=[...], input="Hello"
)

# 변수 미리 채우기
partial = prompt.partial(date="2026-05-23")

# LCEL 체인 연결
chain = prompt | llm | parser

# 단일 변수 template이면 dict 대신 값 직접 전달 가능
result = prompt.invoke("Hello")  # input_variables가 1개일 때
```

### ChatPromptTemplate 연결

```python
# 두 ChatPromptTemplate의 messages 리스트 이어붙임
combined = template1 + template2
```

---

## MessagesPlaceholder

대화 히스토리(메시지 리스트)를 ChatPromptTemplate 내 특정 위치에 삽입하는 컴포넌트.

### 핵심 필드

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `variable_name` | `str` | 필수 | kwargs에서 읽을 키 이름 |
| `optional` | `bool` | **`False`** | `True`: 변수 없으면 빈 리스트 반환; `False`: **`KeyError`** 발생 |
| `n_messages` | `int \| None` | `None` | `None`: 전체 포함; 값 있으면 마지막 N개(`value[-n:]`)만 포함 |

### 중요: optional 기본값 동작

```python
# optional=False (기본값) — kwargs에 "history"가 없으면 KeyError
placeholder = MessagesPlaceholder("history")  # optional=False

# optional=True — kwargs에 "history"가 없으면 빈 리스트
placeholder = MessagesPlaceholder("history", optional=True)

# tuple shorthand → 자동으로 optional=True
("placeholder", "{history}")  # MessagesPlaceholder(variable_name="history", optional=True)
```

**⚠️ 주의**: `MessagesPlaceholder("history")`를 직접 생성하면 `optional=False`이므로, `format_messages()`에 `history` 인자를 전달하지 않으면 `KeyError`가 발생한다.

Source: `langchain-source-prompts-2026-05-23`

### n_messages 사용 패턴

```python
# 최근 10개 메시지만 컨텍스트에 포함 (컨텍스트 윈도우 절약)
MessagesPlaceholder("history", n_messages=10)
```

---

## LCEL 체인에서의 활용

`PromptTemplate`과 `ChatPromptTemplate` 모두 `Runnable`을 상속하므로 LCEL `|` 체인에 그대로 연결 가능하다.

```python
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

# RAG 패턴: 검색 결과를 병렬로 가져와 프롬프트에 주입
chain = (
    RunnableParallel({"context": retriever, "question": RunnablePassthrough()})
    | ChatPromptTemplate.from_messages([
        ("system", "Answer using context:\n\n{context}"),
        ("human", "{question}"),
    ])
    | llm
)
```

---

## 미해결 질문

- `FewShotPromptTemplate`에서 `ExampleSelector`는 어떻게 동작하는가? — Needs Source (`langchain-source-prompts-2026-05-23`에 없음)
- `PipelinePromptTemplate`에서 여러 템플릿을 연결하는 내부 방식은? — Needs Source
- `PydanticOutputParser`는 LLM 출력 텍스트를 Pydantic 모델로 어떻게 변환하는가? — Needs Source
- `with_structured_output`과 `OutputParser`의 관계는? — Needs Source
- `mustache` 포맷의 template_variables 추출 방식 (`mustache_schema` 함수)은? — Needs Source

## 관련 페이지

- [[LangChain]]
- [[Context Engineering]]
- [[Tool Calling]]
- [[Memory]]
- [[RAG]]

## 소스

- `langchain-source-prompts-2026-05-23`
