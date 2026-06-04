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
  - `.github/scripts/models.py`
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
- `README.md`와 `CONTRIBUTING.md`는 Harbor 연동(terminal-bench) 실행 경로를 문서화한다.

## Interpretation
- LLM-as-a-judge의 기본 판정 모델은 `MODEL_GROUPS.md`가 아니라 `llm_judge.py`에서 직접 결정된다.
- `MODEL_GROUPS.md`는 eval 대상 모델 그룹 카탈로그다. judge model 결정 경로의 보조 근거는 될 수 있지만, 기본 judge model의 source of truth는 아니다.
- BFCL 적용 여부 자체는 문서 기준으로는 확인 가능(coverage claim 수준).

## Open Questions
- ✅ LLM-as-a-judge에서 실제 judge 모델 선택 규칙은 `libs/evals/tests/evals/llm_judge.py`에서 결정된다. 기본값은 `claude-sonnet-4-6`, 호출자가 `judge_model` 인자로 override 가능하다.
- BFCL score 계산 로직의 canonical 구현 파일은 무엇인가?

## Related Wiki Pages
- [[Evaluation]]
- [[Deep Agents]]

## Sources
- `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
