"""Client adapter for official Blender Lab MCP; reuses upstream communication."""

import json
from pathlib import Path

from bma.workflow import EDIT_OPERATIONS, GateError


class IntegrationError(RuntimeError):
    pass


def unpack_result(response):
    if hasattr(response, "model_dump"):
        response = response.model_dump(by_alias=True)
    if response.get("isError"):
        raise IntegrationError("Official MCP tool returned an error")
    def unwrap(value):
        if not isinstance(value, dict):
            raise IntegrationError("Official MCP result must be a JSON object")
        if value.get("status") == "error":
            raise IntegrationError("Blender rejected the operation: " + str(value.get("message", "unknown error")))
        if value.get("status") == "ok" and "result" in value:
            if not isinstance(value["result"], dict):
                raise IntegrationError("Blender returned a non-object result")
            return value["result"]
        return value

    if response.get("structuredContent") is not None:
        return unwrap(response["structuredContent"])
    for item in response.get("content", []):
        if item.get("type") == "text":
            try:
                result = json.loads(item["text"])
            except (ValueError, KeyError):
                continue
            if isinstance(result, dict):
                return unwrap(result)
    raise IntegrationError("Expected JSON result; no completion is inferred from plain text")


class BlenderLabAdapter:
    """Transport implements async list_tools() and call_tool(name, arguments)."""

    def __init__(self, transport, shared_checkout):
        self.transport = transport
        self.checkout = str(Path(shared_checkout).resolve())
        self.capabilities = {}

    async def detect(self):
        tools = await self.transport.list_tools()
        if hasattr(tools, "tools"):
            tools = tools.tools
        elif isinstance(tools, dict):
            tools = tools["tools"]
        for tool in tools:
            if hasattr(tool, "model_dump"):
                tool = tool.model_dump(by_alias=True)
            self.capabilities[tool["name"]] = tool.get("inputSchema", {})
        schema = self.capabilities.get("execute_blender_code")
        if schema is None or "code" not in schema.get("properties", {}):
            raise IntegrationError("Official execute_blender_code(code) capability is required")
        if set(schema.get("required", [])) - {"code"}:
            raise IntegrationError("Incompatible execute schema; do not assume a community adapter is equivalent")
        return {"adapter": "official-blender-lab", "tools": sorted(self.capabilities), "live_verified": False}

    async def _run(self, operation, arguments):
        if not self.capabilities:
            await self.detect()
        # Values are Python literals produced by repr, never interpolated shell code.
        code = ("import sys\n"
                f"_bma_root = {self.checkout!r}\n"
                "if _bma_root not in sys.path: sys.path.insert(0, _bma_root)\n"
                "from bma.blender_runtime import dispatch\n"
                f"result = dispatch({operation!r}, {arguments!r})\n")
        response = await self.transport.call_tool("execute_blender_code", {"code": code})
        return unpack_result(response)

    async def inspect(self):
        return await self._run("inventory", {})

    async def validate(self, **arguments):
        return await self._run("validate", arguments)

    async def checkpoint(self, directory, label="checkpoint"):
        return await self._run("checkpoint", {"directory": str(directory), "label": label})

    async def capture(self, directory, names, resolution=512):
        return await self._run("capture_views", {"directory": str(directory), "names": list(names),
                                                  "resolution": resolution})

    async def edit(self, workflow, permit, parameters, expected):
        if permit.operation not in EDIT_OPERATIONS:
            raise GateError("Edit operation is not supported")
        if permit.operation != "create_box" and set(expected) != set(permit.targets):
            raise GateError("Provide fingerprints for exactly the permitted targets")
        workflow.consume(permit)
        # One attempt. If transport fails, inspect Blender before requesting another permit.
        return await self._run(permit.operation, {"targets": list(permit.targets),
                                                 "parameters": parameters, "expected": expected})


class SessionTransport:
    def __init__(self, session):
        self.session = session

    async def list_tools(self):
        return await self.session.list_tools()

    async def call_tool(self, name, arguments):
        return await self.session.call_tool(name, arguments)


async def connect_stdio(command, args, callback, shared_checkout):
    """Run a caller-selected official server command; no setup/install/config mutations."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    parameters = StdioServerParameters(command=command, args=list(args))
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            adapter = BlenderLabAdapter(SessionTransport(session), shared_checkout)
            await adapter.detect()
            return await callback(adapter)
