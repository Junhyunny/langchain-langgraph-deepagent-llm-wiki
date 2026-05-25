"""LangGraph ToolNode: InjectedState / InjectedStore / 병렬 실행.

학습 목표:
1. ToolNode가 AIMessage.tool_calls를 자동으로 처리하는 방식
2. InjectedState: 도구 함수가 현재 그래프 state를 런타임에 받는 방법
3. InjectedStore: 도구가 long-term store에 직접 접근하는 방법
4. 병렬 도구 호출: 여러 tool_call → ThreadPoolExecutor 동시 실행
5. handle_tool_error: 예외 → ToolMessage(error text) 자동 변환

내부 동작 (LangGraph ToolNode flow.md에서 확인):
  AIMessage.tool_calls 개수 = ToolMessage 개수
  ToolNode._func() → _inject_tool_args() → tool.invoke(args)
  InjectedState / InjectedStore 인자는 LLM schema에서 제거됨 (stripped_args)
  병렬 실행: _run_one() 를 ThreadPoolExecutor.map()으로 동시 실행
"""

from __future__ import annotations

from typing import Annotated, Any

from langchain_core.messages import AIMessage, ToolCall, ToolMessage
from langchain_core.tools import BaseTool, tool
from langchain_core.tools import InjectedToolCallId
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import InjectedState, InjectedStore, ToolNode
from langgraph.store.memory import InMemoryStore
from typing_extensions import TypedDict


# ─────────────────────────────────────────────────────────────────────────────
# 공통 상태
# ─────────────────────────────────────────────────────────────────────────────


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_level: str          # InjectedState로 도구에 전달할 값


# ─────────────────────────────────────────────────────────────────────────────
# 실험 1: 기본 ToolNode — AIMessage.tool_calls 자동 처리
# ─────────────────────────────────────────────────────────────────────────────


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b


@tool
def greet(name: str) -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


def experiment_1_basic_toolnode() -> None:
    print("\n" + "=" * 60)
    print("실험 1: 기본 ToolNode — AIMessage.tool_calls 자동 처리")
    print("=" * 60)

    tool_node = ToolNode([multiply, greet])

    # 수동으로 AIMessage with tool_calls 생성 (LLM 없이 시뮬레이션)
    ai_msg = AIMessage(
        content="",
        tool_calls=[
            ToolCall(name="multiply", args={"a": 6, "b": 7}, id="tc_1"),
            ToolCall(name="greet",    args={"name": "LangGraph"}, id="tc_2"),
        ],
    )

    state_in = {"messages": [ai_msg]}
    result = tool_node.invoke(state_in)

    print("  입력: AIMessage with 2 tool_calls")
    print("  출력 messages:")
    for msg in result["messages"]:
        assert isinstance(msg, ToolMessage)
        print(f"    tool_call_id={msg.tool_call_id!r}: content={msg.content!r}")

    print("\n  확인 포인트:")
    print("  - tool_call_id가 AIMessage의 id와 정확히 대응")
    print("  - 2개 tool_call → 2개 ToolMessage (병렬 실행)")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 2: InjectedState — 도구가 그래프 state 읽기
# ─────────────────────────────────────────────────────────────────────────────


@tool
def personalized_greeting(
    name: str,
    state: Annotated[AgentState, InjectedState],  # LLM schema에서 제외됨
) -> str:
    """Return a greeting personalized to the user's level."""
    level = state.get("user_level", "beginner")
    if level == "expert":
        return f"Greetings, esteemed colleague {name}. Welcome to the advanced track."
    return f"Hi {name}! Welcome aboard. You're on the {level} track."


def experiment_2_injected_state() -> None:
    print("\n" + "=" * 60)
    print("실험 2: InjectedState — 도구가 그래프 state를 런타임에 읽기")
    print("=" * 60)

    tool_node = ToolNode([personalized_greeting])

    # LLM이 보는 스키마: name만 있음 (state는 제거됨)
    schema = personalized_greeting.get_input_schema().model_json_schema()
    print(f"  LLM이 보는 스키마 properties: {list(schema['properties'].keys())}")
    print(f"  (state 필드가 schema에서 제외됨 확인)")

    # beginner 레벨 state
    ai_msg = AIMessage(
        content="",
        tool_calls=[ToolCall(name="personalized_greeting", args={"name": "Alice"}, id="tc_g")],
    )
    state_beginner: AgentState = {
        "messages": [ai_msg],
        "user_level": "beginner",
    }
    result = tool_node.invoke(state_beginner)
    print(f"\n  beginner: {result['messages'][0].content!r}")

    # expert 레벨 state
    ai_msg2 = AIMessage(
        content="",
        tool_calls=[ToolCall(name="personalized_greeting", args={"name": "Bob"}, id="tc_g2")],
    )
    state_expert: AgentState = {
        "messages": [ai_msg2],
        "user_level": "expert",
    }
    result2 = tool_node.invoke(state_expert)
    print(f"  expert:   {result2['messages'][0].content!r}")

    print("\n  확인 포인트:")
    print("  - InjectedState는 LLM schema에 노출되지 않음 → 보안/안정성")
    print("  - 도구 내부에서 state['user_level'] 등 어떤 키도 접근 가능")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 3: InjectedStore — 도구가 long-term store에 접근
# ─────────────────────────────────────────────────────────────────────────────


@tool
def save_note(
    key: str,
    content: str,
    tool_call_id: Annotated[str, InjectedToolCallId],   # 자동 주입
    store: Annotated[Any, InjectedStore],               # store 자동 주입
) -> ToolMessage:
    """Save a note to the long-term store."""
    namespace = ("notes",)
    store.put(namespace, key, {"content": content})
    return ToolMessage(
        content=f"Saved note '{key}': {content}",
        tool_call_id=tool_call_id,
    )


@tool
def retrieve_note(
    key: str,
    store: Annotated[Any, InjectedStore],  # store 자동 주입
) -> str:
    """Retrieve a note from the long-term store."""
    namespace = ("notes",)
    item = store.get(namespace, key)
    if item is None:
        return f"No note found for key '{key}'"
    return f"Note '{key}': {item.value['content']}"


def experiment_3_injected_store() -> None:
    print("\n" + "=" * 60)
    print("실험 3: InjectedStore — 도구가 long-term store에 접근")
    print("=" * 60)

    store = InMemoryStore()
    tool_node = ToolNode([save_note, retrieve_note], store=store)

    # step 1: save_note
    ai_save = AIMessage(
        content="",
        tool_calls=[
            ToolCall(name="save_note", args={"key": "project_goal", "content": "LangGraph deep dive"}, id="tc_s"),
        ],
    )
    state_save: AgentState = {"messages": [ai_save], "user_level": "beginner"}
    result_save = tool_node.invoke(state_save)
    print(f"  save: {result_save['messages'][0].content!r}")

    # step 2: retrieve_note
    ai_get = AIMessage(
        content="",
        tool_calls=[
            ToolCall(name="retrieve_note", args={"key": "project_goal"}, id="tc_r"),
        ],
    )
    state_get: AgentState = {"messages": [ai_get], "user_level": "beginner"}
    result_get = tool_node.invoke(state_get)
    print(f"  retrieve: {result_get['messages'][0].content!r}")

    print("\n  확인 포인트:")
    print("  - InjectedStore도 LLM schema에서 제외됨")
    print("  - InjectedToolCallId: tool_call_id를 도구가 직접 ToolMessage에 넣을 때 사용")
    print("  - store는 InMemoryStore / PostgresStore 등 교체 가능")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 4: handle_tool_error — 예외 → ToolMessage 자동 변환
# ─────────────────────────────────────────────────────────────────────────────


@tool
def divide(a: float, b: float) -> float:
    """Divide a by b. Raises ZeroDivisionError if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def experiment_4_handle_tool_error() -> None:
    print("\n" + "=" * 60)
    print("실험 4: handle_tool_error — 예외 → ToolMessage 자동 변환")
    print("=" * 60)

    # handle_tool_error=True: 예외 메시지를 content로 하는 ToolMessage 반환
    tool_node_safe = ToolNode([divide], handle_tool_errors=True)

    ai_bad = AIMessage(
        content="",
        tool_calls=[ToolCall(name="divide", args={"a": 10.0, "b": 0.0}, id="tc_div")],
    )
    state_bad: AgentState = {"messages": [ai_bad], "user_level": "beginner"}

    # handle_tool_errors=False (기본값): 예외 그대로 전파
    tool_node_unsafe = ToolNode([divide], handle_tool_errors=False)

    print("  [handle_tool_errors=True] 에러 케이스:")
    result_safe = tool_node_safe.invoke(state_bad)
    msg = result_safe["messages"][0]
    print(f"    status={msg.status!r}, content={msg.content!r}")

    print("\n  [handle_tool_errors=False] 에러 케이스 (예외 발생):")
    ai_bad2 = AIMessage(
        content="",
        tool_calls=[ToolCall(name="divide", args={"a": 10.0, "b": 0.0}, id="tc_div2")],
    )
    state_bad2: AgentState = {"messages": [ai_bad2], "user_level": "beginner"}
    try:
        tool_node_unsafe.invoke(state_bad2)
    except ValueError as e:
        print(f"    ValueError 발생: {e}")

    print("\n  [handle_tool_errors=True] 정상 케이스:")
    ai_ok = AIMessage(
        content="",
        tool_calls=[ToolCall(name="divide", args={"a": 10.0, "b": 2.0}, id="tc_div3")],
    )
    state_ok: AgentState = {"messages": [ai_ok], "user_level": "beginner"}
    result_ok = tool_node_safe.invoke(state_ok)
    print(f"    result: {result_ok['messages'][0].content!r}")

    print("\n  확인 포인트:")
    print("  - handle_tool_errors=True: 에러도 ToolMessage로 감싸 그래프 계속 실행")
    print("  - msg.status='error' 로 에러 여부 확인 가능")
    print("  - handle_tool_errors=callable: 사용자 정의 에러 메시지 생성 가능")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 5: ToolNode를 그래프에 통합 (전체 루프, LLM 없이)
# ─────────────────────────────────────────────────────────────────────────────


def experiment_5_toolnode_in_graph() -> None:
    print("\n" + "=" * 60)
    print("실험 5: ToolNode를 그래프에 통합")
    print("  LLM 없이 수동 AIMessage로 도구 호출 루프 시뮬레이션")
    print("=" * 60)

    # model_node: pre-scripted AIMessage 순서대로 반환
    responses = [
        AIMessage(content="", tool_calls=[
            ToolCall(name="multiply", args={"a": 3, "b": 8}, id="c1"),
        ]),
        AIMessage(content="The answer is 24."),  # final answer (no tool_calls)
    ]
    response_iter = iter(responses)

    def model_node(state: AgentState) -> dict:
        return {"messages": [next(response_iter)]}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode([multiply, greet])

    g = StateGraph(AgentState)
    g.add_node("model", model_node)
    g.add_node("tools", tool_node)
    g.add_edge(START, "model")
    g.add_conditional_edges("model", should_continue, {"tools": "tools", END: END})
    g.add_edge("tools", "model")
    app = g.compile()

    result = app.invoke({"messages": [("user", "What is 3 × 8?")], "user_level": "beginner"})

    print("  실행된 메시지 순서:")
    for msg in result["messages"]:
        label = type(msg).__name__
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            calls = [f"{tc['name']}({tc['args']})" for tc in msg.tool_calls]
            print(f"    {label}: [tool_calls] {calls}")
        elif isinstance(msg, ToolMessage):
            print(f"    {label}: id={msg.tool_call_id!r}, content={msg.content!r}")
        else:
            print(f"    {label}: {msg.content!r}")

    print("\n  확인 포인트:")
    print("  - model → tools → model 루프: tool_calls 있으면 계속, 없으면 종료")
    print("  - ToolNode는 AIMessage.tool_calls → ToolMessage 변환을 자동 처리")
    print("  - should_continue 패턴이 LangGraph agent 루프의 핵심")


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    experiment_1_basic_toolnode()
    experiment_2_injected_state()
    experiment_3_injected_store()
    experiment_4_handle_tool_error()
    experiment_5_toolnode_in_graph()

    print("\n" + "=" * 60)
    print("학습 정리")
    print("=" * 60)
    print("  기본 ToolNode : AIMessage.tool_calls → ToolMessage 자동 변환")
    print("  InjectedState : state를 LLM schema 노출 없이 도구에 전달")
    print("  InjectedStore : long-term store 직접 접근")
    print("  handle_tool_errors: 예외를 ToolMessage로 감싸 그래프 유지")
    print("  그래프 통합   : model→tools→model 루프 = 에이전트의 핵심 패턴")


if __name__ == "__main__":
    main()
