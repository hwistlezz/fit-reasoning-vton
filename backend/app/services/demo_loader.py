from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from backend.app.schemas.demo import (
    DemoAnalysis,
    DemoCaseInfo,
    DemoCompareResponse,
    DemoImageSet,
    DemoMetric,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DEMO_ROOT = REPO_ROOT / "backend" / "demo"


class DemoNotFoundError(Exception):
    """Raised when a requested demo pair cannot be found."""


class DemoLoader:
    def __init__(self, demo_root: Path = DEFAULT_DEMO_ROOT) -> None:
        self.demo_root = demo_root
        self.samples_dir = demo_root / "samples"
        self.analysis_dir = demo_root / "analysis"

    def list_samples(self) -> list[dict[str, Any]]:
        payload = self._read_json(self.samples_dir / "demo_index.example.json")
        if not isinstance(payload, list):
            raise ValueError("demo index must be a JSON array.")
        return [self._require_sample_item(item) for item in payload]

    def build_artifact_compare(self, pair_id: str) -> DemoCompareResponse:
        return self._build_compare_response(
            page="artifact-compare",
            pair_id=pair_id,
            metrics_path=self.samples_dir / "artifact_compare_metrics.example.json",
        )

    def build_model_compare(self, pair_id: str) -> DemoCompareResponse:
        return self._build_compare_response(
            page="model-compare",
            pair_id=pair_id,
            metrics_path=self.samples_dir / "model_compare_metrics.example.json",
        )

    def _build_compare_response(
        self,
        page: Literal["artifact-compare", "model-compare"],
        pair_id: str,
        metrics_path: Path,
    ) -> DemoCompareResponse:
        sample = self._find_sample(pair_id)
        return DemoCompareResponse(
            page=page,
            pair_id=pair_id,
            case=self._build_case(sample),
            images=self._build_images(pair_id, page),
            metrics=self._load_metrics(metrics_path, pair_id),
            analysis=self._load_analysis(pair_id),
        )

    def _find_sample(self, pair_id: str) -> dict[str, Any]:
        for sample in self.list_samples():
            if sample["pair_id"] == pair_id:
                return sample
        raise DemoNotFoundError(f"demo pair not found: {pair_id}")

    @staticmethod
    def _build_case(sample: dict[str, Any]) -> DemoCaseInfo:
        return DemoCaseInfo(
            category=sample["category"],
            pose_type=sample["pose_type"],
            difficulty=sample["difficulty"],
            gt_fit_label=sample["gt_fit_label"],
            input_confidence=float(sample["input_confidence"]),
        )

    @staticmethod
    def _build_images(pair_id: str, page: Literal["artifact-compare", "model-compare"]) -> DemoImageSet:
        return DemoImageSet(
            person=f"/assets/image/{pair_id}.jpg",
            cloth=f"/assets/cloth/{pair_id}.jpg",
            target_worn=f"/assets/worn/{pair_id}.jpg",
            basic_lora=f"/assets/basic_lora/{pair_id}.png" if page == "artifact-compare" else None,
            stableviton=f"/assets/stableviton/{pair_id}.png" if page == "model-compare" else None,
            artifact_lora=f"/assets/artifact_lora/{pair_id}.png",
            agnostic=f"/assets/agnostic-v3.2/{pair_id}.jpg",
            agnostic_mask=f"/assets/agnostic-mask/{pair_id}.png",
            densepose=f"/assets/image-densepose/{pair_id}.png",
            skeleton_preview=f"/assets/skeleton-preview/{pair_id}.png",
        )

    def _load_metrics(self, metrics_path: Path, pair_id: str) -> list[DemoMetric]:
        payload = self._read_json(metrics_path)
        metrics_payload = self._extract_pair_payload(payload, pair_id, "metrics")
        if not isinstance(metrics_payload, list):
            raise ValueError(f"metrics for {pair_id} must be a JSON array.")
        return [DemoMetric(**metric) for metric in metrics_payload]

    def _load_analysis(self, pair_id: str) -> DemoAnalysis:
        candidates = (
            self.analysis_dir / f"{pair_id}.json",
            self.analysis_dir / f"{pair_id}.example.json",
        )
        for path in candidates:
            if path.is_file():
                payload = self._read_json(path)
                if not isinstance(payload, dict):
                    raise ValueError(f"analysis for {pair_id} must be a JSON object.")
                return DemoAnalysis(**payload)
        raise DemoNotFoundError(f"demo analysis not found: {pair_id}")

    @staticmethod
    def _extract_pair_payload(payload: Any, pair_id: str, nested_key: str) -> Any:
        if isinstance(payload, dict):
            if pair_id in payload:
                return payload[pair_id]
            if payload.get("pair_id") == pair_id and nested_key in payload:
                return payload[nested_key]
        raise DemoNotFoundError(f"demo payload not found for pair: {pair_id}")

    @staticmethod
    def _require_sample_item(item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            raise ValueError("demo index items must be JSON objects.")
        required_keys = {
            "pair_id",
            "category",
            "pose_type",
            "difficulty",
            "gt_fit_label",
            "input_confidence",
        }
        missing_keys = sorted(required_keys - set(item))
        if missing_keys:
            raise ValueError(f"demo index item missing keys: {missing_keys}")
        return item

    @staticmethod
    def _read_json(path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise DemoNotFoundError(f"demo file not found: {path}") from exc


demo_loader = DemoLoader()
