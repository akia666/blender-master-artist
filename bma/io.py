"""Small deterministic, private-by-default artifact helpers."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_json(path, value):
    """Atomic replace; a failed serialization never truncates a valid journal."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=".bma-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def relative_file(root, value):
    """Require an existing workspace file; reject absolute paths and symlink escapes."""
    root = Path(root).resolve()
    value = Path(value)
    if value.is_absolute() or ".." in value.parts:
        raise ValueError("Artifact paths must be relative and contained in the workspace")
    resolved = (root / value).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("Artifact must be an existing file inside the workspace")
    return resolved

