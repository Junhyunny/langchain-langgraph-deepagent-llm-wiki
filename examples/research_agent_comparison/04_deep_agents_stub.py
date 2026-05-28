"""
04. Deep Agents create_deep_agent — 실행 가능한 구조 검사 예제

이 예제는 research_agent_comparison 시리즈에서 Deep Agents 쪽 API 표면을
확인하기 위한 파일이다.

API 키가 없으면 네트워크 호출 없이 다음만 확인한다.
  - 설치된 deepagents 버전
  - create_deep_agent 공개 시그니처
  - research agent를 만들 때 넘기는 주요 인자

`RUN_DEEPAGENTS_EXAMPLE=1`과 provider API 키가 있으면 실제 agent.invoke()까지
시도한다. 기본 모델은 OpenAI 키가 있으면 `openai:gpt-5.4-mini`, Anthropic 키만
있으면 `anthropic:claude-sonnet-4-6`을 사용한다.
"""

from __future__ import annotations

import inspect
import os
from typing import Any

import deepagents
from deepagents import create_deep_agent
from langchain.tools import tool


@tool
def lookup_topic(topic: str) -> str:
    """Return a small static research note for a topic."""
    notes = {
        "python gil": "The GIL serializes Python bytecode execution in CPython; it matters for CPU-bound threads.",
        "langgraph": "LangGraph is a runtime for stateful, durable, graph-shaped agent workflows.",
        "deep agents": "Deep Agents packages a long-running agent harness around LangChain/LangGraph primitives.",
    }
    return notes.get(topic.lower(), f"No local note for: {topic}")


def choose_model() -> str | None:
    if os.getenv("OPENAI_API_KEY"):
        return "openai:gpt-5.4-mini"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic:claude-sonnet-4-6"
    return None


def print_inspection() -> None:
    sig = inspect.signature(create_deep_agent)
    params = ["model", "tools", "system_prompt", "middleware", "subagents", "skills", "memory", "checkpointer"]

    print("=== Deep Agents 구조 검사 ===")
    print(f"deepagents version: {deepagents.__version__}")
    print()
    print("create_deep_agent 주요 파라미터:")
    for name in params:
        p = sig.parameters[name]
        print(f"  - {name}: default={p.default!r}, annotation={p.annotation}")

    print()
    print("이 예제의 research agent 구성:")
    print("  - tools=[lookup_topic]")
    print("  - system_prompt='You are a careful research assistant.'")
    print("  - memory/middleware/subagents는 명시하지 않음")
    print("  - Deep Agents 내부에서 filesystem, todo, summarization, task 계층이 추가됨")


def maybe_run_agent(model: str) -> None:
    agent = create_deep_agent(
        model=model,
        tools=[lookup_topic],
        system_prompt="You are a careful research assistant. Use tools when they help.",
    )
    result: dict[str, Any] = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Use the available tool and explain LangGraph in one sentence.",
                }
            ]
        }
    )
    print()
    print("=== invoke 결과 ===")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    print_inspection()

    model = choose_model()
    if os.getenv("RUN_DEEPAGENTS_EXAMPLE") != "1":
        print()
        print("실제 LLM 호출은 건너뜀: RUN_DEEPAGENTS_EXAMPLE=1 설정 시 실행")
    elif model is None:
        print()
        print("실제 LLM 호출은 건너뜀: OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 필요")
    else:
        maybe_run_agent(model)
