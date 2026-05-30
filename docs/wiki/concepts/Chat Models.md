---
type: concept
framework:
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-30
sources:
  - langchain-docs-models-2026-05-30
---

# Chat Models

## 요약

Chat Model은 provider(OpenAI, Anthropic, Google 등)의 LLM을 **하나의 표준 인터페이스**로 감싼 LangChain 추상화다. 메시지 리스트를 입력받아 메시지를 출력하며, `invoke` / `stream` / `batch` 세 가지 방식으로 호출한다. provider를 바꿔도 애플리케이션 로직을 다시 쓸 필요가 없다.

## 중요한 이유

모델은 에이전트의 **reasoning engine**이다 — 어떤 도구를 호출할지, 결과를 어떻게 해석할지, 언제 최종 답을 낼지 결정한다. 모델 선택이 에이전트의 기본 신뢰성·성능을 좌우한다. Chat Model 인터페이스를 이해하면 standalone LLM 호출에서 에이전트까지 같은 추상화로 확장할 수 있다.
*Source: `langchain-docs-models-2026-05-30`*

## Key Concepts
- [[Messages]] — Chat Model의 입력·출력 단위
- [[Token]] — 입력·출력 길이의 기본 단위 (BPE, ~4 bytes/token)
- [[Sampling]] — temperature / top_p / top_k 파라미터로 다음 토큰 선택 방식 제어
- [[Context Window]] — `max_input_tokens`로 측정되는 입력 한계
- [[Tool Calling]] — 모델이 외부 함수를 호출하는 기능
- [[init_chat_model]] — provider chat model 초기화 진입점
- [[Agent Runtime]] — 모델이 reasoning engine으로 동작하는 맥락

---

## Verified Facts
*Source: `langchain-docs-models-2026-05-30` (official_docs, 공식 문서 기준)*

### 두 가지 사용 방식
- **With agents** — 에이전트 생성 시 모델을 동적으로 지정한다.
- **Standalone** — 에이전트 프레임워크 없이 모델을 직접 호출한다(생성·분류·추출 등).
- 같은 인터페이스가 두 맥락 모두에서 동작한다.

### 모델 초기화 & 첫 호출 (책 1.2)
```python
from langchain.chat_models import init_chat_model

model = init_chat_model("claude-sonnet-4-6")
response = model.invoke("Why do parrots talk?")  # AIMessage 반환
```
- provider와 model을 한 인자로 함께 지정 가능: `"{model_provider}:{model}"` (예: `"openai:o1"`).
- 새 모델 이름은 LangChain 업데이트 없이 즉시 동작한다 — provider 패키지가 이름을 provider API에 그대로 전달하기 때문.

### 세 가지 호출 메서드
| 메서드 | 동작 |
|--------|------|
| `invoke` | 전체 응답을 생성한 뒤 메시지로 반환 |
| `stream` | 생성되는 대로 실시간 스트리밍 |
| `batch` | 여러 요청을 배치로 묶어 효율 처리 |

### 표준 파라미터 (책 1.1)
provider마다 지원 범위가 다르지만 표준 파라미터는 다음과 같다.

| 파라미터 | 의미 |
|----------|------|
| `model` (required) | 모델 이름/식별자 |
| `api_key` | provider 인증 키 (보통 환경 변수) |
| `temperature` | 출력의 randomness 제어. 높을수록 창의적, 낮을수록 결정론적 |
| `max_tokens` | 응답의 총 token 수 제한 → 출력 길이 제어 |
| `timeout` | 응답 대기 최대 시간(초) |
| `max_retries` (default `6`) | 실패 시 재전송 시도 최대 횟수 |

> **token (공식 정의):** "모델이 읽고 생성하는 기본 단위. provider마다 정의가 다를 수 있으나 일반적으로 단어 전체 또는 일부를 나타낸다."

```python
model = init_chat_model(
    "claude-sonnet-4-6",
    temperature=0.7,
    timeout=30,
    max_tokens=1000,
    max_retries=6,
)
```

### Connection resilience
- Chat Model은 실패한 요청을 exponential backoff로 **기본 6회** 자동 재시도한다.
- 재시도 대상: 네트워크 오류, rate limit(429), 서버 오류(5xx).
- 재시도 안 함: client 오류(401 unauthorized, 404).
- 장기 실행 에이전트는 `max_retries`를 10~15로 올리고 [[Checkpointing|checkpointer]]를 함께 쓰는 것이 권장된다.

### Model profiles & Context Window
- `langchain>=1.1`부터 `model.profile`이 지원 기능 dict를 노출한다:
```python
model.profile
# {"max_input_tokens": 400000, "image_inputs": True,
#  "reasoning_output": True, "tool_calling": True, ...}
```
- `max_input_tokens`가 곧 모델의 **context window** 크기다.
- profile 데이터는 오픈소스 [models.dev](https://github.com/sst/models.dev)에서 가져와 LangChain용으로 보강된다.
- 활용 예: [[SummarizationMiddleware]]가 context window 크기로 요약을 트리거, `create_agent`의 structured output 전략 자동 추론, modality·`max_input_tokens` 기반 입력 게이팅.

### Local models (책 1.2)
- LangChain은 로컬 하드웨어 실행을 지원한다 — 데이터 프라이버시, 커스텀 모델, 비용 회피 목적.
- **Ollama**가 chat/embedding 모델을 로컬 실행하는 가장 쉬운 방법 중 하나.

### Prompt caching
- 많은 provider가 동일 token 반복 처리 시 latency·비용 절감용 캐싱을 제공한다.
- **Implicit**: 자동 절감 (OpenAI, Gemini).
- **Explicit**: 수동 캐시 지점 지정 (`ChatOpenAI`의 `prompt_cache_key`, Anthropic `AnthropicPromptCachingMiddleware` 등).

---

## Interpretation
- 책 1.1의 **온도·max_tokens·token 정의·컨텍스트 윈도우(`max_input_tokens`)**는 이 페이지로 근거가 충분하다.
- 책 1.2(첫 호출)는 `init_chat_model` + `invoke` + Ollama(local)로 LangChain 관점에서 커버된다. OpenAI/Anthropic **raw SDK** 직접 호출은 LangChain 문서 범위 밖이라 별도 소스가 필요하다.

## Hypotheses
- `init_chat_model`이 `"openai:o1"` 같은 문자열을 받아 provider 패키지를 lazy import하고 라우팅할 것으로 추정. ⚠️
  Status: Needs verification (소스 코드 확인 필요)

---

## Source Code References
- Repo: `langchain-ai/langchain`
- Commit: UNKNOWN
- Files (미확인 — 다음 코드 리딩 대상):
  - `init_chat_model` 구현 (provider 라우팅)
  - `BaseChatModel.invoke / stream / batch`

## Tests
- TBD (아직 확인 안 함)

## Related Pages
- [[Messages]]
- [[Tool Calling]]
- [[SummarizationMiddleware]]
- [[Agent Runtime]]
- [[RetryMiddleware]]

## Open Questions
- top_p / top_k 등 sampling 파라미터의 정확한 의미와 temperature와의 상호작용은? (Anthropic/OpenAI API 레퍼런스 필요)
- token이 실제로 어떻게 분할되는가(tokenizer/BPE)? — 별도 소스 필요
- `init_chat_model` 내부 구현(라우팅, lazy import)은? — 소스 코드 확인 필요

## Sources
- `langchain-docs-models-2026-05-30`
