# LangGraph core examples

LLM API key 없이 LangGraph의 핵심 실행 모델을 이해하기 위한 작은 예제들이다.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U langgraph
```

## Examples

```bash
python examples/langgraph_core/01_stategraph_basics.py     # StateGraph 기초
python examples/langgraph_core/02_checkpointing_history.py # MemorySaver 체크포인팅
python examples/langgraph_core/03_interrupt_resume.py      # interrupt() / Command(resume=)
python examples/langgraph_core/04_hitl_advanced.py         # HITL 고급: 다중 interrupt, stream
python examples/langgraph_core/05_subgraph_patterns.py     # 서브그래프 / Send map-reduce
python examples/langgraph_core/06_streaming_modes.py       # 7가지 StreamMode 실험
python examples/langgraph_core/07_toolnode_injection.py    # ToolNode + InjectedState/Store
python examples/langgraph_core/08_toolnode_direct.py       # ToolNode 직접 입력 형태 + wrap_tool_call
python examples/langgraph_core/09_toolnode_command_outputs.py # ToolNode Command update/goto
python examples/langgraph_core/10_toolnode_parent_command_send.py # ToolNode Command.PARENT + Send
```

## What To Notice

- `StateGraph`는 공유 state를 node update로 누적한다.
- conditional edge는 state를 보고 다음 node를 고른다.
- `compile(checkpointer=...)` 이후에는 `thread_id`가 checkpoint key가 된다.
- `get_state_history()`는 thread 안의 checkpoint timeline을 보여준다.
- `interrupt()`는 workflow를 멈추고, `Command(resume=...)`가 같은 `thread_id`에서 이어간다.
- `stream_mode="updates"`는 변경분만 yield — 가장 실용적인 스트리밍 모드.
- `StreamWriter`로 노드 내부에서 임의 이벤트를 방출할 수 있다 (`stream_mode="custom"`).
- `ToolNode`는 `AIMessage.tool_calls`를 자동으로 실행하고 `ToolMessage` 리스트로 반환한다.
- `InjectedState`/`InjectedStore`는 LLM schema에 노출하지 않고 런타임 값을 도구에 주입한다.
- `ToolNode(..., wrap_tool_call=...)`은 LangChain `create_agent`의 `AgentMiddleware.wrap_tool_call` 연결 지점이다.
- `ToolNode`가 `Command`를 반환하면 compiled graph 안에서 state update와 `goto` 라우팅으로 해석된다.
- child graph의 `ToolNode`가 `Command(graph=Command.PARENT, goto=[Send(...)])`를 반환하면 parent graph 노드를 동적으로 호출할 수 있다.
