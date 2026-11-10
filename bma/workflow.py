"""Approval gates for cooperative agents; not user authentication or a sandbox."""

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import uuid

from bma.io import digest, file_digest, relative_file, write_json


class GateError(ValueError):
    pass


class Stage(str, Enum):
    RESEARCH = "RESEARCH"
    BLOCKOUT = "BLOCKOUT"
    PRIMARY_GEOMETRY = "PRIMARY_GEOMETRY"
    SECONDARY_GEOMETRY = "SECONDARY_GEOMETRY"
    DETAILING = "DETAILING"
    TOPOLOGY_REVIEW = "TOPOLOGY_REVIEW"
    MATERIALS = "MATERIALS"
    FINAL_VALIDATION = "FINAL_VALIDATION"


STAGES = list(Stage)
VIEWS = {"front", "side", "top", "perspective"}
EDIT_OPERATIONS = {"create_box", "set_dimensions", "add_bevel"}


@dataclass(frozen=True)
class EditPermit:
    token: str
    stage: str
    operation: str
    targets: tuple
    checkpoint: str
    checkpoint_hash: str


class Workflow:
    def __init__(self, root, state=None):
        self.root = Path(root).resolve()
        self.state = state or {
            "schema_version": "1.0", "stage": Stage.RESEARCH.value, "complete": False,
            "stages": {}, "preserved": [], "new_objects": [], "editable": [],
            "protected": [], "permits": {}, "events": [],
        }

    @classmethod
    def load(cls, path):
        path = Path(path)
        instance = cls(path.parent, json.loads(path.read_text(encoding="utf-8")))
        previous = "0" * 64
        for event in instance.state["events"]:
            content = {k: v for k, v in event.items() if k != "hash"}
            if content["previous"] != previous or digest(content) != event["hash"]:
                raise GateError("Journal event chain is invalid")
            previous = event["hash"]
        return instance

    def save(self, path):
        if Path(path).resolve().parent != self.root:
            raise GateError("Store the workflow journal at its artifact root")
        write_json(path, self.state)

    @property
    def stage(self):
        return Stage(self.state["stage"])

    def _event(self, action, **data):
        events = self.state["events"]
        event = {"sequence": len(events), "stage": self.stage.value, "action": action,
                 "data": data, "previous": events[-1]["hash"] if events else "0" * 64}
        event["hash"] = digest(event)
        events.append(event)

    def _working(self):
        if self.state["complete"] or self.state["stages"].get(self.stage.value, {}).get("status") in {
            "approved", "submitted"
        }:
            raise GateError("Stage is locked; reopen or withdraw it before editing")

    def inventory(self, names):
        self._working()
        self.state["preserved"] = sorted(set(self.state["preserved"]) | set(names))
        self._event("inventory", preserved=self.state["preserved"])

    def allow_existing_edits(self, targets, authority_reference):
        self._working()
        if not authority_reference or not set(targets) <= set(self.state["preserved"]):
            raise GateError("Existing edits need a user authority reference and inventoried targets")
        if set(targets) & set(self.state["protected"]):
            raise GateError("Reopen the approved stage before authorizing its targets")
        self.state["editable"] = sorted(set(self.state["editable"]) | set(targets))
        self._event("authorize_existing", targets=list(targets), authority_reference=authority_reference)

    def register_new(self, name):
        self._working()
        if name in self.state["preserved"] or name in self.state["protected"]:
            raise GateError("An existing or approved name cannot be registered as new")
        self.state["new_objects"] = sorted(set(self.state["new_objects"]) | {name})
        self._event("register_new", target=name)

    def permit(self, operation, targets, checkpoint):
        self._working()
        if self.stage == Stage.RESEARCH:
            raise GateError("Finish and approve research before modeling")
        targets = tuple(sorted(set(targets)))
        allowed = set(self.state["new_objects"]) | set(self.state["editable"])
        if operation not in EDIT_OPERATIONS or not targets or not set(targets) <= allowed:
            raise GateError("Operation or targets are outside the authorized scope")
        if set(targets) & set(self.state["protected"]):
            raise GateError("Approved targets need an explicitly reopened revision")
        if operation == "create_box" and not set(targets) <= set(self.state["new_objects"]):
            raise GateError("Creation is limited to reserved new object names")
        path = relative_file(self.root, checkpoint)
        if path.suffix != ".blend":
            raise GateError("A saved .blend checkpoint is required before edits")
        permit = EditPermit(uuid.uuid4().hex, self.stage.value, operation, targets,
                            str(Path(checkpoint).as_posix()), file_digest(path))
        self.state["permits"][permit.token] = digest(permit.__dict__)
        self._event("permit", operation=operation, targets=targets, checkpoint=permit.checkpoint)
        return permit

    def consume(self, permit):
        self._working()
        if permit.stage != self.stage.value:
            raise GateError("Permit belongs to a different stage")
        expected = self.state["permits"].get(permit.token)
        if expected != digest(permit.__dict__):
            raise GateError("Permit is unknown, modified, or already consumed")
        if file_digest(relative_file(self.root, permit.checkpoint)) != permit.checkpoint_hash:
            raise GateError("Rollback checkpoint changed after the permit was issued")
        self.state["permits"].pop(permit.token)
        self._event("consume", token=permit.token)

    def submit(self, artifacts):
        self._working()
        required = {"checkpoint", "checkpoint_receipt", "inventory", "brief", "references"} if self.stage == Stage.RESEARCH else {
            "checkpoint", "checkpoint_receipt", "report", "views", "change_log"
        }
        if not required <= set(artifacts):
            raise GateError("Missing deliverables: " + ", ".join(sorted(required - set(artifacts))))
        paths = {key: relative_file(self.root, path) for key, path in artifacts.items()}
        if paths["checkpoint"].suffix != ".blend":
            raise GateError("Checkpoint must be a .blend file")
        receipt = json.loads(paths["checkpoint_receipt"].read_text(encoding="utf-8"))
        if receipt.get("sha256") != file_digest(paths["checkpoint"]) or receipt.get("filename") != paths["checkpoint"].name:
            raise GateError("Checkpoint does not match its generated receipt")
        if self.stage != Stage.RESEARCH:
            report = json.loads(paths["report"].read_text(encoding="utf-8"))
            if report.get("status") != "pass" or report.get("coverage") != "complete":
                raise GateError("Technical validation must pass without unavailable object checks")
            views = json.loads(paths["views"].read_text(encoding="utf-8"))
            self._validate_views(views)
            fingerprints = {obj["name"]: obj["fingerprint"] for obj in report.get("objects", [])}
            if not fingerprints or views.get("fingerprints") != fingerprints:
                raise GateError("Validation and inspected views must cover the same geometry revision")
            if any(receipt.get("fingerprints", {}).get(name) != value for name, value in fingerprints.items()):
                raise GateError("Geometry evidence does not match the saved checkpoint revision")
        self.state["stages"][self.stage.value] = {
            "status": "submitted", "artifacts": {k: Path(v).as_posix() for k, v in artifacts.items()},
            "hashes": {key: file_digest(path) for key, path in paths.items()},
        }
        self.state["permits"].clear()
        self._event("submit", artifacts=self.state["stages"][self.stage.value]["hashes"])

    def _validate_views(self, manifest):
        views = manifest.get("views", {})
        if not VIEWS <= set(views):
            raise GateError("Front, side, top, and perspective images are required")
        for name in VIEWS:
            item = views[name]
            if not item.get("reviewed") or item.get("reviewer_role") not in {"agent", "user"}:
                raise GateError("Captured views must actually be reviewed")
            path = relative_file(self.root, item["path"])
            if file_digest(path) != item.get("sha256") or not item.get("observation"):
                raise GateError("View evidence is missing, stale, or has no observation")
            if item.get("blocking_issues"):
                raise GateError("Resolve blocking visual issues before submission")

    def _unchanged(self, record):
        for key, path in record["artifacts"].items():
            if file_digest(relative_file(self.root, path)) != record["hashes"][key]:
                raise GateError("Submitted artifact changed: " + key)
        if "views" in record["artifacts"]:
            self._validate_views(json.loads(relative_file(self.root, record["artifacts"]["views"]).read_text()))

    def approve(self, authority_reference):
        record = self.state["stages"].get(self.stage.value, {})
        if not authority_reference or record.get("status") != "submitted":
            raise GateError("Approval requires a submitted stage and explicit user authority reference")
        self._unchanged(record)
        record["status"] = "approved"
        record["authority_reference"] = authority_reference
        record["protected_targets"] = sorted(set(self.state["new_objects"]) | set(self.state["editable"]))
        self.state["protected"] = sorted(set(self.state["protected"]) | set(record["protected_targets"]))
        self._event("approve", authority_reference=authority_reference)

    def advance(self):
        record = self.state["stages"].get(self.stage.value, {})
        if record.get("status") != "approved":
            raise GateError("Explicit user approval is required before advancing")
        self._unchanged(record)
        self._event("advance")
        index = STAGES.index(self.stage)
        if index == len(STAGES) - 1:
            self.state["complete"] = True
        else:
            self.state["stage"] = STAGES[index + 1].value
        self.state["permits"].clear()

    def reopen(self, stage, targets, authority_reference):
        stage = Stage(stage)
        record = self.state["stages"].get(stage.value, {})
        if not authority_reference or record.get("status") != "approved":
            raise GateError("Reopening an approved stage needs explicit user authorization")
        if not targets or not set(targets) <= set(record.get("protected_targets", [])):
            raise GateError("Specify approved targets covered by the stage")
        for later in STAGES[STAGES.index(stage):]:
            old = self.state["stages"].get(later.value)
            if old:
                old["status"] = "invalidated"
        self.state["stage"] = stage.value
        self.state["complete"] = False
        self.state["protected"] = sorted(set(self.state["protected"]) - set(targets))
        self.state["permits"].clear()
        self._event("reopen", targets=list(targets), authority_reference=authority_reference)

    def reject(self, rejected_result, problem, likely_cause, correction, validation):
        if not all((rejected_result, problem, likely_cause, correction, validation)):
            raise GateError("Rejection needs result, problem, cause hypothesis, correction and retry validation")
        record = self.state["stages"].get(self.stage.value, {})
        if record.get("status") == "approved":
            raise GateError("Explicitly reopen an approved stage before revising it")
        record["status"] = "rejected"
        self.state["stages"][self.stage.value] = record
        self.state["permits"].clear()
        self._event("reject", rejected_result=rejected_result, problem=problem,
                    likely_cause=likely_cause, correction=correction, retry_validation=validation)

