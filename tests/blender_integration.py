"""Actual bpy integration suite; invoke in a factory-startup Blender process."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy

from bma.blender_runtime import (
    _edit, capture_views, inventory, object_fingerprint, save_checkpoint, validate_scene,
)
from bma.demo import _shell
from bma.mesh import Profile


class BlenderIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.previous_scene = bpy.context.window.scene
        self.scene = bpy.data.scenes.new("SyntheticTest")
        bpy.context.window.scene = self.scene
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.names = []

    def tearDown(self):
        bpy.context.window.scene = self.previous_scene
        for obj in list(self.scene.objects):
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if isinstance(data, bpy.types.Mesh) and data.users == 0:
                bpy.data.meshes.remove(data)
        bpy.data.scenes.remove(self.scene)

    def cube(self):
        name = "SyntheticBox"
        _edit("create_box", [name], {"dimensions": [2, 2, 2]}, {})
        return self.scene.objects[name]

    def test_inventory_has_dependencies_without_external_paths(self):
        obj = self.cube()
        data = inventory()
        self.assertEqual(data["objects"][0]["name"], obj.name)
        self.assertIn("fingerprint", data["objects"][0])
        self.assertNotIn("filepath", str(data))

    def test_source_and_evaluated_counts_and_no_changes(self):
        obj = self.cube()
        modifier = obj.modifiers.new("TestBevel", "BEVEL")
        modifier.width, modifier.segments = 0.05, 2
        before = object_fingerprint(obj)
        mesh_count = len(bpy.data.meshes)
        report = validate_scene()
        self.assertEqual(report["status"], "pass", report)
        self.assertEqual(report["objects"][0]["source"]["metrics"]["vertices"], 8)
        self.assertGreater(report["objects"][0]["evaluated"]["metrics"]["vertices"], 8)
        self.assertEqual(object_fingerprint(obj), before)
        self.assertEqual(len(bpy.data.meshes), mesh_count)

    def test_nonuniform_world_dimensions_and_area(self):
        obj = self.cube()
        obj.scale = (2, 3, 4)
        bpy.context.view_layer.update()
        report = validate_scene()
        metrics = report["objects"][0]["source"]["metrics"]
        self.assertEqual(metrics["dimensions"], [4, 6, 8])
        self.assertAlmostEqual(metrics["surface_area"], 208)

    def test_defective_mesh_and_profile_context(self):
        mesh = bpy.data.meshes.new("Defective")
        mesh.from_pydata([(0, 0, 0), (1, 0, 0), (2, 0, 0), (0, 0, 0), (3, 0, 0)],
                         [(2, 4)], [(0, 1, 2)])
        obj = bpy.data.objects.new("Defective", mesh)
        self.scene.collection.objects.link(obj)
        report = validate_scene(evaluated=False)
        codes = {i["code"] for i in report["objects"][0]["source"]["issues"]}
        self.assertTrue({"degenerate_faces", "duplicate_vertices", "loose_edges", "loose_vertices"} <= codes)
        self.assertEqual(report["status"], "fail")

    def test_shell_is_closed_with_intentional_cavity(self):
        _shell("Shell", self.scene.collection)
        report = validate_scene()
        self.assertEqual(report["status"], "pass", report)
        self.assertEqual(report["objects"][0]["source"]["metrics"]["faces"], 14)

    def test_uv_required_for_game_export_gate(self):
        self.cube()
        report = validate_scene(Profile.named("game"))
        self.assertEqual(report["status"], "fail")

    def test_uv_changes_invalidate_source_fingerprint(self):
        obj = self.cube()
        layer = obj.data.uv_layers.new(name="UVMap")
        before = object_fingerprint(obj)
        layer.data[0].uv = (0.3, 0.5)
        self.assertNotEqual(object_fingerprint(obj), before)

    def test_zero_scale_fails_without_repair(self):
        obj = self.cube()
        obj.scale.x = 0
        bpy.context.view_layer.update()
        report = validate_scene()
        self.assertEqual(report["status"], "fail")
        self.assertEqual(obj.scale.x, 0)

    def test_stale_fingerprint_blocks_edits(self):
        obj = self.cube()
        before = object_fingerprint(obj)
        obj.data.vertices[0].co.x += 0.1
        with self.assertRaises(ValueError):
            _edit("add_bevel", [obj.name], {"width": 0.02}, {obj.name: before})
        self.assertEqual(len(obj.modifiers), 0)

    def test_non_destructive_edit_keeps_mesh_and_preserves_other_objects(self):
        obj = self.cube()
        mesh = obj.data
        _edit("add_bevel", [obj.name], {"width": 0.02}, {obj.name: object_fingerprint(obj)})
        self.assertEqual(obj.data, mesh)
        self.assertEqual(len(mesh.vertices), 8)
        self.assertEqual(len(obj.modifiers), 1)

    def test_checkpoint_versioning_and_active_file_preservation(self):
        self.cube()
        original = bpy.data.filepath
        first = save_checkpoint(self.root, "test")
        second = save_checkpoint(self.root, "test")
        self.assertNotEqual(first["filename"], second["filename"])
        self.assertEqual(bpy.data.filepath, original)
        with bpy.data.libraries.load(str(self.root / first["filename"])) as (source, _destination):
            self.assertIn("SyntheticBox", source.objects)

    def test_empty_scene_and_missing_scope_fail(self):
        self.assertEqual(validate_scene()["status"], "fail")
        with self.assertRaises(ValueError):
            validate_scene(names=["Missing"])

    def test_edit_mode_is_not_silently_changed(self):
        obj = self.cube()
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        try:
            report = validate_scene()
            self.assertEqual(report["coverage"], "incomplete")
            self.assertEqual(obj.mode, "EDIT")
        finally:
            bpy.ops.object.mode_set(mode="OBJECT")

    def test_four_real_inspection_renders_restore_datablocks(self):
        obj = self.cube()
        fingerprint = object_fingerprint(obj)
        before = {k: len(getattr(bpy.data, k)) for k in ["scenes", "objects", "meshes", "materials", "lights", "cameras", "worlds"]}
        manifest = capture_views(self.root / "views", [obj.name], resolution=64, artifact_root=self.root)
        self.assertEqual(set(manifest["views"]), {"front", "side", "top", "perspective"})
        for item in manifest["views"].values():
            self.assertFalse(item["reviewed"])
            self.assertTrue((self.root / item["path"]).read_bytes().startswith(b"\x89PNG"))
        self.assertEqual(object_fingerprint(obj), fingerprint)
        self.assertEqual(before, {k: len(getattr(bpy.data, k)) for k in before})
        self.assertEqual(bpy.context.scene, self.scene)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BlenderIntegrationTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("Blender integration tests failed")
