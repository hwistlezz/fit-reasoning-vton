from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Mapping


FIT_AWARE_SELECTION_SCHEMA_VERSION = "fit_aware_selection.v1"
FIT_ANALYSIS_SCHEMA_VERSION = "fit_analysis.v2"
CORE_RATIO_KEYS = ("shoulder_ratio", "torso_width_ratio", "garment_length_ratio")
SLEEVE_RATIO_KEY = "sleeve_length_ratio"
SLEEVE_PROXY_WARNING = "sleeve_length_ratio is a wrist-alignment proxy, not a calibrated sleeve-end measurement."
UNKNOWN_CLOTH_TYPE_WARNING = "cloth_type_unknown"
MISSING_CORE_RATIO_WARNING = "missing_core_ratio_count"
FIT_ANALYSIS_MISSING_WARNING = "fit_analysis_missing"
BEST_AVAILABLE_LOW_CONFIDENCE_WARNING = "best_available_low_confidence"
NO_ELIGIBLE_CANDIDATES_WARNING = "no_eligible_candidates"
LOW_CONFIDENCE_SCORE_THRESHOLD = 45.0

FIT_LABEL_ADJUSTMENTS = {
    "regular": 12.0,
    "slightly_oversized": 6.0,
    "oversized": -12.0,
    "fitted_or_slim_direction": -8.0,
    "unknown_low_confidence": -30.0,
    "unknown": -20.0,
}

CORE_COVERAGE_ADJUSTMENTS = {
    0: 8.0,
    1: -6.0,
    2: -16.0,
    3: -25.0,
}

RATIO_BANDS = {
    "shoulder_ratio": {
        "ideal": (0.92, 1.12),
        "acceptable": (0.85, 1.22),
        "max_penalty": 12.0,
    },
    "torso_width_ratio": {
        "ideal": (0.92, 1.15),
        "acceptable": (0.85, 1.25),
        "max_penalty": 12.0,
    },
    "garment_length_ratio": {
        "ideal": (0.85, 1.20),
        "acceptable": (0.75, 1.35),
        "max_penalty": 10.0,
    },
}

MISSING_CORE_RATIO_PATTERN = re.compile(r"missing_core_ratio_count=(\d+)")


def evaluate_fit_aware_candidates(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Rerank generated try-on candidates with embedded fit_analysis.v2 payloads."""

    pair_id = _as_string(manifest.get("pair_id"))
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("manifest.candidates must be a list.")

    scored_candidates = [
        score_candidate(candidate, pair_id=pair_id)
        for candidate in candidates
        if isinstance(candidate, Mapping)
    ]
    ranked_candidates = _rank_candidates(scored_candidates)
    eligible_candidates = [candidate for candidate in ranked_candidates if candidate["eligible"]]
    selected_candidate = eligible_candidates[0] if eligible_candidates else None
    all_low_confidence = bool(eligible_candidates) and all(
        _is_low_confidence_candidate(candidate) for candidate in eligible_candidates
    )

    selection_warnings: list[str] = []
    if not eligible_candidates:
        selection_warnings.append(NO_ELIGIBLE_CANDIDATES_WARNING)
    elif all_low_confidence:
        selection_warnings.append(BEST_AVAILABLE_LOW_CONFIDENCE_WARNING)

    selected_reason = _build_selected_reason(selected_candidate, all_low_confidence)
    user_facing_explanation = _build_user_facing_explanation(selected_candidate, all_low_confidence)
    warnings = _dedupe_strings(
        [
            *selection_warnings,
            *([] if selected_candidate is None else selected_candidate["warnings"]),
        ]
    )

    selected_fit_analysis = _get_fit_analysis(selected_candidate) if selected_candidate else None

    return {
        "schema_version": FIT_AWARE_SELECTION_SCHEMA_VERSION,
        "pair_id": pair_id,
        "selected_candidate": _public_candidate_payload(selected_candidate) if selected_candidate else None,
        "ranked_candidates": [
            _public_candidate_payload(candidate, rank=index + 1)
            for index, candidate in enumerate(ranked_candidates)
        ],
        "selected_reason": selected_reason,
        "user_facing_explanation": user_facing_explanation,
        "fit_analysis": selected_fit_analysis,
        "measurements": _get_measurements(selected_fit_analysis),
        "hotspots": _get_hotspots(selected_fit_analysis),
        "warnings": warnings,
    }


def score_candidate(candidate: Mapping[str, Any], *, pair_id: str | None = None) -> dict[str, Any]:
    """Return a candidate copy enriched with score, warnings, and ranking metadata."""

    output = deepcopy(dict(candidate))
    candidate_id = _as_string(output.get("candidate_id"))
    warnings = _string_list(output.get("warnings"))
    ineligibility_reasons: list[str] = []

    inference_status = _as_string(output.get("inference_status") or "success").lower()
    if inference_status != "success":
        ineligibility_reasons.append(f"inference_status={inference_status}")

    if not output.get("image_url") and not output.get("image_path"):
        ineligibility_reasons.append("image_missing")

    if pair_id and output.get("pair_id") not in (None, pair_id):
        warnings.append("pair_id_mismatch")

    fit_analysis = output.get("fit_analysis")
    if not _is_fit_analysis_v2(fit_analysis):
        score_data = _missing_fit_analysis_score()
        warnings.append(FIT_ANALYSIS_MISSING_WARNING)
    else:
        score_data = _score_fit_analysis(fit_analysis, warnings)

    warnings = _dedupe_strings([*warnings, *score_data["warnings"]])
    output.update(
        {
            "candidate_id": candidate_id,
            "inference_status": inference_status,
            "eligible": not ineligibility_reasons,
            "ineligibility_reasons": ineligibility_reasons,
            "fit_score": score_data["fit_score"],
            "fit_score_components": score_data["components"],
            "fit_label": score_data["fit_label"],
            "confidence_score": score_data["confidence_score"],
            "missing_core_ratio_count": score_data["missing_core_ratio_count"],
            "warnings": warnings,
        }
    )
    return output


def _score_fit_analysis(fit_analysis: Mapping[str, Any], candidate_warnings: list[str]) -> dict[str, Any]:
    confidence = _dict_value(fit_analysis.get("confidence"))
    confidence_score = _clamp(_optional_float(confidence.get("score")) or 0.0)
    confidence_warnings = _string_list(confidence.get("warnings"))
    warnings = _dedupe_strings([*candidate_warnings, *confidence_warnings])

    measurements = _get_measurements(fit_analysis)
    missing_core_ratio_count = _missing_core_ratio_count(measurements, warnings)
    fit_label = _fit_label(fit_analysis)

    label_adjustment = FIT_LABEL_ADJUSTMENTS.get(fit_label, FIT_LABEL_ADJUSTMENTS["unknown"])
    coverage_adjustment = CORE_COVERAGE_ADJUSTMENTS.get(
        min(3, missing_core_ratio_count),
        CORE_COVERAGE_ADJUSTMENTS[3],
    )
    ratio_adjustment = round(
        sum(_ratio_adjustment(key, measurements.get(key)) for key in CORE_RATIO_KEYS),
        2,
    )
    warning_adjustment = _warning_adjustment(warnings)

    score = _clamp(
        confidence_score
        + label_adjustment
        + coverage_adjustment
        + ratio_adjustment
        + warning_adjustment
    )

    if measurements.get(SLEEVE_RATIO_KEY) is not None and SLEEVE_PROXY_WARNING not in warnings:
        warnings.append(SLEEVE_PROXY_WARNING)

    return {
        "fit_score": round(score, 2),
        "fit_label": fit_label,
        "confidence_score": round(confidence_score, 2),
        "missing_core_ratio_count": missing_core_ratio_count,
        "warnings": _dedupe_strings(warnings),
        "components": {
            "base_confidence": round(confidence_score, 2),
            "fit_label_adjustment": label_adjustment,
            "core_ratio_coverage_adjustment": coverage_adjustment,
            "ratio_severity_adjustment": ratio_adjustment,
            "warning_adjustment": warning_adjustment,
        },
    }


def _missing_fit_analysis_score() -> dict[str, Any]:
    return {
        "fit_score": 0.0,
        "fit_label": "unknown_low_confidence",
        "confidence_score": 0.0,
        "missing_core_ratio_count": len(CORE_RATIO_KEYS),
        "warnings": [FIT_ANALYSIS_MISSING_WARNING],
        "components": {
            "base_confidence": 0.0,
            "fit_label_adjustment": FIT_LABEL_ADJUSTMENTS["unknown_low_confidence"],
            "core_ratio_coverage_adjustment": CORE_COVERAGE_ADJUSTMENTS[3],
            "ratio_severity_adjustment": 0.0,
            "warning_adjustment": 0.0,
        },
    }


def _rank_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda candidate: (
            0 if candidate["eligible"] else 1,
            -float(candidate.get("fit_score") or 0.0),
            -float(candidate.get("confidence_score") or 0.0),
            len(candidate.get("warnings") or []),
            int(candidate.get("missing_core_ratio_count") or 0),
            _as_string(candidate.get("candidate_id")),
        ),
    )


def _public_candidate_payload(candidate: dict[str, Any] | None, *, rank: int | None = None) -> dict[str, Any] | None:
    if candidate is None:
        return None

    payload = deepcopy(candidate)
    if rank is not None:
        payload["rank"] = rank
    return payload


def _is_fit_analysis_v2(value: Any) -> bool:
    return isinstance(value, Mapping) and value.get("schema_version") == FIT_ANALYSIS_SCHEMA_VERSION


def _get_fit_analysis(candidate: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not candidate:
        return None
    fit_analysis = candidate.get("fit_analysis")
    return deepcopy(dict(fit_analysis)) if isinstance(fit_analysis, Mapping) else None


def _get_measurements(fit_analysis: Mapping[str, Any] | None) -> dict[str, float | None]:
    if not isinstance(fit_analysis, Mapping):
        return {key: None for key in (*CORE_RATIO_KEYS, SLEEVE_RATIO_KEY)}

    measurements = _dict_value(fit_analysis.get("measurements"))
    fit = _dict_value(fit_analysis.get("fit"))
    scores = _dict_value(fit.get("scores"))

    return {
        key: _optional_float(measurements.get(key, scores.get(key)))
        for key in (*CORE_RATIO_KEYS, SLEEVE_RATIO_KEY)
    }


def _get_hotspots(fit_analysis: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(fit_analysis, Mapping):
        return []
    hotspots = fit_analysis.get("hotspots", fit_analysis.get("annotations", []))
    if not isinstance(hotspots, list):
        return []
    return [deepcopy(dict(hotspot)) for hotspot in hotspots if isinstance(hotspot, Mapping)]


def _fit_label(fit_analysis: Mapping[str, Any]) -> str:
    label = fit_analysis.get("fit_label")
    if isinstance(label, str) and label:
        return label
    fit = _dict_value(fit_analysis.get("fit"))
    label = fit.get("label")
    if isinstance(label, str) and label:
        return label
    return "unknown"


def _missing_core_ratio_count(measurements: Mapping[str, float | None], warnings: list[str]) -> int:
    computed = sum(1 for key in CORE_RATIO_KEYS if measurements.get(key) is None)
    warning_count = None
    for warning in warnings:
        match = MISSING_CORE_RATIO_PATTERN.search(warning)
        if match:
            warning_count = int(match.group(1))
            break
    if warning_count is None:
        return computed
    return max(computed, min(3, warning_count))


def _ratio_adjustment(key: str, value: float | None) -> float:
    if value is None:
        return 0.0

    bands = RATIO_BANDS[key]
    ideal_low, ideal_high = bands["ideal"]
    acceptable_low, acceptable_high = bands["acceptable"]
    max_penalty = bands["max_penalty"]

    if ideal_low <= value <= ideal_high:
        return 3.0
    if acceptable_low <= value <= acceptable_high:
        return 0.0

    if value < acceptable_low:
        distance = acceptable_low - value
    else:
        distance = value - acceptable_high

    return -round(min(max_penalty, 4.0 + distance * 40.0), 2)


def _warning_adjustment(warnings: list[str]) -> float:
    adjustment = 0.0
    generic_warning_count = 0

    for warning in warnings:
        if warning == UNKNOWN_CLOTH_TYPE_WARNING:
            adjustment -= 12.0
        elif "generation_artifact_severe" in warning:
            adjustment -= 20.0
        elif "generation_artifact_mild" in warning:
            adjustment -= 5.0
        elif (
            warning.startswith(MISSING_CORE_RATIO_WARNING)
            or warning == SLEEVE_PROXY_WARNING
            or warning == FIT_ANALYSIS_MISSING_WARNING
        ):
            continue
        else:
            generic_warning_count += 1

    adjustment -= min(10.0, generic_warning_count * 2.0)
    return round(adjustment, 2)


def _is_low_confidence_candidate(candidate: Mapping[str, Any]) -> bool:
    return (
        _as_string(candidate.get("fit_label")) == "unknown_low_confidence"
        or float(candidate.get("fit_score") or 0.0) < LOW_CONFIDENCE_SCORE_THRESHOLD
        or float(candidate.get("confidence_score") or 0.0) < LOW_CONFIDENCE_SCORE_THRESHOLD
    )


def _build_selected_reason(candidate: Mapping[str, Any] | None, all_low_confidence: bool) -> str:
    if candidate is None:
        return "No eligible successful candidates were available."
    if all_low_confidence:
        return "Selected as the best available candidate because every eligible candidate had low fit confidence."
    if int(candidate.get("missing_core_ratio_count") or 0) > 0:
        return "Selected as the best available candidate, but some core fit measurements were unavailable."
    return "Selected because it has the highest calibrated fit_score with reliable fit analysis."


def _build_user_facing_explanation(candidate: Mapping[str, Any] | None, all_low_confidence: bool) -> str:
    if candidate is None:
        return "선택 가능한 착장 후보가 없어 핏 판단을 제공할 수 없습니다."

    fit_analysis = _get_fit_analysis(candidate)
    measurements = _get_measurements(fit_analysis)
    fit_label = _as_string(candidate.get("fit_label")) or "unknown"
    confidence_level = _confidence_level_ko(fit_analysis, float(candidate.get("confidence_score") or 0.0))
    missing_core_ratio_count = int(candidate.get("missing_core_ratio_count") or 0)

    sentences = [
        _fit_label_sentence(fit_label),
        f"신뢰도는 {confidence_level}입니다.",
    ]

    measurement_sentences = _measurement_sentences(measurements)
    if measurement_sentences:
        sentences.append(" ".join(measurement_sentences))
    if missing_core_ratio_count:
        sentences.append("일부 핵심 비율은 판단 보류 상태입니다.")

    if all_low_confidence or fit_label == "unknown_low_confidence":
        sentences.append("모든 후보의 신뢰도가 낮아 결과 해석에 주의가 필요합니다.")
    elif missing_core_ratio_count:
        sentences.append("사용 가능한 측정값 기준으로 가장 안정적인 후보라 선택되었습니다.")
    else:
        sentences.append("핵심 비율과 신뢰도가 가장 안정적이어서 선택되었습니다.")

    return " ".join(sentences)


def _fit_label_sentence(label: str) -> str:
    labels = {
        "regular": "전체 핏은 보통 핏으로 판단됩니다.",
        "slightly_oversized": "전체 핏은 약간 여유 있는 핏으로 판단됩니다.",
        "oversized": "전체 핏은 넉넉한 오버핏 경향으로 판단됩니다.",
        "fitted_or_slim_direction": "전체 핏은 몸에 비교적 맞는 슬림한 방향으로 판단됩니다.",
        "unknown_low_confidence": "현재 결과는 핏 판단 신뢰도가 낮음으로 표시됩니다.",
        "unknown": "현재 결과는 핏 판단을 보류해야 합니다.",
    }
    return labels.get(label, labels["unknown"])


def _confidence_level_ko(fit_analysis: Mapping[str, Any] | None, confidence_score: float) -> str:
    confidence = _dict_value(fit_analysis.get("confidence")) if isinstance(fit_analysis, Mapping) else {}
    level = confidence.get("level")
    if not isinstance(level, str) or not level:
        if confidence_score < 50:
            level = "low"
        elif confidence_score < 80:
            level = "medium"
        else:
            level = "high"

    return {
        "high": "높음",
        "medium": "중간",
        "low": "낮음",
        "unknown": "알 수 없음",
    }.get(level, "알 수 없음")


def _measurement_sentences(measurements: Mapping[str, float | None]) -> list[str]:
    sentences = []
    if measurements.get("shoulder_ratio") is not None:
        sentences.append(f"어깨 비율은 {_format_ratio(measurements['shoulder_ratio'])}로 확인되었습니다.")
    if measurements.get("torso_width_ratio") is not None:
        sentences.append(f"몸통 폭 비율은 {_format_ratio(measurements['torso_width_ratio'])}로 확인되었습니다.")
    if measurements.get("garment_length_ratio") is not None:
        sentences.append(f"기장 비율은 {_format_ratio(measurements['garment_length_ratio'])}로 확인되었습니다.")
    if measurements.get("sleeve_length_ratio") is not None:
        sentences.append(
            f"소매 비율은 {_format_ratio(measurements['sleeve_length_ratio'])}로 확인되었지만, "
            "현재 값은 손목 정렬 기반 proxy입니다."
        )
    return sentences


def _format_ratio(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}"


def _dict_value(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _optional_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _as_string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _dedupe_strings(values: list[str]) -> list[str]:
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
