---
type: source_summary
source_id: deepagents-docs-harness-2026-05-19
title: "Deep Agents — Harness"
framework: Deep Agents
retrieved_at: 2026-05-19
status: verified
confidence: high
---

# Source Summary: Deep Agents — Harness

## Source Info
- **Source ID:** `deepagents-docs-harness-2026-05-19`
- **Type:** official_docs
- **URL:** https://docs.langchain.com/oss/python/deepagents/harness
- **Retrieved At:** 2026-05-19
- **Version / Commit:** UNKNOWN

---

## Key Facts
<!-- 원문에 있는 내용만. 추론 금지. -->

### 하네스 정의
- "An agent harness is a combination of several different capabilities that make building long-running agents easier"
- 8가지 공식 구성요소: Planning, Virtual filesystem, Filesystem permissions, Task delegation (subagents), Context management, Code execution, Human-in-the-loop, Harness profiles
- Skills와 Memory는 별도 항목으로 "alongside" 제공됨 (8가지 구성요소에 포함되지 않음)

### Planning capabilities
- `write_todos` tool 제공
- 태스크 상태: `'pending'`, `'in_progress'`, `'completed'`
- agent state에 영속됨

### Virtual filesystem
- 7가지 built-in tool: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute`
- `execute`는 sandbox backend에서만 사용 가능
- `read_file`: 멀티모달 지원 (image, video, audio, PDF, PPT 등 non-text 파일 포함)
- Virtual filesystem은 skills, memory, code execution, context management에서도 사용됨

### Filesystem permissions
- `permissions=` 파라미터로 declarative rule 목록 전달
- 각 rule: `operations` (`"read"`, `"write"`), `paths` (glob pattern), `mode` (`"allow"` 또는 `"deny"`)
- **first-match-wins**: 첫 번째 매칭 rule이 적용됨
- 매칭 rule 없으면 → **허용**
- Subagent는 parent의 permissions를 상속 (subagent 자체 permissions 선언 시 대체)
- Sandbox backend에는 permissions 미적용 (`execute` tool은 임의 명령 실행)
- `FilesystemMiddleware`가 tool 레벨에서 permissions 적용 (backend 레벨 아님)

### Harness profiles
- `HarnessProfile` + `register_harness_profile`로 모델별 설정 등록
- 등록 키: provider 이름 (`"openai"`) 또는 `provider:model` 키 (`"openai:gpt-5.4"`)
- `create_deep_agent`가 모델 resolve 시 자동 적용
- Provider-level + model-level profile은 resolution time에 병합(merge)됨
- 용도: system-prompt 조정, tool override, middleware 추가 — per-agent 설정 불필요

**코드 예제 (원문):**
```python
from deepagents import HarnessProfile, register_harness_profile

register_harness_profile(
    "anthropic:claude-sonnet-4-6",
    HarnessProfile(
        excluded_tools=frozenset(
            {"ls", "read_file", "write_file", "edit_file", "glob", "grep"}
        ),
    ),
)
```

### excluded_tools vs excluded_middleware 정책
- filesystem tool 숨기기 → `HarnessProfile(excluded_tools=...)` 사용
- `excluded_middleware`로 `FilesystemMiddleware` 자체 제거 → **의도적으로 거부됨**
- `excluded_middleware`로 `SubAgentMiddleware` 제거 → **의도적으로 거부됨**
- `task` tool 제거 방법: harness profile로 auto-added subagent 비활성화 + `subagents=`에 sync subagent 없음

### Task delegation (subagents)
- Main agent는 `task` tool로 subagent 위임
- Subagent: **fresh context**로 실행, 자율적으로 완료 후 **단일 최종 보고서** 반환
- Subagents are **stateless** (can't send multiple messages back)
- 이점: context isolation, 병렬 실행 가능, specialization, token efficiency
- 기본 `general-purpose` subagent 자동 추가됨

### Context management
- Input context: system prompt + memory + skills + tool prompts
- Compression: offloading + summarization (자동)
- Isolation: subagent가 heavy work 격리 → 결과만 반환
- Long-term memory: virtual filesystem 통해 스레드 간 영속

### Code execution
- **Sandbox backend** → `execute` tool (shell commands, isolated environment)
  - `SandboxBackendProtocolV2` 구현 시 자동 추가
  - 의존성 설치, 테스트 실행, CLI 호출, OS filesystem 작업에 적합
- **Interpreter** → `eval` tool (JavaScript, scoped QuickJS runtime)
  - shell access, package install, filesystem/network 접근 없음
  - 루프, 배칭, 결정론적 데이터 변환, programmatic tool calling에 적합

### Skills
- Agent Skills standard (agentskills.io) 준수
- 각 skill: directory + `SKILL.md` 파일 (instructions + metadata)
- **Progressive disclosure**: startup 시 frontmatter만 로드, 관련성 판단 시 전체 로드
- 추가 리소스 포함 가능: scripts, reference docs, templates

### Memory
- `AGENTS.md` 파일 (agents.md 표준) 사용
- **항상 로드** (skills와 달리 progressive disclosure 없음)
- `memory=` 파라미터로 파일 경로 목록 전달
- backend에 저장됨 (StateBackend, StoreBackend, FilesystemBackend)
- agent가 interaction/feedback 기반으로 memory 업데이트 가능

---

## Important Terms
- [[Deep Agents]] — 이 문서의 주제
- [[Subagents]] — task tool, stateless, context isolation
- [[Memory]] — AGENTS.md, 항상 로드
- [[Context Engineering]] — context management 섹션
- [[Tool Calling]] — virtual filesystem 7 tools
- [[Checkpointing]] — subagent context isolation과 연관
- `HarnessProfile` — 모델별 declarative 설정 번들
- `register_harness_profile` — profile 등록 함수
- `FilesystemPermission` — declarative permission rule
- `SandboxBackendProtocolV2` — execute tool 활성화 기준
- Skills — progressive disclosure, SKILL.md
- Harness profiles — provider/model 키로 등록

---

## Interpretation
- 하네스의 핵심 설계 철학: "long-running agent를 위한 공통 패턴의 번들". 각 구성요소를 개별 설정하지 않아도 create_deep_agent 하나로 모두 동작한다.
- `excluded_tools`와 `excluded_middleware`의 명확한 분리는 보안 설계 원칙을 반영한다: middleware는 infrastructure(제거 불가), tool은 model-visible surface(제어 가능).
- HarnessProfile의 provider-level + model-level merge 전략은 "기본값은 provider 수준, 세부 조정은 model 수준"으로 관리할 수 있게 해준다.
- Subagent가 stateless라는 점은 중요하다: 단방향 위임 + 단일 보고서 구조가 context isolation의 핵심 메커니즘이다.
- Skills(progressive disclosure) vs Memory(항상 로드)의 구분은 토큰 효율성 최적화다: 자주 필요한 것은 memory, 상황별로 필요한 것은 skills.

---

## Implications for My AI Agent Project
- HarnessProfile로 모델별 기본 설정을 중앙화할 수 있다. `create_deep_agent` 호출 코드를 수정하지 않고 모델 전환 가능.
- Permissions 설계 시 first-match-wins 순서를 주의해야 한다. deny rule을 allow rule 앞에 배치해야 한다.
- Subagent는 stateless임을 명심: 중간 결과를 main agent에 전달하려면 filesystem을 활용해야 한다.
- Sandbox backend 없이는 `execute` tool을 쓸 수 없다. 코드 실행이 필요한 에이전트는 SandboxBackendProtocolV2 구현체 필요.

---

## Open Questions
- `HarnessProfile`의 전체 필드 목록은? (`base_system_prompt`, `system_prompt_suffix`, `general_purpose_subagent` 등 소스코드에서 확인된 것 외에 더 있는가?)
- Provider-level과 model-level profile의 merge 우선순위는? (어느 쪽이 override하는가?)
- `register_harness_profile`의 전체 시그니처는? (entry points 방식 plugin 패키징 가능하다고 언급됨)
- `FilesystemPermission` rule의 정확한 TypedDict 구조는? (`operations`, `paths`, `mode` 외에 필드가 있는가?)
- Interpreter (`eval` tool, QuickJS)는 어떤 패키지에 포함되어 있는가?
- Sandbox backend가 없을 때 `execute` tool은 error를 반환하는가, 아예 tool 목록에서 제외되는가?

---

## Used By
- [[Deep Agents]]
- [[Subagents]]
- [[Memory]]
- [[Context Engineering]]
- [[Tool Calling]]

---

## Notes
- Skills와 Memory는 하네스 8가지 구성요소와 별도로 "alongside" 제공된다고 명시됨. 구성요소 목록에 포함되지 않음.
- `execute` tool은 virtual filesystem 표에 포함되어 있지만, sandbox backend 없이는 사용 불가.
