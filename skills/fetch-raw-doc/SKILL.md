---
name: fetch-raw-doc
description: >
  Use this skill when the user wants to save official documentation, source code notes,
  or any reference material as a raw file for the LLM wiki.
  Trigger phrases: "raw 파일 만들어줘", "문서 저장해줘", "fetch doc", "raw로 저장",
  "공식 문서 가져와", "이 URL 저장해줘", "raw 템플릿 만들어줘", "manual template".
user-invocable: true
---

# fetch-raw-doc

공식 문서나 소스 자료를 **출처 메타데이터와 함께 raw 파일로 저장**하고, `docs/raw_manifest.yml`을 갱신하는 스킬.

## 지원 에이전트

이 스킬은 다음 에이전트에서 동작한다.

| 에이전트 | 내용 가져오기 수단 | 진입점 |
|----------|-------------------|--------|
| GitHub Copilot CLI | `web_fetch` 내장 도구 | `/fetch-raw-doc` 또는 자연어 |
| Claude Code | `web_fetch` / `curl` (bash) | `/fetch-raw-doc` (`.claude/commands/`) |
| Codex | `curl` via bash | 자연어 또는 `AGENTS.md` 참조 |

---

## 두 가지 모드

| 모드 | 트리거 | 동작 |
|------|--------|------|
| **auto** | URL만 제공 | URL에서 본문 자동 추출 후 저장 |
| **template** | "template" / "수동" / "manual" / "직접 붙여넣기" 언급 | 빈 템플릿 파일 생성 |

---

## 전체 흐름

```
1단계: 입력 수집
     ↓
2단계: 메타데이터 결정
     ↓
3단계: 내용 확보 (auto: URL 가져오기 / template: 빈 파일)
     ↓
4단계: raw 파일 생성
     ↓
5단계: raw_manifest.yml 갱신
     ↓
6단계: 다음 단계 안내
```

---

## 1단계: 입력 수집

다음 정보를 사용자로부터 확인한다. 없으면 물어본다.

**필수:**
- `url` — 저장할 문서의 URL

**선택 (없으면 자동 추론):**
- `source-id` — 고유 ID (없으면 자동 생성)
- `framework` — LangGraph / LangChain / Deep Agents / General (URL에서 자동 감지)
- `title` — 문서 제목 (auto 모드에서는 페이지 `<title>` 또는 `<h1>`에서 추출)
- `type` — 소스 유형 (기본값: `official_docs`)
- `notes` — 추가 메모

**모드 판별:**
- "template", "수동", "manual", "직접 붙여넣기" 언급 → **template 모드**
- 그 외 → **auto 모드**

---

## 2단계: 메타데이터 결정

### framework 자동 감지 (URL 기반)

| URL 패턴 | framework |
|----------|-----------|
| `langgraph` 포함 | LangGraph |
| `langchain` 포함 | LangChain |
| `deepagent` / `deep-agent` / `deep_agent` 포함 | Deep Agents |
| 그 외 | General |

### source-id 자동 생성 규칙

형식: `<framework-slug>-<type-slug>-<topic-slug>-<YYYY-MM-DD>`

예시:
- `langgraph-docs-checkpointing-2026-05-18`
- `langchain-docs-tool-calling-2026-05-18`
- `deepagents-docs-overview-2026-05-18`

규칙:
- 소문자 kebab-case만 사용
- 공백, 특수문자 불가
- 날짜는 오늘 날짜

### 출력 경로

```
docs/raw/official/<framework-lowercase>/<source-id>.md
```

예: `docs/raw/official/langgraph/langgraph-docs-checkpointing-2026-05-18.md`

---

## 3단계: 내용 확보

### auto 모드 — URL 가져오기

에이전트에 따라 적합한 수단으로 URL을 가져온다.

**우선순위:**
1. `web_fetch` 내장 도구가 있으면 사용 (Copilot CLI, Claude Code)
2. 없으면 bash에서 `curl -sL <url>` 사용 (Codex)

**본문 추출 우선순위:**
1. `<main>` 태그
2. `<article>` 태그
3. `role="main"` 속성 요소
4. `.md-content__inner` (MkDocs Material — LangChain/LangGraph 공식 문서)
5. `.rst-content` (Sphinx/ReadTheDocs)
6. `#main-content`, `#content`, `.content`
7. 위 모두 없으면 `<body>`

**제거할 노이즈:**
- `<nav>`, `<header>`, `<footer>`
- sidebar, breadcrumb, cookie banner
- "Edit this page", "Give feedback" 링크
- 중복 heading

**제목 추출:** `<title>` 또는 첫 번째 `<h1>`. " - Framework Name" 같은 suffix는 제거.

**HTML → Markdown 변환:**
- 코드 블록 유지 (백틱 사용)
- 링크 유지
- 테이블 유지
- 불필요한 HTML 태그 제거

### template 모드

내용 없이 파일을 생성한다. `<!-- Paste content here -->` 플레이스홀더를 삽입한다.

---

## 4단계: raw 파일 생성

`references/raw-file-template.md`의 형식을 따른다.

- 출력 디렉토리가 없으면 먼저 생성한다.
- **이미 파일이 존재하는 경우:** 덮어쓰지 않는다. 사용자에게 알리고 중단한다. 새 버전이 필요하면 날짜를 바꿔 새 파일명으로 저장하라고 안내한다.

`capture_method` 값:
- auto 모드 → `web_fetch` 또는 `curl_fetch`
- template 모드 → `manual_browser_copy`

---

## 5단계: raw_manifest.yml 갱신

`references/manifest-entry-template.yml`의 형식을 따라 `docs/raw_manifest.yml`의 `sources:` 배열에 항목을 추가한다.

- **중복 체크:** `id`가 이미 존재하면 추가하지 않고 사용자에게 알린다.
- 갱신 방법: `sources:` 배열의 마지막 항목 뒤에 새 항목을 삽입한다.

---

## 6단계: 다음 단계 안내

```
✅ Raw 파일 저장 완료

📄 파일: docs/raw/official/<framework>/<source-id>.md
🔖 Source ID: <source-id>
```

template 모드인 경우 추가:
```
📋 다음: 파일을 열고 '<!-- Paste content here -->' 위치에 본문을 붙여넣으세요.
```

공통 다음 단계:
```
다음 단계:
  1. source summary 생성:
       docs/source_summaries/<source-id>.md
  2. wiki 페이지 반영 후 Sources 섹션에 '<source-id>' 추가
```

---

## 주의 사항

- raw 파일은 `.gitignore`에 의해 Git에 추적되지 않는다. `raw_manifest.yml`만 Git에 남는다.
- 전체 문서 사이트를 스크래핑하지 않는다. 오늘 공부하는 주제와 직접 관련된 페이지만 저장한다.
- raw 파일에는 원문만 넣는다. 내 해석이나 요약은 `source_summaries/`에 별도 작성한다.
- 공개 레포에 원문 전체를 올리는 것은 저작권 문제가 될 수 있다. raw는 로컬 전용으로 유지한다.

---

## 레퍼런스 파일

| 파일 | 읽는 시점 |
|------|-----------|
| `skills/fetch-raw-doc/references/raw-file-template.md` | 4단계: raw 파일 생성 시 |
| `skills/fetch-raw-doc/references/manifest-entry-template.yml` | 5단계: manifest 갱신 시 |
