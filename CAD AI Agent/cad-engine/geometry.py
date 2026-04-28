from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from common import ExactCylinder


def load_model(input_path: str) -> dict[str, Any]:
    suffix = Path(input_path).suffix.lower()
    if suffix == ".stl":
        mesh = trimesh.load_mesh(input_path, force="mesh")
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
        return {"mesh": ensure_mesh(mesh), "cylinders": [], "format": "stl"}

    raise ValueError("Only STL files are currently supported")


def ensure_mesh(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Failed to create a valid mesh")

    if hasattr(mesh, "unique_faces"):
        unique = mesh.unique_faces()
        if unique is not None:
            mesh.update_faces(unique)

    if hasattr(mesh, "nondegenerate_faces"):
        nondegenerate = mesh.nondegenerate_faces()
        if nondegenerate is not None:
            mesh.update_faces(nondegenerate)

    if hasattr(mesh, "remove_unreferenced_vertices"):
        mesh.remove_unreferenced_vertices()

    if hasattr(mesh, "process"):
        mesh.process(validate=True)

    if mesh.vertices.size == 0 or mesh.faces.size == 0:
        raise ValueError("The CAD model could not be tessellated into a valid mesh")
    return mesh



def export_preview_stl(mesh: trimesh.Trimesh, output_path: str) -> None:
    mesh.export(output_path)
