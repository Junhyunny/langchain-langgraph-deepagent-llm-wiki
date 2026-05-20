"""Checkpointing and state history example.

Shows:
- compile(checkpointer=...)
- thread_id as checkpoint key
- reducer-backed state accumulation
- get_state() and get_state_history()
"""

from __future__ import annotations

from operator import add
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    topic: str
    notes: Annotated[list[str], add]


def collect_docs(state: State) -> dict[str, list[str]]:
    return {"notes": [f"docs:{state['topic']}"]}


def read_source(state: State) -> dict[str, list[str]]:
    return {"notes": [f"source:{state['topic']}"]}


def summarize(state: State) -> dict[str, list[str]]:
    joined = " + ".join(state["notes"])
    return {"notes": [f"summary:{joined}"]}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("collect_docs", collect_docs)
    graph.add_node("read_source", read_source)
    graph.add_node("summarize", summarize)

    graph.add_edge(START, "collect_docs")
    graph.add_edge("collect_docs", "read_source")
    graph.add_edge("read_source", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile(checkpointer=InMemorySaver())


def main() -> None:
    app = build_graph()
    config = {"configurable": {"thread_id": "checkpoint-demo"}}

    result = app.invoke(
        {"topic": "LangGraph checkpointing", "notes": []},
        config=config,
    )
    print("final:", result)

    current = app.get_state(config)
    print("current checkpoint:", current.config["configurable"]["checkpoint_id"])
    print("current next:", current.next)

    print("\nhistory, newest first:")
    for idx, snapshot in enumerate(app.get_state_history(config), start=1):
        checkpoint_id = snapshot.config["configurable"]["checkpoint_id"]
        print(f"{idx}. id={checkpoint_id} next={snapshot.next} values={snapshot.values}")


if __name__ == "__main__":
    main()
