from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import math
from typing import Any

import numpy as np
import trimesh

from common import ExactCylinder, to_float_list

THICKNESS_THRESHOLD = 1.5
MIN_HOLE_DIAMETER = 0.5
MIN_FEATURE_SIZE = 0.8
SHARP_ANGLE_THRESHOLD = 0.82


def analyze_mesh(mesh: trimesh.Trimesh, cylinders: list[ExactCylinder]) -> dict[str, Any]:
    issues = []
    issues.extend(check_wall_thickness(mesh))
    issues.extend(check_hole_diameter(mesh, cylinders))
    issues.extend(check_sharp_edges(mesh))
    issues.extend(check_min_feature_size(mesh))

    ai_insights = infer_risk_zones(mesh, issues)
    issues.extend(ai_insights_to_issues(ai_insights))

    counts = Counter(issue["severity"] for issue in issues)
    score_penalty = counts["critical"] * 18 + counts["warning"] * 9 + counts["info"] * 3

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "critical": counts["critical"],
            "warning": counts["warning"],
            "info": counts["info"],
            "manufacturabilityScore": max(1, 100 - score_penalty),
        },
        "issues": issues,
        "aiInsights": ai_insights,
    }


def check_wall_thickness(mesh: trimesh.Trimesh) -> list[dict[str, Any]]:
    samples, face_indices = trimesh.sample.sample_surface_even(mesh, 220)
    if len(samples) == 0:
        return []

    normals = mesh.face_normals[face_indices]
    origins = samples - normals * 0.15
    locations, ray_ids, _ = mesh.ray.intersects_location(origins, normals, multiple_hits=True)

    per_ray: dict[int, list[float]] = {}
    for location, ray_id in zip(locations, ray_ids):
        distance = float(np.linalg.norm(location - origins[ray_id]))
        if distance > 0.2:
            per_ray.setdefault(int(ray_id), []).append(distance)

    issues = []
    for ray_id, distances in per_ray.items():
        nearest = min(distances)
        if nearest < THICKNESS_THRESHOLD:
            issues.append(
                build_issue(
                    issue_id=f"thin-{ray_id}",
                    issue_type="wall_thickness",
                    severity="critical",
                    title="Thin wall region",
                    description=f"Local wall thickness is {nearest:.2f} mm, below the 1.50 mm limit.",
                    suggested_fix="Increase wall thickness to at least 1.5 mm in this region.",
                    confidence=0.92,
                    point=samples[ray_id],
                    radius=max(nearest * 1.5, 1.2),
                    measurement=nearest,
                    threshold=THICKNESS_THRESHOLD,
                )
            )

    return dedupe_spatial_issues(issues, 3.0)


def check_hole_diameter(mesh: trimesh.Trimesh, cylinders: list[ExactCylinder]) -> list[dict[str, Any]]:
    issues = []

    if cylinders:
        for idx, cylinder in enumerate(cylinders):
            if cylinder.diameter < MIN_HOLE_DIAMETER:
                issues.append(
                    build_issue(
                        issue_id=f"hole-step-{idx}",
                        issue_type="hole_diameter",
                        severity="warning",
                        title="Undersized cylindrical hole",
                        description=f"Cylindrical feature diameter is {cylinder.diameter:.2f} mm, below the 0.50 mm minimum.",
                        suggested_fix="Increase hole diameter to at least 0.5 mm or relax the manufacturing method.",
                        confidence=0.95,
                        point=np.array(cylinder.center),
                        radius=max(cylinder.diameter * 1.8, 1.0),
                        measurement=cylinder.diameter,
                        threshold=MIN_HOLE_DIAMETER,
                        normal=np.array(cylinder.axis),
                    )
                )
        return dedupe_spatial_issues(issues, 2.0)

    defects = mesh.vertex_defects
    candidate_vertices = mesh.vertices[defects < -0.15] if len(defects) else np.empty((0, 3))
    if len(candidate_vertices) == 0:
        return []

    point_cloud = trimesh.points.PointCloud(candidate_vertices)
    tree = point_cloud.kdtree
    visited = set()

    for idx, point in enumerate(candidate_vertices):
        if idx in visited:
            continue
        cluster = tree.query_ball_point(point, r=1.0)
        visited.update(cluster)
        cluster_points = candidate_vertices[cluster]
        if len(cluster_points) < 8:
            continue
        centroid = cluster_points.mean(axis=0)
        radial = np.linalg.norm(cluster_points - centroid, axis=1)
        est_diameter = float(np.percentile(radial, 70) * 2.0)
        if est_diameter < MIN_HOLE_DIAMETER:
            issues.append(
                build_issue(
                    issue_id=f"hole-mesh-{idx}",
                    issue_type="hole_diameter",
                    severity="warning",
                    title="Small recessed opening",
                    description=f"An inward circular feature is estimated at {est_diameter:.2f} mm diameter, below the 0.50 mm minimum.",
                    suggested_fix="Increase the hole or pocket opening above 0.5 mm for easier manufacturing.",
                    confidence=0.63,
                    point=centroid,
                    radius=max(est_diameter * 2.0, 1.0),
                    measurement=est_diameter,
                    threshold=MIN_HOLE_DIAMETER,
                )
            )

    return dedupe_spatial_issues(issues, 2.0)


def check_sharp_edges(mesh: trimesh.Trimesh) -> list[dict[str, Any]]:
    if len(mesh.face_adjacency_edges) == 0:
        return []

    issues = []
    angles = mesh.face_adjacency_angles
    sharp_indices = np.where(angles > SHARP_ANGLE_THRESHOLD)[0]
    for idx in sharp_indices[:60]:
        edge = mesh.face_adjacency_edges[idx]
        points = mesh.vertices[edge]
        issues.append(
            build_issue(
                issue_id=f"sharp-{idx}",
                issue_type="sharp_edge",
                severity="warning",
                title="Sharp edge with elevated stress risk",
                description=f"Detected a dihedral angle of {math.degrees(angles[idx]):.1f} degrees that may create stress concentration.",
                suggested_fix="Add a fillet or chamfer to reduce stress concentration at the edge.",
                confidence=0.84,
                point=points.mean(axis=0),
                radius=max(float(np.linalg.norm(points[0] - points[1])) * 1.4, 1.0),
                measurement=float(math.degrees(angles[idx])),
                threshold=float(math.degrees(SHARP_ANGLE_THRESHOLD)),
            )
        )

    return dedupe_spatial_issues(issues, 4.0)


def check_min_feature_size(mesh: trimesh.Trimesh) -> list[dict[str, Any]]:
    issues = []
    small_edge_indices = np.where(mesh.edges_unique_length < MIN_FEATURE_SIZE)[0]
    for idx in small_edge_indices[:50]:
        edge = mesh.edges_unique[idx]
        points = mesh.vertices[edge]
        size = float(mesh.edges_unique_length[idx])
        issues.append(
            build_issue(
                issue_id=f"feature-{idx}",
                issue_type="minimum_feature_size",
                severity="info",
                title="Small local feature",
                description=f"Detected an edge-scale feature of {size:.2f} mm, below the recommended 0.80 mm minimum.",
                suggested_fix="Thicken or simplify the feature so the minimum local size is at least 0.8 mm.",
                confidence=0.78,
                point=points.mean(axis=0),
                radius=max(size * 2.5, 0.9),
                measurement=size,
                threshold=MIN_FEATURE_SIZE,
            )
        )

    return dedupe_spatial_issues(issues, 2.5)


def infer_risk_zones(mesh: trimesh.Trimesh, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    samples, face_indices = trimesh.sample.sample_surface(mesh, 120)
    if len(samples) == 0:
        return []

    normals = mesh.face_normals[face_indices]
    vertex_normals = mesh.vertex_normals[mesh.faces[face_indices]].mean(axis=1)
    angular_change = np.clip(1.0 - np.einsum("ij,ij->i", normals, vertex_normals), 0.0, 1.0)

    issue_points = np.array([issue["location"]["point"] for issue in issues], dtype=float) if issues else np.empty((0, 3))
    insights = []
    for idx, point in enumerate(samples[:30]):
        density = 0.0
        if len(issue_points):
            distances = np.linalg.norm(issue_points - point, axis=1)
            density = float(np.sum(distances < 8.0)) / max(len(issue_points), 1)
        complexity = float(angular_change[idx])
        risk_score = min(0.98, 0.28 + complexity * 0.45 + density * 0.65)
        if risk_score > 0.74:
            insights.append(
                {
                    "zone": f"Risk zone {len(insights) + 1}",
                    "confidence": round(risk_score, 3),
                    "risk": classify_risk(complexity, density),
                    "point": to_float_list(point),
                }
            )

    return insights[:8]


def ai_insights_to_issues(ai_insights: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        build_issue(
            issue_id=f"ai-{idx}",
            issue_type="manufacturing_risk_zone",
            severity="info",
            title="AI manufacturability risk zone",
            description=f"{insight['risk']} identified from local geometry complexity and issue clustering.",
            suggested_fix="Review this area for simplification, smoother transitions, or thicker supporting geometry.",
            confidence=float(insight["confidence"]),
            point=np.array(insight["point"]),
            radius=3.2,
        )
        for idx, insight in enumerate(ai_insights)
    ]


def classify_risk(complexity: float, density: float) -> str:
    if density > 0.25 and complexity > 0.3:
        return "Stacked manufacturability risks"
    if complexity > 0.45:
        return "Complex geometry concentration"
    return "Potentially delicate feature cluster"


def build_issue(
    issue_id: str,
    issue_type: str,
    severity: str,
    title: str,
    description: str,
    suggested_fix: str,
    confidence: float,
    point: np.ndarray,
    radius: float,
    measurement: float | None = None,
    threshold: float | None = None,
    normal: np.ndarray | None = None,
) -> dict[str, Any]:
    location = {"point": to_float_list(point), "radius": float(radius)}
    if normal is not None:
        location["normal"] = to_float_list(normal)

    payload = {
        "id": issue_id,
        "type": issue_type,
        "severity": severity,
        "title": title,
        "description": description,
        "suggestedFix": suggested_fix,
        "confidence": float(confidence),
        "location": location,
    }
    if measurement is not None:
        payload["measurement"] = float(measurement)
    if threshold is not None:
        payload["threshold"] = float(threshold)
    return payload


def dedupe_spatial_issues(issues: list[dict[str, Any]], radius: float) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    for issue in issues:
        point = np.array(issue["location"]["point"], dtype=float)
        if any(
            issue["type"] == existing["type"]
            and np.linalg.norm(point - np.array(existing["location"]["point"], dtype=float)) < radius
            for existing in deduped
        ):
            continue
        deduped.append(issue)
    return deduped
