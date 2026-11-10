# Reproducible testing

Run from the checkout with Python 3.10+:

```sh
python -m unittest discover -s tests -v
python scripts/check_skills.py .
python scripts/privacy_audit.py .
python -m bma validate-snapshot examples/cube.json --output outputs/cube-report.json
```

The offline tests use synthetic snapshots, journals, authority identifiers, image byte
fixtures and a mock MCP transport. They do not count as Blender or human-review evidence.
The bundle installer is tested with a temporary destination and never changes global config.

Real Blender suite (includes actual four-view CPU renders and checkpoint roundtrip):

```sh
blender --background --factory-startup --python-exit-code 1 --python tests/blender_integration.py
blender --background --factory-startup --python-exit-code 1 --python scripts/blender_demo.py -- --output outputs/demo
```

Use an empty demo directory on each run. Outputs contain actual `.blend` copies,
reports, hashes and PNGs. For limited environments use `--no-render`, but report
visual verification pending. The tests verify original mesh fingerprints, unchanged
datablock counts after capture, modifier preservation, source/evaluated counts,
world-space metrics, defects and stale-target refusal.

For official MCP, first start an isolated factory bridge as in installation. With
the official server installed in the active Python environment, run:

```sh
python scripts/mcp_smoke.py --server-command python --server-arg=-m --server-arg=blmcp --output outputs/mcp-smoke
```

This checks actual schema detection, inspect/create/edit/render/save/validate calls,
preserved factory geometry and refusal to advance without approval. It uses a deliberately
synthetic BLOCKOUT state fixture; it does not record a real user's stage approval.
Stop the bridge after verification. Never run this against a real user project.

In restricted Windows environments asyncio's local socket setup may be blocked even
for offline mock tests. Use an environment permitting local IPC; do not interpret a
hang as a test pass. If temporary-file policies block Blender, point TEMP/TMP at a
writable test-output directory for that process. No system preferences need changing.

CI runs offline tests and packaging checks. A manually dispatched Blender job expects
a self-hosted runner with Blender already installed; it installs no Blender or add-on.
Hosted CI execution has not been claimed from local results.
