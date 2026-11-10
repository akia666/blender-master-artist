from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from bma.correction import CorrectionPlan, correction_loop
from bma.knowledge import KnowledgeRecord
from bma.reference import Dimension, silhouette_iou


class EvidenceTests(unittest.TestCase):
    def test_bounded_corrections_never_invent_visual_pass(self):
        calls = []
        result = correction_loop(lambda: {"technical_status": "fail", "visual_status": "not_reviewed"},
                                 lambda _: CorrectionPlan("defect", "report.json", "targeted repair", ("Body",)),
                                 lambda plan: calls.append(plan.problem), max_iterations=2)
        self.assertEqual(result["status"], "limit_reached")
        self.assertEqual(len(calls), 2)
        result = correction_loop(lambda: {"technical_status": "pass"}, lambda _: None, lambda _: None)
        self.assertEqual(result["status"], "needs_visual_review")

    def test_verified_solution_requires_executed_evidence(self):
        record = KnowledgeRecord("bevel", ("hard-surface",), "overlap", "", False, "reduce width",
                                 "inspect corners", "low", "hypothesis", "proposal-1", "proposed_untested", "not tested")
        record.validate()
        with self.assertRaises(ValueError):
            replace(record, status="verified_success").validate()
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(record.save_revision(directory).is_file())
            with self.assertRaises(FileExistsError):
                record.save_revision(directory)
            self.assertEqual(len(list(Path(directory).glob("*.json"))), 1)

    def test_dimensions_preserve_basis(self):
        self.assertEqual(Dimension(2, "m", "estimated", "side reference", 0.2).basis, "estimated")
        with self.assertRaises(ValueError):
            Dimension(2, "m", "exact_guess", "none", 0)

    def test_iou_requires_alignment_and_real_silhouette(self):
        a = [[True, False], [True, False]]
        b = [[True, True], [False, False]]
        self.assertAlmostEqual(silhouette_iou(a, b, aligned=True)["iou"], 1 / 3)
        with self.assertRaises(ValueError):
            silhouette_iou(a, b)
        with self.assertRaises(ValueError):
            silhouette_iou([[False]], [[False]], aligned=True)

