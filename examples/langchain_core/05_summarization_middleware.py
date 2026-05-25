"""SummarizationMiddleware: 긴 대화 히스토리를 LLM으로 자동 요약.

Shows:
- trigger=("messages", N): N개 이상 메시지가 쌓이면 요약
- keep=("messages", K): 최근 K개 메시지 보존
- before_model 훅: 모델 호출 직전 메시지 교체
- 요약 결과는 HumanMessage로 삽입됨
- 매 trigger마다 반복 동작

Note: summarizer model (요약 전용)과 main agent model 분리.
      summarizer는 실제 API 대신 Fake LLM으로 대체.
"""

from __future__ import annotations

from typing import Any, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool, tool
from langgraph.checkpoint.memory import InMemorySaver


class FakeToolChatModel(FakeMessagesListChatModel):
    """FakeMessagesListChatModel that accepts bind_tools() without error."""

    def bind_tools(self, tools: Sequence[BaseTool | Any], **kwargs: Any) -> "FakeToolChatModel":
        return self


@tool
def calculator(expression: str) -> str:
    """Evaluate a simple math expression."""
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307
    except Exception:
        return "error"


def build_agent(main_responses: list, summarizer_responses: list):
    """Agent with SummarizationMiddleware.

    trigger=("messages", 3): 메시지 3개 이상이면 요약 발동
    keep=("messages", 1):    최근 1개 메시지만 보존
    """
    summarizer = FakeMessagesListChatModel(responses=summarizer_responses)
    main_model = FakeToolChatModel(responses=main_responses)

    return create_agent(
        model=main_model,
        tools=[calculator],
        middleware=[
            SummarizationMiddleware(
                model=summarizer,
                trigger=("messages", 3),
                keep=("messages", 1),
            )
        ],
        checkpointer=InMemorySaver(),
    )


def _print_messages(label: str, messages: list) -> None:
    print(f"  [{label}] 총 {len(messages)}개:")
    for m in messages:
        prefix = type(m).__name__[:6]
        content = str(m.content)[:50]
        extra = ""
        if hasattr(m, "additional_kwargs") and m.additional_kwargs.get("lc_source"):
            extra = " 🔖 [요약]"
        print(f"    {prefix}: {content!r}{extra}")


def main() -> None:
    config = {"configurable": {"thread_id": "demo"}}

    agent = build_agent(
        main_responses=[
            AIMessage(content="1+2는 3입니다."),
            AIMessage(content="4+5는 9입니다."),
            AIMessage(content="10+20는 30입니다."),
        ],
        summarizer_responses=[
            # trigger가 발동될 때마다 요약 모델이 호출됨
            AIMessage(content="이전 대화: 사용자가 덧셈 계산 질문을 두 번 했음."),
            AIMessage(content="이전 요약 + 추가 대화: 3번의 계산 질문이 있었음."),
        ],
    )

    # ─── Turn 1 ───────────────────────────────────────────────────────────────
    print("=== Turn 1: 첫 번째 대화 (요약 미발동) ===")
    r1 = agent.invoke({"messages": [HumanMessage("1+2는?")]}, config=config)
    _print_messages("Turn 1 결과", r1["messages"])
    # 2개 메시지 < 3 → 요약 발동 안 됨
    print()

    # ─── Turn 2 ───────────────────────────────────────────────────────────────
    print("=== Turn 2: 두 번째 대화 → 요약 발동! ===")
    # before_model 시점: [H1, A1] + 새 H2 = 3개 메시지 → trigger(3) 발동
    r2 = agent.invoke({"messages": [HumanMessage("4+5는?")]}, config=config)
    _print_messages("Turn 2 결과", r2["messages"])
    # 예상: [SummaryHumanMsg, H2, A2] — 3개 (H1+A1 → 요약, H2 보존)
    has_summary = any(
        getattr(m, "additional_kwargs", {}).get("lc_source") == "summarization"
        for m in r2["messages"]
    )
    print(f"  요약 메시지 삽입됨: {has_summary}")
    print()

    # ─── Turn 3 ───────────────────────────────────────────────────────────────
    print("=== Turn 3: 세 번째 대화 → 요약 재발동 ===")
    # before_model 시점: [SummaryH, H2, A2] + 새 H3 = 4개 → trigger(3) 재발동
    r3 = agent.invoke({"messages": [HumanMessage("10+20는?")]}, config=config)
    _print_messages("Turn 3 결과", r3["messages"])
    print()

    # ─── 요약 메시지 내용 확인 ──────────────────────────────────────────────────
    print("=== 요약 메시지 내용 확인 ===")
    for msg in r3["messages"]:
        if getattr(msg, "additional_kwargs", {}).get("lc_source") == "summarization":
            print(f"  요약 내용: {msg.content!r}")

    # ─── 핵심 포인트 ────────────────────────────────────────────────────────────
    print()
    print("=== 핵심 포인트 ===")
    print("  1. trigger=None 이면 요약 절대 안 됨 (기본값 주의!)")
    print("  2. 요약 결과는 HumanMessage로 삽입됨 (AIMessage 아님)")
    print("  3. 요약 전용 모델을 가볍게 설정하면 비용 절감 가능")
    print("  4. keep이 작을수록 요약이 더 자주 발동됨")


if __name__ == "__main__":
    main()
