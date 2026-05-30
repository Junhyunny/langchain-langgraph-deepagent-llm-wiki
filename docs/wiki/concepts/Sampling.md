---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-30
sources:
  - anthropic-api-sampling-params-2026-05-30
  - langchain-docs-models-2026-05-30
---

# Sampling

## Summary

Sampling은 LLM이 각 위치에서 다음 토큰을 선택하는 방식을 제어하는 메커니즘이다. 모델이 가능한 다음 토큰에 대해 확률 분포를 계산한 뒤, sampling 파라미터(temperature, top-p, top-k)가 그 분포에서 어떻게 토큰을 뽑을지 결정한다.

## Why It Matters

- 같은 프롬프트라도 sampling 설정에 따라 결과가 달라진다.
- 창의적 작업(높은 temperature)과 분석적 작업(낮은 temperature)은 요구하는 설정이 다르다.
- 에이전트 설계 시 도구 호출의 결정론성을 높이려면 낮은 temperature가 필요하다.

## Key Concepts

- [[Token]] — sampling은 토큰 단위로 일어남
- [[Chat Models]] — temperature, top_p, top_k는 Chat Model의 표준 파라미터
- [[Agent Runtime]] — 에이전트에서 모델의 sampling 설정이 행동 일관성에 영향

---

## Verified Facts

### Greedy Decoding vs Sampling
*Source: HuggingFace Transformers docs (transformers main, 2026-05-30)*

- **Greedy decoding:** 각 단계에서 가장 높은 확률의 토큰 하나만 선택. `temperature → 0`에 가까워질수록 이에 가깝다.
  - 단점: 짧은 출력에는 효과적이나 긴 시퀀스에서 반복 발생.
- **Sampling:** 확률 분포 전체에서 무작위로 토큰 선택. 반복을 줄이고 더 창의적·다양한 출력 생성.

### Temperature
*Source: `anthropic-api-sampling-params-2026-05-30`*

- **Type:** float, **Range:** 0.0~1.0 (Anthropic 기준; OpenAI는 0.0~2.0)
- **Default:** 1.0
- 낮은 값(0.0 근처) → 분석적 작업에 적합, 분포가 뾰족해져 확률 높은 토큰이 선택될 가능성 증가.
- 높은 값(1.0 근처) → 창의적 생성에 적합, 분포가 평탄해져 다양한 토큰이 선택될 기회 증가.
- **주의:** `"even with temperature of 0.0, the results will not be fully deterministic."` — 0.0이어도 완전 결정론적이지 않음.

```python
# 분석적 / 결정론적 → 낮은 temperature
model = init_chat_model("claude-sonnet-4-6", temperature=0.0)

# 창의적 / 다양한 → 높은 temperature
model = init_chat_model("claude-sonnet-4-6", temperature=1.0)
```
*Source: `langchain-docs-models-2026-05-30`*

### Top-p (Nucleus Sampling)
*Source: `anthropic-api-sampling-params-2026-05-30`*

- 토큰 옵션을 확률 내림차순으로 정렬 후 누적 확률이 `p`에 도달하는 지점에서 잘라낸다.
- 잘려진 후보 집합(nucleus)에서만 샘플링.
- 상황에 따라 nucleus 크기가 유동적 — 확률이 집중되면 nucleus가 작아지고, 분산되면 커진다.
- Anthropic: "Recommended for advanced use cases only."

### Top-k
*Source: `anthropic-api-sampling-params-2026-05-30`*

- 상위 K개 확률 토큰만 남기고 나머지 제거 후 샘플링.
- 저확률 이상치(outlier)를 제거하는 효과.
- Top-p와 달리 nucleus 크기가 고정(항상 K개).
- Anthropic: "Recommended for advanced use cases only."

### 파라미터 조합 가이드
*Source: `langchain-docs-models-2026-05-30`, `anthropic-api-sampling-params-2026-05-30`*

| 사용 사례 | temperature | top_p / top_k |
|----------|-------------|---------------|
| 분석, 코드, 도구 호출 | 낮게 (0.0~0.3) | 기본값 유지 |
| 일반 대화 | 중간 (0.5~0.7) | 기본값 유지 |
| 창의적 글쓰기 | 높게 (0.8~1.0) | 필요시 조정 |
| 고급 fine-tuning | 선택 | top_p 또는 top_k 조정 |

---

## Interpretation

- 대부분의 경우 `temperature`만 조정하면 충분하다. top_p / top_k는 특수한 경우에만 필요 (Anthropic 가이드 근거).
- temperature=0.0도 완전 결정론적이 아닌 이유는 floating-point 연산의 비결정성 때문일 것으로 추정 (⚠️ 추측, 소스 없음).
- top_p와 top_k를 동시에 사용할 경우 두 조건의 교집합이 nucleus가 될 것으로 추정 (⚠️ 추측, 소스 없음).

---

## Source Code References
- Repo: `anthropics/anthropic-sdk-python`
- Commit: UNKNOWN
- Files:
  - `src/anthropic/types/message_create_params.py` — temperature, top_p, top_k 파라미터 타입 정의 및 docstring

## Tests
- TBD

## Related Pages
- [[Token]]
- [[Chat Models]]
- [[Agent Runtime]]
- [[Context Engineering]]

## Open Questions
- top_p의 실제 range는 0.0~1.0인가?
- temperature와 top_p를 동시에 설정하면 어떻게 동작하는가? (Anthropic 공식 권장 조합이 있는가?)
- OpenAI의 temperature range(0.0~2.0)와 Anthropic(0.0~1.0)의 실질적 차이는?
- temperature=0.0이 완전 결정론적이 아닌 정확한 이유는?

## Sources
- `anthropic-api-sampling-params-2026-05-30`
- `langchain-docs-models-2026-05-30`
