from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import asyncio

class ToolClient:
    def __init__(self):
        self.url = "http://localhost:8000/mcp/"

    async def multiply(self, a:int, b:int):
       async with streamablehttp_client(self.url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("multiply", {"a": a, "b": b})
                return result.content[0].text