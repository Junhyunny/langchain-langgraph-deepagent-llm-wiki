---
type: source_summary
source_id: deepagents-docs-context-engineering-2026-05-18
title: "Deep Agents — Context Engineering"
framework: Deep Agents
status: verified
confidence: high
retrieved_at: 2026-05-18
url: https://docs.langchain.com/oss/python/deepagents/context-engineering
---

# Source Summary: Deep Agents — Context Engineering

## Key Facts

### 5가지 Context 타입

| Context 타입 | 제어 주체 | 범위 |
|---|---|---|
| **Input context** | startup 시 agent 프롬프트에 들어가는 것 (system prompt, memory, skills) | 정적, 매 실행마다 적용 |
| **Runtime context** | invoke 시 전달되는 정적 설정 (user metadata, API keys, connections) | 실행 당, 서브에이전트로 전파 |
| **Context compression** | 컨텍스트 윈도우 한계 도달 시 자동 offloading + summarization | 자동 |
| **Context isolation** | 무거운 작업을 서브에이전트에 위임, 결과만 메인 에이전트로 반환 | 서브에이전트 단위 |
| **Long-term memory** | 가상 파일시스템을 통한 스레드 간 영속 저장소 | 대화 전체 |

### Input Context

- `system_prompt` 파라미터는 **정적** — 실행마다 변하지 않음
- 동적 프롬프트가 필요하면 `@dynamic_prompt` 사용 (`request.runtime.context`, `request.runtime.store` 접근)
- 도구는 미들웨어 없이도 `ToolRuntime` 객체를 직접 받음

**Memory vs Skills 차이:**
- Memory (`AGENTS.md`): 시스템 프롬프트에 **항상 로드** (진입 필터 없음)
- Skills (`SKILL.md`): startup에 frontmatter만 읽고, 관련성 판단 시에만 전체 로드 (**progressive disclosure**)

### System Prompt 조립 순서 (9단계)

1. Custom `system_prompt` (제공된 경우)
2. Base agent prompt (소스: `graph.py#L37`)
3. To-do list prompt
4. Memory prompt (`memory` 파라미터 제공 시에만)
5. Skills prompt (`skills` 파라미터 제공 시에만)
6. Virtual filesystem prompt
7. Subagent prompt (`task` tool 사용법)
8. 사용자 제공 미들웨어 prompts (커스텀 미들웨어가 있는 경우)
9. Human-in-the-loop prompt (`interrupt_on` 설정 시)

### Runtime Context

- 모델 프롬프트에 **자동 포함되지 않음** — tool/middleware가 읽어서 메시지에 추가해야 함
- `context_schema` (dataclass 또는 TypedDict)로 형태 정의
- `invoke`/`ainvoke`의 `context` 인자로 전달
- **모든 서브에이전트에 자동으로 전파됨**

### Context Compression: Offloading

Offloading 트리거:
- **Tool call inputs > 20,000 tokens**: 세션 컨텍스트가 모델 컨텍스트 윈도우의 85% 초과 시 → 오래된 tool call 잘라내고 파일 포인터로 대체
- **Tool call results > 20,000 tokens**: 결과를 configured backend에 offload → 파일 경로 참조 + 첫 10줄 preview로 대체

### Context Compression: Summarization

Summarization 트리거 조건:
- 컨텍스트가 모델 `max_input_tokens`의 **85%** 초과 + offloading 대상 없음
- `ContextOverflowError` 발생 시 즉시 fallback

Summarization 동작:
- LLM이 구조화된 요약 생성 (session intent, artifacts created, next steps)
- 요약이 전체 대화 히스토리를 대체
- 원본 전체 대화는 파일시스템에 보존

설정값:
- 최근 컨텍스트로 토큰의 **10%** 유지
- 모델 프로파일 불명 시 fallback: **170,000 tokens** 기준 / 최근 **6 messages** 유지

선택적 Summarization Tool: `create_summarization_tool_middleware` — agent가 적절한 시점에 직접 요약 트리거 가능

### Context Isolation (Subagents)

- 메인 에이전트는 `task` tool로 작업 위임
- 서브에이전트는 자체 **fresh context**로 실행
- 서브에이전트가 자율적으로 완료 후 단일 최종 보고서만 반환
- 메인 에이전트의 컨텍스트는 서브에이전트 내부 tool call들을 볼 필요 없음

### Long-term Memory

- 기본 파일시스템: **단일 스레드 내에서만** 영속 (conversation 단위)
- 스레드 간 영속 필요 시: `CompositeBackend` + `StoreBackend` 사용
  - 특정 경로(`/memories/`)를 LangGraph Store로 라우팅
- `/memories/` 경로는 빈 상태로 시작 → agent가 `write_file`, `edit_file`로 직접 생성

```python
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

def make_backend(runtime):
    return CompositeBackend(
        default=StateBackend(runtime),
        routes={"/memories/": StoreBackend(runtime)},
    )
```

## Important Terms

- [[Context Engineering]]
- [[Deep Agents]]
- [[Subagents]]
- [[Memory]]
- [[Tool Calling]]
- `create_summarization_tool_middleware`
- `CompositeBackend` / `StoreBackend` / `StateBackend`
- `ToolRuntime`
- `context_schema`
- progressive disclosure (skills)

## Interpretation

- Memory와 Skills의 구분은 컨텍스트 토큰 효율성 관점에서 중요하다: 항상 필요한 것은 memory, 상황별로 필요한 것은 skills.
- System prompt 조립 순서는 deep agent 동작을 디버깅할 때 핵심 지식이다. 어떤 프롬프트가 우선순위를 갖는지 이 순서로 결정된다.
- Runtime context가 서브에이전트로 자동 전파된다는 점은 multi-agent 시스템에서 인증/설정 공유 패턴을 단순화한다.
- Offloading과 Summarization은 long-running task에서 토큰 비용을 제어하는 핵심 메커니즘이다.

## Open Questions

- `graph.py#L37`의 base agent prompt는 어떤 내용인가? 커스터마이징 가능한가?
- Skills frontmatter 형식은 정확히 무엇인가? 어떤 메타데이터가 있어야 agent가 관련성을 판단하는가?
- Offloading backend는 무엇을 지원하는가? StateBackend가 기본값인가?
- `@dynamic_prompt` 데코레이터의 정확한 시그니처와 사용 패턴은?
- 스레드 간 Long-term memory를 사용하려면 LangGraph Store backend 설정이 필수인가?

## Used By

- [[Context Engineering]]
- [[Deep Agents]]
- [[Memory]]

## Sources

- `deepagents-docs-context-engineering-2026-05-18`
