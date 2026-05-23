---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-23
sources:
  - deepagents-docs-harness-2026-05-19
  - deepagents-source-graph-2026-05-19
  - deepagents-source-subagents-2026-05-23
  - langgraph-docs-graph-api-2026-05-23
---

# Subagents

## 요약

Subagents는 더 큰 워크플로의 일부로 부모(오케스트레이션) agent에 의해 호출되는 agent다. 각 서브에이전트는 자신만의 도구, 상태, 프롬프트를 가질 수 있다.

*상태: 초안 스텁이다. 소스 검증이 필요하다.*

## 중요한 이유

서브에이전트 오케스트레이션은 복잡한 멀티 에이전트 시스템의 핵심 패턴이다. 부모 agent가 서브에이전트에 어떻게 위임하는지, 컨텍스트가 어떻게 전달되는지, 결과가 어떻게 수집되는지를 이해하는 것은 확장 가능한 agent 파이프라인을 구축하는 데 필수적이다.

## 핵심 개념

- **Orchestrator** — 계획하고 위임하는 최상위 agent
- **Subagent** — 하위 작업을 수행하는 특화된 agent
- **위임** — 부모에서 서브에이전트로 작업 또는 컨텍스트를 전달함
- **집계** — 여러 서브에이전트의 결과를 수집하고 병합함
- **Handoff** — agent 간 제어를 넘김

## 프레임워크별 동작

### LangChain

- 서브에이전트는 도구로 감싸서 [[Tool Calling]]을 통해 호출할 수 있다
- *소스 필요.*

### LangGraph
*Source: `langgraph-docs-graph-api-2026-05-23`*

**서브그래프 (subgraph-as-node):**

- 컴파일된 `CompiledStateGraph`를 노드로 직접 추가 가능
- 서브그래프는 자신의 상태 스키마를 가짐 (상위 그래프와 독립)

**Send API — 동적 팬아웃 (map-reduce):**

```python
from langgraph.types import Send

def dispatch(state: OverallState):
    return [Send("worker_node", {"item": item}) for item in state["items"]]

builder.add_conditional_edges("dispatcher", dispatch)
```

- 각 `Send(node, state)`는 독립적인 그래프 복사본을 생성 → 병렬 실행
- reduce 단계: 각 worker의 부분 업데이트가 OverallState의 Reducer로 집계됨
- `Send`의 state는 worker 노드에만 전달되는 격리된 입력

**Command — 크로스 그래프 네비게이션:**

```python
from langgraph.types import Command, PARENT

def child_node(state) -> Command:
    return Command(update={"result": "done"}, goto=PARENT)
```

- 서브그래프 노드에서 상위 그래프로 직접 제어를 넘길 수 있다
- `goto` 대신 `PARENT`를 사용하면 부모 그래프의 다음 노드로 라우팅

Source: `langgraph-docs-graph-api-2026-05-23`

### Deep Agents
*Source: `deepagents-docs-harness-2026-05-19`, `deepagents-source-graph-2026-05-19`, `deepagents-source-subagents-2026-05-23`*

**Subagent 타입:**
- `SubAgent` — declarative 방식. `name`, `description`, `system_prompt`, `model`, `tools` 명시.
- `CompiledSubAgent` — pre-compiled `Runnable`. 상태 스키마에 반드시 `messages` 키 필요.
- (구) `AsyncSubAgent` — remote/background (`graph_id` 필요)

**기본 스펙:**
- 기본 `general-purpose` subagent 자동 추가 (HarnessProfile로 비활성화 가능)
- Subagent는 parent의 `interrupt_on` 상속; `CompiledSubAgent`는 상속 안 함
- Subagent는 parent의 `permissions` 상속; 자체 선언 시 완전 대체

---

#### 상태 격리 메커니즘 (검증됨)
*Source: `deepagents-source-subagents-2026-05-23`*

**`_EXCLUDED_STATE_KEYS`** 상수가 격리의 핵심:

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

**① 호출 시 (입력 필터링) — `_validate_and_prepare_state()`:**
```python
subagent_state = {
    k: v for k, v in runtime.state.items()
    if k not in _EXCLUDED_STATE_KEYS
}
subagent_state["messages"] = [HumanMessage(content=description)]
```
- parent 메시지 히스토리 대신 단일 `HumanMessage(task description)` 전달
- `skills_metadata`, `memory_contents` 등 parent-specific 상태 누출 방지

**② 반환 시 (출력 필터링) — `_return_command_with_state_update()`:**
```python
state_update = {k: v for k, v in result.items() if k not in _EXCLUDED_STATE_KEYS}
```
- subagent 중간 메시지가 parent에 직접 병합되지 않음
- `structured_response`가 있으면 JSON 직렬화 → ToolMessage content
- 없으면 마지막 비어있지 않은 AIMessage text → ToolMessage content

**결과:** `Command(update={...state_update, "messages": [ToolMessage(content)]})` 형태로 parent에 반환.

---

#### task tool 실행 흐름 (검증됨)

```
task(description, subagent_type, runtime)
  ↓
_validate_and_prepare_state()   ← _EXCLUDED_STATE_KEYS 필터 (입력)
  ↓
_build_subagent_config()        ← callbacks/tags/configurable만 전파
                                ← recursion_limit, metadata는 의도적으로 제외
  ↓
subagent.invoke(state, config)  ← LangSmith ls_agent_type="subagent" 태깅
  ↓
_return_command_with_state_update()  ← _EXCLUDED_STATE_KEYS 필터 (출력)
  ↓
Command(update={state_update, messages=[ToolMessage]})
```

---

#### Config 전파 규칙 (검증됨)

parent → subagent로 전달되는 config 키:
- `callbacks` — Pregel 스트리밍 핸들러 전파
- `tags` — tracing 연속성
- `configurable` — Pregel subgraph 인식

전달되지 않는 것 (의도적):
- `recursion_limit` — subagent 자체 bound config 우선
- `metadata` — 전달 시 subagent `lc_agent_name` 덮어씀

---

#### SubAgentMiddleware.wrap_model_call

system prompt에 task tool 사용법 + available subagent 목록을 자동 append:

```python
def wrap_model_call(self, request, handler):
    if self.system_prompt is not None:
        new_system_message = append_to_system_message(
            request.system_message, self.system_prompt
        )
        return handler(request.override(system_message=new_system_message))
    return handler(request)
```

---

**이점:**
- Context isolation — subagent 중간 작업이 main context를 오염시키지 않음
- 병렬 실행 — 단일 메시지에 여러 task tool 호출로 동시 실행
- Specialization — tool/설정을 subagent별로 독립 구성
- Token efficiency — 무거운 작업 context가 단일 ToolMessage로 압축됨

## 미해결 질문

- LangChain에서 orchestrator → subagent 컨텍스트 전달 방식은? — Needs Source
- LangGraph `Send` 사용 시 각 worker의 결과를 집계하는 reduce 단계의 Reducer 설계 패턴은? — Source: `langgraph-docs-graph-api-2026-05-23`
- LangGraph 서브그래프와 상위 그래프 간 상태 스키마 호환성 요구사항은? — Needs Source
- Deep Agents: `SubagentTransformer`의 scope 활용 방식은? (`_subagent_transformer.py` 확인 필요) — Source: `deepagents-source-graph-2026-05-19`
- Deep Agents: subagent가 실패할 때 main agent는 어떻게 처리하는가? — Needs Source

**해소됨:**
- ✅ Deep Agents subagent 상태는 격리됨 — stateless, fresh context로 실행 (Source: `deepagents-docs-harness-2026-05-19`)
- ✅ 결과 집계: 단일 최종 보고서만 반환 (Source: `deepagents-docs-harness-2026-05-19`)
- ✅ LangGraph subagent 패턴 2가지: 서브그래프-as-노드, Send API (Source: `langgraph-docs-graph-api-2026-05-23`)
- ✅ `SubAgentMiddleware` 내부 context isolation 구현: `_EXCLUDED_STATE_KEYS`로 입력/출력 양방향 필터링 (Source: `deepagents-source-subagents-2026-05-23`)
- ✅ Config 전파 규칙: `callbacks`/`tags`/`configurable`만 forwarding, `recursion_limit`/`metadata` 제외 (Source: `deepagents-source-subagents-2026-05-23`)

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[StateGraph]]
- [[Context Engineering]]
- [[Deep Agents create_deep_agent flow]]

## 소스

- `deepagents-docs-harness-2026-05-19`
- `deepagents-source-graph-2026-05-19`
- `deepagents-source-subagents-2026-05-23`
- `langgraph-docs-graph-api-2026-05-23`
