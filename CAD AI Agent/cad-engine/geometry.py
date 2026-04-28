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

    if suffix in {".step", ".stp"}:
        shape = read_step_shape(input_path)
        mesh = shape_to_mesh(shape)
        return {"mesh": ensure_mesh(mesh), "cylinders": extract_cylinders(shape), "format": "step"}

    raise ValueError("Unsupported file format")


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


def read_step_shape(input_path: str):
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPControl import STEPControl_Reader

    reader = STEPControl_Reader()
    status = reader.ReadFile(str(input_path))
    if status != IFSelect_RetDone:
        raise ValueError("Unable to read STEP file")
    reader.TransferRoots()
    return reader.OneShape()


def shape_to_mesh(shape) -> trimesh.Trimesh:
    from OCP.BRep import BRep_Tool
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopLoc import TopLoc_Location

    BRepMesh_IncrementalMesh(shape, 0.5, False, 0.5, True)

    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    vertex_offset = 0
    explorer = TopExp_Explorer(shape, TopAbs_FACE)

    while explorer.More():
        face = face_from_shape(explorer.Current())
        loc = TopLoc_Location()
        triangulation = BRep_Tool.Triangulation(face, loc)
        if triangulation is not None:
            transform = loc.Transformation()
            node_count = triangulation.NbNodes()
            for index in range(1, node_count + 1):
                point = triangulation.Node(index).Transformed(transform)
                vertices.append([point.X(), point.Y(), point.Z()])

            triangle_count = triangulation.NbTriangles()
            for tri_index in range(1, triangle_count + 1):
                triangle = triangulation.Triangle(tri_index)
                i1, i2, i3 = triangle.Get()
                if face.Orientation() == TopAbs_REVERSED:
                    faces.append([vertex_offset + i1 - 1, vertex_offset + i3 - 1, vertex_offset + i2 - 1])
                else:
                    faces.append([vertex_offset + i1 - 1, vertex_offset + i2 - 1, vertex_offset + i3 - 1])

            vertex_offset += node_count
        explorer.Next()

    return trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces), process=True)


def extract_cylinders(shape) -> list[ExactCylinder]:
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepGProp import brepgprop_SurfaceProperties
    from OCP.GProp import GProp_GProps
    from OCP.GeomAbs import GeomAbs_Cylinder
    from OCP.TopAbs import TopAbs_FACE
    from OCP.TopExp import TopExp_Explorer

    cylinders: list[ExactCylinder] = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)

    while explorer.More():
        face = face_from_shape(explorer.Current())
        surface = BRepAdaptor_Surface(face)
        if surface.GetType() == GeomAbs_Cylinder:
            cylinder = surface.Cylinder()
            props = GProp_GProps()
            brepgprop_SurfaceProperties(face, props)
            axis = cylinder.Axis().Direction()
            location = cylinder.Location()
            cylinders.append(
                ExactCylinder(
                    center=[location.X(), location.Y(), location.Z()],
                    axis=[axis.X(), axis.Y(), axis.Z()],
                    diameter=float(cylinder.Radius() * 2.0),
                    face_area=float(props.Mass()),
                )
            )
        explorer.Next()

    return cylinders


def export_preview_stl(mesh: trimesh.Trimesh, output_path: str) -> None:
    mesh.export(output_path)


def face_from_shape(shape):
    try:
        from OCP.TopoDS import TopoDS

        return TopoDS.Face_s(shape)
    except Exception:
        from OCP.TopoDS import topods

        return topods.Face(shape)
