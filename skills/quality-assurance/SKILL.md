---
name: bma-quality-assurance
description: Run read-only Blender mesh validators and evidence-linked visual and stage acceptance checks.
---

# Quality assurance

Use the [validator entrypoint](../../validators/README.md) or official adapter.
Select hard-surface, open-surface, subdivision or game profile and disclose tolerances,
triangle budget, unit scale and object scope. A source defect remains visible even
if a modifier masks it. Never invoke repair as part of inspection.

Inspect structured `issues` by code, severity, count and bounded sample indices. Error
means the configured gate failed; warning requires contextual review; info records
facts or intentional exceptions. Reports include loose geometry, duplicates, incidence,
degenerate area, winding, dimensions, density, transforms, modifiers and UV presence.

Read `limitations` and `unavailable` before interpreting `status`. Technical pass
does not prove outward normals, absent intersections, edge flow, subdivision quality,
anatomy, mechanical feasibility or real export readiness. Edit-mode checks are reported
unavailable rather than synchronizing or changing the mesh.

Require front/side/top/perspective images and observations with hashes. Match their
geometry fingerprints to the validation report and checkpoint receipt. Stage submission
checks this relationship; then explicit user approval unlocks the next stage. Failed
or unreviewed work remains pending with a reproducible next action.
