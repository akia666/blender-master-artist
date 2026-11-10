---
name: blender-master-artist
description: Create, refine, and validate Blender assets through official Blender Lab MCP with reference analysis, geometry preservation, inspection views, and explicit modeling-stage approvals. Use for Blender modeling and mesh quality review.
---

# Blender Master Artist

Use official **Blender Lab MCP**, not a similarly named community package. Discover
the actual tools and schemas. `execute_blender_code(code)` returns a JSON-compatible
`result` dictionary. Prefer an existing inspection/documentation tool when it fits.
See [official integration](integrations/blender-mcp/README.md) for setup and the guarded adapter.

## Start from evidence

1. Inspect objects, collections, modifiers, materials, dependencies, transforms,
   mesh statistics and existing file state. Classify preserved/approved, editable,
   new, and temporary construction objects. Treat existing objects as preserved.
2. Establish intended use, coordinate system, dimensions and references. Label
   dimensions **measured**, **documented**, or **estimated**, with uncertainty.
   If references are absent, state that fidelity cannot be established.
3. Create a versioned checkpoint before substantial edits. Keep source geometry
   and modifier stacks; do not delete seemingly unused objects, remesh, rebuild,
   or apply modifiers without authorization for that specific change.
4. Follow the [stage contract](docs/stages.md) with `bma.workflow.Workflow`.
   Research → blockout → primary → secondary → detailing → topology → materials
   → final validation. Deliver each stage for explicit user approval before advancing.
   Earlier authorization counts when its scope actually covers the action; do not
   ask again for the same authorized operation. Reopen approved geometry only with
   explicit scoped authorization; invalidate dependent stage evidence.

## Model and correct

Prioritize **silhouette → proportions → major forms → secondary forms → functional
details → topology cleanup → materials → presentation**. Use neutral inspection
lighting; appearance is not evidence of clean geometry.

Read only the relevant specialization:

- [Reference analysis](skills/reference-analysis/SKILL.md): uncertain dimensions, view alignment, silhouette comparisons.
- [Hard surface](skills/hard-surface/SKILL.md): executable enclosure workflow and mechanical construction.
- [Subdivision](skills/subdivision-modeling/SKILL.md): smooth panels, edge flow, pinching.
- [Automotive](skills/automotive-modeling/SKILL.md): wheel placement, panel curvature and glass.
- [Environment](skills/environment-modeling/SKILL.md): modular scale, terrain and reuse.
- [Character](skills/character-modeling/SKILL.md): anatomy and deformation readiness.
- [Fabric](skills/fabric-organic/SKILL.md): gravity, contact and fold plausibility.
- [UV](skills/uv-unwrapping/SKILL.md): seam choices, checker inspection and export needs.
- [QA](skills/quality-assurance/SKILL.md): reports, severity profiles and final evidence.

Validate source **and** evaluated meshes with `bma.blender_runtime.validate_scene`.
Reports expose configurable checks; validators never fix geometry. Read
[topology rules](knowledge/topology-rules.md) for interpretation. A triangle or
n-gon is not automatically a defect. `Mesh.validate()` mutates meshes; do not
use it as a read-only validator.

Capture front, side, top and perspective views. Actually inspect each image before
setting its `reviewed` flag. Record concrete observations, image hashes, and blocking
issues. Compare to references only when those references were examined and aligned.
Propose prioritized, localized corrections tied to image or numeric evidence.
Use `bma.correction.correction_loop`, default three attempts; stop at the configured
limit, a missing evidenced plan, or an authorization boundary. Revalidate after edits.

## Report honestly

Distinguish technical pass, visual review, user approval, and tested export. Missing
Blender, unreviewed images, uncertain proportions or failed checks remain explicit;
never mark the model complete by inference. The shipped demo is a synthetic QA
exercise, not user-approved production geometry.

For existing projects read [existing-model workflow](workflows/existing-model.md).
For new assets read [new-model workflow](workflows/new-model.md). For rejection and
correction read [iterative correction](workflows/iterative-correction.md).
Store reusable lessons with `bma.knowledge.KnowledgeRecord`; read
[knowledge policy](knowledge/record-policy.md) before adding a record. Keep raw
conversations, personal paths, photographs, credentials and private assets out of
the repository. Run the [publication audit](docs/privacy.md) before release.

