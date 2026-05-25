"""LLMToolSelectorMiddleware: LLM이 관련 도구를 선별해 메인 모델에 전달.

Shows:
- wrap_model_call 훅: 메인 모델 호출 직전 도구 목록 필터링
- 동적 Literal Union 스키마: 도구 설명 포함한 구조화 출력
- max_tools: 최대 선별 도구 수
- always_include: 항상 포함할 도구 (max_tools 제한 외)
- 선별 생략 조건 (도구 없음, always_include만 있음)
- provider dict 도구 보존

Note: 선별 모델의 with_structured_output을 Fake로 대체 (API 불필요).
"""

from __future__ import annotations

from typing import Any, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import LLMToolSelectorMiddleware
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolCall
from langchain_core.tools import BaseTool, tool


class FakeToolChatModel(FakeMessagesListChatModel):
    """메인 에이전트 모델: bind_tools() 무시, 스크립트된 응답 반환."""

    def bind_tools(self, tools: Sequence[BaseTool | Any], **kwargs: Any) -> "FakeToolChatModel":
        return self


class FakeSelectorModel(FakeMessagesListChatModel):
    """선별 전용 모델: with_structured_output이 고정 선택 결과 반환."""

    selection: list[str] = []

    def bind_tools(self, tools: Sequence[BaseTool | Any], **kwargs: Any) -> "FakeSelectorModel":
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:
        """동적 Literal Union 스키마를 받아 고정 선택 결과를 반환하는 mock."""
        selected = self.selection

        class _FakeStructured:
            def invoke(self, messages: Any, **kw: Any) -> dict[str, list[str]]:
                return {"tools": selected}

        return _FakeStructured()


# ─── 도구 정의 (총 5개 — 다양한 역할) ────────────────────────────────────────
@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    return f"Web result for: {query}"


@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))  # noqa: S307
    except Exception:
        return "error"


@tool
def send_email(to: str, body: str) -> str:
    """Send an email to a recipient."""
    return f"Email sent to {to}"


@tool
def read_file(path: str) -> str:
    """Read contents of a file."""
    return f"Contents of {path}"


@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: sunny"


ALL_TOOLS = [search_web, calculator, send_email, read_file, get_weather]


def build_agent(selection: list[str], main_responses: list, **middleware_kwargs: Any):
    selector = FakeSelectorModel(responses=[], selection=selection)
    main_model = FakeToolChatModel(responses=main_responses)
    middleware = LLMToolSelectorMiddleware(model=selector, **middleware_kwargs)
    return create_agent(model=main_model, tools=ALL_TOOLS, middleware=[middleware])


# ─── 1. 기본 도구 선별 ────────────────────────────────────────────────────────
def demo_basic_selection():
    print("=== 1. 기본 선별: LLM이 calculator만 선택 ===")
    agent = build_agent(
        selection=["calculator"],
        main_responses=[AIMessage(content="2+2는 4입니다.")],
    )
    result = agent.invoke({"messages": [HumanMessage("2+2는?")]})
    print(f"  응답: {result['messages'][-1].content!r}")
    print(f"  전체 메시지 수: {len(result['messages'])}")
    print()


# ─── 2. max_tools: 선별 결과를 N개로 제한 ─────────────────────────────────────
def demo_max_tools():
    print("=== 2. max_tools=2: LLM이 3개 선택해도 2개만 사용 ===")
    agent = build_agent(
        selection=["calculator", "search_web", "get_weather"],  # 3개 선택
        main_responses=[AIMessage(content="완료")],
        max_tools=2,  # 실제 사용은 앞 2개만
    )
    result = agent.invoke({"messages": [HumanMessage("계산하고 검색해줘")]})
    print(f"  응답: {result['messages'][-1].content!r}")
    print("  (wrap_model_call 내부에서 3개 → 2개로 잘림)")
    print()


# ─── 3. always_include: 항상 포함 (max_tools 제한 밖) ─────────────────────────
def demo_always_include():
    print("=== 3. always_include: send_email은 선별 없이 항상 포함 ===")
    agent = build_agent(
        selection=["calculator"],           # LLM이 선택
        main_responses=[AIMessage(content="완료")],
        max_tools=1,
        always_include=["send_email"],       # 선별과 무관하게 항상 추가
    )
    result = agent.invoke({"messages": [HumanMessage("계산 후 이메일 보내줘")]})
    print(f"  응답: {result['messages'][-1].content!r}")
    print("  (최종 도구: calculator[선별] + send_email[always_include] = 2개)")
    print()


# ─── 4. 도구 없음 → 선별 생략 ────────────────────────────────────────────────
def demo_no_tools():
    print("=== 4. 도구 없음: wrap_model_call 패스스루 ===")
    main_model = FakeToolChatModel(responses=[AIMessage(content="도구 없이 응답")])
    middleware = LLMToolSelectorMiddleware(model=FakeSelectorModel(responses=[], selection=[]))
    agent = create_agent(model=main_model, tools=[], middleware=[middleware])
    result = agent.invoke({"messages": [HumanMessage("안녕?")]})
    print(f"  응답: {result['messages'][-1].content!r}")
    print("  (_prepare_selection_request → None → handler(request) 그대로)")
    print()


# ─── 5. 동적 스키마 구조 확인 ─────────────────────────────────────────────────
def demo_schema_structure():
    print("=== 5. 동적 Literal Union 스키마 구조 ===")
    from langchain.agents.middleware.tool_selection import _create_tool_selection_response

    type_adapter = _create_tool_selection_response(ALL_TOOLS)
    schema = type_adapter.json_schema()
    print("  스키마 title:", schema.get("title", "N/A"))
    print("  tools 속성:")
    tools_schema = schema.get("properties", {}).get("tools", {})
    items = tools_schema.get("items", {})
    # anyOf가 있으면 각 Literal 도구 이름 출력
    any_of = items.get("anyOf", [])
    for entry in any_of[:3]:  # 처음 3개만 출력
        const = entry.get("const", "?")
        desc = entry.get("description", "")[:30]
        print(f"    Literal[{const!r}] — {desc}")
    print(f"    ... (총 {len(any_of)}개 도구)")
    print()


def main():
    demo_basic_selection()
    demo_max_tools()
    demo_always_include()
    demo_no_tools()
    demo_schema_structure()


if __name__ == "__main__":
    main()
