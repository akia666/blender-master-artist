# Architecture and measurable gates

The dependency-free `bma` package separates offline mesh analysis and state machines
from `bma.blender_runtime` (Blender only), and `bma.integration` (optional MCP SDK).
The repository is also a portable Agent Skill. Only task-relevant domain files are loaded.

`mesh.py` consumes world-space snapshots. The Blender collector extracts source
and evaluated meshes independently, inventories transforms/dependencies, and
produces JSON plus a readable summary. Validators never repair meshes. Failures,
unavailable checks and visual-review requirements remain explicit.

`workflow.py` enforces ordered stages, existing artifact checkpoints, technical
reports, four reviewed views, explicit user approvals, and downstream invalidation
when an approved stage is reopened. Artifact hashes detect changed evidence.
An authority reference is a redacted identifier of the actual user instruction,
not a stored conversation or the agent's own approval. The local journal is an
audit aid, not an authentication system. Direct MCP access can bypass BMA;
this is not a Python sandbox or security boundary.

`integration.py` discovers official tool schemas via a supplied async transport.
Only named operations are exposed by BMA. Mutating operations need a workflow
permit and an existing checkpoint; declared target names and fingerprints are
checked in Blender immediately before editing. General arbitrary Python execution
remains outside BMA's guarded API. Failed or timed-out mutations are not retried
automatically: inspect actual state first.

`correction.py` caps attempts and records evidence, plans and outcomes. A technical
pass without reviewed images remains `needs_visual_review`. The synthetic defect
demo is a regression exercise, not a claim of autonomous artistic judgment.

Default hard-surface gates: zero degenerate faces, overfull/boundary edges, winding
conflicts and zero-length edges; triangle budget 100,000. Duplicate vertices and
loose elements are warnings requiring context. Open surfaces allow boundaries.
Game profile requires UVs. Subdivision profile warns on non-quads without globally
forbidding triangles or n-gons. Tolerances are in world Blender units; reports also
record scene unit scale. All thresholds are configurable and must match asset use.

The first executed specialization is a removable-lid instrument enclosure. Other
domains supply focused modeling instructions; automated domain-specific quality
metrics and deformation/curvature testing are experimental and not claimed.
