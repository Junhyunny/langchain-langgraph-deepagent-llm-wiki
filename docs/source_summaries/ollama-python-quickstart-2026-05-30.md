---
type: source_summary
source_id: ollama-python-quickstart-2026-05-30
framework: Ollama
retrieved_at: 2026-05-30
status: draft
confidence: high
---

# Source Summary: Ollama Python Library — Quickstart

## Source Info
- **Source ID:** `ollama-python-quickstart-2026-05-30`
- **Type:** official_docs
- **Repo:** `https://github.com/ollama/ollama-python`
- **File:** `README.md`
- **Commit:** UNKNOWN (main branch, 2026-05-30 기준)

---

## Key Facts

### 전제 조건
- Ollama가 설치되어 **실행 중**이어야 함.
- 호출 전 모델을 먼저 pull 해야 함: `ollama pull llama3.2` (또는 `ollama pull gemma3`).

### 설치
- `pip install ollama`

### 첫 호출 패턴

```python
from ollama import chat
from ollama import ChatResponse

response: ChatResponse = chat(model='llama3.2', messages=[
  {
    'role': 'user',
    'content': 'Why is the sky blue?',
  },
])
print(response['message']['content'])
# 또는 속성 접근
print(response.message.content)
```

### Chat vs Generate

```python
import ollama

# 대화형 (messages 리스트)
ollama.chat(model='llama3.2', messages=[{'role': 'user', 'content': '...'}])

# 단순 생성 (prompt 문자열)
ollama.generate(model='llama3.2', prompt='...')
```

### Streaming

```python
stream = chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': '...'}],
    stream=True,
)
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)
```

### 모델 관리

```python
ollama.pull('llama3.2')    # 모델 다운로드
ollama.list()              # 설치된 모델 목록
ollama.delete('llama3.2')  # 모델 삭제
```

### 에러 처리

```python
try:
    ollama.chat(model='nonexistent-model', messages=[...])
except ollama.ResponseError as e:
    print('Error:', e.error)
```

---

## Important Terms
- [[Token]] — 로컬 모델도 동일한 토큰 기반 처리
- [[Chat Models]] — LangChain은 `langchain_ollama.ChatOllama`로 이 패턴을 추상화 (⚠️ 별도 소스 필요)

---

## Interpretation
- Ollama는 로컬 하드웨어에서 오픈소스 LLM을 실행하는 런타임.
- `ollama` Python 라이브러리는 Ollama REST API(`localhost:11434`)를 래핑한 클라이언트 (⚠️ 추정, 소스 미확인).
- API 키 불필요 — 완전 로컬 실행.
- LangChain과 통합하려면 `langchain-ollama` 패키지의 `ChatOllama`를 쓰는 것이 일반적 (⚠️ 별도 소스 필요).

---

## Open Questions
- LangChain `ChatOllama` 초기화 패턴은? (`langchain-ollama` 패키지 소스 필요)
- Ollama가 지원하는 모델 목록은? (https://ollama.com/library)
- GPU 가속이 자동으로 활성화되는가?

---

## Used By
- [[LLM API 첫 호출]]
