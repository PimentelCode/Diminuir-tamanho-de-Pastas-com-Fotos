import io
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Dict

from flask import Flask, request, send_file, send_from_directory, jsonify

import config
import processor


APP_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = APP_DIR / "web"
if not WEB_DIR.exists():
    WEB_DIR = Path.cwd() / "web"

app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(str(WEB_DIR), "index.html")


@app.get("/web/<path:path>")
def static_files(path: str):
    return send_from_directory(str(WEB_DIR), path)


def _cfg_from_request(base_cfg: Dict) -> Dict:
    data = request.form or request.json or {}
    override = {
        "quality": int(data.get("quality")) if data.get("quality") else None,
        "webp": True if str(data.get("webp", "true")).lower() in {"true", "1", "on"} else False,
        "max_width": int(data.get("max_width")) if data.get("max_width") else None,
        "max_height": int(data.get("max_height")) if data.get("max_height") else None,
        "keep_exif": True if str(data.get("keep_exif", "false")).lower() in {"true", "1", "on"} else False,
        "workers": int(data.get("workers")) if data.get("workers") else None,
    }
    return config.override_config(base_cfg, override)


@app.post("/api/preview")
def api_preview():
    base_cfg = config.load_config(None)
    cfg = _cfg_from_request(base_cfg)
    f = request.files.get("file")
    if not f:
        return {"error": "file_required"}, 400
    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td) / f.filename
        f.save(tmp_path)
        res = processor.preview_file(tmp_path, cfg)
        return res


@app.post("/api/optimize")
def api_optimize():
    base_cfg = config.load_config(None)
    cfg = _cfg_from_request(base_cfg)
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
        report = processor.process_directory(tmp_dir, cfg, True, False, int(cfg.get("workers")), False, None)
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in report["results"]:
                if r.get("status") == "optimized":
                    p = Path(r["path"])
                    rel = p.relative_to(tmp_dir)
                    out_root = tmp_dir / "optimized"
                    optimized_path = out_root / rel
                    optimized_path = optimized_path.with_suffix(Path(r["path"]).suffix if not cfg.get("webp", True) else ".webp")
                    if optimized_path.exists():
                        zf.write(optimized_path, arcname=str(rel.with_suffix(optimized_path.suffix)))
            zf.writestr("report.json", json.dumps(report, ensure_ascii=False, indent=2))
        bio.seek(0)
        return send_file(bio, mimetype="application/zip", download_name="optimized.zip", as_attachment=True)


@app.errorhandler(404)
def handle_404(_):
    p = request.path or ""
    if p.startswith("/api/"):
        return jsonify({"error": "not_found", "path": p}), 404
    try:
        return send_from_directory(str(WEB_DIR), "index.html"), 200
    except Exception:
        return "Not Found", 404


def run():
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()