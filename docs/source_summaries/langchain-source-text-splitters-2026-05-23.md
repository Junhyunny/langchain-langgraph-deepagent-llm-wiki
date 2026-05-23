---
type: source_summary
source_id: langchain-source-text-splitters-2026-05-23
framework:
  - LangChain
status: verified
confidence: high
retrieved_at: "2026-05-23"
url: "https://github.com/langchain-ai/langchain/tree/master/libs/text-splitters/langchain_text_splitters"
---

# Source Summary: LangChain Text Splitters

## Source Info
- **Type:** source_code
- **Package:** `langchain-text-splitters` (별도 패키지 — `langchain-core`와 분리)
- **Files:** `character.py`, `base.py`
- **Commit:** UNKNOWN (master branch, 2026-05-23 기준)

---

## Key Facts

### TextSplitter 기반 클래스 (`base.py`)

**상속:** `BaseDocumentTransformer, ABC`

**`__init__` 파라미터 (모든 TextSplitter 공통):**

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `chunk_size` | `4000` | 청크 최대 크기 |
| `chunk_overlap` | `200` | 청크 간 겹치는 문자 수 |
| `length_function` | `len` | 청크 길이 측정 함수 |
| `keep_separator` | `False` | 구분자 유지 여부 (`True`=start, `"start"`, `"end"`) |
| `add_start_index` | `False` | 메타데이터에 청크 시작 인덱스 추가 |
| `strip_whitespace` | `True` | 청크 앞뒤 공백 제거 |

**유효성 검사:**
- `chunk_size > 0` (ValueError)
- `chunk_overlap >= 0` (ValueError)
- `chunk_overlap <= chunk_size` (ValueError)

**추상 메서드:** `split_text(text: str) -> list[str]`

**편의 메서드:**
- `create_documents(texts, metadatas)` → `list[Document]`
- `split_documents(documents)` → `list[Document]`
- `_merge_splits(splits, separator)` → `list[str]` (chunk_size, chunk_overlap 기반 병합)

---

### CharacterTextSplitter (`character.py`)

단일 구분자를 사용해 텍스트를 분할.

```python
CharacterTextSplitter(
    separator="\n\n",         # 기본 구분자: 두 줄 바꿈
    is_separator_regex=False, # regex 여부
    **TextSplitter_kwargs
)
```

- 분할: `re.split(separator, text)`
- lookaround 정규식(`(?=`, `(?<!` 등) 감지 시 구분자 재삽입 생략

---

### RecursiveCharacterTextSplitter (`character.py`)

separators 리스트를 순서대로 시도해 텍스트를 재귀 분할. 범용 텍스트의 공식 권장 방법.

```python
RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " ", ""],  # 기본값 — 범용
    keep_separator=True,                  # 기본값 (CharacterTextSplitter와 다름 ⚠️)
    is_separator_regex=False,
    **TextSplitter_kwargs
)
```

**내부 알고리즘 (`_split_text`):**
1. separators 리스트를 순서대로 순회
2. 현재 텍스트에서 첫 번째로 매칭되는 구분자 선택
3. 선택된 구분자로 분할
4. 분할 결과가 `chunk_size`보다 작으면 `good_splits`에 축적
5. `chunk_size` 초과 조각은 남은 구분자 리스트로 재귀 분할
6. `_merge_splits()`로 최종 병합

**`from_language()` classmethod:**
```python
splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=1000,
    chunk_overlap=200,
)
# is_separator_regex=True로 자동 설정
```

**`get_separators_for_language()` 지원 언어 (30+):**
Python, Markdown, HTML, LaTeX, C/CPP, Go, Java, Kotlin, JS, TS, PHP, Proto, R, RST, Ruby, Elixir, Rust, Scala, Swift, C#, Solidity, COBOL, Lua, Haskell, PowerShell, VisualBasic6 등

언어별 예시:
- `Python`: `["\nclass ", "\ndef ", "\n\tdef ", "\n\n", "\n", " ", ""]`
- `Markdown`: `["\n#{1,6} ", "```\n", "\n\n", "\n", " ", ""]`
- `JS/TS`: `["\nfunction ", "\nconst ", "\nclass ", "\nif ", ...]`

---

### _split_text_with_regex (내부 헬퍼)

```python
def _split_text_with_regex(
    text: str, separator: str, *, keep_separator: bool | Literal["start", "end"]
) -> list[str]
```

- `keep_separator=False`: 구분자 제거
- `keep_separator=True` 또는 `"start"`: 구분자를 청크 **앞**에 붙임
- `keep_separator="end"`: 구분자를 청크 **뒤**에 붙임
- 빈 문자열 필터링: `[s for s in splits if s]`

---

## Interpretation

- `RecursiveCharacterTextSplitter`의 기본 `keep_separator=True`는 `CharacterTextSplitter`의 기본 `keep_separator=False`와 다르다. 이 차이가 분할 결과에 영향을 줄 수 있다.
- 재귀 알고리즘은 "큰 구분자부터 시도 → 실패하면 더 세밀한 구분자로" 전략이다. 이는 문단 단위 분할을 먼저 시도하고 실패하면 줄 단위, 단어 단위로 fallback한다.
- `from_language()`는 내부적으로 `is_separator_regex=True`를 설정하므로, language-specific separators는 모두 정규식으로 해석된다.
- `chunk_size` 기본값이 4000이지만 RAG에서는 일반적으로 500~2000으로 낮춰 사용한다 (임베딩 모델 context limit 고려).

---

## Open Questions

- `_merge_splits()`의 정확한 구현은? `chunk_overlap` 구현 방식은? (base.py 나머지 부분 미수집)
- `keep_separator=True`일 때 구분자가 청크의 앞에 붙는가, 뒤에 붙는가? (기본값 True → "start"와 동일한가?)
- `from_language()`의 `is_separator_regex=True`가 기본 separators에도 적용되면 `\n\n`, `\n` 등은 어떻게 처리되는가?
- `langchain-text-splitters` 패키지는 언제 분리됐는가? `langchain-core`에서는 re-export되는가?
- `TokenTextSplitter`는 어디에 있는가? (`tiktoken`, `transformers` 선택적 import 존재)

---

## Related Wiki Pages

- [[RAG]]
- [[LangChain]]
- [[LangChain Code Map]]

## Sources

- `langchain-source-text-splitters-2026-05-23`
