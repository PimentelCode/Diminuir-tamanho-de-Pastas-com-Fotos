import sys
import tempfile
from pathlib import Path

from flask import Flask, request

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

import config  # noqa: E402
import processor  # noqa: E402

app = Flask(__name__)


@app.post("/api/preview")
def handler():
    cfg = config.load_config(None)
    cfg["workers"] = 1
    f = request.files.get("file")
    if not f:
        return {"error": "file_required"}, 400
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / f.filename
        f.save(p)
        res = processor.preview_file(p, cfg)
        return res