import multiprocessing
from pathlib import Path
from typing import Dict

import yaml


DEFAULTS = {
    "quality": 85,
    "webp": True,
    "max_width": 1920,
    "max_height": 1080,
    "keep_exif": False,
    "workers": max(1, multiprocessing.cpu_count() - 1),
}


def load_config(config_path: Path | None) -> Dict:
    cfg = DEFAULTS.copy()
    if config_path and config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if isinstance(data, dict):
                cfg.update(data)
    return cfg


def override_config(cfg: Dict, overrides: Dict) -> Dict:
    merged = cfg.copy()
    for k, v in overrides.items():
        if v is not None:
            merged[k] = v
    return merged