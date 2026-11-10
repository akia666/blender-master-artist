# Official Blender Lab MCP adapter

Upstream: [Blender Lab MCP](https://projects.blender.org/lab/blender_mcp).
Installation is documented [here](../../docs/installation.md).

`BlenderLabAdapter(transport, shared_checkout)` accepts an async transport with
`list_tools()` and `call_tool(name, arguments)`. It checks actual schemas for
`execute_blender_code(code)`, imports BMA on the Blender host and reads the official
`status/result` response envelope. No custom socket bridge or replacement server ships.
`SessionTransport` wraps an MCP SDK `ClientSession`; `connect_stdio` manages its lifetime.

```python
from pathlib import Path
from bma.integration import connect_stdio

async def inspect(adapter):
    return await adapter.inspect()

# From an async entrypoint, with the official server already installed in this Python:
result = await connect_stdio(
    "python", ["-m", "blmcp"], inspect, shared_checkout=Path.cwd()
)
```

Available adapter operations: `inspect`, `validate`, `checkpoint`, `capture`, `edit`.
Edits are limited to `create_box`, `set_dimensions` and `add_bevel`. Before edit:
inventory existing names, finish research approval, register a new name or authorize
specific existing targets, save a checkpoint, and obtain a one-use `Workflow.permit`.
Supply current fingerprints for every existing target. See
[`examples/guarded_edit.py`](../../examples/guarded_edit.py) for a resumable practical driver.

Capture images with an artifact root matching the workflow root. `capture` defaults
to the inspection directory's parent as that root. Call the runtime directly for an
explicit `artifact_root` if the inspection directory is nested more deeply.

If a mutation fails or times out, the permit remains consumed. Inspect the scene,
compare fingerprints and decide what actually happened before any retry. BMA does
not silently reconnect and repeat a geometry edit. Offline snapshot/unit tests are
available without Blender and must never be reported as live integration success.
