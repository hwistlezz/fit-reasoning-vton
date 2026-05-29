from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TYPE_COUNTS = {
    "wearing_annotation": 0,
    "pair_annotation": 0,
    "unknown": 0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect AIHub annotation JSON files and summarize their structure."
    )
    parser.add_argument("--input", required=True, help="JSON file or directory containing JSON files.")
    parser.add_argument("--output", required=True, help="Path to save report.json.")
    parser.add_argument("--limit", type=int, default=None, help="Only inspect the first N JSON files.")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"--input does not exist: {input_path}")
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be zero or a positive integer.")

    return args


def find_json_files(input_path: Path, limit: int | None) -> list[Path]:
    if input_path.is_file():
        files = [input_path] if input_path.suffix.lower() == ".json" else []
    else:
        files = sorted(path for path in input_path.rglob("*.json") if path.is_file())

    if limit is not None:
        return files[:limit]
    return files


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def first_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    return {}


def pair_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        candidates = []
        for key in ("pairs", "pair", "annotations", "annotation", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates.extend(value)
        if not candidates:
            for value in payload.values():
                if isinstance(value, list):
                    candidates.extend(value)
    else:
        return []

    return [
        item
        for item in candidates
        if isinstance(item, dict)
        and all(isinstance(item.get(key), str) and item.get(key) for key in ("from", "to", "result"))
    ]


def is_wearing_annotation(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False

    info = first_dict(payload.get("info"))
    annotation = first_dict(payload.get("annotation"))
    has_identity = bool(info.get("model_id") or info.get("cloth_id"))
    has_annotation = "segmentation" in annotation or "keypoint" in annotation
    return has_identity and has_annotation


def infer_annotation_type(payload: Any) -> str:
    if pair_records(payload):
        return "pair_annotation"
    if is_wearing_annotation(payload):
        return "wearing_annotation"
    return "unknown"


def inspect_files(json_files: list[Path]) -> dict[str, Any]:
    type_counts = dict(TYPE_COUNTS)
    parsed_files = 0
    failed_files = 0
    samples: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for path in json_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            annotation_type = infer_annotation_type(payload)
            parsed_files += 1
            type_counts[annotation_type] += 1
            samples.append({"path": display_path(path), "type": annotation_type})
        except (OSError, json.JSONDecodeError) as exc:
            failed_files += 1
            errors.append({"path": display_path(path), "error": str(exc)})

    return {
        "total_json_files": len(json_files),
        "parsed_files": parsed_files,
        "failed_files": failed_files,
        "type_counts": type_counts,
        "samples": samples,
        "errors": errors,
    }


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    json_files = find_json_files(input_path, args.limit)

    report = {
        "input": display_path(input_path),
        **inspect_files(json_files),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote report: {output_path}")


if __name__ == "__main__":
    main()
