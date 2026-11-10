# Blender Master Artist

[Русская версия](README.md)

Evidence-based AI modeling workflows for **official Blender Lab MCP**.

BMA combines a portable Agent Skill, read-only Blender mesh validators, versioned
checkpoints, explicit stage approvals and bounded correction loops. Its first working
specialization is an original hard-surface instrument enclosure. It aims for measurable,
reviewable quality; it does not promise flawless or universally production-ready models.

## What works in v0.1

- Scene inventory, source/evaluated mesh reports, geometry fingerprints and JSON summaries.
- Configurable topology, area, duplicate-radius, transform, density, UV-presence and budget checks.
- Four neutral inspection renders with image hashes; visual review remains an explicit action.
- Ordered stage gates, checkpoint receipts, scoped edit permits and stale-evidence rejection.
- Official Blender Lab MCP adapter with schema discovery and a real stdio smoke test.
- A reproducible blockout → refinement → deliberate defects → targeted repair demonstration.
- Provenance-aware knowledge records and a publication privacy audit.

See [verification](docs/verification.md) for actual executed checks and limitations,
[architecture](docs/architecture.md) for contracts, and [research](docs/research.md)
for the integration/licensing comparison. Other modeling domains have focused guidance;
automated domain-specific reconstruction is not implemented.

## Requirements and quick start

Core: Python 3.10+, standard library only. Blender runtime target: Blender 5.1+.
Verified locally with external Python 3.12 and Blender 5.3.0; other target versions
are not yet runtime-certified. MCP client support is optional: `mcp>=1.2,<2`.
Blender's bundled Python supplies `bpy`, `bmesh` and `mathutils`; do not install a
separate `bpy` wheel into your normal interpreter to run this project.

From this checkout:

```sh
python -m unittest discover -s tests -v
python -m bma validate-snapshot examples/cube.json --output outputs/cube-report.json
python scripts/privacy_audit.py .
```

Optional editable package and MCP SDK installation, only when you choose to install:

```sh
python -m pip install -e ".[mcp]"
```

Run the actual Blender demonstration in a **separate factory-startup process**:

```sh
blender --background --factory-startup --python-exit-code 1 --python scripts/blender_demo.py -- --output outputs/demo
```

Use an empty output directory. This writes four versioned `.blend` checkpoints,
checkpoint receipts, source/evaluated reports, defect/correction evidence, and front,
side, top and perspective PNGs. All generated assets stay ignored in `outputs/`.
The demo leaves visual acceptance and user approval pending; no approval is fabricated.

## Use as an agent skill

The root [SKILL.md](SKILL.md) is the platform-independent entry point. Install a
self-contained copy into your chosen agent's skill directory:

```sh
python scripts/install_skill.py --destination .agents/skills/blender-master-artist
```

For Claude Code, use `.claude/skills/blender-master-artist` instead. The installer
copies only reviewed project sources and refuses an existing destination. It never
installs Blender, enables add-ons, registers MCP or changes system configuration.
See [installation](docs/installation.md), [Codex](integrations/codex/README.md),
and [Claude Code](integrations/claude/README.md).

Example prompt:

> Use Blender Master Artist with official Blender Lab MCP. Inspect the current
> scene, preserve existing geometry, and plan a removable-lid enclosure. Establish
> documented dimensions, save a checkpoint, and present the research stage for approval.

## Acceptance and limitations

Technical validation, visual review, user approval and actual export are distinct
results. Technical pass does not prove silhouette fidelity, outward normals, no
self-intersections, good UV packing, useful edge flow, deformation, manufacturing
feasibility or performance in a target engine. BMA ships no vision model or general
automatic repair engine. The demo repair removes known injected defects only.

The workflow journal and guarded adapter prevent accidental cooperative workflow
bypasses. They do not authenticate a human or sandbox arbitrary Python. Direct MCP
access remains outside those guards. Review the [security guidance](SECURITY.md).

## Project and license

`bma/` contains functioning Python code; `skills/`, `knowledge/` and `workflows/`
provide progressive instructions; `integrations/` documents official MCP and agent
differences; `tests/` includes offline and actual Blender suites; `examples/` contains
synthetic inputs. [Contributions](CONTRIBUTING.md) should include relevant evidence.

BMA code and original examples are [MIT licensed](LICENSE). Blender Lab MCP and its
add-on retain their GPL-3.0-or-later licensing and are not bundled here. No personal
assets, private references, account metadata or conversations belong in the project.
Run the [privacy audit](docs/privacy.md) before publication. Nothing is automatically
published or pushed to GitHub.
