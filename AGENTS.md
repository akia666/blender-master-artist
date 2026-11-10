# Working on Blender Master Artist

Use the official Blender Lab MCP integration. Read `SKILL.md` for modeling work;
read `docs/architecture.md` before changing workflow or adapter contracts.

Run `python -m unittest discover -s tests -v` and `python scripts/privacy_audit.py .`.
For Blender changes also run the synthetic integration suite described in `docs/testing.md`.
Keep test outputs under `outputs/`; never commit personal paths, local preferences,
private references, user assets, transcripts, or credentials. Do not publish or push
without explicit user authorization.

Validation is read-only. Do not call `Mesh.validate()` on user meshes: it repairs them.
Do not bypass approvals, claim unviewed images were reviewed, or call a mock test a live test.
Existing and approved geometry is preserved unless the user explicitly authorizes a scoped revision.

