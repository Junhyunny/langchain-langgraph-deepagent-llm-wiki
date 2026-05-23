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
  - `libs/evals/README.md`
  - `libs/evals/CONTRIBUTING.md`

## Key Facts
- `MODEL_GROUPS.md`는 auto-generated 문서이며 eval workflow에서 사용하는 모델 세트 카탈로그다.
- `CONTRIBUTING.md`의 test suite 설명에 BFCL v3가 external benchmarks(`test_external_benchmarks.py`) 범위에 포함됨이 명시되어 있다.
- `README.md`와 `CONTRIBUTING.md`는 Harbor 연동(terminal-bench) 실행 경로를 문서화한다.

## Interpretation
- “judge model이 무엇인지”는 이 소스만으로 확정 불가하며 별도 source(`llm_judge.py`, 모델 레지스트리)가 필요하다.
- BFCL 적용 여부 자체는 문서 기준으로는 확인 가능(coverage claim 수준).

## Open Questions
- LLM-as-a-judge에서 실제 judge 모델 선택 규칙은 어디에서 결정되는가?
- BFCL score 계산 로직의 canonical 구현 파일은 무엇인가?

## Related Wiki Pages
- [[Evaluation]]
- [[Deep Agents]]

## Sources
- `deepagents-evals-model-groups-harbor-bfcl-2026-05-23`
