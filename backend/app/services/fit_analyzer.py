import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from backend.app.core.config import settings


PLACEHOLDER_CONFIDENCE_SCORE = 60
VALID_CONFIDENCE_LEVELS = {"low", "medium", "high", "unknown"}
FIT_SCORE_KEYS = (
    "shoulder_ratio",
    "torso_width_ratio",
    "sleeve_length_ratio",
    "garment_length_ratio",
)
FIT_JSON_FALLBACK_WARNING = "fit.json을 읽지 못해 placeholder 결과를 반환했습니다."
ANNOTATION_LABELS = {
    "shoulder": "어깨",
    "torso": "몸통",
    "sleeve": "소매",
    "length": "기장",
    "cloth_region": "의류 영역",
    "pose": "포즈",
}


@dataclass(frozen=True)
class ConfidenceResult:
    score: int | float
    level: str
    warnings: list[str]


@dataclass(frozen=True)
class FitResult:
    label: str
    scores: dict[str, float | None]
    explanations: list[str]


@dataclass(frozen=True)
class FitAnalysisResult:
    confidence: ConfidenceResult
    fit: FitResult
    annotations: list[dict[str, Any]]

    def to_response_payload(self) -> dict[str, Any]:
        return asdict(self)


def confidence_level_for_score(score: int | float) -> str:
    if score < 40:
        return "low"
    if score < 70:
        return "medium"
    return "high"


def analyze_fit_placeholder(job_id: str, result_image_url: str | None) -> FitAnalysisResult:
    warnings = [
        "현재 fit 분석은 placeholder입니다. 실제 신뢰도 계산은 아직 연결되지 않았습니다.",
        "StableVITON 결과 이미지 생성 여부와 응답 schema 연동만 검증합니다.",
    ]
    if result_image_url is None:
        warnings.append(f"job_id={job_id}의 result_image_url이 없어 실제 fit 판단을 수행하지 않습니다.")

    confidence = ConfidenceResult(
        score=PLACEHOLDER_CONFIDENCE_SCORE,
        level=confidence_level_for_score(PLACEHOLDER_CONFIDENCE_SCORE),
        warnings=warnings,
    )
    fit = FitResult(
        label="unknown",
        scores={
            "shoulder_ratio": None,
            "torso_width_ratio": None,
            "sleeve_length_ratio": None,
            "garment_length_ratio": None,
        },
        explanations=[
            "StableVITON 결과 이미지는 생성되었지만, 실제 fit analyzer는 아직 연결되지 않았습니다."
        ],
    )

    return FitAnalysisResult(confidence=confidence, fit=fit, annotations=[])


def analyze_fit(
    job_id: str,
    result_image_url: str | None,
    fit_result_path: Path | None = None,
) -> FitAnalysisResult:
    for candidate_path in _fit_result_candidates(job_id, fit_result_path):
        if not candidate_path.is_file():
            continue
        try:
            return _load_fit_result(candidate_path)
        except (OSError, json.JSONDecodeError, ValueError, TypeError):
            return _placeholder_with_fit_json_warning(job_id, result_image_url)

    return analyze_fit_placeholder(job_id=job_id, result_image_url=result_image_url)


def _fit_result_candidates(job_id: str, fit_result_path: Path | None) -> list[Path]:
    if fit_result_path is not None:
        return [fit_result_path]

    return [
        settings.output_dir / job_id / "fit.json",
        settings.fit_analysis_root / job_id / "fit.json",
    ]


def _load_fit_result(path: Path) -> FitAnalysisResult:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fit result payload must be an object.")

    if _is_pc2_compact_fit_result(payload):
        return _load_pc2_compact_fit_result(payload)

    return _load_backend_compatible_fit_result(payload)


def _is_pc2_compact_fit_result(payload: dict[str, Any]) -> bool:
    return isinstance(payload.get("confidence"), int | float) and "fit_label" in payload and "features" in payload


def _load_backend_compatible_fit_result(payload: dict[str, Any]) -> FitAnalysisResult:
    confidence_payload = _require_dict(payload.get("confidence"), "confidence")
    fit_payload = _require_dict(payload.get("fit"), "fit")
    annotations_payload = payload.get("annotations", [])
    if not isinstance(annotations_payload, list):
        raise ValueError("annotations must be a list.")

    confidence = _parse_confidence(confidence_payload)
    fit = _parse_fit(fit_payload)
    annotations = [_parse_annotation(annotation) for annotation in annotations_payload]
    annotations = [annotation for annotation in annotations if annotation is not None]

    return FitAnalysisResult(confidence=confidence, fit=fit, annotations=annotations)


def _load_pc2_compact_fit_result(payload: dict[str, Any]) -> FitAnalysisResult:
    features_payload = _require_dict(payload.get("features"), "features")
    annotations_payload = payload.get("annotations", [])
    if not isinstance(annotations_payload, list):
        raise ValueError("annotations must be a list.")

    confidence = _parse_compact_confidence(payload.get("confidence"))
    fit = _parse_compact_fit(payload.get("fit_label"), features_payload)
    annotations = [_parse_annotation(annotation) for annotation in annotations_payload]
    annotations = [annotation for annotation in annotations if annotation is not None]

    return FitAnalysisResult(confidence=confidence, fit=fit, annotations=annotations)


def _require_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object.")
    return value


def _parse_confidence(payload: dict[str, Any]) -> ConfidenceResult:
    score = payload.get("score")
    if not isinstance(score, int | float):
        raise ValueError("confidence.score must be numeric.")

    level = payload.get("level")
    if not isinstance(level, str) or level not in VALID_CONFIDENCE_LEVELS:
        raise ValueError("confidence.level is invalid.")

    warnings = payload.get("warnings", [])
    if not isinstance(warnings, list) or not all(isinstance(warning, str) for warning in warnings):
        raise ValueError("confidence.warnings must be a list of strings.")

    return ConfidenceResult(score=score, level=level, warnings=warnings)


def _parse_compact_confidence(score: Any) -> ConfidenceResult:
    if not isinstance(score, int | float):
        raise ValueError("confidence must be numeric.")

    return ConfidenceResult(score=score, level=_compact_confidence_level(score), warnings=[])


def _compact_confidence_level(score: int | float) -> str:
    if score < 50:
        return "low"
    if score < 80:
        return "medium"
    return "high"


def _parse_fit(payload: dict[str, Any]) -> FitResult:
    label = payload.get("label")
    if not isinstance(label, str):
        raise ValueError("fit.label must be a string.")

    scores_payload = payload.get("scores")
    if not isinstance(scores_payload, dict):
        raise ValueError("fit.scores must be an object.")

    explanations = payload.get("explanations", [])
    if not isinstance(explanations, list) or not all(isinstance(explanation, str) for explanation in explanations):
        raise ValueError("fit.explanations must be a list of strings.")

    scores: dict[str, float | None] = {}
    for key in FIT_SCORE_KEYS:
        scores[key] = _optional_number(scores_payload.get(key), f"fit.scores.{key}")

    return FitResult(label=label, scores=scores, explanations=explanations)


def _parse_compact_fit(label: Any, features: dict[str, Any]) -> FitResult:
    if not isinstance(label, str):
        raise ValueError("fit_label must be a string.")

    scores: dict[str, float | None] = {}
    for key in FIT_SCORE_KEYS:
        scores[key] = _optional_number(features.get(key), f"features.{key}")

    return FitResult(label=label, scores=scores, explanations=[])


def _parse_annotation(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    key = payload.get("key") or payload.get("part")
    if not isinstance(key, str) or not key:
        return None

    x = payload.get("x")
    y = payload.get("y")
    if not isinstance(x, int | float) or not isinstance(y, int | float):
        return None

    text = payload.get("text") or payload.get("message")
    if not isinstance(text, str):
        text = ""

    severity = payload.get("severity")
    if isinstance(severity, str) and severity:
        text = f"{text} (severity: {severity})" if text else f"severity: {severity}"

    label = payload.get("label")
    if not isinstance(label, str) or not label:
        label = ANNOTATION_LABELS.get(key, key)

    return {
        "key": key,
        "label": label,
        "text": text,
        "x": x,
        "y": y,
        "value": _optional_number(payload.get("value"), "annotation.value"),
    }


def _optional_number(value: Any, field_name: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, int | float):
        raise ValueError(f"{field_name} must be numeric or null.")
    return value


def _placeholder_with_fit_json_warning(job_id: str, result_image_url: str | None) -> FitAnalysisResult:
    placeholder = analyze_fit_placeholder(job_id=job_id, result_image_url=result_image_url)
    confidence = ConfidenceResult(
        score=placeholder.confidence.score,
        level=placeholder.confidence.level,
        warnings=[*placeholder.confidence.warnings, FIT_JSON_FALLBACK_WARNING],
    )
    return FitAnalysisResult(
        confidence=confidence,
        fit=placeholder.fit,
        annotations=placeholder.annotations,
    )
