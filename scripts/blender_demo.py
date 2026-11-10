"""Run: blender --background --factory-startup --python-exit-code 1 --python scripts/blender_demo.py -- --output outputs/demo"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bma.demo import run_demo

parser = argparse.ArgumentParser()
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--no-render", action="store_true")
parser.add_argument("--resolution", type=int, default=384)
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
result = run_demo(args.output, render=not args.no_render, resolution=args.resolution)
print("BMA_DEMO_RESULT", result)

