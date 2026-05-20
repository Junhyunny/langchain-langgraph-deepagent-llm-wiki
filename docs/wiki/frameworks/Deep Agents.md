---
type: framework
framework: Deep Agents
status: draft
confidence: high
last_reviewed: 2026-05-19
sources:
  - deepagents-docs-overview-2026-05-18
  - deepagents-docs-context-engineering-2026-05-18
  - deepagents-source-graph-2026-05-19
  - deepagents-docs-harness-2026-05-19
---

# Deep Agents

## Summary

`deepagents`는 PyPI에서 설치 가능한 standalone 라이브러리다.
[[LangChain]]의 core building blocks와 [[LangGraph]] runtime 위에서 동작하는 **agent harness**다.
복잡한 multi-step 태스크, 파일 시스템 기반 context 관리, subagent 위임, long-term memory를 내장 기능으로 제공한다.

## Why It Matters

Deep Agents는 LangChain + LangGraph의 조합을 직접 조립하지 않아도 복잡한 에이전트를 빠르게 만들 수 있도록 공통 패턴을 미리 패키지화한 고수준 harness다.
언제 Deep Agents를 쓰고, 언제 LangGraph를 직접 쓸지 판단하기 위해 내부 구조를 이해하는 것이 중요하다.

## Verified Facts
*Source: `deepagents-docs-overview-2026-05-18`*

- **패키지**: `pip install deepagents` — standalone PyPI 패키지
- **저장소**: `github.com/langchain-ai/deepagents`
- **의존성**: [[LangChain]] building blocks + [[LangGraph]] runtime
- **정의**: "agent harness" — 다른 프레임워크와 동일한 core tool calling loop이지만, built-in tools와 capabilities 포함
- **진입점**: `create_deep_agent(model, tools, system_prompt)`
- **저장소 구성**:
  - **Deep Agents SDK** — 어떤 태스크도 처리하는 에이전트 빌딩 패키지
  - **Deep Agents Code** — Deep Agents SDK 위에 만들어진 터미널 코딩 에이전트
  - **ACP integration** — Zed 등 코드 에디터용 Agent Client Protocol 커넥터
- **LangGraph 활용 기능**: durable execution, streaming, human-in-the-loop

## Use Cases (공식 문서 기준)
*Source: `deepagents-docs-overview-2026-05-18`*

Deep Agents SDK를 사용해야 하는 경우:
- 복잡한 multi-step 태스크 (planning and decomposition 필요)
- 대규모 context 관리 (filesystem tools, summarization)
- filesystem backend 교체 (in-memory / local disk / durable store / sandbox / custom)
- shell 명령어 실행 (`execute` tool, sandbox backend)
- interpreter 코드 실행 (subagent orchestration, structured data transformation)
- specialized subagent에 작업 위임 (context isolation)
- 대화/스레드 간 memory 지속
- 파일 접근 권한 제어 (declarative permission rules)
- human-in-the-loop workflows
- 모든 모델 사용 가능 (provider agnostic)

**더 단순한 에이전트를 만들 때** → LangChain의 `create_agent` 또는 custom [[LangGraph]] workflow 권장
*(Source: `deepagents-docs-overview-2026-05-18`)*

## Quick Start
```python
# pip install -qU deepagents langchain-openai
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-5.4",
    tools=[my_tool],
    system_prompt="You are a helpful assistant",
)

agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

## Public API

전체 시그니처 (소스코드 기준):
```python
create_deep_agent(
    model: str | BaseChatModel | None = None,  # ⚠️ None은 0.5.3부터 deprecated
    tools: Sequence[BaseTool | Callable | dict] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: Sequence[SubAgent | CompiledSubAgent | AsyncSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    permissions: list[FilesystemPermission] | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    response_format: ... | None = None,
    context_schema: type[ContextT] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
) -> CompiledStateGraph
```
Source: `deepagents-source-graph-2026-05-19`

## Harness Capabilities (공식 목록)
*Source: `deepagents-docs-harness-2026-05-19`*

하네스는 8가지 구성요소의 조합이다. Skills·Memory는 구성요소와 별도로 "alongside" 제공됨.

| 구성요소 | 핵심 역할 |
|---------|----------|
| **Planning** | `write_todos` tool — 상태(`pending`/`in_progress`/`completed`) 포함 태스크 목록, agent state에 영속 |
| **Virtual filesystem** | 7 built-in tool (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute`) |
| **Filesystem permissions** | declarative rule 목록, first-match-wins, 기본 허용 |
| **Task delegation** | `task` tool → subagent 위임, stateless, 단일 최종 보고서 반환 |
| **Context management** | offloading + summarization 자동 압축, subagent context isolation |
| **Code execution** | sandbox → `execute` tool / interpreter → `eval` tool (QuickJS) |
| **Human-in-the-loop** | `interrupt_on={"tool_name": True}` — opt-in, tool 호출 전 pause |
| **Harness profiles** | `HarnessProfile` + `register_harness_profile` — 모델별 declarative 설정 번들 |

### Virtual Filesystem — Built-in Tools
*Source: `deepagents-docs-harness-2026-05-19`*

| Tool | 설명 |
|------|------|
| `ls` | 디렉터리 목록 (size, modified time 포함) |
| `read_file` | 파일 읽기 (line numbers, offset/limit, 멀티모달 지원) |
| `write_file` | 새 파일 생성 |
| `edit_file` | exact string replacement (global replace 모드 지원) |
| `glob` | 패턴 매칭 파일 검색 (예: `**/*.py`) |
| `grep` | 파일 내용 검색 (files-only / content+context / counts 모드) |
| `execute` | shell 명령 실행 (**sandbox backend 전용**) |

- `FilesystemMiddleware`가 제거 불가인 이유: 이 tools + permissions 보안이 모두 여기서 처리됨
- filesystem tools 숨기기: `HarnessProfile(excluded_tools=frozenset({...}))` 사용
- `excluded_middleware`로 `FilesystemMiddleware` 제거 시도 → **ValueError**

### Filesystem Permissions
*Source: `deepagents-docs-harness-2026-05-19`*

```python
# permissions= 파라미터에 rule 목록 전달
agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    permissions=[
        {"operations": ["write"], "paths": [".env", "**/*.secret"], "mode": "deny"},
        {"operations": ["read", "write"], "paths": ["/workspace/**"], "mode": "allow"},
    ],
)
```

- **first-match-wins**: 첫 번째 매칭 rule 적용
- 매칭 rule 없음 → **허용** (기본 allow)
- Subagent: parent permissions 상속, 자체 permissions 선언 시 대체
- Sandbox backend의 `execute` tool에는 permissions 미적용

### Harness Profiles
*Source: `deepagents-docs-harness-2026-05-19`*

```python
from deepagents import HarnessProfile, register_harness_profile

# provider:model 키로 등록
register_harness_profile(
    "anthropic:claude-sonnet-4-6",
    HarnessProfile(
        excluded_tools=frozenset({"ls", "read_file", "write_file", "edit_file", "glob", "grep"}),
    ),
)

# provider 키로도 등록 가능 (model-level이 override)
register_harness_profile("openai", HarnessProfile(...))
```

- 등록 키: `"provider"` 또는 `"provider:model"` — provider-level + model-level 병합됨
- `create_deep_agent`가 model resolve 시 자동 적용
- entry points 방식으로 plugin 패키징 가능 (외부 패키지로 배포 가능)

## Context Engineering
*Source: `deepagents-docs-context-engineering-2026-05-18`*

Deep Agents는 5가지 context 타입을 체계적으로 관리한다. 자세한 내용: [[Context Engineering]]

**System Prompt 조립 순서 (소스코드로 확인됨):**
- `USER` (system_prompt 인자) → `BASE` (또는 HarnessProfile `CUSTOM`) → `SUFFIX` (HarnessProfile)
- `USER`가 항상 앞 (caller 우선), `SUFFIX`가 항상 마지막
- `USER`가 `SystemMessage`이면 기존 content_blocks에 text block append (cache_control 보존)

Source: `deepagents-source-graph-2026-05-19`

**핵심 차이:**
- `memory` — 항상 로드 (no progressive disclosure); 필수 규칙/선호도에 사용
- `skills` — frontmatter만 로드, 관련성 판단 시 전체 로드 (progressive disclosure); 특화 워크플로우에 사용

**Context Compression:**
- Offloading: tool call results > 20,000 tokens → backend offload
- Summarization: 컨텍스트 > `max_input_tokens`의 85% → LLM 요약 생성, 원본은 파일시스템 보존

**Runtime Context:** `context_schema` + `context` 인자로 per-run 설정 주입; 서브에이전트로 **자동 전파**

**Long-term Memory:** 기본은 단일 스레드. 스레드 간 영속은 `CompositeBackend` + `StoreBackend` 필요

## Interpretation
- Deep Agents는 LangGraph + LangChain의 기능을 직접 조합하는 대신, 공통 패턴을 미리 구성해 둔 고수준 래퍼로 이해할 수 있다.
- "agent harness"라는 정의는 framework보다 좁은 개념 — 기존 runtime(LangGraph) 위에서 동작하는 조립품이다.
- 세밀한 그래프 제어가 필요할 때는 LangGraph를 직접 쓰는 것이 더 적합할 수 있다.

## Superseded Notes
- **Old:** "Deep Agents는 어떤 저장소에 존재하는가?" — 미확인
- **New:** `github.com/langchain-ai/deepagents` — 확인됨
  Source: `deepagents-docs-overview-2026-05-18`

- **Old:** "상태 관리를 위해 LangGraph에 의존하는가?" — 미확인
- **New:** LangGraph runtime을 사용해 durable execution, streaming, human-in-the-loop 제공 — 확인됨
  Source: `deepagents-docs-overview-2026-05-18`

- **Old:** "System Prompt 조립 순서: custom → base(graph.py#L37) → todos → memory → skills → filesystem → subagent → middleware → human-in-the-loop" (context engineering 문서 기반)
- **New:** 소스코드 기준 system prompt 조립은 USER → BASE (or CUSTOM) → SUFFIX 3단계. 문서가 설명한 항목들(todos, memory, skills 등)은 실제로는 middleware가 system prompt에 주입하는 구조로 확인됨.
  Source: `deepagents-source-graph-2026-05-19`
  Date: 2026-05-19

## Internal Implementation Map
*Source: `deepagents-source-graph-2026-05-19`*

- **모듈 경로:** `libs/deepagents/deepagents/graph.py`
- **위임 구조:** `create_deep_agent` → middleware 조립 → `langchain.agents.create_agent` 위임 → `CompiledStateGraph` 반환
- **State:** `_DeepAgentState(AgentState)` — `DeltaChannel`로 checkpoint O(N²) → O(N) 최적화 (`snapshot_frequency=50`)
- **기본값:** `backend=StateBackend()`, `recursion_limit=9_999`, default model=`claude-sonnet-4-6` (deprecated)
- **Required middleware:** `FilesystemMiddleware` + `SubAgentMiddleware` (제거 시 `ValueError`)

**Middleware 조립 순서 (소스 확인됨):**

| 순서 | Middleware | 조건 |
|------|-----------|------|
| 1 | `TodoListMiddleware` | 항상 |
| 2 | `SkillsMiddleware` | `skills` 파라미터 제공 시 |
| 3 | `FilesystemMiddleware` | 항상 (required) |
| 4 | `SubAgentMiddleware` | inline subagents 있을 때 |
| 5 | `AsyncSubAgentMiddleware` | async subagents 있을 때 |
| 6 | `SummarizationMiddleware` | 항상 |
| 7 | `PatchToolCallsMiddleware` | 항상 |
| — | *사용자 middleware* | `middleware=` 파라미터 |
| 8 | HarnessProfile `extra_middleware` | profile에 있을 때 |
| 9 | `_ToolExclusionMiddleware` | profile `excluded_tools` 있을 때 |
| 10 | `AnthropicPromptCachingMiddleware` | **항상** (비-Anthropic no-op) |
| 11 | `MemoryMiddleware` | `memory` 파라미터 제공 시 |
| 12 | `HumanInTheLoopMiddleware` | `interrupt_on` 파라미터 제공 시 |

자세한 내용: [[Deep Agents create_deep_agent flow]] · [[Deep Agents Code Map]]

## Related Tests

- 소스코드 확인 필요.

## Open Questions

- subagent state isolation의 구체적 메커니즘은? (`SubagentTransformer`, `SubAgentMiddleware` 내부 확인 필요)
- ACP integration은 어떤 프로토콜 스펙을 따르는가?
- Deep Agents Code (터미널 에이전트)는 SDK를 어떻게 확장하는가?
- `langchain.agents.create_agent`의 내부 구현은? LangGraph graph를 어떻게 조립하나?
- `PatchToolCallsMiddleware`는 어떤 tool call 패치를 수행하나?
- `HarnessProfile`의 전체 필드 목록은? (`base_system_prompt`, `system_prompt_suffix`, `general_purpose_subagent` 외에 더 있는가?) — Source: `deepagents-docs-harness-2026-05-19`
- Provider-level과 model-level HarnessProfile의 merge 우선순위는? — Source: `deepagents-docs-harness-2026-05-19`
- `register_harness_profile`의 전체 시그니처 및 entry points 패키징 방법은? — Source: `deepagents-docs-harness-2026-05-19`
- Sandbox backend 없이 `execute` tool 호출 시 error 반환인가, tool 목록에서 제외되는가? — Source: `deepagents-docs-harness-2026-05-19`
- Interpreter (`eval` tool, QuickJS)는 어떤 패키지에 포함되어 있는가? — Source: `deepagents-docs-harness-2026-05-19`

**해소된 질문:**
- ✅ `create_deep_agent`는 `langchain.agents.create_agent`에 위임 → `CompiledStateGraph` 반환 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ `create_deep_agent`와 LangChain `create_agent`의 차이: middleware 조립 후 `create_agent` 위임 (Source: `deepagents-source-graph-2026-05-19`)
- ✅ "durable execution" ↔ checkpointing 연결: `checkpointer` 파라미터 + `_DeepAgentState` `DeltaChannel` (Source: `deepagents-source-graph-2026-05-19`)
- ✅ filesystem tools 목록 확인됨: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute` — `FilesystemMiddleware`에서 주입 (Source: `deepagents-docs-harness-2026-05-19`)
- ✅ `HarnessProfile` 등록 방법: `register_harness_profile(key, HarnessProfile(...))` (Source: `deepagents-docs-harness-2026-05-19`)

## Related Pages

- [[LangChain]]
- [[LangGraph]]
- [[Subagents]]
- [[Tool Calling]]
- [[Checkpointing]]
- [[Deep Agents Code Map]]
- [[Deep Agents create_deep_agent flow]]
- [[LangChain vs LangGraph vs Deep Agents]]

## Sources

- `deepagents-docs-overview-2026-05-18`
- `deepagents-docs-context-engineering-2026-05-18`
- `deepagents-source-graph-2026-05-19`
- `deepagents-docs-harness-2026-05-19`
