import io
import os
from pathlib import Path

import tempfile
import json

from PIL import Image
import sys
import pathlib

# ensure src path in sys.path
SRC_PATH = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_PATH))


def _make_image(path: Path, mode: str = "RGB", size=(320, 240), color=(128, 128, 128), fmt="JPEG") -> None:
    img = Image.new(mode, size, color)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format=fmt)


def test_preview_and_dry_run():
    from pathlib import Path
    import processor
    import config

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "a.jpg"
        _make_image(p, fmt="JPEG")
        cfg = config.load_config(None)
        res = processor.preview_file(p, cfg)
        assert res["original_size"] > 0
        assert res["estimated_new_size"] > 0
        report = processor.process_directory(Path(td), cfg, False, True, max(1, cfg["workers"]), False, None)
        assert report["summary"]["total_files"] == 1
        assert report["summary"]["dry_run"] is True


def test_process_and_report_json(tmp_path: Path):
    import processor
    import config
    d = tmp_path / "photos"
    d.mkdir()
    _make_image(d / "a.jpg", fmt="JPEG")
    _make_image(d / "b.png", fmt="PNG")
    cfg = config.load_config(None)
    out_report = tmp_path / "report.json"
    rep = processor.process_directory(d, cfg, True, False, max(1, cfg["workers"]), False, out_report)
    assert rep["summary"]["total_files"] >= 2
    assert out_report.exists()
    data = json.loads(out_report.read_text("utf-8"))
    assert "summary" in data and "results" in data


def test_unsupported_heic():
    import processor
    import config
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "photo.heic"
        p.write_bytes(os.urandom(1024))
        cfg = config.load_config(None)
        rep = processor.process_directory(Path(td), cfg, False, True, max(1, cfg["workers"]), False, None)
        statuses = {r["status"] for r in rep["results"]}
        assert "unsupported" in statuses or "error" in statuses