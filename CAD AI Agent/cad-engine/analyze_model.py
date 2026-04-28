from __future__ import annotations

import argparse
import json

from analysis import analyze_mesh
from common import mesh_metadata
from geometry import load_model
from reporting import write_reports


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--report-dir", required=True)
    parser.add_argument("--file-id", required=True)
    parser.add_argument("--original-name", required=True)
    args = parser.parse_args()

    loaded = load_model(args.input)
    mesh = loaded["mesh"]
    analysis = analyze_mesh(mesh, loaded["cylinders"])
    write_reports(args.report_dir, args.file_id, args.original_name, mesh_metadata(mesh), analysis)
    print(json.dumps(analysis))


if __name__ == "__main__":
    main()
