"""Read-only geometry checks shared by offline fixtures and Blender extraction.

Distances are in world-space Blender units. This checks incidence and winding,
not semantic edge flow, watertight volume orientation, or self intersections.
"""

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from itertools import product
import math

from bma.io import digest


@dataclass(frozen=True)
class Profile:
    name: str = "hard-surface"
    closed_surface: bool = True
    require_uv: bool = False
    subdivision: bool = False
    max_triangles: int = 100000
    duplicate_tolerance: float = 1e-6
    area_tolerance: float = 1e-12
    sample_limit: int = 20

    def __post_init__(self):
        if (not math.isfinite(self.duplicate_tolerance) or self.duplicate_tolerance <= 0
                or not math.isfinite(self.area_tolerance) or self.area_tolerance < 0
                or type(self.max_triangles) is not int or type(self.sample_limit) is not int
                or self.max_triangles < 1 or self.sample_limit < 1):
            raise ValueError("Invalid tolerance, sample limit, or triangle budget")

    @classmethod
    def named(cls, name):
        options = {
            "hard-surface": {},
            "open-surface": {"closed_surface": False},
            "game": {"require_uv": True},
            "subdivision": {"subdivision": True},
        }
        if name not in options:
            raise ValueError("Unknown profile: " + name)
        return cls(name=name, **options[name])


def polygon_area(vertices, face):
    """Newell area for planar polygons; Blender supplies tessellated areas instead."""
    normal = [0.0, 0.0, 0.0]
    for a, b in zip(face, face[1:] + face[:1]):
        p, q = vertices[a], vertices[b]
        normal[0] += (p[1] - q[1]) * (p[2] + q[2])
        normal[1] += (p[2] - q[2]) * (p[0] + q[0])
        normal[2] += (p[0] - q[0]) * (p[1] + q[1])
    return math.sqrt(sum(x * x for x in normal)) / 2


def duplicate_pairs(vertices, tolerance, limit=20):
    """Spatial hash, Euclidean radius, including adjacent bins; bounded samples."""
    cells = defaultdict(list)
    count, samples = 0, []
    for i, p in enumerate(vertices):
        key = tuple(math.floor(v / tolerance) for v in p)
        for offset in product((-1, 0, 1), repeat=3):
            neighbor = tuple(a + b for a, b in zip(key, offset))
            for j in cells.get(neighbor, ()):
                if math.dist(p, vertices[j]) <= tolerance:
                    count += 1
                    if len(samples) < limit:
                        samples.append([j, i])
        cells[key].append(i)
    return count, samples


def analyze_mesh(snapshot, profile=None):
    profile = profile or Profile()
    vertices = [tuple(v) for v in snapshot["vertices"]]
    faces = [list(f) for f in snapshot["faces"]]
    edges = [tuple(e) for e in snapshot.get("edges", [])]
    issues = []

    def issue(code, severity, count, samples=(), message=""):
        if count:
            issues.append({"code": code, "severity": severity, "count": count,
                           "samples": list(samples)[:profile.sample_limit], "message": message})

    invalid_coordinates = [i for i, p in enumerate(vertices)
                           if len(p) != 3 or not all(math.isfinite(x) for x in p)]
    invalid_faces = [i for i, face in enumerate(faces)
                     if len(face) < 3 or any(type(x) is not int or not 0 <= x < len(vertices) for x in face)]
    invalid_edges = [i for i, edge in enumerate(edges)
                     if len(edge) != 2 or any(type(x) is not int or not 0 <= x < len(vertices) for x in edge)]
    issue("invalid_coordinates", "error", len(invalid_coordinates), invalid_coordinates)
    issue("invalid_face_indices", "error", len(invalid_faces), invalid_faces)
    issue("invalid_edge_indices", "error", len(invalid_edges), invalid_edges)
    if issues:
        return {"status": "fail", "issues": issues, "metrics": {}, "fingerprint": None}

    incidence = defaultdict(list)
    face_vertices = set()
    areas = snapshot.get("face_areas")
    if areas is None:
        areas = [polygon_area(vertices, f) for f in faces]
    if len(areas) != len(faces) or any(not math.isfinite(a) or a < 0 for a in areas):
        raise ValueError("Face areas must be finite, nonnegative, and aligned with faces")
    degenerate = []
    seen_faces, duplicates = set(), []
    for i, face in enumerate(faces):
        if len(set(face)) != len(face) or areas[i] <= profile.area_tolerance:
            degenerate.append(i)
        # Canonical cyclic order, independent of starting corner and winding.
        if len(set(face)) == len(face):
            start = face.index(min(face))
            forward = face[start:] + face[:start]
            backward = [forward[0]] + forward[:0:-1]
            key = min(tuple(forward), tuple(backward))
        else:
            key = tuple(sorted(face))
        if key in seen_faces:
            duplicates.append(i)
        seen_faces.add(key)
        face_vertices.update(face)
        for a, b in zip(face, face[1:] + face[:1]):
            incidence[tuple(sorted((a, b)))].append((i, a, b))

    edge_keys = {tuple(sorted(e)) for e in edges} | set(incidence)
    boundary = [list(e) for e, fs in incidence.items() if len(fs) == 1]
    overfull = [list(e) for e, fs in incidence.items() if len(fs) > 2]
    winding = [list(e) for e, fs in incidence.items()
               if len(fs) == 2 and fs[0][1:] == fs[1][1:]]
    loose_edges = [list(e) for e in edge_keys if e not in incidence]
    edge_vertices = {v for edge in edge_keys for v in edge}
    loose_vertices = [i for i in range(len(vertices)) if i not in face_vertices]
    isolated_vertices = [i for i in range(len(vertices)) if i not in edge_vertices]
    zero_edges = [list(e) for e in edge_keys if math.dist(vertices[e[0]], vertices[e[1]])
                  <= profile.duplicate_tolerance]
    duplicate_count, pairs = duplicate_pairs(vertices, profile.duplicate_tolerance, profile.sample_limit)
    triangles = sum(len(f) - 2 for f in faces)
    dimensions = [max((p[i] for p in vertices), default=0) - min((p[i] for p in vertices), default=0)
                  for i in range(3)]
    total_area = sum(areas)
    distribution = Counter("triangles" if len(f) == 3 else "quads" if len(f) == 4 else "ngons" for f in faces)
    issue("empty_mesh", "error", int(not vertices or not faces))
    issue("boundary_edges", "error" if profile.closed_surface else "info", len(boundary), boundary)
    issue("non_manifold_edges", "error", len(overfull), overfull)
    issue("degenerate_faces", "error", len(degenerate), degenerate)
    issue("duplicate_faces", "error", len(duplicates), duplicates)
    issue("duplicate_vertices", "warning", duplicate_count, pairs, "Coincidence can be intentional at seams")
    issue("zero_length_edges", "error", len(zero_edges), zero_edges)
    issue("loose_edges", "warning", len(loose_edges), loose_edges)
    issue("loose_vertices", "warning", len(loose_vertices), loose_vertices)
    issue("inconsistent_winding", "error", len(winding), winding)
    issue("triangle_budget", "error", int(triangles > profile.max_triangles), message="Triangle budget exceeded")
    issue("missing_uv", "error" if profile.require_uv else "info", int(not snapshot.get("uv_layers")))
    issue("subdivision_nonquads", "warning", sum(len(f) != 4 for f in faces) if profile.subdivision else 0)
    return {
        "status": "fail" if any(i["severity"] == "error" for i in issues) else "pass",
        "issues": issues,
        "fingerprint": digest({"vertices": vertices, "edges": sorted(edge_keys), "faces": faces}),
        "metrics": {"vertices": len(vertices), "edges": len(edge_keys), "faces": len(faces),
                    "triangles": triangles, "face_types": dict(distribution), "dimensions": dimensions,
                    "bounding_box": {"minimum": [min((p[i] for p in vertices), default=0) for i in range(3)],
                                     "maximum": [max((p[i] for p in vertices), default=0) for i in range(3)]},
                    "surface_area": total_area, "faces_per_square_unit": len(faces) / total_area if total_area else None,
                    "isolated_vertices": len(isolated_vertices),
                    "non_manifold_edges_including_boundary_and_wire": len(boundary) + len(overfull) + len(loose_edges)},
        "profile": asdict(profile),
        "limitations": ["Winding consistency does not prove outward normals",
                        "Self intersections, pinching, edge flow, and UV overlap need separate review"],
    }


def summarize(report):
    objects = report.get("objects", [report])
    lines = ["Technical validation: " + report["status"]]
    for obj in objects:
        mesh = obj.get("source", obj)
        metrics = mesh.get("metrics", {})
        lines.append(f"{obj.get('name', 'mesh')}: {metrics.get('vertices', '?')} vertices, "
                     f"{metrics.get('triangles', '?')} triangles")
        sections = {"source": mesh} if "source" not in obj else {
            "source": mesh, "evaluated": obj.get("evaluated", {}), "object": {"issues": obj.get("issues", [])}}
        for section, data in sections.items():
            for item in data.get("issues", []):
                lines.append(f"  {section} {item['severity']}: {item['code']} ({item['count']})")
    return "\n".join(lines)

