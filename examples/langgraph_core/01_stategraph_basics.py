"""Minimal StateGraph example.

Shows:
- typed shared state
- node functions returning partial state updates
- conditional edges
- compile() -> invoke()
"""

from __future__ import annotations

import re
from typing import Literal

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    question: str
    route: Literal["math", "text"]
    answer: str


def classify(state: State) -> dict[str, str]:
    has_number = bool(re.search(r"\d", state["question"]))
    return {"route": "math" if has_number else "text"}


def route_after_classify(state: State) -> Literal["math", "text"]:
    return state["route"]


def answer_math(state: State) -> dict[str, str]:
    numbers = [int(x) for x in re.findall(r"\d+", state["question"])]
    return {"answer": f"sum={sum(numbers)}"}


def answer_text(state: State) -> dict[str, str]:
    words = state["question"].split()
    return {"answer": f"word_count={len(words)}"}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("classify", classify)
    graph.add_node("math", answer_math)
    graph.add_node("text", answer_text)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {"math": "math", "text": "text"},
    )
    graph.add_edge("math", END)
    graph.add_edge("text", END)

    return graph.compile()


def main() -> None:
    app = build_graph()

    examples = [
        {"question": "add 2 and 40", "route": "text", "answer": ""},
        {"question": "explain state graphs briefly", "route": "text", "answer": ""},
    ]

    for item in examples:
        result = app.invoke(item)
        print(result)


if __name__ == "__main__":
    main()
