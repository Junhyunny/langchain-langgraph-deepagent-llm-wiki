---
id: langgraph-source-pregel-loop-2026-05-25
date: 2026-05-25
framework: LangGraph
version: 1.2.1
type: source
files:
  - langgraph/pregel/_loop.py
  - langgraph/pregel/main.py
  - langgraph/checkpoint/base/__init__.py
  - langgraph/checkpoint/memory/__init__.py
  - langgraph/pregel/_checkpoint.py
confidence: high
---

# LangGraph Pregel 런타임 소스 서머리

버전 1.2.1 (`/usr/local/lib/python3.11/dist-packages/langgraph/`) 직접 읽기.

---

## 1. `StateGraph.compile()` 내부 — `graph/state.py:1164`

```
StateGraph.compile(checkpointer, interrupt_before, interrupt_after, ...)
  → ensure_valid_checkpointer(checkpointer)          # None/False/saver 정규화
  → self.validate(interrupt=[...])                   # 구조 검사 (_validate.py)
  → output_channels, stream_channels 결정
    - "__root__" (단일 루트 필드) vs 필드 목록
  → CompiledStateGraph(                              # line 1333
      builder=self,
      channels={**self.channels, **self.managed, START: EphemeralValue(input_schema)},
      input_channels=START,
      checkpointer=checkpointer,
      interrupt_before_nodes=interrupt_before,
      interrupt_after_nodes=interrupt_after,
      ...
    )
  → compiled.attach_node(START, None)                # __start__ 노드 등록
  → for key, node in self.nodes.items():
        compiled.attach_node(key, node)              # 각 노드 등록
  → compiled._output_mapper, _state_mapper 설정      # Pydantic/dataclass 출력 변환
  → for start, end in self.edges: compiled.attach_edge(start, end)
  → for start, branches: compiled.attach_branch(start, name, branch)
  → return compiled.validate()                       # Pregel 검증
```

**핵심**: `CompiledStateGraph`는 `Pregel`의 서브클래스. `compile()`은 Pregel 인스턴스를 구성하고 노드/엣지/브랜치를 attach한 뒤 `validate()`로 구조를 검증한다.

---

## 2. `Pregel.stream()` — 실행 진입점 (`pregel/main.py:2626`)

```python
# main.py line 2868 — SyncPregelLoop context manager
with SyncPregelLoop(
    input,
    stream=StreamProtocol(stream.put, stream_modes),
    config=config,
    checkpointer=checkpointer,
    nodes=self.nodes,
    specs=self.channels,
    ...
) as loop:
    runner = PregelRunner(
        submit=...,
        put_writes=weakref.WeakMethod(loop.put_writes),
        ...
    )
    # BSP (Bulk Synchronous Parallel) 모델
    while loop.tick():                               # superstep 경계
        for task in loop.match_cached_writes():
            loop.output_writes(task.id, task.writes, cached=True)
        for _ in runner.tick(
            [t for t in loop.tasks.values() if not t.writes],
            timeout=self.step_timeout,
            schedule_task=loop.accept_push,
        ):
            yield from _output(...)                  # 스트림 출력
        loop.after_tick()                            # 체크포인트 저장
        if durability_ == "sync":
            loop._put_checkpoint_fut.result()        # 동기 대기
```

**핵심**: `while loop.tick()` 루프가 Pregel의 superstep 반복 구조. 각 iteration = 1 superstep.

---

## 3. `PregelLoop.tick()` — `_loop.py:583`

```python
def tick(self) -> bool:
    if self.step > self.stop:                        # recursion_limit 초과
        self.status = "out_of_steps"
        return False

    self.tasks = prepare_next_tasks(...)             # 실행할 노드 결정

    if not self.tasks:                               # 더 실행할 노드 없음
        self.status = "done"
        return False

    if self.interrupt_before and should_interrupt(...):
        self.status = "interrupt_before"
        raise GraphInterrupt()

    return True
```

**핵심**: `tick()`은 다음 superstep 실행 여부를 결정한다. `prepare_next_tasks()`가 실행 대상 노드를 선정.

---

## 4. `PregelLoop.after_tick()` — `_loop.py:667`

```python
def after_tick(self) -> None:
    writes = [w for t in self.tasks.values() for w in t.writes]
    # 1. 채널 업데이트 적용
    self.updated_channels = apply_writes(
        self.checkpoint, self.channels, self.tasks.values(),
        self.checkpointer_get_next_version, ...
    )
    # 2. output 스트림
    if updated_channels ∩ output_keys:
        self._emit("values", map_output_values, ...)
    # 3. pending_writes 클리어
    self.checkpoint_pending_writes.clear()
    self.is_replaying = False
    # 4. 체크포인트 저장
    self._put_checkpoint({"source": "loop"})
    # 5. interrupt_after 체크
    if self.interrupt_after and should_interrupt(...):
        self.status = "interrupt_after"
        raise GraphInterrupt()
    # 6. step 증가
    self.step += 1
```

**핵심**: superstep 완료 후 채널 업데이트 → 스트림 출력 → 체크포인트 저장 → 인터럽트 체크 → step 증가 순서로 실행.

---

## 5. `PregelLoop.put_writes()` — `_loop.py:407`

```python
def put_writes(self, task_id: str, writes: WritesT) -> None:
    # 특수 채널 write는 last-write-wins 중복 제거
    if all(w[0] in WRITES_IDX_MAP for w in writes):
        writes = list({w[0]: w for w in writes}.values())

    # 기존 동일 task_id write 제거 후 새 write 추가
    self.checkpoint_pending_writes.extend((task_id, c, v) for c, v in writes)

    # checkpointer.put_writes 비동기 호출 (durability != "exit")
    if self.durability != "exit" and self.checkpointer_put_writes is not None:
        fut = self.submit(
            self.checkpointer_put_writes,
            config, writes_to_save, task_id, task_path
        )
```

**핵심**: 노드 실행 결과(writes)를 `checkpoint_pending_writes`에 축적하고 즉시 `checkpointer.put_writes()`를 비동기 호출한다.

---

## 6. `PregelLoop._put_checkpoint()` — `_loop.py:1055`

```python
def _put_checkpoint(self, metadata: CheckpointMetadata) -> None:
    exiting = metadata is self.checkpoint_metadata   # exit 단계 여부

    # DeltaChannel 카운터 증가
    for ch in delta_channels:
        u, s = prev_counters.get(ch_name, (0, 0))
        s += 1
        if ch_name in updated: u += 1

    # create_checkpoint(): 현재 채널 상태 스냅샷
    self.checkpoint = create_checkpoint(
        self.checkpoint, self.channels, self.step, ...
    )

    # checkpointer.put() 비동기 호출
    if do_checkpoint:
        self._put_checkpoint_fut = self.submit(
            self._checkpointer_put_after_previous,
            prev_fut, config, checkpoint, metadata, new_versions
        )
```

**핵심**: `create_checkpoint()`가 현재 채널 상태를 직렬화한 뒤 `checkpointer.put()`을 비동기로 호출한다.

---

## 7. `BaseCheckpointSaver.put()` — `checkpoint/base/__init__.py:277`

```python
def put(
    self,
    config: RunnableConfig,
    checkpoint: Checkpoint,
    metadata: CheckpointMetadata,
    new_versions: ChannelVersions,
) -> RunnableConfig:
    raise NotImplementedError  # 구현체가 오버라이드
```

`put()`이 호출되는 경로:
```
loop.after_tick()
  → _put_checkpoint({"source": "loop"})
      → create_checkpoint(channels, step)
      → submit(_checkpointer_put_after_previous, ...)
          → SyncPregelLoop._checkpointer_put_after_previous()  # line 1498
              → checkpointer.put(config, checkpoint, metadata, new_versions)
```

---

## 8. `InMemorySaver.put()` — `checkpoint/memory/__init__.py:427`

```python
def put(self, config, checkpoint, metadata, new_versions) -> RunnableConfig:
    c = checkpoint.copy()
    thread_id = config["configurable"]["thread_id"]
    checkpoint_ns = config["configurable"]["checkpoint_ns"]
    values = c.pop("channel_values")                 # 채널 값 분리

    # channel_values: blob으로 개별 저장 (버전별 키)
    for k, v in new_versions.items():
        self.blobs[(thread_id, checkpoint_ns, k, v)] = (
            self.serde.dumps_typed(values[k]) if k in values else ("empty", b"")
        )

    # 체크포인트 메타데이터: storage에 저장
    self.storage[thread_id][checkpoint_ns].update({
        checkpoint["id"]: (
            self.serde.dumps_typed(c),
            self.serde.dumps_typed(metadata),
            config["configurable"].get("checkpoint_id"),  # parent id
        )
    })
    return {"configurable": {"thread_id": thread_id, "checkpoint_ns": ..., "checkpoint_id": checkpoint["id"]}}
```

**핵심**: channel_values는 `(thread_id, checkpoint_ns, channel_name, version)` 키로 blob 저장. 체크포인트 메타데이터는 `storage[thread_id][checkpoint_ns][checkpoint_id]`로 저장.

---

## 9. 전체 실행 흐름 요약

```
graph.invoke(input, config)
  → Pregel.stream(input, config)
      → SyncPregelLoop.__enter__()
          → checkpointer.get_tuple(config) → 이전 체크포인트 로드 (없으면 empty)
          → _first(): input → __start__ 채널 write → put_writes()
      → while loop.tick():
          → prepare_next_tasks() → 실행 대상 노드 선정
          → (interrupt_before 체크)
          → runner.tick(tasks):
              → 각 노드 실행 → 결과를 loop.put_writes()로 전달
                  → checkpoint_pending_writes 축적
                  → checkpointer.put_writes(config, writes, task_id) [비동기]
          → loop.after_tick():
              → apply_writes() → 채널 업데이트
              → _put_checkpoint() → create_checkpoint() → checkpointer.put() [비동기]
              → (interrupt_after 체크)
              → step += 1
      → SyncPregelLoop.__exit__() → 최종 체크포인트 저장 (exit 모드)
```

---

## 관련 파일 경로 (v1.2.1)

```
/usr/local/lib/python3.11/dist-packages/langgraph/
  graph/state.py          StateGraph.compile()                  line 1164
  pregel/main.py          Pregel.stream() / SyncPregelLoop 사용  line 2868
  pregel/_loop.py         PregelLoop / SyncPregelLoop            line 155 / 1437
                          tick()                                 line 583
                          after_tick()                           line 667
                          put_writes()                           line 407
                          _put_checkpoint()                      line 1055
  pregel/_checkpoint.py   create_checkpoint() / delta_channels   line 26
  checkpoint/base/__init__.py  BaseCheckpointSaver.put()         line 277
                               BaseCheckpointSaver.put_writes()  line 300
  checkpoint/memory/__init__.py  InMemorySaver.put()             line 427
                                 InMemorySaver.put_writes()      line 473
```
