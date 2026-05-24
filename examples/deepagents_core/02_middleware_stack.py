"""
02_middleware_stack.py — Deep Agents 미들웨어 스택 구조 이해

이 파일이 보여주는 것:
  1. create_deep_agent() 가 조립하는 middleware 스택 순서
  2. middleware 각 클래스의 역할
  3. _DeepAgentState 전체 필드 (AgentState 상속 포함)
  4. checkpointer 파라미터 타입 — None | bool | BaseCheckpointSaver

주의:
  - API 키 없이 실행 가능한 구조 검사 예제입니다.
  - 실제 에이전트 실행은 01_basic_deep_agent.py 참고.

실행:
  python examples/deepagents_core/02_middleware_stack.py
"""

import inspect


# ---------------------------------------------------------------------------
# 1. 미들웨어 스택 — create_deep_agent가 조립하는 순서
# ---------------------------------------------------------------------------

MIDDLEWARE_STACK = [
    # (클래스명, 조건, 역할)
    ("TodoListMiddleware",              "항상",                          "write_todos 도구 주입, 태스크 목록 관리"),
    ("SkillsMiddleware",                "skills= 파라미터 제공 시",       "skills/ 디렉터리에서 스킬 로드"),
    ("FilesystemMiddleware",            "항상 (제거 불가)",               "7개 filesystem 도구 주입, permissions 적용"),
    ("SubAgentMiddleware",              "inline subagents 있을 때",       "task 도구 주입, subagent 호출 처리"),
    ("AsyncSubAgentMiddleware",         "async subagents 있을 때",        "비동기 subagent 도구 주입"),
    ("SummarizationMiddleware",         "항상",                          "컨텍스트 > 85% 시 자동 요약"),
    ("PatchToolCallsMiddleware",        "항상",                          "tool call 형식 정규화"),
    ("--- user middleware ---",         "middleware= 파라미터",           "사용자 정의 미들웨어 삽입 위치"),
    ("HarnessProfile.extra_middleware", "profile에 있을 때",             "모델별 추가 미들웨어"),
    ("_ToolExclusionMiddleware",        "profile.excluded_tools 있을 때", "특정 도구 제거"),
    ("AnthropicPromptCachingMiddleware","항상 (비-Anthropic no-op)",      "Anthropic prompt cache 최적화"),
    ("MemoryMiddleware",                "memory= 파라미터 제공 시",       "AGENTS.md 로드 → system prompt 주입"),
    ("HumanInTheLoopMiddleware",        "interrupt_on= 제공 시",         "지정 도구 호출 전 pause"),
]


def print_middleware_stack() -> None:
    print("=== Middleware 스택 순서 (create_deep_agent 내부) ===")
    print(f"  {'순서':>4}  {'클래스':40}  {'조건':30}  {'역할'}")
    print("  " + "-" * 120)
    for i, (cls, cond, role) in enumerate(MIDDLEWARE_STACK, start=1):
        num = str(i) if not cls.startswith("---") else "--"
        print(f"  {num:>4}  {cls:40}  {cond:30}  {role}")

    print()
    print("What to notice:")
    print("  - FilesystemMiddleware, SubAgentMiddleware 는 required: excluded_middleware 로 제거 시 ValueError")
    print("  - 사용자 middleware 삽입 위치는 PatchToolCallsMiddleware 이후")
    print("  - AnthropicPromptCachingMiddleware 는 항상 추가되지만 비-Anthropic 모델에서는 no-op")
    print("  - general-purpose subagent 가 없는 경우 자동으로 추가됨 (profile로 비활성화 가능)")


# ---------------------------------------------------------------------------
# 2. _DeepAgentState 전체 필드
# ---------------------------------------------------------------------------

def inspect_state_fields() -> None:
    """AgentState 포함 전체 상태 필드를 출력한다."""
    from deepagents.graph import _DeepAgentState  # type: ignore[import]
    from langchain.agents import AgentState        # type: ignore[import]

    print("=== _DeepAgentState 필드 (AgentState 상속 포함) ===")
    print()

    print("  [AgentState 상속 필드]")
    for field, hint in AgentState.__annotations__.items():
        print(f"    {field}: {str(hint)[:60]}...")

    print()
    print("  [_DeepAgentState 추가/오버라이드 필드]")
    for field, hint in _DeepAgentState.__annotations__.items():
        print(f"    {field}: {str(hint)[:80]}...")

    print()
    print("What to notice:")
    print("  - messages 는 _DeepAgentState 에서 DeltaChannel 로 오버라이드됨")
    print("  - jump_to 는 AgentState의 ephemeral 필드 — middleware 간 제어 이동에 사용")
    print("  - structured_response 는 response_format= 파라미터 결과가 저장되는 필드")


# ---------------------------------------------------------------------------
# 3. checkpointer 파라미터 타입 확인
# ---------------------------------------------------------------------------

def inspect_checkpointer_type() -> None:
    """checkpointer 파라미터가 bool도 허용한다는 점을 확인한다."""
    sig = inspect.signature(__import__("deepagents").create_deep_agent)
    cp_param = sig.parameters["checkpointer"]

    print("=== checkpointer 파라미터 타입 ===")
    print(f"  annotation: {cp_param.annotation}")
    print(f"  default: {cp_param.default!r}")
    print()
    print("What to notice:")
    print("  - None | bool | BaseCheckpointSaver 세 가지 허용")
    print("  - bool 타입 의미: True 전달 시 자동으로 MemorySaver 생성 (가설 — 확인 필요)")
    print("  - LangGraph의 Checkpointer type alias와 동일 인터페이스")


# ---------------------------------------------------------------------------
# 4. 설치된 버전 기준 패키지 파일 목록
# ---------------------------------------------------------------------------

def print_package_files() -> None:
    """설치된 deepagents 패키지의 주요 파일을 출력한다."""
    import importlib.util
    import pathlib

    spec = importlib.util.find_spec("deepagents")
    if spec is None or spec.submodule_search_locations is None:
        print("deepagents 패키지를 찾을 수 없습니다.")
        return

    pkg_dir = pathlib.Path(spec.submodule_search_locations[0])
    print(f"=== deepagents 설치 경로 ===")
    print(f"  {pkg_dir}")
    print()
    print("  주요 파일:")
    for f in sorted(pkg_dir.rglob("*.py")):
        rel = f.relative_to(pkg_dir)
        print(f"    {rel}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print_middleware_stack()
    print()
    inspect_state_fields()
    print()
    inspect_checkpointer_type()
    print()
    print_package_files()
