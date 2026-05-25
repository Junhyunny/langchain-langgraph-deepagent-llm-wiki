# AGENTS.md

이 저장소는 LLM이 유지하는 학습용 위키로, AI agent 프레임워크를 내부 구현까지 이해하고, 아키텍처를 추적하며, 실험을 수행하기 위해 존재한다.

주요 중점 영역:
- LangChain
- LangGraph
- Deep Agents
- AI agent 아키텍처
- 도구 호출
- 상태 관리
- Checkpointing
- Memory
- Context Engineering
- Subagents
- Evaluation

이 저장소의 목적은 무작위 메모를 모으는 데 있지 않다.
목적은 다음을 연결하는 지속 가능한 지식 베이스를 구축하는 데 있다.
- 공식 문서
- 소스 코드
- 예제
- 실험
- 실패 사례
- 설계 결정
- 이슈 분석
- 테스트

## 대상 AI assistant

이 저장소는 다음 도구가 편집하거나 검토할 수 있다.
- Codex
- Claude Code
- GitHub Copilot
- 기타 코딩 또는 작성 agent

모든 agent는 이 파일의 규칙을 따라야 한다.

---

# 핵심 철학

이 저장소를 학습 지향적인 LLM 위키로 다룬다.

이 위키는 다음과 같은 질문에 답하는 데 도움이 되어야 한다.
- 이 프레임워크는 내부적으로 어떻게 동작하는가?
- 어떤 공개 API가 어떤 내부 구현에 대응하는가?
- 특정 동작에는 어떤 파일이 관여하는가?
- 예상 동작을 정의하는 테스트는 무엇인가?
- 내가 이미 배웠거나 시도한 것은 무엇인가?
- 무엇이 실패했는가?
- 아직 무엇이 불분명한가?

문서를 많이 만드는 데 최적화하지 않는다.
정확하고, 소스에 근거하며, 재사용 가능한 지식을 만드는 데 최적화한다.

---

# 저장소 구조

```text
.
├── AGENTS.md
├── README.md
├── docs/
│   ├── raw/
│   ├── raw_manifest.yml
│   ├── source_summaries/
│   └── wiki/
│       ├── _index.md
│       ├── _roadmap.md
│       ├── _open_questions.md
│       ├── frameworks/
│       ├── concepts/
│       ├── comparisons/
│       ├── codebase/
│       ├── flows/
│       ├── tests/
│       ├── experiments/
│       ├── failures/
│       ├── decisions/
│       └── issues/
├── examples/
├── reproductions/
├── evals/
└── scripts/
```

실제 저장소가 이 구조와 다르다면 기존 구조를 유지하되 같은 원칙을 적용한다.

---

# 폴더별 역할

## docs/raw/

원시 소스 자료다.

예시:
- 공식 문서 스냅샷
- 문서에서 복사한 발췌문
- 이슈 메모
- PR 토론 메모
- 실험 로그
- 로컬 코드 리딩 메모
- 벤치마크 출력
- 모델 트레이스
- 재현 로그

규칙:
- Raw 파일은 다듬어진 지식이 아니라 근거 자료다.
- 명시적으로 요청받지 않는 한 raw 파일을 다시 쓰지 않는다.
- 기존 파일을 수정하기보다 새 raw 파일을 추가하거나 내용을 덧붙이는 편을 우선한다.
- 시크릿, API 키, 토큰, 개인 자격 증명, 민감한 개인정보를 저장하지 않는다.
- 대형 웹사이트나 전체 문서 트리를 무분별하게 스크래핑하지 않는다.
- 구체적인 학습 주제, 실험, 버그, 이슈, PR 후보와 관련 있을 때만 raw 자료를 수집한다.

## docs/raw_manifest.yml

소스 레지스트리다.

의미 있는 raw 소스는 모두 여기에 기록해야 한다.

이 파일로 다음을 추적한다.
- 소스 ID
- 제목
- 유형
- URL
- 저장소
- 해당하는 경우 commit SHA
- 로컬 raw 경로
- 수집 날짜
- 해당하는 경우 라이선스 / 공유 메모
- 해당 소스가 공개, 비공개, 생성물, 로컬 전용 중 무엇인지

어떤 소스가 위키 페이지에 영향을 주었다면, 해당 위키 페이지는 그 소스 ID를 참조해야 한다.

## docs/source_summaries/

중요한 소스마다 하나의 요약을 둔다.

다음 용도로 사용한다.
- 공식 문서 요약
- 이슈 요약
- PR 토론 요약
- 소스 파일 요약
- 논문/기사 요약

소스 요약은 사실 중심이어야 하며 원문에 가까워야 한다.
여러 소스를 과도하게 종합해서는 안 된다.

## docs/wiki/

정제된 지식 베이스다.

이곳이 메인 LLM 위키다.

위키에는 다음이 포함되어야 한다.
- 프레임워크 페이지
- 개념 페이지
- 비교 페이지
- 아키텍처 맵
- 실행 흐름
- 테스트 맵
- 실험 보고서
- 실패 사례
- 의사결정 기록
- 이슈 분석

위키 페이지는 간결하고, 구조화되어 있으며, 링크가 풍부해야 한다.

## examples/

실행 가능한 학습 예제다.

가능하면 예제는 한 번에 하나의 개념만 보여주어야 한다.

## reproductions/

버그 또는 혼란스러운 동작을 이해하기 위한 최소 재현 예제다.

재현 예제는 작고, 실행 가능하며, 문서화되어 있어야 한다.

## evals/

평가 사례와 결과다.

프레임워크 동작, agent 품질, 회귀 테스트, 반복 실험을 비교할 때 사용한다.

## scripts/

자동화 스크립트다.

예시:
- 선택한 raw 소스 가져오기
- raw 소스 해시 검증
- 소스 요약 생성
- 깨진 위키 링크 스캔
- 인덱스 구축
- 오래된 페이지 찾기

---

# Raw 소스 수집 정책

raw 소스를 무작정 수집하지 않는다.

**좋지 않은 예:**
- LangChain 문서를 모두 다운로드한다.
- LangGraph 문서를 모두 다운로드한다.
- Deep Agents 문서를 모두 다운로드한다.
- 혹시 모를 상황에 대비해 모든 것을 스크래핑한다.

**좋은 예:**
- 오늘은 LangGraph 체크포인팅을 학습한다.
- 공식 체크포인팅 문서, 관련 소스 파일, 관련 테스트, 그리고 관련 이슈 한두 개만 수집한다.

raw 수집은 다음 중 하나가 있을 때 시작되어야 한다.
1. 구체적인 학습 주제
2. 구체적인 실험
3. 혼란스러운 동작
4. 소스 코드 읽기 세션
5. 버그 재현
6. 근거가 필요한 의사결정

raw 자료를 추가하기 전에 다음을 자문한다.
- 왜 이 소스가 필요한가?
- 어떤 위키 페이지가 이를 사용할 것인가?
- 공개인가, 비공개인가?
- Git에 저장하기에 충분히 작은가?
- 저장하는 대신 다시 가져올 수 있는가?
- 안정적인 URL 또는 commit SHA가 있는가?

---

# 소스 매니페스트 형식

`docs/raw_manifest.yml`을 사용한다.

권장 형식:

```yaml
sources:
  - id: langgraph-docs-checkpointing-2026-05-18
    title: LangGraph checkpointing documentation
    type: official_docs
    framework: LangGraph
    url: "https://..."
    local_path: "docs/raw/langgraph/checkpointing.md"
    retrieved_at: "2026-05-18"
    status: public
    used_by:
      - "docs/wiki/concepts/Checkpointing.md"
      - "docs/wiki/frameworks/LangGraph.md"
    notes: "Official documentation snapshot used for checkpointing study."

  - id: deepagents-source-create-deep-agent-2026-05-18
    title: Deep Agents create_deep_agent source reading
    type: source_code
    framework: Deep Agents
    repo: "https://github.com/langchain-ai/deepagents"
    commit: "UNKNOWN"
    local_path: "docs/raw/deepagents/create_deep_agent_source_notes.md"
    retrieved_at: "2026-05-18"
    status: public
    used_by:
      - "docs/wiki/flows/Deep Agents create_deep_agent flow.md"
    notes: "Update commit SHA when known."
```

규칙:
- 모든 소스는 안정적인 `id`를 가져야 한다.
- 소문자 kebab-case ID를 우선한다.
- `retrieved_at`을 포함한다.
- 해당하는 경우 `url` 또는 `repo`를 포함한다.
- 소스 코드를 참조할 때는 `commit`을 포함한다.
- 로컬 raw 파일이 있으면 `local_path`를 포함한다.
- 위키 페이지가 소스에 의존하면 `used_by`를 포함한다.
- 없는 메타데이터를 지어내지 말고 `UNKNOWN`을 사용한다.

---

# 인용 및 근거 규칙

위키 페이지의 비사소한 사실 주장은 모두 추적 가능해야 한다.

위키 페이지에서는 Sources 섹션을 사용한다.

```markdown
## Sources
- `langgraph-docs-checkpointing-2026-05-18`
- `langgraph-source-checkpoint-saver-2026-05-18`
```

소스 코드를 논의할 때는 파일 경로와, 가능하다면 commit SHA를 포함한다.

```markdown
## Source Code References
- Repo: langgraph
- Commit: UNKNOWN
- Files:
  - `libs/langgraph/...`
  - `libs/checkpoint/...`
```

확인하지 않은 소스를 확인한 것처럼 가장하지 않는다.

다음 라벨을 사용한다.
- **검증됨**
- **부분 검증됨**
- **가설**
- **미검증**
- **소스 필요**
- **오래됨**

불확실할 때는 이를 명시적으로 드러낸다.

---

# 위키 페이지 기준

특별한 이유가 없다면 모든 주요 위키 페이지는 이 구조를 따라야 한다.

```markdown
# Page Title

## Summary
Brief explanation.

## Why It Matters
Why this topic matters for AI agent development or contribution.

## Key Concepts
- [[Concept A]]
- [[Concept B]]

## Details
Main content.

## Source Code References
- TBD if unknown.

## Tests
- TBD if unknown.

## Related Pages
- [[Related Page]]

## Open Questions
- Question 1
- Question 2

## Sources
- `source-id`
```

길고 초점이 흐린 페이지를 만들지 않는다.
페이지가 너무 커지면 개념, 흐름, 테스트, 의사결정 페이지로 나눈다.

---

# 위키링크 규칙

중요하고 재사용 가능한 개념에는 Obsidian 스타일의 위키링크를 사용한다.

```
[[LangChain]]
[[LangGraph]]
[[Deep Agents]]
[[Tool Calling]]
[[Checkpointing]]
[[StateGraph]]
[[Subagents]]
[[Context Engineering]]
```

좋은 링크는 관계를 설명한다.

> [[Planner]]는 사용 가능한 도구만 선택하기 위해 [[Tool Registry]]를 사용한다.

좋지 않은 링크는 키워드만 나열한다.

> [[Planner]] [[Tool]] [[State]] [[Agent]]

링크는 지식을 탐색 가능하게 만드는 데 사용하고, 장식용으로 사용하지 않는다.

---

# 페이지 유형

## 프레임워크 페이지

예시: `docs/wiki/frameworks/LangGraph.md`

포함해야 할 내용:
- 요약
- 언제 사용하는가
- 핵심 추상화
- 공개 API
- 내부 구현 맵
- 관련 테스트
- 관련 예제
- 미해결 질문
- 소스

## 개념 페이지

예시: `docs/wiki/concepts/Checkpointing.md`

포함해야 할 내용:
- 정의
- 중요한 이유
- 어디에 등장하는가
- 프레임워크별 동작
- 구현 메모
- 테스트
- 관련 페이지
- 소스

## 비교 페이지

예시: `docs/wiki/comparisons/LangChain vs LangGraph vs Deep Agents.md`

포함해야 할 내용:
- 짧은 의사결정 규칙
- 비교 표
- 트레이드오프
- 예시 사용 사례
- 실험
- 의사결정 시사점
- 소스

## 코드 맵

예시: `docs/wiki/codebase/LangGraph Code Map.md`

포함해야 할 내용:
- 저장소 목적
- 주요 패키지/디렉터리
- 중요한 진입점
- 읽어야 할 소스 파일
- 읽어야 할 테스트
- 불명확한 영역
- 소스

## 실행 흐름

예시: `docs/wiki/flows/Deep Agents create_deep_agent flow.md`

포함해야 할 내용:
- 진입점
- 호출 경로
- 상태/메시지 흐름
- 읽은 파일
- 찾은 테스트
- 유용하다면 다이어그램
- 미해결 질문
- 소스

## 실험 보고서

예시: `docs/wiki/experiments/2026-05-18 same research agent in three frameworks.md`

포함해야 할 내용:
- 목표
- 설정
- 코드 링크
- 기대 동작
- 실제 동작
- 관찰 내용
- 핵심 정리
- 관련 개념
- 소스

## 실패 사례

예시: `docs/wiki/failures/LangGraph checkpoint resume confusion.md`

포함해야 할 내용:
- 문제
- 기대 동작
- 실제 동작
- 재현
- 의심되는 원인
- 알려진 경우 확인된 원인
- 관련 개념
- 다음 행동
- 상태
- 소스

## 의사결정 기록

예시: `docs/wiki/decisions/Use LangGraph for core orchestration.md`

포함해야 할 내용:
- 결정 사항
- 컨텍스트
- 검토한 옵션
- 트레이드오프
- 이유
- 결과
- 재검토 기준
- 소스

## 이슈 분석

예시: `docs/wiki/issues/LangGraph issue 5225.md`

포함해야 할 내용:
- 이슈 요약
- 재현 코드
- 기대 동작 vs 실제 동작
- 소스 추적 결과 (근본 원인 분석)
- 관련 코드 파일 및 라인
- 관련 테스트
- 학습으로 얻은 인사이트
- 미해결 질문
- 소스

---

# 학습 워크플로

주제를 학습할 때는 다음을 따른다.

1. 학습 질문을 식별한다.
2. 관련 있는 소스만 수집한다.
3. `docs/raw_manifest.yml`을 추가하거나 갱신한다.
4. 중요한 소스에 대한 요약을 만든다.
5. 위키 페이지를 만들거나 갱신한다.
6. 관련 개념에 위키링크를 추가한다.
7. 미해결 질문을 추가한다.
8. 코드를 학습했다면 소스 파일 경로를 추가한다.
9. 동작을 테스트했다면 실험 또는 재현 메모를 추가한다.
10. 주요 페이지를 추가할 때 `_index.md`를 갱신한다.

예시 학습 질문:

> LangGraph 체크포인팅은 내부적으로 어떻게 동작하는가?

기대 산출물:
- `docs/source_summaries/langgraph-checkpointing.md`
- `docs/wiki/concepts/Checkpointing.md`
- `docs/wiki/flows/LangGraph checkpointing flow.md`
- `docs/wiki/frameworks/LangGraph.md`
- `docs/wiki/_open_questions.md`

---

# 코드 리딩 워크플로

소스 코드를 읽을 때는 다음을 따른다.

1. 공개 API 또는 관찰한 동작에서 시작한다.
2. 에디터를 사용해 정의를 추적한다.
3. 진입점을 기록한다.
4. 읽은 파일을 기록한다.
5. 핵심 클래스/함수를 기록한다.
6. 관련 테스트를 찾는다.
7. 무엇이 검증되었고 무엇이 아직 불분명한지 적는다.
8. 관련 흐름 또는 코드 맵 페이지를 갱신한다.

소스 파일이나 테스트를 확인하지 않았다면 내부 흐름을 이해했다고 주장하지 않는다.

다음 형식을 사용한다.

```markdown
## Files Read
- `path/to/file.py`
  - Purpose:
  - Important functions/classes:
  - Notes:

## Call Path
1. `public_api()`
2. `internal_function()`
3. `runtime_step()`

## Verified
- ...

## Still Unclear
- ...
```

---

# 실험 워크플로

실험을 수행할 때는 다음을 따른다.

1. 작은 예제 또는 재현 코드를 만든다.
2. 기대 동작을 적는다.
3. 코드를 실행한다.
4. 결과를 저장한다.
5. 관찰 내용을 `docs/wiki/experiments/`에 요약한다.
6. 관련 개념과 프레임워크 페이지를 연결한다.
7. 결과가 버그를 시사하면 실패 사례를 만들거나 갱신한다.

Git에 거대한 raw 로그를 저장하지 않는다.
이를 요약하고 최소 재현만 저장한다.

---

# AI assistant 동작 규칙

이 저장소에서 AI assistant로 동작할 때는 다음을 따른다.

**해야 할 일:**
- 소스에 근거한다.
- 공식 문서, 소스 코드, 테스트, 이슈, PR을 우선한다.
- 불확실성을 명시적으로 표현한다.
- 페이지 구조를 유지한다.
- 중요한 개념에는 위키링크를 추가한다.
- 새 개념이 관련 페이지에 영향을 주면 해당 페이지도 함께 갱신한다.
- raw와 wiki를 분리해 유지한다.
- 다시 쓰라는 요청이 없다면 사용자가 작성한 메모를 보존한다.
- 작고 리뷰 가능한 변경을 우선한다.
- 작업이 정말 모호해서 합리적으로 시도할 수 없을 때만 설명을 요청한다.

**하지 말아야 할 일:**
- 소스를 지어내지 않는다.
- 확인하지 않은 소스 코드를 확인했다고 주장하지 않는다.
- 학습 목적 없이 문서를 대량 스크래핑하지 않는다.
- 메모를 조용히 삭제하지 않는다.
- 필요 이상으로 raw 파일을 덮어쓰지 않는다.
- 명시적으로 요청받지 않는 한 대규모 리팩터링을 하지 않는다.
- 시크릿이나 자격 증명을 추가하지 않는다.
- 외부 저장소에 PR을 제출하거나 fork, commit, push 작업을 수행하지 않는다.
- Obsidian graph view를 그래프 데이터베이스로 취급하지 않는다.
- vector DB 검색을 ontology로 취급하지 않는다.
- 소스 요약과 종합된 위키 페이지를 혼동하지 않는다.

---

# Obsidian 사용법

Obsidian은 Markdown 지식 브라우저로 사용한다.

Obsidian이 제공하는 것:
- 노트 탐색
- 백링크
- graph view
- 로컬 검색
- 속성
- 선택적인 Bases 보기

Obsidian이 자동으로 실제 그래프 데이터베이스나 ontology를 만들어 주는 것은 아니다.

Obsidian 링크를 사용해 지식을 탐색 가능하게 만든다.

> [[LangGraph]]는 [[Checkpointing]]과 [[Human in the Loop]] 같은 런타임 기능을 제공한다.

AI assistant에게 중요한 것은 Obsidian의 UI가 아니다.
중요한 것은 Markdown 구조, 링크, 메타데이터, 소스 참조다.

---

# Ontology-lite 규칙

이 위키는 가벼운 ontology 패턴을 사용할 수 있다.

명시적인 페이지 유형을 사용한다.

```yaml
---
type: concept
framework:
  - LangGraph
status: draft
confidence: medium
last_reviewed: 2026-05-18
sources:
  - langgraph-docs-checkpointing-2026-05-18
---
```

유용한 `type` 값:
- `framework`
- `concept`
- `comparison`
- `code_map`
- `flow`
- `experiment`
- `failure`
- `decision`
- `issue`
- `source_summary`

유용한 `status` 값:
- `draft`
- `in_review`
- `verified`
- `outdated`
- `needs_source`

유용한 `confidence` 값:
- `low`
- `medium`
- `high`

---

# 인덱스 유지 관리

다음을 유지한다.
- `docs/wiki/_index.md`
- `docs/wiki/_roadmap.md`
- `docs/wiki/_open_questions.md`

## _index.md

카테고리별 주요 페이지를 나열해야 한다.

## _roadmap.md

학습 목표와 다음 학습 영역을 추적해야 한다.

## _open_questions.md

해결되지 않은 질문을 수집해야 한다.

주요 페이지를 추가할 때는 `_index.md`를 갱신한다.
불확실성을 발견하면 `_open_questions.md`를 갱신한다.

---

# 권장 초기 페이지

없다면 다음 페이지를 먼저 만든다.

```
docs/wiki/_index.md
docs/wiki/_roadmap.md
docs/wiki/_open_questions.md
docs/wiki/frameworks/LangChain.md
docs/wiki/frameworks/LangGraph.md
docs/wiki/frameworks/Deep Agents.md
docs/wiki/comparisons/LangChain vs LangGraph vs Deep Agents.md
docs/wiki/concepts/Tool Calling.md
docs/wiki/concepts/StateGraph.md
docs/wiki/concepts/Checkpointing.md
docs/wiki/concepts/Subagents.md
docs/wiki/concepts/Context Engineering.md
docs/wiki/concepts/Memory.md
docs/wiki/concepts/Evaluation.md
docs/wiki/codebase/LangChain Code Map.md
docs/wiki/codebase/LangGraph Code Map.md
docs/wiki/codebase/Deep Agents Code Map.md
docs/wiki/flows/LangChain create_agent flow.md
docs/wiki/flows/LangGraph StateGraph compile invoke flow.md
docs/wiki/flows/Deep Agents create_deep_agent flow.md
```

---

# Raw 동기화 및 Git 정책

권장 기본값은 다음과 같다.

```
Git tracks:
- docs/wiki/
- docs/source_summaries/
- docs/raw_manifest.yml
- examples/
- reproductions/
- evals/
- scripts/

Git does not track by default:
- docs/raw/*
- large logs
- generated traces
- local caches
- vector indexes
- databases
- private notes
```

raw 파일이 작고, 공개되어 있으며, 재현성에 중요하다면 의도적으로 커밋할 수 있다.
raw 파일이 크거나, 비공개이거나, 저작권 문제가 있거나, 생성물이거나, 다시 가져오기 쉽다면 커밋하지 않는다.
대신 `docs/raw_manifest.yml`에 기록한다.

---

# 품질 기준

좋은 위키 갱신은 미래의 작업을 더 쉽게 만들어야 한다.

변경을 마치기 전에 다음을 확인한다.
- 소스를 추가했는가?
- 사실과 해석을 구분했는가?
- 관련 페이지를 연결했는가?
- 필요하다면 인덱스를 갱신했는가?
- 미해결 질문을 기록했는가?
- 불필요한 raw 수집을 피했는가?
- 검증되지 않은 주장을 피했는가?
- 변경을 작고 리뷰 가능하게 유지했는가?

---

# 현재 학습 목표

현재 목표는 LangChain, LangGraph, Deep Agents를 다음이 가능할 만큼 깊이 이해하는 것이다.

1. 아키텍처를 설명한다.
2. 트레이드오프를 비교한다.
3. 공개 API에서 내부 구현까지 추적한다.
4. 의미 있는 실험을 수행한다.
5. 테스트를 이해한다.
6. 이슈의 근본 원인을 소스에서 직접 분석한다.

속도보다 깊이, 추적 가능성, 정확성을 우선한다.
