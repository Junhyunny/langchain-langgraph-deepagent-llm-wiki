# 미해결 질문

학습 중 수집한 질문이다. 해결되면 관련 페이지로 옮기거나 삭제한다.

---

## LangChain

- agent executor는 언제 도구 호출을 멈출지 어떻게 결정하는가?
- `AgentExecutor`와 `create_react_agent`의 차이는 무엇인가?
- 메시지 히스토리는 내부적으로 어디에서 관리되는가?
- `stream_events` v3와 이전 버전의 차이는 무엇인가? — Source: `langchain-docs-event-streaming-2026-05-18`
- LangGraph의 Pregel stream mode와 Event Streaming(`stream_events`)의 정확한 관계는? — Source: `langchain-docs-event-streaming-2026-05-18`
- Custom stream transformer의 계약(contract)은 무엇인가? — Source: `langchain-docs-event-streaming-2026-05-18`
- Deep Agents의 `create_deep_agent`도 `stream_events`를 동일하게 지원하는가? — Source: `langchain-docs-event-streaming-2026-05-18`
- `astream_events`와 `astream_log`의 차이는? 반환 타입은? — Source: `langchain-source-runnable-2026-05-23`
- `RunnableParallel`의 thread pool 크기 제한은? `max_concurrency` 옵션이 있는가? — Source: `langchain-source-runnable-2026-05-23`
- `ConversationBufferMemory`, `ConversationSummaryMemory`는 현재도 권장 API인가, deprecated인가? — Needs Source
- `MessagesPlaceholder(optional=False)`일 때 해당 변수가 없으면 KeyError가 발생하는가 확인 필요 — Source: `langchain-source-prompts-2026-05-23`

### 메시지 시스템 (소스 수집 필요)

- `BaseMessage` 클래스 계층은 어떻게 구성되는가? (SystemMessage/HumanMessage/AIMessage/ToolMessage 외에 14개 중 나머지 10개는 무엇인가?)
- `ToolMessage`의 `tool_call_id`는 `AIMessage`의 `tool_calls`와 어떻게 연결되는가?
- 채팅 모델 호출 시 메시지 리스트를 어떻게 전달하는가? (`invoke` vs `batch` vs `stream`)
- `AIMessage`의 `tool_calls` 필드 구조는 어떻게 되는가?

### PromptTemplate / OutputParser

- `FewShotPromptTemplate`에서 예시 선택기(`ExampleSelector`)는 어떻게 동작하는가? — Source: `langchain-source-prompts-2026-05-23`
- `PipelinePromptTemplate`에서 여러 템플릿을 연결하는 내부 방식은? — Source: `langchain-source-prompts-2026-05-23`
- `PydanticOutputParser`는 LLM 출력 텍스트를 Pydantic 모델로 어떻게 변환하는가? — Source: `langchain-source-prompts-2026-05-23`
- `with_structured_output`과 `OutputParser`의 관계는? 내부적으로 같은 메커니즘을 사용하는가? — Source: `langchain-source-prompts-2026-05-23`
- `OutputParser`의 `get_format_instructions()`는 프롬프트에 어떻게 주입되는가? — Source: `langchain-source-prompts-2026-05-23`
- `with_structured_output`이 지원하는 4가지 타입(Pydantic, OpenAI function schema, JSON schema, TypedDict)은 내부적으로 어떻게 처리가 다른가?

**해소됨 (2026-05-23):**
- ✅ `PromptTemplate`과 `ChatPromptTemplate`의 내부 구현 차이는? → PromptTemplate: 단일 문자열 포맷 (`StringPromptTemplate` 상속), ChatPromptTemplate: 메시지 리스트 기반. 둘 다 `Runnable` 상속. (Source: `langchain-source-prompts-2026-05-23`)

### Runnable 인터페이스

- `RunnableLambda`와 일반 함수를 직접 사용하는 것의 차이는? (에러 처리, 스트리밍, 배치 지원) — invoke/batch/stream 인터페이스가 자동 부여됨은 확인, 에러 처리 차이는 Needs Verification. Source: `langchain-source-runnable-2026-05-23`
- `RunnableParallel`의 thread pool thread 수 제한은? `max_concurrency` 옵션이 있는가? — Source: `langchain-source-runnable-2026-05-23`
- `RunnableSequence.invoke` 내부: 각 step 간 에러 처리는 어떻게 되는가? — Source: `langchain-source-runnable-2026-05-23`
- `astream_events`와 `astream_log`의 차이는? — Source: `langchain-source-runnable-2026-05-23`
- `RunnableConfig`의 `configurable` 필드를 통해 실행 시간 설정을 주입하는 방법은? — Source: `langchain-source-runnable-2026-05-23`

**해소됨 (2026-05-23):**
- ✅ LCEL `|` 연산자는 내부적으로 어떤 타입을 생성하는가? → `RunnableSequence`. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `Runnable` 인터페이스의 최소 계약은? → `invoke`만 abstract. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `RunnableParallel`은 실제로 동시 실행되는가? → sync: thread pool, async: asyncio 동시 실행. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `RunnableParallel`의 결과 dict 키는 어떻게 결정되는가? → input mapping의 keys와 동일. (Source: `langchain-source-runnable-2026-05-23`)

### @tool 데코레이터

**해소됨 (2026-05-23):**
- ✅ `@tool` 데코레이터로 만든 tool의 내부 타입은? → `StructuredTool` (infer_schema=True 기본값). infer_schema=False이고 args_schema=None이면 단순 `Tool`. (Source: `langchain-source-tools-2026-05-23`)
- ✅ LLM tool call 응답 → tool 실행 → ToolMessage 반환 흐름은? → `BaseTool.invoke(ToolCall)` → `_prep_run_args` → `run()` → `_to_args_and_kwargs` → `_run()` → `_format_output` → `ToolMessage(content, tool_call_id=id)`. (Source: `langchain-source-tools-2026-05-23`)
- ✅ tool docstring이 LLM에 전달되는 방식은? → `create_schema_from_function` → `_infer_arg_descriptions` → `_create_subset_model(fn_description=description)` → `model_json_schema()["description"]`. (Source: `langchain-source-tools-2026-05-23`)
- ✅ 비동기 tool 정의 방법은? → `async def`로 정의하면 `coroutine` 파라미터로 자동 처리. `StructuredTool._arun`에서 `await self.coroutine(...)` 실행. (Source: `langchain-source-tools-2026-05-23`)
- ✅ tool 실행 중 예외 처리는? → `ToolException`은 `handle_tool_error` 설정에 따라 에러 메시지 반환 or re-raise. `ValidationError`는 `handle_validation_error`로 처리. 기타 예외는 항상 re-raise. (Source: `langchain-source-tools-2026-05-23`)

**해소됨 (2026-05-23):**
- ✅ `@tool`로 만든 tool의 `args_schema.model_json_schema()`가 LLM API 호출 시 어떤 payload로 변환되는가? → `BaseTool.tool_call_schema` → `bind_tools([tool])` (provider 구현체) → `convert_to_openai_tool` → `convert_to_openai_function` → `_format_tool_to_openai_function` → `{"type": "function", "function": {...}}` OpenAI API 형식. `BaseChatModel.bind_tools`는 추상(NotImplementedError)이므로 provider별 구현 필요. (Source: `langchain-source-bind-tools-function-calling-2026-05-23`)

### RAG / 임베딩 / 벡터 스토어 / 리트리버 (소스 수집 필요)

- LangChain의 `Document` 객체 구조는? (`page_content`, `metadata` 외에 다른 필드가 있는가?)
- `CharacterTextSplitter`와 `RecursiveCharacterTextSplitter`의 알고리즘 차이는?
- chunk_overlap이 실제로 앞뒤 문맥을 보존하는 방식은 구체적으로 어떻게 구현되는가?
- FAISS의 `similarity_search`는 내부적으로 어떤 알고리즘을 사용하는가? (L2 거리 기본값인가?)
- FAISS의 거리 점수(낮을수록 유사)와 cosine similarity(높을수록 유사)의 관계는? 변환 공식은?
- LangChain이 지원하는 embedding 모델의 기본 인터페이스(`Embeddings` 클래스)는?
- `as_retriever()`의 `search_type` 옵션은 무엇인가? (`similarity`, `mmr`, `similarity_score_threshold`)
- MMR(Maximal Marginal Relevance)은 무엇이며 언제 사용하는가?
- `BaseRetriever`의 `get_relevant_documents` 메서드 계약은?
- 프로덕션 벡터 DB(Chroma, Pinecone, Weaviate, pgvector, Qdrant) 중 LangChain과 공식 통합이 가장 잘 된 것은?

## LangGraph

### 그래프 기초

- LangGraph에서 cyclic graph는 내부적으로 어떻게 무한 루프를 방지하는가? (recursion_limit 메커니즘?)
- `add_conditional_edges`의 두 번째 인수(path_map)는 선택인가 필수인가? 없을 때 동작 방식은?
- `TypedDict` vs `Pydantic` 상태 스키마의 실질적인 차이는? (런타임 유효성 검사, 직렬화)
- `NodeRuntime.control`과 `NodeRuntime.heartbeat`의 구체적인 사용 사례는? — Source: `langgraph-docs-graph-api-2026-05-23`
- `Send` 사용 시 각 worker 결과를 집계하는 reduce 단계 Reducer 설계 패턴은? — Source: `langgraph-docs-graph-api-2026-05-23`
- LangGraph 서브그래프와 상위 그래프 간 상태 스키마 호환성 요구사항은? — Needs Source
- `Command(resume=value, goto="...")` 패턴은 `interrupt()`와 어떻게 연동되는가? — Source: `langgraph-docs-graph-api-2026-05-23`

**해소됨 (2026-05-23):**
- ✅ 조건부 에지의 라우팅 함수가 반환할 수 있는 값 타입: 문자열, 문자열 리스트(병렬 팬아웃), `Send` 객체 리스트 (Source: `langgraph-docs-graph-api-2026-05-23`)
- ✅ 노드 함수 반환값: 변경된 키만 포함한 **부분 업데이트** 반환 → Reducer가 상태에 병합 (Source: `langgraph-docs-graph-api-2026-05-23`)
- ✅ `Send` API를 사용한 동적 분기: 각 `Send(node, state)`가 독립 그래프 복사본 생성 → 병렬 실행 (Source: `langgraph-docs-graph-api-2026-05-23`)
- ✅ `recursion_limit`은 `configurable` 안이 아닌 config top-level key — `{"recursion_limit": 50}` (Source: `langgraph-docs-graph-api-2026-05-23`)

### Memory / Store

### Checkpointer 종류 (소스 수집 필요)

- `SQLiteSaver`와 `PostgresSaver`의 설정 방법과 `InMemorySaver`와의 실질적 차이는?
- `thread_id` 없이 `invoke`를 호출하면 어떤 에러가 발생하는가?
- checkpointer가 있을 때 같은 `thread_id`로 재실행하면 이전 상태부터 이어서 실행되는가?
- `config = {"configurable": {"thread_id": "..."}}` 패턴은 내부적으로 어떤 경로로 checkpointer에 전달되는가?
- `InMemorySaver`의 `storage`, `writes`, `blobs` 딕셔너리 구조는 어떻게 되는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`

- `StateGraph.compile()` 이후 `Pregel.validate()`는 정확히 어떤 구조 검사를 수행하는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `libs/langgraph/langgraph/pregel/_checkpoint.py`의 `create_checkpoint`, `channels_from_checkpoint`, delta-channel reconstruction은 어떻게 구현되어 있는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- pending writes recovery를 정의하는 canonical test는 어디에 있는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `DeltaChannel` reconstruction/pruning/copying safety를 검증하는 test는 어디에 있는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `exit` durability에서 `_put_exit_delta_writes()`를 검증하는 test는 어디에 있는가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- checkpoint schema migration 또는 state schema 변경 대응은 공식적으로 어떻게 권장되는가? — Source: `langgraph-docs-persistence-2026-05-20`
- `interrupt_before` / `interrupt_after`는 그래프 수준에서 어떻게 동작하는가?
- `MemorySaver`와 persistent saver의 운영상 차이는 무엇인가? async behavior, serialization, retention/pruning API의 버전 차이를 확인해야 한다. — Source: `langgraph-reference-checkpoint-2026-05-20`
- `MemorySaver`와 `InMemorySaver`는 동일한 클래스인가, 다른 클래스인가? — Source: `langgraph-source-checkpoint-runtime-2026-05-20`
- `astream_events`와 함께 스트리밍은 어떻게 동작하는가?
- LangGraph package version과 reference docs version의 관계는? GitHub page는 `langgraph==1.2.0`, `StateGraph.compile` reference는 v1.1.10으로 보였다. — Source: `langgraph-reference-stategraph-compile-2026-05-20`

### Memory Store

**해소됨 (2026-05-23):**
- ✅ `BaseStore` 인터페이스의 핵심 계약: `batch`/`abatch` 추상 메서드 2개. 나머지(`get`, `put`, `search`, `delete`, `list_namespaces`)는 모두 이것의 래퍼. (Source: `langgraph-store-base-2026-05-23`)
- ✅ `store.get(namespace, key)` 반환: `Item | None`. `store.put(namespace, key, value)` 반환: `None`. `value=None` → 삭제. (Source: `langgraph-store-base-2026-05-23`)
- ✅ namespace 개념: `tuple[str, ...]` 계층 경로 — `("user", "123", "memories")` 형식. (Source: `langgraph-store-base-2026-05-23`)
- ✅ `Item` 필드: `value: dict`, `key: str`, `namespace: tuple[str, ...]`, `created_at`, `updated_at`. (Source: `langgraph-store-base-2026-05-23`)
- ✅ `search`의 `query` 파라미터: semantic search용 (구현체가 vector store 지원 시에만 의미 있음). (Source: `langgraph-store-base-2026-05-23`)

**잔여 질문:**
- `InMemoryStore`의 구체적 구현은? vector search를 지원하는가? — Source: `langgraph-store-base-2026-05-23`
- 프로덕션용 Store 구현체(Redis, PostgreSQL)는 어떤 패키지에 있는가? — Needs Source
- `create_deep_agent`에서 Store는 어떤 middleware가 어떻게 활용하는가? (`MemoryMiddleware`와의 관계?) — Needs Source

**해소됨 (2026-05-20):**
- ✅ 체크포인팅은 무엇을 저장하고 무엇을 버릴지 어떻게 결정하는가? → LangGraph는 super-step boundary마다 `StateSnapshot` checkpoint를 저장하고, super-step 내부의 task-level writes도 pending writes로 저장한다. State에 포함되지 않은 외부 side effect나 thread 간 memory는 자동 저장 대상이 아니다. (Source: `langgraph-docs-persistence-2026-05-20`, `langgraph-reference-checkpoint-2026-05-20`)
- ✅ `StateGraph.compile(checkpointer=...)`에서 checkpointer는 어디에 attach되는가? → `state.py`에서 `CompiledStateGraph(..., checkpointer=checkpointer, ...)`에 전달되고, `CompiledStateGraph`는 `Pregel`을 상속한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)
- ✅ `InMemorySaver`의 내부 자료구조는? → `storage`, `writes`, `blobs`로 checkpoint record, pending writes, channel-version blobs를 분리한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)
- ✅ `exit` / `async` / `sync` durability mode는 runtime source에서 어디에 구현되는가? → `_defaults()` 기본값은 `"async"`, `"sync"`는 tick 뒤 checkpoint future를 기다리고, `"exit"`는 `put_writes()` immediate persistence를 건너뛰고 loop exit에서 checkpoint/writes를 저장한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)

## Deep Agents

- subagent state isolation의 구체적 메커니즘은? (`SubagentTransformer`, `SubAgentMiddleware` 내부 확인 필요) — Source: `deepagents-source-graph-2026-05-19`
- ACP (Agent Client Protocol) integration은 어떤 프로토콜 스펙을 따르는가? — Source: `deepagents-docs-overview-2026-05-18`
- Deep Agents Code (터미널 에이전트)는 SDK를 어떻게 확장하는가? — Source: `deepagents-docs-overview-2026-05-18`
- `langchain.agents.create_agent`의 내부 구현은? LangGraph `StateGraph`를 어떻게 조립하나? — Source: `deepagents-source-graph-2026-05-19`
- `HarnessProfile`은 어떤 모델에 어떤 profile을 매핑하나? (`harness_profiles.py` 수집 필요) — Source: `deepagents-source-graph-2026-05-19`
- `PatchToolCallsMiddleware`는 어떤 tool call 패치를 수행하나? — Source: `deepagents-source-graph-2026-05-19`
- `DeltaChannel`의 `snapshot_frequency=50`은 정확히 무엇을 의미하나? 50 super-step인가 50 message인가? full snapshot과 delta 사이 재구성 비용은? — Source: `deepagents-source-graph-2026-05-19` (소스코드 직접 확인 필요: `_messages_reducer.py` + LangGraph `DeltaChannel` 구현)
- Skills frontmatter 형식은 무엇이며 agent는 어떻게 관련성을 판단하는가? — Source: `deepagents-docs-context-engineering-2026-05-18`
- `@dynamic_prompt` 데코레이터의 정확한 시그니처와 사용 패턴은? — Source: `deepagents-docs-context-engineering-2026-05-18`

- `register_harness_profile` entry points 패키징 방법은? — Source: `deepagents-docs-harness-2026-05-19`
- 빌트인 profile(`_builtin_profiles`)에는 어떤 모델에 어떤 profile이 등록되어 있는가? — Source: `deepagents-source-harness-profiles-2026-05-19`
- `serialized_name: ClassVar[str]`을 가지는 공식 middleware는 어떤 것들이 있는가? (`SummarizationMiddleware` 등) — Source: `deepagents-source-harness-profiles-2026-05-19`
- `excluded_middleware`에 매칭되지 않는 entry가 있을 때 rejection은 생성 시점인가, 조립 시점인가? — Source: `deepagents-source-harness-profiles-2026-05-19`
- Sandbox backend 없을 때 `execute` tool은 error 반환인가, tool 목록에서 제외되는가? — Source: `deepagents-docs-harness-2026-05-19`
- Interpreter (`eval` tool, QuickJS)는 어떤 패키지에 포함되어 있는가? — Source: `deepagents-docs-harness-2026-05-19`
- 외부 벤치마크(BFCL, Terminal Bench 2.0)를 "adapting"하는 구체적인 방법은? — Source: `deepagents-blog-evals-2026-05-23`
- LLM-as-a-judge에서 어떤 judge 모델을 사용하는가? — Source: `deepagents-blog-evals-2026-05-23`
- `libs/evals` 디렉토리의 실제 eval 구현 구조는? — Source: `deepagents-blog-evals-2026-05-23`
- eval을 지속적으로 "줄이는(reduce)" 기준은 무엇인가? — Source: `deepagents-blog-evals-2026-05-23`

**해소됨 (2026-05-23):**
- ✅ `HarnessProfile`의 전체 필드 목록은? → 7개: `base_system_prompt`, `system_prompt_suffix`, `tool_description_overrides`, `excluded_tools`, `excluded_middleware`, `extra_middleware`, `general_purpose_subagent` (Source: `deepagents-source-harness-profiles-2026-05-19`)
- ✅ Provider-level vs model-level HarnessProfile의 merge 우선순위는? → exact + provider 둘 다 매칭 시 `_merge_profiles(provider, exact)` — scalar 필드는 model-level(override) 우선, set 필드는 union (Source: `deepagents-source-harness-profiles-2026-05-19`)

**해소됨 (2026-05-19):**
- ✅ `create_deep_agent` 내부에서 LangGraph의 어떤 graph를 생성하는가? → `langchain.agents.create_agent`에 위임 → `CompiledStateGraph` 반환 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ `create_deep_agent`와 LangChain `create_agent`의 내부 구조 차이는? → middleware 조립 후 `create_agent` 위임 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ `graph.py`의 base agent prompt는 어떤 내용인가? → `BASE_AGENT_PROMPT` 상수, graph.py 직접 정의 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ "durable execution"이 LangGraph checkpointing과 어떻게 연결되는가? → `checkpointer` 파라미터 + `_DeepAgentState` `DeltaChannel` (Source: `deepagents-source-graph-2026-05-19`)
- ✅ Offloading backend 기본값은? → `StateBackend()` (Source: `deepagents-source-graph-2026-05-19`)
- ✅ filesystem tools 목록 확인: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute` (Source: `deepagents-docs-harness-2026-05-19`)
- ✅ `HarnessProfile` 등록 방법: `register_harness_profile(key, HarnessProfile(...))` (Source: `deepagents-docs-harness-2026-05-19`)

## 프레임워크 간 비교

- 세 프레임워크는 병렬 도구 호출 처리에서 어떻게 비교되는가?
- human-in-the-loop 지원이 가장 좋은 프레임워크는 무엇인가?
- 각 프레임워크는 컨텍스트 윈도우 한계를 어떻게 처리하는가?
- 한 프레임워크의 체크포인트를 다른 프레임워크로 이식할 수 있는가?
- LangChain "Skills"와 Deep Agents "Skills"는 동일한 개념인가? — Source: `langchain-docs-products-2026-05-23`
- Temporal, Inngest가 LangGraph와 같은 Runtime 범주라면 실질적 차이는? — Source: `langchain-docs-products-2026-05-23`
- Harness가 Runtime의 `interrupt` / checkpoint를 어떻게 추상화하는가? — Source: `langchain-docs-products-2026-05-23`

## PR 기회

- 세 저장소에 테스트 없는 문서화된 이슈가 존재하는가?
- 체크포인팅 구현에 빠진 엣지 케이스 테스트가 있는가?
