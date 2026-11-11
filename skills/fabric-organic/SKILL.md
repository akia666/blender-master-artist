---
name: bma-fabric-organic
description: Inspect Blender fabric and organic folds for gravity, support contact, thickness and local intersections.
---

# Fabric and organic surfaces

Identify gravity, tension anchors, supporting surfaces, fabric thickness and stiffness.
Create broad drape and weight distribution before small wrinkles. Match intentional
stylization explicitly; noise displacement is not evidence of plausible folding.

Inspect contact and fold cross sections, underside normals and silhouette. A fold
should connect naturally to an anchor or compression region. Investigate inverted folds,
penetration and self-intersection in wireframe and sectional views. If using simulation,
record frame, collision thickness, scale and reproducibility settings.

Do not automatically remesh a user surface or apply simulation/subdivision caches.
Use open-surface checks for intentional sheets. BMA has no cloth-specific collision
solver or self-intersection detector: require visual evidence and state this limitation.
