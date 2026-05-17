---
type: source_summary
source_id: deepagents-docs-overview-2026-05-18
framework: Deep Agents
retrieved_at: 2026-05-18
status: verified
confidence: high
---

# Source Summary: Deep Agents Overview

## Source Info
- **Source ID:** `deepagents-docs-overview-2026-05-18`
- **Type:** official_docs
- **URL:** https://docs.langchain.com/oss/python/deepagents/overview
- **Retrieved At:** 2026-05-18
- **Version / Commit:** UNKNOWN

---

## Key Facts
<!-- 원문에 있는 내용만. 추론 금지. -->
- `deepagents`는 PyPI에서 설치 가능한 standalone 라이브러리다.
- [[LangChain]]의 core building blocks를 기반으로 만들어졌다.
- [[LangGraph]] runtime을 사용해 durable execution, streaming, human-in-the-loop 등의 기능을 제공한다.
- 저장소 주소: `github.com/langchain-ai/deepagents`
- 저장소에는 세 가지 구성요소가 포함된다:
  - **Deep Agents SDK**: 모든 태스크를 처리하는 에이전트 패키지
  - **Deep Agents Code**: Deep Agents SDK 위에서 동작하는 터미널 코딩 에이전트
  - **ACP integration**: Zed 등 코드 에디터용 Agent Client Protocol 커넥터
- 핵심 진입점: `create_deep_agent(model, tools, system_prompt)`
- 설치: `pip install deepagents langchain-openai`
- Deep Agents는 "agent harness"로 정의됨 — 다른 에이전트 프레임워크와 동일한 core tool calling loop이지만, built-in tools와 capabilities가 포함됨.
- 공식 문서에서 LangChain을 "agent의 core building blocks를 제공하는 프레임워크"로 명시함.

## Use Cases (원문 기준)
Deep Agents SDK를 사용해야 하는 경우:
- 복잡한 multi-step 태스크 처리 (planning and decomposition 필요)
- 대규모 context 관리 (filesystem tools, summarization)
- filesystem backend 교체 (in-memory / local disk / durable store / sandbox / custom)
- shell 명령어 실행 (`execute` tool, sandbox backend)
- interpreter 코드 실행 (subagent orchestration, structured data transformation)
- specialized subagent에 작업 위임 (context isolation)
- 대화/스레드 간 memory 지속
- 파일 접근 권한 제어 (declarative permission rules)
- human-in-the-loop workflows (sensitive operations에 대한 human approval)
- 모든 모델 사용 가능 (provider agnostic)

## 언제 Deep Agents 대신 다른 것을 쓸까 (원문 기준)
- 더 단순한 에이전트를 만들 때 → LangChain의 `create_agent` 또는 custom [[LangGraph]] workflow

---

## Important Terms
- **agent harness** — core tool calling loop + built-in tools/capabilities의 묶음
- **Deep Agents SDK** — 에이전트 빌딩 패키지
- **Deep Agents Code** — 터미널 코딩 에이전트
- **ACP (Agent Client Protocol)** — 코드 에디터 통합용 커넥터
- **create_deep_agent** — 주 진입점 함수
- **filesystem tools** — context 관리를 위한 내장 파일 시스템 도구
- **subagent** — context isolation을 위해 위임되는 전문 에이전트

---

## Interpretation
<!-- 내가 이해한 의미. 원문과 분리. -->
- Deep Agents는 LangGraph + LangChain의 기능을 직접 조합하는 대신, 공통 패턴을 미리 구성해 둔 "high-level harness"로 이해할 수 있다.
- LangGraph runtime을 직접 쓰지 않아도 durable execution이나 human-in-the-loop를 쉽게 쓸 수 있게 해주는 래퍼 역할이다.
- 복잡한 에이전트를 빠르게 시작할 때 유리하고, 세밀한 그래프 제어가 필요할 때는 LangGraph를 직접 쓰는 것이 더 적합할 수 있다.

---

## Implications for My AI Agent Project
- long-running / multi-step 작업이 있다면 Deep Agents SDK가 가장 빠른 시작점이다.
- subagent delegation, filesystem, memory 같은 패턴이 필요할 때 Deep Agents SDK를 먼저 탐색한다.
- 단순 tool-calling agent라면 LangChain `create_agent`로 충분할 수 있다.
- PR 관점: Deep Agents 코드베이스에서 SDK / Code / ACP 각 모듈의 경계를 소스코드로 확인할 필요가 있다.

---

## Open Questions
- `create_deep_agent` 내부에서 LangGraph의 어떤 graph를 생성하는가?
- filesystem tools는 어디에 정의되어 있는가? (SDK 내부? 별도 패키지?)
- subagent state는 parent agent와 어떻게 분리되는가?
- ACP integration은 어떤 프로토콜 스펙을 따르는가?
- "durable execution"이 LangGraph의 checkpointing과 어떻게 연결되는가?
- Deep Agents Code (터미널 에이전트)는 SDK를 어떻게 확장하는가?

---

## Used By
- [[Deep Agents]]
- [[LangChain vs LangGraph vs Deep Agents]]
