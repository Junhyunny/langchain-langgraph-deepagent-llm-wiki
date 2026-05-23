"""@tool decorator and tool execution mechanics.

Shows:
- @tool creates a StructuredTool (check the type)
- tool.name, tool.description come from function name and docstring
- tool.args_schema is a Pydantic model (becomes the LLM function schema)
- tool.invoke(args_dict) executes the tool and returns the raw result
- tool_call_id in ToolMessage must match AIMessage tool_calls[i]['id']
- agents execute tools by: extract args from ToolCall → invoke → wrap in ToolMessage
"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage, ToolCall, ToolMessage
from langchain_core.tools import tool


@tool
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b


def main() -> None:
    # --- 1. @tool produces StructuredTool ---
    print("type:", type(add).__name__)   # StructuredTool
    print("name:", add.name)             # add
    print("description:", add.description)

    # --- 2. args_schema → JSON schema sent to LLM ---
    schema = add.args_schema.model_json_schema()
    print("\nargs_schema JSON:")
    print(json.dumps(schema, indent=2))

    # --- 3. Normal invocation with a dict ---
    result = add.invoke({"a": 3, "b": 4})
    print("\nadd.invoke({'a': 3, 'b': 4}):", result)  # 7

    # --- 4. What an agent actually does: ToolCall → invoke(args) → ToolMessage ---
    #
    # AIMessage carries tool_calls from the LLM.
    # The agent extracts args and id, invokes the tool, then wraps in ToolMessage.
    # tool_call_id MUST match so the model can correlate result with request.
    ai_msg = AIMessage(
        content="",
        tool_calls=[ToolCall(name="add", args={"a": 10, "b": 20}, id="call_abc")],
    )
    tc = ai_msg.tool_calls[0]
    raw = add.invoke(tc["args"])                           # 30
    tm = ToolMessage(content=str(raw), tool_call_id=tc["id"])

    print("\nAIMessage tool_call id :", tc["id"])
    print("ToolMessage tool_call_id:", tm.tool_call_id)
    print("IDs match               :", tc["id"] == tm.tool_call_id)  # True
    print("ToolMessage content     :", tm.content)                   # "30"


if __name__ == "__main__":
    main()
