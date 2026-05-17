# Wiki 성숙도 평가 기준 (Maturity Rubric)

wiki 상태를 평가할 때 이 기준을 사용한다.

---

## 초기 (Research Plan 모드 적용)

다음 중 하나 이상 해당:

- `docs/raw_manifest.yml`의 `sources` 배열이 비어 있거나 관련 항목 없음
- `docs/source_summaries/`에 질문 주제 관련 파일 없음
- 질문 주제에 해당하는 `docs/wiki/` 페이지가 없거나 `draft` + `confidence: low` 상태
- wiki 페이지에 `## Sources` 섹션이 없거나 source_id 없음

→ AI 역할: **연구 계획자 + 위키 구조 관리자**
→ 응답 목표: 어떤 source를 언제 모아야 하는지 명확히 제시

---

## 중기 (Partial Answer 모드 적용)

다음 중 하나 이상 해당:

- 질문 주제 관련 source summary가 1개 이상 존재
- wiki 페이지가 존재하지만 `status: draft` 또는 일부 섹션 미완성
- `raw_manifest.yml`에 관련 source가 등록되어 있음
- wiki 페이지에 일부 source_id가 있지만 모든 주장을 커버하지 못함

→ AI 역할: **Source 기반 설명자**
→ 응답 목표: 확인된 것과 부족한 것을 명확히 구분하여 답변

---

## 후기 (Wiki Answer 모드 적용)

다음 모두 해당:

- 질문 주제 관련 wiki 페이지가 `status: verified` 또는 실질적 내용 보유
- 핵심 주장에 source_id가 연결되어 있음
- 관련 source summary가 존재하고 wiki 페이지가 이를 참조
- `_open_questions.md`에서 해당 질문이 해결된 상태

→ AI 역할: **개인 연구 조수**
→ 응답 목표: wiki 기반 정확한 답변 + 남은 열린 질문 확인
