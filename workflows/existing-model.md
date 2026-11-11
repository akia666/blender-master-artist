# Existing model

Begin with read-only inventory and a saved copy. Identify collections, objects, linked
data, mesh users, parents, constraints, modifier targets, materials, UVs and approved
parts. Record a baseline report and fingerprints before proposing changes.

Treat existing names as preserved with `Workflow.inventory`. Obtain a scoped edit
authorization and call `allow_existing_edits` for exactly those targets. The guarded
The adapter supports local unparented/unconstrained mesh transforms and unapplied bevels;
more complex dependency changes need a separately reviewed operation, not a guard bypass.

Do not delete invisible objects, rebuild from scratch, apply modifiers, change shared
meshes or automatically remesh as cleanup. Restore/review a checkpoint when a local
correction is insufficient. Compare unrelated-object fingerprints after the edit.
If a target is protected by an approved stage, explicitly reopen that stage and
invalidate dependent evidence before modifying it.
