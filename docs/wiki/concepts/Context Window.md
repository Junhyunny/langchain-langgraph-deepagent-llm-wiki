---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-30
sources:
  - langchain-docs-models-2026-05-30
  - anthropic-api-sampling-params-2026-05-30
  - tiktoken-bpe-2026-05-30
---

# Context Window

## Summary

Context Window는 모델이 한 번의 호출에서 처리할 수 있는 **토큰의 최대 개수**다. 입력(프롬프트·대화 히스토리·도구 정의 등)과 출력(생성 토큰)이 모두 같은 예산 안에서 다뤄지며, 이 한계를 넘으면 호출이 실패하거나 오래된 내용이 잘려나간다. LangChain에서는 `model.profile["max_input_tokens"]`로 노출된다.

## Why It Matters

- **모든 에이전트의 근본 제약:** 대화가 길어지거나 도구 결과가 누적되면 context window를 초과한다. 이를 관리하는 것이 [[Context Engineering]]의 핵심이다.
- **미들웨어 트리거:** [[SummarizationMiddleware]]는 context window 크기를 기준으로 요약을 트리거한다.
- **전략 자동 추론:** `create_agent`는 model profile의 `max_input_tokens`·modality 정보로 입력 게이팅과 structured output 전략을 자동 추론한다.
- **비용·지연:** 입력 토큰이 많을수록 비용과 지연이 증가하므로, context window를 얼마나 채우는지가 곧 비용 설계다.

## Key Concepts

- [[Token]] — context window의 측정 단위
- [[Chat Models]] — `model.profile`로 context window를 노출하는 추상화
- [[SummarizationMiddleware]] — context window 초과를 막기 위한 요약 전략
- [[Context Engineering]] — context window 예산을 배분하는 상위 전략

---

## Verified Facts

### 정의와 측정 단위
*Source: `langchain-docs-models-2026-05-30`*

- Context window는 **토큰 단위**로 측정된다. 토큰의 정의와 분할 방식은 [[Token]] 참조.
- LangChain `langchain>=1.1`부터 `model.profile`이 지원 기능 dict를 노출하며, 그중 `max_input_tokens`가 모델의 context window 크기에 해당한다.

```python
from langchain.chat_models import init_chat_model

model = init_chat_model("claude-sonnet-4-6")
print(model.profile["max_input_tokens"])  # 예: 200000
```

- profile 데이터는 오픈소스 [models.dev](https://github.com/sst/models.dev)에서 가져와 LangChain용 필드로 보강된다. profile은 일반 dict로 직접 덮어쓰거나 인스턴스화 시 `profile=...`로 지정 가능하다.

### 입력과 출력은 같은 예산을 공유한다
*Source: `langchain-docs-models-2026-05-30`, `anthropic-api-sampling-params-2026-05-30`*

- `max_tokens` 파라미터는 **출력**의 총 토큰 수를 제한한다 (출력 길이 제어).
- `max_input_tokens`(model profile)는 **입력** 토큰 한계를 나타낸다.
- 두 값은 별개의 필드지만, provider API 차원에서는 입력+출력 합계가 모델의 전체 context window를 넘을 수 없다.
  - ⚠️ 입력 한계와 전체 window의 정확한 관계(예: `max_input_tokens`가 출력분을 제외한 값인지)는 provider마다 다를 수 있어 추가 검증 필요. (Needs Source)

### model profile의 활용처
*Source: `langchain-docs-models-2026-05-30`*

`max_input_tokens`는 LangChain 내부에서 다음에 직접 사용된다:

| 사용처 | 동작 |
|--------|------|
| [[SummarizationMiddleware]] | context window 크기에 도달하면 대화 히스토리를 요약 |
| `create_agent` | structured output 전략 자동 추론 |
| 입력 게이팅 | modality·`max_input_tokens` 기반으로 입력 허용 여부 판단 |

### Prompt caching과의 관계
*Source: `langchain-docs-models-2026-05-30`, `anthropic-api-sampling-params-2026-05-30`*

- 많은 provider가 동일 토큰 반복 처리 시 latency·비용 절감을 위해 prompt caching을 제공한다 (implicit: OpenAI/Gemini 자동, explicit: 수동 캐시 지점 지정).
- Anthropic API에서 `max_tokens=0`으로 설정하면 출력 생성 없이 **프롬프트 캐시를 사전 워밍(pre-warm)**할 수 있다.
  *Source: `anthropic-api-sampling-params-2026-05-30`*

---

## Interpretation
<!-- 해석. 검증된 사실과 분리. -->

- Context window는 에이전트가 길어질수록 가장 먼저 부딪히는 제약이다. [[Checkpointing]]으로 상태를 저장하더라도, 한 step의 모델 호출은 여전히 window 한계를 지킨다.
- 한국어처럼 bytes-per-character가 높은 언어는 같은 분량의 텍스트가 더 많은 토큰을 소비하므로 동일 window에서 담을 수 있는 "실제 내용"이 적다 (⚠️ 추정, 소스 없음 — [[Token]]의 Open Questions 참조).

## Hypotheses
- 입력+출력 합계가 전체 context window를 구성하며, `max_input_tokens`는 입력에만 적용되는 별도 한계일 것으로 추정. ⚠️
  Status: Needs verification (provider API 레퍼런스 확인 필요)

---

## Source Code References
- Repo: `langchain-ai/langchain`
- Commit: UNKNOWN
- Files (미확인 — 다음 코드 리딩 대상):
  - `model.profile` 구현 및 `max_input_tokens` 소비 지점
  - `SummarizationMiddleware`의 context window 트리거 로직

## Tests
- TBD

## Related Pages
- [[Token]]
- [[Chat Models]]
- [[Sampling]]
- [[SummarizationMiddleware]]
- [[Context Engineering]]
- [[Memory]]

## Open Questions
- `max_input_tokens`는 출력분을 제외한 입력 전용 한계인가, 아니면 전체 window 크기인가?
- 입력+출력 합계가 window를 초과하면 provider는 어떤 동작을 하는가 (오류 vs 잘림)?
- 도구 정의·시스템 프롬프트는 context window 예산에서 어떻게 계산되는가?
- LangChain은 호출 전에 토큰 수를 미리 검증하는가, 아니면 provider 오류에 의존하는가?

## Sources
- `langchain-docs-models-2026-05-30`
- `anthropic-api-sampling-params-2026-05-30`
- `tiktoken-bpe-2026-05-30`
