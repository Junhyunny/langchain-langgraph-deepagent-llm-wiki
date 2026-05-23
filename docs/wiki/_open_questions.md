# 미해결 질문

학습 중 수집한 질문이다. 해결되면 관련 페이지로 옮기거나 삭제한다.

---

## 이번 주 우선순위 큐 (2026-05-23)

- [ ] LangGraph checkpoint pending writes canonical test 경로/회귀 루트를 확정한다.  
  Source: `langgraph-tests-checkpoint-recovery-2026-05-23`
- [ ] Deep Agents eval에서 LLM-as-a-judge 모델 결정 경로를 확정한다 (`MODEL_GROUPS.md` 연계 포함).  
  Source: `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
- [ ] BFCL v3 평가가 실제 실행 경로(테스트/워크플로)에서 어떻게 연결되는지 확정한다.  
  Source: `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`

---

## LangChain

- `RunnableParallel`의 thread pool 크기 제한은? `max_concurrency` 옵션이 있는가? — Source: `langchain-source-runnable-2026-05-23`

**해소됨 (2026-05-23):**
- ✅ `agent executor`는 언제 도구 호출을 멈출지 어떻게 결정하는가? → `create_agent` 내부에서 `add_conditional_edges()`로 구현: model node의 출력에 `tool_calls`가 없으면 `after_agent` → `END`, 있으면 `tools node` → model node 루프. `AgentExecutor` while loop는 현재 API에 없음. (Source: `langchain-source-create-agent-factory-2026-05-23`)
- ✅ `AgentExecutor`와 `create_react_agent`의 차이는 무엇인가? → 둘 다 **deprecated**. `create_tool_calling_agent` + `AgentExecutor`는 구버전 LangChain 패턴. `create_react_agent`는 LangGraph prebuilt 함수로 별개 API. 현재 공식 API는 `langchain.agents.create_agent` (LangGraph StateGraph 기반). 구버전 경로(`tool_calling_agent/base.py`, `agents/agent.py`)는 현재 master에 없음. (Source: `langchain-source-create-agent-factory-2026-05-23`)
- ✅ 메시지 히스토리는 내부적으로 어디에서 관리되는가? → `AgentState`의 `messages` 필드 (StateGraph state의 일부). `add_messages` reducer로 각 노드 실행 후 자동 누적. 영속이 필요하면 `checkpointer=InMemorySaver()` + `thread_id`로 thread-scoped 관리. 레거시 `RunnableWithMessageHistory`는 deprecated. (Source: `langchain-source-create-agent-factory-2026-05-23`, `langchain-source-memory-api-2026-05-23`)

**해소됨 (2026-05-23):**
- ✅ `stream_events` v1/v2/v3 차이 → v1: 구버전 호환(parent_ids 빈 리스트), v2: 기본값(custom events, parent_ids), v3: `GraphRunStream` typed projection(BaseChatModel·CompiledGraph만 지원, 현재 베타). (Source: `langgraph-source-streaming-2026-05-23`)
- ✅ LangGraph Pregel stream_mode와 `stream_events v3`의 관계 → v3는 `_pregel_stream_v3()` → `StreamMux` → `Pregel.stream(stream_mode=합집합, subgraphs=True, version="v2")` 레이어. 각 Transformer의 required_stream_modes 합집합이 Pregel stream_mode가 됨. (Source: `langgraph-source-streaming-2026-05-23`)
- ✅ `astream_events` vs `astream_log` → `astream_log`는 **deprecated** (langchain-core 1.3.3, 제거 예정 2.0.0). RunLogPatch JSON Patch 구형 API. `astream_events`는 StreamEvent dict. `stream_events(v3)`는 GraphRunStream typed projection 현재 권장. (Source: `langgraph-source-streaming-2026-05-23`)
- ✅ Deep Agents `create_deep_agent` stream_events 지원 여부 → **YES.** CompiledStateGraph(Pregel 상속) 반환 → stream_events v3 네이티브 지원. compile 시 ToolCallTransformer 등 자동 등록. (Source: `langgraph-source-streaming-2026-05-23`)
- ✅ `ConversationBufferMemory`, `ConversationSummaryMemory` deprecated 여부 → 경로 404 (현재 LangChain 1.x에 파일 없음). `langchain-community` 2026-05-22 sunset. `RunnableWithMessageHistory` deprecated (langchain-core 1.3.3). 현재 권장: LangGraph checkpointer + SummarizationMiddleware. (Source: `langchain-source-memory-api-2026-05-23`)

**해소됨 (2026-05-23):**
- ✅ `MessagesPlaceholder(optional=False)`일 때 해당 변수가 없으면 KeyError가 발생하는가? → **YES.** `optional=False`(기본값)이면 `kwargs`에 `variable_name`이 없을 경우 `KeyError` 발생. `optional=True`이면 빈 리스트 `[]` 반환. `("placeholder", "{var}")` shorthand는 자동으로 `optional=True`로 생성. (Source: `langchain-source-prompts-2026-05-23`)

**잔여 질문:**
- Custom stream transformer의 정확한 계약(contract)은 무엇인가? (required_stream_modes, push() 메서드?) — Needs Source

### 메시지 시스템

**해소됨 (2026-05-23):**
- ✅ `ToolMessage`의 `tool_call_id`는 `AIMessage`의 `tool_calls`와 어떻게 연결되는가? → `ToolMessage.tool_call_id`가 `AIMessage.tool_calls[i]['id']`와 반드시 일치해야 한다. 불일치 시 모델이 tool 결과를 올바르게 연결하지 못함. (Source: `langchain-docs-messages-2026-05-23`)
- ✅ `AIMessage`의 `tool_calls` 필드 구조는 어떻게 되는가? → `dict[]`, 각 항목은 `{'name': str, 'args': dict, 'id': str}`. tool이 없으면 빈 리스트. (Source: `langchain-docs-messages-2026-05-23`)
- ✅ 채팅 모델 호출 시 메시지 리스트를 어떻게 전달하는가? → `model.invoke([HumanMessage(...), ...])` 또는 OpenAI chat completions dict 형식(`{"role": "user", "content": "..."}`)도 지원. `batch`는 리스트 of 리스트, `stream`은 이터레이터 반환. (Source: `langchain-docs-messages-2026-05-23`)

**잔여 질문:**
- `BaseMessage` 클래스 계층은 어떻게 구성되는가? (SystemMessage/HumanMessage/AIMessage/ToolMessage 외에 14개 중 나머지 10개는 무엇인가?) — Needs Source (공식 문서에서 4종만 확인됨)

### PromptTemplate / OutputParser

- `FewShotPromptTemplate`에서 예시 선택기(`ExampleSelector`)는 어떻게 동작하는가? — Needs Source
- `PipelinePromptTemplate`에서 여러 템플릿을 연결하는 내부 방식은? — Needs Source

**해소됨 (2026-05-23):**
- ✅ `PydanticOutputParser`는 LLM 출력 텍스트를 Pydantic 모델로 어떻게 변환하는가? → `parse()` 파이프라인: LLM 텍스트 → `parse_json_markdown()` → dict → `model.model_validate(dict)` (v2) / `parse_obj()` (v1) → Pydantic 인스턴스. 실패 시 `OutputParserException`. (Source: `langchain-source-output-parsers-2026-05-23`)
- ✅ `with_structured_output`과 `OutputParser`의 관계는? → `with_structured_output`은 method별로 다른 OutputParser를 내부적으로 사용: `json_mode`는 `PydanticOutputParser` / `JsonOutputParser`, `function_calling`(기본)은 tool calling → `PydanticToolsParser` / `JsonOutputKeyToolsParser`, `json_schema`는 `RunnableLambda` / `JsonOutputParser`. OutputParser는 수동 방식, `with_structured_output`은 provider 자동 전략 선택. (Source: `langchain-source-output-parsers-2026-05-23`)
- ✅ `OutputParser`의 `get_format_instructions()`는 프롬프트에 어떻게 주입되는가? → `PydanticOutputParser.get_format_instructions()`가 JSON schema 기반 형식 지시 텍스트 반환 → `PromptTemplate`의 `partial_variables={"format_instructions": parser.get_format_instructions()}` 또는 `{format_instructions}` 변수로 주입. (Source: `langchain-source-output-parsers-2026-05-23`)
- ✅ `with_structured_output`이 지원하는 4가지 타입은 내부적으로 어떻게 처리가 다른가? → Pydantic만 검증됨(Pydantic 인스턴스 반환), TypedDict/JSON schema/OpenAI function schema는 dict 반환(검증 없음). OpenAI: `method` 파라미터로 `function_calling`(기본) / `json_mode` / `json_schema` 3가지 전략 선택. `BaseChatModel.with_structured_output`은 추상 메서드(NotImplementedError), provider별 override 필수. (Source: `langchain-source-output-parsers-2026-05-23`)
- ✅ `PromptTemplate`과 `ChatPromptTemplate`의 내부 구현 차이는? → PromptTemplate: 단일 문자열 포맷 (`StringPromptTemplate` 상속), ChatPromptTemplate: 메시지 리스트 기반. 둘 다 `Runnable` 상속. (Source: `langchain-source-prompts-2026-05-23`)

### Runnable 인터페이스

- `RunnableParallel`의 thread pool thread 수 제한은? `max_concurrency` 옵션이 있는가? — Needs Verification (`base.py` 전체 미수집)
- `RunnableSequence.invoke` 내부: 각 step 간 에러 처리는 어떻게 되는가? — Needs Source (`base.py` 부분 수집만)
- `astream_events`와 `astream_log`의 차이는? — Needs Source
- `RunnableConfig`의 `configurable` 필드를 통해 실행 시간 설정을 주입하는 방법은? — Needs Source

**해소됨 (2026-05-23):**
- ✅ LCEL `|` 연산자는 내부적으로 어떤 타입을 생성하는가? → `RunnableSequence`. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `Runnable` 인터페이스의 최소 계약은? → `invoke`만 abstract. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `RunnableParallel`은 실제로 동시 실행되는가? → sync: thread pool, async: asyncio 동시 실행. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `RunnableParallel`의 결과 dict 키는 어떻게 결정되는가? → input mapping의 keys와 동일. (Source: `langchain-source-runnable-2026-05-23`)
- ✅ `RunnableLambda`와 일반 함수를 직접 사용하는 것의 차이는? → `invoke/batch/stream/ainvoke` 인터페이스 자동 부여 + LCEL `|` 체인 연결 가능. generator 함수 전달 시 streaming 지원. async def 전달 시 `afunc`으로 처리. 에러 처리 차이는 소스 부분 수집으로 미확인(Needs Verification). (Source: `langchain-source-runnable-2026-05-23`)

### @tool 데코레이터

**해소됨 (2026-05-23):**
- ✅ `@tool` 데코레이터로 만든 tool의 내부 타입은? → `StructuredTool` (infer_schema=True 기본값). infer_schema=False이고 args_schema=None이면 단순 `Tool`. (Source: `langchain-source-tools-2026-05-23`)
- ✅ LLM tool call 응답 → tool 실행 → ToolMessage 반환 흐름은? → `BaseTool.invoke(ToolCall)` → `_prep_run_args` → `run()` → `_to_args_and_kwargs` → `_run()` → `_format_output` → `ToolMessage(content, tool_call_id=id)`. (Source: `langchain-source-tools-2026-05-23`)
- ✅ tool docstring이 LLM에 전달되는 방식은? → `create_schema_from_function` → `_infer_arg_descriptions` → `_create_subset_model(fn_description=description)` → `model_json_schema()["description"]`. (Source: `langchain-source-tools-2026-05-23`)
- ✅ 비동기 tool 정의 방법은? → `async def`로 정의하면 `coroutine` 파라미터로 자동 처리. `StructuredTool._arun`에서 `await self.coroutine(...)` 실행. (Source: `langchain-source-tools-2026-05-23`)
- ✅ tool 실행 중 예외 처리는? → `ToolException`은 `handle_tool_error` 설정에 따라 에러 메시지 반환 or re-raise. `ValidationError`는 `handle_validation_error`로 처리. 기타 예외는 항상 re-raise. (Source: `langchain-source-tools-2026-05-23`)

**해소됨 (2026-05-23):**
- ✅ `@tool`로 만든 tool의 `args_schema.model_json_schema()`가 LLM API 호출 시 어떤 payload로 변환되는가? → `BaseTool.tool_call_schema` → `bind_tools([tool])` (provider 구현체) → `convert_to_openai_tool` → `convert_to_openai_function` → `_format_tool_to_openai_function` → `{"type": "function", "function": {...}}` OpenAI API 형식. `BaseChatModel.bind_tools`는 추상(NotImplementedError)이므로 provider별 구현 필요. (Source: `langchain-source-bind-tools-function-calling-2026-05-23`)

### RAG / 임베딩 / 벡터 스토어 / 리트리버

**해소됨 (2026-05-23):**
- ✅ `RecursiveCharacterTextSplitter`가 권장 text splitter: 단락 → 문장 → 단어 → 문자 순서로 분할. `chunk_overlap`으로 경계 문맥 보존. (Source: `langchain-docs-rag-2026-05-23`)
- ✅ `RecursiveCharacterTextSplitter` 내부 알고리즘: separators 리스트를 순서대로 시도, 첫 매칭 구분자로 분할, 초과 청크 재귀 분할, `_merge_splits()`로 병합. `keep_separator=True` 기본값 (CharacterTextSplitter의 False와 다름). (Source: `langchain-source-text-splitters-2026-05-23`)
- ✅ `CharacterTextSplitter` vs `RecursiveCharacterTextSplitter` 차이: 전자는 단일 구분자(기본 `\n\n`) + keep_separator=False, 후자는 구분자 리스트 + keep_separator=True + 재귀 분할. (Source: `langchain-source-text-splitters-2026-05-23`)
- ✅ `from_language()` classmethod: 30+ 언어 지원, is_separator_regex=True로 자동 설정. Python: `["\nclass ", "\ndef ", "\n\tdef ", "\n\n", "\n", " ", ""]`. (Source: `langchain-source-text-splitters-2026-05-23`)
- ✅ RAG 두 가지 패턴: RAG agent (동적, LLM이 검색 시점 결정) vs RAG chain (결정적 파이프라인). (Source: `langchain-docs-rag-2026-05-23`)
- ✅ 지원 벡터 스토어: `InMemoryVectorStore`(개발), Chroma, FAISS, Pinecone, Qdrant, pgvector, Weaviate, Elasticsearch. (Source: `langchain-docs-rag-2026-05-23`)
- ✅ 추가 리트리버 타입: `MultiQueryRetriever`, `ContextualCompressionRetriever`, `BM25Retriever`, `EnsembleRetriever`. (Source: `langchain-docs-rag-2026-05-23`)
- ✅ RAG 보안 위협: Indirect Prompt Injection — 검색 문서에 악성 지시 삽입. 완화: 콘텐츠 정제, 명시적 구분자, 가드레일. (Source: `langchain-docs-rag-2026-05-23`)
- ✅ `@dynamic_prompt` 정체: `langchain.agents.middleware.types`의 AgentMiddleware 생성 데코레이터. 서명 `(request: ModelRequest) -> str | SystemMessage`. wrap_model_call 인터셉트로 시스템 프롬프트 동적 교체. (Source: `langchain-source-dynamic-prompt-2026-05-23`)

**해소됨 (2026-05-23):**
- ✅ `LangChain Document 객체 구조` → `page_content: str`, `metadata: dict`, `id: str | None`, `type: Literal["Document"]`. (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)
- ✅ `Embeddings 기반 클래스 인터페이스` → `embed_documents(list[str]) -> list[list[float]]`, `embed_query(str) -> list[float]` abstract. async 버전은 기본 sync wrapper. (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)
- ✅ `as_retriever()` search_type 옵션 → `similarity`(k=4), `mmr`(k/fetch_k=20/lambda_mult=0.5), `similarity_score_threshold`(score_threshold). (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)
- ✅ `MMR 작동 방식` → fetch_k 후보 → `maximal_marginal_relevance(embedding, candidates, k, lambda_mult)`. lambda_mult: 1.0=관련성, 0.0=다양성, 0.5=기본. (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)
- ✅ `BaseRetriever.get_relevant_documents 계약` → deprecated. 현재 `invoke()` 사용. 구현 시 `_get_relevant_documents()` override. (Source: `langchain-source-vectorstore-embeddings-2026-05-23`)

**해소됨 (2026-05-23):**
- ✅ RAG 문서의 `@dynamic_prompt(user_query: str) -> list` 패턴 — 실제 API와 불일치 → **문서 오류 확정.** 실제 `@dynamic_prompt` 서명: `(request: ModelRequest) -> str | SystemMessage`. RAG 문서 예제는 `@dynamic_prompt`가 아닌 일반 LCEL 함수 패턴을 잘못 표기한 것으로 추정. 올바른 사용법: `request.state["messages"]`에서 쿼리 추출 후 `str` 반환. (Source: `langchain-source-dynamic-prompt-2026-05-23`)

**잔여 질문:**
- ⚠️ FAISS `similarity_search`의 내부 알고리즘 (L2 거리 기본값인가?) — Needs Source (GitHub 파일 접근 실패)
- ⚠️ FAISS 거리 점수와 cosine similarity 관계, 변환 공식 — Needs Source
- `init_embeddings("openai:text-embedding-3-small")` 형식은 새로운 API인가? 구버전 `OpenAIEmbeddings()`와의 차이는? — Source: `langchain-docs-rag-2026-05-23`
- `response_format="content_and_artifact"` 옵션의 정확한 의미는? — Source: `langchain-docs-rag-2026-05-23`
- `_merge_splits()`의 `chunk_overlap` 구현 방식은? 슬라이딩 윈도우인가? — Source: `langchain-source-text-splitters-2026-05-23`
- `wrap_model_call` 데코레이터의 전체 서명과 `before_model` hook과의 차이는? — Source: `langchain-source-dynamic-prompt-2026-05-23`

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

### Human-in-the-Loop / Interrupt

**해소됨 (2026-05-23):**
- ✅ `interrupt_before` / `interrupt_after`는 그래프 수준에서 어떻게 동작하는가? → `Pregel.interrupt_before_nodes` / `interrupt_before_nodes` 속성으로 저장. compile() 시 설정, `"*"` 전달 시 전체 노드. stream 실행 시 runtime override 가능 (`interrupt_before = interrupt_before or self.interrupt_before_nodes`). checkpointer + thread_id 필수. (Source: `langgraph-source-pregel-interrupts-2026-05-23`)
- ✅ `interrupt()` 함수 동작: `GraphInterrupt` 예외로 실행 중단 → state checkpoint 저장 → `Command(resume=...)` 재호출 시 `interrupt()`가 resume 값을 반환하며 노드 계속 실행. scratchpad.resume 인덱스 기반 멱등 설계. (Source: `langgraph-source-pregel-interrupts-2026-05-23`)
- ✅ `interrupt_before/after` vs `interrupt()` 차이: 전자는 compile 시 고정, 조건 불가. 후자는 노드 내 동적, 조건부 가능. 2024-12부터 `interrupt()` 방식이 권장. (Source: `langgraph-source-pregel-interrupts-2026-05-23`)

### Memory / Store

### Checkpointer 종류

**해소됨 (2026-05-23):**
- ✅ `MemorySaver`와 `InMemorySaver`는 동일한 클래스인가, 다른 클래스인가? → **동일. `MemorySaver = InMemorySaver` (하위 호환 alias).** (Source: `langgraph-source-checkpoint-savers-2026-05-23`)
- ✅ `SQLiteSaver` 설정 방법 → `SqliteSaver.from_conn_string(":memory:" | "file.sqlite")`. `setup()` 자동 호출. 단일 스레드 권장. (Source: `langgraph-source-checkpoint-savers-2026-05-23`)
- ✅ `PostgresSaver` 설정 방법 → `PostgresSaver.from_conn_string(DB_URI)` + **`saver.setup()` 명시 호출 필수**. `pipeline=True`로 성능 향상 가능 (단일 Connection만). `AsyncPostgresSaver`는 `asetup()` 사용. (Source: `langgraph-source-checkpoint-savers-2026-05-23`)
- ✅ `InMemorySaver`의 `storage/writes/blobs` 구조 → `storage`: thread→ns→checkpoint_id→(checkpoint, metadata, parent_id). `writes`: (thread, ns, checkpoint_id)→(task_id, write_idx)→(task_id, channel, value, path). `blobs`: (thread, ns, channel, version)→blob. (Source: `langgraph-source-checkpoint-savers-2026-05-23`)
- ✅ `MemorySaver`와 persistent saver의 운영상 차이 → InMemorySaver/MemorySaver는 테스트/디버그 전용. SqliteSaver는 소규모/단일 스레드. PostgresSaver/AsyncPostgresSaver가 프로덕션 권장. (Source: `langgraph-source-checkpoint-savers-2026-05-23`)
- ✅ checkpointer가 있을 때 같은 `thread_id`로 재실행하면 이전 상태부터 이어서 실행되는가? → **YES.** `thread_id` 재사용 시 LangGraph가 해당 thread의 최신 checkpoint를 불러와 이전 state 위에서 계속 실행한다. `_first()`가 기존 `channel_versions`의 존재로 resume 여부를 판단하며, 새 input이 있으면 기존 state에 적용 후 graph를 진행한다. 이것이 multi-turn conversation 연속성의 구현 방식이다. (Source: `langgraph-docs-persistence-2026-05-20`, `langgraph-source-checkpoint-runtime-2026-05-20`)
- ✅ `config = {"configurable": {"thread_id": "..."}}` 패턴의 내부 전달 경로 → `graph.invoke(input, config)` → `Pregel._defaults(config)`에서 effective checkpointer 결정 → `SyncPregelLoop(checkpointer, config)` 생성 → `_first()`에서 `checkpointer.get_tuple(config)` 호출 → saver가 `config["configurable"]["thread_id"]`를 primary key로 thread checkpoint 조회. `InMemorySaver.get_tuple()`은 명시된 checkpoint_id가 있으면 그것을, 없으면 해당 thread/ns의 최신 checkpoint를 반환한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)

**해소됨 (2026-05-23):**
- ✅ `create_checkpoint` 구현 → 이전 checkpoint + live channels에서 새 Checkpoint 빌드. DeltaChannel이면 `channels_to_snapshot`에 포함 여부로 `_DeltaSnapshot(전체값)` vs `ch.checkpoint()(일반값)` 분기. exit 모드에서 쓰기 없는 채널은 channel_versions 수동 bump. (Source: `langgraph-source-checkpoint-internals-2026-05-23`)
- ✅ `channels_from_checkpoint` 구현 → 일반 채널: `spec.from_checkpoint(values[k])` 직접 복원. DeltaChannel이고 `channel_values`에 없으면: `_needs_replay()=True` → `saver.get_delta_channel_history()` 배치 호출 → seed에서 `from_checkpoint` → `replay_writes()` 순서로 재구성. (Source: `langgraph-source-checkpoint-internals-2026-05-23`)
- ✅ `DeltaChannel` snapshot 조건 → `updates >= snapshot_frequency` 또는 `supersteps >= DELTA_MAX_SUPERSTEPS_SINCE_SNAPSHOT` 중 하나 충족 시 스냅샷. `delta_channels_to_snapshot()` 순수 함수로 판단. (Source: `langgraph-source-checkpoint-internals-2026-05-23`)
- ✅ `copy_checkpoint` 구현 → 2-depth 복사: `channel_values.copy()`, `channel_versions.copy()`, `versions_seen={k: v.copy() ...}`. (Source: `langgraph-source-checkpoint-internals-2026-05-23`)

**잔여 질문:**
- `thread_id` 없이 `invoke`를 호출하면 어떤 에러가 발생하는가? — Needs Verification (문서는 "저장/resume 불가"라고만 설명, 에러 타입 미명시)
- `StateGraph.compile()` 이후 `Pregel.validate()`는 정확히 어떤 구조 검사를 수행하는가? — Needs Source (소스 summary에서 호출 사실만 확인, 내용 미수집)
- pending writes recovery를 정의하는 canonical test는 어디에 있는가? — Needs Source
- `DeltaChannel` reconstruction/pruning/copying safety를 검증하는 test는 어디에 있는가? — Needs Source
- `exit` durability에서 `_put_exit_delta_writes()`를 검증하는 test는 어디에 있는가? — `_checkpoint.py`에 없음, `_loop.py` 탐색 필요
- `saver.get_delta_channel_history()` 메서드는 `BaseCheckpointSaver`에 언제 추가됐는가? — Needs Source
- checkpoint schema migration 또는 state schema 변경 대응은 공식적으로 어떻게 권장되는가? — Needs Source
- `astream_events`와 함께 스트리밍은 어떻게 동작하는가?
- LangGraph package version과 reference docs version의 관계는? GitHub page는 `langgraph==1.2.0`, `StateGraph.compile` reference는 v1.1.10으로 보였다. — Source: `langgraph-reference-stategraph-compile-2026-05-20`

### Memory Store

**해소됨 (2026-05-23):**
- ✅ `BaseStore` 인터페이스의 핵심 계약: `batch`/`abatch` 추상 메서드 2개. 나머지(`get`, `put`, `search`, `delete`, `list_namespaces`)는 모두 이것의 래퍼. (Source: `langgraph-store-base-2026-05-23`)
- ✅ `store.get(namespace, key)` 반환: `Item | None`. `store.put(namespace, key, value)` 반환: `None`. `value=None` → 삭제. (Source: `langgraph-store-base-2026-05-23`)
- ✅ namespace 개념: `tuple[str, ...]` 계층 경로 — `("user", "123", "memories")` 형식. (Source: `langgraph-store-base-2026-05-23`)
- ✅ `Item` 필드: `value: dict`, `key: str`, `namespace: tuple[str, ...]`, `created_at`, `updated_at`. (Source: `langgraph-store-base-2026-05-23`)
- ✅ `search`의 `query` 파라미터: semantic search용 (구현체가 vector store 지원 시에만 의미 있음). (Source: `langgraph-store-base-2026-05-23`)

**해소됨 (2026-05-23):**
- ✅ `InMemoryStore`의 vector search 지원 여부는? → 기본값은 keyword filter만 지원. `IndexConfig(dims=..., embed=...)` 설정 시 semantic search 활성화 가능. `SearchOp.query` 파라미터가 구현체의 vector store 지원 시에만 의미 있음. (Source: `langgraph-store-base-2026-05-23`)

**잔여 질문:**
- 프로덕션용 Store 구현체(Redis, PostgreSQL)는 어떤 패키지에 있는가? — Needs Source
- `create_deep_agent`에서 Store는 어떤 middleware가 어떻게 활용하는가? (`MemoryMiddleware`와의 관계?) — Needs Source

**해소됨 (2026-05-20):**
- ✅ 체크포인팅은 무엇을 저장하고 무엇을 버릴지 어떻게 결정하는가? → LangGraph는 super-step boundary마다 `StateSnapshot` checkpoint를 저장하고, super-step 내부의 task-level writes도 pending writes로 저장한다. State에 포함되지 않은 외부 side effect나 thread 간 memory는 자동 저장 대상이 아니다. (Source: `langgraph-docs-persistence-2026-05-20`, `langgraph-reference-checkpoint-2026-05-20`)
- ✅ `StateGraph.compile(checkpointer=...)`에서 checkpointer는 어디에 attach되는가? → `state.py`에서 `CompiledStateGraph(..., checkpointer=checkpointer, ...)`에 전달되고, `CompiledStateGraph`는 `Pregel`을 상속한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)
- ✅ `InMemorySaver`의 내부 자료구조는? → `storage`, `writes`, `blobs`로 checkpoint record, pending writes, channel-version blobs를 분리한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)
- ✅ `exit` / `async` / `sync` durability mode는 runtime source에서 어디에 구현되는가? → `_defaults()` 기본값은 `"async"`, `"sync"`는 tick 뒤 checkpoint future를 기다리고, `"exit"`는 `put_writes()` immediate persistence를 건너뛰고 loop exit에서 checkpoint/writes를 저장한다. (Source: `langgraph-source-checkpoint-runtime-2026-05-20`)

## Deep Agents

- ACP (Agent Client Protocol) integration은 어떤 프로토콜 스펙을 따르는가? — Source: `deepagents-docs-overview-2026-05-18`

**해소됨 (2026-05-23):**
- ✅ subagent state isolation의 구체적 메커니즘은? → `_EXCLUDED_STATE_KEYS = {messages, todos, structured_response, skills_metadata, skills_load_errors, memory_contents}` 로 입력·출력 양방향 필터링. 호출 시 parent 메시지 히스토리 제거 + 단일 HumanMessage. 반환 시 마지막 AIMessage text 또는 structured_response만 ToolMessage로 전달. `SubagentTransformer`는 별도 파일 — 아직 미확인. (Source: `deepagents-source-subagents-2026-05-23`)
- Deep Agents Code (터미널 에이전트)는 SDK를 어떻게 확장하는가? — Source: `deepagents-docs-overview-2026-05-18`
- `langchain.agents.create_agent`의 내부 구현은? LangGraph `StateGraph`를 어떻게 조립하나? — Source: `deepagents-source-graph-2026-05-19`
- `HarnessProfile`은 어떤 모델에 어떤 profile을 매핑하나? (`harness_profiles.py` 수집 필요) — Source: `deepagents-source-graph-2026-05-19`
- ✅ `PatchToolCallsMiddleware`의 역할 → `before_agent` hook에서 dangling tool call(AIMessage에 tool_call은 있지만 대응하는 ToolMessage가 없는 상태) 감지 → 더미 ToolMessage 삽입. invalid_tool_call(인자 파싱 실패: "malformed or truncated")과 cancelled(중단된 정상 호출: "was cancelled") 두 케이스 처리. `Overwrite`로 state.messages 전체 교체. (Source: `deepagents-source-patch-tool-calls-2026-05-23`)
- `DeltaChannel`의 `snapshot_frequency=50`은 정확히 무엇을 의미하나? 50 super-step인가 50 message인가? full snapshot과 delta 사이 재구성 비용은? — Source: `deepagents-source-graph-2026-05-19` (소스코드 직접 확인 필요: `_messages_reducer.py` + LangGraph `DeltaChannel` 구현)
- Skills frontmatter 형식은 무엇이며 agent는 어떻게 관련성을 판단하는가? — Source: `deepagents-docs-context-engineering-2026-05-18`
- `@dynamic_prompt` 데코레이터의 정확한 시그니처와 사용 패턴은? — Source: `deepagents-docs-context-engineering-2026-05-18`

- `register_harness_profile` entry points 패키징 방법은? — Source: `deepagents-docs-harness-2026-05-19`
- 빌트인 profile(`_builtin_profiles`)에는 어떤 모델에 어떤 profile이 등록되어 있는가? — Source: `deepagents-source-harness-profiles-2026-05-19`
- `serialized_name: ClassVar[str]`을 가지는 공식 middleware는 어떤 것들이 있는가? (`SummarizationMiddleware` 등) — Source: `deepagents-source-harness-profiles-2026-05-19`
- `excluded_middleware`에 매칭되지 않는 entry가 있을 때 rejection은 생성 시점인가, 조립 시점인가? — Source: `deepagents-source-harness-profiles-2026-05-19`
- Sandbox backend 없을 때 `execute` tool은 error 반환인가, tool 목록에서 제외되는가? — Source: `deepagents-docs-harness-2026-05-19`
- Interpreter (`eval` tool, QuickJS)는 어떤 패키지에 포함되어 있는가? — Source: `deepagents-docs-harness-2026-05-19`
**해소됨 (2026-05-23):**
- ✅ `libs/evals 디렉토리 실제 구조` → `deepagents_evals/` + `deepagents_harbor/` + `tests/evals/`. pytest + TrajectoryScorer(.success()=hard, .expect()=soft). 111개 eval, 7 카테고리. (Source: `deepagents-source-evals-structure-2026-05-23`)
- ✅ 외부 벤치마크 적용 방법 → Harbor 통해 Terminal Bench 2.0 실행. `DeepAgentsWrapper`로 래핑, LangSmith로 결과 추적. reward score (0.0~1.0) 피드백 push. (Source: `deepagents-source-evals-structure-2026-05-23`)

**잔여 질문:**
- LLM-as-a-judge에서 구체적으로 어떤 judge 모델을 사용하는가? → `MODEL_GROUPS.md` 확인 필요. (Source: `deepagents-blog-evals-2026-05-23`, `deepagents-source-evals-structure-2026-05-23`)
- BFCL 벤치마크도 Harbor를 통해 동일하게 적용되는가? — Needs Source
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
