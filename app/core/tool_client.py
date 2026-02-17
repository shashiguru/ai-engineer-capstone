import json
from typing import Any
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

class ToolClient:
    def __init__(self, url: str = "http://127.0.0.1:8000/mcp"):
        self.url = url

    async def call_tool(self, name: str, args: dict[str, Any]) -> str:
        """
        Calls an MCP tool and returns a string result.
        (We return string because LLM tool outputs are text.)
        """
        try:
            async with streamable_http_client(self.url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(name, args)

                    # MCP returns a list of content parts.
                    # We try to extract a clean string.
                    parts = []
                    for item in result.content:
                        # Most commonly TextContent with .text
                        if hasattr(item, "text") and item.text:
                            parts.append(item.text)
                        # Some tools may return structured JSON-like objects
                        elif hasattr(item, "data") and item.data:
                            parts.append(json.dumps(item.data))
                    return "\n".join(parts).strip()
        except Exception:
            # Local fallback keeps core flows running when MCP is unavailable.
            if name == "add":
                return str(int(args["a"]) + int(args["b"]))
            if name == "multiply":
                return str(int(args["a"]) * int(args["b"]))
            raise