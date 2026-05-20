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
python examples/langgraph_core/01_stategraph_basics.py
python examples/langgraph_core/02_checkpointing_history.py
python examples/langgraph_core/03_interrupt_resume.py
```

## What To Notice

- `StateGraph`는 공유 state를 node update로 누적한다.
- conditional edge는 state를 보고 다음 node를 고른다.
- `compile(checkpointer=...)` 이후에는 `thread_id`가 checkpoint key가 된다.
- `get_state_history()`는 thread 안의 checkpoint timeline을 보여준다.
- `interrupt()`는 workflow를 멈추고, `Command(resume=...)`가 같은 `thread_id`에서 이어간다.
