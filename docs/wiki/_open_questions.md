# 미해결 질문

학습 중 수집한 질문이다. 답을 찾으면 삭제한다.

---

## 이번 주 우선순위 큐 (2026-05-24)

- [ ] Deep Agents eval에서 LLM-as-a-judge 모델 결정 경로를 확정한다 (`MODEL_GROUPS.md` 연계 포함).  
  Source: `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
- [ ] BFCL v3 평가가 실제 실행 경로(테스트/워크플로)에서 어떻게 연결되는지 확정한다.  
  Source: `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
- ✅ `create_agent` 초기화 시간(0.262s)이 `create_react_agent`(0.004s)보다 긴 이유: factory.py `.venv` 직접 확인(2026-05-24). 원인: model이 string이면 `init_chat_model()` 호출(provider import), middleware hook 감지(클래스 비교 전체 순회), `_resolve_schemas()`, `StateGraph` 구성, `graph.compile()`. `bind_tools()`는 **init이 아닌 매 model 호출 시** `_get_bound_model()` 내에서 실행됨. Source: `langchain-venv-factory-read-2026-05-24`
- ✅ Deep Agents `create_deep_agent` 파라미터명 확인: `system_prompt=` (`instructions=` 아님). `.venv` 직접 실행과 local `deepagents 0.6.3` source reading으로 확인 (2026-05-28). Source: `deepagents-venv-create-deep-agent-2026-05-28`

---

## LangChain

- Custom stream transformer의 정확한 계약(contract)은 무엇인가? (required_stream_modes, push() 메서드?) — Needs Source

### 메시지 시스템

- `BaseMessage` 클래스 계층은 어떻게 구성되는가? (SystemMessage/HumanMessage/AIMessage/ToolMessage 외에 14개 중 나머지 10개는 무엇인가?) — Needs Source (공식 문서에서 4종만 확인됨). 4종의 역할·입력 형식은 [[Messages]] 페이지에 정리됨. Source: `langchain-docs-messages-2026-05-30`
- `AIMessage.tool_calls` 정확한 스키마와 ToolMessage의 `tool_call_id` 매칭 방식은? — Needs Source ([[Tool Calling]] 소스 확인 필요)
- standard content block의 전체 스펙(멀티모달 블록 타입)과 message metadata의 token usage 필드 구조는? — Needs Source (원문에 token usage는 TODO로 표시됨). Source: `langchain-docs-messages-2026-05-30`

### 모델 / Chat Models (책 1.1~1.2)

- top_p / top_k 등 sampling 파라미터의 정확한 의미와 temperature와의 상호작용은? — Needs Source (LangChain Models 문서는 temperature·max_tokens만 상세 설명; Anthropic/OpenAI API 레퍼런스 필요). Source: `langchain-docs-models-2026-05-30`
- token이 실제로 어떻게 분할되는가(tokenizer/BPE)? — Needs Source (공식 문서는 정의만 제시)
- `init_chat_model`의 내부 구현은? (`"openai:o1"` 문자열 파싱, provider 패키지 lazy import/라우팅) — Needs Source (소스 코드 확인 필요). Source: `langchain-docs-models-2026-05-30`

### PromptTemplate / OutputParser

- `FewShotPromptTemplate`에서 예시 선택기(`ExampleSelector`)는 어떻게 동작하는가? — Needs Source
- `PipelinePromptTemplate`에서 여러 템플릿을 연결하는 내부 방식은? — Needs Source

### Runnable 인터페이스

- `RunnableParallel`의 thread pool thread 수 제한은? `max_concurrency` 옵션이 있는가? — Needs Verification (`base.py` 전체 미수집)
- `RunnableSequence.invoke` 내부: 각 step 간 에러 처리는 어떻게 되는가? — Needs Source (`base.py` 부분 수집만)
- `RunnableConfig`의 `configurable` 필드를 통해 실행 시간 설정을 주입하는 방법은? — Needs Source

### RAG / 임베딩 / 벡터 스토어 / 리트리버

- ⚠️ FAISS `similarity_search`의 내부 알고리즘 (L2 거리 기본값인가?) — Needs Source (GitHub 파일 접근 실패)
- ⚠️ FAISS 거리 점수와 cosine similarity 관계, 변환 공식 — Needs Source
- `init_embeddings("openai:text-embedding-3-small")` 형식은 새로운 API인가? 구버전 `OpenAIEmbeddings()`와의 차이는? — Source: `langchain-docs-rag-2026-05-23`
- `response_format="content_and_artifact"` 옵션의 정확한 의미는? — Source: `langchain-docs-rag-2026-05-23`
- `_merge_splits()`의 `chunk_overlap` 구현 방식은? 슬라이딩 윈도우인가? — Source: `langchain-source-text-splitters-2026-05-23`
- `wrap_model_call` 데코레이터의 전체 서명과 `before_model` hook과의 차이는? — ✅ **검증됨** (2026-05-28): `wrap_model_call`은 handler를 직접 감싸 모델 호출 자체를 가로채는 반면, `before_model`은 상태/메시지 변환만 함. [[LLMToolSelectorMiddleware]] = wrap_model_call, [[SummarizationMiddleware]] = before_model 참고. Source: `langchain-source-builtin-middleware-2026-05-25`
- 빌트인 미들웨어(`summarization.py`, `pii.py`, `tool_selection.py` 등) 내부 구현은? — ✅ **해소됨** (2026-05-26): [[SummarizationMiddleware]], [[LLMToolSelectorMiddleware]], [[PIIMiddleware]] 위키 페이지 작성 완료. Source: `langchain-source-builtin-middleware-2026-05-25`
- `wrap_tool_call`이 `Command`를 반환할 때 어떤 상태 변화가 가능한가? — ✅ **검증됨**: current graph 기준 `Command.update`는 compiled graph state에 적용되고 `Command.goto`는 정적 edge 없이 대상 노드로 라우팅할 수 있다(2026-05-29). child graph의 `ToolNode`가 `Command(graph=Command.PARENT, goto=[Send(...)])`를 반환하면 parent graph 노드가 동적으로 실행된다(2026-05-30). Source: [[2026-05-29 langgraph toolnode command outputs]], [[2026-05-30 langgraph toolnode parent command send]]
- `ModelRetryMiddleware` + `ModelFallbackMiddleware` 조합 시 어떤 미들웨어의 `wrap_model_call`이 외부를 감싸는가? (등록 순서에 따라 다름인지 확인 필요) — Needs Verification
- `request.override(model=...)` 내부 구현: `ModelRequest`의 immutable copy 패턴인가, shallow copy인가? — ✅ **검증됨**: `ModelRequest.override()`는 새 `ModelRequest` 인스턴스를 반환하는 immutable-style replace 패턴이다. Source: `langchain-agents-middleware-types-2026-05-28`
- `ToolRetryMiddleware`가 `Command` 반환 도구와 함께 동작할 때 재시도 후 `Command` 반환은 어떻게 처리되는가? — Needs Source

---

## LangGraph

### 그래프 기초

- LangGraph에서 cyclic graph는 내부적으로 어떻게 무한 루프를 방지하는가? — ✅ 해소 (2026-05-24, `_loop.py` 직접 확인). `stop = step + recursion_limit + 1`. 매 superstep마다 `step += 1`. `step > stop` 이면 `status="out_of_steps"`. `main.py`에서 `GraphRecursionError` 발생. 기본값 `recursion_limit=25` (`ensure_config()` 확인). Source: `langgraph-venv-loop-py-2026-05-24`
- `add_conditional_edges`의 두 번째 인수(path_map)는 선택인가 필수인가? 없을 때 동작 방식은? — ✅ 해소 (2026-05-25, `graph/_branch.py` + `state.py` 직접 확인). **선택** (`path_map: dict | list | None = None`). None 시 path 함수 반환값이 그대로 노드명으로 사용됨. `Literal[...]` 리턴 타입 힌트가 있으면 자동으로 `{name: name}` dict로 변환. list 제공 시도 `{name: name}` dict로 변환. `BranchSpec.from_path()` line 96-116 확인. Source: `.venv/langgraph/graph/_branch.py`
- `TypedDict` vs `Pydantic` 상태 스키마의 실질적인 차이는? (런타임 유효성 검사, 직렬화)
- `NodeRuntime.control`과 `NodeRuntime.heartbeat`의 구체적인 사용 사례는? — Source: `langgraph-docs-graph-api-2026-05-23`
- `Send` 사용 시 각 worker 결과를 집계하는 reduce 단계 Reducer 설계 패턴은? — ✅ 해소 (2026-05-25, 직접 실행). `Annotated[list[str], add]` Reducer로 병렬 worker 결과 누적. `Send`의 state는 worker 전용 격리 입력. Source: `langgraph-subgraph-experiment-2026-05-25`
- LangGraph 서브그래프와 상위 그래프 간 상태 스키마 호환성 요구사항은? — ✅ 해소 (2026-05-25, 직접 실행). **공유 키만** 부모↔서브그래프 전달. 서브그래프 전용 키는 부모 출력에서 제외. 공유 키 없어도 에러 없음(조용히 무시됨). `input_schema`/`output_schema`로 인터페이스 제한 가능. Source: `langgraph-subgraph-experiment-2026-05-25`
- `Command(resume=value, goto="...")` 패턴은 `interrupt()`와 어떻게 연동되는가? — ✅ 해소 (2026-05-24, `_loop.py` + `types.py` 직접 확인) → `HumanInTheLoop.md` 참조. Source: `langgraph-venv-types-py-hitl-2026-05-24`, `langgraph-venv-loop-py-2026-05-24`

### Checkpointer

- `thread_id` 없이 `invoke`를 호출하면 어떤 에러가 발생하는가? — ✅ 해소 (2026-05-25, 직접 실행 확인). **checkpointer 없으면 thread_id 유무에 무관하게 정상 동작**. checkpointer 있고 thread_id 없으면 `ValueError: Checkpointer requires one or more of the following 'configurable' keys: thread_id, checkpoint_ns, checkpoint_id`. Source: 직접 실행
- `StateGraph.compile()` 이후 `Pregel.validate()`는 정확히 어떤 구조 검사를 수행하는가? — ✅ 해소 (2026-05-24): `_validate.py validate_graph()` 직접 확인. RESERVED 충돌, 구독 channel 존재, input/output/stream channel 존재, interrupt 노드 존재 검사.
- `DeltaChannel` reconstruction/pruning/copying safety를 검증하는 test: `test_delta_channel_migration.py` ✅ 읽음 (2026-05-24) — 9개 시나리오. `test_delta_channel_exit_mode.py` ✅ 읽음 (2026-05-24) — 11개 시나리오, lazy stub(step=-2), per-invoke 2 updates.
- `DeltaChannel`의 `snapshot_frequency` 기본값: ✅ 해소 (2026-05-24, `channels/delta.py` 직접 확인) — **1000** (update 횟수 기준). `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` = **5000**.
- `exit` durability에서 `_put_exit_delta_writes()` 검증: ✅ 해소 (2026-05-24, `test_delta_channel_exit_mode.py`) — lazy stub(step=-2), count-based snapshot, sync/exit 카운터 동등성 확인
- `saver.get_delta_channel_history()` 메서드의 `InMemorySaver` 최적화 override vs `BaseCheckpointSaver` fallback 구현 상세: ✅ 해소 (2026-05-24) — InMemorySaver는 chain 1회 구성 + direct blob 조회 + `_DeltaSnapshot` 분기. fallback은 `get_tuple()` N번 호출. 양쪽 동일 결과.
- `DeltaChannel` 자체 구현: ✅ 해소 (2026-05-24, `channels/delta.py` 전체 읽음) — `from_checkpoint(3분기)`, `replay_writes(Overwrite handling)`, `update()`, `checkpoint()=항상 MISSING`
- checkpoint schema migration 또는 state schema 변경 대응은 공식적으로 어떻게 권장되는가? — Needs Source
- `astream_events`와 함께 스트리밍은 어떻게 동작하는가? — ✅ 부분 해소 (2026-05-24, `main.py` line 3605 확인). v1/v2는 langchain_core `Runnable.stream_events` 위임. v3는 LangGraph-native `GraphRunStream` (실험적). `stream(stream_mode="updates")` 로 interrupt 이벤트 확인 가능 (`__interrupt__` 키). Source: `langgraph-venv-loop-py-2026-05-24`
- LangGraph package version과 reference docs version의 관계는? GitHub page는 `langgraph==1.2.0`, `StateGraph.compile` reference는 v1.1.10으로 보였다. — Source: `langgraph-reference-stategraph-compile-2026-05-20`

### Memory Store

- 프로덕션용 Store 구현체(Redis, PostgreSQL)는 어떤 패키지에 있는가? — ⚠️ 가설 수준 (`langgraph-checkpoint-postgres`, `langgraph-checkpoint-redis` 추정, 직접 확인 필요)
- `InMemoryStore`의 vector search 지원: ✅ 해소 (2026-05-25, `.venv/langgraph/store/memory/__init__.py` 직접 확인). `index` 파라미터로 vector search 활성화. `_data`(dict)/`_vectors`(dict) 이중 저장, cosine similarity. Source: `langgraph-venv-store-memory-2026-05-25`
- `create_deep_agent`에서 Store는 어떤 middleware가 어떻게 활용하는가? (`MemoryMiddleware`와의 관계?) — Needs Source

---

## Deep Agents

- ACP (Agent Client Protocol) integration은 어떤 프로토콜 스펙을 따르는가? — Source: `deepagents-docs-overview-2026-05-18`
- Deep Agents Code (터미널 에이전트)는 SDK를 어떻게 확장하는가? — Source: `deepagents-docs-overview-2026-05-18`
- `HarnessProfile`은 어떤 모델에 어떤 profile을 매핑하나? (`harness_profiles.py` 수집 필요) — Source: `deepagents-source-graph-2026-05-19`
- `DeltaChannel`의 `snapshot_frequency=50`은 정확히 무엇을 의미하나? — ✅ 부분 해소 (2026-05-24): update(write) 횟수가 `snapshot_frequency`에 도달하거나 super-step 수가 `DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT`에 도달하면 스냅샷. 50이면 50 writes.
  재구성 비용은 아직 미확인 (ancestor walk 깊이 및 비용). — Needs Source
- Skills frontmatter 형식은 무엇이며 agent는 어떻게 관련성을 판단하는가? — Source: `deepagents-docs-context-engineering-2026-05-18`
- `@dynamic_prompt` 데코레이터의 정확한 시그니처와 사용 패턴은? — Source: `deepagents-docs-context-engineering-2026-05-18`
- `register_harness_profile` entry points 패키징 방법은? — Source: `deepagents-docs-harness-2026-05-19`
- 빌트인 profile(`_builtin_profiles`)에는 어떤 모델에 어떤 profile이 등록되어 있는가? — Source: `deepagents-source-harness-profiles-2026-05-19`
- `serialized_name: ClassVar[str]`을 가지는 공식 middleware는 어떤 것들이 있는가? (`SummarizationMiddleware` 등) — Source: `deepagents-source-harness-profiles-2026-05-19`
- `excluded_middleware`에 매칭되지 않는 entry가 있을 때 rejection은 생성 시점인가, 조립 시점인가? — Source: `deepagents-source-harness-profiles-2026-05-19`
- Sandbox backend 없을 때 `execute` tool은 error 반환인가, tool 목록에서 제외되는가? — ✅ **검증됨** (2026-05-28): `FilesystemMiddleware`는 `execute` tool을 생성하지만, 기본 `StateBackend`가 `SandboxBackendProtocol`을 지원하지 않으면 `wrap_model_call()`에서 model bind 전 `request.tools`에서 제거한다. `_create_execute_tool()` 내부에는 non-sandbox error `ToolMessage` 경로도 존재한다. Source: `deepagents-venv-create-deep-agent-2026-05-28`
- `SubAgentMiddleware`는 parent state를 subagent에 어떻게 전달하고 결과를 어떻게 병합하는가? — ✅ **검증됨** (2026-05-30): `task` tool 실행 시 `_EXCLUDED_STATE_KEYS`가 입력/출력 양방향으로 적용된다. 예제에서 child는 `messages`, `project_id`만 받았고 parent `todos`는 받지 않았다. child `summary`는 parent에 병합됐지만 child `todos`는 병합되지 않았다. Source: [[2026-05-30 deepagents subagentmiddleware task tool]]
- 단일 parent `AIMessage`가 여러 `task` tool call을 반환하면 subagents는 병렬 실행되는가? — ✅ **검증됨** (2026-05-30): slow/fast task가 같은 시점에 시작했고 fast가 먼저 끝났다. parent `ToolMessage`와 reducer state merge 순서는 완료 순서가 아니라 원래 tool call 순서를 따랐다. Source: [[2026-05-30 deepagents parallel task tool calls]]
- Sandbox backend를 실제로 붙였을 때 `execute` tool 결과 payload는 어떤 message shape인가? — Needs Experiment
- Interpreter (`eval` tool, QuickJS)는 어떤 패키지에 포함되어 있는가? — Source: `deepagents-docs-harness-2026-05-19`
- LLM-as-a-judge에서 구체적으로 어떤 judge 모델을 사용하는가? → `MODEL_GROUPS.md` 확인 필요. (Source: `deepagents-blog-evals-2026-05-23`, `deepagents-source-evals-structure-2026-05-23`)
- BFCL 벤치마크도 Harbor를 통해 동일하게 적용되는가? — Needs Source
- eval을 지속적으로 "줄이는(reduce)" 기준은 무엇인가? — Source: `deepagents-blog-evals-2026-05-23`

---

## 에이전트 런타임 / 에이전트 구성 요소

### 에이전트 런타임 (Agent Runtime)

- 에이전트 런타임(모델 + 오케스트레이션 + 도구)은 LangChain / LangGraph / Deep Agents에서 각각 어떤 클래스/컴포넌트로 구현되는가? — **부분 검증됨**: LangChain = `create_agent` → CompiledStateGraph, LangGraph = `StateGraph.compile()` / `create_react_agent`, Deep Agents = `create_deep_agent` → middleware stack → `langchain.agents.create_agent` → CompiledStateGraph. Source: `deepagents-venv-create-deep-agent-2026-05-28`
- 오케스트레이션 레이어의 인스트럭션(시스템 프롬프트)은 각 프레임워크에서 어떻게 설정하는가? — **검증됨**: `create_agent` → `system_prompt=`, `create_react_agent` → `prompt=`. 동적 변경 여부: Needs Source
- `instructions`와 `system_prompt`는 같은 개념인가? — **부분 검증됨**: `create_agent`=`system_prompt=`, `create_react_agent`=`prompt=`, Deep Agents `create_deep_agent`=`system_prompt=`. 명칭이 다르지만 "system-level instruction" 역할은 유사하다. Source: `deepagents-venv-create-deep-agent-2026-05-28`

### 리즈닝 / 플래닝 (Reasoning / Planning)

- 리즈닝/플래닝은 LLM이 자체적으로 수행하는가, 아니면 프레임워크가 특별히 지원하는 기능(ReAct, CoT 등)인가? — Needs Source
- Deep Agents `create_deep_agent`에서 planning 전용 노드가 별도로 존재하는가, 아니면 단일 LLM 노드가 암묵적으로 reasoning + acting을 수행하는가? — Needs Source (관련: `deepagents-source-graph-2026-05-19`)
- ReAct 패턴, Chain-of-Thought, Plan-and-Execute 중 각 프레임워크가 기본으로 채택하는 방식은 무엇인가? — Needs Source

### 가드레일 (Guardrails)

- LangChain / LangGraph / Deep Agents에서 가드레일(입력 필터링, 출력 검증, 금칙어, 정책 준수)을 구현하는 표준 패턴 또는 전용 API는? — Needs Source
- Deep Agents에 `InputGuardrail` / `OutputGuardrail` 같은 전용 클래스가 있는가? middleware로 구현되는가? — Needs Source (관련: `deepagents-source-harness-profiles-2026-05-19`)
- JSON 스키마 기반 출력 검증은 `with_structured_output`으로 충분한가, 별도 가드레일 레이어가 추가로 필요한가? — Needs Source (관련: `langchain-source-output-parsers-2026-05-23`)
- RAG Indirect Prompt Injection 방어를 위한 가드레일 구현 패턴은? — Needs Source (관련: `langchain-docs-rag-2026-05-23`)

### 핸드오프 (Handoffs)

- 핸드오프가 "특별한 도구 호출"로 구현된다면, LangGraph / Deep Agents에서 어떤 API/클래스를 사용하는가? — Needs Source (OpenAI SDK: `handoff()` 함수, tool name `transfer_to_<agent_name>` 방식은 확인됨)
- 핸드오프 시 메시지 히스토리와 상태는 대상 에이전트로 전달되는가? Deep Agents의 `_EXCLUDED_STATE_KEYS` 패턴과의 관계는? — Needs Source
- LangGraph의 `Command(goto=...)` 패턴이 핸드오프로 사용될 수 있는가? — Needs Source (관련: `langgraph-docs-graph-api-2026-05-23`)
- LangGraph에서 LLM이 tool call로 핸드오프를 트리거하는 패턴이 존재하는가? — Needs Source

### 트레이싱 (Tracing)

- LangChain / LangGraph / Deep Agents의 트레이싱은 LangSmith와 어떻게 통합되는가? (자동 instrumenting vs 명시 설정?) — Needs Source
- 그래프 스텝별 input/output을 프로그래밍 방식으로 접근하는 API는? (`stream_mode="debug"` 등?) — Needs Source (관련: `langgraph-source-streaming-2026-05-23`)
- Deep Agents의 트레이싱 구현체는 별도로 존재하는가, LangGraph Pregel 기반인가? — Needs Source

---

## 프레임워크 간 비교

- 세 프레임워크는 병렬 도구 호출 처리에서 어떻게 비교되는가?
- human-in-the-loop 지원이 가장 좋은 프레임워크는 무엇인가?
- 각 프레임워크는 컨텍스트 윈도우 한계를 어떻게 처리하는가?
- 한 프레임워크의 체크포인트를 다른 프레임워크로 이식할 수 있는가?
- LangChain "Skills"와 Deep Agents "Skills"는 동일한 개념인가? — Source: `langchain-docs-products-2026-05-23`
- Temporal, Inngest가 LangGraph와 같은 Runtime 범주라면 실질적 차이는? — Source: `langchain-docs-products-2026-05-23`
- Harness가 Runtime의 `interrupt` / checkpoint를 어떻게 추상화하는가? — Source: `langchain-docs-products-2026-05-23`
