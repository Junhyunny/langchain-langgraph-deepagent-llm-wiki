"""
01_basic_deep_agent.py — Deep Agents 기본 구조 이해

이 파일이 보여주는 것:
  1. create_deep_agent() 시그니처 — 파라미터 이름과 역할
  2. _DeepAgentState 상태 구조 — DeltaChannel로 checkpoint 최적화
  3. 반환 타입 확인 — CompiledStateGraph
  4. system_prompt 조립 순서 — USER → BASE → SUFFIX

주의:
  - 이 예제는 실제 LLM API 키를 필요로 합니다 (ANTHROPIC_API_KEY 또는 OPENAI_API_KEY).
  - API 키 없이 파라미터 구조와 타입만 확인하려면 INSPECT_ONLY = True 로 설정하세요.

실행:
  ANTHROPIC_API_KEY=<your-key> python examples/deepagents_core/01_basic_deep_agent.py
"""

import inspect
import os

from deepagents import create_deep_agent

INSPECT_ONLY = os.getenv("ANTHROPIC_API_KEY") is None and os.getenv("OPENAI_API_KEY") is None


# ---------------------------------------------------------------------------
# 1. create_deep_agent 시그니처 확인
# ---------------------------------------------------------------------------

def inspect_signature() -> None:
    """create_deep_agent 파라미터 목록을 출력한다."""
    sig = inspect.signature(create_deep_agent)
    print("=== create_deep_agent 파라미터 ===")
    for name, param in sig.parameters.items():
        default = param.default if param.default is not inspect.Parameter.empty else "(필수)"
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else "?"
        print(f"  {name}: {annotation} = {default!r}")

    print()
    print("What to notice:")
    print("  - model 은 None 가능하지만 0.5.3부터 deprecated")
    print("  - system_prompt 파라미터명 확인 (instructions= 아님)")
    print("  - middleware=() 는 빈 튜플 기본값 (list 아님)")
    print("  - checkpointer, store 는 LangGraph와 동일 인터페이스")


# ---------------------------------------------------------------------------
# 2. _DeepAgentState 구조 확인
# ---------------------------------------------------------------------------

def inspect_state() -> None:
    """_DeepAgentState가 DeltaChannel을 어떻게 사용하는지 확인한다."""
    from deepagents.graph import _DeepAgentState  # type: ignore[import]

    print("=== _DeepAgentState 어노테이션 ===")
    hints = getattr(_DeepAgentState, "__annotations__", {})
    for field, hint in hints.items():
        print(f"  {field}: {hint}")

    print()
    print("What to notice:")
    print("  - messages 는 Annotated[list[AnyMessage], DeltaChannel(..., snapshot_frequency=50)]")
    print("  - snapshot_frequency=50 → 50 writes마다 전체 스냅샷 생성, 그 사이는 delta만 저장")
    print("  - O(N²) checkpoint 증가 문제를 O(N)으로 해소")


# ---------------------------------------------------------------------------
# 3. 에이전트 생성 — API 키 없으면 건너뜀
# ---------------------------------------------------------------------------

def create_and_inspect_agent() -> None:
    """실제 에이전트를 생성하고 반환 타입을 확인한다."""
    from langgraph.graph.state import CompiledStateGraph

    model = "anthropic:claude-sonnet-4-6"
    if os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        model = "openai:gpt-5.4-mini"

    print(f"=== create_deep_agent(model='{model}') ===")

    agent = create_deep_agent(
        model=model,
        system_prompt="You are a concise test assistant.",
    )

    print(f"  반환 타입: {type(agent).__name__}")
    print(f"  CompiledStateGraph 인스턴스: {isinstance(agent, CompiledStateGraph)}")
    print(f"  config 기본값 recursion_limit: {agent.config.get('recursion_limit')}")

    print()
    print("What to notice:")
    print("  - create_deep_agent 는 create_agent(LangChain) 에 위임 후 .with_config() 로 래핑")
    print("  - recursion_limit=9_999 — LangGraph 기본값(100)과 다름. 긴 agentic loop 허용")
    print("  - CompiledStateGraph 이므로 invoke/stream/get_state 모두 사용 가능")


# ---------------------------------------------------------------------------
# 4. system_prompt 조립 원리 확인
# ---------------------------------------------------------------------------

def inspect_prompt_assembly() -> None:
    """system_prompt 조립 순서 (USER → BASE → SUFFIX)를 시각화한다."""
    from deepagents.graph import BASE_AGENT_PROMPT

    print("=== system_prompt 조립 순서 ===")
    print("  [USER] system_prompt 인자 (None이면 생략)")
    print("  [BASE] BASE_AGENT_PROMPT (기본 deep agent 지침)")
    print("  [SUFFIX] HarnessProfile.system_prompt_suffix (모델별 추가)")
    print()
    print(f"  BASE_AGENT_PROMPT 첫 줄: {BASE_AGENT_PROMPT.splitlines()[0]!r}")
    print(f"  BASE_AGENT_PROMPT 길이: {len(BASE_AGENT_PROMPT)} chars")
    print()
    print("What to notice:")
    print("  - USER 가 항상 앞 → caller 지침이 SDK 기본 지침보다 우선")
    print("  - system_prompt='...' 전달 시: USER + '\\n\\n' + BASE")
    print("  - system_prompt=SystemMessage 전달 시: content_blocks 에 BASE text block append")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("deepagents 버전 확인:", end=" ")
    import importlib.metadata
    print(importlib.metadata.version("deepagents"))
    print()

    inspect_signature()
    print()
    inspect_state()
    print()
    inspect_prompt_assembly()
    print()

    if INSPECT_ONLY:
        print("=== API 키 없음: 에이전트 생성 건너뜀 ===")
        print("  ANTHROPIC_API_KEY 또는 OPENAI_API_KEY 를 설정하면 에이전트도 생성합니다.")
    else:
        create_and_inspect_agent()
