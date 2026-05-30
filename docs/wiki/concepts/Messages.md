---
type: concept
framework:
  - LangChain
status: draft
confidence: high
last_reviewed: 2026-05-30
sources:
  - langchain-docs-messages-2026-05-30
---

# Messages

## 요약

Message는 LangChain에서 모델 **context의 기본 단위**다. 모델의 입력과 출력을 모두 표현하며, 대화 상태를 담는다. `SystemMessage` / `HumanMessage` / `AIMessage` / `ToolMessage` 네 가지 타입이 있고, provider와 무관하게 동일하게 동작하는 표준 타입이다.

## 중요한 이유

LLM에게 "프롬프트를 준다"는 것은 결국 **메시지 리스트를 구성한다**는 의미다. System(지시) / User(입력) / Assistant(응답)의 역할 구조를 이해하는 것이 프롬프트 엔지니어링과 [[Context Engineering]]의 출발점이다. 컨텍스트 관리도 결국 message 리스트 관리다.
*Source: `langchain-docs-messages-2026-05-30`*

## Key Concepts
- [[Chat Models]] — Message를 입력받아 Message를 출력
- [[Tool Calling]] — `AIMessage.tool_calls` → `ToolMessage` 흐름
- [[Context Engineering]] — 메시지 리스트 구성 전략
- [[Memory]] — 대화 히스토리(메시지) 누적·관리

---

## Verified Facts
*Source: `langchain-docs-messages-2026-05-30` (official_docs, 공식 문서 기준)*

### Message의 구성 요소
Message 객체는 세 가지를 포함한다.
- **Role** — 메시지 유형 식별 (예: `system`, `user`).
- **Content** — 실제 내용 (text, image, audio, document 등).
- **Metadata** — 선택 필드: response 정보, message ID, token usage 등.

### 입력을 주는 세 가지 형식
1. **Text prompt** (문자열) — 단일·독립 요청, 히스토리 불필요 시. 문자열은 단일 `HumanMessage`의 shortcut.
   ```python
   response = model.invoke("Write a haiku about spring")
   ```
2. **Message prompt** (메시지 객체 리스트) — multi-turn 대화, multimodal, system 지시 포함 시.
   ```python
   from langchain.messages import SystemMessage, HumanMessage, AIMessage
   messages = [
       SystemMessage("You are a poetry expert"),
       HumanMessage("Write a haiku about spring"),
       AIMessage("Cherry blossoms bloom..."),
   ]
   response = model.invoke(messages)
   ```
3. **Dictionary format** (OpenAI chat completions 호환) — raw API를 먼저 배운 독자에게 다리 역할.
   ```python
   messages = [
       {"role": "system", "content": "You are a poetry expert"},
       {"role": "user", "content": "Write a haiku about spring"},
       {"role": "assistant", "content": "Cherry blossoms bloom..."},
   ]
   ```

### 네 가지 Message 타입 (책 1.3: System/User/Assistant 구조)
| 타입 | Role | 역할 |
|------|------|------|
| `SystemMessage` | `system` | 모델 동작을 priming하는 초기 지시. tone·역할·응답 가이드라인 수립 |
| `HumanMessage` | `user` | 사용자 입력. text·image·audio·file 등 multimodal 가능 |
| `AIMessage` | (assistant) | 모델 호출의 출력. text content + tool calls + provider metadata |
| `ToolMessage` | (tool) | tool call의 출력 |

> LangChain의 `SystemMessage`/`HumanMessage`/`AIMessage`는 OpenAI의 `system`/`user`/`assistant` role에 각각 대응한다 (dictionary format에서 직접 확인됨).

```python
system_msg = SystemMessage("You are a helpful coding assistant.")
messages = [system_msg, HumanMessage("How do I create a REST API?")]
response = model.invoke(messages)
```

### 타입별 추가 사실
- **HumanMessage**: 선택 metadata `name`(사용자 식별), `id`(추적용). `name` 동작은 provider마다 다르다 — 일부는 식별에 쓰고 일부는 무시.
- **AIMessage**: 모델이 반환하지만, 대화 히스토리에 **수동으로 만들어 삽입**할 수도 있다 (provider가 메시지 유형을 다르게 가중/맥락화하기 때문). few-shot/대화 시뮬레이션에 유용.
- **ToolMessage**: tool call의 결과를 표현 → [[Tool Calling]]의 출력 계약.
- **Content**는 string, provider-native 형식, 또는 standard content block 리스트로 표현 가능.

---

## Interpretation
- 책 1.3(프롬프트 엔지니어링 기초: System/User/Assistant 메시지 구조)은 이 페이지로 근거가 충분하다.
- dictionary format이 OpenAI 호환이라, raw API → LangChain 객체로 넘어가는 학습 다리로 활용하기 좋다.

---

## Source Code References
- Repo: `langchain-ai/langchain`
- Commit: UNKNOWN
- Files (미확인 — 다음 코드 리딩 대상):
  - `libs/core/langchain_core/messages/` (system.py, human.py, ai.py, tool.py, base.py)

## Tests
- TBD (아직 확인 안 함)

## Related Pages
- [[Chat Models]]
- [[Tool Calling]]
- [[Context Engineering]]
- [[Memory]]
- [[PromptTemplate]]

## Open Questions
- `AIMessage.tool_calls` 정확한 스키마와 ToolMessage의 `tool_call_id` 매칭 방식은? — [[Tool Calling]] 소스 확인 필요
- standard content block의 전체 스펙(멀티모달 블록 타입)은? — 소스 확인 필요
- message metadata의 token usage 필드 구조는? (원문에 TODO로 표시됨)

## Sources
- `langchain-docs-messages-2026-05-30`
