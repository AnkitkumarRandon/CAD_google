from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import mesh_metadata
from geometry import export_preview_stl, load_model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--preview-dir", required=True)
    parser.add_argument("--file-id", required=True)
    args = parser.parse_args()

    loaded = load_model(args.input)
    mesh = loaded["mesh"]
    preview_name = f"{args.file_id}.stl"
    export_preview_stl(mesh, str(Path(args.preview_dir) / preview_name))

    print(json.dumps({"previewFile": preview_name, "metadata": mesh_metadata(mesh)}))


if __name__ == "__main__":
    main()
