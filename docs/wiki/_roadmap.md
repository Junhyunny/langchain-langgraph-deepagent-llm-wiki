# 로드맵

## 이 위키의 목적

이 위키는 내가 직접 LangChain, LangGraph, Deep Agents를 학습해서 업스트림에 PR을 제출할 수 있는 기술 수준에 도달하기 위한 학습 지원 자료다.

AI는 참고 자료(wiki 페이지, source summary, 재현 예제)를 준비하는 역할을 하지만, 실제 학습과 기여는 내가 직접 수행한다.
체크 표시는 내가 직접 읽고 이해하거나 코드를 작성한 경우에만 한다.

---

## 현재 목표

아래 능력을 순서대로 키운다. 각 단계는 이전 단계가 충분히 쌓인 뒤 진행한다.

1. 공개 API를 직접 사용해보고 동작을 확인한다
2. 소스 코드를 읽고 공개 API의 내부 구현을 추적한다
3. 테스트를 읽고 어떤 동작이 보장되는지 설명할 수 있다
4. 이슈를 읽고 재현 예제를 스스로 작성한다
5. 소스 코드를 직접 추적해 근본 원인을 분석한다
6. 기존 테스트 패턴을 참고해 새 테스트를 직접 작성한다
7. 패치를 작성하고 검토 가능한 PR을 직접 제출한다

---

## 1단계 — 공개 API 익히기

세 프레임워크의 핵심 API를 직접 사용해보고 어떻게 동작하는지 확인하는 단계다.

- [ ] LangChain: `create_react_agent`, `AgentExecutor` 직접 실행해보기
- [ ] LangGraph: `StateGraph` 정의 → `compile` → `invoke` 직접 실행해보기
- [ ] LangGraph: `MemorySaver`로 체크포인팅 직접 동작 확인
- [ ] Deep Agents: `create_deep_agent` 직접 실행해보기 (패키지 설치 방법 확인 필요)
- [ ] 각 프레임워크에서 도구 등록 및 호출이 어떻게 동작하는지 직접 확인

> 참고 자료 (AI가 준비):
> - `docs/wiki/frameworks/`, `docs/wiki/concepts/`
> - `examples/` 디렉터리

---

## 2단계 — 소스 코드 읽기

공개 API 뒤에서 어떤 코드가 실행되는지 직접 읽는 단계다.

- [ ] LangChain `create_react_agent` 호출 경로를 소스에서 직접 따라가기
- [ ] LangGraph `StateGraph.compile()` 내부 구조를 소스에서 읽기
- [ ] LangGraph `Pregel` 런타임이 어떻게 step을 실행하는지 소스에서 읽기
- [ ] Checkpointing: `BaseCheckpointSaver.put()` 호출 경로를 직접 확인
- [ ] 읽은 파일 경로와 핵심 함수를 `docs/wiki/flows/` 또는 `docs/wiki/codebase/`에 직접 기록

> 참고 자료 (AI가 준비):
> - `docs/wiki/flows/`, `docs/wiki/codebase/`
> - `docs/source_summaries/`

---

## 3단계 — 테스트 읽기

소스 코드와 함께 테스트를 읽고 "어떤 동작이 보장되어야 하는가"를 이해하는 단계다.

- [ ] `test_pregel.py::test_pending_writes_resume` 읽고 무엇을 검증하는지 직접 설명해보기
- [ ] LangGraph 체크포인팅 관련 테스트 3개 이상 읽기
- [ ] LangChain tool calling 관련 테스트 3개 이상 읽기
- [ ] 테스트가 없는 동작이나 엣지 케이스를 스스로 발견하기

---

## 4단계 — 이슈 재현

실제 이슈를 읽고 최소 재현 예제를 직접 작성하는 단계다.

- [ ] LangGraph `help wanted` 이슈 중 하나를 직접 읽기
- [ ] 이슈에서 설명하는 동작을 재현하는 최소 예제를 직접 작성하기
- [ ] 기대 동작과 실제 동작의 차이를 코드로 확인하기
- [ ] 재현 결과를 `reproductions/`에 직접 기록하기

> 참고 자료 (AI가 준비):
> - `reproductions/langgraph_checkpoint_pending_writes/pending_writes_resume.py`
> - `docs/wiki/prs/LangGraph checkpoint pending writes tests documentation PR candidate.md`

---

## 5단계 — 근본 원인 분석 및 PR 제출

이슈의 원인을 소스 코드에서 직접 찾고, 패치를 작성해 PR을 제출하는 단계다.

- [ ] 재현된 이슈의 원인이 되는 코드를 소스에서 직접 찾기
- [ ] 기존 테스트 패턴을 참고해 회귀 테스트 또는 새 테스트를 직접 작성하기
- [ ] 패치 또는 문서 수정 변경사항을 직접 작성하기
- [ ] PR을 직접 fork → branch → commit → open하기
- [ ] 리뷰 피드백을 받고 직접 수정하기

> 첫 번째 시도로 적합한 후보 (난이도 낮음):
> - LangGraph `#5021`: `test_pregel.py`의 `Whats` → `What's` typo 수정 (codespell 이슈, 변경 범위 작고 명확)

---

## 다음으로 읽을 자료

- LangGraph `test_pregel.py` — 이미 `reproductions/`에서 테스트 이름은 확인됨, 직접 전체 읽기
- LangGraph `_loop.py` — `Pregel` step 실행 흐름의 핵심
- LangGraph `_checkpoint.py` — `pending_writes` 처리 경로
- Deep Agents 설치 방법 — 아직 직접 실행 안 해봄
