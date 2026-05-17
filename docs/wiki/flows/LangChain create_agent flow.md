---
type: flow
framework: LangChain
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangChain create_agent flow

## 요약

이 페이지는 `create_react_agent()`에서 시작하여 LangChain agent를 생성하고 실행하는 흐름을 추적한다.

*상태: 초안 스텁이다. 아직 소스 코드를 읽지 않았다. 아래 내용은 모두 가설이다.*

## 진입점

```python
from langchain.agents import create_react_agent, AgentExecutor
agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "..."})
```

## 호출 경로(가설 — 미검증)

1. `create_react_agent(llm, tools, prompt)`
   - 도구를 LLM에 바인딩한다
   - agent runnable을 구성한다
2. `AgentExecutor.invoke(input)`
   - 입력을 포맷한다
   - agent 루프에 진입한다
3. agent 루프:
   - 현재 메시지로 LLM을 호출한다
   - LLM 출력에서 도구 호출을 파싱한다
   - 도구를 실행한다
   - 결과를 메시지 히스토리에 추가한다
   - 더 이상 도구 호출이 없거나 최대 반복 횟수에 도달할 때까지 반복한다
4. 최종 출력을 반환한다

## 읽어야 할 파일

- 추후 작성: `langchain/agents/react/base.py` 또는 유사 파일
- 추후 작성: `langchain/agents/agent.py` (`AgentExecutor`)
- 추후 작성: `langchain_core/runnables/`

## 찾은 테스트

- 추후 작성

## 다이어그램

```
invoke(input)
    │
    ▼
AgentExecutor
    │
    ▼
format messages
    │
    ▼
LLM call
    │
    ├── no tool calls → return output
    │
    └── tool calls
            │
            ▼
        execute tools
            │
            ▼
        append ToolMessage(s)
            │
            ▼
        LLM call (loop)
```

## 미해결 질문

- 도구 호출 파싱 로직은 정확히 어디에 있는가?
- `AgentExecutor`는 최대 반복 횟수를 어떻게 처리하는가?
- 메시지 히스토리는 어디에 누적되는가?

## 관련 페이지

- [[LangChain]]
- [[LangChain Code Map]]
- [[Tool Calling]]
- [[LangChain vs LangGraph vs Deep Agents]]

## 소스

*아직 없음.*
