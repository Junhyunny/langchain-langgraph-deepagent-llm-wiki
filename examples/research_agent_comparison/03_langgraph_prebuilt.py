"""
03. LangGraph create_react_agent — prebuilt 고수준 API

특징:
  - StateGraph 내부 자동 구성 (langgraph.prebuilt)
  - prompt= 파라미터로 시스템 프롬프트 설정
  - langchain.agents.create_agent와 유사한 수준의 추상화
  - 차이: create_agent는 langchain 패키지 (middleware 지원),
          create_react_agent는 langgraph 패키지 (pre_model_hook 지원)

실행:
  cd <repo_root>
  source .venv/bin/activate
  python examples/research_agent_comparison/03_langgraph_prebuilt.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from _mock_llm import make_llm


@tool
def search(query: str) -> str:
    """웹에서 정보를 검색한다."""
    return f"[Mock 검색 결과] {query} → GIL은 CPython의 스레드 안전 뮤텍스입니다."


def run():
    model = make_llm()

    agent = create_react_agent(
        model=model,
        tools=[search],
        prompt="당신은 리서치 에이전트입니다. 도구를 사용해 정보를 검색하고 정확한 답변을 제공합니다.",
    )

    return agent.invoke({
        "messages": [{"role": "user", "content": "Python GIL에 대해 설명하고 우회 방법을 정리해라."}]
    })


if __name__ == "__main__":
    result = run()
    print("=== LangGraph create_react_agent ===")
    print(result["messages"][-1].content)
    print(f"\n총 메시지 수: {len(result['messages'])}")
    print("메시지 타입:", [type(m).__name__ for m in result["messages"]])
