from dataclasses import asdict, dataclass
from typing import Any


PLACEHOLDER_CONFIDENCE_SCORE = 60


@dataclass(frozen=True)
class ConfidenceResult:
    score: int
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


def confidence_level_for_score(score: int) -> str:
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
