"""
공유 Mock LLM — 실제 API 키 없이 에이전트 루프를 테스트하기 위한 FakeLLM.

동작:
  1번째 호출 → AIMessage(tool_calls=[search(...)])
  2번째 이후  → AIMessage(content="최종 답변")
"""
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import PrivateAttr

MOCK_SEARCH_RESULT = (
    "[Mock 검색 결과] GIL(Global Interpreter Lock)은 CPython 인터프리터에서 "
    "한 번에 하나의 스레드만 Python 바이트코드를 실행하도록 보장하는 뮤텍스입니다."
)

FINAL_ANSWER = (
    "**Python GIL (Global Interpreter Lock)**\n\n"
    "GIL은 CPython 인터프리터가 한 번에 하나의 스레드만 Python 바이트코드를 "
    "실행하도록 보장하는 뮤텍스입니다. 멀티코어 CPU에서도 스레드가 병렬로 "
    "실행되지 않는 이유입니다.\n\n"
    "**우회 방법:**\n"
    "1. `multiprocessing` — 프로세스별 GIL, 진정한 병렬 처리 가능\n"
    "2. C 확장 (NumPy, Cython) — 계산 구간에서 GIL 명시적 해제\n"
    "3. `asyncio` — I/O 바운드 작업에서 효율적 처리 (GIL 우회 아님)\n"
    "4. GIL-free CPython 3.13+ (PEP 703) — `PYTHON_GIL=0` 환경변수\n"
)


class FakeResearchLLM(BaseChatModel):
    """두 번 호출되는 Mock LLM: 첫 호출→tool_call, 이후→최종 답변."""

    _call_count: int = PrivateAttr(default=0)

    @property
    def _llm_type(self) -> str:
        return "fake-research-llm"

    def bind_tools(self, tools, **kwargs):
        """Mock: 도구 바인딩을 무시하고 self 반환 (FakeLLM은 응답이 미리 정해짐)."""
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._call_count += 1
        if self._call_count == 1:
            msg = AIMessage(
                content="",
                tool_calls=[{
                    "name": "search",
                    "args": {"query": "Python GIL Global Interpreter Lock 우회 방법"},
                    "id": "call_mock_1",
                    "type": "tool_call",
                }],
            )
        else:
            msg = AIMessage(content=FINAL_ANSWER)
        return ChatResult(generations=[ChatGeneration(message=msg)])


def make_llm() -> FakeResearchLLM:
    """호출할 때마다 상태가 초기화된 새 FakeResearchLLM 반환."""
    return FakeResearchLLM()
