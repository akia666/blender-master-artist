---
name: bma-hard-surface
description: Model mechanical Blender props with separate components, controlled bevels, plausible wall construction and measurable QA.
---

# Hard surface

This is BMA's executable specialization. Follow the stage and preservation
rules in the root skill. The original enclosure demo runs through
`scripts/blender_demo.py`; it is a QA regression exercise, not a stage approval.

1. Establish the envelope and datums from references or a clearly synthetic design.
   Approve the blockout proportions before detailing. Check front/side/top ratios.
2. Separate fixed body, removable cover, controls and moving components. Build actual
   wall thickness where an opening exposes the inside. Record clearance assumptions;
   identify where contacts, screw engagement or load paths remain unverified.
3. Use dimensioned low-density meshes and a small unapplied Bevel modifier. Bevel width
   must fit the thinnest local wall and smallest clearance. Inspect the evaluated mesh,
   corner clamps, normals and silhouette. Do not stack corrective bevels blindly.
4. Keep construction cutters in a named temporary collection. Inspect Boolean results
   in neutral light and wireframe. Applying a Boolean, remeshing, dissolving existing
   geometry or replacing a base mesh requires the relevant authorization and checkpoint.
5. Validate source/evaluated meshes, dimensions and component separations. Use targeted
   fixes only where evidence identifies a defect. Preserve every unrelated component.

Demo specification: 240 × 160 mm enclosure, 72 mm body, 4 mm walls, 6 mm lid and
1 mm separation. The source shell is closed as a surface despite an open internal
cavity. The front panel is separate. No fastener engineering or manufacturing
qualification is claimed. Final source meshes intentionally use planar n-gons/quads
where appropriate; source and Bevel evaluation are reported separately.

Quality gates: no degenerate/zero-length geometry, winding conflicts, unexpected
boundaries or overfull edges; default 100,000 triangle budget. Contextual warnings
must be reviewed. Source warnings are not hidden by a clean evaluated result.
