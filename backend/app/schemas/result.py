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


class TryOnResultResponse(BaseModel):
    job_id: str
    status: str
    person_image_url: str | None = None
    cloth_image_url: str | None = None
    result_image_url: str | None = None
    confidence: ConfidenceResult | None = None
    fit: FitResult | None = None
    annotations: list[Annotation] = Field(default_factory=list)
    message: str
    error: ErrorResponse | None = None
