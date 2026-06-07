#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect AIHub raw dataset folder.

This version ignores duplicate/temporary folders such as:
- ddd
- _ignore_ddd
- __MACOSX

Usage:
python scripts\inspect_aihub_raw.py ^
  --input "backend\datasets\raw\aihub\011.쉐이프리스 의류 및 포즈 데이터\01-1.정식개방데이터" ^
  --output backend\datasets\processed\index\raw_structure_report_full.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
JSON_EXTS = {".json"}

EXCLUDE_DIR_NAMES = {
    "ddd",
    "_ignore_ddd",
    "__MACOSX",
}


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIR_NAMES for part in path.parts)


def iter_files(root: Path):
    for p in root.rglob("*"):
        if is_excluded(p):
            continue
        if p.is_file():
            yield p


def safe_read_json(path: Path) -> Any | None:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    return None


def get_size_bytes(root: Path) -> int:
    total = 0
    for p in iter_files(root):
        try:
            total += p.stat().st_size
        except OSError:
            pass
    return total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="AIHub raw root")
    parser.add_argument("--output", required=True, help="Output report json")
    parser.add_argument("--max-samples", type=int, default=20)
    args = parser.parse_args()

    root = Path(args.input)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    if not root.exists():
        raise FileNotFoundError(f"Input root does not exist: {root}")

    file_ext_counts = Counter()
    image_files: list[str] = []
    json_files: list[str] = []
    top_dirs = []

    for child in sorted(root.iterdir()):
        if is_excluded(child):
            continue
        if child.is_dir():
            top_dirs.append(str(child.relative_to(root)))

    for p in iter_files(root):
        ext = p.suffix.lower()
        file_ext_counts[ext] += 1
        if ext in IMAGE_EXTS and len(image_files) < args.max_samples:
            image_files.append(str(p.relative_to(root)))
        elif ext in JSON_EXTS and len(json_files) < args.max_samples:
            json_files.append(str(p.relative_to(root)))

    json_samples = []
    for rel in json_files[: min(5, len(json_files))]:
        p = root / rel
        obj = safe_read_json(p)
        if isinstance(obj, dict):
            json_samples.append(
                {
                    "path": rel,
                    "top_keys": list(obj.keys())[:30],
                    "preview": {k: str(v)[:300] for k, v in list(obj.items())[:5]},
                }
            )
        elif isinstance(obj, list):
            json_samples.append(
                {
                    "path": rel,
                    "type": "list",
                    "length": len(obj),
                    "first_item_type": type(obj[0]).__name__ if obj else None,
                    "first_item_keys": list(obj[0].keys())[:30] if obj and isinstance(obj[0], dict) else None,
                }
            )
        else:
            json_samples.append({"path": rel, "type": type(obj).__name__})

    dir_counts_by_depth = defaultdict(int)
    for p in root.rglob("*"):
        if is_excluded(p):
            continue
        if p.is_dir():
            depth = len(p.relative_to(root).parts)
            dir_counts_by_depth[str(depth)] += 1

    report = {
        "raw_root": str(root.resolve()),
        "ignored_dir_names": sorted(EXCLUDE_DIR_NAMES),
        "exists": root.exists(),
        "total_size_gb": round(get_size_bytes(root) / (1024**3), 3),
        "num_files": sum(file_ext_counts.values()),
        "num_images": sum(file_ext_counts[e] for e in IMAGE_EXTS),
        "num_json": file_ext_counts[".json"],
        "file_ext_counts": dict(file_ext_counts.most_common()),
        "top_level_dirs": top_dirs,
        "dir_counts_by_depth": dict(dir_counts_by_depth),
        "image_samples": image_files,
        "json_samples": json_samples,
    }

    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote report: {out}")
    print(json.dumps(
        {k: report[k] for k in ["num_images", "num_json", "total_size_gb", "top_level_dirs", "ignored_dir_names"]},
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
