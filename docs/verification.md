# Verification record

Local verification date: 2026-11-11. These are actual local results, not a hosted CI
badge or a comparative AI benchmark. Generated evidence stays in ignored `outputs/`.

Environment: Windows, Blender 5.3.0; installed official Blender Lab add-on 1.0.3;
official upstream MCP server checkout reporting package 1.0.2; MCP SDK 1.30.0;
external Python 3.12. Source and add-on versions are deliberately reported separately.

The initial bridge was unavailable. An isolated background factory-startup Blender
was subsequently launched with the already installed official extension. No Blender
or add-on was installed, no user project was opened and no preferences were saved.

Verified operations (36 offline tests and 14 actual Blender integration tests passed):

- Offline geometry, approval-state, knowledge, reference, correction and adapter tests.
- Actual Blender source/evaluated geometry checks, world dimensions/area, deliberate
  defects, Object-mode refusal, stale-target refusal, non-destructive bevels,
  versioned checkpoint roundtrip and four-view render cleanup.
- Official MCP stdio discovery and actual inspect/create/bevel/validate/render/save calls.
  The real discovered tool count was 26; this is an observation, not a required count.
- Original synthetic enclosure demonstration: blockout, refined shell/lid/panel,
  injected defects, targeted injected-vertex removal and a passing final technical report.
- Saved final `.blend` reopened in another process and passed the same scoped technical gate.
- Runtime wheel and source distribution built locally without installing new build tools.
  The wheel's CLI was exercised directly from its archive in an isolated import path.
- Publication-candidate privacy scan and skill/link validation.

Reproduce with [testing instructions](testing.md). Final execution totals and runtime
evidence are summarized in `outputs/verification.json` when available. Local paths,
raw logs, images and `.blend` files are intentionally excluded from publication.

Limits: Blender 5.1/5.2 and other operating systems have not been runtime-certified;
the source-pinned 1.0.3 MCP server launch has not been independently installed here.
No hosted CI run, general reference reconstruction benchmark, rig deformation test,
self-intersection proof, manufacturing validation or target-engine export is claimed.
The final demo's four exterior views were actually inspected by the agent. The lid seam,
separate front panel and primary box silhouette were visible; the covered interior and
manufacturing fit were not visually verified. That review is recorded with limitations
in the local manifest. No test fixture's approval identifiers stand for a real user
approval. Newly generated demo manifests always start unreviewed.
