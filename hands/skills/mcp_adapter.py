"""
MCP (Model Context Protocol) adapter for Specter.

This is the highest-leverage skill module: instead of hand-writing one skill
per capability, it connects to any number of configured MCP servers, discovers
the tools each one exposes, and turns every tool into a normal Specter skill
(a BaseSkill subclass registered in SKILL_REGISTRY).

That means Discord (/run), the Flask UI, and the CLI all gain those tools for
free, with no changes to their code.

Design notes / tradeoffs
------------------------
* Connections are per-call: every discovery pass and every tool invocation
  opens a fresh stdio connection to the server, calls, and closes it. This is
  simple and robust (no long-lived subprocess lifecycle to babysit) at the cost
  of a little startup latency per call. Fine for a personal tool; can be
  upgraded to persistent sessions later if a server is called in a hot loop.
* The MCP SDK is async; Specter skills are sync. We bridge with asyncio.run()
  inside the sync methods. All current call sites (Discord via asyncio.to_thread,
  Flask request threads, the CLI main thread) run without an active event loop,
  so asyncio.run() is safe.
"""
import os
import json
import asyncio
from typing import Any, Dict, List, Type

from hands.skills.base import BaseSkill

# Project root = .../Specter (two levels up from this file: hands/skills/ -> hands/ -> root)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "mcp_servers.json")


def _load_config() -> Dict[str, dict]:
    """Reads mcp_servers.json. Returns {server_name: {command, args, env, disabled}}."""
    if not os.path.exists(_CONFIG_PATH):
        return {}
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("mcpServers", {}) or {}
    except Exception as e:
        print(f"[-] MCP: could not read {_CONFIG_PATH}: {e}")
        return {}


def _resolve_command(command: str) -> str:
    """
    Lets the config use the placeholder ${PYTHON} to mean 'this project's venv
    python', so configs stay portable across machines.
    """
    if command == "${PYTHON}":
        venv_py = os.path.join(_PROJECT_ROOT, "venv", "Scripts", "python.exe")
        return venv_py if os.path.exists(venv_py) else "python"
    return command


def _server_params(server_cfg: dict):
    """Builds StdioServerParameters from a single server's config block."""
    from mcp import StdioServerParameters

    command = _resolve_command(server_cfg["command"])
    args = list(server_cfg.get("args", []))
    # Merge configured env over the real environment so commands like npx/uvx
    # and PATH-dependent executables resolve correctly (esp. on Windows).
    env = {**os.environ, **(server_cfg.get("env") or {})}
    return StdioServerParameters(command=command, args=args, env=env)


def _content_to_text(result) -> str:
    """Flattens an MCP CallToolResult's content blocks into a single string."""
    parts: List[str] = []
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text is not None:
            parts.append(text)
        else:
            parts.append(str(block))
    return "\n".join(parts).strip()


async def _alist_tools(server_cfg: dict):
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client

    async with stdio_client(_server_params(server_cfg)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resp = await session.list_tools()
            return resp.tools


async def _acall_tool(server_cfg: dict, tool_name: str, arguments: dict):
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client

    async with stdio_client(_server_params(server_cfg)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(tool_name, arguments=arguments)


def _params_from_schema(input_schema: dict) -> Dict[str, str]:
    """Converts a tool's JSON input schema into Specter's {param: description} map."""
    if not input_schema:
        return {}
    props = input_schema.get("properties", {}) or {}
    required = set(input_schema.get("required", []) or [])
    params: Dict[str, str] = {}
    for key, spec in props.items():
        desc = spec.get("description") or spec.get("type", "value")
        tag = "required" if key in required else "optional"
        params[key] = f"({tag}) {desc}"
    return params


def _coerce_arg(value: Any, spec: dict) -> Any:
    """
    Skills are often called with string args (Discord/CLI parse key=value as
    strings). Coerce to the type the tool's schema expects so MCP validation
    passes.
    """
    if not isinstance(value, str):
        return value
    json_type = (spec or {}).get("type")
    try:
        if json_type == "integer":
            return int(value)
        if json_type == "number":
            return float(value)
        if json_type == "boolean":
            return value.strip().lower() in ("true", "1", "yes", "on")
        if json_type in ("object", "array"):
            return json.loads(value)
    except (ValueError, json.JSONDecodeError):
        pass
    return value


def _make_skill_class(server_name: str, server_cfg: dict, tool) -> Type[BaseSkill]:
    """Dynamically builds a BaseSkill subclass bound to one MCP tool."""
    input_schema = getattr(tool, "inputSchema", None) or {}
    schema_props = input_schema.get("properties", {}) or {}
    skill_name = f"mcp_{server_name}_{tool.name}"
    tool_desc = getattr(tool, "description", None) or tool.name

    class _MCPSkill(BaseSkill):
        name = skill_name
        description = f"[MCP:{server_name}] {tool_desc}"
        parameters = _params_from_schema(input_schema)

        # Bind connection details onto the class
        _server_cfg = server_cfg
        _tool_name = tool.name
        _schema_props = schema_props

        def execute(self, **kwargs) -> Dict[str, Any]:
            arguments = {
                k: _coerce_arg(v, self._schema_props.get(k, {}))
                for k, v in kwargs.items()
            }
            try:
                result = asyncio.run(
                    _acall_tool(self._server_cfg, self._tool_name, arguments)
                )
            except Exception as e:
                return {
                    "success": False,
                    "message": f"MCP call to '{self._tool_name}' on '{server_name}' failed: {e}",
                }

            text = _content_to_text(result) or "(no content returned)"
            if getattr(result, "isError", False):
                return {"success": False, "message": f"Tool reported an error: {text}"}
            return {"success": True, "message": text}

    _MCPSkill.__name__ = f"MCP_{server_name}_{tool.name}"
    _MCPSkill.__qualname__ = _MCPSkill.__name__
    return _MCPSkill


def load_mcp_skills(registry: Dict[str, Type[BaseSkill]]) -> None:
    """
    Connects to every enabled MCP server in mcp_servers.json, discovers its
    tools, and registers a skill class for each into `registry`.

    Failures are isolated per-server: a broken or unreachable server logs a
    warning and is skipped without affecting other servers or core skills.
    """
    servers = _load_config()
    if not servers:
        return

    for server_name, server_cfg in servers.items():
        if server_cfg.get("disabled"):
            print(f"[*] MCP: skipping disabled server '{server_name}'")
            continue
        if "command" not in server_cfg:
            print(f"[-] MCP: server '{server_name}' has no 'command'; skipping")
            continue

        try:
            tools = asyncio.run(_alist_tools(server_cfg))
        except Exception as e:
            print(f"[-] MCP: failed to connect to server '{server_name}': {e}")
            continue

        for tool in tools:
            skill_cls = _make_skill_class(server_name, server_cfg, tool)
            registry[skill_cls.name] = skill_cls
            print(f"[+] Loaded MCP skill: {skill_cls.name}")
