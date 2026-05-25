"""
Regression test for LangGraph issue #5225
https://github.com/langchain-ai/langgraph/issues/5225

Bug: Pydantic BaseModel + Annotated reducer + Field(default_factory=...)
     ignores default_factory when invoke({}) is called.

Status: Bug confirmed in langgraph 1.2.1 (2026-05-25)
Fix target: state.py attach_node._get_updates
  — coerce dict input through Pydantic schema for START node
  — so invoke({}) behaves identically to invoke(Schema())

How to run:
  pytest reproductions/langgraph_pydantic_default_factory/test_regression.py -v

xfail tests document the bug.  They will pass once the fix is applied
(strict=True means the test suite will error if the bug disappears without
updating the test, which serves as a reminder to flip xfail → normal).
"""

import operator
from typing import Annotated, TypedDict

import pytest
from pydantic import BaseModel, Field

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph


# ── Shared fixtures ────────────────────────────────────────────────────────────


def extend_list(original: list, new: list) -> list:
    return original + new


class OverallState(BaseModel):
    variable: Annotated[list[str], extend_list] = Field(
        default_factory=lambda: ["default"]
    )


def _make_app(checkpointer=None):
    def node(s: OverallState) -> dict:
        return {"variable": ["added"]}

    g = StateGraph(OverallState)
    g.add_node("node", node)
    g.add_edge(START, "node")
    g.add_edge("node", END)
    return g.compile(checkpointer=checkpointer)


# ── Bug cases (xfail until fix is merged) ─────────────────────────────────────


@pytest.mark.xfail(
    reason="issue #5225: invoke({}) ignores Field(default_factory=...) with Annotated reducer",
    strict=True,
)
def test_invoke_empty_dict_applies_default_factory():
    """
    invoke({}) must be equivalent to invoke(Schema()) when all fields have defaults.
    Expected after fix: ['default', 'added']
    Actual now (bug):   ['added']
    """
    result = _make_app().invoke({})
    assert result["variable"] == ["default", "added"]


@pytest.mark.xfail(
    reason="issue #5225: same bug with checkpointer on first invoke({})",
    strict=True,
)
def test_checkpointer_first_invoke_empty_dict():
    """
    First invoke({}) with checkpointer should seed 'variable' with default_factory value.
    Expected after fix: ['default', 'added']
    Actual now (bug):   ['added']
    """
    app = _make_app(checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "t-bug"}}
    result = app.invoke({}, cfg)
    assert result["variable"] == ["default", "added"]


@pytest.mark.xfail(
    reason="issue #5225: partial dict override — missing fields should use default_factory",
    strict=True,
)
def test_invoke_partial_dict_applies_default_factory():
    """
    When invoke() receives a dict that omits some fields, missing fields with
    default_factory should still be seeded correctly.

    Here OverallState only has 'variable', so {} == partial override of zero fields.
    Added to verify the coercion path handles partial dicts too.
    """

    class TwoFieldState(BaseModel):
        items: Annotated[list[str], extend_list] = Field(
            default_factory=lambda: ["init"]
        )
        label: str = "default_label"

    def n(s: TwoFieldState) -> dict:
        return {"items": ["added"]}

    g = StateGraph(TwoFieldState)
    g.add_node("n", n)
    g.add_edge(START, "n")
    g.add_edge("n", END)
    app = g.compile()

    result = app.invoke({"label": "custom"})
    # items not supplied → should fall back to default_factory → ['init', 'added']
    assert result["items"] == ["init", "added"]
    assert result["label"] == "custom"


# ── Workarounds (work now, must continue to work after fix) ───────────────────


def test_invoke_schema_instance_applies_default_factory():
    """Passing an explicit schema instance correctly applies default_factory."""
    result = _make_app().invoke(OverallState())
    assert result["variable"] == ["default", "added"]


def test_invoke_explicit_value_overrides_default():
    """Explicit field value must override default_factory."""
    result = _make_app().invoke({"variable": ["start"]})
    assert result["variable"] == ["start", "added"]


def test_checkpointer_schema_instance_first_invoke():
    """
    With checkpointer, Schema() as first input seeds default_factory correctly.
    """
    app = _make_app(checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "t-workaround"}}
    result = app.invoke(OverallState(), cfg)
    assert result["variable"] == ["default", "added"]


def test_checkpointer_state_readable_after_run():
    """
    After a completed run, get_state() returns the checkpointed state.
    """
    app = _make_app(checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "t-readable"}}
    app.invoke(OverallState(), cfg)
    state = app.get_state(cfg)
    assert state.values["variable"] == ["default", "added"]
    assert state.next == ()  # graph has completed


def test_checkpointer_second_invoke_appends_via_reducer():
    """
    A second invoke(OverallState()) re-seeds the default via the reducer at START.
    Checkpoint: ['default', 'added']
    START node applies extend_list(['default', 'added'], ['default']) = ['default', 'added', 'default']
    Node appends: extend_list([...], ['added']) = ['default', 'added', 'default', 'added']

    This documents that passing OverallState() twice re-applies the default each time,
    which is the correct reducer semantics (not a bug).
    """
    app = _make_app(checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "t-double"}}

    first = app.invoke(OverallState(), cfg)
    assert first["variable"] == ["default", "added"]

    second = app.invoke(OverallState(), cfg)
    assert second["variable"] == ["default", "added", "default", "added"]


# ── TypedDict path — must be unaffected ───────────────────────────────────────


def test_typeddict_invoke_empty_dict_unaffected():
    """TypedDict with Annotated reducer + invoke({}) should work (no regression)."""

    class TDState(TypedDict, total=False):
        items: Annotated[list[str], operator.add]

    def td_node(s: TDState) -> dict:
        return {"items": ["td_added"]}

    g = StateGraph(TDState)
    g.add_node("n", td_node)
    g.add_edge(START, "n")
    g.add_edge("n", END)
    app = g.compile()

    result = app.invoke({})
    assert result["items"] == ["td_added"]


def test_typeddict_explicit_value():
    """TypedDict with explicit value continues to work."""

    class TDState(TypedDict, total=False):
        items: Annotated[list[str], operator.add]

    def td_node(s: TDState) -> dict:
        return {"items": ["td_added"]}

    g = StateGraph(TDState)
    g.add_node("n", td_node)
    g.add_edge(START, "n")
    g.add_edge("n", END)
    app = g.compile()

    result = app.invoke({"items": ["start"]})
    assert result["items"] == ["start", "td_added"]


# ── Multiple Pydantic fields ───────────────────────────────────────────────────


class MultiFieldState(BaseModel):
    items: Annotated[list[str], extend_list] = Field(
        default_factory=lambda: ["x"]
    )
    count: int = 0


def _make_multi_app():
    def multi_node(s: MultiFieldState) -> dict:
        return {"items": ["appended"], "count": s.count + 1}

    g = StateGraph(MultiFieldState)
    g.add_node("n", multi_node)
    g.add_edge(START, "n")
    g.add_edge("n", END)
    return g.compile()


@pytest.mark.xfail(
    reason="issue #5225: default_factory ignored for all reducer fields in multi-field schema",
    strict=True,
)
def test_multi_field_invoke_empty_dict():
    """
    All default_factory values should be applied across multiple fields.
    Expected after fix: items=['x', 'appended'], count=1
    Actual now (bug):   items=['appended'], count=1  — 'x' seeding lost
    """
    result = _make_multi_app().invoke({})
    assert result["items"] == ["x", "appended"]
    assert result["count"] == 1


def test_multi_field_schema_instance_workaround():
    """Schema instance workaround works for multiple fields."""
    result = _make_multi_app().invoke(MultiFieldState())
    assert result["items"] == ["x", "appended"]
    assert result["count"] == 1
