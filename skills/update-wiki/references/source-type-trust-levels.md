# Source 유형별 신뢰도 기준

source를 wiki에 반영할 때 신뢰도에 따라 표현 강도를 조절한다.

---

## 신뢰도 계층

```
소스 코드 / 테스트 코드
    > 공식 문서
    > Maintainer comment (이슈/PR)
    > Issue discussion
    > 블로그 / 아티클
    > LLM 답변 (wiki에 직접 반영 금지)
```

---

## 유형별 상세

### source_code — High
- 실제 동작의 가장 정확한 근거
- commit SHA를 반드시 기록
- "코드 기준으로 확인됨"으로 표현

### test_code — High
- maintainers가 보장하는 behavior
- 테스트 파일 경로와 함수명 기록
- "테스트 기준으로 검증됨"으로 표현

### official_docs — High (단, 버전 주의)
- public API와 권장 사용법의 기준
- retrieved_at과 URL 필수 기록
- 문서가 바뀔 수 있으므로 날짜 중요
- "공식 문서 기준"으로 표현

### maintainer_comment — Medium-High
- 이슈/PR에서 maintainer가 직접 설명한 내용
- 맥락과 edge case 파악에 유용
- issue/PR 번호와 URL 기록

### issue_discussion — Medium
- 커뮤니티 토론, 재현 사례, 논쟁 파악
- 공식 입장이 아닐 수 있음
- "이슈 토론 기준"으로 표현, 단독 근거로 쓰지 않음

### experiment_log — Medium
- 내가 직접 관찰한 behavior
- 환경, 버전, 재현 코드 기록 필수
- "직접 실험 기준"으로 표현

### blog_article — Low
- 해석/관점 파악에 유용
- 공식 근거로 쓰지 않음
- "외부 해석"으로 표현, Needs Verification 표시 필수

### llm_answer — 사용 금지
- wiki에 직접 반영하지 않음
- wiki 빈 곳을 채우기 위해 LLM 답변을 source로 쓰지 않는다

---

## wiki 표현 예시

```markdown
<!-- High 신뢰도 (공식 문서/소스코드) -->
LangGraph는 durable execution을 위한 런타임을 제공한다.
Source: `langgraph-docs-overview-2026-05-18`

<!-- Medium 신뢰도 (실험/이슈 토론) -->
interrupt/resume은 checkpoint와 연결되어 있는 것으로 보인다.
Source: `langgraph-issue-interrupt-2026-05-18`
Status: Partially verified

<!-- Low 신뢰도 (블로그) -->
## External Interpretation
한 블로그에서는 LangGraph를 "durable orchestration layer"로 해석한다.
다만 이 표현은 공식 문서에서 직접 사용하지 않으며, 추가 확인이 필요하다.
Source: `blog-langgraph-analysis-2026-05-18`
Status: Needs verification
```
