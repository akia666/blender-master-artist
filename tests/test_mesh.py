import math
import unittest

from bma.mesh import Profile, analyze_mesh, duplicate_pairs
from fixtures import cube


class MeshTests(unittest.TestCase):
    def codes(self, report):
        return {i["code"] for i in report["issues"]}

    def test_cube_counts_area_and_dimensions(self):
        result = analyze_mesh(cube())
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["metrics"]["triangles"], 12)
        self.assertEqual(result["metrics"]["edges"], 12)
        self.assertEqual(result["metrics"]["surface_area"], 24)
        self.assertEqual(result["metrics"]["dimensions"], [2, 2, 2])

    def test_open_surface_policy(self):
        mesh = {"vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]], "faces": [[0, 1, 2]]}
        self.assertEqual(analyze_mesh(mesh)["status"], "fail")
        self.assertEqual(analyze_mesh(mesh, Profile.named("open-surface"))["status"], "pass")

    def test_degenerate_and_loose_geometry(self):
        mesh = {"vertices": [[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0], [9, 0, 0]],
                "edges": [[2, 3]], "faces": [[0, 1, 2]]}
        self.assertTrue({"degenerate_faces", "loose_edges", "loose_vertices"} <= self.codes(analyze_mesh(mesh)))

    def test_duplicate_radius_across_negative_bin_boundary(self):
        count, samples = duplicate_pairs([[-0.01, 0, 0], [0.01, 0, 0], [0.1, 0.1, 0.1]], 0.03)
        self.assertEqual((count, samples), (1, [[0, 1]]))

    def test_duplicate_samples_bounded_but_count_is_complete(self):
        count, samples = duplicate_pairs([[0, 0, 0]] * 10, 1e-6, 2)
        self.assertEqual(count, 45)
        self.assertEqual(len(samples), 2)

    def test_flipped_face_detected(self):
        mesh = cube()
        mesh["faces"][0].reverse()
        self.assertIn("inconsistent_winding", self.codes(analyze_mesh(mesh)))

    def test_duplicated_rotated_face_and_overfull_edges(self):
        mesh = cube()
        mesh["faces"].append([2, 1, 0, 3])
        self.assertTrue({"duplicate_faces", "non_manifold_edges"} <= self.codes(analyze_mesh(mesh)))

    def test_uv_and_triangle_budget(self):
        mesh = cube()
        mesh["uv_layers"] = 0
        self.assertIn("missing_uv", self.codes(analyze_mesh(mesh, Profile.named("game"))))
        self.assertEqual(analyze_mesh(mesh, Profile(max_triangles=11))["status"], "fail")

    def test_invalid_indices_and_nan_fail_without_crash(self):
        mesh = cube()
        mesh["faces"][0][0] = -1
        self.assertIn("invalid_face_indices", self.codes(analyze_mesh(mesh)))
        mesh = cube()
        mesh["vertices"][0][0] = math.nan
        self.assertIn("invalid_coordinates", self.codes(analyze_mesh(mesh)))

    def test_invalid_tolerance(self):
        for tolerance in [0, -1, math.inf, math.nan]:
            with self.assertRaises(ValueError):
                Profile(duplicate_tolerance=tolerance)

    def test_snapshot_is_not_modified(self):
        mesh = cube()
        import copy
        previous = copy.deepcopy(mesh)
        analyze_mesh(mesh)
        self.assertEqual(mesh, previous)

