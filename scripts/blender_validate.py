"""Read-only Blender entrypoint for a .blend file already opened by the caller."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bma.blender_runtime import validate_scene
from bma.io import write_json
from bma.mesh import Profile

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--profile", choices=["hard-surface", "open-surface", "game", "subdivision"], default="hard-surface")
parser.add_argument("--object", action="append", dest="names")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
report = validate_scene(Profile.named(args.profile), names=args.names)
write_json(args.output, report)
print(report["summary"])
if report["status"] != "pass":
    raise RuntimeError("BMA technical quality gate failed; inspect the JSON report")
