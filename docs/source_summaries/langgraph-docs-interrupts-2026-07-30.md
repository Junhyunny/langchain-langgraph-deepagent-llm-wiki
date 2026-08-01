---
type: source_summary
source_id: langgraph-docs-interrupts-2026-07-30
title: "LangGraph — Interrupts documentation"
framework: LangGraph
retrieved_at: 2026-07-30
status: verified
confidence: high
---

# Source Summary: LangGraph — Interrupts

## Source Info
- **Source ID:** `langgraph-docs-interrupts-2026-07-30`
- **Type:** official_docs
- **URL:** https://docs.langchain.com/oss/python/langgraph/interrupts
- **Retrieved At:** 2026-07-30
- **Version / Commit:** UNKNOWN (docs 사이트, 버전 표기 없음)

---

## Key Facts
<!-- 원문에 있는 내용만. 추론 금지. -->
- `interrupt()`는 노드 내 임의 지점에서 실행을 멈추고, JSON 직렬화 가능한 값을 caller에게 노출한다. 재개 시 그 값이 `interrupt()` 호출의 반환값이 된다.
- interrupt 사용에는 (1) checkpointer, (2) config의 `thread_id`, (3) `interrupt()` 호출이 필요하다.
- 재개는 같은 `thread_id`로 `Command(resume=...)`를 다시 전달해서 한다. resume 값이 `interrupt()`의 반환값이 된다.
- **권장 실행 방식은 event streaming**: `graph.stream_events(..., version="v3")`. typed projections를 제공한다 — `stream.interrupts`(interrupt payload 튜플), `stream.interrupted`(bool), `stream.output`(최종 상태), `stream.messages`(토큰 단위 메시지), `stream.values`(step별 상태 스냅샷), `stream.subgraphs[*].messages`.
- 기본 `graph.invoke(...)`도 여전히 동작하며 interrupt는 `result["__interrupt__"]`로 노출된다. streamed projection이 필요 없을 때 사용.
- `Command(resume=...)`는 invoke/stream/stream_events 입력으로 쓰이는 **유일한** Command 패턴이다. 나머지 `Command(update=/goto=/graph=)`는 노드 함수 반환 전용이다. 멀티턴 대화 지속에는 `Command(update=...)`가 아니라 일반 입력 dict를 써야 한다.
- **재개 시 노드는 처음부터 재실행된다** — `interrupt` 호출 라인이 아니라 노드 시작점부터. interrupt 앞의 코드는 다시 실행된다.
- **다중 interrupt:** 병렬 브랜치가 동시에 interrupt하면 `Command(resume={interrupt_id: value})` 맵으로 한 번에 재개한다. `stream.interrupts`의 각 `Interrupt`는 `.id`와 `.value`를 가진다.
- **입력 검증 패턴:** 노드 내 `while True` + `interrupt()` 루프 금지(재실행마다 지수적 재실행). 대신 노드당 `interrupt()`를 정확히 1회 호출하고, 무효 시 `pending_question`을 state에 저장 후 conditional edge로 노드에 되돌아오게 한다.
- **Rules of interrupts:**
  - `interrupt`를 bare try/except로 감싸지 말 것 (특수 예외를 잡아버려 interrupt가 전달 안 됨). 구체 예외 타입만 잡을 것.
  - 노드 내 interrupt 호출 순서를 바꾸거나 조건부로 건너뛰지 말 것 — 매칭은 **엄격히 index 기반**.
  - 복잡한 값(함수/클래스 인스턴스) 전달 금지 — 직렬화 불가.
  - `interrupt` 앞의 side effect는 idempotent해야 함 (노드 재실행으로 중복 실행됨). side effect는 interrupt 뒤에 두거나 별도 노드로 분리.
- subgraph를 함수처럼 호출한 경우, 부모 graph는 subgraph를 호출한 노드의 **시작점부터** 재개하고, subgraph도 interrupt가 있던 노드의 시작점부터 재개한다.
- **Static interrupts(`interrupt_before`/`interrupt_after`)**: compile 시 또는 runtime에 노드 실행 전/후 중단점을 건다. checkpointer 필요, `None` 입력으로 재개. **HITL에는 비권장**이며 디버깅/breakpoint 용도. LangSmith Studio UI에서도 설정 가능.

---

## Important Terms
- [[HumanInTheLoop]] — interrupt 기반 사람 개입 패턴.
- `interrupt()` — 노드 내 동적 중단 함수.
- `Command(resume=...)` — interrupt 재개용 유일한 입력 Command.
- `stream_events(version="v3")` — typed projection 기반 권장 실행 API.
- static interrupts — `interrupt_before`/`interrupt_after`, 디버깅용 중단점.

---

## Interpretation
<!-- 내가 이해한 의미. 원문과 분리. -->
- HITL의 권장 진입점이 `invoke(None, ...)`/`Command(resume=...)` + `__interrupt__` 조회에서 `stream_events(version="v3")` + typed projections로 이동했다. 위키의 기존 interrupt 예시(`graph.invoke(Command(resume=...), config)`)는 여전히 유효하지만 "구 API로 여전히 지원됨"으로 격하해 표기하는 것이 정확하다.
- "노드는 처음부터 재실행"과 "index 기반 매칭"은 checkpoint replay 모델의 직접적 귀결이다 — Checkpointing 페이지의 replay 서술과 일관된다.
- 입력 검증에서 conditional edge를 권장하는 것은 재실행 모델과 직렬화 제약을 함께 회피하는 패턴이다.

---

## Implications for My AI Agent Project
- HITL 실험 코드는 `stream_events(version="v3")`의 `stream.interrupted`/`stream.interrupts`를 표준 루프로 삼는 게 최신 문서와 정합적이다.
- interrupt 앞 side effect의 idempotency는 실제 버그의 흔한 원인 — 실험 시 반드시 검증 대상.
- 병렬 fan-out + interrupt를 쓰면 resume를 `{id: value}` 맵으로 다뤄야 한다.

---

## Open Questions
- `stream_events(version="v3")`의 typed projection 객체(`stream.output`/`interrupts`/...)의 소스 구현 위치는? (Needs Source)
- `version="v1"/"v2"`와의 차이 및 마이그레이션 가이드는? (Needs Source)
- `Interrupt.id`가 병렬 브랜치에서 생성되는 규칙(결정성)은 소스 어디서 정해지는가? (Needs Source)

---

## Used By
- [[Checkpointing]]
- [[HumanInTheLoop]]

---

## Notes
- 이 페이지는 `langgraph-source-pregel-interrupts-2026-05-23`(소스 기반 interrupt 요약)과 상호 보완. 소스 요약은 `interrupt()` 내부 구현(scratchpad, resume counter)을, 이 문서는 사용자 API와 규칙을 다룬다.
