"""
08_create_agent_fake_tool_loop.py — LangChain create_agent tool loop + middleware hooks

이 파일이 보여주는 것:
  1. API 키 없이 fake chat model로 create_agent().invoke() 실행
  2. AIMessage.tool_calls → ToolNode → ToolMessage → final AIMessage 흐름
  3. AgentMiddleware 6가지 hook 중 주요 hook 실행 순서
  4. create_agent가 매 모델 호출마다 bind_tools()를 다시 호출한다는 점

실행:
  python examples/langchain_core/08_create_agent_fake_tool_loop.py
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelRequest, ModelResponse, ToolCallRequest
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.tools import BaseTool
from pydantic import Field


class ToolCallingFakeModel(FakeMessagesListChatModel):
    """Fake model that records each bind_tools() call."""

    bound_tool_names_by_call: list[list[str]] = Field(default_factory=list)

    def bind_tools(
        self,
        tools: Sequence[BaseTool | dict[str, Any] | Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> "ToolCallingFakeModel":
        self.bound_tool_names_by_call.append(
            [
                getattr(t, "name", None)
                or (t.get("name") if isinstance(t, dict) else str(t))
                for t in tools
            ]
        )
        return self


class TraceMiddleware(AgentMiddleware):
    """Record hook order without changing behavior."""

    def __init__(self, events: list[str]) -> None:
        self.events = events

    @property
    def name(self) -> str:
        return "trace"

    def before_agent(self, state: dict[str, Any], runtime: Any) -> None:
        self.events.append(f"before_agent messages={len(state['messages'])}")

    def before_model(self, state: dict[str, Any], runtime: Any) -> None:
        self.events.append(f"before_model messages={len(state['messages'])}")

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Any,
    ) -> ModelResponse:
        self.events.append(f"wrap_model_call:before tools={len(request.tools)}")
        response = handler(request)
        self.events.append(f"wrap_model_call:after result={type(response.result[0]).__name__}")
        return response

    def after_model(self, state: dict[str, Any], runtime: Any) -> None:
        last = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", None) or []
        self.events.append(f"after_model last={type(last).__name__} tool_calls={len(tool_calls)}")

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Any,
    ) -> ToolMessage:
        self.events.append(f"wrap_tool_call:before tool={request.tool_call['name']}")
        result = handler(request)
        self.events.append(f"wrap_tool_call:after result={type(result).__name__}")
        return result

    def after_agent(self, state: dict[str, Any], runtime: Any) -> None:
        self.events.append(f"after_agent messages={len(state['messages'])}")


@tool
def lookup_topic(topic: str) -> str:
    """Return a short local note about a topic."""
    notes = {
        "LangChain": "LangChain create_agent builds a LangGraph StateGraph.",
        "LangGraph": "LangGraph runs stateful workflows as graph supersteps.",
    }
    return notes.get(topic, f"No note for {topic}")


def print_messages(messages: list[BaseMessage]) -> None:
    for i, message in enumerate(messages, start=1):
        print(f"  {i}. {type(message).__name__}: content={message.content!r}")
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            print(f"     tool_calls={tool_calls}")
        name = getattr(message, "name", None)
        if name:
            print(f"     name={name}")


def main() -> None:
    events: list[str] = []
    model = ToolCallingFakeModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "lookup_topic",
                        "args": {"topic": "LangChain"},
                        "id": "call-lookup-1",
                    }
                ],
            ),
            AIMessage(content="Final: LangChain create_agent builds a LangGraph StateGraph."),
        ]
    )

    agent = create_agent(
        model=model,
        tools=[lookup_topic],
        system_prompt="You are a concise learning assistant.",
        middleware=[TraceMiddleware(events)],
    )

    result = agent.invoke({"messages": [{"role": "user", "content": "What is LangChain create_agent?"}]})

    print("=== result messages ===")
    print_messages(result["messages"])
    print()

    print("=== middleware events ===")
    for i, event in enumerate(events, start=1):
        print(f"  {i}. {event}")
    print()

    print("=== bind_tools calls ===")
    for i, tool_names in enumerate(model.bound_tool_names_by_call, start=1):
        print(f"  {i}. {tool_names}")
    print()

    print("What to notice:")
    print("  - before_agent / after_agent run once outside the loop")
    print("  - before_model / wrap_model_call / after_model run for each model call")
    print("  - wrap_tool_call wraps ToolNode's execution of lookup_topic")
    print("  - bind_tools() runs once per model call, not only at agent construction")


if __name__ == "__main__":
    main()
