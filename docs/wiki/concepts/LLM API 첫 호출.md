---
type: concept
framework:
  - LangChain
  - Anthropic
  - OpenAI
  - Ollama
status: draft
confidence: high
last_reviewed: 2026-05-30
sources:
  - langchain-docs-models-2026-05-30
  - anthropic-api-quickstart-2026-05-30
  - openai-sdk-python-quickstart-2026-05-30
  - ollama-python-quickstart-2026-05-30
---

# LLM API 첫 호출

## Summary

LLM을 호출하는 방법은 크게 두 가지다. (1) **raw SDK** — provider가 제공하는 Python 라이브러리로 직접 호출. (2) **LangChain `init_chat_model`** — provider와 무관한 통일 인터페이스로 호출. 책 1.2에서는 세 provider(OpenAI, Anthropic, 로컬 Ollama)를 각각 연결해보고, 이후 LangChain이 이 차이를 어떻게 숨겨주는지 확인한다.

## Why It Matters

- 어떤 에이전트 프레임워크를 쓰든 LLM 호출이 기본이다. 각 provider의 인터페이스 차이를 알면 LangChain 추상화의 가치를 이해할 수 있다.
- API 키 설정, 클라이언트 초기화, 메시지 구조는 모든 provider가 비슷하나 반환값 접근 경로가 다르다 — 이 차이가 vendor lock-in의 실체다.

## Key Concepts

- [[Token]] — API 호출 비용과 응답 길이의 기본 단위
- [[Context Window]] — 입력 메시지 합계가 이 한계를 넘으면 오류
- [[Sampling]] — temperature, top_p, top_k로 응답 다양성 제어
- [[Chat Models]] — LangChain이 이 세 패턴을 통일하는 추상화

---

## Verified Facts

### 1. Anthropic Python SDK
*Source: `anthropic-api-quickstart-2026-05-30`*

**설치·인증:**
```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

**첫 호출:**
```python
import os
from anthropic import Anthropic

client = Anthropic()  # ANTHROPIC_API_KEY 자동 감지

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}],
)
print(message.content)
```

- `max_tokens` 필수 파라미터.
- 반환값: `message.content`

---

### 2. OpenAI Python SDK
*Source: `openai-sdk-python-quickstart-2026-05-30`*

**설치·인증:**
```bash
pip install openai
export OPENAI_API_KEY="sk-..."
```

**첫 호출:**
```python
from openai import OpenAI

client = OpenAI()  # OPENAI_API_KEY 자동 감지

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)
print(completion.choices[0].message.content)
```

- 반환값: `completion.choices[0].message.content` (Anthropic과 다름)

---

### 3. Ollama — 로컬 모델
*Source: `ollama-python-quickstart-2026-05-30`*

**전제 조건:** Ollama 앱이 실행 중이어야 하며, 모델을 먼저 pull 해야 함.

**설치·모델 준비:**
```bash
# Ollama 앱 설치 후
ollama pull llama3.2    # 모델 다운로드

pip install ollama
```

**첫 호출:**
```python
from ollama import chat

response = chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': 'Why is the sky blue?'}],
)
print(response.message.content)
```

- API 키 불필요 — 완전 로컬 실행.
- 반환값: `response.message.content`

---

### 4. LangChain `init_chat_model` — 통일 인터페이스
*Source: `langchain-docs-models-2026-05-30`*

세 provider 모두 **동일한 코드**로 호출:

```python
from langchain.chat_models import init_chat_model

# Anthropic
model = init_chat_model("anthropic:claude-opus-4-6")

# OpenAI
model = init_chat_model("openai:gpt-4o")

# 로컬 (Ollama — langchain_ollama 패키지 필요) ⚠️ Needs Source
# model = init_chat_model("ollama:llama3.2")

response = model.invoke("Hello!")
print(response.content)  # 어떤 provider든 동일
```

- provider를 바꿔도 `response.content`로 통일.
- 새 모델 이름은 LangChain 업데이트 없이 즉시 동작 (provider 패키지가 이름을 API에 그대로 전달). **검증됨**

---

## 세 패턴 비교

| 항목 | Anthropic | OpenAI | Ollama (raw) |
|------|-----------|--------|--------------|
| 설치 | `pip install anthropic` | `pip install openai` | `pip install ollama` |
| 인증 | `ANTHROPIC_API_KEY` | `OPENAI_API_KEY` | 불필요 (로컬) |
| 클라이언트 | `Anthropic()` | `OpenAI()` | 함수 직접 호출 |
| 호출 메서드 | `client.messages.create()` | `client.chat.completions.create()` | `chat()` |
| 결과 접근 | `message.content` | `completion.choices[0].message.content` | `response.message.content` |
| Python 요구 | 3.9+ | 3.9+ | - |

**LangChain `init_chat_model`은 이 차이를 모두 `response.content`로 통일한다.**

---

## Interpretation
- raw SDK 직접 호출과 LangChain 추상화를 모두 알면, "LangChain이 왜 필요한가"를 코드로 설명할 수 있다.
- 작은 스크립트라면 raw SDK로 충분하다. provider를 바꿀 가능성이 있거나 에이전트·스트리밍·미들웨어가 필요하면 LangChain이 유리하다.

---

## Source Code References
- `langchain-ai/langchain` — `init_chat_model` provider 라우팅 (미확인 ⚠️)
- `anthropics/anthropic-sdk-python` — `client.messages.create()` 구현
- `openai/openai-python` — `client.chat.completions.create()` 구현

## Tests
- TBD

## Related Pages
- [[Chat Models]]
- [[Token]]
- [[Context Window]]
- [[Sampling]]

## Open Questions
- `init_chat_model("ollama:llama3.2")` 패턴이 실제로 동작하는가? (`langchain-ollama` 패키지 확인 필요)
- Anthropic `message.content`의 정확한 타입은? (list of ContentBlock인지 str인지)
- OpenAI `client.responses.create()`와 `client.chat.completions.create()`의 차이는?
- `.env` 파일을 통한 환경 변수 설정 방법(python-dotenv) — 별도 소스 필요

## Sources
- `langchain-docs-models-2026-05-30`
- `anthropic-api-quickstart-2026-05-30`
- `openai-sdk-python-quickstart-2026-05-30`
- `ollama-python-quickstart-2026-05-30`
