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
  - tiktoken-bpe-2026-05-30
  - langchain-docs-models-2026-05-30
---

# Token

## Summary

Token은 LLM이 텍스트를 처리하는 기본 단위다. 모델은 문자나 단어를 직접 읽지 않고, 텍스트를 token(숫자 ID)의 시퀀스로 변환해 처리한다. 영어 기준 1 token ≈ 4 bytes ≈ 0.75 단어에 해당한다.

## Why It Matters

- **컨텍스트 윈도우**는 토큰 수로 측정된다 — 입력+출력 합계가 한계를 넘으면 오류.
- **비용**은 토큰 수로 청구된다 (provider마다 다름).
- 토큰 수를 예측할 수 있어야 프롬프트 설계와 비용 관리가 가능하다.

## Key Concepts

- [[Context Window]] — 입력+출력 토큰의 최대 합계
- [[Sampling]] — 모델이 다음 토큰을 확률적으로 선택하는 과정
- [[Chat Models]] — token 단위로 입력·출력을 처리하는 LangChain 추상화

---

## Verified Facts

### 토큰이란?
*Source: `tiktoken-bpe-2026-05-30`*

- 언어 모델은 텍스트를 직접 읽지 않고 "numbers known as tokens"로 처리한다.
- 토큰 = byte sequence → integer ID 매핑. 모델은 이 정수 시퀀스를 입력으로 받고 같은 형태로 출력한다.
- **공식 정의 (LangChain docs):** "모델이 읽고 생성하는 기본 단위. provider마다 정의가 다를 수 있으나 일반적으로 단어 전체 또는 일부를 나타낸다."
  *Source: `langchain-docs-models-2026-05-30`*

### BPE (Byte Pair Encoding)
*Source: `tiktoken-bpe-2026-05-30`*

tiktoken(OpenAI)이 사용하는 토크나이저 알고리즘. 다음 특성을 가진다:

| 특성 | 설명 |
|------|------|
| 가역성 | 토큰 → 원문 복원 가능, 무손실 |
| 범용성 | 어떤 텍스트에도 작동 |
| 압축 | 평균 1 token ≈ 4 bytes |
| 언어 인식 | 빈도 기반으로 의미 있는 subword 단위 형성 |

**BPE 학습 과정:**
1. 256개 개별 byte 각각을 토큰으로 초기화 (기본 어휘 256개)
2. regex로 입력 텍스트를 대략적 단어 단위로 사전 분할
3. 학습 데이터에서 가장 빈번한 인접 byte 쌍을 찾아 새 토큰으로 병합
4. 목표 어휘 크기(예: GPT-4는 ~100k)에 도달할 때까지 반복

**인코딩 예시:**
- "encoding" → "encod" + "ing" (두 서브워드 토큰)
- 자주 등장하는 단어는 단일 토큰이 될 수 있음

### 컨텍스트 윈도우와의 관계
*Source: `langchain-docs-models-2026-05-30`*

- LangChain `model.profile`의 `max_input_tokens`가 입력 가능한 최대 토큰 수 = context window 크기.
- 예: Claude Sonnet 4.6 → `max_input_tokens: 200000`

```python
model = init_chat_model("claude-sonnet-4-6")
print(model.profile["max_input_tokens"])  # 예: 200000
```

---

## Interpretation

- 실용적으로는 "영어 단어 1개 ≈ 1~2 토큰"으로 추정하면 된다 (⚠️ 추정, tiktoken 실측 필요).
- 한국어는 영어보다 bytes-per-character가 많아 동일 텍스트 길이에서 더 많은 토큰을 소비할 가능성이 높다 (⚠️ 추정, 소스 없음).
- BPE가 "가역적"이라는 것은 모델의 출력 토큰 시퀀스를 손실 없이 텍스트로 변환할 수 있음을 의미한다.

---

## Source Code References
- Repo: `openai/tiktoken`
- Commit: UNKNOWN
- Files:
  - `tiktoken/_educational.py` — BPE 알고리즘 교육용 구현
  - `README.md` — 기본 특성 및 성능 수치

## Tests
- TBD

## Related Pages
- [[Chat Models]]
- [[Sampling]]
- [[Context Window]]
- [[SummarizationMiddleware]]

## Open Questions
- 한국어 텍스트의 평균 bytes-per-token은?
- GPT-4o와 Claude의 tokenizer 어휘 크기 차이는?
- LangChain의 `get_num_tokens` 메서드는 tiktoken을 내부에서 사용하는가?
- provider마다 tokenizer가 다른데, 같은 텍스트가 서로 다른 토큰 수로 계산되는 실제 사례는?

## Sources
- `tiktoken-bpe-2026-05-30`
- `langchain-docs-models-2026-05-30`
