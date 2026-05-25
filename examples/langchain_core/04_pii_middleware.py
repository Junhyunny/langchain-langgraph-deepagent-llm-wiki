"""PIIMiddleware: 사용자/AI/도구 메시지에서 PII 탐지 및 처리.

Shows:
- apply_to_input=True: 사용자 메시지 PII 리댁션 (기본값)
- apply_to_output=True: AI 응답 PII 리댁션
- apply_to_tool_results=True: Tool 결과 PII 필터링
- strategy: redact / mask / hash / block 4가지
- 커스텀 detector (regex 문자열)
- @hook_config(can_jump_to=["end"]): block 전략 시 에이전트 종료

Note: PIIMiddleware는 regex/rule 기반 → LLM API 불필요.
"""

from __future__ import annotations

from typing import Any, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware
from langchain.agents.middleware._redaction import PIIDetectionError
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolCall, ToolMessage
from langchain_core.tools import BaseTool, tool


class FakeToolChatModel(FakeMessagesListChatModel):
    """FakeMessagesListChatModel that accepts bind_tools() without error."""

    def bind_tools(self, tools: Sequence[BaseTool | Any], **kwargs: Any) -> "FakeToolChatModel":
        return self  # pre-scripted responses ignore tool schemas


@tool
def get_user_info(user_id: str) -> str:
    """Get user info by ID — returns data that may contain PII."""
    return f"User {user_id}: contact john.doe@example.com, IP 192.168.1.100"


def _make_agent(*middlewares, responses: list):
    model = FakeToolChatModel(responses=responses)
    return create_agent(model=model, tools=[get_user_info], middleware=list(middlewares))


# ─── 1. apply_to_input: 사용자 메시지의 이메일 리댁션 ─────────────────────────
def demo_redact_input():
    print("=== 1. apply_to_input: 이메일 리댁션 ===")
    agent = _make_agent(
        PIIMiddleware("email", strategy="redact"),
        responses=[AIMessage(content="정보를 확인했습니다.")],
    )
    result = agent.invoke({
        "messages": [HumanMessage("Please contact john@example.com for support.")]
    })
    messages = result["messages"]
    # before_model이 HumanMessage의 이메일을 리댁션한 뒤 모델에 전달
    human_msg = messages[0]
    print(f"  원본 입력:  'Please contact john@example.com for support.'")
    print(f"  상태 메시지: {human_msg.content!r}")
    # Note: 상태에 저장된 메시지가 리댁션됨
    print(f"  AI 응답:    {messages[-1].content!r}")
    print()


# ─── 2. 4가지 전략 비교 ────────────────────────────────────────────────────────
def demo_strategies():
    print("=== 2. 전략 비교 (email 주소 처리) ===")
    from langchain.agents.middleware._redaction import (
        apply_strategy,
        detect_email,
    )
    content = "Contact alice@company.com or bob@corp.org for details."
    matches = detect_email(content)

    for strategy in ("redact", "mask", "hash"):
        result = apply_strategy(content, matches, strategy)
        print(f"  [{strategy:6s}] {result}")
    print()


# ─── 3. block 전략: PII 탐지 시 에이전트 중단 ─────────────────────────────────
def demo_block():
    print("=== 3. block 전략: PIIDetectionError 발생 ===")
    agent = _make_agent(
        PIIMiddleware("credit_card", strategy="block"),
        responses=[AIMessage(content="처리 완료")],
    )
    try:
        agent.invoke({
            "messages": [HumanMessage("내 카드번호는 4111-1111-1111-1111 입니다.")]
        })
        print("  ⚠️ 에러가 발생하지 않음 (예상치 못한 결과)")
    except Exception as e:
        # block 전략 → PIIDetectionError → 에이전트 "end"로 점프
        print(f"  ✅ 예외 발생: {type(e).__name__}")
        if isinstance(e, PIIDetectionError):
            print(f"  탐지된 타입: {e.pii_type}, 건수: {len(e.matches)}")
        else:
            # PIIDetectionError가 GraphRecursionError 등으로 래핑될 수 있음
            print(f"  메시지: {str(e)[:80]}")
    print()


# ─── 4. apply_to_output: AI 응답의 IP 주소 마스킹 ─────────────────────────────
def demo_output_mask():
    print("=== 4. apply_to_output: AI 응답의 IP 마스킹 ===")
    agent = _make_agent(
        PIIMiddleware("ip", strategy="mask", apply_to_input=False, apply_to_output=True),
        responses=[AIMessage(content="서버 주소는 192.168.1.1 입니다.")],
    )
    result = agent.invoke({"messages": [HumanMessage("서버 IP를 알려줘")]})
    ai_msg = result["messages"][-1]
    print(f"  AI 원본:    '서버 주소는 192.168.1.1 입니다.'")
    print(f"  AI 저장됨:  {ai_msg.content!r}")
    print()


# ─── 5. apply_to_tool_results: Tool 결과의 이메일 해시 ────────────────────────
def demo_tool_results():
    print("=== 5. apply_to_tool_results: Tool 결과 이메일 해시화 ===")
    agent = _make_agent(
        PIIMiddleware(
            "email",
            strategy="hash",
            apply_to_input=False,
            apply_to_tool_results=True,
        ),
        responses=[
            AIMessage(
                content="",
                tool_calls=[ToolCall(name="get_user_info", args={"user_id": "u123"}, id="c1")],
            ),
            AIMessage(content="사용자 정보를 확인했습니다."),
        ],
    )
    result = agent.invoke({"messages": [HumanMessage("사용자 u123 정보 조회해줘")]})
    # ToolMessage에서 이메일이 해시로 교체됨
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    if tool_msgs:
        print(f"  Tool 원본:  'User u123: contact john.doe@example.com, IP 192.168.1.100'")
        print(f"  Tool 저장됨: {tool_msgs[0].content!r}")
    print()


# ─── 6. 커스텀 regex detector ────────────────────────────────────────────────
def demo_custom_detector():
    print("=== 6. 커스텀 detector: API 키 탐지 ===")
    agent = _make_agent(
        PIIMiddleware("api_key", detector=r"sk-[a-zA-Z0-9]{10,}", strategy="redact"),
        responses=[AIMessage(content="키가 제거되었습니다.")],
    )
    result = agent.invoke({
        "messages": [HumanMessage("내 API 키는 sk-abcdefghij1234 입니다.")]
    })
    human_msg = result["messages"][0]
    print(f"  원본:  'sk-abcdefghij1234'")
    print(f"  저장됨: {human_msg.content!r}")
    print()


def main():
    demo_redact_input()
    demo_strategies()
    demo_block()
    demo_output_mask()
    demo_tool_results()
    demo_custom_detector()


if __name__ == "__main__":
    main()
