#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert AIHub shapeless clothes annotations into starter StableVITON-style artifacts.

Input:
  - pairs CSV, e.g. backend/datasets/processed/index/aihub_pairs_explicit_pending.csv
  - AIHub annotation JSON paths from annotation_json / worn_annotation_json / cloth_annotation_json columns

Output under --processed-root:
  train/openpose-json/{pair_id}_keypoints.json
  train/image-parse/{pair_id}.png
  train/cloth-mask/{pair_id}.png
  train/annotation-quality/{pair_id}.json
  test/...

Notes:
  - image-parse is a grayscale PNG using AIHub segmentation class indices.
  - cloth-mask is a binary PNG from the product cloth annotation if available.
  - If cloth_annotation_json is missing, the script tries to resolve it by matching cloth_image basename.
  - This does not generate DensePose or agnostic-v3.2 yet.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm

EXCLUDE_DIR_NAMES = {"ddd", "_ignore_ddd", "__MACOSX"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# AIHub class names from the uploaded schema. The JSON also carries segmentation_class,
# so this is only a fallback.
FALLBACK_SEGMENTATION_CLASSES = [
    "Background",
    "Face",
    "Left-arm",
    "Right-arm",
    "Left-leg",
    "Right-leg",
    "Normal_top",
    "Normal_bottom",
    "Coat",
    "jacket",
    "Jumper",
    "Padding",
    "vest",
    "Cardigan",
    "Blouse",
    "Top",
    "T-shirt",
    "shirts",
    "Sweater",
    "Pants",
    "Skirt",
    "Dress",
    "jumpsuit",
]

CLOTH_CLASS_NAMES = {
    "Normal_top",
    "Normal_bottom",
    "Coat",
    "jacket",
    "Jumper",
    "Padding",
    "vest",
    "Cardigan",
    "Blouse",
    "Top",
    "T-shirt",
    "shirts",
    "Sweater",
    "Pants",
    "Skirt",
    "Dress",
    "jumpsuit",
}

AIHUB_KP_ORDER = [
    "Nose",
    "Left_eye",
    "Right_eye",
    "Left_ear",
    "Right_ear",
    "Left_shoulder",
    "Right_shoulder",
    "Left_elbow",
    "Right_elbow",
    "Left_wrist",
    "Right_wrist",
    "Left_hip",
    "Right_hip",
    "Left_knee",
    "Right_knee",
    "Left_ankle",
    "Right_ankle",
]

# OpenPose COCO-18 order.
OPENPOSE_COCO18_ORDER = [
    "Nose",
    "Neck",
    "Right_shoulder",
    "Right_elbow",
    "Right_wrist",
    "Left_shoulder",
    "Left_elbow",
    "Left_wrist",
    "Right_hip",
    "Right_knee",
    "Right_ankle",
    "Left_hip",
    "Left_knee",
    "Left_ankle",
    "Right_eye",
    "Left_eye",
    "Right_ear",
    "Left_ear",
]


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


def resolve_path(value: str | None, repo_root: Path) -> Path | None:
    if not value or not isinstance(value, str):
        return None
    p = Path(value)
    if p.exists():
        return p
    p2 = repo_root / value
    if p2.exists():
        return p2
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


def first_annotation(obj: Any) -> dict[str, Any]:
    if not isinstance(obj, dict):
        return {}
    ann = obj.get("annotation")
    if isinstance(ann, list) and ann and isinstance(ann[0], dict):
        return ann[0]
    if isinstance(ann, dict):
        return ann
    return {}


def get_image_size_from_json_or_file(obj: Any, image_path: Path | None) -> tuple[int, int]:
    info = first_info(obj)
    image = info.get("image") if isinstance(info.get("image"), dict) else {}
    try:
        w = int(float(image.get("width")))
        h = int(float(image.get("height")))
        if w > 0 and h > 0:
            return w, h
    except Exception:
        pass

    if image_path and image_path.exists():
        with Image.open(image_path) as im:
            return im.size

    raise ValueError("Cannot determine image width/height")


def polygon_to_np(poly: Any) -> np.ndarray | None:
    if not isinstance(poly, list):
        return None
    # AIHub polygon can be [x1,y1,x2,y2,...] or nested.
    if poly and all(isinstance(v, (int, float)) for v in poly):
        pts = poly
    elif poly and isinstance(poly[0], list):
        # Some segmentation ids contain list of polygon lists.
        return None
    else:
        return None

    if len(pts) < 6 or len(pts) % 2 != 0:
        return None
    arr = np.array(pts, dtype=np.float32).reshape(-1, 2)
    if not np.isfinite(arr).all():
        return None
    return np.round(arr).astype(np.int32)


def iter_polygons(segmentation: Any):
    """Yield (class_id_int, polygon_np)."""
    if not isinstance(segmentation, dict):
        return
    for class_id_str, polygons in segmentation.items():
        try:
            class_id = int(class_id_str)
        except Exception:
            continue

        if not isinstance(polygons, list):
            continue

        # Usually: "18": [[x,y,x,y,...], [x,y,...]]
        for poly in polygons:
            arr = polygon_to_np(poly)
            if arr is not None:
                yield class_id, arr
            elif isinstance(poly, list):
                # Extra nested fallback.
                for sub in poly:
                    arr2 = polygon_to_np(sub)
                    if arr2 is not None:
                        yield class_id, arr2


def render_parse_map(obj: Any, image_path: Path | None) -> tuple[np.ndarray, dict[str, Any]]:
    w, h = get_image_size_from_json_or_file(obj, image_path)
    parse = np.zeros((h, w), dtype=np.uint8)
    ann = first_annotation(obj)
    segmentation = ann.get("segmentation")
    num_polygons = 0
    class_counts = Counter()

    for class_id, pts in iter_polygons(segmentation):
        if class_id < 0 or class_id > 255:
            continue
        cv2.fillPoly(parse, [pts], int(class_id))
        num_polygons += 1
        class_counts[str(class_id)] += 1

    meta = {
        "width": w,
        "height": h,
        "num_polygons": num_polygons,
        "class_polygon_counts": dict(class_counts),
    }
    return parse, meta


def class_name_by_id(obj: Any, class_id: int) -> str:
    info = first_info(obj)
    classes = info.get("segmentation_class")
    if not isinstance(classes, list) or not classes:
        classes = FALLBACK_SEGMENTATION_CLASSES
    if 0 <= class_id < len(classes):
        return str(classes[class_id])
    return ""


def render_cloth_mask(obj: Any, image_path: Path | None) -> tuple[np.ndarray, dict[str, Any]]:
    w, h = get_image_size_from_json_or_file(obj, image_path)
    mask = np.zeros((h, w), dtype=np.uint8)
    ann = first_annotation(obj)
    segmentation = ann.get("segmentation")
    num_polygons = 0
    used_classes = Counter()

    for class_id, pts in iter_polygons(segmentation):
        name = class_name_by_id(obj, class_id)
        if name in CLOTH_CLASS_NAMES:
            cv2.fillPoly(mask, [pts], 255)
            num_polygons += 1
            used_classes[name] += 1

    meta = {
        "width": w,
        "height": h,
        "num_cloth_polygons": num_polygons,
        "used_cloth_classes": dict(used_classes),
    }
    return mask, meta


def parse_aihub_keypoints(obj: Any) -> dict[str, tuple[float, float, float]]:
    ann = first_annotation(obj)
    kp = ann.get("keypoint")
    if not isinstance(kp, list):
        return {}
    info = first_info(obj)
    names = info.get("keypoint_class")
    if not isinstance(names, list) or not names:
        names = AIHUB_KP_ORDER

    out: dict[str, tuple[float, float, float]] = {}
    n = min(len(names), len(kp) // 3)
    for i in range(n):
        try:
            x = float(kp[i * 3 + 0])
            y = float(kp[i * 3 + 1])
            v_raw = float(kp[i * 3 + 2])
        except Exception:
            continue
        conf = 1.0 if v_raw > 0 else 0.0
        out[str(names[i])] = (x, y, conf)
    return out


def compute_neck(kps: dict[str, tuple[float, float, float]]) -> tuple[float, float, float]:
    ls = kps.get("Left_shoulder")
    rs = kps.get("Right_shoulder")
    if not ls or not rs or ls[2] <= 0 or rs[2] <= 0:
        return (0.0, 0.0, 0.0)
    return ((ls[0] + rs[0]) / 2.0, (ls[1] + rs[1]) / 2.0, min(ls[2], rs[2]))


def make_openpose_json(obj: Any, image_path: Path | None) -> dict[str, Any]:
    kps = parse_aihub_keypoints(obj)
    if kps:
        kps["Neck"] = compute_neck(kps)

    pose = []
    for name in OPENPOSE_COCO18_ORDER:
        x, y, c = kps.get(name, (0.0, 0.0, 0.0))
        pose.extend([round(x, 3), round(y, 3), round(c, 4)])

    w, h = get_image_size_from_json_or_file(obj, image_path)
    info = first_info(obj)
    return {
        "version": 1.3,
        "source": "AIHub shapeless clothes annotation converted to OpenPose-like COCO18 JSON",
        "image_width": w,
        "image_height": h,
        "model_id": info.get("model_id", ""),
        "cloth_id": info.get("cloth_id", ""),
        "pose_id": (info.get("image") or {}).get("pose", "") if isinstance(info.get("image"), dict) else "",
        "angle": (info.get("image") or {}).get("angle", "") if isinstance(info.get("image"), dict) else "",
        "people": [
            {
                "person_id": [-1],
                "pose_keypoints_2d": pose,
                "face_keypoints_2d": [],
                "hand_left_keypoints_2d": [],
                "hand_right_keypoints_2d": [],
                "pose_keypoint_names": OPENPOSE_COCO18_ORDER,
                "aihub_keypoints_2d": [v for name in AIHUB_KP_ORDER for v in kps.get(name, (0.0, 0.0, 0.0))],
                "aihub_keypoint_names": AIHUB_KP_ORDER,
            }
        ],
    }


def build_annotation_index(raw_root: Path) -> dict[str, Path]:
    """Map image basename/stem from JSON info.image.path to annotation JSON path."""
    idx: dict[str, Path] = {}
    for jp in raw_root.rglob("*.json"):
        if is_excluded(jp):
            continue
        obj = safe_load_json(jp)
        if not isinstance(obj, dict):
            continue
        info = first_info(obj)
        image = info.get("image") if isinstance(info.get("image"), dict) else {}
        image_path = str(image.get("path", ""))
        if not image_path:
            continue
        name = Path(image_path.replace("\\", "/")).name
        if name:
            idx.setdefault(name.lower(), jp)
            idx.setdefault(Path(name).stem.lower(), jp)
    return idx


def resolve_annotation_for_image(image_path_str: str, annotation_index: dict[str, Path], repo_root: Path) -> Path | None:
    if not image_path_str:
        return None
    p = resolve_path(image_path_str, repo_root)
    name = p.name if p else Path(image_path_str.replace("\\", "/")).name
    if not name:
        return None
    return annotation_index.get(name.lower()) or annotation_index.get(Path(name).stem.lower())


def split_name(s: str) -> str:
    if s == "val":
        return "test"
    if s in {"train", "test"}:
        return s
    return "train"


def ensure_dirs(root: Path, split: str) -> dict[str, Path]:
    names = ["openpose-json", "image-parse", "cloth-mask", "annotation-quality"]
    out = {}
    for n in names:
        p = root / split / n
        p.mkdir(parents=True, exist_ok=True)
        out[n] = p
    return out


def read_pairs(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def append_csv(path: Path, row: dict[str, Any], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            w.writeheader()
        w.writerow(row)


def outputs_exist(processed_root: Path, split: str, pair_id: str) -> bool:
    return (
        (processed_root / split / "openpose-json" / f"{pair_id}_keypoints.json").exists()
        and (processed_root / split / "image-parse" / f"{pair_id}.png").exists()
        and (processed_root / split / "cloth-mask" / f"{pair_id}.png").exists()
        and (processed_root / split / "annotation-quality" / f"{pair_id}.json").exists()
    )


def process_one(pair: dict[str, str], args, annotation_index: dict[str, Path] | None) -> tuple[str, list[tuple[str, str, str]], dict[str, Any]]:
    repo_root = Path.cwd()
    processed_root = Path(args.processed_root)
    pair_id = pair["pair_id"]
    split = split_name(pair.get("split", "train"))
    dirs = ensure_dirs(processed_root, split)

    errors: list[tuple[str, str, str]] = []

    if args.resume and outputs_exist(processed_root, split, pair_id):
        return "skipped", errors, {"pair_id": pair_id, "split": split, "skipped": True}

    person_image = resolve_path(pair.get("person_image"), repo_root)
    cloth_image = resolve_path(pair.get("cloth_image"), repo_root)
    worn_image = resolve_path(pair.get("worn_image"), repo_root)

    worn_ann_path = (
        resolve_path(pair.get("worn_annotation_json"), repo_root)
        or resolve_path(pair.get("annotation_json"), repo_root)
    )
    cloth_ann_path = resolve_path(pair.get("cloth_annotation_json"), repo_root)

    if annotation_index is not None:
        if worn_ann_path is None and pair.get("worn_image"):
            worn_ann_path = resolve_annotation_for_image(pair.get("worn_image", ""), annotation_index, repo_root)
        if cloth_ann_path is None and pair.get("cloth_image"):
            cloth_ann_path = resolve_annotation_for_image(pair.get("cloth_image", ""), annotation_index, repo_root)

    if worn_ann_path is None or not worn_ann_path.exists():
        errors.append(("annotation", "MISSING_WORN_ANNOTATION", pair.get("annotation_json", "")))
    if cloth_ann_path is None or not cloth_ann_path.exists():
        errors.append(("annotation", "MISSING_CLOTH_ANNOTATION", pair.get("cloth_annotation_json", "")))

    # Worn/person annotation => openpose + image-parse.
    parse_meta = {}
    openpose_ok = False
    parse_ok = False
    if worn_ann_path and worn_ann_path.exists():
        worn_obj = safe_load_json(worn_ann_path)
        if isinstance(worn_obj, dict):
            try:
                op = make_openpose_json(worn_obj, worn_image or person_image)
                (dirs["openpose-json"] / f"{pair_id}_keypoints.json").write_text(
                    json.dumps(op, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                openpose_ok = True
            except Exception as e:
                errors.append(("openpose-json", "OPENPOSE_JSON_FAILED", repr(e)))

            try:
                parse_map, parse_meta = render_parse_map(worn_obj, worn_image or person_image)
                Image.fromarray(parse_map).save(dirs["image-parse"] / f"{pair_id}.png")
                parse_ok = True
            except Exception as e:
                errors.append(("image-parse", "IMAGE_PARSE_FAILED", repr(e)))
        else:
            errors.append(("annotation", "INVALID_WORN_ANNOTATION_JSON", str(worn_ann_path)))

    # Cloth annotation => cloth-mask.
    cloth_mask_meta = {}
    cloth_mask_ok = False
    if cloth_ann_path and cloth_ann_path.exists():
        cloth_obj = safe_load_json(cloth_ann_path)
        if isinstance(cloth_obj, dict):
            try:
                mask, cloth_mask_meta = render_cloth_mask(cloth_obj, cloth_image)
                Image.fromarray(mask).save(dirs["cloth-mask"] / f"{pair_id}.png")
                cloth_mask_ok = bool(np.count_nonzero(mask) > 0)
                if not cloth_mask_ok:
                    errors.append(("cloth-mask", "EMPTY_CLOTH_MASK", str(cloth_ann_path)))
            except Exception as e:
                errors.append(("cloth-mask", "CLOTH_MASK_FAILED", repr(e)))
        else:
            errors.append(("annotation", "INVALID_CLOTH_ANNOTATION_JSON", str(cloth_ann_path)))

    q = {
        "pair_id": pair_id,
        "split": split,
        "person_image": str(person_image) if person_image else "",
        "cloth_image": str(cloth_image) if cloth_image else "",
        "worn_image": str(worn_image) if worn_image else "",
        "worn_annotation_json": str(worn_ann_path) if worn_ann_path else "",
        "cloth_annotation_json": str(cloth_ann_path) if cloth_ann_path else "",
        "openpose_json_ok": openpose_ok,
        "image_parse_ok": parse_ok,
        "cloth_mask_ok": cloth_mask_ok,
        "parse_meta": parse_meta,
        "cloth_mask_meta": cloth_mask_meta,
        "num_errors": len(errors),
    }
    (dirs["annotation-quality"] / f"{pair_id}.json").write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")

    status = "success" if openpose_ok and parse_ok and cloth_mask_ok and not errors else "success_with_warnings" if openpose_ok or parse_ok or cloth_mask_ok else "failed"
    return status, errors, q


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", required=True)
    parser.add_argument("--processed-root", required=True)
    parser.add_argument("--raw-root", default=None, help="Optional. Used to resolve missing cloth_annotation_json by image basename.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--end-index", type=int, default=None)
    parser.add_argument("--only-status", default="pending")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--save-failures", action="store_true")
    args = parser.parse_args()

    pairs = read_pairs(Path(args.pairs))
    if args.only_status:
        allowed = {x.strip() for x in args.only_status.split(",") if x.strip()}
        pairs = [p for p in pairs if p.get("status", "") in allowed]
    pairs = pairs[args.start_index:args.end_index]
    if args.limit is not None:
        pairs = pairs[: args.limit]

    annotation_index = None
    if args.raw_root:
        print("[INFO] building annotation index from raw-root. This can take a few minutes...")
        annotation_index = build_annotation_index(Path(args.raw_root))
        print(f"[INFO] annotation index size: {len(annotation_index)}")

    processed_root = Path(args.processed_root)
    progress_path = processed_root / "annotation_convert_progress.csv"
    failures_path = processed_root / "annotation_convert_failures.csv"
    progress_fields = ["pair_id", "split", "status", "elapsed_sec", "num_errors"]
    failure_fields = ["pair_id", "stage", "error_code", "message"]

    stats = {
        "num_requested": len(pairs),
        "num_success": 0,
        "num_success_with_warnings": 0,
        "num_failed": 0,
        "num_skipped": 0,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    error_counts = Counter()
    t_all = time.time()

    for pair in tqdm(pairs, desc="convert annotations"):
        t0 = time.time()
        pair_id = pair["pair_id"]
        split = split_name(pair.get("split", "train"))
        try:
            status, errors, _q = process_one(pair, args, annotation_index)
        except Exception as e:
            status = "failed"
            errors = [("unknown", "UNKNOWN_ERROR", repr(e))]

        if status == "success":
            stats["num_success"] += 1
        elif status == "success_with_warnings":
            stats["num_success_with_warnings"] += 1
        elif status == "skipped":
            stats["num_skipped"] += 1
        else:
            stats["num_failed"] += 1

        for stage, code, msg in errors:
            error_counts[code] += 1
            if args.save_failures:
                append_csv(failures_path, {"pair_id": pair_id, "stage": stage, "error_code": code, "message": msg}, failure_fields)

        append_csv(progress_path, {
            "pair_id": pair_id,
            "split": split,
            "status": status,
            "elapsed_sec": round(time.time() - t0, 3),
            "num_errors": len(errors),
        }, progress_fields)

    stats["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    stats["elapsed_sec"] = round(time.time() - t_all, 3)
    stats["error_counts"] = dict(error_counts)
    stats["success_rate_strict"] = round(stats["num_success"] / max(1, len(pairs)), 4)
    stats["success_rate_loose"] = round((stats["num_success"] + stats["num_success_with_warnings"] + stats["num_skipped"]) / max(1, len(pairs)), 4)

    stats_path = processed_root / "annotation_convert_stats.json"
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
