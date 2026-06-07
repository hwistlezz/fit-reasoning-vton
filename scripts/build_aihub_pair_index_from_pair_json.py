#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build AIHub VTON pair index from explicit Pair.json annotations.

Pair.json format:
- from   = product/cloth image path
- to     = model/person image path
- result = worn/result image path

This script:
1. scans raw-root images/jsons, ignoring ddd/_ignore_ddd/__MACOSX
2. reads Pair.json files under TL_페어 / VL_페어 or any JSON containing from/to/result
3. resolves from/to/result by basename against actual extracted files
4. attaches model_id/cloth_id/pose/angle/category from result/worn annotation JSON when possible
5. writes a new explicit pair CSV and report JSON

Recommended output names:
backend/datasets/processed/index/aihub_pairs_explicit_full.csv
backend/datasets/processed/index/aihub_pair_explicit_report.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
JSON_EXTS = {".json"}
EXCLUDE_DIR_NAMES = {"ddd", "_ignore_ddd", "__MACOSX"}


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIR_NAMES for part in path.parts)


def safe_load_json(path: Path) -> Any | None:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    return None


def norm_path_value(s: str) -> str:
    return str(s or "").replace("\\", "/")


def basename_key(s: str) -> str:
    return Path(norm_path_value(s)).name.lower()


def stem_key(s: str) -> str:
    return Path(norm_path_value(s)).stem.lower()


def infer_split_from_path(path: str | Path) -> str:
    text = str(path).lower()
    if "validation" in text or "\\validation" in text or "/validation" in text:
        return "val"
    if "training" in text or "\\training" in text or "/training" in text:
        return "train"
    return "unknown"


def infer_kind_image(path: Path) -> str:
    text = str(path).lower()
    if "제품 착용" in text or "제품착용" in text:
        return "worn"
    if "ts_제품" in text or "\\제품\\" in text or "/제품/" in text:
        return "cloth"
    if "ts_모델" in text or "\\모델\\" in text or "/모델/" in text:
        return "model"
    return "unknown"


def infer_category_from_text(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ("outer", "jacket", "coat", "jumper", "padding", "cardigan", "아우터", "자켓", "재킷", "코트", "점퍼", "패딩", "가디건")):
        return "outer"
    if any(w in t for w in ("top", "shirt", "upper", "blouse", "t-shirt", "sweater", "상의", "티셔츠", "셔츠", "블라우스", "스웨터", "니트")):
        return "top"
    if any(w in t for w in ("dress", "jumpsuit", "원피스", "점프수트")):
        return "dress"
    if any(w in t for w in ("pants", "skirt", "bottom", "하의", "바지", "스커트", "치마")):
        return "bottom"
    return "unknown"


def first_info(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict):
        return {}
    info = obj.get("info")
    if isinstance(info, list) and info and isinstance(info[0], dict):
        return info[0]
    if isinstance(info, dict):
        return info
    return {}


def collect_pair_dicts(obj: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if isinstance(obj, dict):
        if all(k in obj for k in ("from", "to", "result")):
            out.append(obj)
        for v in obj.values():
            out.extend(collect_pair_dicts(v))
    elif isinstance(obj, list):
        for x in obj:
            out.extend(collect_pair_dicts(x))
    return out


def build_image_index(images: list[Path]) -> dict[str, list[Path]]:
    idx: dict[str, list[Path]] = defaultdict(list)
    for p in images:
        idx[p.name.lower()].append(p)
        idx[p.stem.lower()].append(p)
    return idx


def resolve_image(ref: str, image_index: dict[str, list[Path]], preferred_kind: str | None = None) -> Path | None:
    if not ref:
        return None
    keys = [basename_key(ref), stem_key(ref)]
    candidates: list[Path] = []
    seen = set()
    for k in keys:
        for p in image_index.get(k, []):
            if p not in seen:
                candidates.append(p)
                seen.add(p)
    if not candidates:
        return None
    if preferred_kind:
        preferred = [p for p in candidates if infer_kind_image(p) == preferred_kind]
        if preferred:
            return preferred[0]
    return candidates[0]


def build_annotation_index(jsons: list[Path]) -> dict[str, list[Path]]:
    idx: dict[str, list[Path]] = defaultdict(list)
    for jp in jsons:
        obj = safe_load_json(jp)
        if not isinstance(obj, dict):
            continue
        info0 = first_info(obj)
        image = info0.get("image") if isinstance(info0.get("image"), dict) else {}
        img_path = str(image.get("path", ""))
        if img_path:
            idx[basename_key(img_path)].append(jp)
            idx[stem_key(img_path)].append(jp)
        idx[jp.stem.lower()].append(jp)
    return idx


def resolve_annotation_for_image(img: Path | None, ann_index: dict[str, list[Path]]) -> Path | None:
    if img is None:
        return None
    for k in (img.name.lower(), img.stem.lower()):
        hits = ann_index.get(k)
        if hits:
            return hits[0]
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--out-pairs", required=True)
    parser.add_argument("--save-report", required=True)
    parser.add_argument("--dedupe", action="store_true", help="deduplicate by from/to/result basename triple")
    parser.add_argument("--max-rows", type=int, default=None)
    args = parser.parse_args()

    root = Path(args.raw_root)
    out_pairs = Path(args.out_pairs)
    out_report = Path(args.save_report)
    out_pairs.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)

    images = sorted([
        p for p in root.rglob("*")
        if p.is_file() and not is_excluded(p) and p.suffix.lower() in IMAGE_EXTS
    ])
    jsons = sorted([
        p for p in root.rglob("*.json")
        if p.is_file() and not is_excluded(p)
    ])

    image_index = build_image_index(images)
    ann_index = build_annotation_index(jsons)

    pair_json_files = []
    pair_entries = []

    for jp in jsons:
        obj = safe_load_json(jp)
        pairs = collect_pair_dicts(obj)
        if not pairs:
            continue
        pair_json_files.append((jp, len(pairs)))
        for item in pairs:
            pair_entries.append((jp, item))

    if args.max_rows:
        pair_entries = pair_entries[:args.max_rows]

    seen_triples = set()
    rows = []
    unresolved_examples = []
    duplicate_count = 0

    for jp, item in pair_entries:
        from_ref = str(item.get("from", ""))
        to_ref = str(item.get("to", ""))
        result_ref = str(item.get("result", ""))

        triple = (basename_key(from_ref), basename_key(to_ref), basename_key(result_ref))
        if args.dedupe and triple in seen_triples:
            duplicate_count += 1
            continue
        seen_triples.add(triple)

        cloth_img = resolve_image(from_ref, image_index, preferred_kind="cloth")
        person_img = resolve_image(to_ref, image_index, preferred_kind="model")
        worn_img = resolve_image(result_ref, image_index, preferred_kind="worn")

        worn_ann = resolve_annotation_for_image(worn_img, ann_index)
        person_ann = resolve_annotation_for_image(person_img, ann_index)
        cloth_ann = resolve_annotation_for_image(cloth_img, ann_index)

        info0 = {}
        image_info = {}
        if worn_ann:
            obj = safe_load_json(worn_ann)
            info0 = first_info(obj)
            image_info = info0.get("image") if isinstance(info0.get("image"), dict) else {}

        split = infer_split_from_path(worn_img or person_img or cloth_img or jp)
        category = infer_category_from_text(" ".join([str(worn_img or ""), str(cloth_img or ""), str(image_info.get("path", "")), str(jp)]))

        status_errors = []
        if cloth_img is None:
            status_errors.append("missing_cloth")
        if person_img is None:
            status_errors.append("missing_person")
        if worn_img is None:
            status_errors.append("missing_worn")
        if worn_ann is None:
            status_errors.append("missing_worn_annotation")

        status = "pending" if not status_errors else "|".join(status_errors)
        if status_errors and len(unresolved_examples) < 30:
            unresolved_examples.append({
                "pair_json": str(jp),
                "from": from_ref,
                "to": to_ref,
                "result": result_ref,
                "status": status,
            })

        rows.append({
            "pair_id": f"EP{len(rows):08d}",
            "person_image": str(person_img or ""),
            "cloth_image": str(cloth_img or ""),
            "worn_image": str(worn_img or ""),
            "annotation_json": str(worn_ann or ""),
            "person_annotation_json": str(person_ann or ""),
            "cloth_annotation_json": str(cloth_ann or ""),
            "pair_json": str(jp),
            "from_ref": from_ref,
            "to_ref": to_ref,
            "result_ref": result_ref,
            "category": category,
            "pose": str(image_info.get("pose", "")),
            "angle": str(image_info.get("angle", "")),
            "model_id": str(info0.get("model_id", "")),
            "cloth_id": str(info0.get("cloth_id", "")),
            "split": split,
            "status": status,
            "pair_quality": "explicit_pair_annotation",
        })

    fields = [
        "pair_id", "person_image", "cloth_image", "worn_image", "annotation_json",
        "person_annotation_json", "cloth_annotation_json", "pair_json",
        "from_ref", "to_ref", "result_ref",
        "category", "pose", "angle", "model_id", "cloth_id",
        "split", "status", "pair_quality",
    ]

    with out_pairs.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "raw_root": str(root.resolve()),
        "ignored_dir_names": sorted(EXCLUDE_DIR_NAMES),
        "num_images": len(images),
        "num_json": len(jsons),
        "num_pair_json_files": len(pair_json_files),
        "pair_json_files": [{"path": str(p), "num_pair_rows": n} for p, n in pair_json_files],
        "num_pair_entries_found": len(pair_entries) + duplicate_count,
        "num_duplicates_removed": duplicate_count,
        "num_pairs_written": len(rows),
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "split_counts": dict(Counter(r["split"] for r in rows)),
        "category_counts": dict(Counter(r["category"] for r in rows)),
        "num_missing_cloth": sum("missing_cloth" in r["status"] for r in rows),
        "num_missing_person": sum("missing_person" in r["status"] for r in rows),
        "num_missing_worn": sum("missing_worn" in r["status"] for r in rows),
        "num_missing_worn_annotation": sum("missing_worn_annotation" in r["status"] for r in rows),
        "unresolved_examples": unresolved_examples,
    }

    out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] wrote pairs: {out_pairs}")
    print(f"[OK] wrote report: {out_report}")
    print(json.dumps({
        "num_pair_json_files": report["num_pair_json_files"],
        "num_pair_entries_found": report["num_pair_entries_found"],
        "num_duplicates_removed": report["num_duplicates_removed"],
        "num_pairs_written": report["num_pairs_written"],
        "status_counts": report["status_counts"],
        "split_counts": report["split_counts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
