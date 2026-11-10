# Read-only mesh validation

The executable implementation is `bma/mesh.py` plus Blender extraction in
`bma/blender_runtime.py`, avoiding a second divergent validator implementation here.

```sh
blender --background --factory-startup --disable-autoexec model.blend --python-exit-code 1 --python scripts/blender_validate.py -- --output outputs/report.json --profile hard-surface
```

`--object` can repeat to define exact scope. This opens a file in a separate process,
does not save or repair it, writes JSON and prints a summary. A failed quality gate
causes a nonzero Blender exit through `--python-exit-code 1`. Invoke trusted files
with your normal Blender auto-execution policy.

Inside Blender/MCP, import `Profile` and call
`validate_scene(Profile(duplicate_tolerance=1e-6, area_tolerance=1e-12, max_triangles=100000))`.
Threshold distances/areas are world-space Blender units/units squared; the scene's
meters-per-unit is reported, not silently applied as a different unit convention.

Reports include object/collection inventory separately, counts, incidence, winding,
degenerate/duplicate/loose geometry, source/evaluated metrics, transforms, modifiers,
bounds/density, UV presence, unavailable checks, export scope and visual-review status.
Issue samples are bounded while counts remain complete. Duplicate pairs are diagnostic,
not an instruction to merge vertices. Read the report limitations before acceptance.
