import json
import asyncio
from pathlib import Path
import tempfile
import unittest

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from bma.integration import BlenderLabAdapter, IntegrationError, unpack_result
from bma.workflow import GateError, Stage, Workflow


class FakeTransport:
    def __init__(self):
        self.calls = []

    async def list_tools(self):
        return {"tools": [{"name": "execute_blender_code", "inputSchema": {
            "properties": {"code": {"type": "string"}}, "required": ["code"]}}]}

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {"content": [{"type": "text", "text": json.dumps({"status": "ok", "result": {"synthetic": True}})}]}


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_capability_detection_is_not_live_verification(self):
        adapter = BlenderLabAdapter(FakeTransport(), ".")
        self.assertFalse((await adapter.detect())["live_verified"])

    async def test_bad_schema_rejected(self):
        class Wrong(FakeTransport):
            async def list_tools(self):
                return {"tools": [{"name": "execute_python", "inputSchema": {}}]}
        with self.assertRaises(IntegrationError):
            await BlenderLabAdapter(Wrong(), ".").detect()

    async def test_native_json_envelope_and_error_handling(self):
        self.assertEqual(unpack_result({"structuredContent": {"status": "ok", "result": {"a": 1}}}), {"a": 1})
        for response in [{"isError": True}, {"structuredContent": {"status": "error", "message": "failure"}},
                         {"content": [{"type": "text", "text": "Error connecting"}]}]:
            with self.assertRaises(IntegrationError):
                unpack_result(response)

    async def test_inspection_uses_official_code_contract(self):
        transport = FakeTransport()
        adapter = BlenderLabAdapter(transport, ".")
        self.assertTrue((await adapter.inspect())["synthetic"])
        code = transport.calls[0][1]["code"]
        compile(code, "generated_mcp_code", "exec")
        self.assertIn("result = dispatch('inventory'", code)

    async def test_mutation_requires_consumable_permit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "before.blend").write_bytes(b"Synthetic checkpoint")
            workflow = Workflow(root)
            workflow.state["stage"] = Stage.BLOCKOUT.value  # Deliberate synthetic state-machine fixture.
            workflow.register_new("New")
            permit = workflow.permit("create_box", ["New"], "before.blend")
            transport = FakeTransport()
            adapter = BlenderLabAdapter(transport, ".")
            await adapter.edit(workflow, permit, {"dimensions": [1, 1, 1]}, {})
            with self.assertRaises(GateError):
                await adapter.edit(workflow, permit, {"dimensions": [1, 1, 1]}, {})
            self.assertEqual(len(transport.calls), 1)

