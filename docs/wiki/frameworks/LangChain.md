---
type: framework
framework: LangChain
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langchain-docs-event-streaming-2026-05-18
  - langchain-docs-messages-2026-05-23
  - langchain-docs-rag-2026-05-23
  - langchain-docs-tools-2026-05-23
  - langchain-source-prompts-2026-05-23
  - langchain-source-runnable-2026-05-23
  - langchain-source-create-agent-factory-2026-05-23
  - langchain-source-dynamic-prompt-2026-05-23
  - langchain-source-memory-api-2026-05-23
---

# LangChain

## 요약

LangChain은 LLM 기반 애플리케이션을 구축하기 위한 프레임워크다. 채팅 모델, 메시지, 도구, RAG 파이프라인을 위한 추상화를 제공한다. LangGraph와 Deep Agents는 모두 LangChain 추상화 위에 구축된다.

## 중요한 이유

LangChain은 이 생태계의 기반 프레임워크다. LangGraph와 Deep Agents는 모두 LangChain 추상화 위에 구축되므로, 이를 이해하기 전에 LangChain을 이해하는 것이 필요하다.

---

## 메시지 시스템
*Source: `langchain-docs-messages-2026-05-23`*

### 메시지의 정의

메시지는 LangChain에서 **채팅 모델과 소통하는 기본 단위**다. 채팅 모델은 메시지 리스트를 입력으로 받고, AIMessage를 출력으로 반환한다.

메시지의 3가지 요소:
- **Role** — 메시지 유형 식별 (system / human / ai / tool)
- **Content** — 텍스트, 이미지, 오디오 등 멀티모달 지원
- **Metadata** — 응답 정보, 메시지 ID, 토큰 사용량

### 주요 메시지 타입 4종

| 클래스 | Role | 용도 |
|--------|------|------|
| `SystemMessage` | `system` | 모델의 동작 방식/페르소나 지정 |
| `HumanMessage` | `human` | 사용자 입력 (텍스트, 이미지 등) |
| `AIMessage` | `ai` | 모델 응답 (텍스트 + tool_calls) |
| `ToolMessage` | `tool` | tool 실행 결과를 모델에 전달 |

### AIMessage 주요 속성

- `content` — 응답 텍스트
- `tool_calls` — 모델이 호출한 도구 목록 (`[{"name": ..., "args": ..., "id": ...}]`)
- `usage_metadata` — 토큰 사용량 (input_tokens, output_tokens, total_tokens)

### ToolMessage 핵심 계약

`ToolMessage.tool_call_id`는 반드시 `AIMessage.tool_calls[i]['id']`와 일치해야 한다.

```python
# tool call 흐름
messages = [HumanMessage("What's the weather?")]
ai_message = model_with_tools.invoke(messages)
# ai_message.tool_calls = [{"name": "get_weather", "args": {...}, "id": "call_123"}]

tool_message = ToolMessage(
    content="Sunny, 72°F",
    tool_call_id="call_123",  # AIMessage의 id와 매칭 필수
    name="get_weather"
)
messages = messages + [ai_message, tool_message]
final = model.invoke(messages)
```

### 스트리밍: AIMessageChunk

```python
for chunk in model.stream("Hi"):
    chunks.append(chunk)
    full_message = chunk if full_message is None else full_message + chunk
```

---

## 도구(Tool)
*Source: `langchain-docs-tools-2026-05-23`*

### @tool 데코레이터

가장 간단한 도구 생성 방법. **함수의 docstring이 모델에게 보이는 도구 설명이 된다.**

```python
from langchain.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"
```

**필수 규칙:**
- **타입 힌트 필수** — 도구의 입력 스키마를 정의
- **Docstring이 핵심** — 모델이 언제 이 도구를 사용할지 판단하는 근거

### ToolRuntime — 도구 내 컨텍스트 접근

| 컴포넌트 | 설명 | 사용 사례 |
|---------|------|---------|
| **State** | 현재 대화의 단기 메모리 | 대화 이력 접근 |
| **Context** | 호출 시 전달된 불변 설정 | 사용자 ID 기반 개인화 |
| **Store** | 대화 간 영속적 장기 메모리 | 사용자 선호도 저장 |
| **Stream Writer** | 실시간 업데이트 발행 | 진행 상황 표시 |
| **Execution Info** | Thread ID, run ID | 스레드/런 식별 |

### 도구 반환값 3가지

| 반환 타입 | 용도 |
|---------|------|
| `string` | 평문 결과 → ToolMessage 자동 변환 |
| `object` | 구조화 데이터 → 직렬화 후 모델 전달 |
| `Command` | 상태 업데이트 필요 시 |

### 도구 실행 흐름

LangChain에서 도구는 `create_agent`로 에이전트에 등록. LangGraph에서는 `ToolNode`가 실행 처리.

### ⚠️ LCEL 상태 (중요)

> 2026년 기준 새 LangChain docs에 LCEL/Runnable 전용 페이지가 없다.
> 새 docs는 `create_agent` + `AgentMiddleware` + `ToolRuntime` 패턴 중심으로 재편됨.

---

## RAG (Retrieval-Augmented Generation)
*Source: `langchain-docs-rag-2026-05-23`*

### RAG의 목적

RAG는 외부 소스에서 가져온 사실로 LLM의 정확성을 높이는 기법이다.

해결하는 LLM 한계:
1. **Knowledge cutoff** — 학습 데이터 이후 정보 없음
2. **Hallucinations** — 그럴듯하지만 부정확한 정보 생성

### 두 가지 RAG 패턴

| 패턴 | 특징 | 적합한 경우 |
|------|------|------------|
| RAG agent | 지능적으로 검색 시점 결정 | 복잡한 쿼리 |
| RAG chain | 항상 검색 후 생성 (결정적) | 단순 쿼리 |

### 인덱싱 파이프라인 4단계

**1. Document Loaders** — PDF, Word, CSV, HTML, Markdown, DB 등:
```python
from langchain.document_loaders import WebBaseLoader, PyPDFLoader
```

**2. Text Splitting** — 권장: `RecursiveCharacterTextSplitter` (단락→문장→단어→문자 순):
```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200  # 앞뒤 문맥 보존
)
splits = text_splitter.split_documents(docs)
```

**3. Vector Stores** — 임베딩 기반 의미 유사도 검색:
```python
from langchain.embeddings import init_embeddings
from langchain.vectorstores import InMemoryVectorStore

embeddings = init_embeddings("openai:text-embedding-3-small")
vector_store = InMemoryVectorStore(embeddings)
vector_store.add_documents(splits)
results = vector_store.similarity_search("What is LangChain?", k=3)
```

지원 벡터 스토어: InMemoryVectorStore, Chroma, FAISS, Pinecone, Qdrant, pgvector, Weaviate, Elasticsearch

**4. Retrievers** — 벡터 스토어에 대한 추상화 계층:
```python
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
docs = retriever.invoke("What is LangChain?")
```

추가 리트리버: `MultiQueryRetriever`, `ContextualCompressionRetriever`, `BM25Retriever`, `EnsembleRetriever`

### 보안: Indirect Prompt Injection

RAG의 주요 보안 위협 — 악성 지시가 문서에 포함되어 검색 후 프롬프트에 삽입되는 공격.

완화: 검색 콘텐츠 정제, 명시적 구분자, 입출력 가드레일

---

## Event Streaming
*Source: `langchain-docs-event-streaming-2026-05-18`*

- 권장: `stream_events(..., version="v3")`
- 리턴: 타입화된 프로젝션이 있는 run object

| 프로젝션 | 용도 |
|---|---|
| `stream.messages` | LLM 호출별 메시지 스트림 |
| `stream.tool_calls` | tool 실행 라이프사이클 |
| `stream.values` | agent state 스냅샷 |
| `stream.output` | 최종 agent state |
| `stream.subgraphs` | 중첩 그래프 실행 |
| `stream.extensions` | 커스텀 transformer 프로젝션 |

---

## Agent API 변화 (검증됨)

*Source: `langchain-source-create-agent-factory-2026-05-23`*

| API | 상태 | 파일 경로 |
|-----|------|----------|
| `create_agent` | **현재 공식 API** | `libs/langchain_v1/langchain/agents/factory.py` |
| `create_tool_calling_agent` + `AgentExecutor` | **deprecated** | `tool_calling_agent/base.py`, `agents/agent.py` — master에 없음 |
| `create_react_agent` (LangGraph prebuilt) | 별개 API (LangGraph 패키지) | `langgraph.prebuilt.chat_agent_executor` |

`create_agent`는 내부에서 `StateGraph`를 직접 구성한다. 루프 제어는 `add_conditional_edges()`로 구현되며, `tool_calls`가 없으면 `END`, 있으면 tools node → model node 루프.

자세한 흐름: [[LangChain create_agent flow]]

---

## LangGraph와의 관계 (확인됨)

> "LangChain agents are built on LangGraph, so they support the same streaming stack"
> *Source: `langchain-docs-event-streaming-2026-05-18`*

LangChain의 `create_agent`는 LangGraph 위에 구축됨.

---

## 핵심 추상화

- `BaseChatModel` — 모든 LLM 통합의 기본 클래스
- `BaseMessage` / 4종 메시지 클래스 — 표준 메시지 타입 계층
- `BaseRetriever` — 문서 검색 추상화
- `Tool` / `@tool` 데코레이터 — LLM에 노출되는 외부 기능
- `create_agent()` — LangGraph 기반 에이전트 생성

## Prompts (PromptTemplate / ChatPromptTemplate)
*Source: `langchain-source-prompts-2026-05-23`*

### PromptTemplate

`PromptTemplate`은 `StringPromptTemplate → BasePromptTemplate → Runnable` 계층을 상속하므로 LCEL 체인에 직접 연결할 수 있다 (`prompt | llm | parser`).

| 필드 | 기본값 | 설명 |
|------|--------|------|
| `template` | — (필수) | 템플릿 문자열 |
| `template_format` | `"f-string"` | `"f-string"` / `"mustache"` / `"jinja2"` |
| `input_variables` | 자동 추출 | `get_template_variables(template, format)` 으로 자동 추출; `partial_variables` 키는 제외 |
| `partial_variables` | `{}` | 미리 채워진 변수; `input_variables`에서 제외됨 |

**권장 생성 방법:**
```python
prompt = PromptTemplate.from_template("Say {foo}")
prompt.format(foo="bar")  # → "Say bar"
```

기타 생성자: `from_file(path)`, `from_examples(examples, suffix, input_variables)`

**`__add__` 지원:** 같은 format의 두 PromptTemplate을 `+` 로 연결 가능.

**⚠️ Security:** jinja2는 신뢰할 수 없는 소스 입력에 절대 사용 금지. SandboxedEnvironment는 opt-out 방식 — 완전 보장 아님. f-string 권장.

### ChatPromptTemplate

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are {name}."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])
```

**5가지 message input format:**

| 형식 | 예시 | 변환 결과 |
|------|------|----------|
| `BaseMessagePromptTemplate` | `HumanMessagePromptTemplate(...)` | 그대로 사용 |
| `BaseMessage` | `SystemMessage("You are helpful")` | 그대로 사용 |
| 2-tuple (str role, template) | `("human", "{input}")` | role에 맞는 MessagePromptTemplate |
| 2-tuple (message class, template) | `(HumanMessage, "{input}")` | 클래스 기반 생성 |
| str | `"{input}"` | HumanMessagePromptTemplate shorthand |

**role 문자열 → 클래스 매핑:**

| role 문자열 | 결과 |
|-------------|------|
| `"human"` / `"user"` | `HumanMessagePromptTemplate` |
| `"ai"` / `"assistant"` | `AIMessagePromptTemplate` |
| `"system"` | `SystemMessagePromptTemplate` |
| `"placeholder"` | `MessagesPlaceholder(optional=True)` |

### MessagesPlaceholder

```python
MessagesPlaceholder("history")              # 필수 (없으면 KeyError)
MessagesPlaceholder("history", optional=True)  # 없으면 빈 리스트
MessagesPlaceholder("history", n_messages=5)   # 마지막 5개만
```

shorthand: `("placeholder", "{varname}")` → `MessagesPlaceholder(variable_name="varname", optional=True)`

### 단일 변수 template 단축 호출

`input_variables`가 1개이면 dict 대신 값 직접 invoke 가능:
```python
template = ChatPromptTemplate([("system", "You are Carl."), ("human", "{user_input}")])
template.invoke("Hello!")  # → template.invoke({"user_input": "Hello!"})
```

---

## LCEL / Runnable 인터페이스
*Source: `langchain-source-runnable-2026-05-23`*

> **확인됨:** `RunnableLambda`, `RunnableParallel` 등 LCEL 클래스들은 langchain-core `main` 브랜치에 현재도 존재하며 deprecated가 아니다.

### Runnable — 최소 계약

`Runnable(Generic[Input, Output], ABC)` — **유일한 abstract method는 `invoke`** 하나다. 나머지(ainvoke/batch/stream)는 모두 default 구현이 있어 `invoke`만 구현하면 바로 사용 가능.

| 메서드 | 기본 동작 |
|--------|----------|
| `ainvoke` | `invoke`를 executor thread에서 실행. 진짜 async는 override 필요 |
| `batch` | thread pool로 `invoke` 병렬 실행 |
| `stream` | `invoke` 결과 1개를 yield. 진짜 streaming은 override 필요 |
| `__or__` / `pipe` | `RunnableSequence` 생성 |
| `bind` | 인자를 고정한 새 Runnable 반환 |
| `with_config` | 실행 설정 고정 |
| `with_retry` | 예외 시 재시도 (기본 3회) |
| `with_fallbacks` | 실패 시 대안 Runnable |
| `map` | `RunnableEach(bound=self)` 반환 |

### `|` 연산자 → `RunnableSequence`

소스코드 확인:
```python
def __or__(self, other):
    return RunnableSequence(self, coerce_to_runnable(other))
```

`RunnableSequence` 내부 구조: `first: Runnable`, `middle: list[Runnable]`, `last: Runnable`.
각 step의 output이 다음 step의 input으로 전달된다.

### RunnableLambda — callable → Runnable

일반 함수를 LCEL 체인에 연결하는 가장 간단한 방법:
```python
from langchain_core.runnables import RunnableLambda

runnable = RunnableLambda(lambda x: x + 1)
runnable.invoke(1)   # → 2
runnable.batch([1, 2, 3])  # → [2, 3, 4]
```

- `afunc` 없으면 `func`를 thread pool에서 실행
- generator 함수 → streaming 지원 (yield로 chunk 단위 출력)

### RunnableParallel — 병렬 실행

- 출력 타입: `dict[str, Any]` — output keys = input mapping의 keys
- 모든 runnable에 **동일한 input**을 전달하여 **동시 실행** (sync: thread pool, async: asyncio)

```python
from langchain_core.runnables import RunnableParallel

parallel = RunnableParallel({"foo": step1, "bar": step2})
parallel.invoke(input)  # → {"foo": ..., "bar": ...}

# chain 내 dict literal은 자동으로 RunnableParallel로 변환:
chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm
```

### RunnablePassthrough / RunnableAssign / RunnablePick

| 클래스 | 동작 |
|--------|------|
| `RunnablePassthrough` | 입력을 그대로 반환 (identity) |
| `RunnablePassthrough.assign(key=fn)` | 입력 dict에 새 키 추가 → `RunnableAssign` 반환 |
| `RunnablePick("key")` | dict에서 단일 키 값 반환 |
| `RunnablePick(["k1", "k2"])` | dict에서 복수 키 dict 반환 |

### coerce_to_runnable — 자동 변환

| 입력 타입 | 변환 결과 |
|----------|----------|
| `Runnable` 인스턴스 | 그대로 |
| `callable` | `RunnableLambda(thing)` |
| `dict` | `RunnableParallel(thing)` |

chain 내 dict literal(`{"key": step}`)이 자동으로 `RunnableParallel`로 변환되는 이유다.

---

## Superseded Notes

- **Old (Possible Conflict):** 기존 문서에서 LCEL(`Runnable`, `|` 연산자, `RunnableLambda`, `RunnableParallel`)이 deprecated 가능성 있다고 표시
- **New (확인됨):** `langchain-core` main 브랜치 소스코드에 모두 현재 구현 확인. Deprecated 아님.
  Source: `langchain-source-runnable-2026-05-23`

---

---

## 미해결 질문

- `AgentMiddleware`로 에러 핸들링을 구성하는 방법은?
- `init_embeddings("openai:...")` 형식은 구버전 `OpenAIEmbeddings()`와 어떤 차이가 있는가?
- `FewShotPromptTemplate`과 `ExampleSelector`는 어떻게 동작하는가? — Needs Source
- `PipelinePromptTemplate`은 어떻게 여러 템플릿을 연결하는가? — Needs Source
- `PydanticOutputParser`는 LLM 출력 텍스트를 Pydantic 모델로 어떻게 변환하는가? — Needs Source
- `with_structured_output`과 `OutputParser`의 관계는? 내부 구현은? — Needs Source
- `RunnableParallel`의 thread pool thread 수 제한은? `max_concurrency` 옵션이 있는가? — Source: `langchain-source-runnable-2026-05-23`
- `RunnableSequence.invoke` 내부: 각 step 간 에러 처리는 어떻게 되는가? — Source: `langchain-source-runnable-2026-05-23`
- `astream_events`와 `astream_log`의 차이는? — Source: `langchain-source-runnable-2026-05-23`
- `LCEL 체인에서 RunnableConfig`를 통해 실행 시간 설정을 주입하는 방법은? (`configurable` 필드) — Source: `langchain-source-runnable-2026-05-23`

**해소됨 (2026-05-23):**
- ✅ `create_agent`의 내부 구현은? → `libs/langchain_v1/langchain/agents/factory.py`에서 `StateGraph`를 동적 구성하는 팩토리 함수. model node + (조건부) tools node + conditional edges로 루프 구현. 자세한 내용은 [[LangChain create_agent flow]] 참조. (Source: `langchain-source-create-agent-factory-2026-05-23`)
- ✅ `@dynamic_prompt` 데코레이터는 어떤 API인가? → `AgentMiddleware`를 생성하는 데코레이터. 서명 `(request: ModelRequest) -> str | SystemMessage`. `wrap_model_call`로 매 모델 호출 전 시스템 프롬프트 동적 교체. 자세한 내용은 [[Context Engineering]] 참조. (Source: `langchain-source-dynamic-prompt-2026-05-23`)
- ✅ `AgentExecutor`는 도구 호출 루프를 언제 멈출지 결정하는가? → `AgentExecutor`는 deprecated. 현재 `create_agent`에서는 `add_conditional_edges()`의 조건 함수가 `tool_calls` 유무로 결정: 없으면 `END`, 있으면 tools node → model node 루프. (Source: `langchain-source-create-agent-factory-2026-05-23`)

**해소됨 (2026-05-23):**
- ✅ LCEL `RunnableLambda` / `RunnableParallel`은 deprecated인가? → **아니다.** main 브랜치 소스코드에 현재도 존재. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ LCEL `|` 연산자는 내부적으로 어떤 타입을 생성하는가? → `RunnableSequence`. `__or__`가 `RunnableSequence(self, coerce_to_runnable(other))` 반환. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `Runnable` 인터페이스의 최소 계약은? → **`invoke`** 하나만 abstract. 나머지는 default 구현. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `RunnableParallel`은 실제로 동시 실행되는가? → sync: thread pool, async: asyncio로 동시 실행 확인. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `RunnableParallel`의 결과 딕셔너리 키는 어떻게 결정되는가? → input mapping의 keys와 동일. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `PromptTemplate`과 `ChatPromptTemplate`의 차이는? → PromptTemplate: 단일 문자열 포맷, ChatPromptTemplate: 메시지 리스트. 둘 다 Runnable 상속. (Source: `langchain-source-prompts-2026-05-23`)

## 관련 페이지

- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[Memory]]
- [[LangChain Code Map]]
- [[LangChain create_agent flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## 소스

- `langchain-docs-event-streaming-2026-05-18`
- `langchain-docs-messages-2026-05-23`
- `langchain-docs-rag-2026-05-23`
- `langchain-docs-tools-2026-05-23`
- `langchain-source-prompts-2026-05-23`
- `langchain-source-runnable-2026-05-23`
