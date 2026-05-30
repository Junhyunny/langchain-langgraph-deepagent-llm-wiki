"""bind_tools — how the LLM learns what tools exist.

Shows:
- @tool → tool_call_schema (the JSON schema the LLM receives)
- convert_to_openai_tool → exact API payload sent in tools=[] parameter
- InjectedToolArg fields are excluded from the schema (LLM never sees them)
- bind_tools is abstract on BaseChatModel — each provider implements its own conversion

No LLM call is made. All output is the schema transformation that happens
before the model is called, so no API key is needed.

Conceptual flow for Tool Calling:
  [1] Define tool with @tool (name + description + typed args)
         ↓
  [2] model.bind_tools([tool]) → attaches JSON schema to model's call params
         ↓ (actual LLM call happens here)
  [3] LLM reads schema, picks a tool → AIMessage(tool_calls=[{name, args, id}])
         ↓
  [4] Runtime executes: tool.invoke(tool_call) → ToolMessage(content, tool_call_id)
         ↓
  [5] ToolMessage added to history → LLM called again → final AIMessage

Steps [1] and [2] (schema side) are shown here.
Steps [3]-[5] (execution side) are shown in 02_tool_calling.py.
"""

from __future__ import annotations

import json

from langchain_core.tools import InjectedToolArg, tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from typing import Annotated


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city.

    Args:
        city: The name of the city to look up.
    """
    return f"Sunny in {city}, 22°C"


@tool
def calculate(expression: str, precision: int = 2) -> str:
    """Evaluate a mathematical expression and return the result.

    Args:
        expression: A math expression like '3 + 4 * 2'.
        precision: Decimal places in the result.
    """
    result = eval(expression)  # noqa: S307  (demo only)
    return str(round(result, precision))


@tool
def search_database(
    query: str,
    user_id: Annotated[str, InjectedToolArg()],
) -> str:
    """Search the customer database.

    Args:
        query: Search terms to look for.
    """
    return f"Results for '{query}' (user={user_id})"


def main() -> None:
    # --- 1. tool_call_schema: what the LLM sees ---
    #
    # BaseTool.tool_call_schema is the JSON Schema that gets embedded in the
    # tools=[] parameter of the API call.
    # InjectedToolArg fields are stripped — the LLM is never told they exist.
    print("=" * 60)
    print("1. tool_call_schema (raw JSON Schema)")
    print("=" * 60)
    # tool_call_schema is a Pydantic BaseModel subclass (InjectedToolArg fields excluded)
    # call .model_json_schema() to get the serializable dict
    for t in [get_weather, calculate, search_database]:
        print(f"\n--- {t.name} ---")
        print(json.dumps(t.tool_call_schema.model_json_schema(), indent=2))

    # --- 2. convert_to_openai_tool: exact OpenAI API payload ---
    #
    # This is what BaseChatOpenAI.bind_tools() produces internally.
    # Wrapped in {"type": "function", "function": {...}} as OpenAI requires.
    print("\n" + "=" * 60)
    print("2. convert_to_openai_tool → OpenAI API payload")
    print("=" * 60)
    for t in [get_weather, calculate, search_database]:
        openai_schema = convert_to_openai_tool(t)
        print(f"\n--- {t.name} ---")
        print(json.dumps(openai_schema, indent=2))

    # --- 3. InjectedToolArg exclusion ---
    #
    # search_database has 'user_id' as InjectedToolArg.
    # The LLM schema only shows 'query'. The runtime injects 'user_id' separately.
    print("\n" + "=" * 60)
    print("3. InjectedToolArg exclusion")
    print("=" * 60)
    all_params = list(search_database.args_schema.model_fields.keys())
    schema_params = list(search_database.tool_call_schema.model_json_schema().get("properties", {}).keys())
    print(f"Function signature params : {all_params}")
    print(f"LLM-visible schema params : {schema_params}")
    print(f"Hidden from LLM           : {set(all_params) - set(schema_params)}")

    # --- 4. What bind_tools does conceptually ---
    #
    # model.bind_tools([get_weather, calculate]) is equivalent to:
    #   model.bind(tools=[convert_to_openai_tool(t) for t in tools])
    #
    # The resulting model, when called, includes the tools payload in the API
    # request. The LLM reads the descriptions and decides which tool to call.
    print("\n" + "=" * 60)
    print("4. What bind_tools produces (conceptual)")
    print("=" * 60)
    tools_payload = [convert_to_openai_tool(t) for t in [get_weather, calculate]]
    print("tools= parameter in API call:")
    print(json.dumps(tools_payload, indent=2))
    print(
        "\nThis payload is what the LLM reads to decide:\n"
        "  - which tool to call\n"
        "  - what arguments to pass\n"
        "  - how to describe the call in AIMessage.tool_calls"
    )


if __name__ == "__main__":
    main()
