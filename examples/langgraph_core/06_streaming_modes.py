"""LangGraph 스트리밍 모드 실험.

학습 목표:
1. values 모드: 각 step 후 전체 state 스냅샷 (가장 무거움)
2. updates 모드: 변경된 노드 이름 + 변경분만 (가장 흔하게 사용)
3. custom 모드: StreamWriter로 노드 내부에서 임의 이벤트 방출
4. checkpoints 모드: checkpoint 생성 이벤트만 (InMemorySaver 필요)
5. tasks 모드: 태스크 시작/종료 이벤트 (실행 추적에 유용)
6. messages 모드: LLM 토큰 단위 스트림 (FakeMessagesListChatModel 사용)
7. 복수 모드 동시 소비: stream_mode=[...] 리스트 전달 → (mode, payload) tuple

내부 동작 (Event Streaming.md에서 확인):
  stream(stream_mode=X)
    → Pregel._stream() / GraphRunStream
    → 각 mode에 따라 다른 transformer가 이벤트를 걸러냄
  interrupt 이벤트는 updates 모드에서 {'__interrupt__': (...)} 형태로 보임
"""

from __future__ import annotations

from typing import Any, Sequence

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import StreamWriter
from typing_extensions import TypedDict


# ─────────────────────────────────────────────────────────────────────────────
# 공통 상태 및 그래프 (LLM 없이 작동)
# ─────────────────────────────────────────────────────────────────────────────


class PipelineState(TypedDict):
    topic: str
    outline: str
    draft: str


def plan_node(state: PipelineState) -> dict[str, str]:
    return {"outline": f"[outline] how to explain {state['topic']}"}


def write_node(state: PipelineState) -> dict[str, str]:
    return {"draft": f"[draft based on] {state['outline']}"}


def build_pipeline(checkpointer=None) -> Any:
    g = StateGraph(PipelineState)
    g.add_node("plan", plan_node)
    g.add_node("write", write_node)
    g.add_edge(START, "plan")
    g.add_edge("plan", "write")
    g.add_edge("write", END)
    return g.compile(checkpointer=checkpointer)


INPUT = {"topic": "LangGraph streaming", "outline": "", "draft": ""}


# ─────────────────────────────────────────────────────────────────────────────
# 실험 1: stream_mode="values"
# ─────────────────────────────────────────────────────────────────────────────


def experiment_1_values() -> None:
    print("\n" + "=" * 60)
    print("실험 1: stream_mode='values'")
    print("  각 step 후 전체 state 스냅샷 yield")
    print("=" * 60)

    app = build_pipeline()
    for i, chunk in enumerate(app.stream(INPUT, stream_mode="values"), 1):
        keys = {k: v[:30] + "..." if isinstance(v, str) and len(v) > 30 else v
                for k, v in chunk.items()}
        print(f"  chunk {i}: {keys}")

    print("\n  확인 포인트:")
    print("  - 매 step 후 전체 state를 받음 (chunk 수 = node 수 + 1)")
    print("  - 첫 chunk는 START 이전 상태 (입력 그대로)")
    print("  - state가 클수록 비효율 → updates 모드 선호")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 2: stream_mode="updates"
# ─────────────────────────────────────────────────────────────────────────────


def experiment_2_updates() -> None:
    print("\n" + "=" * 60)
    print("실험 2: stream_mode='updates' (기본 권장 모드)")
    print("  변경된 노드 이름 + 변경분만 yield")
    print("=" * 60)

    app = build_pipeline()
    for chunk in app.stream(INPUT, stream_mode="updates"):
        # chunk 형식: {"node_name": {changed_key: new_value, ...}}
        for node, changes in chunk.items():
            print(f"  node={node!r:10s} changes={changes}")

    print("\n  확인 포인트:")
    print("  - 변경된 키만 포함 → 대규모 state에서 효율적")
    print("  - interrupt 이벤트: {'__interrupt__': (Interrupt(...),)}")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 3: stream_mode="custom" (StreamWriter)
# ─────────────────────────────────────────────────────────────────────────────


class ReportState(TypedDict):
    items: list[str]
    report: str


def process_items_node(state: ReportState, writer: StreamWriter) -> dict[str, str]:
    """StreamWriter로 노드 내부의 진행 상황을 실시간 방출."""
    results = []
    for item in state["items"]:
        # 처리 중 진행 상황을 실시간으로 전송
        writer({"progress": f"처리 중: {item}"})
        results.append(item.upper())
    writer({"summary": f"총 {len(results)}개 처리 완료"})
    return {"report": ", ".join(results)}


def experiment_3_custom() -> None:
    print("\n" + "=" * 60)
    print("실험 3: stream_mode='custom' (StreamWriter)")
    print("  노드 내부에서 임의 이벤트를 직접 방출")
    print("=" * 60)

    g = StateGraph(ReportState)
    g.add_node("process", process_items_node)
    g.add_edge(START, "process")
    g.add_edge("process", END)
    app = g.compile()

    items_input = {"items": ["apple", "banana", "cherry"], "report": ""}
    for chunk in app.stream(items_input, stream_mode="custom"):
        # custom 모드: writer()로 방출한 임의 데이터만 수신
        print(f"  custom event: {chunk}")

    print("\n  확인 포인트:")
    print("  - writer(data)로 방출한 값만 custom 모드에서 보임")
    print("  - 노드 반환값(return)은 custom에서 보이지 않음")
    print("  - custom + updates 동시 사용 시: (mode, payload) tuple yield")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 4: stream_mode="checkpoints"
# ─────────────────────────────────────────────────────────────────────────────


def experiment_4_checkpoints() -> None:
    print("\n" + "=" * 60)
    print("실험 4: stream_mode='checkpoints'")
    print("  checkpoint 생성 시 이벤트 (InMemorySaver 필요)")
    print("=" * 60)

    app = build_pipeline(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "ckpt-stream-demo"}}

    checkpoint_count = 0
    for chunk in app.stream(INPUT, config=config, stream_mode="checkpoints"):
        checkpoint_count += 1
        # chunk는 CheckpointTuple-like dict
        step = chunk.get("metadata", {}).get("step", "?")
        source = chunk.get("metadata", {}).get("source", "?")
        print(f"  checkpoint #{checkpoint_count}: step={step}, source={source!r}")

    print(f"\n  총 {checkpoint_count}개 checkpoint 이벤트")
    print("\n  확인 포인트:")
    print("  - checkpointer 없으면 이 모드에서 이벤트 없음")
    print("  - source='loop'(step 실행), source='input'(입력 저장)")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 5: stream_mode="tasks"
# ─────────────────────────────────────────────────────────────────────────────


def experiment_5_tasks() -> None:
    print("\n" + "=" * 60)
    print("실험 5: stream_mode='tasks'")
    print("  각 태스크 시작/종료 이벤트")
    print("=" * 60)

    app = build_pipeline()
    for chunk in app.stream(INPUT, stream_mode="tasks"):
        # chunk: TaskChunk-like dict
        task_name = chunk.get("name", "?")
        task_type = "시작" if chunk.get("result") is None and "error" not in chunk else "완료"
        print(f"  task={task_name!r:10s} type={task_type}")

    print("\n  확인 포인트:")
    print("  - 태스크 시작과 완료가 각각 별도 이벤트로 옴")
    print("  - 에러 발생 시 error 필드 포함")
    print("  - debug 모드 = checkpoints + tasks 결합")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 6: 복수 모드 동시 소비
# ─────────────────────────────────────────────────────────────────────────────


def experiment_6_multi_mode() -> None:
    print("\n" + "=" * 60)
    print("실험 6: 복수 모드 동시 소비 stream_mode=['updates', 'custom']")
    print("  (mode, payload) tuple로 yield")
    print("=" * 60)

    # custom 이벤트가 있는 그래프 재사용
    g = StateGraph(ReportState)
    g.add_node("process", process_items_node)
    g.add_edge(START, "process")
    g.add_edge("process", END)
    app = g.compile()

    items_input = {"items": ["x", "y"], "report": ""}
    for mode, chunk in app.stream(items_input, stream_mode=["updates", "custom"]):
        print(f"  mode={mode!r:10s} chunk={chunk}")

    print("\n  확인 포인트:")
    print("  - 리스트 전달 시 (mode, payload) tuple yield")
    print("  - subgraphs=True + 리스트 → (namespace, mode, payload) triple")


# ─────────────────────────────────────────────────────────────────────────────
# 실험 7: stream_mode="messages" (FakeMessagesListChatModel)
# ─────────────────────────────────────────────────────────────────────────────


class MessagesState(TypedDict):
    messages: list


class FakeStreamingChatModel(FakeMessagesListChatModel):
    """FakeMessagesListChatModel that accepts bind_tools() as no-op."""

    def bind_tools(self, tools: Sequence[BaseTool | Any], **kwargs: Any) -> "FakeStreamingChatModel":
        return self


def experiment_7_messages() -> None:
    print("\n" + "=" * 60)
    print("실험 7: stream_mode='messages'")
    print("  LLM 토큰 단위 스트림 (FakeMessagesListChatModel)")
    print("=" * 60)

    # Fake LLM: 미리 정해진 응답 반환
    model = FakeStreamingChatModel(responses=[
        AIMessage(content="LangGraph streaming is powerful."),
    ])

    def llm_node(state: MessagesState) -> dict:
        response = model.invoke(state["messages"])
        return {"messages": [response]}

    g = StateGraph(MessagesState)
    g.add_node("llm", llm_node)
    g.add_edge(START, "llm")
    g.add_edge("llm", END)
    app = g.compile()

    msg_count = 0
    for chunk in app.stream(
        {"messages": [HumanMessage(content="What is LangGraph streaming?")]},
        stream_mode="messages",
    ):
        # chunk: (message_chunk_or_message, metadata_dict)
        msg_chunk, metadata = chunk
        msg_count += 1
        node = metadata.get("langgraph_node", "?")
        print(f"  [{node}] {type(msg_chunk).__name__}: {repr(msg_chunk.content)[:60]}")

    print(f"\n  총 {msg_count}개 메시지 이벤트")
    print("\n  확인 포인트:")
    print("  - (message_or_chunk, metadata) tuple yield")
    print("  - metadata['langgraph_node']로 어느 노드에서 온 메시지인지 확인")
    print("  - 실제 LLM은 AIMessageChunk 단위로 여러 번 yield")


# ─────────────────────────────────────────────────────────────────────────────
# main
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    experiment_1_values()
    experiment_2_updates()
    experiment_3_custom()
    experiment_4_checkpoints()
    experiment_5_tasks()
    experiment_6_multi_mode()
    experiment_7_messages()

    print("\n" + "=" * 60)
    print("학습 정리")
    print("=" * 60)
    print("  values    : 매 step 후 전체 state — 무거움, 디버깅용")
    print("  updates   : 변경분만 — 가장 실용적, interrupt 이벤트 포함")
    print("  custom    : StreamWriter — 노드 내부 진행상황 실시간 방출")
    print("  checkpoints: checkpoint 이벤트 — InMemorySaver 필요")
    print("  tasks     : 태스크 라이프사이클 — 실행 추적")
    print("  messages  : LLM 토큰 스트림 — 실제 LLM 필요")
    print("  리스트    : 복수 모드 → (mode, payload) tuple")


if __name__ == "__main__":
    main()
