---
type: source_summary
source_id: anthropic-api-sampling-params-2026-05-30
framework: Anthropic
retrieved_at: 2026-05-30
status: draft
confidence: high
---

# Source Summary: Anthropic API — Sampling Parameters

## Source Info
- **Source ID:** `anthropic-api-sampling-params-2026-05-30`
- **Type:** source_code (type annotations + docstrings)
- **Repo:** `https://github.com/anthropics/anthropic-sdk-python`
- **File:** `src/anthropic/types/message_create_params.py`
- **Commit:** UNKNOWN (main branch, 2026-05-30 기준)

---

## Key Facts
<!-- 원문에 있는 내용만. 추론 금지. -->

### temperature
- **Type:** `float`
- **Range:** 0.0 to 1.0
- **Default:** 1.0
- 낮은 값(0.0에 가까울수록) → 분석적 작업에 적합.
- 높은 값(1.0에 가까울수록) → 창의적 생성에 적합.
- 원문 주의사항: `"Note that even with temperature of 0.0, the results will not be fully deterministic."`
  → temperature=0.0이어도 완전히 결정론적이지 않음.

### top_p
- **Type:** `float`
- **Range:** 명시 없음
- **Default:** 명시 없음
- Nucleus sampling 구현: 토큰 옵션을 내림차순 확률로 누적 분포를 계산하고, 지정한 확률 임계값에서 잘라낸다.
- 원문: `"Recommended for advanced use cases only."`

### top_k
- **Type:** `int`
- **Range:** 명시 없음
- **Default:** 명시 없음
- 각 토큰 선택 시 상위 K개 확률 옵션으로 샘플링을 제한해 저확률 이상치를 제거한다.
- 원문: `"Recommended for advanced use cases only."`

### max_tokens
- **Type:** `int` (필수)
- **Range:** 모델마다 다름 (문서 참조)
- **Default:** 없음 (필수 파라미터)
- 모델이 생성하기 전에 멈추는 최대 토큰 수.
- 모델이 max_tokens 이전에 멈출 수도 있음.
- `0`으로 설정하면 출력 생성 없이 프롬프트 캐시를 사전 워밍(pre-warm)한다.

---

## Important Terms
- [[Sampling]] — temperature / top_p / top_k 파라미터가 다음 토큰 선택에 미치는 영향
- [[Token]] — 모델이 읽고 생성하는 기본 단위
- [[Context Window]] — max_tokens와 입력 길이의 합이 context window를 넘으면 안 됨

---

## Interpretation
<!-- 내가 이해한 의미. 원문과 분리. -->
- Anthropic 기준 temperature 범위는 0.0~1.0. OpenAI는 0.0~2.0이므로 provider마다 다름에 주의.
- temperature=0.0도 완전 결정론적이 아니라는 점은 sampling의 확률적 본질을 보여줌.
- top_p와 top_k는 "advanced use cases only"라는 표현으로 보아 대부분의 경우 temperature만으로 충분함을 시사.

---

## Open Questions
- top_p의 실제 range는? (0.0~1.0 또는 다른가?)
- temperature와 top_p를 동시에 설정하면 어떻게 되는가? (Anthropic API에서 권장 조합이 있는가?)
- OpenAI의 temperature range(0.0~2.0)와 Anthropic(0.0~1.0)의 실질적 차이는?

---

## Used By
- [[Sampling]]
- [[Token]]
