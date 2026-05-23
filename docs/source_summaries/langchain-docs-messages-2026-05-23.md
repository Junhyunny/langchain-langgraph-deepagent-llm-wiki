---
type: source_summary
source_id: langchain-docs-messages-2026-05-23
framework:
  - LangChain
status: verified
confidence: high
retrieved_at: "2026-05-23"
url: "https://docs.langchain.com/oss/python/langchain/messages"
---

# Source Summary: LangChain Messages

## Key Facts

### 메시지의 정의

- 메시지는 LangChain에서 모델과 소통하는 기본 단위다.
- 메시지는 세 가지 요소를 가진다: **Role**(타입 식별), **Content**(텍스트/이미지/오디오 등), **Metadata**(응답 정보, 메시지 ID, 토큰 사용량)
- LangChain은 모든 모델 프로바이더에 걸쳐 동작하는 표준 메시지 타입을 제공한다.

### 메시지 타입 4종

| 타입 | 클래스 | 역할 |
|------|--------|------|
| `system` | `SystemMessage` | 모델의 동작 방식/페르소나 지정 |
| `human` | `HumanMessage` | 사용자 입력 (텍스트, 이미지, 오디오 등 멀티모달 지원) |
| `ai` | `AIMessage` | 모델 응답 (텍스트, tool_calls, 메타데이터) |
| `tool` | `ToolMessage` | tool 실행 결과를 모델에 전달 |

### SystemMessage

```python
system_msg = SystemMessage("You are a helpful coding assistant.")
```

### HumanMessage

```python
human_msg = HumanMessage(
    content="Hello!",
    name="alice",   # Optional: 여러 사용자 구분
    id="msg_123",   # Optional: 트레이싱용 고유 식별자
)
```

### AIMessage

모델 호출 결과로 반환되는 메시지.

**주요 속성:**
- `text` (string): 텍스트 내용
- `content` (string | dict[]): 원시 content
- `content_blocks` (ContentBlock[]): 표준화된 content blocks (lazy parse)
- `tool_calls` (dict[] | None): 모델이 호출한 tool call 목록. tool이 없으면 빈 리스트
- `id` (string): 고유 식별자
- `usage_metadata` (dict | None): 토큰 사용량 (input_tokens, output_tokens, total_tokens)
- `response_metadata`: 응답 메타데이터

**tool_calls 구조:**
```python
for tool_call in response.tool_calls:
    print(tool_call['name'])   # 도구 이름
    print(tool_call['args'])   # 도구 인자
    print(tool_call['id'])     # call ID — ToolMessage.tool_call_id와 매칭
```

**스트리밍 시 AIMessageChunk 반환:**
```python
chunks = []
full_message = None
for chunk in model.stream("Hi"):
    chunks.append(chunk)
    full_message = chunk if full_message is None else full_message + chunk
```

### ToolMessage

tool 실행 결과를 모델에 전달할 때 사용. `tool_call_id`가 `AIMessage.tool_calls`의 `id`와 반드시 일치해야 한다.

```python
tool_message = ToolMessage(
    content=weather_result,
    tool_call_id="call_123",  # AIMessage.tool_calls의 id와 매칭
    name="get_weather"
)
```

**ToolMessage 필수 속성:**
- `content` (string): tool 실행 결과 문자열
- `tool_call_id` (string): AIMessage의 tool call ID와 매칭
- `name` (string): 호출된 tool 이름
- `artifact` (dict): 모델에 전달되지 않는 추가 데이터

### 전형적인 tool call 흐름

```python
# 1. 사용자 질문
messages = [HumanMessage("What's the weather in San Francisco?")]

# 2. 모델이 tool_calls가 포함된 AIMessage 반환
ai_message = model_with_tools.invoke(messages)
# ai_message.tool_calls = [{"name": "get_weather", "args": {"location": "..."}, "id": "call_123"}]

# 3. tool 실행 후 ToolMessage 생성
tool_message = ToolMessage(content="Sunny, 72°F", tool_call_id="call_123", name="get_weather")

# 4. 대화 이력에 추가 후 모델 재호출
messages = messages + [ai_message, tool_message]
final_response = model.invoke(messages)
```

### 메시지 content의 3가지 형식

1. 문자열: `HumanMessage("Hello")`
2. 프로바이더 네이티브 형식 (OpenAI 등): `HumanMessage(content=[{"type": "text", ...}])`
3. LangChain 표준 content blocks: `HumanMessage(content_blocks=[...])`

### Standard content blocks (content_blocks 프로퍼티)

`content_blocks`는 `content`를 타입 안전한 표준 형식으로 lazy parse한다. Anthropic `thinking`, OpenAI `reasoning`이 `ReasoningContentBlock`으로 정규화된다.

### 딕셔너리 형식 지원

OpenAI chat completions 포맷으로도 메시지를 전달할 수 있다:
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"},
]
```

## Interpretation

- LangChain이 표준 메시지 타입을 제공하는 핵심 이유는 **프로바이더 중립성**이다 — OpenAI, Anthropic, Google 등 어느 모델을 쓰더라도 같은 코드로 동작한다.
- `ToolMessage.tool_call_id`가 `AIMessage.tool_calls[i]['id']`와 매칭돼야 한다는 것이 중요한 계약(contract)이다. 이를 어기면 모델이 tool 결과를 올바르게 연결하지 못한다.
- `AIMessageChunk`는 스트리밍 청크를 `+` 연산으로 누적할 수 있다.

## Open Questions

- `BaseMessage` 클래스 계층에서 총 14개 클래스 중 SystemMessage/HumanMessage/AIMessage/ToolMessage 외 나머지 10개는 무엇인가?
- `add_messages` reducer(LangGraph)와 `AIMessageChunk` 누적 방식의 관계는?

## Related Wiki Pages

- [[LangChain]]
- [[Tool Calling]]
- [[LangGraph]]

## Sources

- `langchain-docs-messages-2026-05-23`
