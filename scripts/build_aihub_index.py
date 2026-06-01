#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build rough AIHub item/pair index.

This version ignores duplicate/temporary folders such as:
- ddd
- _ignore_ddd
- __MACOSX

Important:
This is a starter indexer. It creates a useful first CSV, but the final AIHub
pair mapping should be refined with the dataset's pair annotation:
from = product image
to = model image
result = worn image

Usage:
python scripts\build_aihub_index.py ^
  --raw-root "backend\datasets\raw\aihub\011.쉐이프리스 의류 및 포즈 데이터\01-1.정식개방데이터" ^
  --out-items backend\datasets\processed\index\aihub_items_full.csv ^
  --out-pairs backend\datasets\processed\index\aihub_pairs_full.csv ^
  --save-report backend\datasets\processed\index\aihub_index_report_full.json
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

EXCLUDE_DIR_NAMES = {
    "ddd",
    "_ignore_ddd",
    "__MACOSX",
}

PERSON_HINTS = ("person", "model", "human", "wear", "worn", "착용", "모델", "사람", "인물")
CLOTH_HINTS = ("cloth", "clothes", "garment", "product", "item", "의류", "상품", "제품", "옷")
WORN_HINTS = ("제품 착용", "착용", "worn", "wear")
TRAIN_HINTS = ("training", "train", "학습", "Training")
VAL_HINTS = ("validation", "valid", "val", "검증", "Validation")


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIR_NAMES for part in path.parts)


def norm_stem(s: str) -> str:
    s = Path(s).stem.lower()
    s = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", s)
    return s.strip("_")


def key_tokens(path: Path) -> set[str]:
    text = "_".join(path.with_suffix("").parts).lower()
    return {t for t in re.split(r"[^0-9a-zA-Z가-힣]+", text) if t}


def infer_split(path: Path) -> str:
    text = str(path).lower()
    if any(h.lower() in text for h in VAL_HINTS):
        return "val"
    if any(h.lower() in text for h in TRAIN_HINTS):
        return "train"
    return "unknown"


def infer_category(path: Path, ann: dict[str, Any] | None = None) -> str:
    text = str(path).lower()
    if ann:
        info = ann.get("info")
        if isinstance(info, list) and info and isinstance(info[0], dict):
            info0 = info[0]
            # category may be absent, but image path often contains product class.
            image = info0.get("image")
            if isinstance(image, dict):
                text += " " + str(image.get("path", "")).lower()

        for k in ("category", "cloth_type", "clothing_type", "class", "label", "item_category", "cloth_type2"):
            v = ann.get(k)
            if isinstance(v, str) and v:
                return v

    if any(w in text for w in ("outer", "jacket", "coat", "jumper", "padding", "cardigan", "아우터", "자켓", "재킷", "코트", "점퍼", "패딩", "가디건")):
        return "outer"
    if any(w in text for w in ("top", "shirt", "upper", "blouse", "t-shirt", "sweater", "상의", "티셔츠", "셔츠", "블라우스", "스웨터", "니트")):
        return "top"
    if any(w in text for w in ("dress", "jumpsuit", "원피스", "점프수트")):
        return "dress"
    if any(w in text for w in ("pants", "skirt", "bottom", "하의", "바지", "스커트", "치마")):
        return "bottom"
    return "unknown"


def infer_kind(path: Path, ann: dict[str, Any] | None = None) -> str:
    text = str(path).lower()

    # Folder naming convention:
    # TS_제품 착용 / TL_제품 착용: worn/result image
    # TS_제품 / TL_제품: product/cloth image
    # TS_모델 / TL_모델: model/base person image
    if "제품 착용" in text or "제품착용" in text:
        return "worn"
    if "ts_제품" in text or "tl_제품" in text or "\\제품\\" in text or "/제품/" in text:
        return "cloth"
    if "ts_모델" in text or "tl_모델" in text or "\\모델\\" in text or "/모델/" in text:
        return "model"

    if ann:
        info = ann.get("info")
        if isinstance(info, list) and info and isinstance(info[0], dict):
            info0 = info[0]
            img_path = ""
            if isinstance(info0.get("image"), dict):
                img_path = str(info0["image"].get("path", ""))
            if "제품 착용" in img_path:
                return "worn"
            if "제품" in img_path and "착용" not in img_path:
                return "cloth"
            if "모델" in img_path:
                return "model"

    if any(h.lower() in text for h in CLOTH_HINTS) and not any(h.lower() in text for h in WORN_HINTS):
        return "cloth"
    if any(h.lower() in text for h in PERSON_HINTS):
        return "model"
    return "unknown"


def safe_read_json(path: Path) -> Any | None:
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    return None


def first_info(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict):
        return {}
    info = obj.get("info")
    if isinstance(info, list) and info and isinstance(info[0], dict):
        return info[0]
    if isinstance(info, dict):
        return info
    return {}


def flatten_find_strings(obj: Any, keys: tuple[str, ...], limit: int = 100) -> list[str]:
    out: list[str] = []

    def walk(x: Any):
        if len(out) >= limit:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                lk = str(k).lower()
                if any(t in lk for t in keys) and isinstance(v, str):
                    out.append(v)
                walk(v)
        elif isinstance(x, list):
            for v in x[:500]:
                walk(v)

    walk(obj)
    return out


def build_basename_index(paths: list[Path]) -> dict[str, list[Path]]:
    d: dict[str, list[Path]] = defaultdict(list)
    for p in paths:
        d[p.name.lower()].append(p)
        d[p.stem.lower()].append(p)
    return d


def resolve_by_json_path(json_path_value: str, basename_index: dict[str, list[Path]]) -> str:
    if not json_path_value:
        return ""
    name = Path(json_path_value.replace("\\", "/")).name.lower()
    if not name:
        return ""
    hits = basename_index.get(name) or basename_index.get(Path(name).stem.lower())
    if not hits:
        return ""
    # Prefer non-ignored paths implicitly already indexed.
    return str(hits[0])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True)
    parser.add_argument("--out-items", required=True)
    parser.add_argument("--out-pairs", required=True)
    parser.add_argument("--save-report", required=True)
    args = parser.parse_args()

    root = Path(args.raw_root)
    out_items = Path(args.out_items)
    out_pairs = Path(args.out_pairs)
    out_report = Path(args.save_report)
    out_items.parent.mkdir(parents=True, exist_ok=True)
    out_pairs.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)

    if not root.exists():
        raise FileNotFoundError(f"raw-root does not exist: {root}")

    images = sorted([
        p for p in root.rglob("*")
        if p.is_file() and not is_excluded(p) and p.suffix.lower() in IMAGE_EXTS
    ])
    jsons = sorted([
        p for p in root.rglob("*")
        if p.is_file() and not is_excluded(p) and p.suffix.lower() in JSON_EXTS
    ])

    image_by_basename = build_basename_index(images)

    json_by_stem: dict[str, list[Path]] = defaultdict(list)
    json_preview_by_path: dict[Path, dict[str, Any]] = {}

    for jp in jsons:
        json_by_stem[norm_stem(jp.name)].append(jp)
        obj = safe_read_json(jp)
        if isinstance(obj, dict):
            json_preview_by_path[jp] = obj

            info0 = first_info(obj)
            image_info = info0.get("image") if isinstance(info0.get("image"), dict) else {}
            json_image_path = str(image_info.get("path", ""))
            if json_image_path:
                json_by_stem[norm_stem(Path(json_image_path).name)].append(jp)

            refs = flatten_find_strings(obj, ("file", "image", "img", "path", "filename", "name"))
            for ref in refs:
                if Path(ref.replace("\\", "/")).suffix.lower() in IMAGE_EXTS:
                    json_by_stem[norm_stem(ref)].append(jp)

    rows = []
    for i, img in enumerate(images):
        rel = img.relative_to(root)
        stem = norm_stem(img.name)
        candidate_jsons = json_by_stem.get(stem, [])

        if not candidate_jsons:
            # fallback: same stem in json filename
            candidate_jsons = json_by_stem.get(norm_stem(img.stem), [])

        ann_path = candidate_jsons[0] if candidate_jsons else None
        ann_obj = json_preview_by_path.get(ann_path) if ann_path else None
        info0 = first_info(ann_obj) if ann_obj else {}
        image_info = info0.get("image") if isinstance(info0.get("image"), dict) else {}

        rows.append(
            {
                "item_id": f"I{i:08d}",
                "image_path": str(img),
                "image_rel": str(rel),
                "annotation_json": str(ann_path) if ann_path else "",
                "kind": infer_kind(rel, ann_obj if isinstance(ann_obj, dict) else None),
                "split": infer_split(rel),
                "category": infer_category(rel, ann_obj if isinstance(ann_obj, dict) else None),
                "stem": stem,
                "model_id": str(info0.get("model_id", "")),
                "cloth_id": str(info0.get("cloth_id", "")),
                "angle": str(image_info.get("angle", "")),
                "pose": str(image_info.get("pose", "")),
                "json_image_path": str(image_info.get("path", "")),
                "status": "pending" if ann_path else "missing_annotation",
            }
        )

    item_fields = [
        "item_id", "image_path", "image_rel", "annotation_json", "kind", "split", "category", "stem",
        "model_id", "cloth_id", "angle", "pose", "json_image_path", "status"
    ]
    with out_items.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=item_fields)
        writer.writeheader()
        writer.writerows(rows)

    # Build helper indexes from items.
    cloth_items = [r for r in rows if r["kind"] == "cloth"]
    model_items = [r for r in rows if r["kind"] == "model"]
    worn_items = [r for r in rows if r["kind"] == "worn"]

    cloth_by_cloth_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    model_by_model_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    worn_by_model_cloth: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)

    for r in cloth_items:
        if r["cloth_id"]:
            cloth_by_cloth_id[r["cloth_id"]].append(r)
    for r in model_items:
        if r["model_id"]:
            model_by_model_id[r["model_id"]].append(r)
    for r in worn_items:
        if r["model_id"] and r["cloth_id"]:
            worn_by_model_cloth[(r["model_id"], r["cloth_id"])].append(r)

    # Pair annotation jsons may be simple dict/list with from/to/result.
    explicit_pairs = []
    for jp, obj in json_preview_by_path.items():
        candidates = []
        if isinstance(obj, list):
            candidates = [x for x in obj if isinstance(x, dict)]
        elif isinstance(obj, dict):
            if all(k in obj for k in ("from", "to", "result")):
                candidates = [obj]
            else:
                # Sometimes pair list is nested.
                for v in obj.values():
                    if isinstance(v, list):
                        candidates.extend([x for x in v if isinstance(x, dict) and all(k in x for k in ("from", "to", "result"))])
        for c in candidates:
            explicit_pairs.append((jp, c))

    pair_rows = []

    # Prefer explicit pair annotations if found.
    if explicit_pairs:
        for idx, (jp, p) in enumerate(explicit_pairs):
            cloth_img = resolve_by_json_path(str(p.get("from", "")), image_by_basename)
            model_img = resolve_by_json_path(str(p.get("to", "")), image_by_basename)
            worn_img = resolve_by_json_path(str(p.get("result", "")), image_by_basename)
            pair_rows.append({
                "pair_id": f"P{idx:08d}",
                "person_image": model_img or worn_img,
                "cloth_image": cloth_img,
                "worn_image": worn_img,
                "annotation_json": str(jp),
                "category": infer_category(Path(worn_img or cloth_img or model_img or ""), None),
                "pose": "",
                "angle": "",
                "model_id": "",
                "cloth_id": "",
                "split": infer_split(jp),
                "status": "pending" if cloth_img and (model_img or worn_img) else "pair_path_unresolved",
                "pair_quality": "explicit_pair_annotation",
            })
    else:
        # Fallback: use worn image as person/target, match cloth by cloth_id if available.
        idx = 0
        for w in worn_items:
            cloth = None
            if w["cloth_id"] and cloth_by_cloth_id.get(w["cloth_id"]):
                cloth = cloth_by_cloth_id[w["cloth_id"]][0]

            pair_rows.append({
                "pair_id": f"P{idx:08d}",
                "person_image": w["image_path"],       # fallback: worn image
                "cloth_image": cloth["image_path"] if cloth else "",
                "worn_image": w["image_path"],
                "annotation_json": w["annotation_json"],
                "category": w["category"],
                "pose": w["pose"],
                "angle": w["angle"],
                "model_id": w["model_id"],
                "cloth_id": w["cloth_id"],
                "split": w["split"],
                "status": "pending" if w["annotation_json"] else "missing_annotation",
                "pair_quality": "worn_plus_cloth_id" if cloth else "worn_only_needs_cloth_mapping",
            })
            idx += 1

        # If no worn images were classified, fallback to all person-like/model images.
        if not pair_rows:
            person_like = [r for r in rows if r["kind"] in ("model", "unknown")]
            for p in person_like:
                cloth = None
                if p["cloth_id"] and cloth_by_cloth_id.get(p["cloth_id"]):
                    cloth = cloth_by_cloth_id[p["cloth_id"]][0]
                pair_rows.append({
                    "pair_id": f"P{idx:08d}",
                    "person_image": p["image_path"],
                    "cloth_image": cloth["image_path"] if cloth else "",
                    "worn_image": "",
                    "annotation_json": p["annotation_json"],
                    "category": p["category"],
                    "pose": p["pose"],
                    "angle": p["angle"],
                    "model_id": p["model_id"],
                    "cloth_id": p["cloth_id"],
                    "split": p["split"],
                    "status": "pending" if p["annotation_json"] else "missing_annotation",
                    "pair_quality": "fallback_model_plus_cloth_id" if cloth else "fallback_needs_review",
                })
                idx += 1

    pair_fields = [
        "pair_id", "person_image", "cloth_image", "worn_image", "annotation_json", "category",
        "pose", "angle", "model_id", "cloth_id", "split", "status", "pair_quality"
    ]
    with out_pairs.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=pair_fields)
        writer.writeheader()
        writer.writerows(pair_rows)

    report = {
        "raw_root": str(root.resolve()),
        "ignored_dir_names": sorted(EXCLUDE_DIR_NAMES),
        "num_images": len(images),
        "num_json": len(jsons),
        "num_items": len(rows),
        "num_cloth_items": len(cloth_items),
        "num_model_items": len(model_items),
        "num_worn_items": len(worn_items),
        "num_pairs": len(pair_rows),
        "num_explicit_pair_annotations": len(explicit_pairs),
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "pair_status_counts": dict(Counter(r["status"] for r in pair_rows)),
        "pair_quality_counts": dict(Counter(r["pair_quality"] for r in pair_rows)),
        "kind_counts": dict(Counter(r["kind"] for r in rows)),
        "category_counts": dict(Counter(r["category"] for r in rows)),
        "split_counts": dict(Counter(r["split"] for r in rows)),
        "note": "ddd/_ignore_ddd folders are ignored. Inspect aihub_pairs CSV before preprocessing.",
    }
    out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] items: {out_items}")
    print(f"[OK] pairs: {out_pairs}")
    print(f"[OK] report: {out_report}")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
