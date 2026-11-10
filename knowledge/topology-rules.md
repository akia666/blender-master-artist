# Topology rules and scope

| Condition | Default treatment | Context |
| --- | --- | --- |
| Boundary edges | Error for closed hard-surface; info for sheets | An open cavity with wall thickness can still have a closed manifold surface |
| More than two faces per edge | Error | Requires local inspection and an authorized correction |
| Degenerate faces or zero-length edges | Error | Area/radius tolerances are in world units; adjust for scale |
| Coincident vertices | Warning | UV seams and intentionally split parts may coincide |
| Loose vertices/edges | Warning | Construction objects may be intentional; never delete silently |
| Conflicting shared-edge winding | Error | Does not prove outward-facing normals |
| Triangles/n-gons | Allowed; subdivision non-quads warn | Final game meshes and planar mechanical surfaces differ from deforming cages |
| Polygon density | Configurable triangle budget and density facts | More faces do not imply more accuracy |
| Missing UV layer | Info by default, error for game profile | Presence is not unwrap quality |
| Unapplied/negative scale | Warning | Do not apply transforms automatically; dependencies may rely on them |

Inspect smoothing, custom normals, Boolean artifacts, useful edge flow and support-loop
spacing visually. Use evaluated views to detect pinching. No automatic self-intersection
or semantic topology test is claimed. Blender's `Mesh.validate()` changes geometry and
is deliberately excluded from read-only inspection.
