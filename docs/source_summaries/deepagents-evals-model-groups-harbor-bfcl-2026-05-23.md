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
  - `.github/scripts/models.py`
  - `.github/workflows/evals.yml`
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

## Interpretation
- LLM-as-a-judge의 기본 판정 모델은 `MODEL_GROUPS.md`가 아니라 `llm_judge.py`에서 직접 결정된다.
- `MODEL_GROUPS.md`는 eval 대상 모델 그룹 카탈로그다. judge model 결정 경로의 보조 근거는 될 수 있지만, 기본 judge model의 source of truth는 아니다.
- BFCL은 Harbor 통합과 별개로 Deep Agents의 일반 pytest eval suite에 들어간 curated external benchmark다.
- BFCL v3를 Deep Agents에 맞게 조정한 핵심은 "벤치마크 ground truth tool-call 문자열"을 그대로 비교하지 않고, 동일한 API class의 최종 state를 비교하는 방식이다.

## Open Questions
- ✅ LLM-as-a-judge에서 실제 judge 모델 선택 규칙은 `libs/evals/tests/evals/llm_judge.py`에서 결정된다. 기본값은 `claude-sonnet-4-6`, 호출자가 `judge_model` 인자로 override 가능하다.
- ✅ BFCL score 계산 로직의 canonical 구현 파일은 `libs/evals/tests/evals/external_benchmarks.py`다. `run_bfcl_case()`가 state comparison을 수행하고 LangSmith `correctness` feedback을 기록한다.

## Related Wiki Pages
- [[Evaluation]]
- [[Deep Agents]]

## Sources
- `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
