# Installation

No installer is run automatically. Choose the operations below that you need.

1. Install Blender 5.1+ and the official Blender Lab MCP add-on following the
   [official page](https://www.blender.org/lab/mcp-server/). The official 1.0.3 extension
   is GPL-3.0-or-later. Enable its bridge manually for an interactive session. Do not
   confuse it with a community add-on that also happens to use port 9876.
2. Obtain this checkout. Run the standard-library tests before installation. Optional:
   `python -m pip install -e ".[mcp]"` installs the BMA package and the SDK client.
3. Install the skill with an explicitly chosen destination. For a project Codex setup:
   `python scripts/install_skill.py --destination .agents/skills/blender-master-artist`.
   For Claude Code use `.claude/skills/blender-master-artist`. User-level destinations
   can also be passed explicitly. Existing destinations are refused, not overwritten.
4. Register the **official source** server using the platform instructions below. A
   source pin avoids accidentally resolving an unrelated package with the same name.
   First-time dependency downloads may need a longer startup timeout.
5. Start/reload the agent, confirm the skill appears, and ask for read-only scene inventory.
   Tool discovery alone does not establish a working Blender bridge.

Portable official server launch, with `uv` and Git already installed:

```sh
uv tool run --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp" blender-mcp --transport stdio
```

This command may download dependencies when you run it; BMA does not execute it as
part of its installer. Alternatively install the reviewed official server checkout
into an isolated environment, then launch that environment's Python with `-m blmcp`.
The official source, add-on and SDK have independent version constraints.

See [Codex setup](../integrations/codex/README.md), [Claude setup](../integrations/claude/README.md)
and [official adapter usage](../integrations/blender-mcp/README.md). The Blender
machine must have the same BMA checkout available at the adapter's `shared_checkout`
path. A remote MCP host cannot import a path that exists only on the client machine.

For testing an already installed official extension, use an isolated background bridge:

```sh
blender --background --factory-startup --online-mode --addons bl_ext.user_default.mcp --command blender_mcp --host 127.0.0.1 --port 9876
```

The extension module depends on the repository Blender installed it into; replace
`bl_ext.user_default.mcp` with the actual installed module (for example the Lab repository).
Do not install a duplicate copy. `--online-mode` affects that process; never save
preferences to enable it globally as an incidental setup step. Stop the test process
after verification. Run the synthetic demo in a separate factory process as documented.
