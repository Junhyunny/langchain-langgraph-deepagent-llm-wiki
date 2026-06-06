---
type: concept
framework: Deep Agents
status: verified
confidence: high
last_reviewed: 2026-06-06
sources:
  - deepagents-source-filesystem-middleware-2026-06-06
  - deepagents-source-backends-protocol-2026-06-06
  - deepagents-docs-harness-2026-05-19
---

# FilesystemMiddleware

## Summary

`FilesystemMiddleware`는 Deep Agents의 **required middleware**로, 7개의 virtual filesystem tool을 에이전트에 주입하고 파일시스템 접근 권한을 관리한다.
`excluded_middleware`로 제거 시도 시 `ValueError` 발생 — 이 middleware가 없으면 Deep Agents harness가 성립하지 않는다.

Source: `deepagents-docs-harness-2026-05-19`, `deepagents-source-filesystem-middleware-2026-06-06`

## Why It Matters

Deep Agents가 "virtual filesystem"을 제공하는 방식이 바로 이 미들웨어다. 단순히 tool을 등록하는 것을 넘어서:
- 대용량 결과를 자동으로 파일시스템으로 오프로드해 컨텍스트 윈도우를 보호한다
- permissions 시스템으로 에이전트가 접근할 수 있는 경로를 선언적으로 통제한다
- sandbox backend 유무에 따라 `execute` tool을 동적으로 포함하거나 제거한다

## 클래스 정의

```python
class FilesystemMiddleware(AgentMiddleware[FilesystemState, ContextT, ResponseT]):
    def __init__(
        self,
        backend: BACKEND_TYPES | None = None,
        system_prompt: str | None = None,
        custom_tool_descriptions: Mapping[str, str] | None = None,
        tool_token_limit_before_evict: int | None = 20000,
        human_message_token_limit_before_evict: int | None = 50000,
        max_execute_timeout: int = 3600,
        _permissions: list[FilesystemPermission] | None = None,
    ) -> None
```

`create_deep_agent()`가 `permissions=` 인자를 받아 `FilesystemMiddleware(_permissions=...)` 형태로 전달한다.

Source: `deepagents-source-filesystem-middleware-2026-06-06`

## 주입되는 Tool 목록

`__init__`에서 `StructuredTool.from_function()`으로 7개 tool을 생성해 `self.tools`에 보관한다.

| Tool | 입력 스키마 | 핵심 동작 |
|------|------------|----------|
| `ls` | `LsSchema` | `backend.ls()` → `FileInfo` 리스트 → permissions 필터 |
| `read_file` | `ReadFileSchema` (offset, limit) | `backend.read()` → 텍스트(라인 번호 추가) 또는 바이너리(base64) |
| `write_file` | `WriteFileSchema` | 권한 검증 → `backend.write()` |
| `edit_file` | `EditFileSchema` (replace_all 지원) | 권한 검증 → `backend.edit()` → 교체된 인스턴스 수 반환 |
| `glob` | `GlobSchema` | `ThreadPoolExecutor` 20초 타임아웃 → permissions 필터 |
| `grep` | `GrepSchema` (output_mode: files/content/count) | `backend.grep()` → permissions 필터 |
| `execute` | `ExecuteSchema` | sandbox 여부 조건부 실행 — 아래 참조 |

Source: `deepagents-source-filesystem-middleware-2026-06-06`

## FilesystemState

```python
class FilesystemState(AgentState):
    files: Annotated[dict, DeltaChannel(...)]
```

`files` 채널이 LangGraph state에 존재하며, `StateBackend`가 이 채널에 파일을 저장한다.

## Permissions 시스템

### FilesystemPermission 구조

```python
@dataclass
class FilesystemPermission:
    operations: list[FilesystemOperation]  # "read" | "write" | "execute" 등
    paths: list[str]                       # glob 패턴 (예: "**/*.secret")
    mode: Literal["allow", "deny", "interrupt"]
```

`__post_init__`에서 경로가 `/` 시작이고 `..` · `~` 미포함인지 검증한다.

### 매칭 방식

```python
def _check_fs_permission(
    rules: list[FilesystemPermission],
    operation: FilesystemOperation,
    path: str,
) -> Literal["allow", "deny", "interrupt"]
```

- **first-match-wins**: 첫 번째로 매칭되는 rule 적용
- **글로브 매칭**: `wcmatch.glob` 사용 (GLOBSTAR, BRACE 플래그)
- **매칭 rule 없음**: 기본 `allow`
- `interrupt` 모드: Human-in-the-Loop 승인 대기

Source: `deepagents-source-filesystem-middleware-2026-06-06`

## wrap_model_call 동작

모델 호출 전 세 가지 작업을 수행한다:

1. **System Prompt 주입**: 파일시스템 도구 설명 + (execute 지원 시) `EXECUTION_SYSTEM_PROMPT` 추가
2. **execute tool 조건부 제거**:

```python
def supports_execution(backend: BackendProtocol) -> bool:
    if isinstance(backend, CompositeBackend):
        return isinstance(backend.default, SandboxBackendProtocol)
    return isinstance(backend, SandboxBackendProtocol)

# wrap_model_call 내부 로직
if has_execute_tool and not backend_supports_execution:
    filtered_tools = [t for t in request.tools if tool_name(t) != "execute"]
    request = request.override(tools=filtered_tools)
```

3. **HumanMessage 대용량 오프로드**: 최근 HumanMessage가 `human_message_token_limit_before_evict` (기본 50,000 토큰) 초과 시 파일시스템에 저장하고 `ExtendedModelResponse`로 상태 업데이트 명령 반환

Source: `deepagents-source-filesystem-middleware-2026-06-06`

## wrap_tool_call 동작

tool 실행 후 결과 크기를 확인한다:

- `tool_token_limit_before_evict` (기본 20,000 토큰) 초과 시 파일시스템으로 오프로드
- **단, 다음 tool은 제외** (`TOOLS_EXCLUDED_FROM_EVICTION`): `ls`, `glob`, `grep`, `read_file`, `edit_file`, `write_file`
  - 이 tool들의 결과는 크기와 무관하게 항상 직접 반환

Source: `deepagents-source-filesystem-middleware-2026-06-06`

## read_file 내부 동작 상세

```
read_file(path, offset=None, limit=None)
  → 권한 검증 (_check_fs_permission "read")
  → backend.read(file_path, offset, limit)
  → ReadResult.file_data 확인
    → 텍스트: 라인 번호 prefix 추가 ("1\t...", "2\t...")
    → 바이너리(이미지/PDF 등): base64 멀티모달 콘텐츠 블록 반환
  → 콘텐츠 크기 초과 시 READ_FILE_TRUNCATION_MSG 추가
```

Source: `deepagents-source-filesystem-middleware-2026-06-06`

## write_file 내부 동작 상세

```
write_file(path, content)
  → 권한 검증 (_check_fs_permission "write")
  → backend.write(file_path, content)
  → WriteResult.error 확인
  → 성공: "Updated file {path}" 반환
```

Source: `deepagents-source-filesystem-middleware-2026-06-06`

## execute tool — sandbox 없을 때 동작

→ `docs/wiki/flows/Deep Agents execute sandbox flow.md` 참조

## Source Code References

- Repo: `https://github.com/langchain-ai/deepagents`
- Commit: UNKNOWN
- Files:
  - `libs/deepagents/deepagents/middleware/filesystem.py` — FilesystemMiddleware 전체
  - `libs/deepagents/deepagents/backends/protocol.py` — BackendProtocol, SandboxBackendProtocol, 데이터 클래스

## Related Pages

- [[Deep Agents]]
- [[Agent Harness]]
- [[Deep Agents create_deep_agent flow]]
- [[Deep Agents execute sandbox flow]]
- [[Context Engineering]]
- [[HumanInTheLoop]]

## Open Questions

- `FilesystemPermission`의 `interrupt` 모드는 `HumanInTheLoopMiddleware`와 어떻게 상호작용하는가?
- `TOOLS_EXCLUDED_FROM_EVICTION` 상수 전체 목록 — 현재 확인된 6개가 전부인가?
- `_intercept_large_tool_result()`의 정확한 오프로드 대상 파일 경로 결정 방식

## Sources

- `deepagents-source-filesystem-middleware-2026-06-06`
- `deepagents-source-backends-protocol-2026-06-06`
- `deepagents-docs-harness-2026-05-19`
