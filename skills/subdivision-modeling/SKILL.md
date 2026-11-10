---
name: bma-subdivision-modeling
description: Refine smooth Blender subdivision surfaces while checking edge flow, support spacing and pinching.
---

# Subdivision surfaces

Use the subdivision QA profile; its non-quad warning is contextual, not a universal
failure. Keep a low-density control cage and compare both cage and intended subdivision
level. Distribute supporting loops by curvature needs rather than uniform density.

Inspect silhouette, broad neutral highlights, pole placement, unequal edge spacing,
crease transitions and pinching from four views. Move poles away from high-curvature
or deforming areas where practical. Test one local adjustment before adding loops
across an approved surface. Preserve symmetry datums and smooth tangent transitions.

Do not apply subdivision merely to satisfy an export count. Obtain approval before
changing approved control topology or using destructive remeshing. Record source and
evaluated budgets independently. Automated curvature/edge-flow and pinching metrics
are not implemented in v0.1; image evidence is required.
