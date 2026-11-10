"""Reviewable technical lessons, without conversations or personal attribution."""

from dataclasses import asdict, dataclass
from pathlib import Path

from bma.io import digest, write_json


STATUSES = {"verified_success", "user_approved", "proposed_untested", "rejected", "recommendation"}
EVIDENCE = {"deterministic_test", "inspected_images", "user_approval", "technical_reference", "hypothesis"}


@dataclass(frozen=True)
class KnowledgeRecord:
    category: str
    asset_types: tuple
    symptoms: str
    root_cause: str
    cause_verified: bool
    correction: str
    validation: str
    confidence: str
    evidence_type: str
    evidence_reference: str
    status: str
    limitations: str

    def validate(self):
        if self.status not in STATUSES or self.evidence_type not in EVIDENCE:
            raise ValueError("Unknown knowledge status or evidence type")
        if self.confidence not in {"low", "medium", "high"}:
            raise ValueError("Confidence must be low, medium, or high")
        if not all((self.category, self.asset_types, self.symptoms, self.correction, self.validation,
                    self.evidence_reference, self.limitations)):
            raise ValueError("A lesson requires scope, symptoms, correction, validation, evidence and limitations")
        if self.cause_verified and (not self.root_cause or self.evidence_type == "hypothesis"):
            raise ValueError("A verified cause needs evidence")
        if self.status == "verified_success" and self.evidence_type not in {"deterministic_test", "inspected_images"}:
            raise ValueError("Verified success needs executed or visually inspected evidence")
        if self.status == "user_approved" and self.evidence_type != "user_approval":
            raise ValueError("User-approved knowledge needs user-approval evidence")
        return asdict(self)

    def save_revision(self, directory):
        value = self.validate()
        path = Path(directory) / (digest(value) + ".json")
        if path.exists():
            raise FileExistsError("Knowledge revisions are immutable; review or create a new revision")
        write_json(path, value)
        return path

