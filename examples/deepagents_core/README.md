# Deep Agents Core 예제

`deepagents` 패키지의 공개 API를 탐색하는 예제 모음.

## 실행 환경

```bash
# 의존성 설치
pip install deepagents

# 예제 실행 (저장소 루트에서)
python examples/deepagents_core/01_basic_deep_agent.py
python examples/deepagents_core/02_middleware_stack.py
python examples/deepagents_core/03_tool_call_and_filesystem.py
python examples/deepagents_core/04_subagent_middleware_task_tool.py
```

API 키 없이 실행하면 구조 검사만 수행합니다.  
실제 에이전트 생성/실행은 `ANTHROPIC_API_KEY` 또는 `OPENAI_API_KEY` 필요.

---

## 예제 목록

### `01_basic_deep_agent.py` — 기본 구조 이해

- `create_deep_agent()` 파라미터 목록 및 타입 확인
- `_DeepAgentState` 구조 — `DeltaChannel`로 checkpoint O(N²) → O(N) 최적화
- 반환 타입 `CompiledStateGraph` 확인
- `system_prompt` 조립 순서: `USER → BASE → SUFFIX`

**What To Notice:**

1. **`system_prompt=` 파라미터명** — `instructions=`이 아님. API 키 없이 시그니처 확인 가능.

2. **`_DeepAgentState.messages`의 `DeltaChannel`** — 기본 `add_messages` reducer 대신 `DeltaChannel`을 사용해 메시지 히스토리가 길어져도 checkpoint 크기가 O(N)으로 유지된다. `snapshot_frequency=50`이므로 50 writes마다 전체 스냅샷, 그 사이는 delta만 저장.

3. **`create_deep_agent`는 `create_agent`(LangChain)에 위임** — middleware 조립 후 `langchain.agents.create_agent`에 위임하고 `.with_config(recursion_limit=9_999)` 적용 후 반환.

---

### `02_middleware_stack.py` — 미들웨어 스택 구조

- `create_deep_agent`가 조립하는 미들웨어 13개와 적용 순서
- `AgentState` 상속 필드 — `jump_to`, `structured_response`
- `checkpointer` 파라미터 — `None | bool | BaseCheckpointSaver`

**What To Notice:**

1. **미들웨어 삽입 위치** — 사용자 `middleware=` 파라미터는 `PatchToolCallsMiddleware` 이후에 삽입됨. 순서가 중요한 미들웨어라면 이 위치를 고려해야 함.

2. **`FilesystemMiddleware` 제거 불가** — `excluded_middleware`로 제거 시도 시 `ValueError` 발생. 보안 보장(permissions 적용)과 filesystem 도구 주입이 여기에 집중되어 있기 때문.

3. **`AgentState`의 숨겨진 필드** — `jump_to` (EphemeralValue: 미들웨어 간 제어 이동용)와 `structured_response` (`response_format=` 결과 저장용)는 일반 메시지 I/O와 별개로 상태를 전달하는 데 사용됨.

---

### `03_tool_call_and_filesystem.py` — 실제 invoke/tool/filesystem 흐름

- fake chat model로 API 키 없이 `create_deep_agent().invoke()` 실행
- 사용자 정의 `record_finding` tool 호출 흐름 확인
- built-in `write_file` tool이 `StateBackend`의 `files` state를 갱신하는지 확인
- non-sandbox backend에서 `execute` tool이 모델에 bind되기 전에 필터링되는지 확인

**What To Notice:**

1. **fake model이어도 그래프 런타임은 실제 실행됨** — model 응답만 deterministic할 뿐, LangChain agent loop, ToolNode, checkpointed state는 실제 경로를 탄다.

2. **StateBackend files는 로컬 파일시스템이 아니다** — `/notes/langgraph.md`는 디스크가 아니라 LangGraph state의 `files` 채널에 저장된다.

3. **`execute` tool 필터링** — `FilesystemMiddleware`는 `execute` tool을 만들지만, 기본 `StateBackend`가 `SandboxBackendProtocol`을 구현하지 않으면 `wrap_model_call`에서 tool 목록에서 제거한다.

---

### `04_subagent_middleware_task_tool.py` — SubAgentMiddleware task tool 흐름

- `SubAgentMiddleware`가 parent agent에 `task` tool을 추가하는지 확인
- fake parent model의 `task(description, subagent_type)` 호출이 compiled subagent runnable로 이어지는지 확인
- parent state에서 subagent로 전달되는 키와 제외되는 키를 관찰
- subagent 결과가 `Command(update=...)`로 parent state에 병합되는지 확인

**What To Notice:**

1. **`task`는 일반 tool처럼 bound됨** — parent model은 `task` tool schema를 보고 tool call을 만든다.

2. **message history는 격리됨** — subagent는 parent messages 전체가 아니라 task description 하나만 `HumanMessage`로 받는다.

3. **상태 병합도 필터링됨** — 예제에서 child `summary`는 parent state로 병합되지만, child `todos`는 제외된다.

---

## 소스 기반 확인 사항 (v0.6.3)

| 항목 | 확인 내용 | 파일 |
|------|----------|------|
| 진입점 파라미터 | `system_prompt=` (not `instructions=`) | `graph.py` |
| 기본 모델 | `claude-sonnet-4-6` (deprecated since 0.5.3) | `graph.py:153` |
| 최종 반환 | `CompiledStateGraph.with_config(recursion_limit=9_999)` | `graph.py:765–788` |
| 상태 스키마 | `_DeepAgentState` + `DeltaChannel(snapshot_frequency=50)` | `graph.py:63–66` |
| required middleware | `FilesystemMiddleware`, `SubAgentMiddleware` | `graph.py:187–204` |
| `checkpointer` 타입 | `None \| bool \| BaseCheckpointSaver` | `graph.py` 시그니처 |
| non-sandbox execute | `FilesystemMiddleware.wrap_model_call()`에서 모델 bind 전 필터링 | `filesystem.py` |
