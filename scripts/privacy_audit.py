"""Audit publication candidates, including staged/ignored files explicitly selected.

Prints relative filenames, rule IDs and line numbers; never echoes matched secrets.
This heuristic is a release aid, not proof that a repository is free of private data.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess


PATTERNS = {
    "personal_windows_path": re.compile(r"[A-Za-z]:[\\/]+(?:Users|Documents and Settings)[\\/]+[^\s\\/<>]+", re.I),
    "personal_unix_path": re.compile(r"/(?:home|Users)/[A-Za-z0-9_.-]+/"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "service_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b"),
    "assigned_secret": re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']"),
    "email_address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}
SKIP_DIRS = {".git", ".venv", ".cache", "__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist"}
SENSITIVE_NAMES = {"secrets", "credentials", "id_rsa", "id_ed25519", "chat_history.json", "conversations.json"}
BINARY_SUFFIXES = {".blend", ".blend1", ".fbx", ".glb", ".gltf", ".obj", ".png", ".jpg", ".jpeg",
                   ".webp", ".pdf", ".zip", ".7z", ".mp4", ".wav", ".exr", ".docx"}


def git_files(root):
    try:
        result = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                                capture_output=True, check=True)
        return [Path(p) for p in result.stdout.decode("utf-8").split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        return None


def audit(root, all_files=False):
    root = Path(root).resolve()
    selected = None if all_files else git_files(root)
    candidates = selected if selected is not None else [p.relative_to(root) for p in root.rglob("*")
                                                        if p.is_file() or p.is_symlink()]
    findings = []
    scanned = 0
    for relative in sorted(set(candidates)):
        # Tracked files in ignored directories are still audited. Only unversioned
        # fallback enumeration skips local outputs/runtime folders.
        if selected is None and (set(relative.parts) & SKIP_DIRS or any(p.endswith(".egg-info") for p in relative.parts) or
                                 (not all_files and relative.parts[0] in {"outputs", "private"})):
            continue
        path = root / relative
        label = relative.as_posix()
        if path.is_symlink():
            findings.append({"path": label, "rule": "symlink_requires_review", "line": 0})
            continue
        if not path.is_file():
            continue
        scanned += 1
        lower = path.name.lower()
        if (set(p.lower() for p in relative.parts) & SENSITIVE_NAMES or lower.startswith(".env")
                or path.suffix.lower() in {".pem", ".key", ".p12"}):
            findings.append({"path": label, "rule": "sensitive_filename", "line": 0})
        if path.suffix.lower() in BINARY_SUFFIXES or re.search(r"\.blend\d+$", lower):
            findings.append({"path": label, "rule": "asset_requires_license_and_metadata_review", "line": 0})
            continue
        if path.stat().st_size > 2_000_000:
            findings.append({"path": label, "rule": "large_file_requires_review", "line": 0})
            continue
        data = path.read_bytes()
        if b"\0" in data:
            findings.append({"path": label, "rule": "unrecognized_binary", "line": 0})
            continue
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            findings.append({"path": label, "rule": "unrecognized_encoding", "line": 0})
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for rule, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append({"path": label, "rule": rule, "line": number})
    return {"status": "fail" if findings else "pass", "files_scanned": scanned, "findings": findings,
            "mode": "all_files" if all_files else "publication_candidates",
            "limitations": "Names, proprietary content and secrets outside known patterns require human review"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--all-files", action="store_true", help="Also scan ignored outputs and private directories")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root, args.all_files)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return int(result["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
