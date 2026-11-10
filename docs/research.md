# Integration research

Researched 2026-11-11. Links are upstream evidence, not endorsements or copied code.
The chosen integration is **official Blender Lab MCP**, as requested. Other candidates
are evaluated for context and are not dependencies or fallback transports.

| Project | Availability and maintenance evidence | License and compatibility | Decision |
| --- | --- | --- | --- |
| [Blender Lab MCP](https://projects.blender.org/lab/blender_mcp) | Official [Blender page](https://www.blender.org/lab/mcp-server/); [v1.0.3 release](https://projects.blender.org/lab/blender_mcp/releases) dated 2026-09-11; Lab listing updated 2026-09-29. Local upstream source and installed extension were inspected. | GPL-3.0-or-later; Blender 5.1+; local server metadata requires external Python 3.10+ and MCP SDK <2. | Selected. Small documented tool surface, API/manual search, JSON results, background variants. |
| [ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender) | Former `blender-mcp` repository redirects here; current package metadata shows 2.2.7. Reachable source and README; no GitHub releases on the inspected page. Exact latest commit date could not be independently retrieved. | MIT; README says Blender 3.0+, external Python 3.10+. Has `execute_blender_code`, scene inspection, `look`, asset/generator integrations and telemetry. | Not used. Different add-on protocol and broader external integrations. Sharing port 9876 does not imply compatibility. |
| [DCC-MCP Blender](https://github.com/dcc-mcp/dcc-mcp-blender) | Reachable source; metadata 0.2.27; repository has tests and CI. Exact latest commit date unavailable from accessible metadata. | Source/PyPI MIT; Blender Extensions ZIP GPL-3.0-or-later according to README. Depends on `dcc-mcp-core>=0.20,<0.21`; embedded host Python governs actual compatibility, not just package minimum. | Not used. Typed tools and progressive skills are useful, but an additional gateway is unnecessary for this release. |
| [BlendRelay](https://github.com/shefq/blendrelay-mcp) | Reachable; [0.7.7 release](https://github.com/shefq/blendrelay-mcp/releases) dated 2026-11-09. Release notes describe transport limitations. | Package metadata says MIT AND GPL-3.0-or-later; Blender 4.5+, external Python 3.11+. | Not used. Prompts, sketches and checkpoints are documented; its broader UI/runtime is outside this integration. |
| [Blender agent skills](https://github.com/EL4CTEO/blender-skills) | Reachable README and MIT license; claims Blender 5.2+ workflows and headless tests. Its test and quality claims were not independently rerun. Exact last commit date unverified. | MIT, Blender 5.2+ according to README. | Useful comparison for routing; no content or scripts vendored. BMA supplies executable evidence and approval gates. |

## Verified official contract

The installed official 1.0.3 extension manifest declares Blender 5.1+ and
GPL-3.0-or-later. The available MCP tools were enumerated in this environment;
capabilities are derived from names and input schemas, never advertised counts.

- `get_objects_summary` inventories collection hierarchy.
- `get_object_detail_summary` drills into named objects.
- `execute_blender_code(code)` expects a JSON-serializable `result` variable.
- Screenshot, render, documentation search and `*_for_cli` tools exist, but their
  presence alone does not prove a live connection.
- The initial live inventory request failed because no bridge was listening.
  Subsequent verification results belong in `docs/verification.md`.

BMA uses the official MCP client transport and reuses these tools. It implements
no replacement socket protocol or MCP server. Its runtime package must be
available on the Blender machine through a shared local checkout. MCP source
and add-on may have different versions; report them separately.

## Validation and feedback

Blender's bundled `bpy.types.Mesh` documentation was inspected through the official
`get_python_api_docs` tool. `Mesh.validate()` corrects/removes invalid geometry;
therefore BMA never invokes it on source meshes. It copies source data for
tessellation and separately frees evaluated meshes. Incidence, area, duplicate
radius and triangle budgets are deterministic; outward normals, plausible
construction, pinching, deformation and silhouette quality need contextual review.

[BMesh documentation](https://docs.blender.org/api/current/bmesh.types.html)
provides manifold/boundary concepts. The 3D Print Toolbox is another domain-specific
checker, not a universal quality certificate; its current extension listing was
inaccessible during research, so no current compatibility claim is made.

[ViSculpt](https://arxiv.org/abs/2608.24169) describes visual feedback for localized
mesh editing and preservation. It motivates explicit image evidence, not a BMA
benchmark claim. BMA captures four fixed views, records hashes, separates capture
from review, and bounds correction attempts. It ships no autonomous vision model.
Measured aligned binary silhouette IoU is available; photos require camera alignment
and segmentation before that number is meaningful.

## Licensing boundary

BMA is original MIT-licensed code and documentation. It neither vendors nor
redistributes Blender Lab code, manuals, add-ons, or third-party models. Blender
and official upstream MCP components retain their GPL terms. A distributor
combining or modifying those components must assess and comply with their licenses;
BMA's MIT license does not relicense them. Synthetic example geometry is original.

