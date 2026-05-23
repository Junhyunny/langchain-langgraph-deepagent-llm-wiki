---
type: source_summary
source_id: langchain-source-dynamic-prompt-2026-05-23
framework:
  - LangChain
status: verified
confidence: high
retrieved_at: "2026-05-23"
url: "https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/types.py"
---

# Source Summary: LangChain @dynamic_prompt Decorator

## Source Info
- **Type:** source_code
- **Module:** `langchain.agents.middleware.types`
- **Import:** `from langchain.agents.middleware import dynamic_prompt`
- **Commit:** UNKNOWN (master branch, 2026-05-23 기준)

---

## Key Facts

### @dynamic_prompt — 정의와 목적

`@dynamic_prompt`는 **AgentMiddleware를 생성하는 데코레이터**다. 모델 호출 전 시스템 프롬프트를 동적으로 교체하는 미들웨어를 만든다.

**함수 서명 (데코레이팅 대상):**
```python
(request: ModelRequest[ContextT]) -> str | SystemMessage
```

**반환 타입 (데코레이터 결과):** `AgentMiddleware` 인스턴스

**⚠️ Possible Conflict with RAG docs:**
RAG 공식 문서 예제는 `(user_query: str) -> list` 서명을 사용했으나,
실제 소스는 `(request: ModelRequest) -> str | SystemMessage`를 요구한다.
두 사용 패턴이 다름 — RAG 문서 예제 확인 필요. Source: `langchain-source-dynamic-prompt-2026-05-23`

---

### 사용법

```python
from langchain.agents.middleware import dynamic_prompt
from langchain.agents.middleware.types import ModelRequest

# 기본 사용
@dynamic_prompt
def my_prompt(request: ModelRequest) -> str:
    user_name = request.runtime.context.get("user_name", "User")
    return f"You are a helpful assistant helping {user_name}."

# 상태 기반 조건 분기
@dynamic_prompt
def context_aware_prompt(request: ModelRequest) -> str:
    msg_count = len(request.state["messages"])
    if msg_count > 10:
        return "You are in a long conversation. Be concise."
    return "You are a helpful assistant."

# agent에 등록
agent = create_agent(model, middleware=[my_prompt])
```

Source: `langchain-source-dynamic-prompt-2026-05-23`

---

### 내부 구현 흐름

1. 데코레이팅된 함수 호출 → `str | SystemMessage` 반환
2. 결과가 `str`이면 `SystemMessage(content=prompt)` 변환
3. `request.override(system_message=...)` 로 불변 복사본 생성
4. `handler(request)` 호출 — 실제 모델 호출로 위임
5. sync/async 모두 지원 (`iscoroutinefunction` 감지)
6. 내부적으로 `type(name, (AgentMiddleware,), {...})()` 로 동적 클래스 생성

---

### ModelRequest 클래스

```python
@dataclass
class ModelRequest(Generic[ContextT]):
    model: BaseChatModel
    messages: list[AnyMessage]       # system message 제외
    system_message: SystemMessage | None
    tool_choice: Any | None
    tools: list[BaseTool | dict]
    response_format: ResponseFormat | None
    state: AgentState[Any]
    runtime: Runtime[ContextT]       # context, store, stream_writer 등 접근
    model_settings: dict[str, Any]

    def override(self, **kwargs) -> ModelRequest:
        """불변 패턴: 새 필드 값으로 복사본 생성."""
```

`request.system_prompt` (deprecated) → `request.system_message` 권장

---

### AgentState

```python
class AgentState(TypedDict, Generic[ResponseT]):
    messages: Required[Annotated[list[AnyMessage], add_messages]]
    jump_to: NotRequired[JumpTo | None]           # EphemeralValue
    structured_response: NotRequired[ResponseT]   # OmitFromInput
```

---

### AgentMiddleware 기반 클래스

hook 메서드 (오버라이드 가능):

| 메서드 | 시점 | 입력 | 반환 |
|--------|------|------|------|
| `before_agent` | agent 실행 전 | state, runtime | dict \| None |
| `after_agent` | agent 실행 후 | state, runtime | dict \| None |
| `before_model` | 모델 호출 전 | state, runtime | dict \| None |
| `after_model` | 모델 호출 후 | state, runtime, response | dict \| None |
| `wrap_model_call` | 모델 호출 래핑 | request, handler | ModelResponse \| AIMessage |
| `wrap_tool_call` | 도구 호출 래핑 | request, handler | ToolMessage \| Command |

`@dynamic_prompt`는 내부적으로 `wrap_model_call` / `awrap_model_call`을 구현한다.

---

### middleware/__init__.py — 사용 가능한 미들웨어

```python
from langchain.agents.middleware import (
    # 핵심 데코레이터
    dynamic_prompt, wrap_model_call, wrap_tool_call,
    before_agent, after_agent, before_model, after_model,
    # 미들웨어 클래스
    SummarizationMiddleware, ContextEditingMiddleware,
    HumanInTheLoopMiddleware, ModelCallLimitMiddleware,
    ModelFallbackMiddleware, ModelRetryMiddleware,
    PIIMiddleware, ShellToolMiddleware,
    TodoListMiddleware, ToolCallLimitMiddleware,
    ToolRetryMiddleware, LLMToolEmulator,
    LLMToolSelectorMiddleware, FilesystemFileSearchMiddleware,
)
```

---

## Interpretation

- `@dynamic_prompt`는 "시스템 프롬프트 동적 교체"에 특화된 미들웨어 shortcut이다. 매 모델 호출마다 실행되어 state/runtime을 보고 시스템 프롬프트를 바꿀 수 있다.
- RAG 문서에서 보여준 `(user_query: str) -> list` 패턴은 실제 API와 다르다. RAG chain 패턴에서의 "dynamic prompt"는 아마도 `@dynamic_prompt` 미들웨어가 아니라 다른 추상화를 의미했을 가능성이 높다.
- `request.override()`를 사용하는 불변 패턴은 미들웨어 체인에서 의도치 않은 부작용을 방지한다.
- `@dynamic_prompt`로 생성된 미들웨어는 `create_agent(model, middleware=[...])` 에서 리스트의 한 원소로 전달한다.

---

## Open Questions

- RAG 문서의 `@dynamic_prompt(user_query: str) -> list` 패턴의 실제 정체는? 다른 데코레이터인가, 문서 오류인가? — Source: `langchain-docs-rag-2026-05-23`
- `wrap_model_call` 데코레이터의 전체 서명과 사용 예제는? — Source: `langchain-source-dynamic-prompt-2026-05-23`
- `before_model` vs `wrap_model_call`의 실질적 차이는? (둘 다 모델 호출 전에 개입 가능한가?)
- `ModelRequest.runtime`의 `Runtime` 클래스 전체 인터페이스는? (`context`, `store`, `stream_writer` 외에 무엇이 있는가?) — Needs Source

---

## Related Wiki Pages

- [[LangChain]]
- [[Agent Harness]]
- [[Context Engineering]]
- [[RAG]]
- [[LangChain Code Map]]

## Sources

- `langchain-source-dynamic-prompt-2026-05-23`
