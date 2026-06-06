---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: verified
confidence: high
last_reviewed: 2026-06-06
sources:
  - deepagents-blog-evals-2026-05-23
  - deepagents-source-evals-structure-2026-05-23
  - deepagents-evals-model-groups-harbor-bfcl-2026-05-23
---

# Evaluation

## 요약

Evaluation은 agent의 품질, 정확성, 동작을 측정하는 과정이다. **"More evals ≠ better agents"** — 프로덕션에서 중요한 동작을 반영하는 targeted eval을 만드는 것이 핵심이다.

Source: `deepagents-blog-evals-2026-05-23` ⚠️ blog 출처 (medium confidence)

## Why It Matters

- Eval 없이는 agent 개선이 실제인지 착시인지 판단할 수 없다.
- 모든 eval은 agent 동작을 이동시키는 압력 벡터다 — 추가할수록 시스템 프롬프트·tool 설명 조정에 영향을 준다.
- 좋은 PR에는 테스트가 포함되거나 갱신되므로, 업스트림 기여를 위해서도 평가 프레임워크는 중요하다.

## 핵심 개념

- **Targeted eval** — 프로덕션에서 중요한 동작만 측정하는 eval
- **Ideal trajectory** — 불필요한 액션 없이 올바른 결과를 내는 기준 경로
- **LLM-as-judge** — agent 출력의 의미론적 정확성을 LLM으로 채점
- **Correctness + Efficiency** — 정확성을 먼저, 그다음 효율성 측정
- **Eval taxonomy** — 출처가 아닌 "무엇을 테스트하는가"로 분류
- **SDK unit test vs model capability eval** — 반드시 분리해야 한다

## Deep Agents Eval 접근법 (Verified)

*Source: `deepagents-blog-evals-2026-05-23` ⚠️ blog*

### Eval 데이터 소싱 3가지

1. **Dogfooding** — 매일 직접 사용, 모든 오류를 eval 작성 기회로
2. **External benchmarks** — BFCL (function calling), Terminal Bench 2.0 (coding in sandbox) — 조정해서 사용
3. **Artisanal (hand-written)** — 중요 동작을 직접 단위 테스트로 작성

> **핵심 원칙:** SDK unit/integration test (system prompt passthrough, interrupt config, subagent routing)는 model capability eval과 분리한다. SDK 테스트는 어떤 모델도 통과하므로 scoring에 포함하면 신호가 없다.

### Eval 카테고리 Taxonomy (7가지)

| Category | What It Tests |
|----------|--------------|
| `file_operations` | File tools (read, write, edit, ls, grep, glob), parallel invocation, pagination |
| `retrieval` | Finding information across files, search strategies, multi-hop document synthesis |
| `tool_use` | Selecting the right tool, chaining multi-step calls, tracking state across turns |
| `memory` | Recalling seeded context, extracting implicit preferences, persisting durable info |
| `conversation` | Asking clarifying questions for vague requests, sustaining multi-turn dialogue |
| `summarization` | Handling context overflow, triggering summarization, recovering info after compaction |
| `unit_tests` | SDK plumbing — system prompt passthrough, interrupt config, subagent routing |

분류 기준: **"어디서 왔는가"가 아니라 "무엇을 테스트하는가"**

### Correctness 측정 방법

| 상황 | 방법 |
|------|------|
| 내부 custom eval | custom assertions ("did the agent parallelize tool calls?") |
| 외부 벤치마크 (BFCL) | adapted benchmark scoring. 현재 Deep Agents BFCL v3 경로는 final API state comparison |
| 의미론적 정확성 | LLM-as-a-judge |

### 5가지 메트릭

| Metric | Definition | 방향 |
|--------|-----------|------|
| Correctness | 태스크를 올바르게 완료했는가 | 높을수록 |
| Step ratio | 관찰된 agent steps / ideal steps | 낮을수록 |
| Tool call ratio | 관찰된 tool calls / ideal tool calls | 낮을수록 |
| Latency ratio | 관찰된 latency / ideal latency | 낮을수록 |
| Solve rate | expected steps / observed latency (오답이면 0) | 높을수록 |

**Solve rate**: latency ratio와 달리, 실패한 run을 0으로 처리 — 정확성과 속도를 단일 지표로 결합.

### Ideal Trajectory

**정의**: 불필요한 액션 없이 올바른 결과를 내는 기준 경로.

구성 요건:
- 최소한의 tool calls
- 독립적인 tool calls는 병렬화
- 불필요한 중간 턴 없음

예시: "현재 시간과 날씨를 알려줘"
- **Ideal**: 4 steps, 4 tool calls, ~8초
- **Inefficient (정확하지만 비효율)**: 6 steps, 5 tool calls, ~14초
  - step ratio 1.5, tool_call_ratio 1.25, latency_ratio 1.75, solve_rate 0.29

### 모델 선택 순서

1. **Correctness 먼저** — 원하는 태스크를 충분히 정확하게 수행하는 모델 필터링
2. **Efficiency 다음** — 통과 모델 중 correctness/latency/cost 트레이드오프 최적 선택

### 실행 환경

- **pytest + GitHub Actions** — CI에서 재현 가능한 환경
- **LangSmith** — 모든 eval run trace → 팀 전체 분석·수정 가능
- **태그 기반 subset 실행**: `--eval-category file_operations --eval-category tool_use`
- **오픈소스 구현**: [`github.com/langchain-ai/deepagents/tree/main/libs/evals`](https://github.com/langchain-ai/deepagents/tree/main/libs/evals)

## libs/evals 실제 구조 (소스 검증)

Source: `deepagents-source-evals-structure-2026-05-23`

### 디렉토리 구조

```
libs/evals/
├── deepagents_evals/        # 공유 eval 유틸리티
├── deepagents_harbor/       # Harbor 샌드박스 연동
├── tests/
│   └── evals/
│       ├── utils.py         # AgentTrajectory, TrajectoryScorer, run_agent
│       ├── conftest.py      # pytest fixtures, --model CLI
│       ├── pytest_reporter.py   # 메트릭 수집/리포트
│       └── llm_judge.py     # LLM-as-a-judge (OpenEvals 래퍼)
├── EVAL_CATALOG.md          # 111개 eval 전체 목록
└── MODEL_GROUPS.md          # 사용 가능한 LLM 모델 카탈로그
```

### TrajectoryScorer 패턴 (소스 검증)

```python
@pytest.mark.langsmith
def test_example(model: BaseChatModel) -> None:
    agent = create_deep_agent(model=model)
    run_agent(
        agent,
        model=model,
        query="...",
        scorer=(
            TrajectoryScorer()
            .expect(agent_steps=1)              # soft: 로그만, fail 없음
            .success(final_text_contains("4"))  # hard: 실패 시 test fail
        ),
    )
```

### LLM-as-a-judge 구현 (Verified)

Source: `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`

```python
from tests.evals.llm_judge import llm_judge

scorer = TrajectoryScorer().success(
    llm_judge(
        "The answer mentions Paris.",
        "The tone is conversational.",
    )
)
```

- `llm_judge.py`는 **OpenEvals**의 `create_llm_as_judge`를 감싼다.
- 기본 judge model은 `claude-sonnet-4-6`이다.
- 호출자가 `llm_judge(..., judge_model="...")` 인자를 넘기면 기본 judge model을 override할 수 있다.
- 각 criterion은 독립적으로 평가되고, 하나라도 실패하면 전체 `SuccessAssertion`이 실패한다.
- 기본값 `include_tool_calls=False`에서는 agent text response만 judge prompt에 들어간다.
- `include_tool_calls=True`이면 tool call을 포함한 full trajectory가 judge prompt에 들어간다.
- `MODEL_GROUPS.md`는 eval 대상 모델 그룹 카탈로그이며, judge model 기본값을 정하는 파일은 아니다.

### MODEL_GROUPS.md와의 관계

`MODEL_GROUPS.md`는 eval workflow에서 사용할 수 있는 모델 그룹의 quick reference다. 파일 자체도 source of truth를 `.github/scripts/models.py`로 명시한다.

핵심 구분:

| 항목 | 결정 위치 | 의미 |
|------|-----------|------|
| Eval 대상 모델 | `.github/scripts/models.py` → `MODEL_GROUPS.md` | `--model` 또는 workflow matrix로 실행할 agent model 후보 |
| LLM-as-a-judge 기본 모델 | `libs/evals/tests/evals/llm_judge.py` | semantic assertion을 채점하는 judge model |
| Judge model override | `llm_judge(..., judge_model=...)` | 특정 eval에서 판정 모델을 명시적으로 바꿈 |

따라서 21.2의 결론은 다음이다.

> **검증됨:** Deep Agents eval의 LLM-as-a-judge 기본 판정 모델은 `claude-sonnet-4-6`이며, 이는 `MODEL_GROUPS.md`가 아니라 `llm_judge.py`의 `_DEFAULT_JUDGE_MODEL`에서 결정된다.

### BFCL v3 실행 경로 (Verified)

Source: `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`

BFCL v3는 Harbor 경로가 아니라 일반 pytest eval suite의 curated external benchmark로 실행된다.

진입점:

```text
libs/evals/tests/evals/test_external_benchmarks.py::test_bfcl_v3
→ run_bfcl_case(case, model)
→ create_deep_agent(..., tools=BFCL API tools, checkpointer=MemorySaver())
→ multi-turn agent.invoke(..., config={"configurable": {"thread_id": ...}})
→ replay ground truth calls on fresh API instances
→ compare final public API state
→ log LangSmith correctness feedback
```

핵심 파일:

| File | Role |
|------|------|
| `tests/evals/test_external_benchmarks.py` | FRAMES/Nexus/BFCL 15개 curated hard-set의 pytest entrypoint |
| `tests/evals/external_benchmarks.py` | BFCL case loading, tool wrapping, agent run, state-comparison scoring |
| `tests/evals/data/benchmark_samples/bfcl_v3_final.json` | curated BFCL v3 case source |
| `tests/evals/data/bfcl_apis/*` | stateful API implementations used as live tools |

BFCL case 구성:

- 현재 curated set은 5개 case ID를 사용한다: `multi_turn_composite_97`, `multi_turn_composite_116`, `multi_turn_composite_199`, `multi_turn_miss_func_55`, `multi_turn_miss_param_55`.
- 각 case의 `involved_classes`에 따라 `VehicleControlAPI`, `MessageAPI`, `TradingBot`, `TravelAPI`, `TicketAPI`를 생성한다.
- API instance의 public method를 `StructuredTool.from_function()`으로 감싸 Deep Agent에 전달한다.
- agent system prompt는 domain API tools 사용을 지시하고, `task`/subagent 및 file tools 사용을 금지한다.
- multi-turn conversation은 동일한 `thread_id`로 순차 `invoke()`되어 [[Checkpointing]] 기반 state continuity를 사용한다.

채점 방식:

- ground truth call string을 별도 fresh API instance에 replay한다.
- model이 tool calls로 변경한 API instance state와 ground-truth API instance state를 비교한다.
- public attribute diff가 있으면 `pytest.fail(...)`와 LangSmith `correctness=0`.
- diff가 없으면 LangSmith `correctness=1`.
- invoke exception도 `correctness=0`으로 기록된다.

정리하면, Deep Agents의 BFCL v3 적용은 "LLM tool-call 문자열 exact match"라기보다 **stateful tool execution 결과의 final state equivalence**를 보는 방식이다.

### BFCL과 Harbor의 관계

BFCL v3는 Harbor를 통해 실행되는 Terminal Bench 2.0 경로와 다르다.

| Benchmark | Execution path | Scoring |
|-----------|----------------|---------|
| BFCL v3 curated set | `pytest tests/evals/test_external_benchmarks.py`, 일반 eval workflow | API final state comparison + LangSmith correctness feedback |
| Terminal Bench 2.0 | `uv run harbor run --agent-import-path deepagents_harbor:DeepAgentsWrapper --dataset terminal-bench@2.0 ...` | Harbor reward score, optional LangSmith feedback push |

따라서 "BFCL도 Harbor를 통해 동일하게 적용되는가?"에 대한 현재 결론은 **아니다**다. BFCL은 Deep Agents eval pytest suite 내부에 직접 적응되어 있고, Harbor 통합은 Terminal Bench 2.0 중심이다.

### deepagents_harbor 모듈 구조 (Partial)

Source: `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`

`libs/evals/deepagents_harbor/`는 Harbor benchmark를 Deep Agents로 실행하기 위한 integration layer다. 핵심은 Harbor의 `BaseAgent` / `BaseEnvironment` 인터페이스와 Deep Agents의 sandbox backend 계약을 이어 주는 것이다.

| File | Role |
|------|------|
| `__init__.py` | public export surface. `DeepAgentsWrapper`, `HarborSandbox`, `LangSmithEnvironment`, LangSmith helper, failure/metadata 타입을 re-export |
| `deepagents_wrapper.py` | Harbor `BaseAgent` 구현체. `--agent-import-path deepagents_harbor:DeepAgentsWrapper`로 사용되는 진입점 |
| `backend.py` | `HarborSandbox`: Harbor `BaseEnvironment`를 Deep Agents `SandboxBackendProtocol`로 감싸는 async backend |
| `langsmith.py` | Harbor tasks → LangSmith dataset/experiment/feedback 연결 helper |
| `langsmith_environment.py` | LangSmith Sandbox를 Harbor `BaseEnvironment`로 사용하는 adapter |
| `failure.py` | 실패를 capability vs infra OOM/timeout/sandbox/unknown으로 분류 |
| `metadata.py` | host/sandbox CPU, memory, OS, concurrency 같은 infra metadata 수집 |

`DeepAgentsWrapper`와 Harbor agent interface 연결:

- `DeepAgentsWrapper`는 Harbor `BaseAgent`를 상속한다.
- Harbor CLI는 `--agent-import-path deepagents_harbor:DeepAgentsWrapper`로 이 class를 import한다.
- Harbor는 agent 생성 시 `logs_dir`, `model_name`, `--agent-kwarg` 값을 넘기고, `DeepAgentsWrapper.__init__()`은 `super().__init__(logs_dir, model_name, ...)`를 호출한다.
- `setup(environment)`은 현재 no-op이고, 실제 trial 실행은 `run(instruction, environment, context)`에서 일어난다.

`DeepAgentsWrapper.run()`의 주요 책임:

- Harbor `environment`를 `HarborSandbox`로 감싼다.
- sandbox 내부 `pwd`/`ls` 결과를 기반으로 system prompt에 작업 디렉터리 컨텍스트를 추가한다.
- 기본값은 Deep Agents CLI agent(`create_cli_agent`)를 사용하며, 옵션에 따라 SDK agent(`create_deep_agent`)도 만들 수 있다.
- CLI agent 모드에서는 `auto_approve=True`, `enable_memory=False`, `enable_skills=False`, `enable_shell=False`로 Harbor 실행 환경에 맞게 제한한다.
- `LANGSMITH_EXPERIMENT`가 있으면 LangSmith `trace()` context로 감싸고, 없으면 runnable config metadata로 기록한다.
- 실행 결과의 `AIMessage` / `ToolMessage`를 ATIF trajectory JSON으로 변환해 `trajectory.json`에 저장한다.

`HarborSandbox`의 주요 책임:

- `aexecute()`는 Harbor environment의 `exec()`를 호출하고 timeout 및 shell artifact stderr 정리를 처리한다.
- `aread`, `awrite`, `aedit`, `als`, `agrep`, `aglob` 등 async filesystem/search operations를 구현한다.
- 큰 파일 write/edit은 명령행에 content를 직접 넣지 않고 Harbor native upload/download를 사용해 OS `ARG_MAX` 문제를 피한다.
- sync method는 지원하지 않고 `NotImplementedError`를 던진다.

Harbor CI workflow 실행 경로:

1. `.github/workflows/harbor.yml` workflow dispatch 입력에서 model group, sandbox env, task 수, concurrency, agent mode를 받는다.
2. `.github/scripts/models.py harbor`가 Harbor model matrix를 만든다.
3. `scripts/harbor_langsmith.py ensure-dataset "$HARBOR_DATASET_NAME" --version "$HARBOR_DATASET_VERSION"`로 LangSmith dataset을 준비한다.
4. model별 job에서 `scripts/harbor_langsmith.py create-experiment "$HARBOR_DATASET_NAME" --model "$HARBOR_MODEL"`를 실행하고 stdout 2줄을 experiment name/URL로 해석한다.
5. `uv run harbor run --agent-import-path deepagents_harbor:DeepAgentsWrapper --dataset terminal-bench@2.0 ... --agent-kwarg use_cli_agent=false` 형태로 Harbor를 실행한다. CI 기본 `agent_mode`는 `sdk`라서 `use_cli_agent=false`가 기본이다.
6. 최신 Harbor job directory를 찾은 뒤 `scripts/harbor_langsmith.py add-feedback "$HARBOR_JOB_DIR" --project-name "$LANGSMITH_EXPERIMENT_NAME"`로 Harbor reward를 LangSmith trace feedback에 붙인다.

LangSmith sandbox를 쓸 때는 Harbor `--env` 대신 `--environment-import-path deepagents_harbor.langsmith_environment:LangSmithEnvironment`가 사용된다. docker/daytona/modal/runloop은 Harbor native `--env` 값으로 전달된다.

Makefile 로컬 실행 경로:

- `libs/evals/Makefile`은 `AGENT_MODE ?= cli`를 기본값으로 둔다.
- `AGENT_MODE=cli`이면 `--agent-kwarg use_cli_agent=true`, 그 외에는 `false`로 번역된다.
- `run-hello-world`는 `hello-world` dataset을 docker env로 1개 trial 실행한다.
- `run-terminal-bench-docker`, `run-terminal-bench-daytona`, `run-terminal-bench-modal`, `run-terminal-bench-runloop`은 모두 `terminal-bench@2.0`, `deepagents_harbor:DeepAgentsWrapper`, `jobs/terminal-bench`를 사용하고 sandbox env와 concurrency만 다르게 둔다.

`harbor_langsmith.py` 실행 경로:

- `create-dataset` / `ensure-dataset`은 Harbor tasks를 LangSmith dataset으로 만들거나 재사용한다.
- `create-experiment`는 LangSmith project/session을 만들고, workflow가 파싱할 수 있도록 experiment name과 URL만 stdout에 출력한다.
- `add-feedback`은 Harbor job folder의 trial subdirectory를 순회하고, 각 `result.json`의 `verifier_result.rewards.reward`를 `harbor_reward` feedback으로 기록한다.
- LangSmith root run matching은 `metadata.trial_name == <trial directory name>` 필터로 수행된다. verifier result가 없거나 reward가 numeric이 아니면 `0.0`으로 기록하고 comment에 이유를 남긴다.

### Harbor 샌드박스 (Terminal Bench 2.0)

```bash
uv run harbor run \
  --agent-import-path deepagents_harbor:DeepAgentsWrapper \
  --dataset terminal-bench@2.0 -n 10 \
  --jobs-dir jobs/terminal-bench --env daytona
```

지원 환경: `docker`, `daytona`, `modal`, `runloop`

Harbor → LangSmith 통합: reward score (0.0~1.0) 피드백 자동 push.

## 프레임워크별 동작

### LangChain

- `langchain.evaluation`에 평가 유틸리티 제공
- *소스 필요 (미검증)*

### LangGraph

- LangGraph 앱은 LangSmith를 통해 trace 가능
- *소스 필요 (미검증)*

### Deep Agents

- [[Deep Agents]] eval 접근법은 위 섹션 참조
- 오픈소스 eval 구현: `libs/evals`
- Source: `deepagents-blog-evals-2026-05-23`

## Interpretation

- "eval = 압력 벡터" 관점은 eval을 단순 테스트가 아닌 **agent 동작 설계 도구**로 보는 것이다.
- ideal trajectory는 correctness만으로 부족하다는 인식에서 나온다 — 정확하지만 비효율적인 모델도 프로덕션에서 문제다.
- SDK test와 model capability eval을 분리하는 것은 신호 희석을 막기 위한 중요한 설계 결정이다.

## 미해결 질문

**해소됨 (2026-05-23):**
- ✅ `libs/evals` 디렉토리 실제 구조 → `deepagents_evals/` + `deepagents_harbor/` + `tests/evals/`. pytest + TrajectoryScorer. (Source: `deepagents-source-evals-structure-2026-05-23`)
- ✅ 외부 벤치마크 적용 방법 → Harbor를 통해 Terminal Bench 2.0 실행. `DeepAgentsWrapper`로 래핑, LangSmith로 결과 추적. (Source: `deepagents-source-evals-structure-2026-05-23`)

**해소됨 (2026-06-05):**
- ✅ LLM-as-a-judge 기본 판정 모델 → `claude-sonnet-4-6`. `MODEL_GROUPS.md`는 eval 대상 모델 카탈로그이고, judge model 기본값은 `llm_judge.py`에서 결정됨. `judge_model` 인자로 override 가능. (Source: `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`)
- ✅ BFCL v3 실행 경로 → Harbor가 아니라 `test_external_benchmarks.py::test_bfcl_v3` → `external_benchmarks.py::run_bfcl_case()` 경로. BFCL API methods를 `StructuredTool`로 감싸 multi-turn Deep Agent run을 실행하고, final API state comparison으로 correctness를 기록함. (Source: `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`)

**잔여 질문:**
- eval을 지속적으로 "줄이는(reduce)" 기준은 무엇인가? — Source: `deepagents-blog-evals-2026-05-23`
- 각 프레임워크에는 어떤 내장 평가 유틸리티가 존재하는가? (LangChain, LangGraph 소스 필요)
- LangSmith를 Trajectory evaluation에 어떻게 사용할 수 있는가?

## 관련 페이지

- [[Deep Agents]]
- [[LangChain]]
- [[LangGraph]]
- [[Tool Calling]]
- [[Memory]]
- [[Context Engineering]]

## Sources

- `deepagents-blog-evals-2026-05-23` ⚠️ blog (medium confidence)
- `deepagents-source-evals-structure-2026-05-23`
- `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
