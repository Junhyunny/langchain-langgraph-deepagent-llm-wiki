---
type: flow
framework: Deep Agents
status: partial
confidence: medium
last_reviewed: 2026-06-06
sources:
  - deepagents-source-filesystem-middleware-2026-06-06
  - deepagents-source-backends-sandbox-2026-06-06
  - deepagents-source-backends-composite-2026-06-06
  - deepagents-source-backends-state-2026-06-06
  - deepagents-source-backends-protocol-2026-06-06
---

# Deep Agents execute tool & sandbox flow

## Summary

Deep Agents의 `execute` tool은 shell 명령을 실행하는 도구로, **sandbox backend가 있을 때만 에이전트에 노출**된다.
backend가 `SandboxBackendProtocol`을 구현하지 않으면 `wrap_model_call`에서 tool 목록에서 조용히 제거된다.

## 전체 흐름 — sandbox 없을 때 (20.1)

```
create_deep_agent(backend=None)
  → backend 기본값: StateBackend()
  → StateBackend는 BackendProtocol만 구현 (SandboxBackendProtocol 미구현)

모델 호출 전 (FilesystemMiddleware.wrap_model_call):
  → supports_execution(StateBackend()) → False
  → execute tool을 request.tools에서 제거
  → 에이전트는 execute tool을 볼 수 없음 → 호출 불가
```

**즉, 에러가 발생하지 않는다.** execute tool이 도구 목록에서 빠질 뿐이다.

Source: `deepagents-source-filesystem-middleware-2026-06-06`, `deepagents-source-backends-state-2026-06-06`

## supports_execution 판단 로직

```python
def supports_execution(backend: BackendProtocol) -> bool:
    if isinstance(backend, CompositeBackend):
        return isinstance(backend.default, SandboxBackendProtocol)
    return isinstance(backend, SandboxBackendProtocol)
```

| backend 타입 | execute 지원 여부 |
|------------|-----------------|
| `StateBackend()` | ❌ (기본값, SandboxBackendProtocol 미구현) |
| `BaseSandbox` 하위 클래스 | ✅ |
| `CompositeBackend(default=StateBackend())` | ❌ |
| `CompositeBackend(default=SandboxBackend())` | ✅ |

Source: `deepagents-source-filesystem-middleware-2026-06-06`, `deepagents-source-backends-composite-2026-06-06`

## Backend 프로토콜 계층

```
BackendProtocol (ABC)
  ├── ls, read, write, edit, grep, glob, upload_files, download_files
  └── StateBackend          ← 기본 백엔드, LangGraph state에 파일 저장
      FilesystemBackend     ← 로컬 디스크 기반 (추정)

SandboxBackendProtocol(BackendProtocol)  ← execute + id 추가
  └── BaseSandbox (ABC)
        ├── execute (추상)
        ├── upload_files (추상)
        ├── download_files (추상)
        └── ls/read/write/edit/grep/glob → execute() 위임으로 구현
```

Source: `deepagents-source-backends-protocol-2026-06-06`, `deepagents-source-backends-sandbox-2026-06-06`

## execute tool 실행 흐름 — sandbox 있을 때 (20.2)

```
에이전트 → execute(command="ls -la", timeout=30)
  → FilesystemMiddleware.wrap_tool_call()
  → ToolCallRequest 처리
  → ExecuteSchema 검증 (timeout: 0 ~ max_execute_timeout)
  → backend.execute(command, timeout=timeout)
  → ExecuteResponse { output, exit_code, truncated } 반환
  → ToolMessage 생성:
      content = f"{output}\nExit code: {exit_code}"
      (truncated=True이면 절단 표시 추가)
```

Source: `deepagents-source-filesystem-middleware-2026-06-06`, `deepagents-source-backends-protocol-2026-06-06`

## ExecuteResponse 구조

```python
@dataclass
class ExecuteResponse:
    output: str          # stdout + stderr 합친 결과
    exit_code: int       # 셸 종료 코드
    truncated: bool      # 출력이 잘렸는지 여부
```

Source: `deepagents-source-backends-protocol-2026-06-06`

## BaseSandbox — 설계 원칙

`BaseSandbox`는 `execute()`를 추상 메서드로 남기고, 나머지 파일시스템 작업(ls, read, write 등)을 **`execute()` 호출 방식으로 구현**한다.

```python
class BaseSandbox(SandboxBackendProtocol, ABC):
    @abstractmethod
    def execute(command: str, *, timeout: int | None = None) -> ExecuteResponse: ...

    def ls(path: str) -> LsResult:
        # execute("ls -la {path}") 형태로 위임
        ...

    def read(file_path: str, ...) -> ReadResult:
        # execute("python3 -c 'read file script'") 형태로 위임
        ...
```

**설계 의미:** sandbox 환경에서는 파일시스템도 shell 명령으로 접근하는 것이 일관성 있다.
하위 클래스는 `execute`, `upload_files`, `download_files` 세 가지만 구현하면 된다.

Source: `deepagents-source-backends-sandbox-2026-06-06`

## CompositeBackend — 여러 백엔드 조합

```python
backend = CompositeBackend(
    default=SandboxBackend(...),          # execute 지원
    routes={
        "/memories/": StoreBackend(),     # 메모리는 별도 스토어
    },
    artifacts_root="/",
)
```

- **경로 prefix 기반 라우팅**: `/memories/` 경로 → `StoreBackend`로 위임
- **default**: 매칭 없는 모든 경로 처리 + execute 지원 여부 기준
- `CompositeBackend.execute()`: `default`가 `SandboxBackendProtocol`이면 위임, 아니면 `NotImplementedError`

Source: `deepagents-source-backends-composite-2026-06-06`

## StateBackend — execute 없음

```python
class StateBackend(BackendProtocol):
    # execute 메서드 없음 — SandboxBackendProtocol 미구현
    # files 채널: LangGraph state의 DeltaChannel에 저장
    # CONFIG_KEY_READ / CONFIG_KEY_SEND로 state 접근
```

`StateBackend`는 파일을 LangGraph의 state checkpointing 메커니즘에 저장한다.
스레드 내에서는 지속되지만 스레드 간 영속은 `CompositeBackend + StoreBackend` 필요.

Source: `deepagents-source-backends-state-2026-06-06`

## 실전 패턴

### execute 없이 사용 (기본)
```python
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[...],
    # backend 생략 → StateBackend() 기본값
    # execute tool은 자동으로 도구 목록에서 제외됨
)
```

### execute 활성화 (sandbox backend 필요)
```python
from deepagents.backends import SandboxBackend  # 하위 구현 클래스

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[...],
    backend=SandboxBackend(...),   # SandboxBackendProtocol 구현체
    # execute tool이 도구 목록에 포함됨
)
```

**주의:** `SandboxBackend`의 구체적 구현 클래스(`__init__` 파라미터, 연결 방식)는 현재 소스에서 미확인 — 하위 클래스가 담당.

## Call Path 요약

### execute tool 제거 경로
```
FilesystemMiddleware.wrap_model_call()
  → supports_execution(backend) → False
  → request.override(tools=[t for t if t.name != "execute"])
  → 모델은 execute tool 없이 호출됨
```

### execute tool 실행 경로
```
모델 → AIMessage(tool_calls=[{name: "execute", args: {...}}])
  → FilesystemMiddleware.wrap_tool_call()
  → ExecuteSchema 검증
  → backend.execute(command, timeout)
  → ExecuteResponse → ToolMessage
```

## 미검증 사항

- **검증됨**: `StateBackend`는 `SandboxBackendProtocol` 미구현 → execute tool 제거 동작
- **검증됨**: `BaseSandbox`가 `execute()`로 모든 파일시스템 작업을 위임하는 설계
- **검증됨**: `ExecuteResponse` 구조 (output, exit_code, truncated)
- **소스 필요**: 실제 배포 가능한 `SandboxBackend` 구현 클래스의 `__init__` 파라미터 및 외부 서비스 연결 방식 (HTTP? WebSocket? gVisor?)
- **소스 필요**: `execute` 허용/거부 permissions 적용 여부 (`FilesystemPermission`이 execute operation도 커버하는지)

## Source Code References

- Repo: `https://github.com/langchain-ai/deepagents`
- Commit: UNKNOWN
- Files:
  - `libs/deepagents/deepagents/middleware/filesystem.py` — `supports_execution()`, `wrap_model_call`, execute tool 조건부 제거
  - `libs/deepagents/deepagents/backends/protocol.py` — `SandboxBackendProtocol`, `ExecuteResponse`
  - `libs/deepagents/deepagents/backends/state.py` — `StateBackend` (execute 없음)
  - `libs/deepagents/deepagents/backends/sandbox.py` — `BaseSandbox` (execute 추상)
  - `libs/deepagents/deepagents/backends/composite.py` — `CompositeBackend`, execute 위임 로직

## Related Pages

- [[FilesystemMiddleware]]
- [[Deep Agents]]
- [[Agent Harness]]
- [[Deep Agents create_deep_agent flow]]
- [[Subagents]]

## Open Questions

- `SandboxBackend`의 실제 구현 클래스는 어디에 있는가? (별도 패키지? Deep Agents Code 레이어?)
- sandbox backend 없이 `execute` tool을 직접 호출하면 ToolMessage error가 반환되는가, 아니면 실행 자체가 불가능한가?
- `FilesystemPermission`의 `operations`에 `"execute"` 값이 있는가? sandbox execute에도 permissions가 적용되는가?
- `BaseSandbox.read()`가 Python 스크립트를 `execute()`로 실행할 때 sandbox 측 Python 버전은 어디서 결정되는가?

## Sources

- `deepagents-source-filesystem-middleware-2026-06-06`
- `deepagents-source-backends-protocol-2026-06-06`
- `deepagents-source-backends-state-2026-06-06`
- `deepagents-source-backends-sandbox-2026-06-06`
- `deepagents-source-backends-composite-2026-06-06`
