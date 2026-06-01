#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch dry-run/preprocess wrapper.

At this stage it copies base images and writes quality/progress/failure logs.
DWPose/SCHP/DensePose are not included here; connect them later after pair
mapping is verified.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import time
from pathlib import Path
from typing import Any

from PIL import Image
from tqdm import tqdm


def read_pairs(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv_append(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def split_name(s: str) -> str:
    if s == "val":
        return "test"
    if s in ("train", "test"):
        return s
    return "train"


def ensure_dirs(root: Path, split: str) -> dict[str, Path]:
    names = [
        "image", "cloth", "worn", "cloth-mask", "image-parse", "openpose-json",
        "image-densepose", "agnostic-v3.2", "agnostic-mask", "quality", "fit"
    ]
    out = {}
    for n in names:
        p = root / split / n
        p.mkdir(parents=True, exist_ok=True)
        out[n] = p
    return out


def copy_if_exists(src: str, dst: Path) -> bool:
    if not src:
        return False
    p = Path(src)
    if not p.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dst)
    return True


def get_image_size(path: Path):
    try:
        with Image.open(path) as im:
            return list(im.size)
    except Exception:
        return None


def outputs_exist(root: Path, split: str, pair_id: str) -> bool:
    return (root / split / "image" / f"{pair_id}.jpg").exists() and (root / split / "quality" / f"{pair_id}.json").exists()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int, default=None)
    parser.add_argument("--category", default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--save-failures", action="store_true")
    parser.add_argument("--save-quality-json", action="store_true")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    pairs = read_pairs(Path(args.pairs))
    if args.category:
        cats = {x.strip().lower() for x in args.category.split(",") if x.strip()}
        pairs = [p for p in pairs if p.get("category", "").lower() in cats]
    pairs = pairs[args.start_index:args.end_index]
    if args.limit:
        pairs = pairs[:args.limit]

    out_root = Path(args.output)
    out_root.mkdir(parents=True, exist_ok=True)

    progress_path = out_root / "preprocess_progress.csv"
    failures_path = out_root / "failures.csv"
    progress_fields = ["pair_id", "split", "status", "elapsed_sec", "num_errors"]
    failure_fields = ["pair_id", "stage", "error_code", "message", "person_path", "cloth_path", "worn_path"]

    stats = {
        "num_requested": len(pairs),
        "num_success": 0,
        "num_failed": 0,
        "num_skipped": 0,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "device": args.device,
    }
    all_start = time.time()

    for pair in tqdm(pairs, desc="preprocess"):
        t0 = time.time()
        pair_id = pair["pair_id"]
        split = split_name(pair.get("split", "train"))
        dirs = ensure_dirs(out_root, split)

        if args.resume and outputs_exist(out_root, split, pair_id):
            stats["num_skipped"] += 1
            write_csv_append(progress_path, {"pair_id": pair_id, "split": split, "status": "skipped", "elapsed_sec": 0, "num_errors": 0}, progress_fields)
            continue

        errors = []
        ok_person = copy_if_exists(pair.get("person_image", ""), dirs["image"] / f"{pair_id}.jpg")
        ok_cloth = copy_if_exists(pair.get("cloth_image", ""), dirs["cloth"] / f"{pair_id}.jpg")
        ok_worn = copy_if_exists(pair.get("worn_image", ""), dirs["worn"] / f"{pair_id}.jpg")

        if not ok_person:
            errors.append(("copy", "MISSING_PERSON_IMAGE", pair.get("person_image", "")))
        if not ok_cloth:
            errors.append(("copy", "MISSING_CLOTH_IMAGE", pair.get("cloth_image", "")))
        if pair.get("worn_image") and not ok_worn:
            errors.append(("copy", "MISSING_WORN_IMAGE", pair.get("worn_image", "")))

        # External artifacts expected later.
        errors.extend([
            ("dwpose", "DWPOSE_NOT_AVAILABLE", "external model not connected yet"),
            ("schp", "SCHP_NOT_AVAILABLE", "external model not connected yet"),
            ("densepose", "DENSEPOSE_NOT_AVAILABLE", "external model not connected yet"),
        ])

        q = {
            "pair_id": pair_id,
            "split": split,
            "person_image": str(dirs["image"] / f"{pair_id}.jpg") if ok_person else "",
            "cloth_image": str(dirs["cloth"] / f"{pair_id}.jpg") if ok_cloth else "",
            "worn_image": str(dirs["worn"] / f"{pair_id}.jpg") if ok_worn else "",
            "person_size": get_image_size(dirs["image"] / f"{pair_id}.jpg") if ok_person else None,
            "cloth_size": get_image_size(dirs["cloth"] / f"{pair_id}.jpg") if ok_cloth else None,
            "annotation_json": pair.get("annotation_json", ""),
            "model_id": pair.get("model_id", ""),
            "cloth_id": pair.get("cloth_id", ""),
            "pose": pair.get("pose", ""),
            "angle": pair.get("angle", ""),
            "category": pair.get("category", ""),
        }
        (dirs["quality"] / f"{pair_id}.json").write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")

        if ok_person:
            stats["num_success"] += 1
            status = "success_with_warnings" if errors else "success"
        else:
            stats["num_failed"] += 1
            status = "failed"

        if args.save_failures:
            for stage, code, msg in errors:
                write_csv_append(failures_path, {
                    "pair_id": pair_id,
                    "stage": stage,
                    "error_code": code,
                    "message": msg,
                    "person_path": pair.get("person_image", ""),
                    "cloth_path": pair.get("cloth_image", ""),
                    "worn_path": pair.get("worn_image", ""),
                }, failure_fields)

        write_csv_append(progress_path, {
            "pair_id": pair_id,
            "split": split,
            "status": status,
            "elapsed_sec": round(time.time() - t0, 3),
            "num_errors": len(errors),
        }, progress_fields)

    stats["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    stats["elapsed_sec"] = round(time.time() - all_start, 3)
    stats["success_rate"] = round(stats["num_success"] / max(1, len(pairs)), 4)
    stats_path = out_root / "preprocessing_stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
