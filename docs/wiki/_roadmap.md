# 로드맵

## 이 위키의 목적

이 위키는 내가 직접 LangChain, LangGraph, Deep Agents를 학습해서 업스트림에 PR을 제출할 수 있는 기술 수준에 도달하기 위한 학습 지원 자료다.

AI는 참고 자료(wiki 페이지, source summary, 재현 예제)를 준비하는 역할을 하지만, 실제 학습과 기여는 내가 직접 수행한다.
체크 표시는 내가 직접 읽고 이해하거나 코드를 작성한 경우에만 한다.

---

## 현재 목표

아래 능력을 순서대로 키운다. 각 단계는 이전 단계가 충분히 쌓인 뒤 진행한다.

1. 공개 API를 직접 사용해보고 동작을 확인한다
2. 소스 코드를 읽고 공개 API의 내부 구현을 추적한다
3. 테스트를 읽고 어떤 동작이 보장되는지 설명할 수 있다
4. 이슈를 읽고 재현 예제를 스스로 작성한다
5. 소스 코드를 직접 추적해 근본 원인을 분석한다
6. 기존 테스트 패턴을 참고해 새 테스트를 직접 작성한다
7. 패치를 작성하고 검토 가능한 PR을 직접 제출한다

---

## 1단계 — 공개 API 익히기

세 프레임워크의 핵심 API를 직접 사용해보고 어떻게 동작하는지 확인하는 단계다.

- [ ] LangChain: `create_react_agent`, `AgentExecutor` 직접 실행해보기
- [x] LangChain: `create_agent` + `PIIMiddleware` / `SummarizationMiddleware` / `LLMToolSelectorMiddleware` 직접 실행해보기 ✅ (2026-05-26, `examples/langchain_core/04_pii_middleware.py`, `05_summarization_middleware.py`, `06_tool_selector_middleware.py`)
- [x] LangGraph: `StateGraph` 정의 → `compile` → `invoke` 직접 실행해보기 ✅ (2026-05-25, `examples/langgraph_core/01_stategraph_basics.py`)
- [x] LangGraph: `MemorySaver`로 체크포인팅 직접 동작 확인 ✅ (2026-05-25, `examples/langgraph_core/02_checkpointing_history.py` — 5단계 checkpoint 히스토리 확인)
- [x] LangGraph: `interrupt()`/`Command(resume=)` 직접 동작 확인 ✅ (2026-05-25, `examples/langgraph_core/03_interrupt_resume.py` — pause/resume 전체 흐름)
- [x] LangGraph: 서브그래프, Send map-reduce, input_schema/output_schema 직접 확인 ✅ (2026-05-25, `examples/langgraph_core/05_subgraph_patterns.py`)
- [x] Deep Agents: `create_deep_agent` 구조 검사 직접 실행해보기 ✅ (2026-05-28, `examples/deepagents_core/01_basic_deep_agent.py`, `02_middleware_stack.py`, `examples/research_agent_comparison/04_deep_agents_stub.py` — API key 없음으로 실제 LLM invocation은 미실행)
- [x] Deep Agents: fake model로 custom tool + built-in `write_file` 호출 흐름 직접 확인 ✅ (2026-05-28, `examples/deepagents_core/03_tool_call_and_filesystem.py`)
- [x] LangChain: fake model로 `create_agent` tool loop + middleware hook 순서 직접 확인 ✅ (2026-05-28, `examples/langchain_core/08_create_agent_fake_tool_loop.py`)
- [ ] LangGraph에서 도구 등록 및 호출이 어떻게 동작하는지 직접 확인

> 참고 자료 (AI가 준비):
> - `docs/wiki/frameworks/`, `docs/wiki/concepts/`
> - `examples/` 디렉터리

---

## 2단계 — 소스 코드 읽기

공개 API 뒤에서 어떤 코드가 실행되는지 직접 읽는 단계다.

- [x] LangChain `create_react_agent` 호출 경로를 소스에서 직접 따라가기 ✅ (2026-05-28, `chat_agent_executor.py` 1015 lines)
- [x] LangChain `create_agent` + middleware 시스템 소스 읽기 ✅ (2026-05-28, `factory.py` + `middleware/types.py`)
- [x] LangChain 빌트인 미들웨어 소스 읽기: `SummarizationMiddleware`, `PIIMiddleware`, `LLMToolSelectorMiddleware`, `ModelRetryMiddleware`, `ToolRetryMiddleware`, `ModelFallbackMiddleware` ✅ (2026-05-26)
- [x] LangGraph `StateGraph.compile()` 내부 구조를 소스에서 읽기 ✅ (2026-05-25, `graph/state.py:1164`, v1.2.1 직접 읽기)
- [x] LangGraph `Pregel` 런타임이 어떻게 step을 실행하는지 소스에서 읽기 ✅ (2026-05-25, `pregel/_loop.py:583` tick/after_tick, `pregel/main.py:2868` SyncPregelLoop)
- [x] Checkpointing: `BaseCheckpointSaver.put()` 호출 경로를 직접 확인 ✅ (2026-05-25, `_put_checkpoint → _checkpointer_put_after_previous → checkpointer.put()`, `InMemorySaver.put():427`)
- [x] 읽은 파일 경로와 핵심 함수를 `docs/wiki/flows/` 또는 `docs/wiki/codebase/`에 직접 기록 ✅ (2026-05-25, `flows/LangGraph StateGraph compile invoke flow.md` 갱신)

> 참고 자료 (AI가 준비):
> - `docs/wiki/flows/`, `docs/wiki/codebase/`
> - `docs/source_summaries/`

---

## 3단계 — 테스트 읽기

소스 코드와 함께 테스트를 읽고 "어떤 동작이 보장되어야 하는가"를 이해하는 단계다.

- [x] `test_pregel.py::test_pending_writes_resume` 읽고 무엇을 검증하는지 직접 설명해보기 ✅ (2026-05-25)
- [x] LangGraph 체크포인팅 관련 테스트 3개 이상 읽기 ✅ (2026-05-25, test_checkpoint_metadata, test_checkpoint_recovery, test_pending_writes_resume)
- [x] LangGraph interrupt 관련 테스트 6개 읽기 ✅ (2026-05-25)
- [x] LangChain tool calling 관련 테스트 3개 이상 읽기 ✅ (2026-05-27, test_unnamed_decorator, test_tool_injected_tool_call_id, test_exception_handling_*, test_tool_default_factory_not_required)
- [ ] 테스트가 없는 동작이나 엣지 케이스를 스스로 발견하기 (예: InjectedStore + ToolNode 조합)

---

## 7단계 — PR 작성 및 제출

소스 근거와 회귀 테스트를 갖춘 실제 기여 PR을 작성하는 단계다.

- [x] PR 준비 문서 작성: issue #5225 수정 방향, 변경 사항, 테스트 계획 ✅ (2026-05-25)
  - 위치: `docs/wiki/prs/LangGraph pydantic default factory reducer bug.md`
  - 제목 초안: `fix(graph): coerce dict input through Pydantic schema at START to apply default_factory`
- [ ] `langchain-ai/langgraph` CONTRIBUTING.md 읽기 (이슈 사전 승인 정책 확인)
- [ ] issue #5225에 댓글로 수정 방향 공유 (PR 전 maintainer 확인)
- [ ] 실제 fork → feature 브랜치 생성 → 패치 적용 → PR 제출

---

## 이후 탐색 영역

아래 항목은 7단계 이후 관심 방향이다. 순서는 고정이 아니다.

- [x] LangGraph 스트리밍 7가지 모드 직접 실험 ✅ (2026-05-25, `examples/langgraph_core/06_streaming_modes.py`)
  - values / updates / custom / checkpoints / tasks / messages / 복수 모드 동시 소비
- [x] LangGraph ToolNode + InjectedState / InjectedStore 직접 실험 ✅ (2026-05-25, `examples/langgraph_core/07_toolnode_injection.py`)
  - 기본 ToolNode → InjectedState → InjectedStore → handle_tool_error → 그래프 통합 루프
- [x] Deep Agents `create_deep_agent` fake model invocation + filesystem tool call 확인 ✅ (2026-05-28, default `StateBackend` files state 및 non-sandbox `execute` filtering 확인)
- [ ] Deep Agents 실제 provider LLM invocation + sandbox backend `execute` tool call 확인
- [ ] `stream_events(version="v3")` typed projection 직접 실험 (real LLM 필요)
- [ ] LangGraph Streaming: custom transformer 작성 (ToolCallTransformer 구현 패턴 참고)
- [ ] Deep Agents eval: LLM-as-a-judge 모델 결정 경로 (`MODEL_GROUPS.md` 직접 읽기)

> 참고 자료:
> - `docs/wiki/tests/test_pregel_interrupt_map.md`
> - `docs/wiki/tests/test_pregel_checkpoint_map.md`

---

## 4단계 — 이슈 재현

실제 이슈를 읽고 최소 재현 예제를 직접 작성하는 단계다.

- [x] LangGraph `help wanted` 이슈 중 하나를 직접 읽기 ✅ (2026-05-25, #5225)
- [x] 이슈에서 설명하는 동작을 재현하는 최소 예제를 직접 작성하기ã ✅ (2026-05-25)
- [x] 기대 동작과 실제 동작의 차이를 코드로 확인하기 ✅ (2026-05-25)
- [x] 재현 결과를 `reproductions/`에 직접 기록하기 ✅ (2026-05-25)

> 참고 자료:
> - `reproductions/langgraph_pydantic_default_factory/reproduce.py`
> - `docs/wiki/issues/LangGraph issue 5225 pydantic default factory.md`

---

## 5단계 — 근본 원인 분석

이슈의 원인을 소스 코드에서 직접 찾고, 분석 결과를 위키에 정리하는 단계다.

- [x] 재현된 이슈의 원인이 되는 코드를 소스에서 직접 찾기 ✅ (2026-05-25, `state.py attach_node._get_updates`, `binop.py BinaryOperatorAggregate.__init__`, `_fields.py get_field_default`)
- [x] 기존 테스트 패턴을 참고해 동작이 어떻게 검증되어야 하는지 설명하기 ✅ (2026-05-25, Pydantic+reducer 조합 회귀 테스트 패턴 — 현재 테스트 없음 확인)
- [x] 수정 방향을 소스 근거와 함께 위키에 정리하기 ✅ (2026-05-25, `_get_updates` START+Pydantic coercion, `.venv` 로컬 fix 8케이스 검증)
- [x] 분석 결과를 `docs/wiki/issues/`에 기록하기 ✅ (2026-05-25, `issues/LangGraph issue 5225 pydantic default factory.md`)

> 학습 자료:
> - `reproductions/langgraph_pydantic_default_factory/reproduce.py`
> - `docs/wiki/issues/LangGraph issue 5225 pydantic default factory.md`

---

## 다음으로 읽을 자료

- LangGraph `test_pregel.py` — 이미 `reproductions/`에서 테스트 이름은 확인됨, 직접 전체 읽기
- ~~LangGraph `_loop.py`~~ ✅ 완료 (2026-05-25, tick/after_tick/put_writes/_put_checkpoint 소스 읽기)
- ~~LangGraph `_checkpoint.py`~~ ✅ 완료 (2026-05-25, create_checkpoint/delta_channels_to_snapshot)
- ~~Deep Agents `create_deep_agent` 구조 검사~~ ✅ 완료 (2026-05-28, local `deepagents 0.6.3`)
- ~~Deep Agents fake model invocation + filesystem state 확인~~ ✅ 완료 (2026-05-28)
- Deep Agents 실제 provider LLM invocation + sandbox backend `execute` tool payload 확인

## 6단계 — 테스트 직접 작성

- [x] issue #5225 회귀 테스트 직접 작성: Pydantic BaseModel + `default_factory` + reducer 조합 테스트 ✅ (2026-05-25)
  - 위치: `reproductions/langgraph_pydantic_default_factory/test_regression.py`
  - 결과: 12개 테스트 (8 passed, 4 xfailed) — xfail 4개가 버그를 문서화, fix 후 xfail → pass로 전환 예정
  - 검증 케이스:
    - `invoke({})` → xfail (버그: default_factory 무시됨)
    - `invoke(State())` → pass (워크어라운드)
    - `invoke({'variable': [...]})` → pass (명시적 값)
    - checkpointer 상태 보존 및 중복 호출 누산 → pass
    - TypedDict 경로 영향 없음 → pass
    - 멀티 필드 케이스 → xfail (버그 동일하게 재현)
- [ ] 테스트가 없는 동작이나 엣지 케이스를 스스로 발견하기
