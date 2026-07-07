from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping

try:
    import numpy as np
    from PIL import Image
except Exception:  # pragma: no cover - handled at runtime in score output
    Image = None  # type: ignore[assignment]
    np = None  # type: ignore[assignment]


VISUAL_SCORE_SCHEMA_VERSION = "candidate_visual_score.v1"
OFFLINE_REFERENCE_SOURCE = "offline_reference_metric"
IMAGE_SANITY_SOURCE = "image_sanity_only"
UNAVAILABLE_SOURCE = "unavailable"
PER_CANDIDATE_METRIC_SOURCE = "per_candidate_metric"


def score_candidate_visual(
    candidate: Mapping[str, Any],
    *,
    reference_image_path: str | Path | None = None,
) -> dict[str, Any]:
    """Score one generated candidate image without mutating files.

    The offline reference path is intended for evaluation-only smoke tests. A
    production scorer should not depend on target/worn ground truth images.
    """

    image_path = _path_or_none(candidate.get("image_path") or candidate.get("image_url"))
    if Image is None or np is None:
        return _unavailable("image_libraries_unavailable")
    if image_path is None:
        return _unavailable("candidate_image_path_missing")
    if not image_path.is_file():
        return _unavailable("candidate_image_missing", image_path=image_path)

    output_image = _load_rgb_array(image_path)
    if output_image is None:
        return _unavailable("candidate_image_load_failed", image_path=image_path)

    sanity = _image_sanity_components(output_image, image_path)
    warnings = list(sanity["warnings"])

    reference_path = _path_or_none(reference_image_path)
    if reference_path is not None and reference_path.is_file():
        reference_image = _load_rgb_array(reference_path)
        if reference_image is None:
            warnings.append("reference_image_load_failed")
        else:
            if reference_image.shape != output_image.shape:
                reference_image = _resize_array(reference_path, output_image.shape[1], output_image.shape[0])
                warnings.append("reference_resized_to_candidate_shape")
            if reference_image is not None:
                psnr = _psnr(output_image, reference_image)
                ssim = _global_ssim(output_image, reference_image)
                score_data = score_from_reference_metrics(psnr=psnr, ssim=ssim)
                components = {
                    **sanity["components"],
                    "reference_image_path": str(reference_path),
                    "psnr": round(psnr, 6),
                    "ssim": round(ssim, 6),
                    "psnr_score": score_data["components"]["psnr_score"],
                    "ssim_score": score_data["components"]["ssim_score"],
                }
                return {
                    "schema_version": VISUAL_SCORE_SCHEMA_VERSION,
                    "visual_score": score_data["visual_score"],
                    "visual_score_source": OFFLINE_REFERENCE_SOURCE,
                    "visual_score_mode": "offline_eval",
                    "visual_warnings": _dedupe([*warnings, *score_data["visual_warnings"]]),
                    "candidate_specific_visual_score": True,
                    "visual_score_components": components,
                }

    score = _sanity_score(sanity["components"], warnings)
    return {
        "schema_version": VISUAL_SCORE_SCHEMA_VERSION,
        "visual_score": score,
        "visual_score_source": IMAGE_SANITY_SOURCE,
        "visual_score_mode": "image_sanity_only",
        "visual_warnings": _dedupe(warnings),
        "candidate_specific_visual_score": True,
        "visual_score_components": sanity["components"],
    }


def score_from_reference_metrics(*, psnr: float | None, ssim: float | None) -> dict[str, Any]:
    psnr_value = float(psnr) if psnr is not None and math.isfinite(float(psnr)) else None
    ssim_value = float(ssim) if ssim is not None and math.isfinite(float(ssim)) else None
    warnings: list[str] = []

    if psnr_value is None:
        warnings.append("psnr_unavailable")
        psnr_score = 0.0
    else:
        psnr_score = _clamp((psnr_value - 10.0) / 25.0 * 100.0)

    if ssim_value is None:
        warnings.append("ssim_unavailable")
        ssim_score = 0.0
    else:
        ssim_score = _clamp(ssim_value * 100.0)

    if psnr_value is None and ssim_value is None:
        source = UNAVAILABLE_SOURCE
        score = None
    else:
        source = PER_CANDIDATE_METRIC_SOURCE
        score = round(_clamp((0.35 * psnr_score) + (0.65 * ssim_score)), 4)

    return {
        "schema_version": VISUAL_SCORE_SCHEMA_VERSION,
        "visual_score": score,
        "visual_score_source": source,
        "visual_score_mode": "offline_eval",
        "visual_warnings": warnings,
        "candidate_specific_visual_score": score is not None,
        "components": {
            "psnr": None if psnr_value is None else round(psnr_value, 6),
            "ssim": None if ssim_value is None else round(ssim_value, 6),
            "psnr_score": round(psnr_score, 4),
            "ssim_score": round(ssim_score, 4),
        },
    }


def _unavailable(reason: str, *, image_path: Path | None = None) -> dict[str, Any]:
    components: dict[str, Any] = {}
    if image_path is not None:
        components["image_path"] = str(image_path)
    return {
        "schema_version": VISUAL_SCORE_SCHEMA_VERSION,
        "visual_score": None,
        "visual_score_source": UNAVAILABLE_SOURCE,
        "visual_score_mode": "unavailable",
        "visual_warnings": [reason],
        "candidate_specific_visual_score": False,
        "visual_score_components": components,
    }


def _path_or_none(value: Any) -> Path | None:
    if value is None:
        return None
    text = str(value)
    if not text or text.startswith("http://") or text.startswith("https://"):
        return None
    return Path(text)


def _load_rgb_array(path: Path) -> Any | None:
    try:
        with Image.open(path) as image:  # type: ignore[union-attr]
            return np.asarray(image.convert("RGB"), dtype=np.float32)  # type: ignore[union-attr]
    except (OSError, ValueError):
        return None


def _resize_array(path: Path, width: int, height: int) -> Any | None:
    try:
        with Image.open(path) as image:  # type: ignore[union-attr]
            return np.asarray(image.convert("RGB").resize((width, height), Image.BICUBIC), dtype=np.float32)  # type: ignore[union-attr]
    except (OSError, ValueError):
        return None


def _image_sanity_components(image: Any, image_path: Path) -> dict[str, Any]:
    height, width = image.shape[:2]
    mean = float(image.mean())
    std = float(image.std())
    min_pixel = float(image.min())
    max_pixel = float(image.max())
    warnings: list[str] = []
    if width <= 0 or height <= 0:
        warnings.append("invalid_dimensions")
    if std < 2.0:
        warnings.append("near_blank_image")
    if mean < 5.0:
        warnings.append("extreme_dark_image")
    if mean > 250.0:
        warnings.append("extreme_bright_image")
    return {
        "warnings": warnings,
        "components": {
            "image_path": str(image_path),
            "file_size_bytes": image_path.stat().st_size,
            "width": int(width),
            "height": int(height),
            "mean_pixel": round(mean, 4),
            "std_pixel": round(std, 4),
            "min_pixel": round(min_pixel, 4),
            "max_pixel": round(max_pixel, 4),
        },
    }


def _sanity_score(components: Mapping[str, Any], warnings: list[str]) -> float:
    score = 100.0
    penalties = {
        "invalid_dimensions": 100.0,
        "near_blank_image": 45.0,
        "extreme_dark_image": 35.0,
        "extreme_bright_image": 35.0,
    }
    for warning in warnings:
        score -= penalties.get(warning, 5.0)
    file_size = _float_or_none(components.get("file_size_bytes")) or 0.0
    if file_size < 1024:
        score -= 25.0
    return round(_clamp(score), 4)


def _psnr(candidate: Any, reference: Any) -> float:
    mse = float(np.mean((candidate - reference) ** 2))  # type: ignore[union-attr]
    if mse <= 1e-12:
        return 99.0
    return float(20.0 * math.log10(255.0 / math.sqrt(mse)))


def _global_ssim(candidate: Any, reference: Any) -> float:
    cand = _to_luma(candidate)
    ref = _to_luma(reference)
    c1 = (0.01 * 255.0) ** 2
    c2 = (0.03 * 255.0) ** 2
    mu_x = float(cand.mean())
    mu_y = float(ref.mean())
    sigma_x = float(((cand - mu_x) ** 2).mean())
    sigma_y = float(((ref - mu_y) ** 2).mean())
    sigma_xy = float(((cand - mu_x) * (ref - mu_y)).mean())
    numerator = (2.0 * mu_x * mu_y + c1) * (2.0 * sigma_xy + c2)
    denominator = (mu_x**2 + mu_y**2 + c1) * (sigma_x + sigma_y + c2)
    if denominator == 0:
        return 0.0
    return _clamp(float(numerator / denominator), lower=-1.0, upper=1.0)


def _to_luma(image: Any) -> Any:
    return (0.299 * image[:, :, 0]) + (0.587 * image[:, :, 1]) + (0.114 * image[:, :, 2])


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
