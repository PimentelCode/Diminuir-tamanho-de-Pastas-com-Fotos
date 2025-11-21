import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

from tqdm import tqdm

import utils


logger = logging.getLogger("photo_slimmer.processor")


def _compute_dest(path: Path, base_dir: Path, output_root: Path, target_ext: str) -> Path:
    rel = path.relative_to(base_dir)
    dest = output_root / rel
    dest = dest.with_suffix(target_ext)
    return dest


def _worker(path: Path, base_dir: Path, output_root: Path, cfg: Dict, dry_run: bool, in_place: bool) -> Dict:
    fmt = utils.detect_format(path)
    supported = utils.is_supported(path)
    record: Dict = {
        "path": str(path),
        "format": fmt,
        "status": "skipped",
        "original_size": path.stat().st_size if path.exists() else 0,
        "new_size": None,
        "bytes_saved": None,
        "percent_saved": None,
        "actions": {},
    }
    if not supported:
        record["status"] = "unsupported"
        return record
    if dry_run:
        orig, new, meta = utils.estimate_new_size(path, cfg)
        record.update({
            "status": meta.get("status", "ok"),
            "original_size": orig,
            "new_size": new,
            "bytes_saved": max(orig - new, 0),
            "percent_saved": round((max(orig - new, 0) / orig) * 100, 2) if orig > 0 else 0.0,
            "actions": meta.get("actions", {}),
        })
        return record
    target_fmt = "WEBP" if cfg.get("webp", True) else fmt
    target_ext = ".webp" if target_fmt == "WEBP" else path.suffix
    dest = path if in_place else _compute_dest(path, base_dir, output_root, target_ext)
    orig, new, meta = utils.save_optimized(path, dest, cfg)
    record.update({
        "status": meta.get("status", "optimized"),
        "original_size": orig,
        "new_size": new,
        "bytes_saved": max(orig - (new or 0), 0),
        "percent_saved": round((max(orig - (new or 0), 0) / orig) * 100, 2) if orig > 0 and new else 0.0,
        "actions": meta.get("actions", {}),
    })
    return record


def _iter_files(root: Path, recursive: bool) -> List[Path]:
    if recursive:
        return [p for p in root.rglob("*") if p.is_file()]
    return [p for p in root.glob("*") if p.is_file()]


def process_directory(
    dir_path: Path,
    cfg: Dict,
    recursive: bool,
    dry_run: bool,
    workers: int,
    confirm: bool,
    output_report: Path | None,
) -> Dict:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", filename="photo-slimmer.log")
    files = _iter_files(dir_path, recursive)
    output_root = dir_path / "optimized"
    in_place = bool(confirm)
    if not dry_run and not in_place:
        output_root.mkdir(parents=True, exist_ok=True)
    results: List[Dict] = []
    total_bytes_before = 0
    total_bytes_after = 0
    with ProcessPoolExecutor(max_workers=max(1, workers)) as ex:
        futures = [ex.submit(_worker, f, dir_path, output_root, cfg, dry_run, in_place) for f in files]
        for fut in tqdm(as_completed(futures), total=len(futures), desc="Processando"):
            rec = fut.result()
            results.append(rec)
            total_bytes_before += rec.get("original_size", 0) or 0
            if rec.get("new_size"):
                total_bytes_after += rec.get("new_size", 0) or 0
    summary = {
        "total_files": len(results),
        "optimized_files": sum(1 for r in results if r.get("status") == "optimized"),
        "unsupported_files": sum(1 for r in results if r.get("status") == "unsupported"),
        "error_files": sum(1 for r in results if r.get("status") == "error"),
        "bytes_before": total_bytes_before,
        "bytes_after": total_bytes_after,
        "bytes_saved": max(total_bytes_before - total_bytes_after, 0),
        "percent_saved": round((max(total_bytes_before - total_bytes_after, 0) / total_bytes_before) * 100, 2) if total_bytes_before > 0 else 0.0,
        "in_place": in_place,
        "dry_run": dry_run,
    }
    report = {"summary": summary, "results": results}
    if output_report:
        try:
            with open(output_report, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Failed writing report: %s", e)
    return report


def preview_file(file_path: Path, cfg: Dict) -> Dict:
    orig, new, meta = utils.estimate_new_size(file_path, cfg)
    return {
        "path": str(file_path),
        "original_size": orig,
        "estimated_new_size": new,
        "bytes_saved": max(orig - new, 0),
        "percent_saved": round((max(orig - new, 0) / orig) * 100, 2) if orig > 0 else 0.0,
        "status": meta.get("status"),
        "actions": meta.get("actions"),
    }