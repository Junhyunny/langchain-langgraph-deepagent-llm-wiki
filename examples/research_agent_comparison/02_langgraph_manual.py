"""
02. LangGraph StateGraph 수동 구성

특징:
  - 오케스트레이션(루프, 분기)을 개발자가 명시적으로 정의
  - 노드(agent, tools) + 엣지(conditional) 구조가 코드에 드러남
  - compile(checkpointer=...) 로 체크포인팅 추가 가능
  - 가드레일 = 별도 노드로 삽입 가능

실행:
  cd <repo_root>
  source .venv/bin/activate
  python examples/research_agent_comparison/02_langgraph_manual.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from _mock_llm import make_llm


@tool
def search(query: str) -> str:
    """웹에서 정보를 검색한다."""
    return f"[Mock 검색 결과] {query} → GIL은 CPython의 스레드 안전 뮤텍스입니다."


def build_graph():
    model = make_llm()

    def agent_node(state: MessagesState):
        return {"messages": [model.invoke(state["messages"])]}

    def should_continue(state: MessagesState):
        return "tools" if state["messages"][-1].tool_calls else END

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode([search]))
    builder.set_entry_point("agent")
    builder.add_conditional_edges("agent", should_continue)
    builder.add_edge("tools", "agent")

    return builder.compile()


def run():
    graph = build_graph()
    return graph.invoke({
        "messages": [{"role": "user", "content": "Python GIL에 대해 설명하고 우회 방법을 정리해라."}]
    })


if __name__ == "__main__":
    result = run()
    print("=== LangGraph StateGraph 수동 구성 ===")
    print(result["messages"][-1].content)
    print(f"\n총 메시지 수: {len(result['messages'])}")
    print("메시지 타입:", [type(m).__name__ for m in result["messages"]])
