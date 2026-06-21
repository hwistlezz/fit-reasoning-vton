from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np


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

UPPER_LABELS = {6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18}
ARM_LABELS = {2, 3}
FACE_LABELS = {1}
LOWER_LABELS = {4, 5, 7, 19, 20}
FULL_BODY_LABELS = {21, 22}
FULL_BODY_MARKERS = {"dress", "jumpsuit", "onepiece", "full-body", "full_body"}


@dataclass
class WorkItem:
    pair_id: str
    person_name: str
    split: str = ""
    annotation_json: str = ""
    category: str = ""


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Generate StableVITON-style agnostic-v3.2 and agnostic-mask artifacts "
            "with a broader upper-garment replacement mask."
        )
    )
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--output-root", default=None, help="Defaults to --data-root.")
    ap.add_argument("--metadata", help="Optional chunk metadata CSV for pair_id/category/annotation_json.")
    ap.add_argument("--layout", choices=("auto", "stableviton", "chunk-flat"), default="auto")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force-pair", action="append", default=[])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--gray-value", type=int, default=128)
    ap.add_argument(
        "--fill-mode",
        choices=("gray", "blurred_person", "original_person"),
        default="gray",
        help=(
            "Agnostic fill strategy. 'gray' preserves the legacy hard neutral fill, "
            "'blurred_person' fills the replacement area from a strongly blurred person image, "
            "and 'original_person' is debug-only."
        ),
    )
    ap.add_argument(
        "--mask-source",
        choices=("generated", "existing"),
        default="generated",
        help="Use the generated v2 replacement mask or an existing agnostic-mask from --data-root.",
    )
    ap.add_argument(
        "--skip-mask-output",
        action="store_true",
        help="Write only agnostic-v3.2 images. Useful for fill-only patches that reuse existing masks.",
    )
    ap.add_argument("--blur-radius-scale", type=float, default=0.025)
    ap.add_argument("--blur-radius-min", type=float, default=31.0)
    ap.add_argument("--feather-radius-scale", type=float, default=0.0035)
    ap.add_argument("--feather-radius-min", type=float, default=4.0)
    ap.add_argument("--include-arms", dest="include_arms", action="store_true", default=True)
    ap.add_argument("--exclude-arms", dest="include_arms", action="store_false")
    ap.add_argument("--use-annotation-polygons", dest="use_annotation_polygons", action="store_true", default=True)
    ap.add_argument("--no-annotation-polygons", dest="use_annotation_polygons", action="store_false")
    ap.add_argument("--dilate", type=int, default=115)
    ap.add_argument("--close-kernel", type=int, default=45)
    ap.add_argument("--torso-expand-x", type=float, default=1.20)
    ap.add_argument("--hip-expand-x", type=float, default=0.90)
    ap.add_argument("--top-margin", type=float, default=0.24)
    ap.add_argument("--bottom-margin", type=float, default=0.48)
    ap.add_argument("--arm-scale", type=float, default=0.18)
    ap.add_argument("--arm-circle-scale", type=float, default=0.18)
    ap.add_argument("--target-min-ratio", type=float, default=0.12)
    ap.add_argument("--target-max-ratio", type=float, default=0.28)
    ap.add_argument("--suspicious-max-ratio", type=float, default=0.40)
    ap.add_argument("--adaptive-dilate-step", type=int, default=45)
    ap.add_argument("--adaptive-dilate-iterations", type=int, default=14)
    ap.add_argument("--diagnostics-json", default=None)
    ap.add_argument("--allow-repo-output", action="store_true")
    return ap.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def ensure_output_allowed(path: Path, allow_repo_output: bool) -> None:
    if allow_repo_output:
        return
    if is_relative_to(path, repo_root()):
        raise ValueError(f"Refusing to write generated agnostic artifacts inside repository: {path}")


def detect_layout(data_root: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if (data_root / "test" / "image").is_dir():
        return "stableviton"
    if (data_root / "image").is_dir():
        return "chunk-flat"
    raise ValueError(f"Cannot infer layout for {data_root}")


def normalize_pair_id(value: str | None) -> str:
    return (value or "").strip().upper()


def read_pairs(data_root: Path) -> list[WorkItem]:
    p = data_root / "test_pairs.txt"
    if not p.exists():
        raise FileNotFoundError(p)
    rows: list[WorkItem] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        parts = s.split()
        if len(parts) != 2:
            raise ValueError(f"bad pair line: {s}")
        person_name = parts[0]
        rows.append(WorkItem(pair_id=Path(person_name).stem.upper(), person_name=person_name))
    return rows


def read_metadata(path: Path, limit: int | None, force_pairs: list[str]) -> list[WorkItem]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    forced = {normalize_pair_id(value) for value in force_pairs}
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    by_pair = {normalize_pair_id(row.get("pair_id")): row for row in rows}
    for pair_id in forced:
        row = by_pair.get(pair_id)
        if row and pair_id not in seen:
            selected.append(row)
            seen.add(pair_id)
    for row in rows:
        if limit is not None and len(selected) >= limit:
            break
        pair_id = normalize_pair_id(row.get("pair_id"))
        if not pair_id or pair_id in seen:
            continue
        selected.append(row)
        seen.add(pair_id)
    return [
        WorkItem(
            pair_id=normalize_pair_id(row.get("pair_id")),
            person_name=f"{normalize_pair_id(row.get('pair_id'))}.jpg",
            split=row.get("split", ""),
            annotation_json=row.get("annotation_json", ""),
            category=row.get("category", ""),
        )
        for row in selected
    ]


def select_items(items: list[WorkItem], limit: int | None, force_pairs: list[str]) -> list[WorkItem]:
    if limit is None:
        return items
    forced = {normalize_pair_id(value) for value in force_pairs}
    selected: list[WorkItem] = []
    seen: set[str] = set()
    for item in items:
        if item.pair_id in forced and item.pair_id not in seen:
            selected.append(item)
            seen.add(item.pair_id)
    for item in items:
        if len(selected) >= limit:
            break
        if item.pair_id in seen:
            continue
        selected.append(item)
        seen.add(item.pair_id)
    return selected


def load_items(args: argparse.Namespace, data_root: Path) -> list[WorkItem]:
    if args.metadata:
        return read_metadata(Path(args.metadata), args.limit, args.force_pair)
    return select_items(read_pairs(data_root), args.limit, args.force_pair)


def candidate_paths(base: Path, stem: str, exts: tuple[str, ...]) -> list[Path]:
    return [base / f"{stem}{ext}" for ext in exts]


def find_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def image_path(data_root: Path, layout: str, item: WorkItem) -> Path | None:
    if layout == "stableviton":
        return find_existing([data_root / "test" / "image" / item.person_name])
    return find_existing(candidate_paths(data_root / "image", item.pair_id, (".jpg", ".jpeg", ".png")))


def keypoint_path(data_root: Path, layout: str, item: WorkItem) -> Path | None:
    stem = Path(item.person_name).stem if layout == "stableviton" else item.pair_id
    if layout == "stableviton":
        base = data_root / "test" / "openpose-json"
        return find_existing([base / f"{stem}_keypoints.json", base / f"{stem}.json"])
    base = data_root / "openpose-json"
    return find_existing([base / f"{stem}.json", base / f"{stem}_keypoints.json"])


def output_paths(output_root: Path, layout: str, item: WorkItem) -> tuple[Path, Path]:
    if layout == "stableviton":
        image_out = output_root / "test" / "agnostic-v3.2" / item.person_name
        mask_out = output_root / "test" / "agnostic-mask" / f"{Path(item.person_name).stem}_mask.png"
        return image_out, mask_out
    return output_root / "agnostic-v3.2" / f"{item.pair_id}.jpg", output_root / "agnostic-mask" / f"{item.pair_id}.png"


def existing_mask_path(data_root: Path, layout: str, item: WorkItem) -> Path | None:
    if layout == "stableviton":
        stem = Path(item.person_name).stem
        base = data_root / "test" / "agnostic-mask"
        return find_existing([base / f"{stem}_mask.png", base / f"{stem}.png"])
    return find_existing(candidate_paths(data_root / "agnostic-mask", item.pair_id, (".png", ".jpg", ".jpeg")))


def resolve_annotation_path(value: str) -> Path | None:
    if not value:
        return None
    path = Path(value)
    candidates = [path]
    if not path.is_absolute():
        candidates.extend([repo_root() / value, Path.cwd() / value])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def load_keypoints(path: Path | None) -> dict[str, tuple[float, float, float]]:
    if not path or not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
    people = obj.get("people") or []
    if not people:
        return {}
    arr = people[0].get("pose_keypoints_2d") or []
    out: dict[str, tuple[float, float, float]] = {}
    for name, idx in OPENPOSE.items():
        j = idx * 3
        if j + 2 < len(arr):
            x, y, c = float(arr[j]), float(arr[j + 1]), float(arr[j + 2])
            if x > 0 and y > 0 and c > 0.05:
                out[name] = (x, y, c)
    return out


def xy(kps: dict[str, tuple[float, float, float]], name: str) -> tuple[float, float] | None:
    v = kps.get(name)
    if not v:
        return None
    return float(v[0]), float(v[1])


def fill_poly(mask: np.ndarray, pts: list[tuple[float, float]]) -> None:
    points = np.array([[int(round(x)), int(round(y))] for x, y in pts], dtype=np.int32)
    cv2.fillPoly(mask, [points], 255)


def fill_segmentation(mask: np.ndarray, segmentation: dict[str, Any], labels: set[int]) -> int:
    polygons = 0
    for key, items in segmentation.items():
        try:
            class_id = int(key)
        except ValueError:
            continue
        if class_id not in labels or not isinstance(items, list):
            continue
        for poly in items:
            if not isinstance(poly, list) or len(poly) < 6:
                continue
            pts = list(zip(poly[0::2], poly[1::2]))
            fill_poly(mask, pts)
            polygons += 1
    return polygons


def annotation_masks(
    annotation_path: Path | None,
    shape: tuple[int, int, int],
    category: str,
) -> tuple[np.ndarray, np.ndarray, int]:
    h, w = shape[:2]
    target = np.zeros((h, w), dtype=np.uint8)
    preserve = np.zeros((h, w), dtype=np.uint8)
    if not annotation_path:
        return target, preserve, 0
    try:
        data = json.loads(annotation_path.read_text(encoding="utf-8"))
        annotation = (data.get("annotation") or [{}])[0]
        segmentation = annotation.get("segmentation") or {}
    except Exception:
        return target, preserve, 0

    category_text = (category or "").lower()
    labels = set(UPPER_LABELS)
    if any(marker in category_text for marker in FULL_BODY_MARKERS):
        labels |= FULL_BODY_LABELS
    polygons = fill_segmentation(target, segmentation, labels)
    fill_segmentation(preserve, segmentation, FACE_LABELS | LOWER_LABELS)
    return target, preserve, polygons


def draw_capsule(mask: np.ndarray, a: tuple[float, float] | None, b: tuple[float, float] | None, radius: int) -> None:
    if a is None or b is None:
        return
    axy = (int(round(a[0])), int(round(a[1])))
    bxy = (int(round(b[0])), int(round(b[1])))
    cv2.line(mask, axy, bxy, 255, radius * 2)
    cv2.circle(mask, axy, radius, 255, -1)
    cv2.circle(mask, bxy, radius, 255, -1)


def blend_point(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return (a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t)


def clear_circle(mask: np.ndarray, center: tuple[float, float] | None, radius: int) -> None:
    if center is None:
        return
    cv2.circle(mask, (int(round(center[0])), int(round(center[1]))), max(1, radius), 0, -1)


def fill_holes(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape[:2]
    flood = mask.copy()
    flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    cv2.floodFill(flood, flood_mask, (0, 0), 255)
    holes = cv2.bitwise_not(flood)
    return cv2.bitwise_or(mask, holes)


def mask_ratio(mask: np.ndarray) -> float:
    return float(np.count_nonzero(mask)) / float(mask.size)


def keypoint_preserve_mask(shape: tuple[int, int, int], kps: dict[str, tuple[float, float, float]], shoulder_width: float) -> np.ndarray:
    h, w = shape[:2]
    preserve = np.zeros((h, w), dtype=np.uint8)
    face_points = [xy(kps, name) for name in ("nose", "left_eye", "right_eye", "left_ear", "right_ear")]
    face_points = [pt for pt in face_points if pt is not None]
    if face_points:
        xs = [pt[0] for pt in face_points]
        ys = [pt[1] for pt in face_points]
        center = (sum(xs) / len(xs), sum(ys) / len(ys))
        clear_radius = int(max(28, shoulder_width * 0.34))
        cv2.circle(preserve, (int(center[0]), int(center[1])), clear_radius, 255, -1)
    hand_radius = int(max(22, shoulder_width * 0.16))
    clear_circle(preserve, xy(kps, "left_wrist"), hand_radius)
    clear_circle(preserve, xy(kps, "right_wrist"), hand_radius)
    return preserve


def make_openpose_mask(
    image_shape: tuple[int, int, int],
    kps: dict[str, tuple[float, float, float]],
    *,
    include_arms: bool,
    torso_expand_x: float,
    hip_expand_x: float,
    top_margin: float,
    bottom_margin: float,
    arm_scale: float,
    arm_circle_scale: float,
) -> tuple[np.ndarray, dict[str, Any]]:
    h, w = image_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    ls = xy(kps, "left_shoulder")
    rs = xy(kps, "right_shoulder")
    lh = xy(kps, "left_hip")
    rh = xy(kps, "right_hip")
    neck = xy(kps, "neck")
    if not all([ls, rs, lh, rh]):
        return mask, {"openpose_torso": False}

    shoulder_width = max(20.0, float(np.linalg.norm(np.array(ls) - np.array(rs))))
    shoulder_y = (ls[1] + rs[1]) / 2.0
    hip_y = (lh[1] + rh[1]) / 2.0
    torso_h = max(35.0, hip_y - shoulder_y)
    top_y = shoulder_y - torso_h * top_margin
    if neck is not None:
        top_y = min(top_y, neck[1] - torso_h * 0.08)
    top_y = max(0.0, top_y)
    bottom_y = min(h - 1.0, hip_y + torso_h * bottom_margin)

    sx = shoulder_width * torso_expand_x
    hx = shoulder_width * hip_expand_x
    left_top = (max(0.0, ls[0] - sx), top_y)
    right_top = (min(w - 1.0, rs[0] + sx), top_y)
    right_mid = (min(w - 1.0, rs[0] + sx * 0.96), shoulder_y + torso_h * 0.30)
    right_bottom = (min(w - 1.0, rh[0] + hx), bottom_y)
    left_bottom = (max(0.0, lh[0] - hx), bottom_y)
    left_mid = (max(0.0, ls[0] - sx * 0.96), shoulder_y + torso_h * 0.30)
    fill_poly(mask, [left_top, right_top, right_mid, right_bottom, left_bottom, left_mid])

    chest_top_y = max(0.0, top_y - torso_h * 0.04)
    fill_poly(
        mask,
        [
            (max(0.0, ls[0] - sx * 0.70), chest_top_y),
            (min(w - 1.0, rs[0] + sx * 0.70), chest_top_y),
            (min(w - 1.0, rs[0] + sx * 0.50), shoulder_y + torso_h * 0.12),
            (max(0.0, ls[0] - sx * 0.50), shoulder_y + torso_h * 0.12),
        ],
    )

    if include_arms:
        arm_r = int(max(16, shoulder_width * arm_scale))
        joint_r = int(max(16, shoulder_width * arm_circle_scale))
        for shoulder_name, elbow_name, wrist_name in (
            ("left_shoulder", "left_elbow", "left_wrist"),
            ("right_shoulder", "right_elbow", "right_wrist"),
        ):
            shoulder = xy(kps, shoulder_name)
            elbow = xy(kps, elbow_name)
            wrist = xy(kps, wrist_name)
            if elbow is not None:
                draw_capsule(mask, shoulder, elbow, arm_r)
                clear_circle(mask, elbow, 0)
                cv2.circle(mask, (int(round(elbow[0])), int(round(elbow[1]))), joint_r, 255, -1)
            if elbow is not None and wrist is not None:
                sleeve_end = blend_point(elbow, wrist, 0.72)
                draw_capsule(mask, elbow, sleeve_end, arm_r)
            elif shoulder is not None and wrist is not None:
                sleeve_end = blend_point(shoulder, wrist, 0.58)
                draw_capsule(mask, shoulder, sleeve_end, arm_r)

        left_root = blend_point(ls, lh, 0.18)
        right_root = blend_point(rs, rh, 0.18)
        fill_poly(mask, [left_top, (ls[0], shoulder_y), left_root, left_mid])
        fill_poly(mask, [(rs[0], shoulder_y), right_top, right_mid, right_root])

    lower_clip = int(min(h - 1, hip_y + torso_h * 0.50))
    mask[lower_clip:, :] = 0
    return mask, {
        "openpose_torso": True,
        "shoulder_width": shoulder_width,
        "torso_height": torso_h,
        "lower_clip_y": lower_clip,
    }


def build_replacement_mask(
    image_shape: tuple[int, int, int],
    kps: dict[str, tuple[float, float, float]],
    annotation_path: Path | None,
    category: str,
    args: argparse.Namespace,
) -> tuple[np.ndarray, dict[str, Any]]:
    openpose_mask, info = make_openpose_mask(
        image_shape,
        kps,
        include_arms=args.include_arms,
        torso_expand_x=args.torso_expand_x,
        hip_expand_x=args.hip_expand_x,
        top_margin=args.top_margin,
        bottom_margin=args.bottom_margin,
        arm_scale=args.arm_scale,
        arm_circle_scale=args.arm_circle_scale,
    )
    annotation_target, annotation_preserve, polygon_count = (
        annotation_masks(annotation_path, image_shape, category)
        if args.use_annotation_polygons
        else (np.zeros(image_shape[:2], dtype=np.uint8), np.zeros(image_shape[:2], dtype=np.uint8), 0)
    )
    mask = cv2.bitwise_or(openpose_mask, annotation_target)

    shoulder_width = float(info.get("shoulder_width") or max(image_shape[1] * 0.08, 50.0))
    preserve = cv2.bitwise_or(annotation_preserve, keypoint_preserve_mask(image_shape, kps, shoulder_width))

    if args.close_kernel > 1:
        close_k = np.ones((args.close_kernel, args.close_kernel), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_k)
    mask = fill_holes(mask)

    if args.dilate > 0:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (args.dilate, args.dilate))
        mask = cv2.dilate(mask, kernel, iterations=1)
    mask[preserve > 0] = 0

    adaptive_iterations = 0
    if args.adaptive_dilate_step > 0:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (args.adaptive_dilate_step, args.adaptive_dilate_step),
        )
        while mask_ratio(mask) < args.target_min_ratio and adaptive_iterations < args.adaptive_dilate_iterations:
            grown = cv2.dilate(mask, kernel, iterations=1)
            grown[preserve > 0] = 0
            if mask_ratio(grown) > args.suspicious_max_ratio:
                break
            mask = grown
            adaptive_iterations += 1

    mask = (mask > 0).astype(np.uint8) * 255
    ratio = mask_ratio(mask)
    info.update(
        {
            "annotation_polygon_count": polygon_count,
            "annotation_used": polygon_count > 0,
            "mask_ratio": ratio,
            "adaptive_dilate_iterations": adaptive_iterations,
            "target_min_ratio": args.target_min_ratio,
            "target_max_ratio": args.target_max_ratio,
            "suspicious_small": ratio < 0.08,
            "suspicious_large": ratio > args.suspicious_max_ratio,
        }
    )
    return mask, info


def apply_neutral_fill(image: np.ndarray, mask: np.ndarray, gray_value: int) -> np.ndarray:
    agnostic = image.copy()
    value = max(0, min(255, int(gray_value)))
    agnostic[mask > 0] = (value, value, value)
    return agnostic


def apply_blurred_person_fill(image: np.ndarray, mask: np.ndarray, args: argparse.Namespace) -> np.ndarray:
    h, w = image.shape[:2]
    min_dim = max(1, min(h, w))
    blur_sigma = max(float(args.blur_radius_min), float(min_dim) * float(args.blur_radius_scale))
    feather_sigma = max(float(args.feather_radius_min), float(min_dim) * float(args.feather_radius_scale))
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=blur_sigma, sigmaY=blur_sigma)
    alpha = (mask > 0).astype(np.float32)
    if feather_sigma > 0:
        alpha = cv2.GaussianBlur(alpha, (0, 0), sigmaX=feather_sigma, sigmaY=feather_sigma)
        alpha[mask <= 0] = 0.0
    alpha = np.clip(alpha, 0.0, 1.0)[..., None]
    agnostic = image.astype(np.float32) * (1.0 - alpha) + blurred.astype(np.float32) * alpha
    return np.clip(agnostic, 0, 255).astype(np.uint8)


def apply_fill(image: np.ndarray, mask: np.ndarray, args: argparse.Namespace) -> np.ndarray:
    if args.fill_mode == "gray":
        return apply_neutral_fill(image, mask, args.gray_value)
    if args.fill_mode == "blurred_person":
        return apply_blurred_person_fill(image, mask, args)
    if args.fill_mode == "original_person":
        return image.copy()
    raise ValueError(f"Unsupported fill mode: {args.fill_mode}")


def load_existing_mask(mask_path: Path | None, image_shape: tuple[int, int, int]) -> tuple[np.ndarray | None, dict[str, Any]]:
    info: dict[str, Any] = {
        "mask_source": "existing",
        "existing_mask_path": str(mask_path) if mask_path else "",
    }
    if not mask_path:
        info["reason"] = "missing_existing_agnostic_mask"
        return None, info
    mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
    if mask is None:
        info["reason"] = "existing_agnostic_mask_read_failed"
        return None, info
    if mask.shape[:2] != image_shape[:2]:
        info.update(
            {
                "reason": "existing_agnostic_mask_size_mismatch",
                "image_size": [int(image_shape[1]), int(image_shape[0])],
                "mask_size": [int(mask.shape[1]), int(mask.shape[0])],
            }
        )
        return None, info
    mask = (mask > 0).astype(np.uint8) * 255
    ratio = mask_ratio(mask)
    info.update(
        {
            "reason": "",
            "mask_ratio": ratio,
            "suspicious_small": ratio < 0.08,
            "suspicious_large": ratio > 0.40,
        }
    )
    return mask, info


def process_one(
    data_root: Path,
    output_root: Path,
    layout: str,
    item: WorkItem,
    args: argparse.Namespace,
) -> dict[str, Any]:
    img_path = image_path(data_root, layout, item)
    kp_path = keypoint_path(data_root, layout, item)
    annotation_path = resolve_annotation_path(item.annotation_json)
    detail: dict[str, Any] = {
        "pair_id": item.pair_id,
        "person_name": item.person_name,
        "category": item.category,
        "image_path": str(img_path) if img_path else "",
        "openpose_path": str(kp_path) if kp_path else "",
        "annotation_path": str(annotation_path) if annotation_path else "",
        "status": "failed",
        "reason": "",
    }
    if not img_path:
        detail["reason"] = "missing_image"
        return detail
    if args.mask_source == "generated" and not kp_path:
        detail["reason"] = "missing_openpose_json"
        return detail
    image = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
    if image is None:
        detail["reason"] = "image_read_failed"
        return detail
    kps = load_keypoints(kp_path) if kp_path else {}
    if args.mask_source == "generated" and not kps:
        detail["reason"] = "no_valid_openpose_keypoints"
        return detail
    if args.mask_source == "existing":
        mask, mask_info = load_existing_mask(existing_mask_path(data_root, layout, item), image.shape)
        if mask is None:
            detail["reason"] = mask_info.get("reason", "existing_mask_failed")
            detail.update(mask_info)
            return detail
    else:
        mask, mask_info = build_replacement_mask(image.shape, kps, annotation_path, item.category, args)
        mask_info["mask_source"] = "generated"
    if int(mask.sum()) <= 0:
        detail["reason"] = "empty_mask"
        return detail

    agnostic = apply_fill(image, mask, args)
    out_img, out_mask = output_paths(output_root, layout, item)
    out_img.parent.mkdir(parents=True, exist_ok=True)
    ok_img = cv2.imwrite(str(out_img), agnostic)
    ok_mask = True
    if not args.skip_mask_output:
        out_mask.parent.mkdir(parents=True, exist_ok=True)
        ok_mask = cv2.imwrite(str(out_mask), mask)
    if not ok_img or not ok_mask:
        detail["reason"] = "write_failed"
        return detail
    detail.update(mask_info)
    detail.update(
        {
            "status": "ok",
            "reason": "",
            "fill_mode": args.fill_mode,
            "agnostic_path": str(out_img),
            "mask_path": "" if args.skip_mask_output else str(out_mask),
            "mask_output_skipped": bool(args.skip_mask_output),
        }
    )
    return detail


def write_diagnostics(path: Path | None, details: list[dict[str, Any]], data_root: Path, output_root: Path) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    ok = [item for item in details if item.get("status") == "ok"]
    ratios = [float(item["mask_ratio"]) for item in ok if "mask_ratio" in item]
    summary = {
        "data_root": str(data_root),
        "output_root": str(output_root),
        "fill_modes": sorted({str(item.get("fill_mode")) for item in ok if item.get("fill_mode")}),
        "mask_sources": sorted({str(item.get("mask_source")) for item in ok if item.get("mask_source")}),
        "requested": len(details),
        "generated": len(ok),
        "failed": len(details) - len(ok),
        "mask_ratio": {
            "min": min(ratios) if ratios else None,
            "median": float(np.median(ratios)) if ratios else None,
            "mean": float(np.mean(ratios)) if ratios else None,
            "max": max(ratios) if ratios else None,
        },
        "too_small_lt_0_08": sum(1 for item in ok if float(item.get("mask_ratio", 0)) < 0.08),
        "too_small_lt_0_10": sum(1 for item in ok if float(item.get("mask_ratio", 0)) < 0.10),
        "too_large_gt_0_40": sum(1 for item in ok if float(item.get("mask_ratio", 0)) > 0.40),
        "details": details,
    }
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    data_root = Path(args.data_root).expanduser()
    output_root = Path(args.output_root).expanduser() if args.output_root else data_root
    layout = detect_layout(data_root, args.layout)
    ensure_output_allowed(output_root, args.allow_repo_output)
    items = load_items(args, data_root)
    if not items:
        print("[ERROR] no work items")
        return 1

    diagnostics: list[dict[str, Any]] = []
    ok = 0
    fail = 0
    for item in items:
        detail = process_one(data_root, output_root, layout, item, args)
        diagnostics.append(detail)
        if detail["status"] == "ok":
            ok += 1
            print("[OK]", item.pair_id, f"mask_ratio={detail.get('mask_ratio'):.4f}")
        else:
            fail += 1
            print("[WARN]", item.pair_id, detail.get("reason", "failed"))

    diagnostics_path = Path(args.diagnostics_json) if args.diagnostics_json else None
    write_diagnostics(diagnostics_path, diagnostics, data_root, output_root)
    print()
    print("Summary:")
    print("layout=", layout)
    print("requested=", len(items))
    print("generated=", ok)
    print("failed=", fail)
    print("data_root=", data_root)
    print("output_root=", output_root)
    if diagnostics_path:
        print("diagnostics_json=", diagnostics_path)
    return 0 if ok > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
