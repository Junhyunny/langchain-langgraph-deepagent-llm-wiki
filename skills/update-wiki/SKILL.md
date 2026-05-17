---
name: update-wiki
description: >
  Use this skill when the user wants to update the wiki from a raw file or source summary.
  Trigger phrases: "wiki 업데이트해줘", "source summary 만들어줘", "raw 기반으로 wiki 반영해줘",
  "wiki에 넣어줘", "문서 반영해줘", "source 정리해줘", "/update-wiki".
user-invocable: true
---

# update-wiki

raw 파일 또는 source summary를 기반으로 wiki 페이지를 **안전하게** 업데이트하는 스킬.
단순 붙여넣기가 아니라 출처 추적, 충돌 감지, 사실/해석 분리를 통해 지식 품질을 유지한다.

## 지원 에이전트

| 에이전트 | 진입점 |
|----------|--------|
| GitHub Copilot CLI | `/update-wiki` 또는 자연어 트리거 |
| Claude Code | `/update-wiki` (`.claude/commands/`) |
| Codex | 자연어 트리거 또는 AGENTS.md 참조 |

---

## 핵심 원칙

> raw 기반 wiki 업데이트의 목표는 "요약을 많이 만드는 것"이 아니라,
> 출처가 추적 가능하고, 기존 지식과 연결되며, 다음 질문을 더 잘 만들 수 있는 지식 상태로 바꾸는 것이다.

---

## 전체 흐름

```
1단계: 입력 수집 및 source 분류
     ↓
2단계: source summary 생성 (raw 입력인 경우)
     ↓
3단계: 영향받는 wiki 페이지 목록 제안
     ↓
4단계: 사용자 확인 (계획 승인)
     ↓
5단계: wiki 페이지 업데이트
     ↓
6단계: _open_questions.md 업데이트
     ↓
7단계: 업데이트 후 체크리스트 실행
```

---

## 1단계: 입력 수집 및 source 분류

### 입력

다음 중 하나를 확인한다.

- `docs/raw/` 하위의 raw 파일 경로
- `docs/source_summaries/` 하위의 source summary 파일 경로

경로가 제공되지 않으면 사용자에게 물어본다.

### source 분류

`references/source-type-trust-levels.md`를 참조해 다음을 판단한다.

| 항목 | 판단할 내용 |
|------|------------|
| source 유형 | official_docs / source_code / test_code / issue / experiment_log / blog 등 |
| 신뢰도 | High / Medium / Low |
| 현재 버전 | retrieved_at, commit SHA, version 기록 여부 |
| 주요 claims | 이 source에서 wiki에 반영할 핵심 주장 목록 |

분류 결과를 간단히 출력한다.

```
📋 Source 분류
  유형: official_docs
  신뢰도: High
  날짜: 2026-05-18
  주요 claims: [claim 1], [claim 2], ...
```

---

## 2단계: source summary 생성 (raw 입력인 경우)

입력이 raw 파일이면 먼저 source summary를 만든다.
입력이 이미 source summary이면 이 단계를 건너뛴다.

출력 경로: `docs/source_summaries/<source-id>.md`

`references/source-summary-template.md`를 따른다.

규칙:
- **원문에 있는 내용만** Key Facts에 적는다.
- 내 추론/해석은 "Interpretation" 섹션에 분리한다.
- 확실하지 않은 내용은 "Open Questions"에 적는다.
- 관련 개념은 `[[wikilink]]`로 연결한다.
- source_id를 frontmatter에 유지한다.
- 아직 wiki 문서는 수정하지 않는다.

---

## 3단계: 영향받는 wiki 페이지 목록 제안

source summary를 바탕으로 어떤 wiki 페이지에 영향을 주는지 분석한다.

각 페이지마다 다음을 판단한다.

| 페이지 경로 | 업데이트 이유 | 변경 강도 | 충돌 위험 |
|------------|--------------|----------|----------|
| `docs/wiki/frameworks/...` | | Minor / Major | Low / High |
| `docs/wiki/concepts/...` | | | |
| `docs/wiki/_open_questions.md` | | | |

**새 페이지 생성 기준:**
- 반복해서 등장할 개념인가?
- 다른 문서에서 링크할 가능성이 높은가?
- 하나의 source를 넘어 일반화할 가치가 있는가?

→ 위 기준을 충족하지 않으면 기존 페이지에 통합한다.

---

## 4단계: 사용자 확인 (계획 승인)

3단계의 계획을 출력하고 사용자 확인을 기다린다.

```
📝 변경 계획
  수정: docs/wiki/frameworks/Deep Agents.md — [이유]
  수정: docs/wiki/_open_questions.md — [이유]
  신규: docs/wiki/concepts/Agent Harness.md — [이유]

계속 진행할까요? (y/n)
```

사용자가 특정 페이지를 제외하거나 범위를 좁히면 그에 따른다.
**명시적 확인 없이 파일을 수정하지 않는다.**

---

## 5단계: wiki 페이지 업데이트

승인된 각 페이지를 업데이트한다.

### 업데이트 규칙

**① 사실 / 해석 / 가설 분리**

```markdown
## Verified Facts
- [공식 문서/코드/테스트 기반 사실]
  Source: `<source-id>`

## Interpretation
- [내가 이해한 의미, 내 프로젝트에 대한 함의]

## Hypotheses
- [아직 검증되지 않은 추정] ⚠️
  Status: Needs verification
```

**② 기존 내용과 충돌 감지**

`references/conflict-guide.md`를 참조해 기존 내용과 비교한다.

충돌이 확실할 때:
```markdown
## Superseded Notes
- Old: [기존 설명]
- New: [새 설명]
- Source: `<source-id>`
```

충돌이 불확실할 때:
```markdown
## Possible Conflict
기존 문서에서는 [A]라고 정리했지만, 새 source는 [B]처럼 보인다.
추가 확인 필요. Source: `<source-id>`
```

**③ Sources 섹션 유지**

```markdown
## Sources
- `<source-id>`
```

**④ 내 프로젝트에 대한 의미 추가**

```markdown
## Implications for My AI Agent Project
- [이 내용이 내 프로젝트에서 의미하는 것]
```

**⑤ 버전/날짜 정보 기록**

```markdown
## Source Code References
- Repo: <repo>
- Commit: <SHA 또는 UNKNOWN>
- Files: <관련 파일>
```

---

## 6단계: _open_questions.md 업데이트

업데이트 과정에서 발견된 미해결 질문을 `docs/wiki/_open_questions.md`에 추가한다.

- source를 읽고도 애매한 점
- 추가 source 코드 확인이 필요한 부분
- 다음 학습 루프의 출발점이 될 질문

```markdown
## [Framework 이름]
- [새 미해결 질문] — Source: `<source-id>`
```

---

## 7단계: 업데이트 후 체크리스트

`references/update-checklist.md`를 참조해 완료 전 검증한다.

```
✅ 체크리스트
  [ ] 출처(source_id)가 모든 주요 claim에 연결되어 있는가?
  [ ] source_id가 raw_manifest.yml에 등록되어 있는가?
  [ ] 사실 / 해석 / 가설이 분리되어 있는가?
  [ ] 기존 내용과 충돌 여부를 확인했는가?
  [ ] 충돌이 있으면 Superseded 또는 Possible Conflict로 표시했는가?
  [ ] Open Questions를 업데이트했는가?
  [ ] 관련 페이지에 wikilink를 추가했는가?
  [ ] 불필요하게 새 페이지를 만들지 않았는가?
  [ ] 버전/날짜/commit 정보가 있는가?
  [ ] _index.md 갱신이 필요한 새 페이지가 있으면 반영했는가?
```

체크리스트 결과를 출력한다. 미통과 항목이 있으면 수정 후 재확인한다.

---

## 완료 출력

```
✅ Wiki 업데이트 완료

수정된 파일:
  - [파일 경로]
  - [파일 경로]

추가된 Open Questions: [n]개
Source ID: <source-id>

다음 단계:
  [ ] git diff로 변경 내용 리뷰
  [ ] 추가 필요 source: [있으면 목록]
```

---

## 주의 사항

- 사용자가 확인하기 전에 파일을 수정하지 않는다. (4단계 계획 승인 필수)
- 기존 내용을 조용히 덮어쓰지 않는다. 충돌은 반드시 표시한다.
- 원문 사실과 내 해석을 섞지 않는다.
- 확인하지 않은 소스 코드를 확인했다고 주장하지 않는다.
- 새 페이지는 꼭 필요한 경우에만 만든다.
- 블로그/의견성 source는 신뢰도를 낮게 표시한다.
- 한 번에 너무 많은 페이지를 수정하지 않는다. 작고 검토 가능하게 유지한다.

---

## 레퍼런스 파일

| 파일 | 읽는 시점 |
|------|-----------|
| `skills/update-wiki/references/source-type-trust-levels.md` | 1단계: source 분류 시 |
| `skills/update-wiki/references/source-summary-template.md` | 2단계: source summary 생성 시 |
| `skills/update-wiki/references/conflict-guide.md` | 5단계: 충돌 감지 시 |
| `skills/update-wiki/references/update-checklist.md` | 7단계: 완료 검증 시 |
