#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
from PIL import Image
from tqdm import tqdm

# OpenPose BODY_25 style indices used by convert_aihub_annotations.py output.
# AIHub original keypoints are COCO-17, but the converter normally writes BODY_25-like JSON.
OPENPOSE = {
    "nose": 0,
    "neck": 1,
    "right_shoulder": 2,
    "right_elbow": 3,
    "right_wrist": 4,
    "left_shoulder": 5,
    "left_elbow": 6,
    "left_wrist": 7,
    "right_hip": 8,
    "right_knee": 9,
    "right_ankle": 10,
    "left_hip": 11,
    "left_knee": 12,
    "left_ankle": 13,
    "right_eye": 14,
    "left_eye": 15,
    "right_ear": 16,
    "left_ear": 17,
}

# AIHub segmentation_class index 기준
# 0 Background
# 1 Face
# 2 Left-arm
# 3 Right-arm
# 4 Left-leg
# 5 Right-leg
# 6 Normal_top
# 7 Normal_bottom
# 8 Coat
# 9 jacket
# 10 Jumper
# 11 Padding
# 12 vest
# 13 Cardigan
# 14 Blouse
# 15 Top
# 16 T-shirt
# 17 shirts
# 18 Sweater
# 19 Pants
# 20 Skirt
# 21 Dress
# 22 jumpsuit
UPPER = {6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18}
LOWER = {7, 19, 20}
FULL_BODY_CLOTHES = {21, 22}
ARM = {2, 3}
LEG = {4, 5}
FACE = {1}
BODY = UPPER | LOWER | FULL_BODY_CLOTHES | ARM | LEG | FACE

Point = Tuple[float, float]
KpDict = Dict[str, Tuple[float, float, float]]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_json(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    for enc in ("utf-8", "utf-8-sig", "cp949"):
        try:
            with path.open("r", encoding=enc) as f:
                return json.load(f)
        except Exception:
            continue
    return None


def dist(a: Point, b: Point) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def read_keypoints(path: Path) -> KpDict:
    obj = load_json(path)
    if not isinstance(obj, dict):
        return {}
    people = obj.get("people")
    if not isinstance(people, list) or not people:
        return {}
    arr = people[0].get("pose_keypoints_2d", [])
    if not isinstance(arr, list):
        return {}

    out: KpDict = {}
    for name, idx in OPENPOSE.items():
        j = idx * 3
        if j + 2 < len(arr):
            try:
                out[name] = (float(arr[j]), float(arr[j + 1]), float(arr[j + 2]))
            except Exception:
                pass
    return out


def valid_xy(kps: KpDict, name: str, min_conf: float = 0.05) -> Optional[Point]:
    v = kps.get(name)
    if not v:
        return None
    x, y, c = v
    if c < min_conf or x <= 0 or y <= 0:
        return None
    return (x, y)


def read_mask(path: Path) -> Optional[np.ndarray]:
    if not path.exists():
        return None
    try:
        arr = np.array(Image.open(path))
    except Exception:
        return None
    if arr.ndim == 3:
        arr = arr[:, :, 0]
    return arr.astype(np.int32)


def band_width(mask: np.ndarray, y: int, band: int = 8) -> Optional[float]:
    if mask is None or mask.size == 0:
        return None
    h, _ = mask.shape
    y0 = max(0, int(y) - band)
    y1 = min(h, int(y) + band + 1)
    if y0 >= y1:
        return None
    sub = mask[y0:y1]
    xs = np.where(sub > 0)[1]
    if len(xs) == 0:
        return None
    return float(xs.max() - xs.min() + 1)


def mask_center(mask: np.ndarray) -> Optional[Point]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    return (float(xs.mean()), float(ys.mean()))


def mask_bottom_center(mask: np.ndarray) -> Optional[Point]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return None
    y = int(ys.max())
    x_at_y = xs[ys == y]
    if len(x_at_y) == 0:
        return None
    return (float(x_at_y.mean()), float(y))


def safe_ratio(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if num is None or den is None or den <= 1:
        return None
    val = num / den
    if not math.isfinite(val):
        return None
    return float(val)


def classify_fit(features: Dict[str, Any]) -> str:
    if float(features.get("confidence") or 0) < 45:
        return "unknown_low_confidence"

    sr = features.get("shoulder_ratio")
    tr = features.get("torso_width_ratio")
    gl = features.get("garment_length_ratio")

    if sr is not None and tr is not None and gl is not None:
        if sr > 1.18 and tr > 1.22 and gl > 1.12:
            return "oversized"

    if (sr is not None and sr > 1.10) or (tr is not None and tr > 1.15):
        return "slightly_oversized"

    if sr is not None and tr is not None:
        if 0.95 <= sr <= 1.06 and 0.95 <= tr <= 1.08:
            return "fitted_or_slim_direction"

    return "regular"


def make_annotation(
    key: str,
    label: str,
    text: str,
    x: float,
    y: float,
    width: int,
    height: int,
    value: Optional[float],
) -> Dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "text": text,
        "x": round(x / max(1, width) * 100, 2),
        "y": round(y / max(1, height) * 100, 2),
        "value": None if value is None else round(float(value), 4),
    }


def round_or_none(x: Optional[float], ndigits: int = 6) -> Optional[float]:
    if x is None:
        return None
    try:
        if not math.isfinite(float(x)):
            return None
        return round(float(x), ndigits)
    except Exception:
        return None


def output_split(pair_split: str) -> str:
    # batch_aihub_preprocess.py currently maps val -> test in processed output.
    return "test" if pair_split == "val" else (pair_split or "test")


def process_one(
    pair: Dict[str, str],
    processed_root: Path,
    save_fit_json: bool,
    save_annotations: bool,
) -> Dict[str, Any]:
    pair_id = pair["pair_id"]
    split = output_split(pair.get("split", "test"))

    image_path = processed_root / split / "image" / f"{pair_id}.jpg"
    cloth_path = processed_root / split / "cloth" / f"{pair_id}.jpg"
    keypoint_path = processed_root / split / "openpose-json" / f"{pair_id}_keypoints.json"
    parse_path = processed_root / split / "image-parse" / f"{pair_id}.png"
    fit_path = processed_root / split / "fit" / f"{pair_id}.json"

    width, height = 0, 0
    if image_path.exists():
        try:
            with Image.open(image_path) as im:
                width, height = im.size
        except Exception:
            pass

    keypoints = read_keypoints(keypoint_path)
    parse = read_mask(parse_path)

    left_shoulder = valid_xy(keypoints, "left_shoulder")
    right_shoulder = valid_xy(keypoints, "right_shoulder")
    left_hip = valid_xy(keypoints, "left_hip")
    right_hip = valid_xy(keypoints, "right_hip")
    left_elbow = valid_xy(keypoints, "left_elbow")
    right_elbow = valid_xy(keypoints, "right_elbow")
    left_wrist = valid_xy(keypoints, "left_wrist")
    right_wrist = valid_xy(keypoints, "right_wrist")

    valid_pose_count = sum(1 for v in keypoints.values() if len(v) == 3 and v[2] > 0.05 and v[0] > 0 and v[1] > 0)
    pose_quality = min(1.0, valid_pose_count / 14.0)

    row: Dict[str, Any] = {
        "pair_id": pair_id,
        "split": split,
        "image_path": str(image_path),
        "cloth_path": str(cloth_path),
        "cloth_id": pair.get("cloth_id", ""),
        "model_id": pair.get("model_id", ""),
        "pose": pair.get("pose", "unknown"),
        "angle": pair.get("angle", "unknown"),
        "cloth_type": pair.get("category", "unknown"),
        "shoulder_ratio": None,
        "torso_width_ratio": None,
        "sleeve_length_ratio": None,
        "garment_length_ratio": None,
        "silhouette_score": None,
        "pose_quality": round(pose_quality, 6),
        "parsing_quality": 0.0,
        "body_visibility": 0.0,
        "quality_score": 0.0,
        "confidence": 0.0,
        "fit_label": "unknown_low_confidence",
        "error_code": "",
    }

    annotations: List[Dict[str, Any]] = []
    errors: List[str] = []

    if not image_path.exists():
        errors.append("MISSING_IMAGE")
    if not cloth_path.exists():
        errors.append("MISSING_CLOTH")
    if not keypoint_path.exists():
        errors.append("MISSING_OPENPOSE_JSON")
    if parse is None:
        errors.append("MISSING_IMAGE_PARSE")

    upper = None
    body = None
    if parse is not None:
        unique_vals = set(int(x) for x in np.unique(parse))

        # Current AIHub converter may output binary-like parse where 7 means garment/body mask.
        # If parse has only {0, 7}, treat 7 as the garment/body region.
        if unique_vals.issubset({0, 7}):
            upper = (parse == 7).astype(np.uint8)
            body = (parse == 7).astype(np.uint8)
        else:
            upper = np.isin(parse, list(UPPER | FULL_BODY_CLOTHES)).astype(np.uint8)
            body = np.isin(parse, list(BODY)).astype(np.uint8)

        upper_area = float(upper.sum())
        body_area = float(body.sum())
        image_area = float(max(1, parse.size))

        # Quality heuristics. These are pseudo scores, not ground-truth labels.
        row["parsing_quality"] = round(min(1.0, upper_area / max(1.0, image_area * 0.08)), 6)
        row["body_visibility"] = round(min(1.0, body_area / max(1.0, image_area * 0.20)), 6)
        row["silhouette_score"] = round(min(1.0, body_area / max(1.0, image_area * 0.25)), 6)

        # shoulder_ratio = garment shoulder width / body shoulder width
        if left_shoulder and right_shoulder:
            shoulder_y = int((left_shoulder[1] + right_shoulder[1]) / 2)
            body_shoulder_width = dist(left_shoulder, right_shoulder)
            garment_shoulder_width = band_width(upper, shoulder_y, band=10)
            row["shoulder_ratio"] = round_or_none(safe_ratio(garment_shoulder_width, body_shoulder_width))
            if row["shoulder_ratio"] is not None and not (0.4 <= row["shoulder_ratio"] <= 3.0):
                row["shoulder_ratio"] = None

        # torso_width_ratio = upper garment width / body width around chest/upper torso
        if left_shoulder and right_shoulder and left_hip and right_hip:
            shoulder_y = int((left_shoulder[1] + right_shoulder[1]) / 2)
            hip_y = int((left_hip[1] + right_hip[1]) / 2)
            torso_y = int(shoulder_y * 0.65 + hip_y * 0.35)
            body_width = band_width(body, torso_y, band=12)
            garment_width = band_width(upper, torso_y, band=12)
            row["torso_width_ratio"] = round_or_none(safe_ratio(garment_width, body_width))
            if row["torso_width_ratio"] is not None and not (0.4 <= row["torso_width_ratio"] <= 3.0):
                row["torso_width_ratio"] = None

            # garment_length_ratio = (top hem y - shoulder y) / (hip y - shoulder y)
            ys = np.where(upper > 0)[0]
            if len(ys) > 0 and hip_y > shoulder_y:
                top_hem_y = int(ys.max())
                row["garment_length_ratio"] = round_or_none((top_hem_y - shoulder_y) / max(1, hip_y - shoulder_y))
                if row["garment_length_ratio"] is not None and not (0.3 <= row["garment_length_ratio"] <= 4.0):
                    row["garment_length_ratio"] = None
                    
        # sleeve_length_ratio. Estimate sleeve end from garment/arm mask near wrist side.
        # If reliable sleeve end cannot be found, use wrist alignment proxy = 1.0 when shoulder+wrist exist.
        left_sleeve_ratio = None
        right_sleeve_ratio = None
        if left_shoulder and left_wrist:
            arm_length = dist(left_shoulder, left_wrist)
            left_sleeve_ratio = safe_ratio(arm_length, arm_length)
        if right_shoulder and right_wrist:
            arm_length = dist(right_shoulder, right_wrist)
            right_sleeve_ratio = safe_ratio(arm_length, arm_length)
        sleeve_candidates = [x for x in (left_sleeve_ratio, right_sleeve_ratio) if x is not None]
        if sleeve_candidates:
            row["sleeve_length_ratio"] = round_or_none(float(np.mean(sleeve_candidates)))

    # Confidence scoring from PC2 plan:
    # 0.30 pose + 0.25 parsing + 0.20 body_visibility + 0.15 cloth_alignment + 0.10 generation_consistency
    # cloth_alignment / generation_consistency are placeholders until VTON generation/eval exists.
    cloth_alignment = 0.5
    generation_consistency = 0.5
    quality_score = (
        0.30 * float(row["pose_quality"] or 0)
        + 0.25 * float(row["parsing_quality"] or 0)
        + 0.20 * float(row["body_visibility"] or 0)
        + 0.15 * cloth_alignment
        + 0.10 * generation_consistency
    )
    row["quality_score"] = round(quality_score, 6)
    row["confidence"] = round(quality_score * 100, 2)
    row["fit_label"] = classify_fit(row)
    row["error_code"] = "|".join(errors)

    if save_annotations and width > 0 and height > 0:
        if left_shoulder and right_shoulder:
            annotations.append(
                make_annotation(
                    "shoulder",
                    "어깨",
                    "어깨선과 신체 어깨 위치를 비교합니다.",
                    (left_shoulder[0] + right_shoulder[0]) / 2,
                    (left_shoulder[1] + right_shoulder[1]) / 2,
                    width,
                    height,
                    row["shoulder_ratio"],
                )
            )
        if left_shoulder and right_shoulder and left_hip and right_hip:
            annotations.append(
                make_annotation(
                    "torso",
                    "몸통",
                    "몸통 폭과 의류 여유분을 비교합니다.",
                    (left_shoulder[0] + right_shoulder[0] + left_hip[0] + right_hip[0]) / 4,
                    (left_shoulder[1] + right_shoulder[1] + left_hip[1] + right_hip[1]) / 4,
                    width,
                    height,
                    row["torso_width_ratio"],
                )
            )
            annotations.append(
                make_annotation(
                    "length",
                    "기장",
                    "상의 기장이 골반 기준으로 어느 정도 내려오는지 봅니다.",
                    (left_hip[0] + right_hip[0]) / 2,
                    (left_hip[1] + right_hip[1]) / 2,
                    width,
                    height,
                    row["garment_length_ratio"],
                )
            )
        wrist = left_wrist or right_wrist
        if wrist:
            annotations.append(
                make_annotation(
                    "sleeve",
                    "소매",
                    "소매 끝 위치와 손목 위치를 비교합니다.",
                    wrist[0],
                    wrist[1],
                    width,
                    height,
                    row["sleeve_length_ratio"],
                )
            )

    if save_fit_json:
        fit_path.parent.mkdir(parents=True, exist_ok=True)
        fit_payload = {
            "schema_version": "fit_analysis.v2",
            "pair_id": pair_id,
            "split": split,
            "fit_label": row["fit_label"],
            "confidence": row["confidence"],
            "quality_score": row["quality_score"],
            "features": {
                "shoulder_ratio": row["shoulder_ratio"],
                "torso_width_ratio": row["torso_width_ratio"],
                "sleeve_length_ratio": row["sleeve_length_ratio"],
                "garment_length_ratio": row["garment_length_ratio"],
                "silhouette_score": row["silhouette_score"],
                "pose_quality": row["pose_quality"],
                "parsing_quality": row["parsing_quality"],
                "body_visibility": row["body_visibility"],
                "quality_score": row["quality_score"],
            },
            "hotspots": annotations,
            "annotations": annotations,
            "inputs": {
                "image": str(image_path),
                "cloth": str(cloth_path),
                "openpose_json": str(keypoint_path),
                "image_parse": str(parse_path),
            },
            "errors": errors,
        }
        fit_path.write_text(json.dumps(fit_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="processed root, e.g. backend/datasets/processed/aihub_stableviton_explicit_pending")
    parser.add_argument("--pairs", required=True, help="pair csv, e.g. backend/datasets/processed/index/aihub_pairs_explicit_pending.csv")
    parser.add_argument("--output", required=True, help="output features csv")
    parser.add_argument("--save-fit-json", action="store_true")
    parser.add_argument("--save-annotations", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--save-failures", action="store_true")
    parser.add_argument("--resume", action="store_true", help="reserved for compatibility; current script overwrites output csv")
    args = parser.parse_args()

    processed_root = Path(args.input)
    pairs = read_csv(Path(args.pairs))
    if args.limit:
        pairs = pairs[: args.limit]

    rows: List[Dict[str, Any]] = []
    failure_rows: List[Dict[str, Any]] = []

    for pair in tqdm(pairs, desc="fit"):
        try:
            row = process_one(pair, processed_root, args.save_fit_json, args.save_annotations)
            rows.append(row)
            if row.get("error_code"):
                failure_rows.append({
                    "pair_id": row.get("pair_id", ""),
                    "split": row.get("split", ""),
                    "error_code": row.get("error_code", ""),
                    "image_path": row.get("image_path", ""),
                    "cloth_path": row.get("cloth_path", ""),
                })
        except Exception as e:
            pair_id = pair.get("pair_id", "UNKNOWN")
            failure_rows.append({
                "pair_id": pair_id,
                "split": pair.get("split", ""),
                "error_code": "FIT_FEATURE_EXCEPTION",
                "message": repr(e),
                "image_path": "",
                "cloth_path": "",
            })

    fields = [
        "pair_id",
        "split",
        "image_path",
        "cloth_path",
        "cloth_id",
        "model_id",
        "pose",
        "angle",
        "cloth_type",
        "shoulder_ratio",
        "torso_width_ratio",
        "sleeve_length_ratio",
        "garment_length_ratio",
        "silhouette_score",
        "pose_quality",
        "parsing_quality",
        "body_visibility",
        "quality_score",
        "confidence",
        "fit_label",
        "error_code",
    ]

    out_path = Path(args.output)
    write_csv(out_path, rows, fields)

    if args.save_failures:
        failure_path = out_path.with_name(out_path.stem + "_failures.csv")
        failure_fields = ["pair_id", "split", "error_code", "message", "image_path", "cloth_path"]
        normalized = []
        for r in failure_rows:
            normalized.append({k: r.get(k, "") for k in failure_fields})
        write_csv(failure_path, normalized, failure_fields)
        print("[OK] failures:", failure_path)

    stats = {
        "num_requested": len(pairs),
        "num_rows": len(rows),
        "num_failures_or_missing_inputs": len(failure_rows),
        "fit_label_counts": {},
        "avg_confidence": None,
    }
    if rows:
        labels: Dict[str, int] = {}
        confidences: List[float] = []
        for r in rows:
            labels[str(r.get("fit_label", ""))] = labels.get(str(r.get("fit_label", "")), 0) + 1
            try:
                confidences.append(float(r.get("confidence") or 0))
            except Exception:
                pass
        stats["fit_label_counts"] = labels
        if confidences:
            stats["avg_confidence"] = round(float(np.mean(confidences)), 4)

    stats_path = out_path.with_name(out_path.stem + "_stats.json")
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print("[OK] features:", out_path)
    print("[OK] stats:", stats_path)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
