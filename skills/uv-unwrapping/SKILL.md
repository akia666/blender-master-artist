---
name: bma-uv-unwrapping
description: Review Blender UV layer presence and plan seams, distortion, texel density and packing for asset delivery.
---

# UV guidance

Confirm target use, texture size, texel-density range, intentional overlaps and required
UV channels. Inspect existing UVs before editing; preserve approved or hand-authored
islands. Mark seams along plausible boundaries with low visibility and distortion cost.

Inspect checker distortion from four views, island orientation, padding at actual
delivery resolution and density across components. Mirror/stack islands only when
texturing and baking requirements allow it. Export and reimport the actual target format
when UV delivery is required.

The game profile enforces layer presence. That does not establish UV quality, valid
coordinates, overlap, padding or baking suitability. Those automatic metrics are not
implemented in v0.1. Do not call a UV-presence pass an unwrap-quality pass.
