from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def write_reports(report_dir: str, file_id: str, original_name: str, metadata: dict[str, Any], analysis: dict[str, Any]) -> None:
    report_dir_path = Path(report_dir)
    report_dir_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "fileId": file_id,
        "originalName": original_name,
        "metadata": metadata,
        "analysis": analysis,
    }
    (report_dir_path / f"{file_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (report_dir_path / f"{file_id}.html").write_text(render_html(payload), encoding="utf-8")


def render_html(payload: dict[str, Any]) -> str:
    metadata = payload["metadata"]
    analysis = payload["analysis"]
    rows = []
    for issue in analysis["issues"]:
        rows.append(
            f"""
            <tr>
              <td>{html.escape(issue['severity'].upper())}</td>
              <td>{html.escape(issue['title'])}</td>
              <td>{html.escape(issue['description'])}</td>
              <td>{html.escape(issue['suggestedFix'])}</td>
              <td>{issue['confidence']:.2f}</td>
            </tr>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CAD Validation Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; background: #0f172a; color: #e2e8f0; }}
    .card {{ background: #111c33; border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 20px; margin-bottom: 20px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); vertical-align: top; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
  </style>
</head>
<body>
  <h1>CAD Validation Report</h1>
  <div class="card">
    <h2>File</h2>
    <p>{html.escape(payload['originalName'])}</p>
    <p>Generated: {html.escape(analysis['generatedAt'])}</p>
  </div>
  <div class="card">
    <h2>Summary</h2>
    <div class="metrics">
      <div>Critical: {analysis['summary']['critical']}</div>
      <div>Warnings: {analysis['summary']['warning']}</div>
      <div>Info: {analysis['summary']['info']}</div>
      <div>Score: {analysis['summary']['manufacturabilityScore']}</div>
    </div>
  </div>
  <div class="card">
    <h2>Geometry Metadata</h2>
    <p>Extents: {' x '.join(f"{value:.2f}" for value in metadata['extentsMm'])} mm</p>
    <p>Faces: {metadata['faceCount']}</p>
    <p>Area: {metadata['areaMm2']}</p>
    <p>Volume: {metadata['volumeMm3']}</p>
  </div>
  <div class="card">
    <h2>Issues</h2>
    <table>
      <thead>
        <tr>
          <th>Severity</th>
          <th>Issue</th>
          <th>Description</th>
          <th>Suggested Fix</th>
          <th>Confidence</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
