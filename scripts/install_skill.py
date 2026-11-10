"""Copy a self-contained, allowlisted skill bundle to an explicitly chosen location."""

import argparse
from pathlib import Path
import shutil

ROOT_FILES = ["SKILL.md", "README.md", "README.en.md", "LICENSE", "AGENTS.md", "CLAUDE.md", "pyproject.toml",
              "SECURITY.md", "CONTRIBUTING.md", "MANIFEST.in", ".gitignore"]
ROOT_DIRS = ["bma", "scripts", "skills", "knowledge", "workflows", "validators", "integrations", "docs", "examples", "tests"]


def install_bundle(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists():
        raise FileExistsError("Destination already exists; review/version it before installing an update")
    candidates = [source / name for name in ROOT_FILES]
    for directory in ROOT_DIRS:
        candidates.extend(p for p in (source / directory).rglob("*") if p.is_file()
                          and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"})
    for path in candidates:
        if path.is_symlink() or not path.resolve().is_relative_to(source) or not path.is_file():
            raise ValueError("Bundle source must contain real, contained project files")
    # Enumerate first so a destination below the checkout cannot recursively copy itself.
    for path in candidates:
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    return {"files": len(candidates), "skill": "blender-master-artist"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(install_bundle(Path(__file__).resolve().parents[1], args.destination))


if __name__ == "__main__":
    main()
