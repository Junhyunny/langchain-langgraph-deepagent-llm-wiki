---
type: code_map
framework: LangChain
status: partial
confidence: medium
last_reviewed: 2026-05-24
sources:
  - langchain-source-prompts-2026-05-23
  - langchain-source-runnable-2026-05-23
  - langchain-source-tools-2026-05-23
  - langchain-source-create-agent-factory-2026-05-23
  - langchain-source-bind-tools-function-calling-2026-05-23
  - langchain-venv-factory-read-2026-05-24
---

# LangChain Code Map

## 요약

이 페이지는 LangChain 저장소 구조를 매핑한다. 소스 코드를 읽을 때 탐색 가이드로 사용한다.

## 저장소

- **저장소:** `https://github.com/langchain-ai/langchain`
- **주요 패키지 루트:** `libs/core/langchain_core/`

## 핵심 패키지 구조

```
libs/
  core/
    langchain_core/
      runnables/          ← LCEL 핵심 (Runnable, RunnableSequence, RunnableParallel...)
        base.py           ← Runnable 추상 클래스
        passthrough.py    ← RunnablePassthrough, RunnableAssign, RunnablePick
        parallel.py       ← RunnableParallel
        lambda_.py        ← RunnableLambda
        branch.py         ← RunnableBranch
        utils.py          ← coerce_to_runnable
      tools/              ← Tool 시스템 핵심
        base.py           ← BaseTool, ToolException, create_schema_from_function, InjectedToolArg
        structured.py     ← StructuredTool, from_function classmethod
        convert.py        ← @tool 데코레이터 구현
        simple.py         ← Tool (string→string 단순 도구)
      messages/           ← 메시지 시스템
        base.py           ← BaseMessage
        human.py          ← HumanMessage
        ai.py             ← AIMessage, AIMessageChunk
        tool.py           ← ToolMessage, ToolCall, ToolOutputMixin
        system.py         ← SystemMessage
      prompts/            ← 프롬프트 템플릿
        base.py           ← BasePromptTemplate
        prompt.py         ← PromptTemplate (StringPromptTemplate 상속)
        chat.py           ← ChatPromptTemplate
        few_shot.py       ← FewShotPromptTemplate
        pipeline.py       ← PipelinePromptTemplate
  langchain_v1/
    langchain/
      agents/
        factory.py        ← create_agent (현재 공식 API, LangGraph StateGraph 기반)
  langchain/              ← 구버전 패키지 (master에서 부분 유지)
    agents/               ← create_react_agent, AgentExecutor (deprecated)
```

## 핵심 파일별 역할

### `langchain_core/tools/base.py`
*Source: `langchain-source-tools-2026-05-23`*

| 심볼 | 역할 |
|------|------|
| `BaseTool` | 모든 tool의 추상 기반. `RunnableSerializable` 상속 |
| `create_schema_from_function` | 함수 시그니처 → Pydantic schema 변환 (pydantic validate_arguments 사용) |
| `ToolException` | tool 에러를 agent에 전달하는 전용 예외 |
| `InjectedToolArg` | LLM schema에서 제외되는 runtime 주입 인자 annotation |
| `InjectedToolCallId` | tool_call_id를 runtime 주입할 때 사용 |
| `_format_output` | tool 출력 → `ToolMessage` 래핑 |
| `FILTERED_ARGS` | `("run_manager", "callbacks")` — schema에서 항상 제외 |

### `langchain_core/tools/structured.py`
*Source: `langchain-source-tools-2026-05-23`*

| 심볼 | 역할 |
|------|------|
| `StructuredTool` | `@tool` 기본 반환 타입. `func`/`coroutine` 필드 보유 |
| `StructuredTool.from_function` | `@tool` 내부에서 호출되는 실제 생성 진입점 |

### `langchain_core/tools/convert.py`
*Source: `langchain-source-tools-2026-05-23`*

| 심볼 | 역할 |
|------|------|
| `tool()` | `@tool` 데코레이터 구현. `StructuredTool.from_function` 위임 |
| `convert_runnable_to_tool` | `Runnable` → `BaseTool` 변환 |

### `langchain_core/runnables/base.py`
*Source: `langchain-source-runnable-2026-05-23`*

| 심볼 | 역할 |
|------|------|
| `Runnable` | 추상 기반. `invoke`만 abstract |
| `RunnableSequence` | `|` 연산자 결과. `steps` 리스트로 순서 실행 |
| `RunnableLambda` | callable → Runnable 변환 |
| `RunnableParallel` | 병렬 실행. sync=thread pool, async=asyncio |

### `langchain_core/prompts/chat.py`
*Source: `langchain-source-prompts-2026-05-23`*

| 심볼 | 역할 |
|------|------|
| `ChatPromptTemplate` | 메시지 리스트 기반 프롬프트 |
| `MessagesPlaceholder` | 메시지 히스토리 삽입 (optional, n_messages 제한 가능) |

## 실행 흐름 요약

```
@tool 함수 정의
    │
    └─→ StructuredTool (args_schema 자동 생성)
            │
            └─→ LLM.bind_tools([tool]) → tool_call_schema JSON 전달
                    │
                    LLM이 AIMessage(tool_calls=[...]) 반환
                    │
                    └─→ BaseTool.invoke(ToolCall)
                                │
                                └─→ _run() → _format_output → ToolMessage
```

### `langchain_v1/langchain/agents/factory.py`
*Source: `langchain-source-create-agent-factory-2026-05-23`, `.venv` 직접 확인 2026-05-24*

| 심볼 | 역할 |
|------|------|
| `create_agent` | 현재 공식 agent 생성 API. StateGraph 동적 구성 후 compile 반환 |
| `_get_bound_model` | 매 model 호출 시 `bind_tools()` 실행 + AutoStrategy 처리 (런타임) |
| `_execute_model_sync` | 동기 model 호출. `_get_bound_model` → `model_.invoke` |
| `_execute_model_async` | 비동기 model 호출. `_get_bound_model` → `model_.ainvoke` |
| `model_node` | graph에 추가되는 model 노드 함수 |
| `_chain_model_call_handlers` | middleware model call handler 체이닝 (sync) |
| `_chain_async_model_call_handlers` | middleware model call handler 체이닝 (async) |
| `_chain_tool_call_wrappers` | middleware tool call wrapper 체이닝 |
| `_resolve_schemas` | middleware state schema + base_state 병합 |
| `ResponseFormat` | `ToolStrategy | ProviderStrategy | AutoStrategy` 유형 |

**검증됨 (v0.6.3 .venv 직접 확인):**

1. **초기화 시점 작업 (create_agent 호출 시):**
   - `init_chat_model(model)` — model이 string일 때만 실행 (provider 패키지 import 포함)
   - middleware hook 감지 (클래스 비교 방식, 전체 middleware 순회)
   - `ToolNode` 생성 (available_tools + middleware_tools 결합)
   - `_resolve_schemas(state_schemas)` — middleware schema 병합
   - `StateGraph` 생성 + 모든 노드/엣지 추가
   - `graph.compile()` — LangGraph compile (edge 검증, Pregel 생성)
   - `.with_config(recursion_limit=9_999)` 래핑

2. **런타임 시점 작업 (매 model 호출 시):**
   - `_get_bound_model(request)` 호출
   - `bind_tools(final_tools, ...)` 실행 — **bind_tools는 init에서 하지 않음**
   - AutoStrategy → ProviderStrategy/ToolStrategy 자동 결정 (model capability 기반)

3. **초기화 시간 차이 원인:**
   - `model` 인수가 **string**이면 `init_chat_model()` 호출 → provider 패키지 import 발생 (느림)
   - `model` 인수가 **BaseChatModel 인스턴스**이면 skip (빠름)
   - **middleware 수가 많을수록** hook 감지, schema 병합, 노드 추가 작업 증가
   - `create_deep_agent` = `create_agent` + 13개 middleware → compile 시 노드 수 대폭 증가

4. **recursion_limit=9_999:**
   - `create_agent` 자체가 line 1665에서 직접 설정 (Deep Agents 전용이 아님)
   - Deep Agents는 `create_agent` 반환값에 `.with_config(recursion_limit=9_999)`를 한 번 더 적용 (동일 값)

5. **`create_tool_calling_agent` + `AgentExecutor` 패턴**: deprecated, 현재 master에 없음

### `langchain_core/utils/function_calling.py`
*Source: `langchain-source-bind-tools-function-calling-2026-05-23`*

| 심볼 | 역할 |
|------|------|
| `convert_to_openai_tool` | tool → OpenAI API tool schema 변환 진입점 |
| `convert_to_openai_function` | 다양한 입력 타입(BaseTool/Pydantic/callable/dict) → OpenAI function 형식 |
| `_format_tool_to_openai_function` | BaseTool 전용 변환. tool_call_schema → OpenAI function |

### `langchain_core/language_models/chat_models.py`
*Source: `langchain-source-bind-tools-function-calling-2026-05-23`*

| 심볼 | 역할 |
|------|------|
| `BaseChatModel` | 모든 chat model의 추상 기반. `_generate` abstract |
| `BaseChatModel.bind_tools` | 추상 메서드(NotImplementedError). provider별 구현 필요 |

**검증됨:** `bind_tools`는 추상이므로 실제 변환은 provider 패키지에 있다. OpenAI → `BaseChatOpenAI.bind_tools` → `convert_to_openai_tool`.

## 실행 흐름 요약 (업데이트)

```
@tool 함수 정의
    │
    └─→ StructuredTool (args_schema 자동 생성)
            │
            └─→ create_agent(model, tools=[tool])
                    │  factory.py: StateGraph 구성
                    │  · model node
                    │  · tools node (ToolNode)
                    │  · conditional edges
                    │
                    LLM API 호출 시:
                    tool.tool_call_schema
                        → bind_tools([tool])           (provider)
                        → convert_to_openai_tool()     (langchain_core)
                        → {"type": "function", ...}
                    │
                    LLM이 AIMessage(tool_calls=[...]) 반환
                    │
                    └─→ ToolNode → BaseTool.invoke(ToolCall)
                                        │
                                        └─→ _run() → _format_output → ToolMessage
```

## 불명확한 영역

- `_chain_model_call_handlers()`의 구체적인 체이닝 구현은?
- `create_react_agent`(LangGraph prebuilt)과 `create_agent`(LangChain)의 차이는?
- Anthropic provider `bind_tools`의 변환 경로는?
- `init_chat_model("provider:model_name")` 형식의 문자열 파싱 규칙은?

## 관련 페이지

- [[LangChain]]
- [[LangChain create_agent flow]]
- [[Tool Calling]]

## 소스

- `langchain-source-tools-2026-05-23`
- `langchain-source-runnable-2026-05-23`
- `langchain-source-prompts-2026-05-23`
- `langchain-source-create-agent-factory-2026-05-23`
- `langchain-source-bind-tools-function-calling-2026-05-23`
- `langchain-venv-factory-read-2026-05-24`
