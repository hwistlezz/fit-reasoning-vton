from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping

try:
    import numpy as np
    from PIL import Image
except Exception:  # pragma: no cover - reported by score output at runtime
    Image = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]


ONLINE_VISUAL_PROXY_SCHEMA_VERSION = "online_candidate_visual_proxy.v1"
ONLINE_VISUAL_SCORE_SOURCE = "online_visual_proxy"
ONLINE_VISUAL_SCORE_MODE = "production_proxy_v1"

COMPONENT_WEIGHTS = {
    "image_readability": 0.10,
    "dimension_exposure_sanity": 0.10,
    "artifact_score": 0.15,
    "cloth_mask_alignment_proxy": 0.15,
    "agnostic_boundary_consistency": 0.15,
    "body_preservation_proxy": 0.15,
    "pose_visibility_sanity": 0.10,
    "garment_boundary_proxy": 0.10,
}


def score_online_candidate_visual_proxy(
    candidate: Mapping[str, Any],
    *,
    artifact_root: str | Path | None = None,
) -> dict[str, Any]:
    """Score a generated candidate with production-safe request-time artifacts only.

    This scorer intentionally does not read worn, fit, target, or other ground-truth
    reference images. It is a heuristic visual guardrail for candidate reranking,
    not a calibrated fit-quality model.
    """

    warnings: list[str] = []
    if Image is None or np is None:
        return _unavailable("image_libraries_unavailable")

    image_path = _path_or_none(candidate.get("image_path") or candidate.get("image_url"))
    if image_path is None:
        return _unavailable("candidate_image_path_missing")
    if not image_path.is_file():
        return _unavailable("candidate_image_missing", image_path=image_path)

    candidate_image = _load_rgb_array(image_path)
    if candidate_image is None:
        return _unavailable("candidate_image_load_failed", image_path=image_path)

    pair_id = _as_string(candidate.get("pair_id"))
    root = _artifact_root(candidate, artifact_root)
    artifacts = _resolve_artifacts(candidate, pair_id=pair_id, artifact_root=root)
    person_image = _load_optional_rgb(artifacts.get("person_path"), candidate_image)
    cloth_image = _load_optional_rgb(artifacts.get("cloth_path"), None)
    agnostic_mask = _load_optional_mask(artifacts.get("agnostic_mask_path"), candidate_image.shape[:2])
    cloth_mask = _load_optional_mask(artifacts.get("cloth_mask_path"), None)
    parse_mask = _load_optional_mask(artifacts.get("image_parse_path"), candidate_image.shape[:2], binary=False)
    openpose = _load_openpose(artifacts.get("openpose_json_path"))

    metadata_components, metadata_warnings = _metadata_components(candidate, artifacts)
    warnings.extend(metadata_warnings)

    readability, readability_warnings = _image_readability(candidate_image, image_path, person_image)
    exposure, exposure_warnings = _dimension_exposure_sanity(candidate_image, person_image)
    artifact_score, artifact_warnings = _artifact_proxy(candidate_image, agnostic_mask)
    cloth_score, cloth_warnings = _cloth_mask_alignment_proxy(cloth_image, cloth_mask, agnostic_mask)
    agnostic_score, agnostic_warnings = _agnostic_boundary_consistency(candidate_image, person_image, agnostic_mask)
    body_score, body_warnings = _body_preservation_proxy(candidate_image, person_image, agnostic_mask, parse_mask)
    pose_score, pose_warnings = _pose_visibility_sanity(candidate_image, openpose)
    garment_score, garment_warnings = _garment_boundary_proxy(candidate_image, agnostic_mask, cloth_mask)

    warnings.extend(
        [
            *readability_warnings,
            *exposure_warnings,
            *artifact_warnings,
            *cloth_warnings,
            *agnostic_warnings,
            *body_warnings,
            *pose_warnings,
            *garment_warnings,
        ]
    )
    warnings = _dedupe(warnings)

    component_scores = {
        "image_readability": readability,
        "dimension_exposure_sanity": exposure,
        "artifact_score": artifact_score,
        "cloth_mask_alignment_proxy": cloth_score,
        "agnostic_boundary_consistency": agnostic_score,
        "body_preservation_proxy": body_score,
        "pose_visibility_sanity": pose_score,
        "garment_boundary_proxy": garment_score,
    }
    score = _weighted_score(component_scores)
    score = _apply_hard_floors(score, warnings)

    return {
        "schema_version": ONLINE_VISUAL_PROXY_SCHEMA_VERSION,
        "online_visual_score": round(score, 4),
        "online_visual_score_source": ONLINE_VISUAL_SCORE_SOURCE,
        "online_visual_score_mode": ONLINE_VISUAL_SCORE_MODE,
        "online_visual_components": {
            **component_scores,
            **metadata_components,
            "candidate_image_path": str(image_path),
            "artifact_root": None if root is None else str(root),
            "production_safe_inputs_only": True,
        },
        "online_visual_warnings": warnings,
        "candidate_specific_online_score": True,
        "production_safe": True,
    }


def warning_penalty(warnings: list[str]) -> float:
    penalties = {
        "generation_artifact_mild": 3.0,
        "generation_artifact_severe": 12.0,
        "agnostic_change_leakage": 6.0,
        "body_region_distortion_proxy": 8.0,
        "candidate_image_missing": 100.0,
        "candidate_image_load_failed": 100.0,
        "near_blank_image": 15.0,
        "extreme_dark_image": 12.0,
        "extreme_bright_image": 12.0,
        "low_dynamic_range": 6.0,
        "cloth_mask_alignment_low": 4.0,
        "pose_visibility_low": 4.0,
        "boundary_discontinuity_proxy": 4.0,
    }
    return round(sum(penalties.get(warning, 0.0) for warning in set(warnings)), 4)


def _unavailable(reason: str, *, image_path: Path | None = None) -> dict[str, Any]:
    components: dict[str, Any] = {"production_safe_inputs_only": True}
    if image_path is not None:
        components["candidate_image_path"] = str(image_path)
    return {
        "schema_version": ONLINE_VISUAL_PROXY_SCHEMA_VERSION,
        "online_visual_score": None,
        "online_visual_score_source": ONLINE_VISUAL_SCORE_SOURCE,
        "online_visual_score_mode": ONLINE_VISUAL_SCORE_MODE,
        "online_visual_components": components,
        "online_visual_warnings": [reason],
        "candidate_specific_online_score": False,
        "production_safe": True,
    }


def _artifact_root(candidate: Mapping[str, Any], artifact_root: str | Path | None) -> Path | None:
    value = artifact_root or candidate.get("artifact_root")
    if value is None:
        return None
    path = Path(str(value))
    return path if path.exists() else path


def _resolve_artifacts(candidate: Mapping[str, Any], *, pair_id: str, artifact_root: Path | None) -> dict[str, Path | None]:
    person_path = _path_or_none(candidate.get("person_path"))
    cloth_path = _path_or_none(candidate.get("cloth_path"))
    output: dict[str, Path | None] = {
        "person_path": person_path,
        "cloth_path": cloth_path,
        "agnostic_mask_path": None,
        "cloth_mask_path": None,
        "image_parse_path": None,
        "openpose_json_path": None,
        "densepose_path": None,
    }
    if not pair_id or artifact_root is None:
        return output

    candidates = {
        "person_path": [artifact_root / "image" / f"{pair_id}.jpg"],
        "cloth_path": [artifact_root / "cloth" / f"{pair_id}.jpg"],
        "agnostic_mask_path": [artifact_root / "agnostic-mask" / f"{pair_id}.png"],
        "cloth_mask_path": [artifact_root / "cloth-mask" / f"{pair_id}.png"],
        "image_parse_path": [artifact_root / "image-parse" / f"{pair_id}.png"],
        "openpose_json_path": [
            artifact_root / "openpose-json" / f"{pair_id}_keypoints.json",
            artifact_root / "openpose-json" / f"{pair_id}.json",
        ],
        "densepose_path": [
            artifact_root / "image-densepose" / f"{pair_id}.png",
            artifact_root / "image-densepose" / f"{pair_id}.jpg",
        ],
    }
    for key, paths in candidates.items():
        if output.get(key) is not None and Path(output[key]).is_file():  # type: ignore[arg-type]
            continue
        output[key] = next((path for path in paths if path.is_file()), paths[0])
    return output


def _metadata_components(candidate: Mapping[str, Any], artifacts: Mapping[str, Path | None]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    inference_status = _as_string(candidate.get("inference_status") or "success").lower()
    if inference_status != "success":
        warnings.append(f"inference_status={inference_status}")

    artifact_exists = {}
    for key, path in artifacts.items():
        exists = bool(path is not None and Path(path).is_file())
        artifact_exists[key] = exists
        if key in {"person_path", "agnostic_mask_path"} and not exists:
            warnings.append(f"missing_{key}")
    return {
        "inference_status": inference_status,
        "artifact_exists": artifact_exists,
    }, warnings


def _image_readability(image: Any, image_path: Path, person_image: Any | None) -> tuple[float, list[str]]:
    warnings: list[str] = []
    height, width = image.shape[:2]
    score = 100.0
    if width <= 0 or height <= 0:
        warnings.append("invalid_dimensions")
        score -= 100.0
    if image_path.stat().st_size < 1024:
        warnings.append("candidate_image_too_small")
        score -= 35.0
    if person_image is not None and person_image.shape[:2] != image.shape[:2]:
        warnings.append("unexpected_output_dimensions")
        score -= 10.0
    aspect_ratio = width / max(1, height)
    if aspect_ratio < 0.35 or aspect_ratio > 1.4:
        warnings.append("aspect_ratio_outlier")
        score -= 15.0
    return _clamp(score), warnings


def _dimension_exposure_sanity(image: Any, person_image: Any | None) -> tuple[float, list[str]]:
    warnings: list[str] = []
    mean = float(image.mean())
    std = float(image.std())
    dynamic_range = float(image.max() - image.min())
    dark_ratio = float((image < 8).mean())
    bright_ratio = float((image > 247).mean())
    score = 100.0
    if std < 2.0:
        warnings.append("near_blank_image")
        score -= 65.0
    if mean < 8.0:
        warnings.append("extreme_dark_image")
        score -= 45.0
    if mean > 247.0:
        warnings.append("extreme_bright_image")
        score -= 45.0
    if dynamic_range < 20.0:
        warnings.append("low_dynamic_range")
        score -= 35.0
    if dark_ratio > 0.35 or bright_ratio > 0.55:
        warnings.append("exposure_outlier")
        score -= 15.0
    if person_image is not None:
        person_mean = float(person_image.mean())
        if abs(mean - person_mean) > 65.0:
            warnings.append("candidate_person_exposure_mismatch")
            score -= 8.0
    return _clamp(score), warnings


def _artifact_proxy(image: Any, agnostic_mask: Any | None) -> tuple[float, list[str]]:
    warnings: list[str] = []
    luma = _to_luma(image)
    gy, gx = np.gradient(luma)  # type: ignore[union-attr]
    grad = np.sqrt(gx * gx + gy * gy)  # type: ignore[union-attr]
    grad_mean = float(grad.mean())
    grad_p99 = float(np.percentile(grad, 99))  # type: ignore[union-attr]
    border_score = _border_artifact_score(luma)
    score = 100.0
    if grad_mean < 1.2:
        warnings.append("generation_artifact_mild")
        score -= 12.0
    if grad_p99 > 120.0:
        warnings.append("checkerboard_artifact_proxy")
        score -= 10.0
    if border_score < 70.0:
        warnings.append("visible_border_artifact")
        score -= 100.0 - border_score
    if agnostic_mask is not None:
        boundary_score = _mask_boundary_smoothness(luma, agnostic_mask)
        if boundary_score < 55.0:
            warnings.append("boundary_discontinuity_proxy")
            score -= 12.0
    if score < 55.0:
        warnings.append("generation_artifact_severe")
    elif score < 78.0:
        warnings.append("generation_artifact_mild")
    return _clamp(score), _dedupe(warnings)


def _cloth_mask_alignment_proxy(cloth_image: Any | None, cloth_mask: Any | None, agnostic_mask: Any | None) -> tuple[float, list[str]]:
    warnings: list[str] = []
    score = 100.0
    if cloth_mask is None:
        return 78.0, ["cloth_mask_unavailable"]
    coverage = _mask_coverage(cloth_mask)
    if coverage < 0.01 or coverage > 0.90:
        warnings.append("cloth_area_outlier")
        score -= 25.0
    elif coverage < 0.04 or coverage > 0.65:
        warnings.append("cloth_area_marginal")
        score -= 8.0
    if cloth_image is None:
        warnings.append("cloth_image_unavailable")
        score -= 5.0
    if agnostic_mask is not None:
        agn_cov = _mask_coverage(agnostic_mask)
        if agn_cov < 0.02 or agn_cov > 0.80:
            warnings.append("cloth_mask_alignment_low")
            score -= 10.0
    return _clamp(score), warnings


def _agnostic_boundary_consistency(candidate: Any, person: Any | None, mask: Any | None) -> tuple[float, list[str]]:
    if person is None or mask is None:
        return 76.0, ["agnostic_consistency_artifact_unavailable"]
    warnings: list[str] = []
    person_resized = _resize_like(person, candidate)
    diff = np.mean(np.abs(candidate - person_resized), axis=2)  # type: ignore[union-attr]
    mask_bool = mask > 0.5
    if mask_bool.mean() < 0.01:
        return 65.0, ["agnostic_mask_too_small"]
    inside = float(diff[mask_bool].mean()) if mask_bool.any() else 0.0
    outside = float(diff[~mask_bool].mean()) if (~mask_bool).any() else 0.0
    score = 100.0
    if outside > max(18.0, inside * 0.70):
        warnings.append("agnostic_change_leakage")
        score -= min(35.0, (outside - max(18.0, inside * 0.70)) * 1.2)
    if inside < 8.0:
        warnings.append("agnostic_region_under_changed")
        score -= 18.0
    boundary = _binary_boundary(mask_bool)
    if boundary.any():
        boundary_diff = float(diff[boundary].mean())
        if boundary_diff > max(45.0, inside * 1.7):
            warnings.append("boundary_discontinuity_proxy")
            score -= 12.0
    return _clamp(score), warnings


def _body_preservation_proxy(candidate: Any, person: Any | None, mask: Any | None, parse_mask: Any | None) -> tuple[float, list[str]]:
    if person is None:
        return 75.0, ["person_image_unavailable"]
    warnings: list[str] = []
    person_resized = _resize_like(person, candidate)
    diff = np.mean(np.abs(candidate - person_resized), axis=2)  # type: ignore[union-attr]
    preserve_region = np.ones(diff.shape, dtype=bool)  # type: ignore[union-attr]
    if mask is not None:
        preserve_region = preserve_region & ~(mask > 0.5)
    if parse_mask is not None:
        preserve_region = preserve_region & (parse_mask > 0.01)
    if preserve_region.mean() < 0.02:
        preserve_region = np.ones(diff.shape, dtype=bool)  # type: ignore[union-attr]
        if mask is not None:
            preserve_region = preserve_region & ~(mask > 0.5)
    outside_change = float(diff[preserve_region].mean()) if preserve_region.any() else float(diff.mean())
    score = 100.0 - min(60.0, outside_change * 1.2)
    if outside_change > 32.0:
        warnings.append("body_region_distortion_proxy")
    top_region = preserve_region.copy()
    top_region[int(top_region.shape[0] * 0.35) :, :] = False
    if top_region.any() and float(diff[top_region].mean()) > 28.0:
        warnings.append("face_region_changed")
        score -= 8.0
    return _clamp(score), warnings


def _pose_visibility_sanity(candidate: Any, openpose: dict[str, Any] | None) -> tuple[float, list[str]]:
    if not openpose:
        return 76.0, ["openpose_unavailable"]
    keypoints = _extract_keypoints(openpose)
    if not keypoints:
        return 60.0, ["pose_visibility_low"]
    warnings: list[str] = []
    required = {2: "right_shoulder", 5: "left_shoulder", 4: "right_wrist", 7: "left_wrist"}
    present = 0
    visible = 0
    luma = _to_luma(candidate)
    height, width = luma.shape
    for index, name in required.items():
        point = keypoints.get(index)
        if not point or point[2] < 0.05:
            if "shoulder" in name:
                warnings.append("shoulder_keypoints_missing")
            if "wrist" in name:
                warnings.append("wrist_keypoints_missing")
            continue
        present += 1
        x = int(round(point[0]))
        y = int(round(point[1]))
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        patch = luma[max(0, y - 5) : min(height, y + 6), max(0, x - 5) : min(width, x + 6)]
        if patch.size and float(patch.std()) > 1.5 and 5.0 < float(patch.mean()) < 250.0:
            visible += 1
    score = 100.0 if present == 0 else 70.0 + 30.0 * (visible / max(1, present))
    if present < 2 or visible < max(1, present // 2):
        warnings.append("pose_visibility_low")
    return _clamp(score), _dedupe(warnings)


def _garment_boundary_proxy(candidate: Any, agnostic_mask: Any | None, cloth_mask: Any | None) -> tuple[float, list[str]]:
    warnings: list[str] = []
    luma = _to_luma(candidate)
    gy, gx = np.gradient(luma)  # type: ignore[union-attr]
    grad = np.sqrt(gx * gx + gy * gy)  # type: ignore[union-attr]
    score = 90.0
    if agnostic_mask is not None:
        boundary = _binary_boundary(agnostic_mask > 0.5)
        if boundary.any():
            boundary_grad = float(grad[boundary].mean())
            global_grad = float(grad.mean())
            ratio = boundary_grad / max(global_grad, 1e-6)
            if ratio < 0.55:
                warnings.append("torso_boundary_proxy_low")
                score -= 12.0
            elif ratio > 4.5:
                warnings.append("shoulder_boundary_proxy_low")
                score -= 8.0
    else:
        warnings.append("garment_boundary_mask_unavailable")
        score -= 8.0
    if cloth_mask is not None:
        coverage = _mask_coverage(cloth_mask)
        if coverage < 0.015:
            warnings.append("garment_length_boundary_proxy_low")
            score -= 10.0
    return _clamp(score), warnings


def _weighted_score(component_scores: Mapping[str, float]) -> float:
    total = 0.0
    for key, weight in COMPONENT_WEIGHTS.items():
        total += _clamp(component_scores.get(key, 0.0)) * weight
    return _clamp(total)


def _apply_hard_floors(score: float, warnings: list[str]) -> float:
    output = score
    if "near_blank_image" in warnings:
        output = min(output, 35.0)
    if "generation_artifact_severe" in warnings:
        output = min(output, 55.0)
    if "body_region_distortion_proxy" in warnings:
        output = min(output, 60.0)
    return _clamp(output)


def _load_optional_rgb(path: Path | None, fallback_shape_like: Any | None) -> Any | None:
    if path is None or not path.is_file():
        return None
    image = _load_rgb_array(path)
    if image is None:
        return None
    if fallback_shape_like is not None and image.shape[:2] != fallback_shape_like.shape[:2]:
        image = _resize_like(image, fallback_shape_like)
    return image


def _load_rgb_array(path: Path) -> Any | None:
    try:
        with Image.open(path) as image:  # type: ignore[union-attr]
            return np.asarray(image.convert("RGB"), dtype=np.float32)  # type: ignore[union-attr]
    except (OSError, ValueError):
        return None


def _load_optional_mask(path: Path | None, size_hw: tuple[int, int] | None, *, binary: bool = True) -> Any | None:
    if path is None or not path.is_file():
        return None
    try:
        with Image.open(path) as image:  # type: ignore[union-attr]
            gray = image.convert("L")
            if size_hw is not None and gray.size != (size_hw[1], size_hw[0]):
                gray = gray.resize((size_hw[1], size_hw[0]), Image.NEAREST)
            arr = np.asarray(gray, dtype=np.float32)  # type: ignore[union-attr]
    except (OSError, ValueError):
        return None
    if binary:
        return (arr > 127.0).astype(np.float32)  # type: ignore[union-attr]
    return (arr / 255.0).astype(np.float32)  # type: ignore[union-attr]


def _load_openpose(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _extract_keypoints(openpose: Mapping[str, Any]) -> dict[int, tuple[float, float, float]]:
    people = openpose.get("people")
    if isinstance(people, list) and people:
        raw = people[0].get("pose_keypoints_2d") if isinstance(people[0], Mapping) else None
    else:
        raw = openpose.get("pose_keypoints_2d")
    if not isinstance(raw, list):
        return {}
    points: dict[int, tuple[float, float, float]] = {}
    for index in range(0, len(raw) - 2, 3):
        try:
            points[index // 3] = (float(raw[index]), float(raw[index + 1]), float(raw[index + 2]))
        except (TypeError, ValueError):
            continue
    return points


def _resize_like(image: Any, reference: Any) -> Any:
    height, width = reference.shape[:2]
    if image.shape[:2] == (height, width):
        return image
    pil_image = Image.fromarray(np.clip(image, 0, 255).astype("uint8"))  # type: ignore[union-attr]
    return np.asarray(pil_image.resize((width, height), Image.BICUBIC), dtype=np.float32)  # type: ignore[union-attr]


def _border_artifact_score(luma: Any) -> float:
    height, width = luma.shape
    margin = max(2, min(height, width) // 32)
    border = np.concatenate(  # type: ignore[union-attr]
        [
            luma[:margin, :].ravel(),
            luma[-margin:, :].ravel(),
            luma[:, :margin].ravel(),
            luma[:, -margin:].ravel(),
        ]
    )
    center = luma[margin:-margin, margin:-margin]
    if center.size == 0:
        return 80.0
    diff = abs(float(border.mean()) - float(center.mean()))
    return _clamp(100.0 - diff * 1.6)


def _mask_boundary_smoothness(luma: Any, mask: Any) -> float:
    boundary = _binary_boundary(mask > 0.5)
    if not boundary.any():
        return 82.0
    gy, gx = np.gradient(luma)  # type: ignore[union-attr]
    grad = np.sqrt(gx * gx + gy * gy)  # type: ignore[union-attr]
    boundary_grad = float(grad[boundary].mean())
    global_grad = float(grad.mean())
    ratio = boundary_grad / max(global_grad, 1e-6)
    if ratio <= 2.0:
        return 100.0
    return _clamp(100.0 - (ratio - 2.0) * 22.0)


def _binary_boundary(mask: Any) -> Any:
    mask_bool = mask.astype(bool)  # type: ignore[union-attr]
    up = np.roll(mask_bool, 1, axis=0)  # type: ignore[union-attr]
    down = np.roll(mask_bool, -1, axis=0)  # type: ignore[union-attr]
    left = np.roll(mask_bool, 1, axis=1)  # type: ignore[union-attr]
    right = np.roll(mask_bool, -1, axis=1)  # type: ignore[union-attr]
    return mask_bool & (~(up & down & left & right))


def _mask_coverage(mask: Any) -> float:
    return float((mask > 0.5).mean())


def _to_luma(image: Any) -> Any:
    return (0.299 * image[:, :, 0]) + (0.587 * image[:, :, 1]) + (0.114 * image[:, :, 2])


def _path_or_none(value: Any) -> Path | None:
    if value is None:
        return None
    text = str(value)
    if not text or text.startswith("http://") or text.startswith("https://"):
        return None
    return Path(text)


def _as_string(value: Any) -> str:
    return "" if value is None else str(value)


def _clamp(value: float, *, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, float(value)))


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
