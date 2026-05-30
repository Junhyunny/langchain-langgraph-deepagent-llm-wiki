---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-30
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
*Source: `langgraph-docs-graph-api-2026-05-23`, `langgraph-subgraph-experiment-2026-05-25`*

**서브그래프-as-노드: 상태 스키마 호환성 (검증됨)**

```python
class ParentState(TypedDict):
    query: str
    result: str         # 부모와 서브그래프 양쪽에 존재

class SubgraphState(TypedDict):
    query: str          # 공유 키 → 부모 값이 서브그래프로 전달됨
    result: str         # 공유 키 → 서브그래프 결과가 부모로 반환됨
    internal_step: str  # 서브그래프 전용 → 부모 출력에서 제외됨
```

- 컴파일된 `CompiledStateGraph`를 노드로 직접 추가: `graph.add_node("sub", subgraph)`
- **공유 키(shared keys)만** 부모↔서브그래프 간 전달됨 — 서브그래프 전용 키는 부모에 누출되지 않음
- 공유 키가 아예 없어도 에러 없음 — 서브그래프 출력이 조용히 무시됨 (버그 원인 주의)
- `input_schema` / `output_schema` 파라미터로 공개 인터페이스를 부모에 노출하는 키 제한 가능

**Send API — 동적 팬아웃 (map-reduce, 검증됨):**

```python
from typing import Annotated
from operator import add
from langgraph.types import Send

class OverallState(TypedDict):
    items: list[str]
    results: Annotated[list[str], add]  # Reducer: 각 worker 결과 누적

def dispatch(state: OverallState) -> list[Send]:
    return [Send("worker", {"item": item}) for item in state["items"]]

graph.add_conditional_edges("dispatcher", dispatch)
```

- 각 `Send(node, state)`는 독립적인 그래프 복사본을 생성 → 병렬 실행
- reduce 단계: 각 worker의 반환값이 OverallState의 Reducer(`add`)로 자동 집계됨
- `Send`의 state는 worker 노드에만 전달되는 격리된 입력 (OverallState와 스키마 달라도 됨)

**input_schema / output_schema로 인터페이스 분리 (검증됨):**

```python
class FullState(TypedDict):    # 내부 상태
    query: str
    result: str
    debug_info: str

class InputSchema(TypedDict):  # 호출자가 제공해야 할 것
    query: str

class OutputSchema(TypedDict): # 호출자에게 반환할 것
    result: str

graph = StateGraph(FullState, input_schema=InputSchema, output_schema=OutputSchema)
```

- 내부 상태 `debug_info`는 invoke() 결과에서 자동 제외됨
- 서브그래프-as-노드로 사용할 때 부모에 노출되는 키도 output_schema로 제한 가능

**Command — 크로스 그래프 네비게이션:**

```python
from langgraph.types import Command, PARENT

def child_node(state) -> Command:
    return Command(update={"result": "done"}, goto=PARENT)
```

- 서브그래프 노드에서 상위 그래프로 직접 제어를 넘길 수 있다
- `Command(graph=Command.PARENT, goto=[Send("collector", {...})])` 패턴은 parent graph의 특정 노드를 동적으로 실행한다
- child graph 안의 `ToolNode`가 여러 tool call에서 parent `Send`를 반환하면 parent collector가 여러 번 실행되고, parent reducer로 결과가 병합된다

실험: [[2026-05-30 langgraph toolnode parent command send]]

Source: `langgraph-docs-graph-api-2026-05-23`, `langgraph-subgraph-experiment-2026-05-25`

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

실행 검증: [[2026-05-30 deepagents subagentmiddleware task tool]]

- `task`가 parent model에 bound tool로 노출됨
- child state에는 `project_id` 같은 일반 state key가 전달되고, `messages`/`todos` 같은 excluded key는 전달되지 않음
- child `summary`는 parent state에 병합되고, child `todos`는 병합되지 않음
- child invoke config에는 `ls_agent_type="subagent"`가 추가됨

다중 호출 검증: [[2026-05-30 deepagents parallel task tool calls]]

- 단일 parent `AIMessage`의 여러 `task` tool call은 병렬 실행됨
- 완료 순서가 아니라 원래 tool call 순서대로 `ToolMessage`와 reducer state가 parent에 반영됨
- 여러 child가 같은 parent state key를 업데이트하려면 reducer를 명시하는 것이 안전함

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
- Deep Agents: `SubagentTransformer`의 scope 활용 방식은? (`_subagent_transformer.py` 확인 필요) — Source: `deepagents-source-graph-2026-05-19`
- Deep Agents: subagent가 실패할 때 main agent는 어떻게 처리하는가? — Needs Source

**해소됨:**
- ✅ LangGraph Send API map-reduce: `Annotated[list, add]` Reducer로 병렬 worker 결과 누적. `Send`의 state는 worker 전용 격리 입력 (직접 실행 확인, 2026-05-25)
- ✅ LangGraph 서브그래프 상태 스키마 호환성: **공유 키만** 부모↔서브그래프 전달. 서브그래프 전용 키는 부모 출력에서 제외. 공유 키 없어도 에러 없음 (직접 실행 확인, 2026-05-25)
- ✅ `input_schema`/`output_schema`로 서브그래프 공개 인터페이스 제한 가능 (직접 실행 확인, 2026-05-25)
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
- [[Deep Agents SubAgentMiddleware task tool flow]]
- [[LangGraph ToolNode Command vs Deep Agents task tool]]

## 소스

- `deepagents-docs-harness-2026-05-19`
- `deepagents-source-graph-2026-05-19`
- `deepagents-source-subagents-2026-05-23`
- `langgraph-docs-graph-api-2026-05-23`
