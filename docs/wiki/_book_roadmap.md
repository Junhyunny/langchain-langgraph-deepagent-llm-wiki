# 책 로드맵: LangChain · LangGraph · Deep Agents 완전 분석

---

## 이 로드맵의 목적

500페이지 분량의 블로그 책을 쓰기 위한 목차형 학습 로드맵이다.

**대상 독자:** Python 중급 개발자. LLM API 호출은 처음이거나 막 시작한 수준.  
**목표:** 기본 개념부터 내부 소스 코드까지 깊이 이해하고, 초보자도 읽을 수 있는 글로 설명할 수 있다.

---

## 학습 사이클 (한 바퀴 = 블로그 글 1편)

```
[1] AI가 준비한다
    - 해당 섹션의 관련 위키 페이지 보강 및 검증 라벨 갱신
    - 소스 코드 근거 확인, "검증됨" / "소스 필요" 라벨 정리
    - 예제 코드 또는 실험 결과 연결

[2] 사람이 이해한다
    - 위키 페이지를 읽는다
    - 예제 코드를 직접 실행해본다
    - 모르는 건 /wiki-ask 로 질문한다

[3] 사람이 블로그 글을 쓴다
    - 초보자도 읽을 수 있는 수준으로
    - 개념 설명 → 코드 예시 → 내부 동작 → 실전 팁 흐름
    - 소스 코드 근거가 있는 주장은 파일 경로까지 포함

[4] 사람이 [x] 체크한다
    - 블로그 글을 발행하면 아래 목차에서 [ ] → [x]
    - 이 체크는 "이 개념을 남에게 설명할 수 있다"는 증거
```

> `_open_questions.md`는 위키 리서치 리소스 수집용으로 별도 운영한다.  
> `_roadmap.md`는 오픈소스 기여자 성장 로드맵으로 별도 운영한다.

---

## 진행 현황

| 파트 | 섹션 수 | 완료 | 예상 분량 |
|------|---------|------|----------|
| Part 0: 시작하며 | 2 | 0 | ~10p |
| Part 1: AI 에이전트 기초 | 14 | 0 | ~70p |
| Part 2: LangChain 완전 분석 | 24 | 0 | ~120p |
| Part 3: LangGraph 완전 분석 | 26 | 0 | ~130p |
| Part 4: Deep Agents 완전 분석 | 20 | 0 | ~100p |
| Part 5: 심화 비교와 실전 | 14 | 0 | ~70p |
| **합계** | **100** | **0** | **~500p** |

---

## Part 0: 시작하며 (~10페이지)

- [ ] **0.1** 이 책을 쓰는 이유 — AI 에이전트 프레임워크를 소스 코드까지 이해한다는 것
- [ ] **0.2** 개발 환경 설정 — Python 3.11+, 패키지 설치, API 키 설정

---

## Part 1: AI 에이전트 기초 (~70페이지)

### 1장. LLM 기초

- [ ] **1.1** LLM이란 무엇인가? — 토큰, 컨텍스트 윈도우, 온도, 샘플링
- [ ] **1.2** LLM API 첫 호출 — OpenAI / Anthropic / 로컬 모델 직접 연결하기
- [ ] **1.3** 프롬프트 엔지니어링 기초 — System / User / Assistant 메시지 구조

### 2장. AI 에이전트란 무엇인가?

- [ ] **2.1** 에이전트의 정의 — LLM + 도구 + 오케스트레이션이 만나는 지점
- [ ] **2.2** ReAct 패턴 — Reasoning + Acting, 생각하고 행동하고 관찰한다
- [ ] **2.3** Tool Calling이란? — LLM이 함수를 호출하는 원리
  - 위키: [[Tool Calling]]
- [ ] **2.4** 에이전트 런타임의 구성 요소 — 모델 · 도구 · 상태 · 오케스트레이터
  - 위키: [[Agent Runtime]]

### 3장. 세 프레임워크 한눈에 보기

- [ ] **3.1** LangChain이란? — 포지셔닝, 핵심 추상화, 언제 쓰는가
  - 위키: [[LangChain]]
- [ ] **3.2** LangGraph란? — 왜 그래프 구조로 에이전트를 만드는가
  - 위키: [[LangGraph]], [[StateGraph]]
- [ ] **3.3** Deep Agents란? — LangChain 위에 올라간 미들웨어 스택의 철학
  - 위키: [[Deep Agents]], [[Agent Harness]]
- [ ] **3.4** 세 프레임워크 한눈에 비교 — 언제 무엇을 선택하는가
  - 위키: [[LangChain vs LangGraph vs Deep Agents]]

---

## Part 2: LangChain 완전 분석 (~120페이지)

### 4장. Runnable — LangChain의 기반 인터페이스

- [ ] **4.1** Runnable 인터페이스란? — invoke / stream / batch / pipe의 통일된 계약
- [ ] **4.2** RunnableSequence — LCEL 체인을 `|` 연산자로 연결하는 방식
- [ ] **4.3** RunnableParallel — 병렬 실행과 내부 thread pool 동작
- [ ] **4.4** RunnableConfig — 실행 시간 설정 주입, configurable 패턴

### 5장. 프롬프트와 출력 파싱

- [ ] **5.1** PromptTemplate — ChatPromptTemplate, FewShotPromptTemplate 내부 구조
  - 위키: [[PromptTemplate]]
- [ ] **5.2** OutputParser — StrOutputParser, JsonOutputParser, 구조화 출력
- [ ] **5.3** with_structured_output — JSON 스키마 기반 출력 강제의 동작 원리

### 6장. Tool 시스템

- [ ] **6.1** Tool 정의 방법 — `@tool` 데코레이터, BaseTool 상속, 두 방식의 차이
- [ ] **6.2** bind_tools 내부 — 모델에 도구가 어떻게 연결되는가 (`_get_bound_model`)
- [ ] **6.3** Tool Calling 실행 흐름 — AIMessage(tool_calls) → ToolMessage 전체 경로
- [ ] **6.4** InjectedToolArg / InjectedState — 런타임 주입 패턴

### 7장. LangChain 에이전트

- [ ] **7.1** create_react_agent — 소스 코드로 보는 ReAct 루프 (`chat_agent_executor.py`)
  - 위키: [[LangChain create_agent flow]]
- [ ] **7.2** create_agent — factory.py 내부 구조, 초기화 비용의 정체
  - 위키: [[LangChain create_agent flow]]
- [ ] **7.3** Middleware 시스템 설계 — before_model / wrap_model_call / wrap_tool_call 훅의 역할

### 8장. LangChain 빌트인 미들웨어

- [ ] **8.1** SummarizationMiddleware — 컨텍스트 윈도우를 어떻게 줄이는가
  - 위키: [[SummarizationMiddleware]]
- [ ] **8.2** PIIMiddleware — 개인정보 필터링 패턴
  - 위키: [[PIIMiddleware]]
- [ ] **8.3** LLMToolSelectorMiddleware — LLM이 도구를 동적으로 고르는 방식
  - 위키: [[LLMToolSelectorMiddleware]]
- [ ] **8.4** ModelRetryMiddleware + ModelFallbackMiddleware — 복원력 설계
  - 위키: [[RetryMiddleware]], [[ModelFallbackMiddleware]]
- [ ] **8.5** ToolRetryMiddleware — 실패한 도구 호출을 어떻게 재시도하는가

### 9장. 메모리, 스트리밍, RAG

- [ ] **9.1** Memory API — 대화 히스토리 관리와 세션 간 기억
  - 위키: [[Memory]]
- [ ] **9.2** Event Streaming — astream_events 완전 가이드, v1/v2/v3 차이
  - 위키: [[Event Streaming]]
- [ ] **9.3** RAG 파이프라인 — 임베딩, 벡터 스토어, 리트리버, 청크 전략
  - 위키: [[RAG]]

---

## Part 3: LangGraph 완전 분석 (~130페이지)

### 10장. StateGraph 기초

- [ ] **10.1** StateGraph란? — 노드, 엣지, 상태의 관계를 그래프로 표현하는 이유
  - 위키: [[StateGraph]]
- [ ] **10.2** 상태 정의 — TypedDict vs Pydantic, Reducer의 역할
- [ ] **10.3** 엣지 라우팅 — add_edge, add_conditional_edges, path_map 선택과 생략
- [ ] **10.4** StateGraph.compile() 내부 — Pregel 그래프가 만들어지는 과정 (`state.py:1164`)
  - 위키: [[LangGraph StateGraph compile invoke flow]]

### 11장. Pregel 런타임

- [ ] **11.1** invoke 실행 흐름 — SyncPregelLoop이 step을 실행하는 전체 경로
  - 위키: [[LangGraph StateGraph compile invoke flow]]
- [ ] **11.2** Superstep 메커니즘 — tick / after_tick / recursion_limit의 동작
- [ ] **11.3** 무한 루프 방지 — `stop = step + recursion_limit + 1` 내부 구현

### 12장. Checkpointing

- [ ] **12.1** Checkpointing이란? — 왜 체크포인트가 필요한가, 어떤 문제를 해결하는가
  - 위키: [[Checkpointing]]
- [ ] **12.2** MemorySaver 내부 — `_put_checkpoint → checkpointer.put()` 호출 경로
- [ ] **12.3** DeltaChannel — 증분 저장의 동작 원리, snapshot_frequency
  - 위키: [[DeltaChannel]]
- [ ] **12.4** Checkpoint 복구 — pending_writes와 resume 흐름의 내부 구조
  - 위키: [[LangGraph pending writes resume confusion]]

### 13장. Human-in-the-Loop

- [ ] **13.1** interrupt() / Command(resume=) — 일시정지와 재개의 내부 메커니즘
  - 위키: [[Human-in-the-Loop]]
- [ ] **13.2** HITL 실전 패턴 — 승인 / 수정 / 거부 흐름 구현

### 14장. ToolNode

- [ ] **14.1** ToolNode 내부 구조 — 도구 실행의 전체 흐름 분석
  - 위키: [[LangGraph ToolNode flow]]
- [ ] **14.2** InjectedState / InjectedStore — ToolNode의 런타임 주입 패턴
- [ ] **14.3** Command 반환 패턴 — `Command(update/goto/PARENT)` 동작과 차이
- [ ] **14.4** handle_tool_error — 에러 처리, 메시지 형태, 재시도 흐름

### 15장. 고급 LangGraph 패턴

- [ ] **15.1** Subgraph — 모듈화와 parent ↔ child 상태 스키마 호환성
  - 위키: [[Subagents]]
- [ ] **15.2** Send / Map-Reduce — 병렬 worker 패턴, reducer 집계 설계
- [ ] **15.3** child ToolNode의 Command.PARENT + Send — fan-out 실험 분석
- [ ] **15.4** Streaming 7가지 모드 — values / updates / custom / checkpoints / tasks / messages / debug
  - 위키: [[Event Streaming]]
- [ ] **15.5** InMemoryStore — namespace, vector search, cosine similarity 내부
  - 위키: [[Store]]

### 16장. create_react_agent (LangGraph 버전)

- [ ] **16.1** create_react_agent 소스 분석 — LangChain의 것과 무엇이 다른가
  - 위키: [[LangGraph create_react_agent flow]]
- [ ] **16.2** pre_model_hook / post_model_hook — 고급 커스터마이징 포인트

---

## Part 4: Deep Agents 완전 분석 (~100페이지)

### 17장. Deep Agents 기초

- [ ] **17.1** create_deep_agent — 내부 구조 완전 분석, 미들웨어 스택이 조립되는 과정
  - 위키: [[Deep Agents create_deep_agent flow]]
- [ ] **17.2** Agent Harness란? — Harness의 역할과 구성 요소
  - 위키: [[Agent Harness]]
- [ ] **17.3** HarnessProfile — 모델별 프로필 매핑, `_builtin_profiles` 내부

### 18장. Deep Agents Middleware 스택

- [ ] **18.1** Middleware 스택의 조립 원리 — wrap_model_call 중첩 순서와 실행 방향
- [ ] **18.2** FilesystemMiddleware — write_file / read_file 도구의 내부 구현
- [ ] **18.3** SubAgentMiddleware — task 도구 실행, subagent 생성, 상태 격리 흐름
  - 위키: [[Deep Agents SubAgentMiddleware task tool flow]]
- [ ] **18.4** 병렬 task 도구 호출 — 단일 AIMessage의 다중 task call 동시 실행
- [ ] **18.5** _EXCLUDED_STATE_KEYS — parent / child 상태 격리 패턴의 설계 이유

### 19장. Context Engineering

- [ ] **19.1** Context Engineering이란? — Deep Agents가 컨텍스트를 구성하는 전략
  - 위키: [[Context Engineering]]
- [ ] **19.2** Skills frontmatter — agent가 관련 skill을 선택하는 메커니즘
- [ ] **19.3** @dynamic_prompt 데코레이터 — 동적 시스템 프롬프트 생성 패턴

### 20장. Sandbox와 코드 실행

- [ ] **20.1** FilesystemMiddleware의 execute 도구 — sandbox backend가 없을 때 동작 방식
- [ ] **20.2** Sandbox backend 연결 — 실제 코드 실행 환경과 execute 결과 payload

### 21장. Evaluation

- [ ] **21.1** Deep Agents eval 구조 — evals/ 디렉터리와 평가 파이프라인
  - 위키: [[Evaluation]]
- [ ] **21.2** LLM-as-a-judge — 판정 모델 결정 경로와 MODEL_GROUPS.md
- [ ] **21.3** BFCL 벤치마크 — tool calling 능력을 숫자로 측정하는 방법
- [ ] **21.4** Harbor 통합 — 평가 파이프라인 오케스트레이션

---

## Part 5: 심화 비교와 실전 (~70페이지)

### 22장. 아키텍처 비교

- [ ] **22.1** Tool Calling 내부 비교 — LangChain vs LangGraph vs Deep Agents의 실행 경로
  - 위키: [[ToolNode in LangGraph vs LangChain create_agent]], [[LangGraph ToolNode Command vs Deep Agents task tool]]
- [ ] **22.2** 상태 관리 비교 — TypedDict / Pydantic / middleware state의 트레이드오프
- [ ] **22.3** Checkpointing 비교 — 세 프레임워크의 지속성 전략
- [ ] **22.4** 병렬 실행 비교 — Send / RunnableParallel / parallel task의 설계 차이
- [ ] **22.5** 컨텍스트 윈도우 관리 비교 — SummarizationMiddleware vs LangGraph streaming

### 23장. 언제 무엇을 쓰는가

- [ ] **23.1** 프레임워크 선택 의사결정 가이드 — 10가지 기준으로 비교
  - 위키: [[When to use LangGraph vs Deep Agents for orchestration]]
- [ ] **23.2** LangGraph vs Deep Agents 오케스트레이션 심층 비교
  - 위키: [[create_agent vs create_deep_agent]]
- [ ] **23.3** Guardrails 구현 비교 — 세 프레임워크에서 입출력을 어떻게 통제하는가
  - 위키: [[Guardrails]]
- [ ] **23.4** Tracing과 관찰 가능성 — LangSmith 통합, 그래프 스텝별 디버깅
  - 위키: [[Tracing]]

### 24장. 실전 프로젝트: 리서치 에이전트 3가지 버전

- [ ] **24.1** 리서치 에이전트 설계 — 공통 요구사항과 각 프레임워크 접근 방식
- [ ] **24.2** LangChain 버전 — create_agent + 미들웨어 스택으로 구현
- [ ] **24.3** LangGraph 버전 — StateGraph + ToolNode + Checkpointing으로 구현
- [ ] **24.4** Deep Agents 버전 — SubAgentMiddleware + task tool로 구현
- [ ] **24.5** 세 버전 코드 비교 — 같은 문제를 다르게 푸는 방식에서 배우는 것

### 25장. 오픈소스 기여

- [ ] **25.1** 이슈 분석에서 PR까지 — LangGraph #5225 Pydantic default_factory 버그 사례
  - 위키: [[LangGraph issue 5225 pydantic default factory]]
- [ ] **25.2** 기여자가 되는 법 — CONTRIBUTING.md 읽기, maintainer 소통, 테스트 작성

---

## 다음 사이클 시작 방법

1. 위 목차에서 `[ ]` 항목 중 순서대로 하나를 고른다
2. `/wiki-ask` 로 "X 섹션 준비해줘" 라고 요청한다 — AI가 관련 위키 보강 및 검증을 수행한다
3. 위키를 읽고 예제를 실행한다
4. 블로그 글을 쓴다
5. `[ ]` → `[x]` 로 직접 체크한다
