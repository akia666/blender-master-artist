"""Resumable usage pattern; this function does not invent or record user approval.

An async MCP client supplies a connected adapter. Model creation is only possible
after the user has approved research and advanced the persisted workflow to BLOCKOUT.
"""

from pathlib import Path

from bma.io import write_json
from bma.workflow import GateError, Stage, Workflow


async def create_blockout(adapter, journal_path):
    journal_path = Path(journal_path)
    workflow = Workflow.load(journal_path)
    if workflow.stage != Stage.BLOCKOUT:
        raise GateError("Present research, record the user's explicit approval, and advance first")
    inventory = await adapter.inspect()
    target = "Enclosure_Blockout"
    if target in {o["name"] for o in inventory["objects"]}:
        raise GateError("Target already exists; inspect before deciding whether to resume")
    workflow.register_new(target)
    checkpoint = await adapter.checkpoint(workflow.root, "before-blockout")
    permit = workflow.permit("create_box", [target], checkpoint["filename"])
    try:
        result = await adapter.edit(workflow, permit, {"dimensions": [0.24, 0.16, 0.079]}, {})
    finally:
        # Persist consumed permits even on a timeout; inspect instead of blindly retrying.
        workflow.save(journal_path)
    report = await adapter.validate(names=[target])
    write_json(workflow.root / "blockout-report.json", report)
    await adapter.capture(workflow.root / "blockout-views", [target])
    await adapter.checkpoint(workflow.root, "blockout")
    # Inspect the actual images and assemble submit artifacts before requesting approval.
    return result
