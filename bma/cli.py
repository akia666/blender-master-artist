"""Dependency-free command line for offline checks and approval journals."""

import argparse
import json
from pathlib import Path

from bma.io import write_json
from bma.mesh import Profile, analyze_mesh, summarize
from bma.workflow import Workflow


def main(argv=None):
    parser = argparse.ArgumentParser(prog="bma")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-snapshot", help="Offline geometry fixture; not live Blender validation")
    validate.add_argument("snapshot", type=Path)
    validate.add_argument("--output", type=Path)
    validate.add_argument("--profile", default="hard-surface", choices=["hard-surface", "open-surface", "game", "subdivision"])
    workflow = commands.add_parser("workflow")
    workflow.add_argument("action", choices=["init", "status", "submit", "approve", "advance", "reopen", "reject"])
    workflow.add_argument("journal", type=Path)
    workflow.add_argument("--artifacts", type=Path, help="JSON object mapping deliverable keys to relative artifact paths")
    workflow.add_argument("--authority-reference", help="Redacted reference to actual explicit user authorization")
    workflow.add_argument("--stage")
    workflow.add_argument("--target", action="append", default=[])
    workflow.add_argument("--failure", type=Path, help="Structured rejection JSON")
    args = parser.parse_args(argv)
    if args.command == "validate-snapshot":
        report = analyze_mesh(json.loads(args.snapshot.read_text(encoding="utf-8")), Profile.named(args.profile))
        report["execution_mode"] = "offline_snapshot"
        if args.output:
            write_json(args.output, report)
        print(summarize(report))
        return int(report["status"] != "pass")
    if args.action == "init":
        if args.journal.exists():
            parser.error("Journal already exists")
        instance = Workflow(args.journal.parent)
    else:
        instance = Workflow.load(args.journal)
    if args.action == "submit":
        if args.artifacts is None:
            parser.error("submit requires --artifacts")
        instance.submit(json.loads(args.artifacts.read_text(encoding="utf-8")))
    elif args.action == "approve":
        instance.approve(args.authority_reference)
    elif args.action == "advance":
        instance.advance()
    elif args.action == "reopen":
        instance.reopen(args.stage, args.target, args.authority_reference)
    elif args.action == "reject":
        if args.failure is None:
            parser.error("reject requires --failure")
        instance.reject(**json.loads(args.failure.read_text(encoding="utf-8")))
    if args.action != "status":
        instance.save(args.journal)
    print(json.dumps(instance.state, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
