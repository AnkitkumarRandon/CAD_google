from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import trimesh


@dataclass
class ExactCylinder:
    center: list[float]
    axis: list[float]
    diameter: float
    face_area: float | None = None


def to_float_list(values: np.ndarray | list[float]) -> list[float]:
    arr = np.asarray(values, dtype=float)
    return [float(x) for x in arr.tolist()]


def mesh_metadata(mesh: trimesh.Trimesh) -> dict[str, Any]:
    extents = mesh.bounding_box.extents if mesh.vertices.size else np.zeros(3)
    return {
        "extentsMm": to_float_list(extents),
        "faceCount": int(len(mesh.faces)),
        "volumeMm3": float(mesh.volume) if mesh.is_volume else None,
        "areaMm2": float(mesh.area) if mesh.faces.size else None,
    }
