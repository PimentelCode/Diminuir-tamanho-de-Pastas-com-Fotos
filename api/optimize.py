import io
import json
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


@app.post("/api/optimize")
def handler():
    cfg = config.load_config(None)
    cfg["workers"] = 1
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
        report = processor.process_directory(tmp_dir, cfg, True, False, 1, False, None)
        bio = io.BytesIO(json.dumps(report, ensure_ascii=False).encode("utf-8"))
        bio.seek(0)
        return send_file(bio, mimetype="application/json", download_name="report.json")