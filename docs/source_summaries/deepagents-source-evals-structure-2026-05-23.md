# Source Summary: Deep Agents — libs/evals 디렉토리 구조

**Source ID:** `deepagents-source-evals-structure-2026-05-23`
**Type:** source_code + official_docs
**Framework:** Deep Agents
**URLs:**
- `https://github.com/langchain-ai/deepagents/tree/main/libs/evals`
- `https://raw.githubusercontent.com/langchain-ai/deepagents/main/libs/evals/EVAL_CATALOG.md`
- `https://raw.githubusercontent.com/langchain-ai/deepagents/main/libs/evals/CONTRIBUTING.md`
**Retrieved:** 2026-05-23

---

## 디렉토리 구조

```
libs/evals/
├── deepagents_evals/        # 공유 eval 유틸리티 (metrics, judge, base)
├── deepagents_harbor/       # Harbor 샌드박스 연동
├── scripts/                 # 유틸리티 스크립트
├── tests/
│   └── evals/
│       ├── utils.py         # 핵심: AgentTrajectory, TrajectoryScorer, run_agent
│       ├── conftest.py      # pytest fixtures, --model CLI 옵션
│       ├── pytest_reporter.py   # 효율성 메트릭 수집 및 리포트 생성
│       └── llm_judge.py     # LLM-as-a-judge (OpenEvals 래퍼)
├── AGENTS.md
├── CONTRIBUTING.md
├── EVAL_CATALOG.md          # 111개 eval 전체 목록
├── MODEL_GROUPS.md          # 사용 가능한 LLM 모델 카탈로그
├── pyproject.toml
└── uv.lock
```

---

## Eval 카탈로그 (111개, 7개 카테고리)

| 카테고리 | 개수 | 테스트 내용 |
|---------|------|-----------|
| File Operations | 13 | 파일 읽기/쓰기/편집, 디렉토리 조작, 병렬 쓰기, 파일 복구 |
| Retrieval | 6 | 패턴 검색(grep/glob), 병렬 문서 검색 |
| Tool Use | 53 | 단일/멀티 tool 오케스트레이션, 그래프/관계형 쿼리 |
| Memory | 22 | 지속적 컨텍스트, 선호도 학습, 정보 recall, 환각 방지 |
| Conversation | 3 | 멀티턴 대화, 제약 충족 |
| Summarization | 5 | 콘텐츠 압축, 태스크 계속 |
| Unit Test | 9 | Skills, 서브에이전트, 시스템 설정 |

---

## Eval 구조 (pytest 기반)

### TrajectoryScorer — 두 계층 assertion 모델

```python
@pytest.mark.langsmith
def test_example(model: BaseChatModel) -> None:
    agent = create_deep_agent(model=model)
    run_agent(
        agent,
        model=model,
        query="What is 2 + 2?",
        scorer=(
            TrajectoryScorer()
            .expect(agent_steps=1)           # soft assertion: 로그만, fail 없음
            .success(final_text_contains("4"))  # hard assertion: fail하면 테스트 실패
        ),
    )
```

| assertion | 메서드 | 동작 |
|-----------|--------|------|
| **Hard fail** | `.success(...)` | 실패 시 테스트 fail. 정확성(correctness) 검사 |
| **Soft (logged)** | `.expect(...)` | 실패해도 fail 없음. 효율성(step/tool 수) 추적 |

### 핵심 컴포넌트

- `AgentTrajectory` — agent 실행 전체 경로 기록
- `TrajectoryScorer` — `.success()` / `.expect()` 조합으로 scoring 정의
- `run_agent()` — agent 실행 + scoring 적용 + 메트릭 수집
- `llm_judge()` — OpenEvals 기반 LLM-as-a-judge (semantic 평가)

---

## 메트릭 정의

| 메트릭 | 설명 | 계산 방식 |
|--------|------|----------|
| `correctness` | 모든 hard assertion을 통과한 테스트 비율 | (통과 수) / (전체 수) |
| `step_ratio` | 실제 vs 기대 agent steps 비율 | actual / expected (micro-averaged) |
| `tool_call_ratio` | 실제 vs 기대 tool 호출 수 비율 | actual / expected |
| `solve_rate` | 통과 테스트의 기대 단계 수 / 소요 시간 | expected_steps / duration_s (평균) |

멀티-trial 집계 (`evals_trials.yml`):
```json
{
  "metrics": {
    "correctness": {"n": 5, "mean": 0.49, "stdev": 0.012},
    "solve_rate": {"n": 5, "mean": 0.38, "stdev": 0.009}
  },
  "category_scores": {
    "memory": {"n": 5, "mean": 0.62, "stdev": 0.018}
  }
}
```

---

## LLM-as-a-judge

```python
from tests.evals.llm_judge import llm_judge

scorer = TrajectoryScorer().success(
    llm_judge(
        "The answer mentions the capital of France is Paris.",
        "The tone is conversational, not robotic.",
    )
)
```

- `llm_judge`는 **OpenEvals**를 래핑한 `SuccessAssertion` 구현체
- human-readable criteria string을 LLM에 전달해 semantic 평가
- ⚠️ 어떤 구체적 judge 모델(GPT-4o vs Claude vs 기타)을 사용하는지는 미확인 — `MODEL_GROUPS.md` 확인 필요

---

## Harbor 샌드박스 통합

```bash
# Terminal Bench 2.0 실행 예시
uv run harbor run \
  --agent-import-path deepagents_harbor:DeepAgentsWrapper \
  --dataset terminal-bench@2.0 \
  -n 10 \
  --jobs-dir jobs/terminal-bench \
  --env daytona
```

지원 환경: `docker`, `daytona`, `modal`, `runloop`

**LangSmith 통합 워크플로:**
1. Harbor tasks에서 dataset 생성
2. LangSmith experiment tracking으로 benchmark 실행
3. `harbor_langsmith.py add-feedback`으로 reward score (0.0~1.0) 피드백 push

---

## CI/CD

- `evals.yml` — GitHub Actions 자동 테스트
- `harbor.yml` — Harbor 샌드박스 테스트
- 외부 벤치마크: Terminal Bench 2.0 (Harbor), BFCL (블로그 언급)

---

## 해소된 Open Questions

- ✅ `libs/evals 디렉토리 실제 구조` → `deepagents_evals/` + `deepagents_harbor/` + `tests/evals/`. pytest + TrajectoryScorer 패턴. (Source: `deepagents-source-evals-structure-2026-05-23`)
- ✅ `외부 벤치마크 적용 방법` → Harbor 통해 Terminal Bench 2.0 실행. `DeepAgentsWrapper`로 agent 래핑. LangSmith로 결과 추적. (Source: `deepagents-source-evals-structure-2026-05-23`)
- ✅ `메트릭 정의` → correctness(hard assertion 통과율), step_ratio, tool_call_ratio, solve_rate. (Source: `deepagents-source-evals-structure-2026-05-23`)
- ✅ `eval 줄이는 기준` → `.expect()`(soft)는 fail 없이 로그만. `.success()`(hard)만 실패 조건. 다수 통과가 기준이 되는 것은 정량 임계값이 아닌 팀 판단으로 보임 — Needs Verification.

---

## 잔여 Open Questions

- ⚠️ LLM-as-a-judge에서 구체적으로 어떤 judge 모델(GPT-4o, Claude, etc.)을 사용하는가? — `MODEL_GROUPS.md` 확인 필요
- `BFCL` 벤치마크는 Harbor를 통해 동일한 방식으로 적용되는가? — Needs Source
- `latency_ratio` 메트릭이 블로그에서 언급됐지만 CONTRIBUTING에서는 `solve_rate`로 보임 — 동일한가? — Needs Verification
