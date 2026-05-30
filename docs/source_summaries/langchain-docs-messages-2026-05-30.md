---
type: source_summary
source_id: langchain-docs-messages-2026-05-30
framework: LangChain
retrieved_at: 2026-05-30
status: draft
confidence: high
---

# Source Summary: LangChain — Messages

## Source Info
- **Source ID:** `langchain-docs-messages-2026-05-30`
- **Type:** official_docs
- **URL:** https://docs.langchain.com/oss/python/langchain/messages
- **Retrieved At:** 2026-05-30
- **Version / Commit:** `langchain-ai/docs` `src/oss/langchain/messages.mdx` @ `main` (commit UNKNOWN)

---

## Key Facts
<!-- 원문에 있는 내용만. 추론 금지. -->
- Message는 LangChain에서 모델의 "context의 기본 단위"이며, 모델의 입력과 출력을 표현한다. 대화 상태(content + metadata)를 담는다.
- Message 객체는 세 가지를 포함한다:
  - **Role**: 메시지 유형 식별 (예: `system`, `user`).
  - **Content**: 실제 내용 (text, image, audio, document 등).
  - **Metadata**: 선택 필드 — response 정보, message ID, token usage 등.
- LangChain은 모든 provider에서 동작하는 표준 message 타입을 제공해 일관된 동작을 보장한다.
- 기본 사용: message 객체를 만들어 `model.invoke([...])`에 전달. `SystemMessage`, `HumanMessage`, `AIMessage`를 `langchain.messages`에서 import.
- 모델에 입력을 주는 **세 가지 형식:**
  1. **Text prompt** (문자열): 단일·독립 요청, 히스토리 불필요 시. 문자열은 단일 `HumanMessage`의 shortcut.
  2. **Message prompt** (메시지 객체 리스트): multi-turn 대화, multimodal, system 지시 포함 시.
  3. **Dictionary format** (OpenAI chat completions 형식): `{"role": "system"|"user"|"assistant", "content": ...}`.
- **네 가지 message 타입:**
  - **SystemMessage** (`system`): 모델 동작을 priming하는 초기 지시 집합. tone 설정, 역할 정의, 응답 가이드라인 수립에 사용.
  - **HumanMessage** (`user`): 사용자 입력·상호작용. text, image, audio, file 등 multimodal content 포함 가능. 선택 metadata: `name`(사용자 식별), `id`(추적용).
  - **AIMessage**: 모델 호출의 출력. text content, tool calls, provider-specific metadata 포함. 모델이 반환하지만, 대화 히스토리에 수동으로 만들어 삽입할 수도 있다(provider가 메시지 유형을 다르게 가중/맥락화하기 때문).
  - **ToolMessage**: tool call의 출력을 표현.
- `name` 필드 동작은 provider마다 다르다 — 일부는 사용자 식별에 쓰고 일부는 무시한다.
- Message content는 string, provider-native 형식, 또는 standard content block 리스트로 표현 가능하다.

---

## Important Terms
- [[Messages]] — provider 무관 표준 메시지 추상화.
- [[SystemMessage]] — 모델 동작을 priming하는 지시.
- [[HumanMessage]] — 사용자 입력 (`user` role).
- [[AIMessage]] — 모델 출력 (text + tool calls + metadata).
- [[ToolMessage]] — 도구 실행 결과.
- [[Tool Calling]] — AIMessage의 tool_calls와 ToolMessage가 관여하는 흐름.

---

## Interpretation
<!-- 내가 이해한 의미. 원문과 분리. -->
- 책 1.3(프롬프트 엔지니어링 기초: System/User/Assistant 메시지 구조)은 이 문서로 근거가 충분하다. LangChain의 `SystemMessage`/`HumanMessage`/`AIMessage`가 OpenAI의 `system`/`user`/`assistant` role에 각각 대응한다(dictionary format에서 직접 확인됨).
- 세 가지 입력 형식 중 dictionary format은 OpenAI 호환 형식이라, raw API를 먼저 배운 독자에게 LangChain 객체로 넘어가는 다리 역할을 한다.
- AIMessage를 수동으로 만들어 히스토리에 넣는 패턴은 few-shot/대화 시뮬레이션에 쓰이며, 이후 [[Memory]] 페이지와 연결된다.

---

## Implications for My AI Agent Project
- 메시지 = context의 기본 단위라는 프레이밍은 [[Context Engineering]]의 토대다. 컨텍스트 관리는 결국 message 리스트 관리다.
- AIMessage의 tool_calls + ToolMessage 구조는 [[Tool Calling]] 흐름의 입출력 계약을 정의한다.

---

## Open Questions
- AIMessage의 `tool_calls` 필드 정확한 스키마와, ToolMessage가 어떤 `tool_call_id`로 매칭되는가? — [[Tool Calling]] 소스 확인 필요
- standard content block의 전체 스펙(멀티모달 블록 타입)은? — 본 문서 후반부 + 소스 확인 필요
- message metadata의 token usage 필드 구조는? (문서에 TODO로 표시되어 있음)

---

## Used By
- [[Messages]]

---

## Notes
- docs.langchain.com이 이 환경에서 Cloudflare로 차단되어 `langchain-ai/docs` 저장소의 `.mdx` 소스로 수집함.
- `.mdx`는 Python/JS 코드 그룹을 함께 포함. 위 Key Facts는 Python 기준으로 정리.
