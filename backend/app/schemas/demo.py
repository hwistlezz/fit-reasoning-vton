from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DemoCaseInfo(BaseModel):
    category: str
    pose_type: str
    difficulty: str
    gt_fit_label: str
    input_confidence: float


class DemoImageSet(BaseModel):
    person: str
    cloth: str
    target_worn: str
    basic_lora: str | None = None
    stableviton: str | None = None
    artifact_lora: str
    agnostic: str | None = None
    agnostic_mask: str | None = None
    densepose: str | None = None
    skeleton_preview: str | None = None


class DemoMetric(BaseModel):
    key: str
    title: str
    description: str | None = None
    baseline_label: str
    method_label: str
    baseline_value: float
    method_value: float
    direction: Literal["higher_is_better", "lower_is_better"]
    improvement_text: str


class DemoHotspot(BaseModel):
    key: str
    label: str
    text: str
    x: float
    y: float
    value: float | None = None


class DemoKeypoint(BaseModel):
    name: str
    x: float
    y: float
    confidence: float


class DemoAnalysis(BaseModel):
    fit: dict[str, Any]
    pose: dict[str, Any]
    hotspots: list[DemoHotspot] = Field(default_factory=list)
    keypoints: list[DemoKeypoint] = Field(default_factory=list)
    reliability: dict[str, Any]


class DemoCompareResponse(BaseModel):
    page: Literal["artifact-compare", "model-compare"]
    pair_id: str
    case: DemoCaseInfo
    images: DemoImageSet
    metrics: list[DemoMetric] = Field(default_factory=list)
    analysis: DemoAnalysis


class DemoSamplesResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    count: int
