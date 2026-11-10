import json
from pathlib import Path
import tempfile
import unittest

from bma.io import file_digest, write_json
from bma.workflow import GateError, Stage, Workflow


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workflow = Workflow(self.root)
        for name in ["checkpoint.blend", "brief.md", "references.json", "changes.md"]:
            (self.root / name).write_text("Synthetic test fixture", encoding="utf-8")
        write_json(self.root / "checkpoint-receipt.json", {"filename": "checkpoint.blend",
                   "sha256": file_digest(self.root / "checkpoint.blend"), "fingerprints": {"Body": "synthetic-fingerprint"}})
        write_json(self.root / "inventory.json", {"objects": []})
        self.research = {"checkpoint": "checkpoint.blend", "checkpoint_receipt": "checkpoint-receipt.json",
                         "inventory": "inventory.json", "brief": "brief.md", "references": "references.json"}

    def approve_research(self):
        self.workflow.submit(self.research)
        self.workflow.approve("synthetic-test-approval")
        self.workflow.advance()

    def view_artifacts(self):
        write_json(self.root / "report.json", {"status": "pass", "coverage": "complete",
                                              "objects": [{"name": "Body", "fingerprint": "synthetic-fingerprint"}]})
        views = {}
        for name in ["front", "side", "top", "perspective"]:
            path = self.root / (name + ".png")
            path.write_bytes(b"Synthetic test image fixture")
            views[name] = {"path": path.name, "sha256": file_digest(path), "reviewed": True,
                           "reviewer_role": "agent", "observation": "Synthetic review fixture", "blocking_issues": []}
        write_json(self.root / "views.json", {"views": views, "fingerprints": {"Body": "synthetic-fingerprint"}})
        return {"checkpoint": "checkpoint.blend", "checkpoint_receipt": "checkpoint-receipt.json",
                "report": "report.json", "views": "views.json", "change_log": "changes.md"}

    def test_mismatched_geometry_evidence_cannot_be_approved(self):
        self.approve_research()
        artifacts = self.view_artifacts()
        views = json.loads((self.root / "views.json").read_text())
        views["fingerprints"]["Body"] = "another-revision"
        write_json(self.root / "views.json", views)
        with self.assertRaises(GateError):
            self.workflow.submit(artifacts)

    def test_no_implicit_advance_or_approval(self):
        with self.assertRaises(GateError):
            self.workflow.advance()
        self.workflow.submit(self.research)
        with self.assertRaises(GateError):
            self.workflow.approve("")

    def test_modified_submission_rejected(self):
        self.workflow.submit(self.research)
        (self.root / "brief.md").write_text("Changed after review")
        with self.assertRaises(GateError):
            self.workflow.approve("synthetic-test-approval")

    def test_existing_geometry_needs_scoped_authority(self):
        self.workflow.inventory(["Existing"])
        self.approve_research()
        with self.assertRaises(GateError):
            self.workflow.permit("set_dimensions", ["Existing"], "checkpoint.blend")
        self.workflow.allow_existing_edits(["Existing"], "synthetic-user-edit-scope")
        permit = self.workflow.permit("set_dimensions", ["Existing"], "checkpoint.blend")
        self.workflow.consume(permit)
        with self.assertRaises(GateError):
            self.workflow.consume(permit)

    def test_research_cannot_model(self):
        self.workflow.register_new("New")
        with self.assertRaises(GateError):
            self.workflow.permit("create_box", ["New"], "checkpoint.blend")

    def test_stale_checkpoint_blocks_edit(self):
        self.approve_research()
        self.workflow.register_new("New")
        permit = self.workflow.permit("create_box", ["New"], "checkpoint.blend")
        (self.root / "checkpoint.blend").write_text("Modified")
        with self.assertRaises(GateError):
            self.workflow.consume(permit)

    def test_approved_targets_need_reopen_and_invalidate_downstream(self):
        self.approve_research()
        self.workflow.register_new("Body")
        self.workflow.submit(self.view_artifacts())
        self.workflow.approve("synthetic-test-blockout")
        self.workflow.advance()
        with self.assertRaises(GateError):
            self.workflow.permit("add_bevel", ["Body"], "checkpoint.blend")
        self.workflow.reopen(Stage.BLOCKOUT, ["Body"], "synthetic-test-revision")
        self.assertEqual(self.workflow.stage, Stage.BLOCKOUT)
        self.workflow.permit("add_bevel", ["Body"], "checkpoint.blend")

    def test_unreviewed_or_changed_view_blocks_submission_and_advance(self):
        self.approve_research()
        artifacts = self.view_artifacts()
        views = json.loads((self.root / "views.json").read_text())
        views["views"]["front"]["reviewed"] = False
        write_json(self.root / "views.json", views)
        with self.assertRaises(GateError):
            self.workflow.submit(artifacts)
        views["views"]["front"]["reviewed"] = True
        write_json(self.root / "views.json", views)
        self.workflow.submit(artifacts)
        self.workflow.approve("synthetic-test")
        (self.root / "front.png").write_bytes(b"Changed image")
        with self.assertRaises(GateError):
            self.workflow.advance()

    def test_technical_fail_or_incomplete_blocks_submission(self):
        self.approve_research()
        artifacts = self.view_artifacts()
        for status, coverage in [("fail", "complete"), ("pass", "incomplete")]:
            write_json(self.root / "report.json", {"status": status, "coverage": coverage})
            with self.assertRaises(GateError):
                self.workflow.submit(artifacts)

    def test_path_escape_rejected(self):
        artifacts = dict(self.research, brief="../outside.md")
        with self.assertRaises(ValueError):
            self.workflow.submit(artifacts)

    def test_rejection_is_structured_and_does_not_approve(self):
        self.workflow.reject("blockout", "proportion mismatch", "hypothesis: wrong aspect", "adjust width", "side image")
        self.assertEqual(self.workflow.state["events"][-1]["data"]["problem"], "proportion mismatch")
        with self.assertRaises(GateError):
            self.workflow.advance()

    def test_journal_roundtrip_and_tamper_detection(self):
        self.workflow.inventory(["Existing"])
        path = self.root / "workflow.json"
        self.workflow.save(path)
        self.assertEqual(Workflow.load(path).state, self.workflow.state)
        state = json.loads(path.read_text())
        state["events"][0]["data"]["preserved"] = ["Changed"]
        write_json(path, state)
        with self.assertRaises(GateError):
            Workflow.load(path)

