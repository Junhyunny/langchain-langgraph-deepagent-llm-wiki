---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - deepagents-docs-context-engineering-2026-05-18
  - langchain-source-prompts-2026-05-23
  - langchain-source-runnable-2026-05-23
  - langchain-source-bind-tools-function-calling-2026-05-23
  - langchain-source-dynamic-prompt-2026-05-23
---

# Context Engineering

## 요약

Context Engineering은 출력의 품질과 신뢰성을 극대화하기 위해 LLM에 전달되는 컨텍스트(시스템 프롬프트, 대화 히스토리, 도구 설명, 주입된 데이터)를 의도적으로 구성하는 실천이다.

## 중요한 이유

컨텍스트는 LLM의 주요 입력이다. 컨텍스트가 잘못 구성되면 agent 동작도 나빠진다. 프레임워크가 컨텍스트를 어떻게 구축하는지 이해하는 것은 agent 실패를 진단하고 agent 품질을 개선하는 데 필수적이다.

## 핵심 개념

- **시스템 프롬프트** — LLM에 대한 최상위 지시문
- **메시지 히스토리** — 이전 대화 턴
- **도구 스키마 주입** — 컨텍스트에 추가되는 도구 설명
- **RAG 주입** — 컨텍스트에 추가되는 검색 문서
- **컨텍스트 윈도우** — LLM이 처리할 수 있는 최대 토큰 수
- **컨텍스트 압축** — 컨텍스트 윈도우에 맞추기 위해 히스토리를 줄이는 것
- **Progressive Disclosure** — 필요할 때만 컨텍스트를 로드하는 전략 (Deep Agents의 skills 패턴)

## 프레임워크별 동작

### LangChain
*Source: `langchain-source-prompts-2026-05-23`, `langchain-source-runnable-2026-05-23`*

**프롬프트 조립:**

- `ChatPromptTemplate.from_messages()`로 system prompt + 대화 히스토리 + 사용자 입력을 조립
- `MessagesPlaceholder("history")`로 대화 히스토리 삽입 위치를 지정
- `partial_variables`로 날짜·언어 등 고정값을 미리 바인딩하면 runtime에 전달할 변수 수 감소

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Today is {date}."),
    MessagesPlaceholder("history"),
    ("human", "{input}"),
])
```

**LCEL 컨텍스트 파이프라인:**

- `PromptTemplate`·`ChatPromptTemplate` 모두 `Runnable` 상속 → LCEL `|` 체인에 그대로 연결 가능
- `RunnableParallel`로 여러 컨텍스트 소스(retriever, passthrough 등)를 병렬 조회 후 프롬프트에 주입

```python
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

chain = (
    RunnableParallel({"context": retriever, "question": RunnablePassthrough()})
    | prompt
    | llm
)
```

**동적 시스템 프롬프트 (`@dynamic_prompt`):**
*Source: `langchain-source-dynamic-prompt-2026-05-23`*

- `@dynamic_prompt`는 **`AgentMiddleware`를 생성하는 데코레이터**. 매 모델 호출 전 시스템 프롬프트를 동적으로 교체한다.
- **올바른 서명**: `(request: ModelRequest) -> str | SystemMessage`
- `str` 반환 시 내부적으로 `SystemMessage(content=...)` 로 자동 변환
- `request.override(system_message=...)` 패턴으로 불변 복사본 생성 후 핸들러 위임

```python
from langchain.agents.middleware import dynamic_prompt
from langchain.agents.middleware.types import ModelRequest

@dynamic_prompt
def context_aware_prompt(request: ModelRequest) -> str:
    msg_count = len(request.state["messages"])
    if msg_count > 10:
        return "You are in a long conversation. Be concise."
    return "You are a helpful assistant."

agent = create_agent(model, middleware=[context_aware_prompt])
```

> ⚠️ **문서 오류 주의**: 일부 공식 문서 예제는 `(user_query: str) -> list` 서명을 사용하지만, 이는 실제 `@dynamic_prompt` API가 아니다. 올바른 서명은 위와 같다. (Source: `langchain-source-dynamic-prompt-2026-05-23`)

**도구 스키마 주입 (bind_tools):**
*Source: `langchain-source-bind-tools-function-calling-2026-05-23`*

- `model.bind_tools([tool1, tool2])` 호출 시 각 tool의 schema가 LLM API 요청의 `tools=[]` 파라미터로 주입됨
- 변환 체인:

```
BaseTool.tool_call_schema          ← InjectedToolArg 필드 제외된 args_schema
    ↓
bind_tools([tool])                 ← provider 구현체 (BaseChatOpenAI 등)
    ↓
convert_to_openai_tool(tool)       ← langchain_core/utils/function_calling.py
    ↓
convert_to_openai_function(tool)   ← Anthropic/Bedrock/OpenAI/JSON schema 자동 감지
    ↓
_format_tool_to_openai_function()  ← dict schema or Pydantic model 분기 처리
    ↓
{"type": "function", "function": {"name": ..., "description": ..., "parameters": {...}}}
```

- `BaseChatModel.bind_tools`는 추상 메서드(`NotImplementedError`) — 실제 변환은 provider 구현체마다 다름
- OpenAI 구현(`BaseChatOpenAI`)은 `convert_to_openai_tool` 공유 유틸 사용
- Anthropic 구현(`langchain_anthropic`)은 별도 변환 경로로 `{"input_schema": {...}}` 형식 생성
- `tool_choice` 정규화: 이름 → `{"type": "function", "function": {"name": ...}}`, `"any"` → `"required"`

**컨텍스트 압축:**
- *소스 필요* — `ConversationSummaryMemory` 등 요약 기반 압축 기능의 내부 구현 확인 필요

### LangGraph

- 상태(`State`)의 메시지 목록이 LLM 노드에 직접 전달된다
- `add_messages` reducer가 메시지 히스토리 누적을 관리 — ID 기반 중복 제거/업데이트 포함
- 프롬프트는 보통 노드 함수 내부에서 `ChatPromptTemplate`으로 조립된다
- *LangGraph 전용 컨텍스트 압축 메커니즘 소스 필요*

### Deep Agents
*Source: `deepagents-docs-context-engineering-2026-05-18`*

Deep Agents는 5가지 context 타입으로 구분하여 체계적으로 관리한다.

#### 5가지 Context 타입

| Context 타입 | 범위 |
|---|---|
| **Input context** | 정적, 매 실행마다 적용 (startup 시 system prompt 구성) |
| **Runtime context** | 실행 당, 서브에이전트로 자동 전파 |
| **Context compression** | 자동 (offloading + summarization) |
| **Context isolation** | 서브에이전트 단위 (무거운 작업 격리) |
| **Long-term memory** | 스레드 간 영속 (CompositeBackend 필요) |

#### System Prompt 조립 순서 (9단계)

1. Custom `system_prompt` (제공된 경우)
2. Base agent prompt (소스: `graph.py#L37`)
3. To-do list prompt
4. Memory prompt (`memory` 파라미터 제공 시에만)
5. Skills prompt (`skills` 파라미터 제공 시에만)
6. Virtual filesystem prompt
7. Subagent prompt (`task` tool 사용법)
8. 사용자 제공 미들웨어 prompts
9. Human-in-the-loop prompt (`interrupt_on` 설정 시)

#### Memory vs Skills

| | Memory | Skills |
|---|---|---|
| 로드 시점 | **항상** 시스템 프롬프트에 포함 | frontmatter만 읽고, 관련성 판단 시 전체 로드 |
| 패턴 | No progressive disclosure | **Progressive disclosure** |
| 용도 | 항상 필요한 프로젝트 규칙, 선호도 | 상황별 특화 워크플로우 |

#### Context Compression

**Offloading (20,000 tokens threshold):**
- Tool call results > 20,000 tokens → backend에 offload, 파일 경로 + 첫 10줄 preview로 대체
- 세션 컨텍스트 > 85% 도달 → 오래된 tool call inputs 잘라내고 파일 포인터로 대체

**Summarization (85% threshold):**
- 컨텍스트 > `max_input_tokens`의 85% AND offloading 대상 없음 → LLM이 구조화된 요약 생성
- 요약이 전체 대화 히스토리 대체 / 원본은 파일시스템에 보존
- 최근 컨텍스트 10% 유지
- Fallback: 모델 프로파일 불명 시 170,000 tokens / 6 messages 기준

#### Runtime Context

- 모델 프롬프트에 **자동 포함되지 않음** — tool/middleware가 명시적으로 읽어야 함
- `context_schema` (dataclass 또는 TypedDict)로 타입 정의
- `invoke`의 `context` 인자로 전달
- 모든 서브에이전트로 **자동 전파**

#### Long-term Memory

- 기본 filesystem: 단일 스레드 내에서만 영속
- 스레드 간 영속: `CompositeBackend` + `StoreBackend` (LangGraph Store 연동)
- `/memories/` 경로를 `StoreBackend`로 라우팅하는 패턴이 표준

## 미해결 질문

- LangChain, LangGraph에서 컨텍스트 윈도우 초과를 어떻게 처리하는가? (Deep Agents에서만 확인됨) — Needs Source
- ~~도구 설명은 어떤 형식으로 구성되고 주입되는가?~~ → 위 "도구 스키마 주입" 섹션 참조. (Source: `langchain-source-bind-tools-function-calling-2026-05-23`) ✅
- Deep Agents의 `graph.py#L37` base agent prompt는 어떤 내용인가? 커스터마이징 가능한가?
- Skills frontmatter 형식은 무엇이며 agent는 어떻게 관련성을 판단하는가?
- LangChain에서 `RunnableParallel` 병렬 실행 시 thread pool 크기 제한은? — Source: `langchain-source-runnable-2026-05-23`
- `MessagesPlaceholder(optional=True)`와 `optional=False`의 runtime 차이는? (optional=False 시 KeyError) — Source: `langchain-source-prompts-2026-05-23`

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Memory]]
- [[Subagents]]
- [[Tool Calling]]

## 소스

- `deepagents-docs-context-engineering-2026-05-18`
- `langchain-source-prompts-2026-05-23`
- `langchain-source-runnable-2026-05-23`
- `langchain-source-bind-tools-function-calling-2026-05-23`
- `langchain-source-dynamic-prompt-2026-05-23`
