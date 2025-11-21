import argparse
import logging
from pathlib import Path

import config
import processor


def _add_common_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("path", nargs="?", help="Pasta ou arquivo")
    p.add_argument("--quality", type=int, default=None)
    p.add_argument("--webp", action="store_true")
    p.add_argument("--max-width", type=int, default=None)
    p.add_argument("--max-height", type=int, default=None)
    p.add_argument("--keep-exif", action="store_true")
    p.add_argument("--strip-exif", action="store_true")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--workers", type=int, default=None)
    p.add_argument("--output", type=str, default=None)
    p.add_argument("--config", type=str, default=None)
    p.add_argument("--confirm", action="store_true")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", filename="photo-slimmer.log")
    ap = argparse.ArgumentParser(prog="photo-slimmer", description="Otimizador de imagens em lote")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_process = sub.add_parser("process", help="Processar pasta")
    _add_common_options(p_process)
    p_preview = sub.add_parser("preview", help="Estimar antes/depois")
    _add_common_options(p_preview)
    args = ap.parse_args()

    base_cfg = config.load_config(Path(args.config) if args.config else None)
    override = {
        "quality": args.quality,
        "webp": True if args.webp else None,
        "max_width": args.max_width,
        "max_height": args.max_height,
        "keep_exif": True if args.keep_exif else (False if args.strip_exif else None),
        "workers": args.workers,
    }
    cfg = config.override_config(base_cfg, override)

    if args.cmd == "process":
        if not args.path:
            raise SystemExit("Informe a pasta a processar")
        report = processor.process_directory(
            Path(args.path),
            cfg,
            bool(args.recursive),
            bool(args.dry_run),
            int(cfg.get("workers")),
            bool(args.confirm),
            Path(args.output) if args.output else None,
        )
        print("Resumo:")
        print(report["summary"])
    elif args.cmd == "preview":
        if not args.path:
            raise SystemExit("Informe o arquivo para preview")
        res = processor.preview_file(Path(args.path), cfg)
        print(res)


if __name__ == "__main__":
    main()