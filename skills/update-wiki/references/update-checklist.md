# Wiki 업데이트 후 체크리스트

wiki 업데이트 완료 전 반드시 확인한다.

---

## 출처 추적

- [ ] 모든 주요 claim에 `source_id`가 연결되어 있는가?
- [ ] 해당 `source_id`가 `docs/raw_manifest.yml`에 등록되어 있는가?
- [ ] source summary (`docs/source_summaries/`) 파일이 있는가?

## 내용 품질

- [ ] Verified Facts / Interpretation / Hypotheses가 분리되어 있는가?
- [ ] 가설이나 추정에는 `⚠️` 또는 `Status: Needs verification`이 붙어 있는가?
- [ ] LLM 일반 지식이 wiki에 직접 들어가지 않았는가?

## 충돌 처리

- [ ] 기존 내용과 충돌하는 부분을 확인했는가?
- [ ] 충돌이 있으면 `Superseded Notes` 또는 `Possible Conflict`로 표시했는가?
- [ ] 기존 내용을 조용히 삭제하지 않았는가?

## 구조

- [ ] `## Sources` 섹션에 `source_id`가 추가되었는가?
- [ ] `## Open Questions`에 새 미해결 질문이 추가되었는가?
- [ ] 관련 개념에 `[[wikilink]]`가 연결되어 있는가?
- [ ] `docs/wiki/_open_questions.md`에 새 질문이 추가되었는가?

## 범위 관리

- [ ] 불필요하게 새 페이지를 만들지 않았는가?
- [ ] 새 페이지를 만들었다면 `docs/wiki/_index.md`를 갱신했는가?
- [ ] 변경이 작고 한 번에 리뷰 가능한 크기인가?

## 버전 정보

- [ ] `retrieved_at` / `framework_version` / `repo_commit`이 기록되어 있는가?
- [ ] 버전이 불명확하면 `UNKNOWN`으로 표시했는가?

---

## 빠른 리뷰 프롬프트

업데이트 후 AI에게 검증을 시킬 때:

```
방금 업데이트한 wiki 변경사항을 리뷰해줘.
확인 항목:
- 출처 누락
- 과도한 추론 (Interpretation을 Fact처럼 쓴 경우)
- 기존 내용과의 충돌 (Possible Conflict 미표시)
- 깨진 wikilink
- Open Questions 누락
- LLM 일반 지식이 source 없이 들어간 경우
```
