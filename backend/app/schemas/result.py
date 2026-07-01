from typing import Any

from pydantic import BaseModel, Field


class FitScores(BaseModel):
    shoulder_ratio: float | None = None
    torso_width_ratio: float | None = None
    sleeve_length_ratio: float | None = None
    garment_length_ratio: float | None = None


class FitResult(BaseModel):
    label: str
    scores: FitScores
    explanations: list[str] = Field(default_factory=list)


class ConfidenceResult(BaseModel):
    score: float
    level: str
    warnings: list[str] = Field(default_factory=list)


class QualityResult(BaseModel):
    pose_quality: float | None = None
    parsing_quality: float | None = None
    body_visibility: float | None = None
    quality_score: float | None = None
    silhouette_score: float | None = None


class Annotation(BaseModel):
    key: str
    label: str
    text: str
    x: float
    y: float
    value: float | None = None


class ErrorResponse(BaseModel):
    code: str
    message: str


class FitAnalysisResponse(BaseModel):
    schema_version: str = "fit_analysis.v2"
    source: dict[str, Any] = Field(default_factory=dict)
    fit_label: str
    measurements: FitScores
    confidence: ConfidenceResult
    fit: FitResult
    quality: QualityResult = Field(default_factory=QualityResult)
    hotspots: list[Annotation] = Field(default_factory=list)
    annotations: list[Annotation] = Field(default_factory=list)


class TryOnResultResponse(BaseModel):
    job_id: str
    status: str
    person_image_url: str | None = None
    cloth_image_url: str | None = None
    result_image_url: str | None = None
    confidence: ConfidenceResult | None = None
    fit: FitResult | None = None
    quality: QualityResult | None = None
    annotations: list[Annotation] = Field(default_factory=list)
    hotspots: list[Annotation] = Field(default_factory=list)
    fit_analysis: FitAnalysisResponse | None = None
    message: str
    error: ErrorResponse | None = None
