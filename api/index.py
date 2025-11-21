import io
import json
import os
import sys
import tempfile
from pathlib import Path

from flask import Flask, request, send_file

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

import config  # noqa: E402
import processor  # noqa: E402


app = Flask(__name__)


@app.post("/api/preview")
def api_preview():
    base_cfg = config.load_config(None)
    base_cfg["workers"] = 1
    f = request.files.get("file")
    if not f:
        return {"error": "file_required"}, 400
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td) / f.filename
        f.save(tmp_path)
        res = processor.preview_file(tmp_path, base_cfg)
        return res


@app.post("/api/optimize")
def api_optimize():
    base_cfg = config.load_config(None)
    base_cfg["workers"] = 1
    files = request.files.getlist("files")
    if not files:
        return {"error": "files_required"}, 400
    with tempfile.TemporaryDirectory() as td:
        tmp_dir = Path(td) / "input"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            dest = tmp_dir / f.filename
            dest.parent.mkdir(parents=True, exist_ok=True)
            f.save(dest)
        report = processor.process_directory(tmp_dir, base_cfg, True, False, 1, False, None)
        bio = io.BytesIO()
        bio.write(json.dumps(report, ensure_ascii=False).encode("utf-8"))
        bio.seek(0)
        return send_file(bio, mimetype="application/json", download_name="report.json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)