from mcp.server.fastmcp import FastMCP

math_mcp = FastMCP("MathTools", stateless_http=True, json_response=True)

@math_mcp.tool()
def add(a:int, b:int) -> int:
    """
    Add two numbers together
    """
    return a + b

@math_mcp.tool()
def multiply(a:int, b:int) -> int:
    """Multiply two numbers together"""
    return a * b
