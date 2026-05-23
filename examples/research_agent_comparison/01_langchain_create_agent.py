"""
01. LangChain create_agent — 고수준 API

특징:
  - langchain.agents.create_agent() 가 내부적으로 LangGraph StateGraph를 생성
  - 오케스트레이션(루프, 분기)은 프레임워크가 자동 처리
  - system_prompt 파라미터로 시스템 지시문 설정
  - middleware= 파라미터로 확장 가능 (Deep Agents 스타일 미들웨어)

실행:
  cd <repo_root>
  source .venv/bin/activate
  python examples/research_agent_comparison/01_langchain_create_agent.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain.agents import create_agent
from langchain_core.tools import tool
from _mock_llm import make_llm


@tool
def search(query: str) -> str:
    """웹에서 정보를 검색한다."""
    return f"[Mock 검색 결과] {query} → GIL은 CPython의 스레드 안전 뮤텍스입니다."


def run():
    model = make_llm()

    agent = create_agent(
        model=model,
        tools=[search],
        system_prompt="당신은 리서치 에이전트입니다. 도구를 사용해 정보를 검색하고 정확한 답변을 제공합니다.",
    )

    result = agent.invoke({
        "messages": [{"role": "user", "content": "Python GIL에 대해 설명하고 우회 방법을 정리해라."}]
    })

    return result


if __name__ == "__main__":
    result = run()
    print("=== LangChain create_agent ===")
    print(result["messages"][-1].content)
    print(f"\n총 메시지 수: {len(result['messages'])}")
    print("메시지 타입:", [type(m).__name__ for m in result["messages"]])
