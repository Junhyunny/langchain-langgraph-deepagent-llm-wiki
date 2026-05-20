"""Human-in-the-loop interrupt/resume example.

Shows:
- interrupt() pauses graph execution
- Command(resume=...) continues the same thread
- checkpointer keeps the paused state
"""

from __future__ import annotations

from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    topic: str
    draft: str
    approved: bool


def draft_answer(state: State) -> dict[str, str]:
    return {"draft": f"Short note about {state['topic']}"}


def human_review(state: State) -> dict[str, bool]:
    approved = interrupt(
        {
            "question": "Approve this draft?",
            "draft": state["draft"],
        }
    )
    return {"approved": bool(approved)}


def publish(state: State) -> dict[str, str]:
    status = "published" if state["approved"] else "rejected"
    return {"draft": f"{state['draft']} [{status}]"}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("draft", draft_answer)
    graph.add_node("review", human_review)
    graph.add_node("publish", publish)

    graph.add_edge(START, "draft")
    graph.add_edge("draft", "review")
    graph.add_edge("review", "publish")
    graph.add_edge("publish", END)

    return graph.compile(checkpointer=InMemorySaver())


def main() -> None:
    app = build_graph()
    config = {"configurable": {"thread_id": "interrupt-demo"}}

    first = app.invoke(
        {"topic": "LangGraph interrupts", "draft": "", "approved": False},
        config=config,
    )
    print("first result:", first)

    paused = app.get_state(config)
    print("paused next:", paused.next)
    print("paused tasks:", paused.tasks)

    resumed = app.invoke(Command(resume=True), config=config)
    print("resumed result:", resumed)


if __name__ == "__main__":
    main()
