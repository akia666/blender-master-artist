---
name: bma-environment-modeling
description: Organize modular Blender environments with consistent scale, reusable components and terrain contact checks.
---

# Environment guidance

Define metric module size, grid increment, pivot conventions and intended traversal
scale. Prototype a small assembly before duplicating it. Use linked data/instances for
repetition; identify intentional shared meshes before editing any source mesh.

Separate terrain, reusable modules and unique dressing into purposeful collections.
Inspect seams, contact with terrain, intersections at foundations, silhouette repetition
and visible density. Validate representative source meshes plus the assembled scene.
Bounds overlap is only a candidate collision; inspect actual geometry before reporting it.

Track unique geometry and evaluated instances separately. BMA mesh reports do
not inspect every instance or non-mesh Geometry Nodes component. Do not claim an entire
instanced environment is export-ready from source-mesh checks. Large-world streaming,
occlusion and target-engine performance require separate validation.

For massing, street scale and functional routes read
[architecture and environments](../../references/architecture-and-environments.md).
For rule-based variation and linked modules read
[procedural modeling](../../references/procedural-modeling.md). Use
[camera-aware performance guidance](../../references/performance-optimization.md)
without treating environment-specific techniques as rules for unrelated assets.
