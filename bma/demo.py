"""Original synthetic hard-surface regression asset, isolated from user scenes."""

import json
from pathlib import Path

from bma.blender_runtime import capture_views, inventory, object_fingerprint, save_checkpoint, validate_scene
from bma.correction import CorrectionPlan, correction_loop
from bma.io import write_json


def _box(name, dimensions, location, collection):
    import bpy
    from bma.blender_runtime import _edit
    _edit("create_box", [name], {"dimensions": dimensions}, {})
    obj = bpy.context.scene.objects[name]
    obj.location = location
    for previous in list(obj.users_collection):
        previous.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def _shell(name, collection):
    """Closed 4 mm wall shell with an open cavity; 16 vertices, 14 quads."""
    import bpy
    vertices = []
    for x, y, z in [(0.12, 0.08, 0.0), (0.12, 0.08, 0.072),
                    (0.116, 0.076, 0.072), (0.116, 0.076, 0.004)]:
        vertices.extend([(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)])
    faces = [(0, 3, 2, 1), (12, 13, 14, 15)]
    for i in range(4):
        j = (i + 1) % 4
        faces.extend([(i, j, 4 + j, 4 + i), (4 + i, 4 + j, 8 + j, 8 + i),
                      (8 + i, 8 + j, 12 + j, 12 + i)])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def run_demo(directory, render=True, resolution=384):
    """Synthetic QA exercise; never auto-approves a modeling stage.

    Always creates a separate scene and restores the previous scene on exit.
    It never resets, deletes or overwrites any existing scene or artifact.
    """
    import bpy
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise FileExistsError("Use an empty output directory for a reproducible demo")
    original_scene = bpy.context.window.scene
    demo_scene = bpy.data.scenes.new("BMA_SyntheticDemo")
    collection = bpy.data.collections.new("BMA_OriginalEnclosure")
    demo_scene.collection.children.link(collection)
    original_fingerprints = {o.name: object_fingerprint(o) for o in original_scene.objects
                             if o.type == "MESH" and o.mode == "OBJECT"}
    bpy.context.window.scene = demo_scene
    stages = []
    try:
        demo_scene.unit_settings.system = "METRIC"
        demo_scene.unit_settings.scale_length = 1.0
        write_json(directory / "reference.json", {
            "asset": "Original removable-lid instrument enclosure", "license": "MIT",
            "coordinate_system": "+X right, +Y rear, +Z up, front -Y",
            "dimensions": {"width": 0.24, "depth": 0.16, "body_height": 0.072,
                           "wall": 0.004, "lid_thickness": 0.006, "lid_gap": 0.001},
            "unit": "m", "basis": "documented synthetic design specification",
            "limitation": "Illustrative enclosure; no fastener engagement or manufacturing certification"})
        blockout = _box("BMA_Blockout", (0.24, 0.16, 0.079), (0, 0, 0.0395), collection)
        bpy.context.view_layer.update()
        stages.append({"stage": "blockout", "checkpoint": save_checkpoint(directory, "01-blockout")})
        write_json(directory / "01-blockout-report.json", validate_scene())
        if render:
            capture_views(directory / "blockout-views", [blockout.name], resolution, directory)
        # Only the generated temporary blockout is replaced; no user geometry is touched.
        blockout_mesh = blockout.data
        bpy.data.objects.remove(blockout, do_unlink=True)
        bpy.data.meshes.remove(blockout_mesh)
        body = _shell("BMA_Body", collection)
        lid = _box("BMA_Lid", (0.24, 0.16, 0.006), (0, 0, 0.076), collection)
        panel = _box("BMA_FrontPanel", (0.12, 0.002, 0.026), (0, -0.0811, 0.037), collection)
        for obj in (body, lid, panel):
            bevel = obj.modifiers.new("BMA_Bevel", "BEVEL")
            bevel.width = 0.0006 if obj == panel else 0.001
            bevel.segments = 3
            bevel.limit_method = "ANGLE"
        bpy.context.view_layer.update()
        names = [body.name, lid.name, panel.name]
        refined = validate_scene()
        if refined["status"] != "pass":
            raise AssertionError("Refined synthetic geometry failed: " + json.dumps(refined))
        write_json(directory / "02-refined-report.json", refined)
        stages.append({"stage": "refined", "checkpoint": save_checkpoint(directory, "02-refined")})
        # Deliberately attach a collinear triangle, coincident vertex, wire and isolated vertex.
        # The injected vertices are tagged by recorded indices; correction removes only those.
        original_vertices = [tuple(v.co) for v in body.data.vertices]
        original_faces = [list(p.vertices) for p in body.data.polygons]
        offset = len(original_vertices)
        defective_vertices = original_vertices + [(0.16, 0, 0), (0.17, 0, 0), (0.18, 0, 0),
                                                   original_vertices[0], (0.19, 0, 0)]
        body.data.clear_geometry()
        body.data.from_pydata(defective_vertices, [(offset + 2, offset + 4)],
                              original_faces + [[offset, offset + 1, offset + 2]])
        bpy.context.view_layer.update()
        defective = validate_scene()
        codes = {i["code"] for obj in defective["objects"] for i in obj.get("source", {}).get("issues", [])}
        required = {"degenerate_faces", "duplicate_vertices", "loose_edges", "loose_vertices", "boundary_edges"}
        if not required <= codes or defective["status"] != "fail":
            raise AssertionError("Injected defects were not detected")
        write_json(directory / "03-defects-report.json", defective)
        stages.append({"stage": "defective", "checkpoint": save_checkpoint(directory, "03-defective")})
        lid_fingerprint, panel_fingerprint = object_fingerprint(lid), object_fingerprint(panel)

        def inspect():
            report = validate_scene()
            return {"technical_status": report["status"], "visual_status": "not_reviewed",
                    "evidence": "03-defects-report.json" if report["status"] == "fail" else "04-final-report.json"}

        def propose(observation):
            if observation["technical_status"] == "pass":
                return None
            return CorrectionPlan("Injected degenerate triangle and loose coincident elements",
                                  "03-defects-report.json", "Remove only known injected vertex indices",
                                  (body.name,))

        def apply(plan):
            import bmesh
            mesh = bmesh.new()
            try:
                mesh.from_mesh(body.data)
                mesh.verts.ensure_lookup_table()
                injected = [v for v in mesh.verts if v.index >= offset]
                bmesh.ops.delete(mesh, geom=injected, context="VERTS")
                mesh.to_mesh(body.data)
            finally:
                mesh.free()
            bpy.context.view_layer.update()
            if object_fingerprint(lid) != lid_fingerprint or object_fingerprint(panel) != panel_fingerprint:
                raise AssertionError("Correction modified an unrelated component")
            return {"removed_injected_vertices": len(injected), "preserved": [lid.name, panel.name]}

        correction = correction_loop(inspect, propose, apply, max_iterations=2)
        final = validate_scene()
        if final["status"] != "pass":
            raise AssertionError("Targeted correction did not pass final technical checks")
        if final["objects"][0].get("source") is None:
            raise AssertionError("Missing actual mesh evidence")
        write_json(directory / "04-final-report.json", final)
        write_json(directory / "correction-history.json", correction)
        stages.append({"stage": "corrected", "checkpoint": save_checkpoint(directory, "04-final")})
        if render:
            capture_views(directory / "final-views", names, resolution, directory)
        manifest = {"schema_version": "1.0", "blender_version": bpy.app.version_string,
                    "technical_status": final["status"], "visual_status": "needs_review",
                    "user_approval": "pending", "stages": stages, "defects_detected": sorted(codes),
                    "rendered": render, "original_scene_preserved": True,
                    "correction_status": correction["status"]}
        write_json(directory / "demo.json", manifest)
        write_json(directory / "inventory.json", inventory())
        return manifest
    finally:
        bpy.context.window.scene = original_scene
        if any(object_fingerprint(original_scene.objects[name]) != fingerprint
               for name, fingerprint in original_fingerprints.items()):
            raise AssertionError("Pre-existing geometry changed")

