---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - langchain-docs-tools-2026-05-23
  - langchain-docs-messages-2026-05-23
---

# Tool Calling

## 요약

Tool Calling은 추론 중 LLM이 외부 함수(도구)를 선택하고 호출하는 메커니즘이다. LLM은 구조화된 도구 호출 요청을 출력하고, 런타임은 해당 도구를 실행한 뒤 결과를 `ToolMessage`로 반환한다.

## 중요한 이유

Tool Calling은 LLM agent가 외부 시스템과 상호작용하는 기본 방식이다. LLM의 지식 범위를 넘어 실시간 데이터 조회, 코드 실행, DB 쿼리, 세계에 대한 행동이 가능해진다.

---

## LangChain에서의 Tool Calling
*Source: `langchain-docs-tools-2026-05-23`*

### @tool 데코레이터

가장 간단한 도구 생성 방법:

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

**핵심 규칙:**
- **타입 힌트 필수** — 도구의 JSON 입력 스키마를 자동 생성
- **Docstring = 모델이 읽는 설명** — 명확한 docstring이 모델의 도구 선택 근거가 됨

### 도구 이름/설명 커스터마이징

```python
@tool("web_search")  # 커스텀 이름
def search(query: str) -> str: ...

@tool("calculator", description="Performs arithmetic calculations.")
def calc(expression: str) -> str: ...
```

### ToolRuntime — 도구 내 컨텍스트 접근

| 컴포넌트 | 설명 |
|---------|------|
| `runtime.state` | 현재 대화 단기 메모리 (가변) |
| `runtime.context` | 호출 시 전달된 불변 설정 |
| `runtime.store` | 대화 간 영속적 장기 메모리 |
| `runtime.stream_writer` | 실시간 업데이트 발행 |
| `runtime.execution_info` | Thread ID, run ID |
| `runtime.tool_call_id` | ToolMessage 생성 시 필요한 call ID |

### 도구 반환값 3가지

| 반환 타입 | 동작 |
|---------|------|
| `string` | ToolMessage로 자동 변환 |
| `object` | 직렬화 후 모델에 전달 |
| `Command` | 상태 업데이트 + 다음 노드 라우팅 |

**Command 반환 예시:**
```python
from langgraph.types import Command
from langchain.messages import ToolMessage

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

### 예약 파라미터

| 파라미터 | 목적 |
|---------|------|
| `config` | RunnableConfig 전달 |
| `runtime` | ToolRuntime 접근 |

---

## Tool Call 흐름 (메시지 관점)
*Source: `langchain-docs-messages-2026-05-23`*

```
1. HumanMessage("사용자 질문")
        ↓
2. AIMessage with tool_calls=[{"name": ..., "args": ..., "id": "call_123"}]
        ↓
3. Tool 실행
        ↓
4. ToolMessage(content=결과, tool_call_id="call_123")  ← id 반드시 매칭
        ↓
5. 모델 재호출 → 최종 AIMessage
```

`ToolMessage.tool_call_id`는 반드시 `AIMessage.tool_calls[i]['id']`와 일치해야 한다.

---

## LangGraph에서의 Tool Calling

- 도구는 `StateGraph` 안의 노드로 정의하거나 `ToolNode`를 사용
- `ToolNode`는 `langgraph.prebuilt`에서 제공
- `Command` 반환으로 상태 업데이트와 라우팅을 동시 처리 가능

*Source: 소스 코드 확인 필요*

---

## Deep Agents에서의 Tool Calling

- 추후 작성 — 도구 레지스트리와 도구 위임 메커니즘 확인 필요
- *소스 필요*

---

## 핵심 개념

- **도구 정의** — 이름, 설명, 입력 스키마 (타입 힌트에서 자동 생성)
- **도구 선택** — 모델이 docstring을 읽고 언제/어떤 도구를 쓸지 결정
- **도구 실행** — 런타임이 함수 호출
- **도구 결과** — ToolMessage로 반환, tool_call_id로 연결

## 미해결 질문

- 각 프레임워크는 병렬 도구 호출을 내부적으로 어떻게 처리하는가?
- 도구가 예외를 발생시키면 어떻게 되는가? `AgentMiddleware` 에러 처리는?
- LangGraph `ToolNode`와 `create_agent` 도구 실행의 차이는?
- LCEL `.bind_tools()` 방식과 `create_agent([tool])` 방식의 차이는?

## 관련 페이지

- [[LangChain]]
- [[LangGraph]]
- [[Deep Agents]]
- [[StateGraph]]
- [[Subagents]]

## 소스

- `langchain-docs-tools-2026-05-23`
- `langchain-docs-messages-2026-05-23`
