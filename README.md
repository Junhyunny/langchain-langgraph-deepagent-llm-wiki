# LangChain / LangGraph / Deep Agents — LLM 위키

이 저장소는 AI agent 프레임워크를 내부 구현까지 이해하고, 아키텍처를 추적하며, 실험을 수행하고, 궁극적으로 높은 품질의 업스트림 PR을 만들 수 있을 만큼 깊이 있게 학습하기 위한 위키다.

## 주요 중점 영역

- LangChain, LangGraph, Deep Agents
- 도구 호출, 상태 관리, 체크포인팅, 메모리
- 컨텍스트 엔지니어링, 서브에이전트, 평가
- 오픈소스 기여 워크플로

## 구조

```
docs/wiki/          # Curated knowledge base (main wiki)
docs/source_summaries/  # One summary per important source
docs/raw/           # Raw source material (git-ignored by default)
docs/raw_manifest.yml   # Source registry
examples/           # Runnable learning examples
reproductions/      # Minimal bug/behavior reproductions
evals/              # Evaluation cases and results
scripts/            # Automation scripts
```

## 시작하기

소스를 추가하는 방법, 위키 페이지를 작성하는 방법, PR을 준비하는 방법을 포함한 전체 안내는 [`AGENTS.md`](AGENTS.md)를 참조한다.

위키 인덱스는 [`docs/wiki/_index.md`](docs/wiki/_index.md)를 참조한다.

현재 학습 로드맵은 [`docs/wiki/_roadmap.md`](docs/wiki/_roadmap.md)를 참조한다.

## 대상 AI assistant

이 저장소는 Codex, Claude Code, GitHub Copilot 및 기타 코딩/작성 agent가 읽고 편집할 수 있도록 설계되었다. 모든 agent는 `AGENTS.md`의 규칙을 따라야 한다.