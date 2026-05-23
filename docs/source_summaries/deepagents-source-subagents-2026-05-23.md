---
source_id: deepagents-source-subagents-2026-05-23
title: "Deep Agents — middleware/subagents.py (SubAgentMiddleware 소스코드)"
type: source_code
framework: Deep Agents
url: "https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/deepagents/middleware/subagents.py"
retrieved_at: "2026-05-23"
status: current
used_by:
  - "docs/wiki/concepts/Subagents.md"
---

# Summary

`SubAgentMiddleware`의 전체 구현 파일. subagent state isolation 메커니즘의 핵심 소스.

---

## 핵심 타입

### SubAgent (TypedDict)
Subagent 명세 — declarative 방식으로 정의.

필수 필드:
- `name: str` — 고유 식별자 (task tool 호출 시 사용)
- `description: str` — 위임 여부 결정에 사용
- `system_prompt: str` — subagent 지시사항

선택 필드:
- `tools` — 없으면 parent agent 상속
- `model: str | BaseChatModel` — `'provider:model-name'` 형식
- `middleware: list[AgentMiddleware]`
- `interrupt_on: dict[str, bool | InterruptOnConfig]` — checkpointer 필요
- `skills: list[str]` — SkillsMiddleware 경로
- `permissions: list[FilesystemPermission]` — 없으면 parent 상속, 있으면 완전 대체
- `response_format: ResponseFormat | type | dict` — 구조화 출력 스키마

### CompiledSubAgent (TypedDict)
Pre-compiled runnable을 가지는 subagent.
- `runnable: Runnable` — 상태 스키마에 반드시 `messages` 키 포함 필요
- `structured_response`가 non-None이면 JSON 직렬화 후 ToolMessage content로 반환

---

## 상태 격리 메커니즘 (_EXCLUDED_STATE_KEYS)

```python
_EXCLUDED_STATE_KEYS = {
    "messages",
    "todos",
    "structured_response",
    "skills_metadata",
    "skills_load_errors",
    "memory_contents",
}
```

**두 방향으로 적용:**

1. **Subagent 호출 시 (입력 필터링)** — `_validate_and_prepare_state()`:
   ```python
   subagent_state = {
       k: v for k, v in runtime.state.items()
       if k not in _EXCLUDED_STATE_KEYS
   }
   subagent_state["messages"] = [HumanMessage(content=description)]
   ```
   - parent의 메시지 히스토리 대신 단일 HumanMessage(task description)만 전달
   - `skills_metadata`, `memory_contents` 등 parent-specific 상태 누출 방지

2. **Subagent 결과 반환 시 (출력 필터링)** — `_return_command_with_state_update()`:
   ```python
   state_update = {k: v for k, v in result.items() if k not in _EXCLUDED_STATE_KEYS}
   ```
   - subagent의 messages 중 마지막 AIMessage text(또는 structured_response)만 ToolMessage로 parent에 전달
   - `todos`, `structured_response`(이미 직렬화) 등은 parent state에 직접 병합 안 됨

**설계 이유:**
- `messages`는 명시적으로 처리 — subagent 중간 단계가 parent에 노출되지 않음
- `todos`/`structured_response`는 subagent 범위를 벗어나면 의미 없음
- `skills_metadata`/`memory_contents`는 `PrivateStateAttr` 어노테이션으로도 제외되지만, runtime.state 전달 시 이중으로 명시적 필터링

---

## Config 전파 규칙 (_build_subagent_config)

parent runtime config에서 다음 키만 subagent에 전달:
- `callbacks` — Pregel 스트리밍 핸들러 전파용
- `tags` — tracing 연속성
- `configurable` — subgraph 인식을 위한 Pregel 필요 사항

**의도적으로 전달하지 않는 것:**
- `recursion_limit` — subagent 자체 bound config 우선
- `metadata` — 전달 시 subagent의 `lc_agent_name` 등을 덮어씀

추가로 `configurable["ls_agent_type"] = "subagent"` 자동 태깅.

---

## LangSmith Tracing 통합

`_subagent_tracing_context()` context manager가 subagent 실행 전후에:
- `metadata["ls_agent_type"] = "subagent"` 태깅
- 기존 tracing context(parent, client, tags 등) 유지 — 덮어쓰지 않음

---

## task tool 동작 흐름

```
task(description, subagent_type, runtime)
  ↓
_validate_and_prepare_state()   ← _EXCLUDED_STATE_KEYS 필터 적용 (입력)
  ↓
_build_subagent_config()        ← callbacks/tags/configurable만 전파
  ↓
subagent.invoke(subagent_state, subagent_config)
  ↓
_return_command_with_state_update()  ← _EXCLUDED_STATE_KEYS 필터 적용 (출력)
  ↓
Command(update={...state_update, "messages": [ToolMessage(content)]})
```

---

## SubAgentMiddleware.wrap_model_call

```python
def wrap_model_call(self, request, handler):
    if self.system_prompt is not None:
        new_system_message = append_to_system_message(
            request.system_message, self.system_prompt
        )
        return handler(request.override(system_message=new_system_message))
    return handler(request)
```

- system_prompt에 task tool 사용법 + available subagent 목록을 자동으로 model system message에 append

---

## 상수

- `DEFAULT_SUBAGENT_PROMPT` — subagent 기본 지시사항. 중간 작업이 아닌 최종 응답에 완전한 답 포함 요구.
- `TASK_TOOL_DESCRIPTION` — `{available_agents}` placeholder 포함. task tool LLM 설명.
- `TASK_SYSTEM_PROMPT` — task tool 사용 가이드라인 (언제 쓸지/쓰지 말지).
- `GENERAL_PURPOSE_SUBAGENT` — 기본 general-purpose subagent 스펙.

---

## 결과 추출 우선순위

1. `structured_response`가 non-None → JSON 직렬화 (Pydantic: model_dump_json, dataclass: asdict, 기타: json.dumps)
2. 없으면 → messages를 역순으로 순회해 마지막 비어있지 않은 AIMessage text 추출
   (Anthropic의 trailing empty end_turn AIMessage 방어 로직 포함)
