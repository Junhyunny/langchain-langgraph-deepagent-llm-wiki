---
source_id: deepagents-blog-evals-2026-05-23
title: "How We Build Evals for Deep Agents"
type: blog
framework: Deep Agents
status: current
confidence: medium
retrieved_at: "2026-05-23"
---

# Source Summary: How We Build Evals for Deep Agents

## Overview

LangChain 팀의 공식 블로그 포스트. Deep Agents eval 설계 철학, 데이터 수집 방법, 메트릭 정의, 실행 방식을 설명한다.

> ⚠️ Blog 출처 — 공식 API 문서가 아니므로 medium confidence로 처리한다.

---

## Key Facts

### Eval 핵심 철학

- **"More evals ≠ better agents"** — 수백~수천 개의 테스트를 맹목적으로 추가하면 프로덕션과 무관한 eval suite를 잘 통과하는 착시가 생긴다.
- 대신: **targeted evals** — 프로덕션에서 중요한 동작만 측정하는 eval을 만든다.
- 모든 eval은 agent 시스템의 동작을 이동시키는 벡터다 (시스템 프롬프트·tool 설명 조정으로 이어짐).
- **단위/통합 테스트 (SDK plumbing)는 model capability eval과 분리한다.** SDK 테스트는 어떤 모델도 통과하므로 scoring에 포함하면 신호가 없다.

### Eval 데이터 소싱 3가지

1. **Dogfooding** — 에이전트를 매일 직접 사용, 모든 오류를 eval 작성 기회로 활용
2. **External benchmarks** — BFCL (function calling), Terminal Bench 2.0 (coding tasks in sandbox), FRAMES (retrieval) — 그대로 쓰지 않고 특정 에이전트에 맞게 조정
3. **Artisanal (hand-written)** — 중요하다고 판단한 동작을 직접 단위 테스트로 작성

### Eval 카테고리 Taxonomy (7가지)

| Category | What It Tests |
|----------|--------------|
| `file_operations` | File tools (read, write, edit, ls, grep, glob), parallel invocation, pagination |
| `retrieval` | Finding information across files, search strategies, multi-hop document synthesis |
| `tool_use` | Selecting the right tool, chaining multi-step calls, tracking state across turns |
| `memory` | Recalling seeded context, extracting implicit preferences, persisting durable info |
| `conversation` | Asking clarifying questions for vague requests, sustaining multi-turn dialogue |
| `summarization` | Handling context overflow, triggering summarization, recovering info after compaction |
| `unit_tests` | SDK plumbing — system prompt passthrough, interrupt config, subagent routing |

- 분류 기준: **"어디서 왔는가"가 아니라 "무엇을 테스트하는가"로 분류**
- 오늘 모든 eval은 end-to-end agent run이다 (단계별 단위 테스트 아님)
- 구조 다양성 의도: 1-step 완료부터 10+ turn (user 시뮬레이션) 까지

### Correctness 측정 방법

| 상황 | 측정 방법 |
|------|----------|
| 내부 custom eval | custom assertions ("did the agent parallelize tool calls?") |
| 외부 벤치마크 (BFCL) | exact matching against ground truth |
| 의미론적 정확성 (memory persistence 등) | LLM-as-a-judge |

### 5가지 메트릭

| Metric | Definition | 방향 |
|--------|-----------|------|
| Correctness | 태스크를 올바르게 완료했는가 | 높을수록 좋음 |
| Step ratio | 관찰된 agent steps / ideal steps | 낮을수록 좋음 |
| Tool call ratio | 관찰된 tool calls / ideal tool calls | 낮을수록 좋음 |
| Latency ratio | 관찰된 latency / ideal latency | 낮을수록 좋음 |
| Solve rate | expected steps / observed latency (오답이면 0) | 높을수록 좋음 |

### Ideal Trajectory

- **정의**: 불필요한 액션 없이 올바른 결과를 내는 기준 경로 (단계 시퀀스)
- 단순·명확한 태스크: 최적 경로가 명백
- 복잡한 태스크: 현재 best-performing 모델을 기준으로 근사, 이후 개선
- **구성 요건**: 최소한의 tool calls, 독립 tool calls 병렬화, 불필요한 중간 턴 없음

예시 ("현재 시간과 날씨를 알려줘"):
- **Ideal**: 4 steps, 4 tool calls, ~8초
- **Inefficient (but correct)**: 6 steps, 5 tool calls, ~14초 → step ratio 1.5, tool_call_ratio 1.25, latency_ratio 1.75

### 모델 선택 기준 (2단계)

1. **Correctness 먼저** — 원하는 태스크를 충분히 정확하게 수행하는 모델 필터링
2. **Efficiency 다음** — correctness 통과 모델 중 correctness/latency/cost 트레이드오프 최적 선택

### 실행 환경

- **pytest + GitHub Actions** — CI에서 재현 가능한 환경으로 실행
- **LangSmith** — 모든 eval run을 공유 프로젝트에 trace → 팀 전체가 분석·수정 가능
- **태그 기반 subset 실행**: `--eval-category file_operations --eval-category tool_use`
- **오픈소스 구현**: `github.com/langchain-ai/deepagents/tree/main/libs/evals`

---

## Interpretation

- "eval 하나 = agent 동작의 압력 벡터"라는 관점은 eval을 단순 테스트가 아닌 **agent 동작 설계 도구**로 보는 것.
- ideal trajectory 개념은 correctness만으로는 부족하다는 인식에서 나온다 — 정확하지만 느리고 비효율적인 모델도 문제다.
- SDK unit/integration test를 model capability eval에서 분리하는 것은 중요한 설계 결정 — 두 층의 테스트가 섞이면 신호가 희석된다.
- `solve rate`는 latency ratio와 달리 실패한 run을 0으로 처리해 정확성과 속도를 단일 지표로 합산한다.

---

## Open Questions

- 외부 벤치마크(BFCL, Terminal Bench 2.0)를 "adapting"한다는 것의 구체적인 방법은?
- LLM-as-a-judge에서 어떤 judge 모델을 사용하는가?
- `libs/evals` 디렉토리의 실제 eval 구현 구조는?
- 지속적으로 eval을 어떻게 "줄이는(reduce)" 것인가? (과도한 eval 제거 기준은?)

---

## Related Pages

- [[Evaluation]]
- [[Deep Agents]]
- [[Tool Calling]]
- [[Memory]]
- [[Context Engineering]]

## Sources

- `deepagents-blog-evals-2026-05-23`
