---
type: source_summary
source_id: langchain-docs-models-2026-05-30
framework: LangChain
retrieved_at: 2026-05-30
status: draft
confidence: high
---

# Source Summary: LangChain — Models

## Source Info
- **Source ID:** `langchain-docs-models-2026-05-30`
- **Type:** official_docs
- **URL:** https://docs.langchain.com/oss/python/langchain/models
- **Retrieved At:** 2026-05-30
- **Version / Commit:** `langchain-ai/docs` `src/oss/langchain/models.mdx` @ `main` (commit UNKNOWN)

---

## Key Facts
<!-- 원문에 있는 내용만. 추론 금지. -->
- LLM은 텍스트를 해석·생성하는 AI 도구이며, 많은 모델이 tool calling / structured output / multimodality / reasoning을 추가로 지원한다.
- 모델은 에이전트의 "reasoning engine"으로, 어떤 도구를 호출할지·결과를 어떻게 해석할지·언제 최종 답을 낼지 결정한다.
- 모델을 쓰는 방식은 두 가지다: (1) 에이전트 생성 시 모델 지정, (2) standalone 직접 호출(생성·분류·추출 등). 같은 인터페이스가 두 맥락 모두에서 동작한다.
- standalone 시작은 `init_chat_model`로 provider의 chat model을 초기화한다. 예: `model.invoke("Why do parrots talk?")`.
- provider/model은 `"{model_provider}:{model}"` 형식 한 인자로 함께 지정 가능하다 (예: `"openai:o1"`).
- 새 모델 이름은 LangChain 업데이트 없이 즉시 동작한다 — provider 패키지가 모델 이름을 provider API에 그대로 전달하기 때문.
- **표준 파라미터(provider마다 지원 범위 다름):**
  - `model` (required): 모델 이름/식별자.
  - `api_key`: provider 인증 키. 보통 환경 변수로 설정.
  - `temperature` (number): 출력의 randomness 제어. 높을수록 창의적, 낮을수록 결정론적.
  - `max_tokens` (number): 응답의 총 token 수 제한 → 출력 길이 제어.
  - `timeout` (number): 응답 대기 최대 시간(초).
  - `max_retries` (number, default `6`): 실패 시 재전송 시도 최대 횟수.
- 원문 정의(tooltip): **token**은 "모델이 읽고 생성하는 기본 단위. provider마다 정의가 다를 수 있으나 일반적으로 단어 전체 또는 일부를 나타낸다."
- 파라미터는 `init_chat_model`에 inline `**kwargs`로 전달한다 (예: `temperature=0.7, timeout=30, max_tokens=1000, max_retries=6`).
- **Connection resilience:** chat model은 실패한 API 요청을 exponential backoff로 자동 재시도한다. 기본 **6회**, 대상은 네트워크 오류·rate limit(429)·서버 오류(5xx). client 오류(401, 404)는 재시도하지 않는다.
- **세 가지 주요 invocation 메서드:** `invoke` (전체 응답 생성 후 메시지 반환), `stream` (생성되는 대로 실시간 스트리밍), `batch` (여러 요청을 배치로 효율 처리).
- **Model profiles (`langchain>=1.1`):** `model.profile`이 지원 기능 dict를 노출한다. 예 필드: `max_input_tokens`(예 400000), `image_inputs`, `reasoning_output`, `tool_calling`.
- model profile 데이터는 대부분 오픈소스 [models.dev](https://github.com/sst/models.dev) 프로젝트에서 가져오며 LangChain용 필드로 보강된다. `profile`은 일반 dict로 직접 덮어쓰거나 인스턴스화 시 `profile=...`로 지정 가능.
- model profile 활용 예: SummarizationMiddleware가 context window 크기로 요약 트리거, `create_agent`의 structured output 전략 자동 추론, modality/`max_input_tokens` 기반 입력 게이팅.
- **Local models:** LangChain은 로컬 하드웨어 실행을 지원한다(데이터 프라이버시·커스텀 모델·비용 회피). [Ollama]가 chat/embedding 모델을 로컬 실행하는 가장 쉬운 방법 중 하나.
- **Prompt caching:** 많은 provider가 동일 token 반복 처리 시 latency·비용 절감을 위해 implicit(자동 절감, OpenAI/Gemini) 또는 explicit(수동 캐시 지점 지정, `ChatOpenAI`의 `prompt_cache_key`, Anthropic `AnthropicPromptCachingMiddleware` 등) 캐싱을 제공한다.
- chat model 외에도 LangChain은 embedding model, vector store 등 인접 기술을 지원한다.

---

## Important Terms
- [[Chat Models]] — provider별 LLM을 표준 인터페이스로 감싼 LangChain 추상화.
- [[Token]] — 모델이 읽고 생성하는 기본 단위 (단어 전체/일부).
- [[Context Window]] — model profile의 `max_input_tokens`로 노출되는 입력 토큰 한계.
- [[Tool Calling]] — 모델이 외부 도구를 호출하는 기능.
- [[init_chat_model]] — provider chat model을 초기화하는 진입 함수.

---

## Interpretation
<!-- 내가 이해한 의미. 원문과 분리. -->
- 책 1.1(토큰·컨텍스트 윈도우·온도·샘플링) 중 **온도·max_tokens·token 정의·컨텍스트 윈도우(`max_input_tokens`)**는 이 문서로 근거가 충분하다. 다만 **sampling(top_p/top_k)의 의미**는 이 문서가 "standard ones include" 목록에만 넣고 상세히 설명하지 않으므로 별도 근거가 필요하다.
- 책 1.2(첫 API 호출)는 `init_chat_model` + `invoke` 예제 + local models(Ollama)로 LangChain 관점에서 커버된다. OpenAI/Anthropic raw SDK 직접 호출은 LangChain 문서 범위 밖이다.
- "모델 = reasoning engine" 프레이밍은 이후 [[Agent Runtime]], [[Reasoning and Planning]] 페이지와 자연스럽게 연결된다.

---

## Implications for My AI Agent Project
- standalone과 agent에서 동일한 모델 인터페이스가 쓰이므로, 작은 `invoke` 예제로 시작해 점진적으로 에이전트로 확장하는 학습 경로가 타당하다.
- `max_retries`/`timeout`은 [[RetryMiddleware]], checkpointer와 함께 장기 실행 에이전트의 복원력 설계로 이어진다.
- model profile의 `max_input_tokens`는 [[SummarizationMiddleware]]의 컨텍스트 윈도우 트리거와 직접 연결된다.

---

## Open Questions
- top_p / top_k 같은 sampling 파라미터의 정확한 의미와 temperature와의 상호작용은? (Anthropic/OpenAI API 레퍼런스 필요)
- token이 실제로 어떻게 분할되는가(tokenizer/BPE)? 이 문서는 정의만 제시. — 별도 소스 필요
- `init_chat_model`의 내부 구현(provider 패키지 라우팅, lazy import)은? — 소스 코드 확인 필요

---

## Used By
- [[Chat Models]]

---

## Notes
- docs.langchain.com이 이 환경에서 Cloudflare로 차단되어 `langchain-ai/docs` 저장소의 `.mdx` 소스로 수집함. 렌더 페이지와 동일 내용.
- `.mdx`는 Python/JS 코드 그룹을 함께 포함. 위 Key Facts는 Python 기준으로 정리.
