---
name: bma-reference-analysis
description: Establish Blender modeling coordinates, uncertain dimensions, reference views and calibrated silhouette comparisons.
---

# Reference analysis

Record each reference's allowed local identifier, license, view (front/side/rear/top/
perspective/unknown), perspective distortion and reliability. Do not fetch private
collections or infer permission to redistribute an image. Store private images outside
the publication tree. Inspect the images before making claims about them.

Use +Z up, +X right and front looking from -Y unless the project already has a
documented convention. Identify the datum plane, origin, scale anchor and symmetry
planes. Preserve an existing coordinate system rather than rotating a project casually.
Use `bma.reference.Dimension(value, unit, basis, source, uncertainty)` for dimensions.
Document an assumed synthetic design separately from a specification for a real object.

Begin with a blockout and compare bounding ratios, cross sections and outline in
calibrated orthographic views. For a perspective photograph estimate the camera and
distortion before treating projected errors as shape errors. Resolve contradictory
references with confidence ranges; do not average unrelated variants into one design.

`silhouette_iou` accepts aligned boolean masks. Match crop, projection and scale first;
record segmentation method. IoU measures projected occupancy, not depth, topology,
functional construction or model correctness. No automatic image segmentation ships.

Deliver reference metadata, dimension table, coordinate convention, primary ratios,
uncertainties and four blockout views for the BLOCKOUT gate.
