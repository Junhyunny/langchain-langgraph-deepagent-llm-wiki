---
type: code_map
framework: Deep Agents
status: partial
confidence: medium
last_reviewed: 2026-06-06
sources:
  - deepagents-agents-md-contributing-2026-06-06
---

# Deep Agents Contributing Guide

## Summary

Deep Agents 오픈소스 기여 방법 정리. 개발 환경 설정부터 PR 제출까지의 전체 절차.
저장소: `https://github.com/langchain-ai/deepagents`

Source: `deepagents-agents-md-contributing-2026-06-06`

## 저장소 구조 (monorepo)

```
libs/
├── deepagents/   ← Core SDK — create_deep_agent, middleware, backends
├── acp/          ← Agent Client Protocol 통합
├── evals/        ← 평가 모음 및 Harbor 통합
├── code/         ← 코딩 에이전트 (Textual TUI 인터페이스)
├── cli/          ← 배포용 CLI 도구
└── partners/     ← 공급자(provider) 통합
```

각 패키지는 독립적인 `pyproject.toml`을 가진다.

Source: `deepagents-agents-md-contributing-2026-06-06`

## 개발 환경 설정

**패키지 매니저: `uv`만 사용. `pip`, `poetry`, `conda` 직접 호출 금지.**

```bash
# 의존성 설치 (프로젝트 루트 또는 특정 libs/ 패키지 안에서)
uv sync
uv sync --group test         # 테스트 의존성 포함
uv sync --all-groups         # 모든 그룹 포함

# 가상환경 수동 활성화 불필요 — uv run으로 바로 실행
uv run python my_script.py
```

Python 버전 요구사항은 각 패키지의 `pyproject.toml` → `requires-python` 확인.

Source: `deepagents-agents-md-contributing-2026-06-06`

## 테스트 실행

```bash
# 단위 테스트 전체 (네트워크 없음)
make test

# 특정 파일만
uv run --group test pytest tests/unit_tests/test_specific.py

# 통합 테스트 (네트워크 허용)
uv run --group test pytest tests/integration_tests/
```

**테스트 규칙:**
- 모든 새 기능 및 버그 수정 → 단위 테스트 작성 필수
- `tests/unit_tests/` — 외부 네트워크 금지
- `tests/integration_tests/` — 네트워크 허용
- 테스트 파일 경로는 소스 코드 구조를 반영해야 한다

Source: `deepagents-agents-md-contributing-2026-06-06`

## 코딩 스타일 / 린트 / 포맷

```bash
make lint     # ruff로 린트 검사
make format   # ruff로 자동 포맷
```

**코드 표준:**
- 모든 Python 코드에 타입 힌트 + 반환 타입 필수
- Google 스타일 docstring
- 함수가 20줄 초과 시 분해 고려
- `Any` 타입 회피
- 린트 억제: 파일 전체보다 인라인 `# noqa: RULE` 선호

Source: `deepagents-agents-md-contributing-2026-06-06`

## 브랜치 및 커밋 규칙

**브랜치 명명:** `<github-username>/<scope>/<short-description>`
```
# 예시
mdrxy/sdk/concrete-toolruntime-middleware-tools
junhyun/evals/add-bfcl-benchmark-case
```

**커밋 메시지:** Conventional Commits 규칙 준수
```
feat(sdk): add new middleware hook
fix(evals): correct tool call ratio calculation
docs(sdk): update FilesystemMiddleware docstring
```

Source: `deepagents-agents-md-contributing-2026-06-06`

## PR 제출 절차

### PR 제목 형식
```
type(scope): description
```
- 첫 글자 소문자 (고유명사 제외)
- 코드 항목은 백틱: `` feat(sdk): add `FilesystemMiddleware` execute hook ``

### PR 설명 작성
```markdown
Closes #123
---

**Why**: 기존 execute tool이 sandbox 없이 호출 시 에러를 던짐.
**Solution**: `wrap_model_call`에서 `supports_execution()` 체크 후 tool 제거.
```

- 이슈 종료: 맨 위에 `Closes #번호`
- "왜"를 설명 (what이 아닌 why)
- 라인 번호/전체 파일 경로 언급 금지 (변경될 수 있음)

### 머지 전 체크리스트
- [ ] 공개 API 서명 변경 여부 확인
- [ ] 타입 힌트 추가됨
- [ ] 단위 테스트 작성됨
- [ ] `make lint` / `make format` 통과

Source: `deepagents-agents-md-contributing-2026-06-06`

## Good First Issues 찾기

GitHub 이슈 탭에서 필터:
```
is:open is:issue label:"good first issue"
```

이슈 템플릿 종류:
- `.github/ISSUE_TEMPLATE/bug-report.yml`
- `.github/ISSUE_TEMPLATE/feature-request.yml`
- `.github/ISSUE_TEMPLATE/privileged.yml`

Source: `deepagents-agents-md-contributing-2026-06-06`

## Maintainer 소통 팁

- PR 오픈 전에 먼저 이슈를 열어 방향 확인 권장 (대규모 변경의 경우)
- 관련 레이블 `label:"good first issue"` 이슈부터 시작
- PR 설명에 "이 변경이 필요한 이유"를 구체적으로 적기

**소스 필요:** maintainer 소통 채널(Discord, Slack 등)은 현재 미확인

## 기여 실전 사례

- [[LangGraph issue 5225 pydantic default factory]] — LangGraph PR 기여 사례 (이슈 분석 → 소스 추적 → 테스트 확인)
  이 사례에서 확인된 공통 패턴: 이슈 재현 → 관련 소스 파일 추적 → 테스트 찾기 → 수정 → 단위 테스트 작성

## Source Code References

- Repo: `https://github.com/langchain-ai/deepagents`
- Files:
  - `AGENTS.md` — 기여 가이드, 브랜치/커밋/PR 규칙, 개발 환경 설정
  - `.pre-commit-config.yaml` — pre-commit hooks 설정
  - `libs/deepagents/pyproject.toml` — SDK 패키지 의존성

## Related Pages

- [[Deep Agents]]
- [[Deep Agents Code Map]]
- [[LangGraph issue 5225 pydantic default factory]]

## Open Questions

- maintainer 소통 채널(Discord/Slack/Forum)이 있는가?
- `libs/evals/` 기여 시 Harbor 로컬 설치가 필요한가?
- `libs/code/` (터미널 에이전트)는 SDK와 별도 기여 프로세스가 있는가?
- pre-commit hooks (`ruff`, `mypy` 등) 구체적 설정은?

## Sources

- `deepagents-agents-md-contributing-2026-06-06`
