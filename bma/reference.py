"""Reference metadata and aligned, binary silhouette comparison."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Dimension:
    value: float
    unit: str
    basis: str
    source: str
    uncertainty: float

    def __post_init__(self):
        if self.basis not in {"measured", "documented", "estimated"} or not self.source:
            raise ValueError("Dimension needs a measured/documented/estimated basis and source")
        if not math.isfinite(self.value) or self.value <= 0 or not math.isfinite(self.uncertainty) or self.uncertainty < 0:
            raise ValueError("Dimension and uncertainty must be finite and physically valid")


def silhouette_iou(reference, candidate, *, aligned=False):
    """Binary row arrays only; segmentation/alignment are explicit caller responsibilities."""
    if not aligned:
        raise ValueError("Calibrate view, crop, scale and projection before comparing masks")
    if not reference or not reference[0] or len(reference) != len(candidate):
        raise ValueError("Masks must be nonempty and have matching dimensions")
    width = len(reference[0])
    if any(len(row) != width for row in list(reference) + list(candidate)):
        raise ValueError("Masks must be rectangular and identically sized")
    if any(type(p) is not bool for row in list(reference) + list(candidate) for p in row):
        raise ValueError("Provide binary boolean masks")
    intersection = union = 0
    for a, b in zip(reference, candidate):
        for x, y in zip(a, b):
            intersection += x and y
            union += x or y
    if not union:
        raise ValueError("Two empty silhouettes do not establish fidelity")
    return {"iou": intersection / union, "intersection": intersection, "union": union,
            "scope": "aligned binary silhouette only"}
