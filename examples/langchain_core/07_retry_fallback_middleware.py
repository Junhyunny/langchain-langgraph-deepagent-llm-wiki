"""ModelRetryMiddleware + ToolRetryMiddleware + ModelFallbackMiddleware 직접 실행.

Shows:
- ModelRetryMiddleware: 2번 실패 후 3번째 성공 → max_retries + 1회 시도
- ModelRetryMiddleware on_failure="continue": 재시도 소진 → AIMessage 반환
- ModelRetryMiddleware on_failure="error": 재시도 소진 → 예외 re-raise
- ModelRetryMiddleware retry_on 필터: 특정 예외만 재시도
- ToolRetryMiddleware: 도구 2번 실패 후 성공
- ToolRetryMiddleware tools 필터: 특정 도구만 재시도 대상
- ModelFallbackMiddleware: primary 실패 → fallback 모델 전환

Note: 실제 딜레이 없이 테스트하기 위해 initial_delay=0, jitter=False 사용.
"""

from __future__ import annotations

from typing import Any, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware
from langchain.agents.middleware.model_fallback import ModelFallbackMiddleware
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool, tool


# ─── 헬퍼: 공통 Fake 모델 베이스 ─────────────────────────────────────────────
class FakeBase(FakeMessagesListChatModel):
    """bind_tools를 무시하는 베이스 클래스."""

    def bind_tools(self, tools: Sequence[BaseTool | Any], **kwargs: Any) -> "FakeBase":
        return self


# ─── 1. ModelRetryMiddleware: 2번 실패 후 성공 ───────────────────────────────
def demo_model_retry_success():
    print("=== 1. ModelRetryMiddleware: 2번 실패 후 3번째 성공 ===")
    attempt = {"n": 0}

    class FlakeyModel(FakeBase):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            attempt["n"] += 1
            if attempt["n"] < 3:
                raise ConnectionError(f"일시적 연결 오류 #{attempt['n']}")
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="성공!"))])

    retry = ModelRetryMiddleware(max_retries=3, initial_delay=0, jitter=False)
    agent = create_agent(model=FlakeyModel(responses=[]), tools=[], middleware=[retry])
    result = agent.invoke({"messages": [HumanMessage("안녕")]})

    print(f"  총 시도 횟수: {attempt['n']} (max_retries=3 → 최대 4회 가능)")
    print(f"  결과: {result['messages'][-1].content!r}")
    print()


# ─── 2. ModelRetryMiddleware on_failure="continue" ────────────────────────────
def demo_model_retry_continue():
    print("=== 2. on_failure='continue': 재시도 소진 → AIMessage 반환 ===")
    attempt = {"n": 0}

    class AlwaysFailModel(FakeBase):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            attempt["n"] += 1
            raise ValueError("영구 오류: 모델 API 불가")

    retry = ModelRetryMiddleware(
        max_retries=2, initial_delay=0, jitter=False, on_failure="continue"
    )
    agent = create_agent(model=AlwaysFailModel(responses=[]), tools=[], middleware=[retry])
    result = agent.invoke({"messages": [HumanMessage("실패 테스트")]})

    content = result["messages"][-1].content
    print(f"  총 시도 횟수: {attempt['n']} (초기 1 + 재시도 2 = 3)")
    print(f"  반환된 AIMessage: {content[:60]!r}")
    print(f"  에이전트는 계속 실행됨 (예외 없음)")
    print()


# ─── 3. ModelRetryMiddleware on_failure="error" ───────────────────────────────
def demo_model_retry_error():
    print("=== 3. on_failure='error': 재시도 소진 → 예외 re-raise ===")
    attempt = {"n": 0}

    class AlwaysFailModel(FakeBase):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            attempt["n"] += 1
            raise RuntimeError("치명적 오류")

    retry = ModelRetryMiddleware(
        max_retries=1, initial_delay=0, jitter=False, on_failure="error"
    )
    agent = create_agent(model=AlwaysFailModel(responses=[]), tools=[], middleware=[retry])

    try:
        agent.invoke({"messages": [HumanMessage("에러")]})
        print("  ERROR: 예외가 발생해야 함!")
    except RuntimeError as e:
        print(f"  총 시도 횟수: {attempt['n']} (초기 1 + 재시도 1 = 2)")
        print(f"  예외 발생: {type(e).__name__}({e!r})")
        print(f"  에이전트 중단됨")
    print()


# ─── 4. ModelRetryMiddleware retry_on 필터 ────────────────────────────────────
def demo_model_retry_filter():
    print("=== 4. retry_on 필터: ConnectionError만 재시도, ValueError는 즉시 실패 ===")
    attempt = {"n": 0}

    class SelectiveFailModel(FakeBase):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            attempt["n"] += 1
            raise ValueError("재시도 대상 아님")  # ConnectionError만 재시도 대상

    retry = ModelRetryMiddleware(
        max_retries=3,
        initial_delay=0,
        jitter=False,
        retry_on=(ConnectionError,),     # ValueError는 재시도 안 함
        on_failure="continue",
    )
    agent = create_agent(model=SelectiveFailModel(responses=[]), tools=[], middleware=[retry])
    result = agent.invoke({"messages": [HumanMessage("필터 테스트")]})

    print(f"  총 시도 횟수: {attempt['n']} (ValueError → 즉시 실패, 재시도 없음)")
    print(f"  결과: {result['messages'][-1].content[:50]!r}")
    print()


# ─── 5. ToolRetryMiddleware: 도구 2번 실패 후 성공 ───────────────────────────
def demo_tool_retry_success():
    print("=== 5. ToolRetryMiddleware: 도구 2번 실패 후 3번째 성공 ===")
    tool_attempt = {"n": 0}

    @tool
    def unstable_search(query: str) -> str:
        """Search the web (unstable)."""
        tool_attempt["n"] += 1
        if tool_attempt["n"] < 3:
            raise TimeoutError(f"네트워크 타임아웃 #{tool_attempt['n']}")
        return f"'{query}' 검색 성공"

    class ToolCallerModel(FakeBase):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            # 마지막 메시지가 ToolMessage이면 최종 응답
            if messages and isinstance(messages[-1], ToolMessage):
                msg = AIMessage(content=f"완료: {messages[-1].content}")
            else:
                msg = AIMessage(
                    content="",
                    tool_calls=[{
                        "name": "unstable_search",
                        "args": {"query": "LangChain"},
                        "id": "tc1",
                        "type": "tool_call",
                    }],
                )
            return ChatResult(generations=[ChatGeneration(message=msg)])

    tool_retry = ToolRetryMiddleware(max_retries=3, initial_delay=0, jitter=False)
    agent = create_agent(
        model=ToolCallerModel(responses=[]),
        tools=[unstable_search],
        middleware=[tool_retry],
    )
    result = agent.invoke({"messages": [HumanMessage("LangChain 검색")]})

    print(f"  도구 호출 횟수: {tool_attempt['n']} (2번 실패 + 1번 성공)")
    print(f"  결과: {result['messages'][-1].content!r}")
    print()


# ─── 6. ToolRetryMiddleware tools 필터 ───────────────────────────────────────
def demo_tool_retry_filter():
    print("=== 6. ToolRetryMiddleware tools 필터: 특정 도구만 재시도 ===")
    call_counts = {"retry_target": 0, "no_retry": 0}

    @tool
    def retry_target_tool(x: str) -> str:
        """This tool is in the retry filter."""
        call_counts["retry_target"] += 1
        if call_counts["retry_target"] < 3:
            raise ConnectionError("일시 오류")
        return "retry_target 성공"

    @tool
    def no_retry_tool(x: str) -> str:
        """This tool is NOT in the retry filter."""
        call_counts["no_retry"] += 1
        raise ValueError("재시도 없이 즉시 실패")

    print(f"  tools=['retry_target_tool'] 설정 시:")
    print(f"  - retry_target_tool: 재시도 O")
    print(f"  - no_retry_tool: 재시도 X → 즉시 on_failure 처리")

    # 설정 확인 (실제 실행은 모델 응답 시나리오가 복잡해 생략)
    tool_retry = ToolRetryMiddleware(
        max_retries=3,
        tools=["retry_target_tool"],   # 이 도구만 재시도
        on_failure="continue",
        initial_delay=0,
        jitter=False,
    )
    print(f"  _tool_filter: {tool_retry._tool_filter}")
    print(f"  retry_target_tool 재시도 여부: {tool_retry._should_retry_tool('retry_target_tool')}")
    print(f"  no_retry_tool 재시도 여부: {tool_retry._should_retry_tool('no_retry_tool')}")
    print()


# ─── 7. ModelFallbackMiddleware: primary 실패 → fallback ─────────────────────
def demo_model_fallback():
    print("=== 7. ModelFallbackMiddleware: primary 실패 → fallback 모델 전환 ===")
    attempt_primary = {"n": 0}

    class PrimaryModel(FakeBase):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            attempt_primary["n"] += 1
            raise ConnectionError("Primary 모델 다운")

    class FallbackModel(FakeBase):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content="Fallback 응답!"))])

    fallback = ModelFallbackMiddleware(FallbackModel(responses=[]))
    agent = create_agent(model=PrimaryModel(responses=[]), tools=[], middleware=[fallback])
    result = agent.invoke({"messages": [HumanMessage("안녕")]})

    print(f"  Primary 시도 횟수: {attempt_primary['n']}")
    print(f"  결과 (fallback 응답): {result['messages'][-1].content!r}")
    print()


# ─── 8. ModelFallbackMiddleware: 모두 실패 → 마지막 예외 ──────────────────────
def demo_model_fallback_all_fail():
    print("=== 8. ModelFallbackMiddleware: 모든 모델 실패 → 마지막 예외 re-raise ===")

    class FailModel(FakeBase):
        label: str = "unknown"
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            raise RuntimeError(f"{self.label} 실패")

    class PrimaryFail(FailModel):
        label: str = "Primary"
    class Fallback1Fail(FailModel):
        label: str = "Fallback1"
    class Fallback2Fail(FailModel):
        label: str = "Fallback2"

    fallback = ModelFallbackMiddleware(
        Fallback1Fail(responses=[]),
        Fallback2Fail(responses=[]),
    )
    agent = create_agent(model=PrimaryFail(responses=[]), tools=[], middleware=[fallback])

    try:
        agent.invoke({"messages": [HumanMessage("모두 실패")]})
        print("  ERROR: 예외가 발생해야 함!")
    except RuntimeError as e:
        print(f"  마지막 예외: {e!r}")
        print(f"  (Fallback2의 예외가 re-raise됨)")
    print()


def main():
    demo_model_retry_success()
    demo_model_retry_continue()
    demo_model_retry_error()
    demo_model_retry_filter()
    demo_tool_retry_success()
    demo_tool_retry_filter()
    demo_model_fallback()
    demo_model_fallback_all_fail()


if __name__ == "__main__":
    main()
