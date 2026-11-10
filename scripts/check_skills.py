"""Standard-library packaging and local-link checks for the authored skills."""

import argparse
from pathlib import Path
import re


def check(root):
    root = Path(root)
    failures = []
    paths = [root / "SKILL.md"] + sorted((root / "skills").glob("*/SKILL.md"))
    names = set()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            failures.append(f"{path.relative_to(root)}: missing YAML frontmatter")
            continue
        header = text.split("---", 2)[1]
        fields = dict(re.findall(r"^(name|description):\s*(.+)$", header, re.M))
        name = fields.get("name", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) >= 64 or name in names:
            failures.append(f"{path.relative_to(root)}: invalid or duplicate name")
        names.add(name)
        if not fields.get("description", "").strip():
            failures.append(f"{path.relative_to(root)}: empty description")
    # Validate local Markdown file links throughout the bundle, including docs.
    for path in root.rglob("*.md"):
        if {"outputs", ".git", ".venv", ".cache", ".agents", ".claude"} & set(path.relative_to(root).parts):
            continue
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            if target and not (path.parent / target).exists():
                failures.append(f"{path.relative_to(root)}: missing local link {target}")
    return {"skills_checked": len(paths), "status": "fail" if failures else "pass", "failures": failures}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    result = check(parser.parse_args().root)
    print(result)
    raise SystemExit(result["status"] != "pass")
