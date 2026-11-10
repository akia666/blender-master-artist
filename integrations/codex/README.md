# Codex

Install the complete BMA skill bundle into `.agents/skills/blender-master-artist`
for the chosen project. Codex discovers skills in `.agents/skills`; use `/skills`
or mention `$blender-master-artist`. The frontmatter is loaded for discovery;
domain guidance loads only as needed. See [official skills documentation](https://learn.chatgpt.com/docs/build-skills).

Register the official upstream source, rather than an ambiguous package name:

```sh
codex mcp add blender -- uv tool run --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp" blender-mcp --transport stdio
codex mcp list
```

This is a user-selected configuration change; the BMA installer does not run it.
See the [official MCP documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
For slower renders choose an appropriate `tool_timeout_sec` in your private MCP
configuration. Keep all modeling invariants in the root skill, not Codex-only text.
