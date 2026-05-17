---
type: code_map
framework: LangChain
status: draft
confidence: low
last_reviewed: 2026-05-18
sources: []
---

# LangChain Code Map

## 요약

이 페이지는 LangChain 저장소 구조를 매핑한다. 소스 코드를 읽을 때 탐색 가이드로 사용한다.

*상태: 초안 스텁이다. 실제 저장소를 기준으로 한 소스 검증이 필요하다.*

## 저장소

- **저장소:** `https://github.com/langchain-ai/langchain`
- **커밋:** UNKNOWN

## 주요 패키지 / 디렉터리

```
langchain/                    # Main package
langchain_core/               # Core abstractions (Runnable, BaseMessage, etc.)
langchain_community/          # Community integrations
langchain_text_splitters/     # Text splitting utilities
libs/
  langchain/
  langchain_core/
  langchain_community/
```

*소스 필요: 실제 디렉터리 구조를 확인해야 한다.*

## 중요한 진입점

- `langchain_core.runnables` — `Runnable`, `RunnableSequence`, `RunnableLambda`
- `langchain.agents` — `create_react_agent`, `AgentExecutor`
- `langchain_core.messages` — `HumanMessage`, `AIMessage`, `ToolMessage`
- `langchain_core.tools` — `BaseTool`, `@tool`

*소스 필요.*

## 읽어야 할 소스 파일

- 추후 작성: `langchain.agents.create_react_agent`에서 시작 → [[LangChain create_agent flow]]

## 읽어야 할 테스트

- 추후 작성

## 불명확한 영역

- LCEL(파이프 `|`)은 내부적으로 runnable을 어떻게 조합하는가?
- 메시지 타입 디스패치 로직은 어디에 있는가?

## 관련 페이지

- [[LangChain]]
- [[LangChain create_agent flow]]
- [[Tool Calling]]

## 소스

*아직 없음.*
