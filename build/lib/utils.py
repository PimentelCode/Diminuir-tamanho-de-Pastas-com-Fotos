import io
import os
from pathlib import Path
from typing import Dict, Tuple, Optional

from PIL import Image


SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif", ".avif"}


def _try_register_heif() -> bool:
    try:
        from pillow_heif import register_heif_opener  # type: ignore
        register_heif_opener()
        return True
    except Exception:
        return False


HEIF_AVAILABLE = _try_register_heif()


def detect_format(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        return "JPEG"
    if ext == ".png":
        return "PNG"
    if ext == ".gif":
        return "GIF"
    if ext == ".webp":
        return "WEBP"
    if ext in {".heic", ".heif", ".avif"}:
        return "HEIF"
    try:
        with Image.open(path) as im:
            return im.format or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def is_supported(path: Path) -> bool:
    ext = path.suffix.lower()
    return ext in SUPPORTED_EXTS


def _resize_in_place(img: Image.Image, max_w: Optional[int], max_h: Optional[int]) -> None:
    if max_w and max_h:
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    elif max_w:
        img.thumbnail((max_w, img.height), Image.Resampling.LANCZOS)
    elif max_h:
        img.thumbnail((img.width, max_h), Image.Resampling.LANCZOS)


def _prepare_save_params(fmt: str, cfg: Dict, exif_bytes: Optional[bytes]) -> Dict:
    params: Dict = {}
    quality = int(cfg.get("quality", 85))
    keep_exif = bool(cfg.get("keep_exif", False))
    if fmt == "JPEG":
        params.update({"format": "JPEG", "quality": quality, "optimize": True, "progressive": True, "subsampling": "4:2:0"})
        if keep_exif and exif_bytes:
            params["exif"] = exif_bytes
    elif fmt == "PNG":
        params.update({"format": "PNG", "optimize": True, "compress_level": 9})
    elif fmt == "WEBP":
        params.update({"format": "WEBP", "quality": quality, "method": 6})
        if keep_exif and exif_bytes:
            params["exif"] = exif_bytes
    else:
        params["format"] = fmt
    return params


def _first_frame(img: Image.Image) -> Image.Image:
    try:
        img.seek(0)
    except Exception:
        pass
    return img.convert("RGB")


def estimate_new_size(path: Path, cfg: Dict) -> Tuple[int, int, Dict]:
    fmt = detect_format(path)
    original_size = path.stat().st_size if path.exists() else 0
    actions = {"resized": False, "converted": False, "target_format": fmt}
    if fmt == "HEIF" and not HEIF_AVAILABLE:
        return original_size, original_size, {"status": "unsupported", "reason": "heif_not_available", "actions": actions}
    try:
        with Image.open(path) as im:
            if fmt == "GIF":
                im = _first_frame(im)
            max_w = cfg.get("max_width")
            max_h = cfg.get("max_height")
            if max_w or max_h:
                _resize_in_place(im, max_w, max_h)
                actions["resized"] = True
            to_webp = bool(cfg.get("webp", True))
            target_fmt = "WEBP" if to_webp else fmt
            actions["converted"] = target_fmt != fmt
            actions["target_format"] = target_fmt
            exif_bytes = im.info.get("exif") if cfg.get("keep_exif", False) else None
            params = _prepare_save_params(target_fmt, cfg, exif_bytes)
            bio = io.BytesIO()
            im.save(bio, **params)
            new_size = bio.tell()
            return original_size, new_size, {"status": "ok", "actions": actions}
    except Exception as e:
        return original_size, original_size, {"status": "error", "error": str(e), "actions": actions}


def save_optimized(path: Path, dest: Path, cfg: Dict) -> Tuple[int, int, Dict]:
    fmt = detect_format(path)
    original_size = path.stat().st_size
    actions = {"resized": False, "converted": False, "target_format": fmt}
    if fmt == "HEIF" and not HEIF_AVAILABLE:
        return original_size, original_size, {"status": "unsupported", "reason": "heif_not_available", "actions": actions}
    try:
        with Image.open(path) as im:
            if fmt == "GIF":
                im = _first_frame(im)
            max_w = cfg.get("max_width")
            max_h = cfg.get("max_height")
            if max_w or max_h:
                _resize_in_place(im, max_w, max_h)
                actions["resized"] = True
            to_webp = bool(cfg.get("webp", True))
            target_fmt = "WEBP" if to_webp else fmt
            actions["converted"] = target_fmt != fmt
            actions["target_format"] = target_fmt
            exif_bytes = im.info.get("exif") if cfg.get("keep_exif", False) else None
            params = _prepare_save_params(target_fmt, cfg, exif_bytes)
            dest.parent.mkdir(parents=True, exist_ok=True)
            im.save(dest, **params)
            new_size = dest.stat().st_size
            st = os.stat(path)
            os.utime(dest, (st.st_atime, st.st_mtime))
            return original_size, new_size, {"status": "optimized", "actions": actions}
    except Exception as e:
        return original_size, original_size, {"status": "error", "error": str(e), "actions": actions}