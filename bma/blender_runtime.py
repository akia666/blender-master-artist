"""Operations executed inside Blender. No MCP/socket implementation lives here."""

from dataclasses import asdict
import math
from pathlib import Path

from bma.io import digest, file_digest, write_json
from bma.mesh import Profile, analyze_mesh, summarize


def _bpy():
    import bpy
    return bpy


def _modifier_data(modifier):
    result = {"name": modifier.name, "type": modifier.type}
    for prop in modifier.bl_rna.properties:
        if prop.is_readonly or prop.identifier in {"rna_type", "name", "type"} or prop.type not in {"BOOLEAN", "INT", "FLOAT", "ENUM", "STRING"}:
            continue
        try:
            value = getattr(modifier, prop.identifier)
            if prop.is_array:
                value = list(value)
            if isinstance(value, set):
                value = sorted(value)
            result[prop.identifier] = value
        except (AttributeError, TypeError):
            continue
    return result


def object_fingerprint(obj):
    if obj.type != "MESH":
        raise ValueError("Editing only supports mesh objects")
    return digest({"vertices": [list(v.co) for v in obj.data.vertices],
                   "edges": [list(e.vertices) for e in obj.data.edges],
                   "faces": [list(p.vertices) for p in obj.data.polygons],
                   "matrix_world": [list(row) for row in obj.matrix_world],
                   "modifiers": [_modifier_data(m) for m in obj.modifiers],
                   "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
                   "face_settings": [[p.material_index, p.use_smooth] for p in obj.data.polygons],
                   "uv_layers": [[[float(x) for x in loop.uv] for loop in layer.data] for layer in obj.data.uv_layers]})


def _inventory_fingerprint(obj):
    if obj.type != "MESH" or obj.mode != "OBJECT":
        return None
    try:
        return object_fingerprint(obj)
    except ValueError:
        return None  # Nonfinite data is inventoried, then explicitly fails validation.


def inventory():
    bpy = _bpy()
    scene = bpy.context.scene
    return {
        "schema_version": "1.0", "blender_version": bpy.app.version_string,
        "unit_system": scene.unit_settings.system, "meters_per_unit": scene.unit_settings.scale_length,
        "mode": bpy.context.mode,
        "collections": [{"name": c.name, "objects": sorted(o.name for o in c.objects),
                         "children": sorted(ch.name for ch in c.children)} for c in bpy.data.collections],
        "objects": [{"name": o.name, "type": o.type, "parent": o.parent.name if o.parent else None,
                     "collections": sorted(c.name for c in o.users_collection),
                     "materials": [s.material.name if s.material else None for s in o.material_slots],
                     "modifiers": [_modifier_data(m) for m in o.modifiers],
                     "constraints": [{"type": c.type, "target": getattr(getattr(c, "target", None), "name", None)}
                                     for c in o.constraints],
                     "linked": bool(o.library), "mesh_users": o.data.users if o.type == "MESH" else None,
                     "fingerprint": _inventory_fingerprint(o)}
                    for o in sorted(scene.objects, key=lambda o: o.name)],
        "privacy": "External paths, custom properties, authors, and image contents omitted",
    }


def _snapshot(mesh, matrix):
    from mathutils.geometry import area_tri
    vertices = [matrix @ v.co for v in mesh.vertices]
    mesh.calc_loop_triangles()
    areas = [0.0] * len(mesh.polygons)
    for triangle in mesh.loop_triangles:
        areas[triangle.polygon_index] += area_tri(*(vertices[i] for i in triangle.vertices))
    return {"vertices": [list(v) for v in vertices], "edges": [list(e.vertices) for e in mesh.edges],
            "faces": [list(p.vertices) for p in mesh.polygons], "face_areas": areas,
            "uv_layers": len(mesh.uv_layers)}


def validate_scene(profile=None, names=None, evaluated=True):
    """Analyze detached source copies and temporary evaluated meshes; never repair."""
    bpy = _bpy()
    profile = Profile(**profile) if isinstance(profile, dict) else profile or Profile()
    scene = bpy.context.scene
    if names is not None and (not names or set(names) - set(scene.objects.keys())):
        raise ValueError("Requested object scope is empty or contains missing objects")
    objects = [o for o in scene.objects if o.type == "MESH" and (names is None or o.name in names)]
    results, unavailable = [], []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in sorted(objects, key=lambda o: o.name):
        record = {"name": obj.name, "issues": [], "modifiers": [_modifier_data(m) for m in obj.modifiers]}
        results.append(record)
        if obj.mode != "OBJECT":
            unavailable.append({"object": obj.name, "reason": "Object mode required; live edit mesh was not synchronized or modified"})
            continue
        if (any(not math.isfinite(x) for row in obj.matrix_world for x in row)
                or any(not math.isfinite(x) for vertex in obj.data.vertices for x in vertex.co)):
            record["issues"].append({"code": "nonfinite_geometry_or_transform", "severity": "error", "count": 1})
            unavailable.append({"object": obj.name, "reason": "Nonfinite source geometry/transform prevents meaningful metrics"})
            continue
        fingerprint = object_fingerprint(obj)
        copy = obj.data.copy()
        try:
            record["source"] = analyze_mesh(_snapshot(copy, obj.matrix_world), profile)
            record["source"]["smooth_faces"] = sum(p.use_smooth for p in copy.polygons)
            record["source"]["custom_normals"] = copy.has_custom_normals
        finally:
            bpy.data.meshes.remove(copy)
        record["fingerprint"] = fingerprint
        matrix = obj.matrix_world
        record["transform"] = {"location": list(obj.location), "rotation": list(obj.rotation_euler),
                               "scale": list(obj.scale), "world_determinant": matrix.determinant()}
        for code, severity, condition in [
            ("singular_transform", "error", matrix.determinant() == 0),
            ("negative_transform", "warning", matrix.determinant() < 0),
            ("unapplied_scale", "warning", any(abs(x - 1) > 1e-6 for x in obj.scale)),
            ("unapplied_rotation", "info", any(abs(x) > 1e-6 for x in obj.rotation_euler)),
            ("shared_mesh", "info", obj.data.users > 1),
        ]:
            if condition:
                record["issues"].append({"code": code, "severity": severity, "count": 1})
        record["bounds"] = record["source"]["metrics"].get("dimensions")
        if evaluated:
            evaluated_obj = obj.evaluated_get(depsgraph)
            try:
                mesh = evaluated_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                record["evaluated"] = analyze_mesh(_snapshot(mesh, evaluated_obj.matrix_world), profile)
            except (RuntimeError, ValueError) as exc:
                unavailable.append({"object": obj.name, "reason": type(exc).__name__})
            finally:
                evaluated_obj.to_mesh_clear()
        if object_fingerprint(obj) != fingerprint:
            raise RuntimeError("Source changed during validation")
    instance_count = sum(i.is_instance for i in depsgraph.object_instances)
    errors = sum(i["severity"] == "error" for obj in results for i in obj["issues"])
    errors += sum(i["severity"] == "error" for obj in results for key in ("source", "evaluated")
                  for i in obj.get(key, {}).get("issues", []))
    status = "pass" if results and not errors and not unavailable else "fail"
    report = {"schema_version": "1.0", "status": status, "coverage": "incomplete" if unavailable else "complete",
              "profile": asdict(profile), "blender_version": bpy.app.version_string,
              "meters_per_unit": scene.unit_settings.scale_length, "objects": results,
              "unavailable": unavailable, "dependency_instances": instance_count,
              "visual_status": "needs_review", "export_readiness": {
                  "mesh_gate": status, "actual_export_tested": False,
                  "limitations": "Exporter format, axes, texture resolution and target engine must be tested separately"},
              "limitations": ["No self-intersection, UV-overlap, outward-volume or semantic topology proof",
                              "Evaluated mesh checks do not inspect other Geometry Nodes components or each instance",
                              "Technical pass is not stage approval or visual acceptance"]}
    report["summary"] = summarize(report)
    return report


def save_checkpoint(directory, label="checkpoint"):
    bpy = _bpy()
    if not label or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in label):
        raise ValueError("Use a plain checkpoint label")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for version in range(1, 100000):
        path = directory / f"{label}-{version:04d}.blend"
        if not path.exists():
            break
    else:
        raise FileExistsError("Checkpoint namespace exhausted")
    original_path = bpy.data.filepath
    filepaths = bpy.context.preferences.filepaths
    preview_type = filepaths.file_preview_type
    try:
        # A checkpoint needs no desktop screenshot or thumbnail-cache write.
        filepaths.file_preview_type = "NONE"
        bpy.ops.wm.save_as_mainfile(filepath=str(path.resolve()), copy=True, check_existing=False)
    finally:
        filepaths.file_preview_type = preview_type
    if bpy.data.filepath != original_path:
        raise RuntimeError("Checkpoint unexpectedly changed the active project path")
    receipt = {"filename": path.name, "sha256": file_digest(path),
               "fingerprints": {o.name: _inventory_fingerprint(o) for o in bpy.context.scene.objects
                                if o.type == "MESH" and o.mode == "OBJECT"}}
    receipt_name = path.name + ".json"
    write_json(directory / receipt_name, receipt)
    return dict(receipt, receipt=receipt_name)


def capture_views(directory, names, resolution=512, artifact_root=None):
    """Render evaluated copies in an isolated scene, with neutral CPU Cycles lighting."""
    bpy = _bpy()
    from mathutils import Vector
    if not 64 <= resolution <= 2048:
        raise ValueError("Inspection resolution must be 64..2048")
    if not names or set(names) - set(bpy.context.scene.objects.keys()):
        raise ValueError("All inspection targets must exist")
    directory = Path(directory)
    artifact_root = Path(artifact_root).resolve() if artifact_root else directory.resolve().parent
    if not directory.resolve().is_relative_to(artifact_root):
        raise ValueError("Inspection directory must be inside the artifact root")
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / "views.json").exists():
        raise FileExistsError("Use a fresh inspection directory to preserve earlier evidence")
    source_scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    temp = bpy.data.scenes.new("BMA_Inspection")
    owned_objects, owned_meshes, owned_lights = [], [], []
    camera_data = material = world = None
    try:
        points = []
        for name in names:
            source = source_scene.objects[name]
            if source.type != "MESH" or source.mode != "OBJECT":
                raise ValueError("Inspection targets must be Object-mode meshes")
            evaluated = source.evaluated_get(depsgraph)
            mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
            owned_meshes.append(mesh)
            mesh.materials.clear()
            obj = bpy.data.objects.new("Inspection_" + name, mesh)
            owned_objects.append(obj)
            obj.matrix_world = source.matrix_world.copy()
            temp.collection.objects.link(obj)
            points.extend(obj.matrix_world @ v.co for v in mesh.vertices)
        if not points:
            raise ValueError("Cannot inspect empty geometry")
        minimum = Vector(tuple(min(p[i] for p in points) for i in range(3)))
        maximum = Vector(tuple(max(p[i] for p in points) for i in range(3)))
        center = (minimum + maximum) / 2
        diameter = max((maximum - minimum).length, 0.001)
        material = bpy.data.materials.new("BMA_Neutral")
        material.use_nodes = True
        shader = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        shader.inputs["Base Color"].default_value = (0.48, 0.48, 0.48, 1)
        shader.inputs["Roughness"].default_value = 0.65
        for obj in owned_objects:
            obj.data.materials.append(material)
        world = bpy.data.worlds.new("BMA_InspectionWorld")
        world.use_nodes = True
        background = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
        background.inputs["Color"].default_value = (0.45, 0.45, 0.45, 1)
        background.inputs["Strength"].default_value = 0.7
        temp.world = world
        light_data = bpy.data.lights.new("BMA_InspectionLight", "AREA")
        owned_lights.append(light_data)
        light_data.energy = 30 * diameter * diameter
        light_data.shape = "DISK"
        light_data.size = diameter * 2
        light = bpy.data.objects.new("BMA_InspectionLight", light_data)
        owned_objects.append(light)
        light.location = center + Vector((-1, -2, 3)) * diameter
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
        temp.collection.objects.link(light)
        camera_data = bpy.data.cameras.new("BMA_InspectionCamera")
        camera = bpy.data.objects.new("BMA_InspectionCamera", camera_data)
        owned_objects.append(camera)
        temp.collection.objects.link(camera)
        temp.camera = camera
        temp.render.engine = "CYCLES"
        temp.cycles.device = "CPU"
        temp.cycles.samples = 8
        temp.cycles.use_denoising = False
        temp.render.resolution_x = temp.render.resolution_y = resolution
        temp.render.resolution_percentage = 100
        temp.render.image_settings.file_format = "PNG"
        temp.render.film_transparent = False
        temp.view_settings.view_transform = "Standard"
        manifest = {"schema_version": "1.0", "visual_status": "needs_review",
                    "fingerprints": {name: object_fingerprint(source_scene.objects[name]) for name in names},
                    "coordinate_system":
                    "+X right, +Y rear, +Z up; front looks from -Y", "targets": list(names), "views": {}}
        directions = {"front": (0, -1, 0), "side": (1, 0, 0), "top": (0, 0, 1), "perspective": (1.5, -2, 1.4)}
        for name, direction in directions.items():
            camera_data.type = "PERSP" if name == "perspective" else "ORTHO"
            camera_data.ortho_scale = diameter * 1.15
            camera_data.lens = 50
            camera_data.clip_start = diameter / 1000
            camera_data.clip_end = diameter * 100
            camera.location = center + Vector(direction).normalized() * diameter * 2.3
            camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
            path = directory / (name + ".png")
            temp.render.filepath = str(path.resolve())
            bpy.ops.render.render(scene=temp.name, write_still=True)
            manifest["views"][name] = {"path": path.resolve().relative_to(artifact_root).as_posix(), "sha256": file_digest(path),
                                       "reviewed": False, "reviewer_role": None, "observation": "",
                                       "blocking_issues": [], "projection": camera_data.type,
                                       "camera_matrix": [list(row) for row in camera.matrix_world]}
        write_json(directory / "views.json", manifest)
        return manifest
    finally:
        for obj in owned_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.scenes.remove(temp)
        for mesh in owned_meshes:
            bpy.data.meshes.remove(mesh)
        for light in owned_lights:
            bpy.data.lights.remove(light)
        if camera_data:
            bpy.data.cameras.remove(camera_data)
        if material:
            bpy.data.materials.remove(material)
        if world:
            bpy.data.worlds.remove(world)


def _edit(operation, targets, parameters, expected):
    bpy = _bpy()
    scene = bpy.context.scene
    if bpy.context.mode != "OBJECT":
        raise ValueError("Object mode required; BMA does not switch the user's editing mode")
    if operation == "create_box":
        if len(targets) != 1 or targets[0] in bpy.data.objects:
            raise ValueError("Creation needs one unoccupied object name")
    else:
        for name in targets:
            obj = scene.objects.get(name)
            if obj is None or obj.type != "MESH" or obj.library or obj.constraints or obj.parent:
                raise ValueError("Editable target must be local, unparented, unconstrained mesh geometry")
            if object_fingerprint(obj) != expected.get(name):
                raise ValueError("Target changed or lacks a pre-edit fingerprint: " + name)
    if operation in {"create_box", "set_dimensions"}:
        size = parameters.get("dimensions", [])
        if len(size) != 3 or any(not math.isfinite(x) or x <= 0 for x in size):
            raise ValueError("Dimensions must be three finite positive numbers")
        if operation == "create_box":
            x, y, z = (v / 2 for v in size)
            vertices = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
                        (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
            faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                     (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            mesh = bpy.data.meshes.new(targets[0])
            mesh.from_pydata(vertices, [], faces)
            obj = bpy.data.objects.new(targets[0], mesh)
            scene.collection.objects.link(obj)
        else:
            # Transform only; never apply modifiers or rewrite shared mesh data.
            for name in targets:
                obj = scene.objects[name]
                if any(d <= 1e-12 for d in obj.dimensions):
                    raise ValueError("Cannot dimension a flat or empty target")
            for name in targets:
                scene.objects[name].dimensions = size
    elif operation == "add_bevel":
        width, segments = parameters.get("width", 0.001), parameters.get("segments", 3)
        if not math.isfinite(width) or width <= 0 or type(segments) is not int or not 1 <= segments <= 8:
            raise ValueError("Invalid bevel parameters")
        for name in targets:
            obj = scene.objects[name]
            if any(m.name.startswith("BMA_Bevel") for m in obj.modifiers):
                raise ValueError("A BMA bevel already exists; inspect it instead of stacking duplicates")
        for name in targets:
            mod = scene.objects[name].modifiers.new("BMA_Bevel", "BEVEL")
            mod.width, mod.segments = width, segments
            mod.limit_method = "ANGLE"
    else:
        raise ValueError("Unsupported edit operation")
    bpy.context.view_layer.update()
    return {"operation": operation, "fingerprints": {n: object_fingerprint(scene.objects[n]) for n in targets}}


def dispatch(operation, arguments):
    """Narrow, named entry point used by the official MCP adapter."""
    operations = {"inventory": inventory, "validate": validate_scene, "capture_views": capture_views,
                  "checkpoint": save_checkpoint}
    if operation in operations:
        return operations[operation](**arguments)
    if operation in {"create_box", "set_dimensions", "add_bevel"}:
        return _edit(operation, **arguments)
    raise ValueError("Unknown BMA runtime operation")

