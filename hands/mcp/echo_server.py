"""
A tiny local MCP server used to prove the Specter MCP adapter works
end-to-end with zero external dependencies.

Run standalone for a sanity check:
    python -m hands.mcp.echo_server
(it will sit waiting on stdio, which is normal — Ctrl+C to quit)

It is normally launched automatically by the MCP adapter via mcp_servers.json.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("specter-echo")


@mcp.tool()
def echo(text: str) -> str:
    """Echoes back whatever text it is given. Useful for testing connectivity."""
    return f"echo: {text}"


@mcp.tool()
def add(a: float, b: float) -> str:
    """Adds two numbers together and returns the sum."""
    return f"{a} + {b} = {a + b}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
