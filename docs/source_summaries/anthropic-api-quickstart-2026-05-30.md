---
type: source_summary
source_id: anthropic-api-quickstart-2026-05-30
framework: Anthropic
retrieved_at: 2026-05-30
status: draft
confidence: high
---

# Source Summary: Anthropic Python SDK — Quickstart

## Source Info
- **Source ID:** `anthropic-api-quickstart-2026-05-30`
- **Type:** official_docs
- **Repo:** `https://github.com/anthropics/anthropic-sdk-python`
- **File:** `README.md`
- **Commit:** UNKNOWN (main branch, 2026-05-30 기준)

---

## Key Facts

### 설치
- `pip install anthropic`
- Python 3.9+ 필요.

### 인증
- SDK가 `ANTHROPIC_API_KEY` 환경 변수에서 자동으로 API 키를 감지.
- 클라이언트 초기화 시 명시적으로 전달도 가능: `Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))`.

### 첫 호출 패턴

```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

message = client.messages.create(
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}],
    model="claude-opus-4-6",
)
print(message.content)
```

- 진입점: `Anthropic()` 클라이언트 생성 → `client.messages.create()` 호출.
- `messages` 파라미터: role/content 딕셔너리 리스트.
- `max_tokens` 필수 파라미터.
- 반환값: `message.content` 로 결과 접근.

---

## Important Terms
- [[Chat Models]] — LangChain이 이 패턴을 `init_chat_model`로 추상화
- [[Token]] — `max_tokens`가 출력 최대 토큰 수
- [[Sampling]] — `temperature`, `top_p`, `top_k`를 `messages.create()`에 추가 가능

---

## Interpretation
- LangChain 없이 Anthropic API를 직접 쓰는 가장 최소 패턴.
- LangChain의 `init_chat_model("anthropic:claude-...")` + `invoke()`는 이 패턴을 표준 인터페이스로 감싼 것.

---

## Open Questions
- `message.content`의 정확한 타입은? (list of ContentBlock인지 str인지)
- async 버전(`AsyncAnthropic`)의 사용 패턴은?

---

## Used By
- [[LLM API 첫 호출]]
