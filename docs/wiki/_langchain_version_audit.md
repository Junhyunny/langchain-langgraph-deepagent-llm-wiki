---
type: decision
status: verified
confidence: high
updated_at: 2026-07-30
last_reviewed: 2026-07-30
langchain_version: 1.3.14
langchain_core_version: 1.5.2
langgraph_version: 1.2.10
managed_file_count: 208
inventory_sha256: "700698dd10a9cfc5a23b6dac98dae5c773cb4f8852ce2a955913f33dbbd74fb9"
sources:
  - langchain-pypi-1-3-14-2026-07-30
  - langchain-source-1-3-14-2026-07-30
  - langchain-core-source-1-5-2-2026-07-30
  - langchain-docs-event-streaming-2026-07-30
---

# LangChain version audit

## Summary

2026-07-30 기준 저장소 전체 관리 파일을 LangChain 최신 버전 관점에서
감사했다. 이전 가상환경의 `langchain==1.3.1`은 최신 안정판이 아니었고,
공식 PyPI의 최신 안정판 `1.3.14`로 올렸다.

현재 해석된 핵심 버전:

| Package | Version |
|---------|---------|
| `langchain` | `1.3.14` |
| `langchain-core` | `1.5.2` |
| `langgraph` | `1.2.10` |
| `deepagents` | `0.6.3` |

## Scope

감사 inventory는 Git이 추적하는 파일과 ignore되지 않은 새 파일을 합친 뒤 이
감사 문서 자체를 제외한 208개 파일이다. `.git/`, `.venv/`, cache,
`__pycache__`처럼 저장소가 관리하지 않는 파일은 inventory에 포함하지 않는다.

전체 파일은 다음처럼 처리했다.

- LangChain API·소스·문서 주장을 포함한 파일: 최신 공식 문서, 1.3.14 tag,
  1.5.2 core tag, 설치된 API signature와 대조했다.
- 실행 예제: 모든 Python 파일을 compile하고, `langchain_core`,
  `langgraph_core`, `deepagents_core`, `research_agent_comparison`의 실행
  가능한 예제를 전부 실행했다.
- 재현: pending-writes 재현은 1.2.10에서 assertion을 통과했고, issue #5225
  default-factory 버그는 1.2.10에서도 재현됐다.
- 과거 실험·source summary: 당시 버전의 관찰값은 역사적 근거이므로
  1.3.14로 덮어쓰지 않았다. 현재 기준과 충돌하는 경우 “오래됨 / 이력
  보존” 표시 또는 최신 source summary 링크를 추가했다.
- 설정·skill·GitHub 템플릿·빈 placeholder 등 LangChain 런타임 내용과
  무관한 파일: version 영향 없음으로 분류했다.

## Material updates

- [[LangChain]], [[LangChain Code Map]], [[LangChain create_agent flow]]에
  1.3.14/1.5.2 기준과 tag commit을 고정했다.
- [[Event Streaming]]에 v3 권장과 `Runnable.stream_events`의 v2 기본값을
  구분했다.
- [[PIIMiddleware]]의 stream transformer 기반 PII 보호를 추가했다.
- [[ModelFallbackMiddleware]]의 provider별 `cache_control` 정리를 추가했다.
- [[Memory]]와 [[SummarizationMiddleware]]의 잘못된 import 및 `keep`
  tuple 예제를 고쳤다.
- 새 공개 API인 [[ProviderToolSearchMiddleware]]와
  [[ToolErrorMiddleware]] 페이지를 추가했다.
- 실제 최신 저장소 구조에 맞게 Runnable과 v1 agent 소스 경로를 고쳤다.
- 누락된 manifest source 3개와 최신 release source 4개를 등록하고 중복 source
  ID를 병합했다.

## Rework guard

`inventory_sha256`은 감사 문서를 제외한 전체 관리 파일의 경로와 내용을
순서대로 해시한 값이다. 다음 명령이 성공하면 이 감사 이후 관리 파일이
바뀌지 않은 상태다.

```bash
source .venv/bin/activate
python scripts/check_langchain_version_audit.py --check
```

명령이 `audit_status: stale`을 출력하면 파일이 추가·삭제·변경된 것이므로,
변경된 파일의 LangChain 영향만 다시 검토한 뒤 이 문서의
`managed_file_count`, `inventory_sha256`, `updated_at`을 갱신한다.

단, 해시 일치는 “2026-07-30 당시 검토 상태가 유지됨”을 뜻할 뿐 PyPI에 더
새로운 버전이 나오지 않았다는 뜻은 아니다. 최신 버전 확인 시에는 공식
PyPI를 다시 조회해야 한다.

## Validation

- `python -m compileall -q examples reproductions scripts` — 통과
- 전체 실행 가능한 예제 — 통과
- pending writes reproduction — 통과
- issue #5225 reproduction — 1.2.10에서도 버그 재현
- YAML frontmatter parse — 통과
- manifest source ID uniqueness — 통과
- frontmatter source ID resolution — 통과
- `git diff --check` — 통과
- `python -m pytest -q reproductions` — `8 passed, 4 xfailed`
  (`pytest==9.1.1`; xfail은 issue #5225의 알려진 버그 계약)

## Coverage sync

새 페이지는 `_index.md`에 연결했다. `_book_roadmap.md`에는 새 페이지를
참조하는 `위키:` 행이 없으므로 준비도 기호 변경 대상이 없다.

## Sources

- `langchain-pypi-1-3-14-2026-07-30`
- `langchain-source-1-3-14-2026-07-30`
- `langchain-core-source-1-5-2-2026-07-30`
- `langchain-docs-event-streaming-2026-07-30`
