from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_DEMO_ROOT = Path("backend/demo")
DEFAULT_INDEX = Path("backend/demo/samples/demo_index.example.json")
DEFAULT_OUTPUT_JSON = Path("backend/training/outputs/demo_asset_validation/report.json")


@dataclass(frozen=True)
class AssetSpec:
    key: str
    candidates: tuple[str, ...]


REQUIRED_ASSETS: tuple[AssetSpec, ...] = (
    AssetSpec("person_image", ("assets/image/{pair_id}.jpg",)),
    AssetSpec("cloth", ("assets/cloth/{pair_id}.jpg",)),
    AssetSpec("target_worn", ("assets/worn/{pair_id}.jpg",)),
    AssetSpec("basic_lora", ("assets/basic_lora/{pair_id}.png",)),
    AssetSpec("stableviton", ("assets/stableviton/{pair_id}.png",)),
    AssetSpec("artifact_lora", ("assets/artifact_lora/{pair_id}.png",)),
)

OPTIONAL_ASSETS: tuple[AssetSpec, ...] = (
    AssetSpec("agnostic", ("assets/agnostic-v3.2/{pair_id}.jpg",)),
    AssetSpec("agnostic_mask", ("assets/agnostic-mask/{pair_id}.png",)),
    AssetSpec("densepose", ("assets/image-densepose/{pair_id}.png",)),
    AssetSpec("skeleton_preview", ("assets/skeleton-preview/{pair_id}.png",)),
    AssetSpec(
        "analysis",
        (
            "analysis/{pair_id}.json",
            "analysis/{pair_id}.example.json",
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate local demo assets for compare API sample packages.")
    parser.add_argument("--demo-root", type=Path, default=DEFAULT_DEMO_ROOT)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        items = _read_demo_index(args.index)
        selected_items = _apply_limit(items, args.limit)
        pair_reports = [_validate_pair(args.demo_root, item["pair_id"]) for item in selected_items]
        report = _build_report(args, total_pairs=len(items), pair_reports=pair_reports)
        _write_json(args.output_json, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if args.strict and report["required_missing_count"] > 0:
            print(
                f"[STRICT] required assets missing: {report['required_missing_count']}",
                file=sys.stderr,
            )
            return 1
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


def _read_demo_index(index_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"demo index must be a JSON array: {index_path}")

    items: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"demo index item {index} must be a JSON object.")
        pair_id = item.get("pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError(f"demo index item {index} is missing pair_id.")
        items.append(item)
    return items


def _apply_limit(items: list[dict[str, Any]], limit: int | None) -> list[dict[str, Any]]:
    if limit is None:
        return items
    if limit < 0:
        raise ValueError("--limit must be non-negative.")
    return items[:limit]


def _validate_pair(demo_root: Path, pair_id: str) -> dict[str, Any]:
    required_exists, required_missing = _validate_specs(demo_root, pair_id, REQUIRED_ASSETS)
    optional_exists, optional_missing = _validate_specs(demo_root, pair_id, OPTIONAL_ASSETS)
    return {
        "pair_id": pair_id,
        "required": {
            "missing": required_missing,
            "exists": required_exists,
        },
        "optional": {
            "missing": optional_missing,
            "exists": optional_exists,
        },
    }


def _validate_specs(demo_root: Path, pair_id: str, specs: tuple[AssetSpec, ...]) -> tuple[list[str], list[str]]:
    exists: list[str] = []
    missing: list[str] = []

    for spec in specs:
        existing_path = _first_existing_path(demo_root, pair_id, spec)
        if existing_path is None:
            missing.append(_format_missing(spec, pair_id))
        else:
            exists.append(_display_path(existing_path))

    return exists, missing


def _first_existing_path(demo_root: Path, pair_id: str, spec: AssetSpec) -> Path | None:
    for pattern in spec.candidates:
        candidate = demo_root / pattern.format(pair_id=pair_id)
        if candidate.is_file():
            return candidate
    return None


def _format_missing(spec: AssetSpec, pair_id: str) -> str:
    if len(spec.candidates) == 1:
        return spec.candidates[0].format(pair_id=pair_id)
    return " | ".join(pattern.format(pair_id=pair_id) for pattern in spec.candidates)


def _build_report(args: argparse.Namespace, total_pairs: int, pair_reports: list[dict[str, Any]]) -> dict[str, Any]:
    required_missing_count = sum(len(pair_report["required"]["missing"]) for pair_report in pair_reports)
    optional_missing_count = sum(len(pair_report["optional"]["missing"]) for pair_report in pair_reports)
    return {
        "demo_root": _display_path(args.demo_root),
        "index": _display_path(args.index),
        "total_pairs": total_pairs,
        "checked_pairs": len(pair_reports),
        "strict": bool(args.strict),
        "required_missing_count": required_missing_count,
        "optional_missing_count": optional_missing_count,
        "pairs": pair_reports,
    }


def _display_path(path: Path) -> str:
    return path.as_posix()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
