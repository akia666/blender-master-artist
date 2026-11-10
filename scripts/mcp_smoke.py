"""Exercise the official server against an isolated Blender bridge, never a user scene.

Caller starts factory Blender with the official add-on and passes its server command.
All authority values below are explicitly synthetic test fixtures, never user approvals.
"""

import argparse
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bma.integration import connect_stdio
from bma.io import write_json
from bma.workflow import GateError, Stage, Workflow


async def smoke(adapter, output):
    detected = await adapter.detect()
    before = await adapter.inspect()
    if {o["name"] for o in before["objects"]} - {"Cube", "Camera", "Light"}:
        raise RuntimeError("Smoke test requires an isolated factory-startup scene")
    checkpoint = await adapter.checkpoint(output, "mcp-before")
    workflow = Workflow(output)
    workflow.state["stage"] = Stage.BLOCKOUT.value  # Synthetic workflow fixture, not user approval.
    workflow.inventory([o["name"] for o in before["objects"]])
    workflow.register_new("BMA_MCP_TestBox")
    permit = workflow.permit("create_box", ["BMA_MCP_TestBox"], checkpoint["filename"])
    await adapter.edit(workflow, permit, {"dimensions": [0.24, 0.16, 0.08]}, {})
    created = await adapter.inspect()
    box = next(o for o in created["objects"] if o["name"] == "BMA_MCP_TestBox")
    permit = workflow.permit("add_bevel", [box["name"]], checkpoint["filename"])
    await adapter.edit(workflow, permit, {"width": 0.002, "segments": 3}, {box["name"]: box["fingerprint"]})
    report = await adapter.validate(names=[box["name"]])
    if report["status"] != "pass":
        raise AssertionError("MCP-generated box failed technical validation")
    write_json(output / "report.json", report)
    views = await adapter.capture(output / "views", [box["name"]], resolution=128)
    final_checkpoint = await adapter.checkpoint(output, "mcp-after")
    after = await adapter.inspect()
    for original in before["objects"]:
        actual = next(o for o in after["objects"] if o["name"] == original["name"])
        if original["fingerprint"] != actual["fingerprint"]:
            raise AssertionError("MCP smoke test changed pre-existing mesh geometry")
    try:
        workflow.advance()
        raise AssertionError("Approval gate incorrectly allowed advancement")
    except GateError:
        pass
    result = {"adapter": detected["adapter"], "tools_detected": len(detected["tools"]),
              "blender_version": before["blender_version"], "live_verified": True,
              "checks": {"inspect": True, "create": True, "bevel": True, "validate": True,
                         "render_four_views": set(views["views"]) == {"front", "side", "top", "perspective"},
                         "save": True, "preserve_existing_geometry": True, "approval_blocks_advance": True},
              "final_checkpoint": final_checkpoint, "visual_status": "needs_review",
              "scope": "Synthetic isolated scene; no user stage approved"}
    workflow.save(output / "workflow.json")
    write_json(output / "mcp-smoke.json", result)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-command", required=True)
    parser.add_argument("--server-arg", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        parser.error("Use an empty output directory")
    result = asyncio.run(connect_stdio(args.server_command, args.server_arg,
                                     lambda adapter: smoke(adapter, output), Path(__file__).resolve().parents[1]))
    print(result)


if __name__ == "__main__":
    main()
