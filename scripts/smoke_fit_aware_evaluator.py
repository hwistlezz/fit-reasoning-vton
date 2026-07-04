from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.fit_aware_evaluator import (  # noqa: E402
    BEST_AVAILABLE_LOW_CONFIDENCE_WARNING,
    SLEEVE_PROXY_WARNING,
    UNKNOWN_CLOTH_TYPE_WARNING,
    evaluate_fit_aware_candidates,
)


def fit_analysis(
    *,
    label: str,
    score: float,
    measurements: dict[str, float | None],
    warnings: list[str] | None = None,
    level: str = "high",
) -> dict[str, Any]:
    return {
        "schema_version": "fit_analysis.v2",
        "source": {"type": "synthetic_smoke"},
        "fit_label": label,
        "measurements": measurements,
        "confidence": {
            "score": score,
            "level": level,
            "warnings": warnings or [],
        },
        "fit": {
            "label": label,
            "scores": measurements,
            "explanations": [],
        },
        "quality": {
            "pose_quality": 1.0,
            "parsing_quality": 1.0,
            "body_visibility": 1.0,
            "quality_score": score / 100,
            "silhouette_score": 0.9,
        },
        "hotspots": [
            {
                "key": "shoulder",
                "label": "Shoulder",
                "text": "Synthetic shoulder hotspot.",
                "x": 50.0,
                "y": 30.0,
                "value": measurements.get("shoulder_ratio"),
            }
        ],
        "annotations": [],
    }


def candidate(
    candidate_id: str,
    fit_payload: dict[str, Any],
    *,
    pair_id: str = "PAIR_SYNTH",
    inference_status: str = "success",
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "pair_id": pair_id,
        "candidate_id": candidate_id,
        "generator": "synthetic",
        "seed": None,
        "inference_status": inference_status,
        "image_url": f"/outputs/synthetic/{candidate_id}.png",
        "source_artifact": {"type": "synthetic"},
        "fit_analysis": fit_payload,
        "fit_score": None,
        "warnings": warnings or [],
    }


def build_main_manifest() -> dict[str, Any]:
    return {
        "schema_version": "fit_aware_candidates.v1",
        "pair_id": "PAIR_SYNTH",
        "request_id": "synthetic_smoke",
        "candidates": [
            candidate(
                "regular_good",
                fit_analysis(
                    label="regular",
                    score=84.0,
                    measurements={
                        "shoulder_ratio": 1.04,
                        "torso_width_ratio": 1.08,
                        "garment_length_ratio": 1.10,
                        "sleeve_length_ratio": 1.0,
                    },
                    warnings=[SLEEVE_PROXY_WARNING],
                ),
            ),
            candidate(
                "unknown_missing_heavy",
                fit_analysis(
                    label="unknown_low_confidence",
                    score=72.0,
                    measurements={
                        "shoulder_ratio": None,
                        "torso_width_ratio": None,
                        "garment_length_ratio": None,
                        "sleeve_length_ratio": 1.0,
                    },
                    warnings=[
                        "missing_core_ratio_count=3",
                        UNKNOWN_CLOTH_TYPE_WARNING,
                        SLEEVE_PROXY_WARNING,
                    ],
                    level="medium",
                ),
            ),
            candidate(
                "regular_missing_ratios",
                fit_analysis(
                    label="regular",
                    score=84.0,
                    measurements={
                        "shoulder_ratio": None,
                        "torso_width_ratio": 1.07,
                        "garment_length_ratio": None,
                        "sleeve_length_ratio": 1.0,
                    },
                    warnings=["missing_core_ratio_count=2", SLEEVE_PROXY_WARNING],
                ),
            ),
            candidate(
                "failed_high_score",
                fit_analysis(
                    label="regular",
                    score=95.0,
                    measurements={
                        "shoulder_ratio": 1.0,
                        "torso_width_ratio": 1.0,
                        "garment_length_ratio": 1.0,
                        "sleeve_length_ratio": 1.0,
                    },
                ),
                inference_status="failed",
            ),
        ],
    }


def build_all_low_manifest() -> dict[str, Any]:
    return {
        "schema_version": "fit_aware_candidates.v1",
        "pair_id": "PAIR_LOW",
        "request_id": "synthetic_low_smoke",
        "candidates": [
            candidate(
                "low_unknown_a",
                fit_analysis(
                    label="unknown_low_confidence",
                    score=38.0,
                    measurements={
                        "shoulder_ratio": None,
                        "torso_width_ratio": None,
                        "garment_length_ratio": None,
                        "sleeve_length_ratio": 1.0,
                    },
                    warnings=["missing_core_ratio_count=3", SLEEVE_PROXY_WARNING],
                    level="low",
                ),
                pair_id="PAIR_LOW",
            ),
            candidate(
                "low_unknown_b",
                fit_analysis(
                    label="unknown",
                    score=42.0,
                    measurements={
                        "shoulder_ratio": None,
                        "torso_width_ratio": 1.4,
                        "garment_length_ratio": None,
                        "sleeve_length_ratio": 1.0,
                    },
                    warnings=["missing_core_ratio_count=2", SLEEVE_PROXY_WARNING],
                    level="low",
                ),
                pair_id="PAIR_LOW",
            ),
        ],
    }


def main() -> None:
    main_result = evaluate_fit_aware_candidates(build_main_manifest())
    selected = main_result["selected_candidate"]
    ranked_by_id = {candidate["candidate_id"]: candidate for candidate in main_result["ranked_candidates"]}

    assert selected is not None
    assert selected["candidate_id"] == "regular_good"
    assert ranked_by_id["unknown_missing_heavy"]["fit_score"] < selected["fit_score"]
    assert ranked_by_id["regular_missing_ratios"]["fit_score"] < selected["fit_score"]
    assert "proxy" in main_result["user_facing_explanation"]

    low_result = evaluate_fit_aware_candidates(build_all_low_manifest())
    assert low_result["selected_candidate"] is not None
    assert BEST_AVAILABLE_LOW_CONFIDENCE_WARNING in low_result["warnings"]
    assert "주의" in low_result["user_facing_explanation"]

    summary = {
        "high_confidence_regular_selection": selected["candidate_id"],
        "unknown_low_confidence_suppressed": ranked_by_id["unknown_missing_heavy"]["fit_score"]
        < selected["fit_score"],
        "missing_ratio_penalty": {
            "regular_good": selected["fit_score"],
            "regular_missing_ratios": ranked_by_id["regular_missing_ratios"]["fit_score"],
        },
        "sleeve_proxy_warning_in_explanation": "proxy" in main_result["user_facing_explanation"],
        "all_low_confidence_fallback": {
            "selected": low_result["selected_candidate"]["candidate_id"],
            "warnings": low_result["warnings"],
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
