---
type: concept
framework:
  - LangChain
  - LangGraph
  - Deep Agents
status: draft
confidence: medium
last_reviewed: 2026-05-23
sources:
  - deepagents-blog-evals-2026-05-23
  - deepagents-source-evals-structure-2026-05-23
---

# Evaluation

## 요약

Evaluation은 agent의 품질, 정확성, 동작을 측정하는 과정이다. **"More evals ≠ better agents"** — 프로덕션에서 중요한 동작을 반영하는 targeted eval을 만드는 것이 핵심이다.

Source: `deepagents-blog-evals-2026-05-23` ⚠️ blog 출처 (medium confidence)

## Why It Matters

- Eval 없이는 agent 개선이 실제인지 착시인지 판단할 수 없다.
- 모든 eval은 agent 동작을 이동시키는 압력 벡터다 — 추가할수록 시스템 프롬프트·tool 설명 조정에 영향을 준다.
- 좋은 PR에는 테스트가 포함되거나 갱신되므로, 업스트림 기여를 위해서도 평가 프레임워크는 중요하다.

## 핵심 개념

- **Targeted eval** — 프로덕션에서 중요한 동작만 측정하는 eval
- **Ideal trajectory** — 불필요한 액션 없이 올바른 결과를 내는 기준 경로
- **LLM-as-judge** — agent 출력의 의미론적 정확성을 LLM으로 채점
- **Correctness + Efficiency** — 정확성을 먼저, 그다음 효율성 측정
- **Eval taxonomy** — 출처가 아닌 "무엇을 테스트하는가"로 분류
- **SDK unit test vs model capability eval** — 반드시 분리해야 한다

## Deep Agents Eval 접근법 (Verified)

*Source: `deepagents-blog-evals-2026-05-23` ⚠️ blog*

### Eval 데이터 소싱 3가지

1. **Dogfooding** — 매일 직접 사용, 모든 오류를 eval 작성 기회로
2. **External benchmarks** — BFCL (function calling), Terminal Bench 2.0 (coding in sandbox) — 조정해서 사용
3. **Artisanal (hand-written)** — 중요 동작을 직접 단위 테스트로 작성

> **핵심 원칙:** SDK unit/integration test (system prompt passthrough, interrupt config, subagent routing)는 model capability eval과 분리한다. SDK 테스트는 어떤 모델도 통과하므로 scoring에 포함하면 신호가 없다.

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

분류 기준: **"어디서 왔는가"가 아니라 "무엇을 테스트하는가"**

### Correctness 측정 방법

| 상황 | 방법 |
|------|------|
| 내부 custom eval | custom assertions ("did the agent parallelize tool calls?") |
| 외부 벤치마크 (BFCL) | exact matching against ground truth |
| 의미론적 정확성 | LLM-as-a-judge |

### 5가지 메트릭

| Metric | Definition | 방향 |
|--------|-----------|------|
| Correctness | 태스크를 올바르게 완료했는가 | 높을수록 |
| Step ratio | 관찰된 agent steps / ideal steps | 낮을수록 |
| Tool call ratio | 관찰된 tool calls / ideal tool calls | 낮을수록 |
| Latency ratio | 관찰된 latency / ideal latency | 낮을수록 |
| Solve rate | expected steps / observed latency (오답이면 0) | 높을수록 |

**Solve rate**: latency ratio와 달리, 실패한 run을 0으로 처리 — 정확성과 속도를 단일 지표로 결합.

### Ideal Trajectory

**정의**: 불필요한 액션 없이 올바른 결과를 내는 기준 경로.

구성 요건:
- 최소한의 tool calls
- 독립적인 tool calls는 병렬화
- 불필요한 중간 턴 없음

예시: "현재 시간과 날씨를 알려줘"
- **Ideal**: 4 steps, 4 tool calls, ~8초
- **Inefficient (정확하지만 비효율)**: 6 steps, 5 tool calls, ~14초
  - step ratio 1.5, tool_call_ratio 1.25, latency_ratio 1.75, solve_rate 0.29

### 모델 선택 순서

1. **Correctness 먼저** — 원하는 태스크를 충분히 정확하게 수행하는 모델 필터링
2. **Efficiency 다음** — 통과 모델 중 correctness/latency/cost 트레이드오프 최적 선택

### 실행 환경

- **pytest + GitHub Actions** — CI에서 재현 가능한 환경
- **LangSmith** — 모든 eval run trace → 팀 전체 분석·수정 가능
- **태그 기반 subset 실행**: `--eval-category file_operations --eval-category tool_use`
- **오픈소스 구현**: [`github.com/langchain-ai/deepagents/tree/main/libs/evals`](https://github.com/langchain-ai/deepagents/tree/main/libs/evals)

## libs/evals 실제 구조 (소스 검증)

Source: `deepagents-source-evals-structure-2026-05-23`

### 디렉토리 구조

```
libs/evals/
├── deepagents_evals/        # 공유 eval 유틸리티
├── deepagents_harbor/       # Harbor 샌드박스 연동
├── tests/
│   └── evals/
│       ├── utils.py         # AgentTrajectory, TrajectoryScorer, run_agent
│       ├── conftest.py      # pytest fixtures, --model CLI
│       ├── pytest_reporter.py   # 메트릭 수집/리포트
│       └── llm_judge.py     # LLM-as-a-judge (OpenEvals 래퍼)
├── EVAL_CATALOG.md          # 111개 eval 전체 목록
└── MODEL_GROUPS.md          # 사용 가능한 LLM 모델 카탈로그
```

### TrajectoryScorer 패턴 (소스 검증)

```python
@pytest.mark.langsmith
def test_example(model: BaseChatModel) -> None:
    agent = create_deep_agent(model=model)
    run_agent(
        agent,
        model=model,
        query="...",
        scorer=(
            TrajectoryScorer()
            .expect(agent_steps=1)              # soft: 로그만, fail 없음
            .success(final_text_contains("4"))  # hard: 실패 시 test fail
        ),
    )
```

### LLM-as-a-judge 구현

```python
from tests.evals.llm_judge import llm_judge

scorer = TrajectoryScorer().success(
    llm_judge(
        "The answer mentions Paris.",
        "The tone is conversational.",
    )
)
```

- **OpenEvals** 라이브러리를 래핑
- human-readable criteria string을 LLM에 전달해 semantic 평가
- ⚠️ 구체적 judge 모델 미확인 (`MODEL_GROUPS.md` 확인 필요)

### Harbor 샌드박스 (Terminal Bench 2.0)

```bash
uv run harbor run \
  --agent-import-path deepagents_harbor:DeepAgentsWrapper \
  --dataset terminal-bench@2.0 -n 10 \
  --jobs-dir jobs/terminal-bench --env daytona
```

지원 환경: `docker`, `daytona`, `modal`, `runloop`

Harbor → LangSmith 통합: reward score (0.0~1.0) 피드백 자동 push.

## 프레임워크별 동작

### LangChain

- `langchain.evaluation`에 평가 유틸리티 제공
- *소스 필요 (미검증)*

### LangGraph

- LangGraph 앱은 LangSmith를 통해 trace 가능
- *소스 필요 (미검증)*

### Deep Agents

- [[Deep Agents]] eval 접근법은 위 섹션 참조
- 오픈소스 eval 구현: `libs/evals`
- Source: `deepagents-blog-evals-2026-05-23`

## Interpretation

- "eval = 압력 벡터" 관점은 eval을 단순 테스트가 아닌 **agent 동작 설계 도구**로 보는 것이다.
- ideal trajectory는 correctness만으로 부족하다는 인식에서 나온다 — 정확하지만 비효율적인 모델도 프로덕션에서 문제다.
- SDK test와 model capability eval을 분리하는 것은 신호 희석을 막기 위한 중요한 설계 결정이다.

## 미해결 질문

**해소됨 (2026-05-23):**
- ✅ `libs/evals` 디렉토리 실제 구조 → `deepagents_evals/` + `deepagents_harbor/` + `tests/evals/`. pytest + TrajectoryScorer. (Source: `deepagents-source-evals-structure-2026-05-23`)
- ✅ 외부 벤치마크 적용 방법 → Harbor를 통해 Terminal Bench 2.0 실행. `DeepAgentsWrapper`로 래핑, LangSmith로 결과 추적. (Source: `deepagents-source-evals-structure-2026-05-23`)

**잔여 질문:**
- LLM-as-a-judge에서 구체적으로 어떤 judge 모델을 사용하는가? → `MODEL_GROUPS.md` 확인 필요
- BFCL 벤치마크도 Harbor를 통해 동일하게 적용되는가? — Needs Source
- eval을 지속적으로 "줄이는(reduce)" 기준은 무엇인가? — Source: `deepagents-blog-evals-2026-05-23`
- 각 프레임워크에는 어떤 내장 평가 유틸리티가 존재하는가? (LangChain, LangGraph 소스 필요)
- LangSmith를 Trajectory evaluation에 어떻게 사용할 수 있는가?

## 관련 페이지

- [[Deep Agents]]
- [[LangChain]]
- [[LangGraph]]
- [[Tool Calling]]
- [[Memory]]
- [[Context Engineering]]

## Sources

- `deepagents-blog-evals-2026-05-23` ⚠️ blog (medium confidence)
