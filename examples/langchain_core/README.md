# LangChain core examples

LLM API key 없이 LangChain의 핵심 실행 모델을 이해하기 위한 작은 예제들이다.

## Setup

```bash
# 저장소 루트에서 실행
source .venv/bin/activate
```

## Examples

```bash
python examples/langchain_core/01_lcel_chain.py
python examples/langchain_core/02_tool_calling.py
python examples/langchain_core/03_create_react_agent.py
python examples/langchain_core/08_create_agent_fake_tool_loop.py
```

## What To Notice

### 01 — LCEL chain
- `RunnableLambda(fn)` → 일반 함수에 Runnable 인터페이스(`invoke`, `batch`, `stream`)를 부여한다.
- `a | b` → `RunnableSequence`를 반환한다. `|`는 Python `__or__` 연산자를 오버라이딩한 것.
- `RunnableParallel(key=runnable, ...)` → 각 runnable을 동시 실행하고 결과를 dict로 모은다.

### 02 — @tool decorator
- `@tool` → `StructuredTool`을 반환한다. 함수 이름이 `name`, docstring이 `description`이 된다.
- `args_schema.model_json_schema()` → LLM에 전달되는 함수 스키마가 이 JSON이다.
- 에이전트의 tool 실행 흐름: `AIMessage.tool_calls[i]` → `tool.invoke(args)` → `ToolMessage(content, tool_call_id=id)`
- `tool_call_id`는 반드시 대응하는 `AIMessage.tool_calls[i]["id"]`와 일치해야 한다.

### 03 — create_agent
- `create_agent(model, tools, checkpointer)` → `CompiledStateGraph`를 반환한다.
- `langchain.agents.create_agent`가 현재 공식 API. `langgraph.prebuilt.create_react_agent`는 deprecated.
- state 안의 `messages` 리스트는 매 턴마다 누적된다 (`add_messages` reducer).
- `checkpointer=InMemorySaver()` + `thread_id` → 멀티 턴 대화 연속성 확보.
- `FakeToolChatModel.bind_tools()` no-op 패턴: `create_agent`는 내부적으로 `model.bind_tools(tools)`를 호출한다.

### 08 — create_agent fake tool loop
- fake chat model로 `create_agent().invoke()`의 실제 LangGraph 실행 경로를 검증한다.
- `AIMessage.tool_calls` → `ToolNode` → `ToolMessage` → 다음 model call → final `AIMessage` 순서를 확인한다.
- `AgentMiddleware` hook 순서: `before_agent`/`after_agent`는 루프 밖에서 1회, `before_model`/`wrap_model_call`/`after_model`은 모델 호출마다 실행된다.
- `bind_tools()`는 agent 생성 시점이 아니라 매 model call 시점에 실행된다.
