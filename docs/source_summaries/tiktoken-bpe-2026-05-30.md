---
type: source_summary
source_id: tiktoken-bpe-2026-05-30
framework: OpenAI
retrieved_at: 2026-05-30
status: draft
confidence: high
---

# Source Summary: tiktoken — BPE Tokenization

## Source Info
- **Source ID:** `tiktoken-bpe-2026-05-30`
- **Type:** source_code + README
- **Repo:** `https://github.com/openai/tiktoken`
- **Files:**
  - `README.md`
  - `tiktoken/_educational.py`
- **Commit:** UNKNOWN (main branch, 2026-05-30 기준)

---

## Key Facts
<!-- 원문에 있는 내용만. 추론 금지. -->

### Token이란
- 언어 모델은 텍스트를 직접 읽지 않고 "a sequence of numbers (known as tokens)"로 처리한다.
- tiktoken은 텍스트와 이 숫자 표현 사이를 변환하는 라이브러리다.
- 토큰 = byte sequence → integer ID 매핑의 dictionary entry.

### BPE (Byte Pair Encoding)
- tiktoken이 사용하는 토크나이저 방식.
- **가역적(reversible)이고 무손실(lossless):** "It's reversible and lossless, so you can convert tokens back into the original text."
- **범용성:** 어떤 텍스트에도 작동, 낯선 내용 포함.
- **압축 효율:** token sequence는 raw bytes보다 짧다. "each token corresponds to about 4 bytes."
- **언어 인식:** 알고리즘이 일반적인 언어 단위를 인식함. 예: "encoding"을 "encod"+"ing"처럼 의미 있는 subword로 분할.
- tiktoken은 유사 오픈소스 토크나이저보다 "3-6x faster."

### BPE 학습 과정 (step-by-step)
1. **초기화:** 256개 개별 byte 값 각각에 토큰 할당 (기본 어휘 256개).
2. **텍스트 분할:** regex 패턴으로 입력 텍스트를 대략적인 단어 단위로 나눈 후 BPE 적용.
3. **반복 병합:** 학습 데이터에서 가장 빈번한 인접 byte 쌍을 찾아 새 토큰으로 결합. 목표 어휘 크기에 도달할 때까지 반복.

### BPE 인코딩 과정
- "iterate over all pairs and find the pair we want to merge the most"
- 학습 시 계산된 merge rank(우선순위 순서)로 쌍을 선택.

---

## Important Terms
- [[Token]] — 모델이 읽고 생성하는 기본 단위, tiktoken이 관리하는 integer ID
- [[Context Window]] — 입력+출력 토큰 수의 합이 context window를 초과하면 안 됨
- BPE (Byte Pair Encoding) — tiktoken의 토크나이저 알고리즘

---

## Interpretation
<!-- 내가 이해한 의미. 원문과 분리. -->
- "~4 bytes per token"은 경험적 평균. 영어 단어 평균 ~1.3 tokens, 한국어/중국어는 더 많을 수 있음 (추정, 소스 없음 ⚠️).
- BPE의 "가역성"은 생성된 텍스트를 다시 원문으로 복원 가능함을 보장 — 정보 손실 없음.
- regex 기반 사전 분할은 단어 경계를 넘나드는 토큰 병합을 방지하는 역할을 할 것으로 추정 (⚠️ 추측).

---

## Open Questions
- 한국어 텍스트에서의 평균 bytes-per-token은?
- GPT-4o와 Claude의 tokenizer 차이는? (어휘 크기, 분할 방식)
- LangChain의 `get_num_tokens` 메서드는 tiktoken을 내부에서 쓰는가?

---

## Used By
- [[Token]]
