import json
import time
from typing import Any
import uuid

from openai import AsyncOpenAI
from app.core.config import OPENAI_API_KEY, OPENAI_MODEL
from app.core.tool_client import ToolClient
from pydantic import ValidationError
from app.core.tool_schemas import AddArgs, MultiplyArgs
import hashlib
from app.core.tool_log_repo import insert_tool_log

ALLOWED_TOOLS = {"add","multiply"}
MAX_TOOL_CALLS_PER_REQUEST = 5


# Define the tools your LLM is allowed to call
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "Add two integers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "Multiply two integers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
        },
    },
]

def hash_args(args: dict) -> str:
    raw = json.dumps(args, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

class LLMClient:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing. Put it in .env")
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.tool_client = ToolClient()

    async def chat_with_tools(self, user_message: str, request_id: str) -> tuple[str, dict]:
        """
        LLM decides if tool call is needed. If yes:
        - execute tool via MCP
        - return tool result back to LLM
        - LLM produces final answer
        """
        overall_start = time.perf_counter()
        tools_used: list[dict[str, Any]] = []
        tool_calls_count = 0

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": "You are a helpful assistant. Use tools for exact math."},
            {"role": "user", "content": user_message},
        ]

        # loop in case model calls multiple tools
        for _ in range(5):
            resp = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            choice = resp.choices[0]
            msg = choice.message


            # If no tool calls, we're done
            if not msg.tool_calls:
                latency_ms = (time.perf_counter() - overall_start) * 1000.0
                meta = {
                    "model": OPENAI_MODEL,
                    "latency_ms": round(latency_ms, 2),
                    "tools_used": tools_used,
                }
                if resp.usage:
                    meta.update(
                        {
                            "prompt_tokens": resp.usage.prompt_tokens,
                            "completion_tokens": resp.usage.completion_tokens,
                            "total_tokens": resp.usage.total_tokens,
                        }
                    )
                return (msg.content or "").strip(), meta

            # Model wants to call tools
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [tc.model_dump() for tc in msg.tool_calls],
                }
            )

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments or "{}")
                if tool_name not in ALLOWED_TOOLS:
                    raise ValueError(f"Tool {tool_name} is not allowed")
                
                tool_calls_count += 1
                if tool_calls_count > MAX_TOOL_CALLS_PER_REQUEST:
                    raise ValueError(f"Tool calls limit of {MAX_TOOL_CALLS_PER_REQUEST} reached")

                try:
                    if tool_name == "add":
                        validated = AddArgs.model_validate(tool_args)
                        tool_args = validated.model_dump()
                    elif tool_name == "multiply":
                        validated = MultiplyArgs.model_validate(tool_args)
                        tool_args = validated.model_dump()
                    else:
                        raise ValueError(f"Tool {tool_name} is not allowed")
                except ValidationError as e:
                    raise ValueError(f"Invalid tool arguments {tool_name}: {e}")

                tool_start = time.perf_counter()
                args_hash = hash_args(tool_args)
                tool_latency_ms = None

                try:
                    tool_output = await self.tool_client.call_tool(tool_name, tool_args)
                    tool_latency_ms = (time.perf_counter() - tool_start) * 1000.0

                    # Tool output validation for math tools:
                    # Should be numeric string
                    if tool_name in {"add", "multiply"}:
                        stripped = tool_output.strip()
                        if not stripped.lstrip("-").isdigit():
                            raise ValueError(f"Tool returned non-numeric output: {tool_output}")

                    insert_tool_log(
                        request_id=request_id,
                        tool_name=tool_name,
                        args_hash=args_hash,
                        args=tool_args,
                        tool_latency_ms=round(tool_latency_ms, 2),
                        tool_output_preview=tool_output,
                        success=True,
                    )

                except Exception as e:
                    if tool_latency_ms is None:
                        tool_latency_ms = (time.perf_counter() - tool_start) * 1000.0
                    insert_tool_log(
                        request_id=request_id,
                        tool_name=tool_name,
                        args_hash=args_hash,
                        args=tool_args,
                        tool_latency_ms=round(tool_latency_ms, 2),
                        tool_output_preview="",
                        success=False,
                        error=str(e),
                    )
                    raise

                tools_used.append(
                    {
                        "name": tool_name,
                        "args": tool_args,
                        "tool_latency_ms": round(tool_latency_ms, 2),
                    }
                )

                # Send tool result back to model
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_output or "",
                    }
                )

        # Safety fallback
        latency_ms = (time.perf_counter() - overall_start) * 1000.0
        return (
            "I couldn't complete the request with tools.",
            {"model": OPENAI_MODEL, "latency_ms": round(latency_ms, 2), "tools_used": tools_used},
        )
