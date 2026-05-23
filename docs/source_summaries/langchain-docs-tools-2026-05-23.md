---
type: source_summary
source_id: langchain-docs-tools-2026-05-23
framework:
  - LangChain
status: verified
confidence: high
retrieved_at: "2026-05-23"
url: "https://docs.langchain.com/oss/python/langchain/tools"
notes: "LCEL 전용 페이지는 새 docs에 없음. Tools 페이지가 @tool 패턴을 커버."
---

# Source Summary: LangChain Tools

## Key Facts

### 도구(Tool)의 정의

도구는 에이전트가 외부 세계와 상호작용할 수 있게 해주는 함수로:
- 실시간 데이터 가져오기
- 코드 실행
- 외부 DB 쿼리
- 세계에 대한 행동 실행

모델은 대화 문맥을 바탕으로 **언제** 도구를 호출하고 **어떤 인자**를 전달할지 결정한다.

### @tool 데코레이터

가장 간단한 도구 생성 방법. **함수의 docstring이 도구의 description이 된다.**

```python
from langchain.tools import tool

@tool
def search_database(query: str, limit: int = 10) -> str:
    """Search the customer database for records matching the query.

    Args:
        query: Search terms to look for
        limit: Maximum number of results to return
    """
    return f"Found {limit} results for '{query}'"
```

**필수 규칙:**
- **타입 힌트 필수** — 도구의 입력 스키마를 정의한다
- **Docstring이 모델에게 제공되는 설명** — informative하고 concise해야 함

### 도구 이름/설명 커스터마이징

```python
@tool("web_search")  # 커스텀 이름
def search(query: str) -> str: ...

@tool("calculator", description="Performs arithmetic calculations.")
def calc(expression: str) -> str: ...
```

### 예약된 파라미터 이름

| 파라미터 | 목적 |
|---------|------|
| `config` | RunnableConfig 전달용 예약 |
| `runtime` | ToolRuntime 접근용 예약 |

### ToolRuntime — 도구 내 컨텍스트 접근

| 컴포넌트 | 설명 | 사용 사례 |
|---------|------|---------|
| **State** | 단기 메모리 — 현재 대화의 가변 데이터 | 대화 이력 접근 |
| **Context** | 호출 시 전달되는 불변 설정 | 사용자 ID 기반 개인화 |
| **Store** | 장기 메모리 — 대화 간 영속 | 사용자 선호도 저장 |
| **Stream Writer** | 실행 중 실시간 업데이트 발행 | 진행 상황 표시 |
| **Execution Info** | Thread ID, run ID, attempt 번호 | 스레드/런 ID 접근 |
| **Server Info** | LangGraph Server 실행 시 메타데이터 | assistant/graph ID 접근 |

**State 접근 예시:**
```python
@tool
def get_last_user_message(runtime: ToolRuntime) -> str:
    """Get the most recent message from the user."""
    messages = runtime.state["messages"]
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message.content
    return "No user messages found"
```

**Store 접근 예시:**
```python
@tool
def save_user_info(user_id: str, user_info: dict, runtime: ToolRuntime) -> str:
    """Save user info."""
    runtime.store.put(("users",), user_id, user_info)
    return "Successfully saved user info."
```

### 도구 반환값 3가지

| 반환 타입 | 용도 |
|---------|------|
| `string` | 인간 가독 평문 결과 → ToolMessage로 변환 |
| `object` | 모델이 파싱할 구조화 데이터 → 직렬화 후 전달 |
| `Command` | 상태 쓰기 필요 시 사용 |

**Command 반환 예시 (상태 업데이트):**
```python
from langgraph.types import Command

@tool
def set_language(language: str, runtime: ToolRuntime) -> Command:
    """Set the preferred response language."""
    return Command(
        update={
            "preferred_language": language,
            "messages": [
                ToolMessage(
                    content=f"Language set to {language}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
```

### 도구 실행 흐름

LangChain에서 도구는 `create_agent`를 통해 에이전트에 등록. LangGraph 워크플로우에서는 `ToolNode`가 실행 처리.

### 에러 핸들링

에이전트 미들웨어를 통해 설정: 실패한 tool call 재시도 또는 커스텀 에러 메시지 반환.

### LCEL 상태 (중요)

> ⚠️ 2026년 기준 새 LangChain docs에 LCEL/Runnable 전용 페이지가 없음.
> 새 docs는 `create_agent` + `AgentMiddleware` + `ToolRuntime` 패턴 중심으로 재편됨.
> `RunnableLambda`, `RunnableParallel`, `|` 연산자는 구버전 docs에만 존재.

## Interpretation

- docstring이 도구 설명이 된다는 점은 모델이 도구를 올바르게 선택하는 데 직결됨 — 명확한 docstring이 사실상 프롬프트 엔지니어링이다.
- `ToolRuntime`은 도구가 단순 함수가 아니라 에이전트 상태의 일부임을 의미 — state 읽기/쓰기, store 영속화까지 도구 안에서 가능하다.
- LCEL → `create_agent` 전환은 LangChain의 큰 패러다임 변화임 — 학습 자료 선택 시 버전 확인 필요.

## Open Questions

- `create_agent`의 내부 구현은 어떻게 동작하는가?
- `AgentMiddleware`로 에러 핸들링을 구성하는 방법은?
- LangGraph `ToolNode`와 `create_agent` 도구 실행의 차이는?
- LCEL `RunnableLambda` / `RunnableParallel`은 완전히 deprecated인가, 아니면 여전히 지원되는가?

## Related Wiki Pages

- [[LangChain]]
- [[Tool Calling]]
- [[LangGraph]]
- [[Memory]]

## Sources

- `langchain-docs-tools-2026-05-23`
