"""
04. Deep Agents create_deep_agent — 개념 스텁 (실행 불가)

⚠️ 이 파일은 실행할 수 없습니다.
   deepagents 패키지가 공개 PyPI에서 확인되지 않았습니다.
   코드 구조 참고용으로만 사용하세요.

특징 (추정, Needs Source):
  - create_agent 기반 + Middleware 계층 추가
  - MemoryMiddleware, SummarizationMiddleware 등 기본 제공 가능
  - HarnessProfile로 모델별 설정 자동화
  - SubagentTransformer로 서브에이전트 스트리밍 지원

비교:
  create_agent (langchain)      — middleware= 파라미터
  create_react_agent (langgraph) — pre_model_hook= 파라미터
  create_deep_agent (deepagents) — middleware= 파라미터 (langchain과 동일 계층?)
"""

# ---- 개념 코드 (실행 불가) ----
#
# from deepagents import create_deep_agent
# from deepagents.middleware import MemoryMiddleware
# from langchain.agents import tool
# from langchain_openai import ChatOpenAI
#
# @tool
# def search(query: str) -> str:
#     """웹에서 정보를 검색한다."""
#     return f"Search results for: {query}"
#
# model = ChatOpenAI(model="gpt-4o-mini")
#
# agent = create_deep_agent(
#     model=model,
#     tools=[search],
#     system_prompt="당신은 리서치 에이전트입니다.",
#     middleware=[MemoryMiddleware()],  # Deep Agents 고유: Middleware로 메모리 자동 관리
# )
#
# result = agent.invoke({
#     "messages": [{"role": "user", "content": "Python GIL에 대해 설명해라."}]
# })
# print(result["messages"][-1].content)
# ---- 끝 ----


if __name__ == "__main__":
    print("⚠️  Deep Agents 예제는 패키지 미설치로 실행할 수 없습니다.")
    print("    코드 구조는 파일 주석을 참고하세요.")
    print()
    print("예상 구조 (langchain.agents.create_agent와 비교):")
    print("  langchain : create_agent(model, tools, system_prompt=, middleware=)")
    print("  deepagents: create_deep_agent(model, tools, system_prompt=, middleware=)")
    print()
    print("핵심 차이 (⚠️ 가설 — Needs Source):")
    print("  - MemoryMiddleware 기본 내장 여부")
    print("  - HarnessProfile 모델별 자동 설정")
    print("  - SubagentTransformer 스트리밍 지원")
