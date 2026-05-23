---
source_id: deepagents-source-patch-tool-calls-2026-05-23
title: "Deep Agents — middleware/patch_tool_calls.py (PatchToolCallsMiddleware 소스코드)"
type: source_code
framework: Deep Agents
url: "https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/deepagents/middleware/patch_tool_calls.py"
retrieved_at: "2026-05-23"
status: current
used_by:
  - "docs/wiki/flows/Deep Agents create_deep_agent flow.md"
  - "docs/wiki/concepts/Agent Harness.md"
---

# Summary

`PatchToolCallsMiddleware`의 전체 구현 — "dangling tool call" 문제를 해결하는 미들웨어.

---

## 클래스 정의

```python
class PatchToolCallsMiddleware(AgentMiddleware):
    """Middleware to patch dangling tool calls in the messages history."""
```

**오버라이드하는 hook: `before_agent` 단 하나.** (wrap_model_call, before_tool, after_tool 없음)

---

## before_agent 로직 전체

```python
def before_agent(self, state: AgentState, runtime: Runtime[Any]) -> dict[str, Any] | None:
    messages = state["messages"]
    if not messages:
        return None

    # 이미 응답된 tool_call_id 집합
    answered_ids = {msg.tool_call_id for msg in messages if msg.type == "tool"}

    # dangling tool call 존재 여부 확인
    if not any(
        tool_call["id"] is not None and tool_call["id"] not in answered_ids
        for msg in messages
        if isinstance(msg, AIMessage)
        for tool_call in (*msg.tool_calls, *msg.invalid_tool_calls)
    ):
        return None  # no-op

    # dangling tool call마다 더미 ToolMessage 삽입
    patched_messages: list[AnyMessage] = []
    for msg in messages:
        patched_messages.append(msg)
        if not isinstance(msg, AIMessage):
            continue
        for tool_call in (*msg.tool_calls, *msg.invalid_tool_calls):
            tool_call_id = tool_call["id"]
            if tool_call_id is None or tool_call_id in answered_ids:
                continue
            name = tool_call["name"] or "unknown"
            if tool_call.get("type") == "invalid_tool_call":
                content = f"Tool call {name} with id {tool_call_id} could not be executed - arguments were malformed or truncated."
            else:
                content = f"Tool call {name} with id {tool_call_id} was cancelled - another message came in before it could be completed."
            patched_messages.append(ToolMessage(content=content, name=name, tool_call_id=tool_call_id))

    return {"messages": Overwrite(patched_messages)}
```

---

## 핵심 역할

LLM이 tool call을 요청했으나 그에 대응하는 `ToolMessage`가 메시지 히스토리에 존재하지 않는 "dangling tool call" 상태를 에이전트 실행 직전에 감지하여, 누락된 응답을 대신하는 더미 `ToolMessage`로 채워 넣는다. 인터럽트, 메시지 취소, 인자 파싱 실패 등으로 tool 실행이 미완료된 채 히스토리가 남았을 때 LLM이 해당 히스토리를 읽어 오류를 일으키는 것을 방지한다. `Overwrite` 타입으로 state를 교체하므로 메시지 reducer의 append 동작을 우회해 히스토리 전체를 정합성 있는 상태로 만든다.

---

## 처리하는 두 케이스

| 케이스 | tool_call type | 삽입 메시지 |
|--------|---------------|------------|
| 인자 파싱 실패 | `"invalid_tool_call"` | "could not be executed - arguments were malformed or truncated." |
| 중단된 정상 호출 | (없음, 일반 tool_call) | "was cancelled - another message came in before it could be completed." |

---

## middleware 스택 내 위치

`create_deep_agent`의 base stack에서 고정으로 포함됨:
1. TodoListMiddleware
2. SkillsMiddleware
3. FilesystemMiddleware
4. SubAgentMiddleware
5. AsyncSubAgentMiddleware
6. create_summarization_middleware (SummarizationMiddleware)
7. **PatchToolCallsMiddleware** ← 여기
(이후 사용자 middleware, tail stack)

메인 agent, subagent, general-purpose subagent 모두에 적용됨.

---

## 왜 필요한가

LangGraph의 interrupt 기능, 사용자가 중간에 새 메시지를 보내는 경우, Anthropic 모델의 trailing empty AIMessage 등으로 tool call이 히스토리에 남을 수 있다. 이 상태에서 LLM을 다시 호출하면 "tool call without response" 형식 에러가 발생한다. 이 middleware가 매 agent 실행 전에 이 상태를 자동으로 수정한다.
