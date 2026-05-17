---
name: wiki-ask
description: >
  Use this skill when the user asks a question about LangChain, LangGraph, Deep Agents,
  or any AI agent topic while building the LLM wiki.
  Trigger phrases: "wiki 기준으로 답해줘", "지금 wiki로 답할 수 있어?", "근거 있는 것만 말해줘",
  "source 부족한 거 표시해줘", "research plan 만들어줘", "ingest 순서 알려줘",
  "wiki에서 어떤 페이지 필요해?", "어떤 source 수집해야 해?", "/wiki-ask".
user-invocable: true
---

# wiki-ask

LLM Wiki의 **현재 상태를 먼저 파악**한 뒤, 질문에 적합한 응답 모드를 선택하는 스킬.
wiki가 비어 있을수록 "답변"이 아니라 "연구 계획"을 생성한다.

## 지원 에이전트

| 에이전트 | 진입점 |
|----------|--------|
| GitHub Copilot CLI | `/wiki-ask` 또는 자연어 트리거 |
| Claude Code | `/wiki-ask` (`.claude/commands/`) |
| Codex | 자연어 트리거 또는 AGENTS.md 참조 |

---

## 핵심 원칙

> 초기 wiki에서 AI는 답변 엔진이 아니라 **연구 계획자**다.
> wiki가 성숙할수록 **source 기반 설명자**, 이후 **개인 연구 조수**로 전환된다.

| Wiki 단계 | AI 역할 | 응답 모드 |
|-----------|---------|-----------|
| **초기** (source 거의 없음) | 연구 계획자 + 위키 구조 관리자 | Research Plan 모드 |
| **중기** (source summary 일부 존재) | Source 기반 설명자 | Partial Answer 모드 |
| **후기** (wiki + source summary 충실) | 개인 연구 조수 | Wiki Answer 모드 |

---

## 전체 흐름

```
1단계: wiki 현재 상태 파악
     ↓
2단계: 응답 모드 결정
     ↓
3단계: 질문 재구성 (필요시)
     ↓
4단계: 모드에 맞는 응답 생성
     ↓
5단계: 다음 행동 제안
```

---

## 1단계: wiki 현재 상태 파악

다음 파일을 읽는다.

- `docs/raw_manifest.yml` — 수집된 source 목록
- `docs/wiki/_index.md` — 존재하는 wiki 페이지 목록
- `docs/wiki/_open_questions.md` — 미해결 질문 목록
- `docs/source_summaries/` — 존재하는 source summary 목록
- 질문 주제와 관련된 `docs/wiki/` 하위 페이지들

**파악할 내용:**
- 질문 주제에 대한 wiki 페이지가 존재하는가?
- 관련 source summary가 있는가?
- `raw_manifest.yml`에 관련 source가 등록되어 있는가?
- 기존 wiki에 해당 주제의 핵심 주장이 있는가?

`references/wiki-maturity-rubric.md`를 참조해 현재 wiki 상태를 평가한다.

---

## 2단계: 응답 모드 결정

| 조건 | 응답 모드 |
|------|-----------|
| 관련 source summary 없음 + wiki 페이지 없음 | **Research Plan** |
| source summary 일부 있음, wiki 페이지 미완성 | **Partial Answer** |
| wiki 페이지 충실 + source summary 존재 | **Wiki Answer** |

모드를 결정한 뒤 응답 시작 전에 명시한다.

```
📊 Wiki 상태: [초기 / 중기 / 후기]
🔍 응답 모드: [Research Plan / Partial Answer / Wiki Answer]
```

---

## 3단계: 질문 재구성 (Research Plan 모드일 때만)

원래 질문이 wiki 상태와 맞지 않으면 더 좋은 질문으로 재구성한다.

**재구성 예시:**

| 원래 질문 (wiki 없을 때 별 의미 없음) | 재구성된 질문 |
|--------------------------------------|--------------|
| "LangGraph 내부 아키텍처를 설명해줘" | "LangGraph 아키텍처를 이해하려면 어떤 source가 필요한가?" |
| "create_deep_agent는 어떻게 동작해?" | "create_deep_agent를 분석하기 위한 연구 계획을 만들어줘" |
| "checkpointing과 memory의 차이는?" | "checkpointing vs memory를 비교하려면 어떤 페이지를 먼저 수집해야 해?" |

재구성된 질문을 사용자에게 보여주고 진행한다.

---

## 4단계: 모드에 맞는 응답 생성

### Research Plan 모드

`references/response-research-plan.md` 형식을 따른다.

출력 구조:
```
## 현재 wiki 상태 요약
[관련 페이지/source 없음 또는 부족한 내용 요약]

## 현재 wiki로 확인된 내용
- [있으면 나열, 없으면 "없음"]
- Source: [source_id 또는 "근거 없음"]

## Needs Source
- [답변에 필요하지만 아직 없는 정보 목록]

## 필요한 Source 목록
| 우선순위 | 유형 | 제목/설명 | 예상 URL 또는 경로 |
|---------|------|----------|-----------------|
| 1 | official_docs | ... | ... |
| 2 | source_code | ... | ... |

## 추천 Ingest 순서
1. [먼저 읽어야 할 source]
2. [그다음]
3. [이후]

## 임시 가설 ⚠️
> 이하는 wiki에 근거 없는 추측입니다. 검증 전까지 사용에 주의하세요.
- [가설 1]
- [가설 2]

## 만들어야 할 Wiki 페이지
- [페이지 경로]: [이유]

## 추천 다음 질문
- [더 좋은 형태로 재구성된 후속 질문]
```

---

### Partial Answer 모드

`references/response-partial-answer.md` 형식을 따른다.

출력 구조:
```
## 현재 wiki로 답할 수 있는 것
[source summary 또는 wiki 페이지 근거로 답변]
Source: [source_id]

## 근거가 부족한 부분
- [항목]: Needs Source

## 추가로 필요한 Source
[짧은 목록]

## 임시 가설 ⚠️
[있으면 표시, 없으면 생략]
```

---

### Wiki Answer 모드

`references/response-wiki-answer.md` 형식을 따른다.

출력 구조:
```
## 답변
[wiki 기반 답변]

## 근거
- [주장]: Source: [source_id]
- [주장]: Source: [source_id]

## 관련 Wiki 페이지
- [[페이지명]]

## 열린 질문
- [아직 wiki에 없는 부분]
```

---

## 5단계: 다음 행동 제안

응답 마지막에 항상 다음을 포함한다.

```
---
💡 다음 행동 제안:
  [ ] fetch-raw-doc: [수집 우선 source URL]
  [ ] source summary 생성: [source_id]
  [ ] wiki 페이지 업데이트: [페이지 경로]
  [ ] _open_questions.md 추가: [미해결 질문]
```

---

## 주의 사항

- wiki에 근거 없는 주장은 반드시 **⚠️ 가설** 또는 **Needs Source**로 표시한다.
- 일반 LLM 지식으로 wiki를 대체하지 않는다. wiki가 비어 있으면 비어 있다고 명시한다.
- "모른다"는 것을 숨기지 않는다. "현재 wiki에는 근거가 없습니다"가 올바른 답변이다.
- 한 번에 너무 많은 source를 제안하지 않는다. 오늘 공부할 수 있는 2~5개만 제안한다.

---

## 레퍼런스 파일

| 파일 | 읽는 시점 |
|------|-----------|
| `skills/wiki-ask/references/wiki-maturity-rubric.md` | 1단계: wiki 상태 평가 시 |
| `skills/wiki-ask/references/response-research-plan.md` | 4단계: Research Plan 모드 |
| `skills/wiki-ask/references/response-partial-answer.md` | 4단계: Partial Answer 모드 |
| `skills/wiki-ask/references/response-wiki-answer.md` | 4단계: Wiki Answer 모드 |
