# Claude Code

Install the same bundle into `.claude/skills/blender-master-artist`; invoke
`/blender-master-artist`. The root `CLAUDE.md` points at shared repository instructions.
See [official skills documentation](https://code.claude.com/docs/en/skills).

Register the official source server only when you choose to configure it:

```sh
claude mcp add --transport stdio blender -- uv tool run --from "git+https://projects.blender.org/lab/blender_mcp.git@v1.0.3#subdirectory=mcp" blender-mcp --transport stdio
```

See [Claude's MCP documentation](https://code.claude.com/docs/en/mcp). Do not configure
blanket automatic approval of arbitrary code to bypass BMA's modeling gates. Use the
same core workflow, reports and evidence as Codex; no separate modeling rules apply.
