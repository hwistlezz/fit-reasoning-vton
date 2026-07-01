#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.fit_analyzer import analyze_fit


MEASUREMENT_KEYS = (
    "shoulder_ratio",
    "torso_width_ratio",
    "sleeve_length_ratio",
    "garment_length_ratio",
)
QUALITY_KEYS = (
    "pose_quality",
    "parsing_quality",
    "body_visibility",
    "quality_score",
    "silhouette_score",
)
HOTSPOT_POSITIONS = {
    "shoulder_ratio": ("shoulder", "Shoulder", 50.0, 27.0),
    "torso_width_ratio": ("torso", "Torso", 50.0, 47.0),
    "sleeve_length_ratio": ("sleeve", "Sleeve", 72.0, 48.0),
    "garment_length_ratio": ("length", "Length", 50.0, 68.0),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test fit_analysis.v2 loader compatibility from an existing features_fit CSV."
    )
    parser.add_argument(
        "--features-csv",
        type=Path,
        default=Path("backend/datasets/features_fit_10k_v3.csv"),
        help="Existing features_fit CSV path.",
    )
    parser.add_argument("--limit", type=int, default=25, help="Number of rows to check.")
    return parser.parse_args()


def read_rows(path: Path, limit: int) -> list[dict[str, str]]:
    if limit <= 0:
        raise ValueError("--limit must be positive.")
    with path.open(newline="", encoding="utf-8-sig") as file:
        rows = []
        for index, row in enumerate(csv.DictReader(file)):
            if index >= limit:
                break
            rows.append(row)
    return rows


def optional_float(row: dict[str, str], key: str) -> float | None:
    value = (row.get(key) or "").strip()
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if not math.isfinite(parsed):
        return None
    return parsed


def build_hotspots(row: dict[str, str]) -> list[dict[str, Any]]:
    hotspots = []
    for metric_key, (key, label, x, y) in HOTSPOT_POSITIONS.items():
        value = optional_float(row, metric_key)
        if value is None:
            continue
        hotspots.append(
            {
                "key": key,
                "label": label,
                "text": f"{label} hotspot generated from {metric_key}.",
                "x": x,
                "y": y,
                "value": value,
            }
        )
    return hotspots


def build_compact_payload(row: dict[str, str]) -> dict[str, Any]:
    features = {key: optional_float(row, key) for key in (*MEASUREMENT_KEYS, *QUALITY_KEYS)}
    confidence = optional_float(row, "confidence")
    return {
        "schema_version": "fit_analysis.v2",
        "pair_id": row.get("pair_id") or row.get("case_id") or "UNKNOWN",
        "split": row.get("split", ""),
        "fit_label": row.get("fit_label") or "unknown",
        "confidence": 0.0 if confidence is None else confidence,
        "quality_score": features.get("quality_score"),
        "features": features,
        "hotspots": build_hotspots(row),
        "annotations": build_hotspots(row),
    }


def update_coverage(summary: dict[str, Any], row: dict[str, str]) -> None:
    for key in (*MEASUREMENT_KEYS, *QUALITY_KEYS, "confidence", "fit_label"):
        if (row.get(key) or "").strip():
            summary["coverage"][key] = summary["coverage"].get(key, 0) + 1

    label = row.get("fit_label") or "unknown"
    summary["fit_label_counts"][label] = summary["fit_label_counts"].get(label, 0) + 1


def run_smoke(rows: list[dict[str, str]], features_csv: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "features_csv": str(features_csv),
        "checked": len(rows),
        "loader_errors": 0,
        "coverage": {},
        "fit_label_counts": {},
        "sample_fit_analysis": None,
    }

    with tempfile.TemporaryDirectory(prefix="fit-analysis-v2-smoke-") as tmp:
        tmp_dir = Path(tmp)
        for index, row in enumerate(rows):
            update_coverage(summary, row)
            payload = build_compact_payload(row)
            pair_id = str(payload["pair_id"])
            fit_path = tmp_dir / f"{pair_id}.fit.json"
            fit_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            try:
                analysis = analyze_fit(pair_id, result_image_url=None, fit_result_path=fit_path)
                analysis_payload = analysis.to_response_payload()
            except Exception:
                summary["loader_errors"] += 1
                continue

            if index == 0:
                summary["sample_fit_analysis"] = analysis_payload

    for key, count in list(summary["coverage"].items()):
        summary["coverage"][key] = {
            "non_empty": count,
            "pct": round(count / max(1, len(rows)) * 100, 2),
        }
    return summary


def main() -> int:
    args = parse_args()
    rows = read_rows(args.features_csv, args.limit)
    summary = run_smoke(rows, args.features_csv)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["loader_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
