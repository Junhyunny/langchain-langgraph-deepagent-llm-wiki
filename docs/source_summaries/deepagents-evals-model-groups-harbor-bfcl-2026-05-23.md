---
type: source_summary
source_id: deepagents-evals-model-groups-harbor-bfcl-2026-05-23
title: "Deep Agents evals — MODEL_GROUPS, Harbor, BFCL references"
framework: Deep Agents
retrieved_at: "2026-05-23"
status: verified
confidence: medium
---

# Source Summary: Deep Agents eval model groups + Harbor/BFCL

## Source Info
- **Source ID:** `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
- **Type:** source_code / docs
- **Files:**
  - `libs/evals/MODEL_GROUPS.md`
  - `libs/evals/tests/evals/llm_judge.py`
  - `libs/evals/tests/evals/test_external_benchmarks.py`
  - `libs/evals/tests/evals/external_benchmarks.py`
  - `libs/evals/deepagents_harbor/__init__.py`
  - `libs/evals/deepagents_harbor/deepagents_wrapper.py`
  - `libs/evals/deepagents_harbor/backend.py`
  - `libs/evals/deepagents_harbor/langsmith.py`
  - `libs/evals/deepagents_harbor/langsmith_environment.py`
  - `libs/evals/deepagents_harbor/failure.py`
  - `libs/evals/deepagents_harbor/metadata.py`
  - `.github/scripts/models.py`
  - `.github/workflows/evals.yml`
  - `.github/workflows/harbor.yml`
  - `libs/evals/Makefile`
  - `libs/evals/scripts/harbor_langsmith.py`
  - `libs/evals/README.md`
  - `libs/evals/CONTRIBUTING.md`

## Key Facts
- `MODEL_GROUPS.md`는 auto-generated 문서이며 eval workflow에서 사용하는 모델 세트 카탈로그다.
- `MODEL_GROUPS.md`는 source of truth가 아니라 `.github/scripts/models.py`에서 생성된 quick reference다.
- `MODEL_GROUPS.md`의 `fast` 그룹에는 `anthropic:claude-sonnet-4-6`, `google_genai:gemini-3-flash-preview`, `openai:gpt-5.4-mini`가 포함된다.
- `llm_judge.py`는 `openevals.llm.create_llm_as_judge`를 감싼 `LLMJudge` / `llm_judge()` 구현체다.
- `llm_judge.py`의 기본 judge model은 `_DEFAULT_JUDGE_MODEL = "claude-sonnet-4-6"`이다.
- `llm_judge(*criteria, judge_model=..., include_tool_calls=False)` 호출자가 `judge_model`을 넘기면 기본 judge model을 override할 수 있다.
- `include_tool_calls=False`가 기본값이면 judge는 agent text response만 본다. `include_tool_calls=True`이면 tool call을 포함한 full trajectory를 judge prompt에 넣는다.
- `CONTRIBUTING.md`의 test suite 설명에 BFCL v3가 external benchmarks(`test_external_benchmarks.py`) 범위에 포함됨이 명시되어 있다.
- `test_external_benchmarks.py`는 15개 curated hard-set을 실행한다: FRAMES 5개, Nexus 5개, BFCL v3 5개.
- `test_bfcl_v3()`는 `@pytest.mark.eval_category("tool_use")`, `@pytest.mark.langsmith`, `pytest.mark.parametrize("case", _tiered_params(BFCL_V3_CASES, _BFCL_V3_HILLCLIMB))`로 정의되고 `run_bfcl_case(case, model)`을 호출한다.
- `external_benchmarks.py`의 BFCL 경로는 `tests/evals/data/benchmark_samples/bfcl_v3_final.json`에서 5개 case ID를 선택한다.
- BFCL case는 `VehicleControlAPI`, `MessageAPI`, `TradingBot`, `TravelAPI`, `TicketAPI` 중 case가 요구하는 API class를 인스턴스화하고 public method를 `StructuredTool`로 감싼다.
- BFCL agent는 `create_deep_agent(model=model, tools=tools, system_prompt=_BFCL_SYSTEM_PROMPT, checkpointer=MemorySaver())`로 생성된다.
- BFCL은 multi-turn conversation을 같은 `thread_id` config로 순차 `agent.invoke()` 하며, stateful tool/API 상태를 유지한다.
- BFCL 채점은 text exact match가 아니라 state comparison이다. ground truth call strings를 fresh API instance에 replay한 뒤, model-run API instance의 public state와 비교한다.
- state diff가 있거나 invoke exception이 발생하면 LangSmith feedback `correctness=0`; diff가 없으면 `correctness=1`을 기록한다.
- BFCL 경로는 Harbor CLI를 사용하지 않는다. Harbor 문서화 경로는 Terminal Bench 2.0용이다.
- `.github/workflows/evals.yml`는 `eval_categories` 입력에 `tool_use`를 포함하고, 이 경로로 `test_external_benchmarks.py::test_bfcl_v3`도 일반 eval pytest suite 안에서 실행될 수 있다.
- `README.md`와 `CONTRIBUTING.md`는 Harbor 연동(terminal-bench) 실행 경로를 문서화한다.

### `deepagents_harbor/` module structure

| File | Key exports / role |
|------|--------------------|
| `__init__.py` | Public package surface: `DeepAgentsWrapper`, `HarborSandbox`, `LangSmithEnvironment`, LangSmith dataset/experiment/feedback helpers, `FailureCategory`, `InfraMetadata` |
| `deepagents_wrapper.py` | Harbor `BaseAgent` implementation. Builds either Deep Agents CLI agent (`create_cli_agent`) or SDK agent (`create_deep_agent`), injects Harbor sandbox backend, runs task instruction, saves ATIF trajectory. |
| `backend.py` | `HarborSandbox`, an async `SandboxBackendProtocol` adapter over Harbor `BaseEnvironment`. Provides `aexecute`, `aread`, `awrite`, `aedit`, `als`, `agrep`, `aglob`, `aupload_files`, `adownload_files`. Sync methods intentionally raise `NotImplementedError`. |
| `langsmith.py` | LangSmith integration helpers: create/ensure dataset from Harbor tasks, create experiment sessions, resolve API key, add Harbor reward feedback to LangSmith traces. |
| `langsmith_environment.py` | Harbor `BaseEnvironment` implementation backed by LangSmith sandboxes. Loads Docker image/snapshot, starts sandbox, executes commands, transfers files. |
| `failure.py` | Failure classification utilities that distinguish model capability failure from infra OOM, timeout, sandbox/network failure, or unknown. |
| `metadata.py` | Best-effort host/sandbox infrastructure metadata collection for post-hoc noise analysis. |

`deepagents_wrapper.py` is the agent-facing adapter Harbor imports via `--agent-import-path deepagents_harbor:DeepAgentsWrapper`. It wraps the Harbor environment in `HarborSandbox`, then passes that backend to the Deep Agents CLI/SDK agent so file and command tools operate inside the Harbor trial environment.

### `DeepAgentsWrapper` to Harbor `BaseAgent`

`DeepAgentsWrapper` subclasses Harbor's `BaseAgent` and is loaded by Harbor with `--agent-import-path deepagents_harbor:DeepAgentsWrapper`.

Connection path:

1. Harbor CLI imports `deepagents_harbor:DeepAgentsWrapper`.
2. Harbor constructs the agent with `logs_dir`, `model_name`, and any `--agent-kwarg` values.
3. `DeepAgentsWrapper.__init__()` calls `super().__init__(logs_dir, model_name, ...)`, initializes the chat model, and stores execution-mode settings.
4. Harbor calls `setup(environment)`, which is currently a no-op.
5. Harbor calls `run(instruction, environment, context)` for each trial.
6. `run()` wraps Harbor `BaseEnvironment` with `HarborSandbox`, builds either a CLI agent (`create_cli_agent`) or SDK agent (`create_deep_agent`), invokes it with the benchmark instruction, and saves `trajectory.json` in ATIF format.

The interface boundary is therefore Harbor `BaseAgent.run()` on one side and Deep Agents `SandboxBackendProtocol` on the other side. `HarborSandbox` is the adapter between them.

### Harbor workflow and local targets

`.github/workflows/harbor.yml` is a manual GitHub Actions workflow for Terminal Bench 2.0. The flow is:

1. Resolve model matrix with `.github/scripts/models.py harbor`.
2. Ensure the LangSmith dataset exists with `scripts/harbor_langsmith.py ensure-dataset terminal-bench --version 2.0`.
3. Create a LangSmith experiment with `scripts/harbor_langsmith.py create-experiment terminal-bench --model "$HARBOR_MODEL"`.
4. Run Harbor:

```bash
uv run harbor run \
  --agent-import-path deepagents_harbor:DeepAgentsWrapper \
  --dataset terminal-bench@2.0 \
  -n "$HARBOR_CONCURRENCY" \
  --jobs-dir jobs/terminal-bench \
  --model "$HARBOR_MODEL" \
  --agent-kwarg use_cli_agent=false
```

If `sandbox_env=langsmith`, the workflow uses `--environment-import-path deepagents_harbor.langsmith_environment:LangSmithEnvironment`; otherwise it uses Harbor's `--env docker|daytona|modal|runloop`. The workflow input defaults `agent_mode` to `sdk`, so CI passes `use_cli_agent=false` by default.

`libs/evals/Makefile` provides local shortcuts. It defaults `AGENT_MODE ?= cli`, translates that into `--agent-kwarg use_cli_agent=true`, and exposes `run-hello-world`, `run-terminal-bench-docker`, `run-terminal-bench-daytona`, `run-terminal-bench-modal`, and `run-terminal-bench-runloop`.

### `harbor_langsmith.py` execution path

`libs/evals/scripts/harbor_langsmith.py` is a CLI wrapper around `deepagents_harbor.langsmith`.

Subcommands:

- `create-dataset`: creates a LangSmith dataset from Harbor tasks.
- `ensure-dataset`: creates or reuses the dataset.
- `create-experiment`: creates a LangSmith project/session and prints exactly two stdout lines: experiment name and URL. `harbor.yml` parses those two lines into `LANGSMITH_EXPERIMENT` and `LANGSMITH_EXPERIMENT_URL`.
- `add-feedback`: reads Harbor trial results from a job directory and writes `harbor_reward` feedback to matching LangSmith traces.

`add_feedback()` iterates trial directories under the Harbor job folder, reads each `result.json`, extracts `verifier_result.rewards.reward`, then finds the corresponding LangSmith root run by `metadata.trial_name == <trial directory name>`. Missing verifier output becomes reward `0.0` with an explanatory comment.

## Interpretation
- LLM-as-a-judge의 기본 판정 모델은 `MODEL_GROUPS.md`가 아니라 `llm_judge.py`에서 직접 결정된다.
- `MODEL_GROUPS.md`는 eval 대상 모델 그룹 카탈로그다. judge model 결정 경로의 보조 근거는 될 수 있지만, 기본 judge model의 source of truth는 아니다.
- BFCL은 Harbor 통합과 별개로 Deep Agents의 일반 pytest eval suite에 들어간 curated external benchmark다.
- BFCL v3를 Deep Agents에 맞게 조정한 핵심은 "벤치마크 ground truth tool-call 문자열"을 그대로 비교하지 않고, 동일한 API class의 최종 state를 비교하는 방식이다.
- `deepagents_harbor/`는 Terminal Bench 2.0 같은 Harbor benchmark를 Deep Agents로 실행하기 위한 integration layer다. 핵심 경계는 Harbor `BaseAgent` / `BaseEnvironment`와 Deep Agents `SandboxBackendProtocol` 사이를 연결하는 것이다.
- CI의 Harbor workflow 기본값은 SDK agent mode이고, 로컬 Makefile 기본값은 CLI agent mode다. 둘 다 같은 `DeepAgentsWrapper`를 쓰며 `--agent-kwarg use_cli_agent=<true|false>`로 분기한다.

## Open Questions
- ✅ LLM-as-a-judge에서 실제 judge 모델 선택 규칙은 `libs/evals/tests/evals/llm_judge.py`에서 결정된다. 기본값은 `claude-sonnet-4-6`, 호출자가 `judge_model` 인자로 override 가능하다.
- ✅ BFCL score 계산 로직의 canonical 구현 파일은 `libs/evals/tests/evals/external_benchmarks.py`다. `run_bfcl_case()`가 state comparison을 수행하고 LangSmith `correctness` feedback을 기록한다.
- ✅ Harbor agent interface 연결은 `DeepAgentsWrapper(BaseAgent)`와 `--agent-import-path deepagents_harbor:DeepAgentsWrapper`에서 시작한다. Harbor `BaseEnvironment`는 `HarborSandbox`를 통해 Deep Agents sandbox backend로 변환된다.
- ✅ `harbor.yml`, `Makefile`, `harbor_langsmith.py` 실행 경로를 확인했다. CI는 Terminal Bench 2.0 + LangSmith experiment/feedback 중심이고, 로컬 Makefile은 sandbox별 Harbor shortcut이다.

## Related Wiki Pages
- [[Evaluation]]
- [[Deep Agents]]

## Sources
- `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
