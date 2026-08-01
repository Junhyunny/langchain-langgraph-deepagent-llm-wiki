---
type: source_summary
source_id: langgraph-docs-checkpointers-2026-07-30
title: "LangGraph — Checkpointers documentation"
framework: LangGraph
retrieved_at: 2026-07-30
status: verified
confidence: high
---

# Source Summary: LangGraph — Checkpointers

## Source Info
- **Source ID:** `langgraph-docs-checkpointers-2026-07-30`
- **Type:** official_docs
- **URL:** https://docs.langchain.com/oss/python/langgraph/checkpointers
- **Retrieved At:** 2026-07-30
- **Version / Commit:** UNKNOWN (docs 사이트, 버전 표기 없음)

---

## Key Facts
<!-- 원문에 있는 내용만. 추론 금지. -->
- 이 페이지는 구 `persistence` 페이지의 상세 checkpointer 내용을 흡수한 신규 페이지다 (threads, checkpoints, super-steps, StateSnapshot 필드, get_state, get_state_history, replay, update_state, durability modes).
- persistence 계층은 두 개의 storage 추상화 위에 구축된다: **Checkpoints 테이블**(super-step당 1행, `channel_values`/`channel_versions`/`versions_seen` 및 parent 링크 저장)과 **Writes 테이블**(super-step 내 node output당 1행, `(task_id, channel, value)` 저장).
- `checkpoint_ns`: `""`는 부모(root) graph, `"node_name:uuid"`는 subgraph. 중첩 subgraph는 `|`로 join된다 (예: `"outer:uuid|inner:uuid"`).
- **Serializer:** 기본 serializer는 `JsonPlusSerializer`이며 내부적으로 ormsgpack + JSON을 사용한다. LangChain/LangGraph primitives, datetime, enum, Pydantic v2, dataclass, numpy 등을 처리한다.
- msgpack이 지원하지 않는 타입(예: Pandas DataFrame)은 `JsonPlusSerializer(pickle_fallback=True)`로 pickle fallback을 켤 수 있다.
- **암호화:** `EncryptedSerializer`를 saver의 `serde` 인자로 전달하면 모든 저장 상태를 암호화한다. `EncryptedSerializer.from_pycryptodome_aes()`는 `LANGGRAPH_AES_KEY` 환경변수(또는 `key` 인자)에서 AES 키를 읽는다. LangSmith에서는 `LANGGRAPH_AES_KEY`가 있으면 암호화가 자동 활성화된다. 다른 방식은 `CipherProtocol` 구현으로 가능.
- **Checkpointer 라이브러리:** `langgraph-checkpoint`(base + `InMemorySaver` 내장), `langgraph-checkpoint-sqlite`(`SqliteSaver`/`AsyncSqliteSaver`), `langgraph-checkpoint-postgres`(`PostgresSaver`/`AsyncPostgresSaver`, LangSmith에서 사용), `langchain-azure-cosmosdb`(`CosmosDBSaver`/`CosmosDBSaverSync`, Microsoft Entra ID 인증).
- `BaseCheckpointSaver` 필수 메서드는 `.put`, `.put_writes`, `.get_tuple`, `.list`이며, async 실행 시 `.aput`/`.aput_writes`/`.aget_tuple`/`.alist`가 사용된다. custom saver 구현 시 `adelete_thread`도 필요하다 (누락 시 런타임 `NotImplementedError`).
- custom saver의 `put`은 metadata를 **전체 저장**해야 한다 — LangGraph가 minor 릴리스에서 새 metadata 필드(예: delta channel용 `counters_since_delta_snapshot`)를 추가하므로 unknown key를 버리면 기능이 조용히 깨진다.
- `get_tuple`은 `checkpoint_id`가 있으면 정확히 그 checkpoint를, 없으면 thread+ns의 최신 checkpoint를 반환해야 한다. **specific-id 경로는 time travel과 delta channel 재구성에 필수**이며, 깨지면 delta channel 상태가 조용히 빈 값으로 손상된다.
- `checkpoint_id`는 ULID라 사전식 정렬 시 큰 값이 최신이다. "최신 조회"는 `ORDER BY checkpoint_id DESC LIMIT 1`, "id 조회"는 primary key 등치 조회.
- `WRITES_IDX_MAP`(`langgraph.checkpoint.base`)은 특수 채널(`__error__`, `__interrupt__` 등)을 예약된 음수 인덱스로 매핑한다.
- **Durability modes** (least → most durable): `"exit"`(graph 종료 시에만 저장, 최고 성능, 중간 크래시 복구 불가), `"async"`(다음 step 실행 중 비동기 저장, 크래시 시 미기록 위험 소량), `"sync"`(다음 step 전 동기 저장, 최고 내구성).
- **Extended capabilities**(선택, Agent Server 기능 활성화): `adelete_for_runs`(rollback multitask), `acopy_thread`(thread forking), `aprune`(history pruning), `aget_delta_channel_history`(delta channel 재구성). Agent Server가 startup 시 자동 감지한다.
- **DeltaChannel:** checkpoint blob에 전체 값 대신 sentinel(`MISSING`)만 저장하고, ancestor writes를 reducer로 replay해 상태를 재구성한다. blob이 step당 O(1)(O(N) 대신). 로딩 시 `saver.get_delta_channel_history(config, channels=[...])`를 호출하며, 반환값은 채널별 `writes`(오래된 순)와 선택적 `seed`(가장 가까운 `_DeltaSnapshot` blob). 런타임은 `channel.from_checkpoint(seed)` + `channel.replay_writes(writes)`로 복원한다.
- `BaseCheckpointSaver`는 기본 `get_delta_channel_history`를 제공하며 이는 정확한 `get_tuple` 구현에 의존한다 (ancestor를 parent 방향으로 walk). 성능을 위해 두 쿼리로 override 가능.
- delta channel pruning 주의: `_DeltaSnapshot`까지의 ancestor write chain을 지우면 안 된다. 안전 옵션은 (1) walk 후 non-deletable 표시, (2) pruning 전 snapshot 강제, (3) delta thread pruning 생략.
- **Conformance suite:** `pip install langgraph-checkpoint-conformance` → `langgraph.checkpoint.conformance`의 `checkpointer_test`/`validate`로 전체 계약(delta channel history 포함) 검증. extended capability 자동 감지 후 관련 테스트 실행. CI에서 실행 권장.

---

## Important Terms
- [[Checkpointing]] — super-step 경계마다 graph state를 저장하는 persistence 메커니즘.
- `JsonPlusSerializer` — 기본 직렬화기 (ormsgpack + JSON, pickle_fallback 옵션).
- `EncryptedSerializer` — 저장 상태 AES 암호화 serializer (`LANGGRAPH_AES_KEY`).
- `BaseCheckpointSaver` — checkpoint backend 인터페이스 (`put`/`put_writes`/`get_tuple`/`list`).
- `DeltaChannel` — 누적 채널을 delta로 저장하는 reducer 채널.
- `checkpoint_ns` — root graph(`""`) vs subgraph(`node:uuid`) 구분 namespace.
- `WRITES_IDX_MAP` — 특수 채널 → 예약 음수 인덱스 매핑.
- durability mode — `exit`/`async`/`sync` 내구성-성능 트레이드오프.

---

## Interpretation
<!-- 내가 이해한 의미. 원문과 분리. -->
- 문서 구조 변경(persistence → checkpointers 분리)은 LangGraph가 checkpointer를 "설정 옵션"이 아니라 별도 확장 서브시스템(직렬화·암호화·custom backend·conformance)으로 격상했다는 신호로 보인다.
- Serializer/암호화/conformance suite의 문서화는 오픈소스 기여 관점에서 중요하다 — custom saver PR을 낼 때 conformance suite 통과가 사실상의 계약이 된다.
- `get_tuple`의 specific-id 경로가 delta channel 정합성의 단일 실패점이라는 서술은, checkpointer 버그 분석 시 가장 먼저 봐야 할 지점을 알려준다.

---

## Implications for My AI Agent Project
- custom checkpointer를 만들거나 평가한다면 `langgraph-checkpoint-conformance`를 CI에 포함해야 한다.
- 민감 상태를 저장하는 agent라면 `EncryptedSerializer` + `LANGGRAPH_AES_KEY`로 at-rest 암호화를 검토한다.
- 긴 대화(messages 누적) agent는 DeltaChannel로 checkpoint 크기를 O(1)/step으로 억제할 수 있다.
- metadata를 stripping하는 custom saver는 향후 LangGraph 릴리스에서 조용히 깨질 수 있으므로 전체 저장이 원칙.

---

## Open Questions
- 기본 `get_delta_channel_history`가 `BaseCheckpointSaver`에 도입된 정확한 버전/commit은? (Needs Source)
- `CosmosDBSaver`의 Entra ID 인증 흐름과 sync/async 클래스 차이의 소스 구현은? (Needs Source)
- conformance suite가 검증하는 "base capability" 전체 목록과 실패 기준은? (Needs Source)
- `pickle_fallback=True`가 보안/이식성에 주는 실제 영향(RCE 위험 등)에 대한 공식 경고 위치는? (Needs Source)

---

## Used By
- [[Checkpointing]]

---

## Notes
- 이 페이지는 구 `langgraph-docs-persistence-2026-05-20`, `langgraph-docs-durable-execution-2026-05-20`의 상세 내용을 대체/흡수한다. durable-execution URL은 현재 persistence로 308 리다이렉트.
