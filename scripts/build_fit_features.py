from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


FEATURE_COLUMNS = [
    "case_id",
    "model_id",
    "cloth_id",
    "pose",
    "angle",
    "cloth_type",
    "cloth_fit",
    "shoulder_ratio",
    "torso_width_ratio",
    "sleeve_length_ratio",
    "garment_length_ratio",
    "cloth_area_ratio",
    "body_visibility_score",
    "pose_quality_score",
    "segmentation_quality_score",
    "confidence_score",
    "fit_label",
]
UPPER_GARMENT_CLASSES = {
    "Top",
    "T-shirt",
    "shirts",
    "Sweater",
    "Blouse",
    "Coat",
    "jacket",
    "Jumper",
    "Padding",
    "vest",
    "Cardigan",
}
REQUIRED_KEYPOINTS = [
    "Left_shoulder",
    "Right_shoulder",
    "Left_wrist",
    "Right_wrist",
    "Left_hip",
    "Right_hip",
]
SKELETON_WARNING = (
    "AIHub feature extraction skeleton 결과입니다. 실제 fit score 기준은 아직 확정되지 않았습니다."
)


Point = dict[str, float]
BBox = tuple[float, float, float, float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build placeholder fit features from one AIHub wearing annotation JSON."
    )
    parser.add_argument("--input", required=True, help="AIHub wearing annotation JSON path.")
    parser.add_argument("--out-features", required=True, help="Path to save features.csv.")
    parser.add_argument("--out-fit-result", required=True, help="Path to save fit_result.json.")
    parser.add_argument("--case-id", default=None, help="Output case_id. Defaults to info[0].id.")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"input file does not exist: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"failed to parse JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("input JSON must be an object.")
    return payload


def first_object(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, list) or not value or not isinstance(value[0], dict):
        raise ValueError(f"input JSON must contain {key}[0] object.")
    return value[0]


def parse_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def visible(point: Point | None) -> bool:
    return point is not None and point["visibility"] > 0


def distance(a: Point | None, b: Point | None) -> float | None:
    if not visible(a) or not visible(b):
        return None
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def parse_keypoints(
    keypoint_classes: Any,
    keypoint_values: Any,
    warnings: list[str],
) -> dict[str, Point]:
    if not isinstance(keypoint_classes, list) or not all(isinstance(name, str) for name in keypoint_classes):
        raise ValueError("info[0].keypoint_class must be a list of strings.")
    if not isinstance(keypoint_values, list):
        raise ValueError("annotation[0].keypoint must be a list.")

    expected_values = len(keypoint_classes) * 3
    if len(keypoint_values) < expected_values:
        warnings.append("keypoint 길이가 class 수 * 3보다 짧아 가능한 keypoint만 파싱했습니다.")

    keypoints: dict[str, Point] = {}
    for index, name in enumerate(keypoint_classes):
        offset = index * 3
        if offset + 2 >= len(keypoint_values):
            break

        x = parse_float(keypoint_values[offset])
        y = parse_float(keypoint_values[offset + 1])
        visibility_value = parse_float(keypoint_values[offset + 2])
        if visibility_value <= 0:
            continue

        keypoints[name] = {"x": x, "y": y, "visibility": visibility_value}

    return keypoints


def polygon_bbox(polygon: Any) -> BBox | None:
    if not isinstance(polygon, list) or len(polygon) < 6:
        return None
    points = [parse_float(value, default=math.nan) for value in polygon]
    if any(math.isnan(value) for value in points):
        return None

    xs = points[0::2]
    ys = points[1::2]
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def merge_bbox(current: BBox | None, next_bbox: BBox | None) -> BBox | None:
    if next_bbox is None:
        return current
    if current is None:
        return next_bbox
    return (
        min(current[0], next_bbox[0]),
        min(current[1], next_bbox[1]),
        max(current[2], next_bbox[2]),
        max(current[3], next_bbox[3]),
    )


def bbox_width(bbox: BBox | None) -> float | None:
    if bbox is None:
        return None
    return max(0.0, bbox[2] - bbox[0])


def bbox_height(bbox: BBox | None) -> float | None:
    if bbox is None:
        return None
    return max(0.0, bbox[3] - bbox[1])


def bbox_area(bbox: BBox | None) -> float | None:
    width = bbox_width(bbox)
    height = bbox_height(bbox)
    if width is None or height is None:
        return None
    return width * height


def class_name_for_segmentation_id(segmentation_classes: list[str], class_id: str) -> str | None:
    try:
        class_index = int(class_id)
    except ValueError:
        return None
    if 0 <= class_index < len(segmentation_classes):
        return segmentation_classes[class_index]
    return None


def upper_garment_bbox(
    segmentation_classes: Any,
    segmentation: Any,
    warnings: list[str],
) -> BBox | None:
    if not isinstance(segmentation_classes, list) or not all(
        isinstance(name, str) for name in segmentation_classes
    ):
        raise ValueError("info[0].segmentation_class must be a list of strings.")
    if not isinstance(segmentation, dict) or not segmentation:
        warnings.append("segmentation이 비어 있어 segmentation_quality_score=0.0으로 계산했습니다.")
        return None

    bbox: BBox | None = None
    unmatched_ids: list[str] = []
    for class_id, polygons in segmentation.items():
        class_name = class_name_for_segmentation_id(segmentation_classes, str(class_id))
        if class_name is None:
            unmatched_ids.append(str(class_id))
            continue
        if class_name not in UPPER_GARMENT_CLASSES:
            continue
        if not isinstance(polygons, list):
            continue
        for polygon in polygons:
            bbox = merge_bbox(bbox, polygon_bbox(polygon))

    if unmatched_ids and bbox is None:
        warnings.append(
            "upper garment segmentation class id를 segmentation_class index와 매칭하지 못했습니다: "
            + ", ".join(unmatched_ids)
        )
    return bbox


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def average(values: list[float]) -> float | None:
    valid_values = [value for value in values if value is not None]
    if not valid_values:
        return None
    return sum(valid_values) / len(valid_values)


def round_optional(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def csv_value(value: Any) -> Any:
    if value is None:
        return ""
    return value


def clamp_int(value: float, lower: int = 0, upper: int = 100) -> int:
    return max(lower, min(upper, round(value)))


def confidence_level(score: int) -> str:
    if score < 50:
        return "low"
    if score < 80:
        return "medium"
    return "high"


def fit_label(confidence_score: int, shoulder_ratio: float | None) -> str:
    if confidence_score < 50:
        return "low_confidence"
    if shoulder_ratio is None:
        return "unknown"
    if shoulder_ratio < 0.9:
        return "slim"
    if shoulder_ratio <= 1.15:
        return "regular"
    if shoulder_ratio <= 1.35:
        return "loose"
    return "oversized"


def percent(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round(value / total * 100, 2)


def build_features(payload: dict[str, Any], case_id_override: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    info = first_object(payload, "info")
    annotation = first_object(payload, "annotation")
    image = info.get("image")
    if not isinstance(image, dict):
        raise ValueError("info[0].image must be an object.")

    warnings = [SKELETON_WARNING]
    image_width = parse_float(image.get("width"))
    image_height = parse_float(image.get("height"))
    if image_width <= 0 or image_height <= 0:
        warnings.append("image width/height가 없거나 0이어서 일부 ratio를 계산하지 못할 수 있습니다.")

    keypoints = parse_keypoints(info.get("keypoint_class"), annotation.get("keypoint"), warnings)
    garment_bbox = upper_garment_bbox(info.get("segmentation_class"), annotation.get("segmentation"), warnings)
    garment_width = bbox_width(garment_bbox)
    garment_height = bbox_height(garment_bbox)
    garment_area = bbox_area(garment_bbox)
    image_area = image_width * image_height if image_width > 0 and image_height > 0 else None

    shoulder_width = distance(keypoints.get("Left_shoulder"), keypoints.get("Right_shoulder"))
    hip_width = distance(keypoints.get("Left_hip"), keypoints.get("Right_hip"))
    left_arm_length = distance(keypoints.get("Left_shoulder"), keypoints.get("Left_wrist"))
    right_arm_length = distance(keypoints.get("Right_shoulder"), keypoints.get("Right_wrist"))
    arm_length = average([value for value in [left_arm_length, right_arm_length] if value is not None])

    shoulder_ratio = round_optional(safe_ratio(garment_width, shoulder_width))
    torso_width_ratio = round_optional(safe_ratio(garment_width, hip_width))
    sleeve_length_ratio = round_optional(safe_ratio(arm_length, image_height))
    garment_length_ratio = round_optional(safe_ratio(garment_height, image_height))
    cloth_area_ratio = round_optional(safe_ratio(garment_area, image_area))
    visible_required_count = sum(1 for name in REQUIRED_KEYPOINTS if visible(keypoints.get(name)))
    pose_quality_score = round_optional(visible_required_count / len(REQUIRED_KEYPOINTS)) or 0.0
    segmentation_quality_score = 1.0 if garment_bbox is not None else 0.0
    body_visibility_score = pose_quality_score
    confidence_score = clamp_int(50 + pose_quality_score * 25 + segmentation_quality_score * 25)
    label = fit_label(confidence_score, shoulder_ratio)

    case_id = case_id_override or str(info.get("id", ""))
    feature_row = {
        "case_id": case_id,
        "model_id": str(info.get("model_id", "")),
        "cloth_id": str(info.get("cloth_id", "")),
        "pose": str(image.get("pose", "")),
        "angle": str(image.get("angle", "")),
        "cloth_type": "",
        "cloth_fit": "",
        "shoulder_ratio": shoulder_ratio,
        "torso_width_ratio": torso_width_ratio,
        "sleeve_length_ratio": sleeve_length_ratio,
        "garment_length_ratio": garment_length_ratio,
        "cloth_area_ratio": cloth_area_ratio,
        "body_visibility_score": round_optional(body_visibility_score),
        "pose_quality_score": round_optional(pose_quality_score),
        "segmentation_quality_score": round_optional(segmentation_quality_score),
        "confidence_score": confidence_score,
        "fit_label": label,
    }
    fit_result = {
        "case_id": case_id,
        "source": "aihub_feature_skeleton",
        "confidence": {
            "score": confidence_score,
            "level": confidence_level(confidence_score),
            "warnings": warnings,
        },
        "fit": {
            "label": label,
            "scores": {
                "shoulder_ratio": shoulder_ratio,
                "torso_width_ratio": torso_width_ratio,
                "sleeve_length_ratio": sleeve_length_ratio,
                "garment_length_ratio": garment_length_ratio,
            },
            "explanations": [
                "keypoint와 segmentation 기반 placeholder feature로 생성한 fit 결과입니다."
            ],
        },
        "annotations": build_annotations(keypoints, image_width, image_height, shoulder_ratio),
    }
    return feature_row, fit_result


def build_annotations(
    keypoints: dict[str, Point],
    image_width: float,
    image_height: float,
    shoulder_ratio: float | None,
) -> list[dict[str, Any]]:
    left_shoulder = keypoints.get("Left_shoulder")
    right_shoulder = keypoints.get("Right_shoulder")
    if visible(left_shoulder) and visible(right_shoulder):
        x = (left_shoulder["x"] + right_shoulder["x"]) / 2
        y = (left_shoulder["y"] + right_shoulder["y"]) / 2
    else:
        x = image_width / 2 if image_width > 0 else 0.0
        y = image_height * 0.3 if image_height > 0 else 0.0

    severity = "low" if shoulder_ratio is not None else "medium"
    message = "어깨선 기준 feature 확인이 필요한 placeholder annotation입니다."
    if shoulder_ratio is None:
        message = "어깨선 ratio를 계산하지 못해 확인이 필요한 placeholder annotation입니다."

    return [
        {
            "part": "shoulder",
            "x": percent(x, image_width),
            "y": percent(y, image_height),
            "severity": severity,
            "message": message,
        }
    ]


def write_features_csv(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FEATURE_COLUMNS)
        writer.writeheader()
        writer.writerow({column: csv_value(row[column]) for column in FEATURE_COLUMNS})


def write_fit_result(path: Path, fit_result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fit_result, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    out_features = Path(args.out_features)
    out_fit_result = Path(args.out_fit_result)

    try:
        payload = load_json(input_path)
        feature_row, fit_result = build_features(payload, args.case_id)
        write_features_csv(out_features, feature_row)
        write_fit_result(out_fit_result, fit_result)
    except ValueError as exc:
        raise SystemExit(f"[ERROR] {exc}") from exc

    print("AIHub fit feature extraction:")
    print(f"[OK] input: {input_path}")
    print(f"[OK] case_id: {feature_row['case_id']}")
    print(f"[OK] out_features: {out_features}")
    print(f"[OK] out_fit_result: {out_fit_result}")
    print(f"[OK] confidence_score: {feature_row['confidence_score']}")
    print(f"[OK] fit_label: {feature_row['fit_label']}")


if __name__ == "__main__":
    main()
