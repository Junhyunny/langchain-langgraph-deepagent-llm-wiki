"""
LangGraph Issue #5225 — Minimum reproduction
https://github.com/langchain-ai/langgraph/issues/5225

Bug: Pydantic BaseModel with Annotated reducer + Field(default_factory=...)
     ignores default_factory when invoke({}) is called.
"""

from typing import Annotated

from pydantic import BaseModel, Field

from langgraph.graph import END, START, StateGraph


def extend_list(original: list, new: list) -> list:
    return original + new


class OverallState(BaseModel):
    variable: Annotated[list[str], extend_list] = Field(
        default_factory=lambda: ["default"]
    )


def node(s: OverallState) -> dict:
    return {"variable": ["added"]}


graph = StateGraph(OverallState)
graph.add_node("node", node)
graph.add_edge(START, "node")
graph.add_edge("node", END)
app = graph.compile()

if __name__ == "__main__":
    print("=== Issue #5225 Reproduction ===\n")

    # Bug case: default_factory is ignored
    result_empty = app.invoke({})
    print(f"invoke({{}}):")
    print(f"  Got:      {result_empty['variable']}")
    print(f"  Expected: ['default', 'added']")
    print(f"  Bug?      {result_empty['variable'] != ['default', 'added']}\n")

    # Workaround: pass explicit OverallState instance
    result_explicit = app.invoke(OverallState())
    print(f"invoke(OverallState()):")
    print(f"  Got:      {result_explicit['variable']}")
    print(f"  Expected: ['default', 'added']")
    print(f"  OK?       {result_explicit['variable'] == ['default', 'added']}\n")

    # Normal: pass explicit initial value
    result_value = app.invoke({"variable": ["start"]})
    print(f"invoke({{'variable': ['start']}}):")
    print(f"  Got:      {result_value['variable']}")
    print(f"  Expected: ['start', 'added']")
    print(f"  OK?       {result_value['variable'] == ['start', 'added']}")
