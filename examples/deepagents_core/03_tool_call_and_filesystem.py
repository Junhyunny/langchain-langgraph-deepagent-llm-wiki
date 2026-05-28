"""
03_tool_call_and_filesystem.py — Deep Agents 실제 invoke/tool/filesystem 흐름

이 파일이 보여주는 것:
  1. API 키 없이도 fake chat model로 create_deep_agent().invoke() 실행
  2. 사용자 정의 tool 호출 → ToolMessage → 최종 AIMessage 흐름
  3. built-in write_file tool 호출 → StateBackend files state 갱신
  4. non-sandbox StateBackend에서는 execute tool이 모델에 bind되기 전에 필터링됨

주의:
  - 실제 LLM 품질을 보는 예제가 아니라, Deep Agents 런타임 경로를 검증하는 예제입니다.
  - 모델 응답은 ToolCallingFakeModel에 미리 넣어둔 AIMessage 순서대로 반환됩니다.

실행:
  python examples/deepagents_core/03_tool_call_and_filesystem.py
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from deepagents import create_deep_agent
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import Field


class ToolCallingFakeModel(FakeMessagesListChatModel):
    """Fake model that supports bind_tools() enough for LangChain agents."""

    bound_tool_names: list[str] = Field(default_factory=list)

    def bind_tools(
        self,
        tools: Sequence[BaseTool | dict[str, Any] | Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> "ToolCallingFakeModel":
        self.bound_tool_names = [
            getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else str(t))
            for t in tools
        ]
        return self


@tool
def record_finding(topic: str, note: str) -> str:
    """Record one research finding."""
    return f"recorded:{topic}:{note}"


def print_messages(messages: list[BaseMessage]) -> None:
    for i, message in enumerate(messages, start=1):
        tool_calls = getattr(message, "tool_calls", None)
        name = getattr(message, "name", None)
        status = getattr(message, "status", None)
        print(f"  {i}. {type(message).__name__}: content={message.content!r}")
        if tool_calls:
            print(f"     tool_calls={tool_calls}")
        if name:
            print(f"     name={name}")
        if status:
            print(f"     status={status}")


def run_custom_tool_example() -> None:
    print("=== 1. 사용자 정의 tool 호출 ===")
    model = ToolCallingFakeModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "record_finding",
                        "args": {
                            "topic": "LangGraph",
                            "note": "durable graph runtime",
                        },
                        "id": "call-record-1",
                    }
                ],
            ),
            AIMessage(content="Final: LangGraph is a durable graph runtime."),
        ]
    )
    agent = create_deep_agent(
        model=model,
        tools=[record_finding],
        system_prompt="You are a careful research assistant.",
        checkpointer=InMemorySaver(),
    )

    config = {"configurable": {"thread_id": "deepagents-custom-tool-demo"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Research LangGraph."}]},
        config=config,
    )

    print_messages(result["messages"])
    print()
    print("bound tools:")
    print(f"  {model.bound_tool_names}")
    print()


def run_filesystem_example() -> None:
    print("=== 2. built-in write_file + StateBackend files state ===")
    model = ToolCallingFakeModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "write_file",
                        "args": {
                            "file_path": "/notes/langgraph.md",
                            "content": "LangGraph = durable graph runtime",
                        },
                        "id": "call-write-1",
                    }
                ],
            ),
            AIMessage(content="Final: wrote /notes/langgraph.md."),
        ]
    )
    agent = create_deep_agent(
        model=model,
        system_prompt="You are a careful file-writing assistant.",
        checkpointer=InMemorySaver(),
    )

    config = {"configurable": {"thread_id": "deepagents-filesystem-demo"}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "Write a short LangGraph note."}]},
        config=config,
    )
    state = agent.get_state(config=config)

    print_messages(result["messages"])
    print()
    print("bound tools:")
    print(f"  {model.bound_tool_names}")
    print()
    print("checkpointed files state:")
    print(f"  {state.values.get('files')}")
    print()
    print("What to notice:")
    print("  - write_file은 실제 로컬 파일이 아니라 LangGraph state의 files 채널을 갱신")
    print("  - 기본 StateBackend는 non-sandbox라 execute tool이 bound tools에서 빠짐")


if __name__ == "__main__":
    run_custom_tool_example()
    print()
    run_filesystem_example()
