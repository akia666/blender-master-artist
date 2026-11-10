# Security

Blender Lab MCP executes Python with Blender's process privileges. BMA is not a
sandbox. Its named operations, stale-state checks and approval journal reduce
accidental workflow mistakes but cannot prevent a client from using upstream tools
directly. Run trusted code, keep the bridge on loopback, and stop test bridges when done.
Use isolation appropriate to the sensitivity of your projects.

No network calls, telemetry, credential storage or automatic software installation
exist in the BMA core. The optional SDK launches only the caller-selected server command;
upstream components have their own policies and dependencies. Source pins should be
reviewed before changing them. Do not load untrusted `.blend` scripts with unrestricted
auto-execution just to inspect an asset.

Report security issues privately through your hosting platform's private vulnerability
reporting mechanism if enabled. If unavailable, contact the maintainers through a
private channel they publish; never put credentials or private assets in a public issue.
Remove and rotate exposed credentials independently of deleting a Git commit.
