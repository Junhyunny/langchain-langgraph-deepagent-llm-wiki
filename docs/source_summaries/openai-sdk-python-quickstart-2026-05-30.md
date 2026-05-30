---
type: source_summary
source_id: openai-sdk-python-quickstart-2026-05-30
framework: OpenAI
retrieved_at: 2026-05-30
status: draft
confidence: high
---

# Source Summary: OpenAI Python SDK — Quickstart

## Source Info
- **Source ID:** `openai-sdk-python-quickstart-2026-05-30`
- **Type:** official_docs
- **Repo:** `https://github.com/openai/openai-python`
- **File:** `README.md`
- **Commit:** UNKNOWN (main branch, 2026-05-30 기준)

---

## Key Facts

### 설치
- `pip install openai`
- Python 3.9+ 필요.

### 인증
- `OPENAI_API_KEY` 환경 변수 설정.
- python-dotenv로 `.env` 파일에 저장 가능.
- API 키 발급: https://platform.openai.com/settings/organization/api-keys

### 첫 호출 패턴 (Chat Completions)

```python
from openai import OpenAI

client = OpenAI()  # OPENAI_API_KEY 환경 변수 자동 감지

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "developer", "content": "Talk like a pirate."},
        {"role": "user", "content": "How do I check if a Python object is an instance of a class?"},
    ],
)
print(completion.choices[0].message.content)
```

- 진입점: `OpenAI()` 클라이언트 생성 → `client.chat.completions.create()` 호출.
- 반환값: `completion.choices[0].message.content` 로 결과 접근.

### Streaming

```python
stream = client.responses.create(
    model="gpt-4o",
    input="...",
    stream=True,
)
for event in stream:
    print(event)
```

### 주요 특성
- 동기·비동기 클라이언트 모두 지원.
- 포괄적인 타입 정의 제공.

---

## Important Terms
- [[Chat Models]] — LangChain이 이 패턴을 `init_chat_model`로 추상화
- [[Token]] — `messages` 입력 토큰 + 출력 토큰이 비용에 반영
- [[Event Streaming]] — `stream=True`로 스트리밍 활성화

---

## Interpretation
- LangChain 없이 OpenAI API를 직접 쓰는 가장 최소 패턴.
- Anthropic SDK와 구조가 유사 (`client` 초기화 → `create()` 호출)하나 반환값 접근 경로가 다름 (`choices[0].message.content` vs `message.content`).
- LangChain의 `init_chat_model("openai:gpt-4o")` + `invoke()`는 이 차이를 통일된 인터페이스로 숨겨준다.

---

## Open Questions
- `client.responses.create()`와 `client.chat.completions.create()`의 차이는? (Responses API가 신규 API인지 확인 필요)
- `role: "developer"`는 기존 `"system"` role과 다른가?

---

## Used By
- [[LLM API 첫 호출]]
