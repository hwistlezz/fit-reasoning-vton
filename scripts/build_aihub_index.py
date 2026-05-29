from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ITEM_COLUMNS = [
    "item_id",
    "model_id",
    "cloth_id",
    "image_path",
    "width",
    "height",
    "angle",
    "pose",
    "annotation_path",
    "has_segmentation",
    "has_keypoint",
]
PAIR_COLUMNS = [
    "pair_id",
    "from_image",
    "to_image",
    "result_image",
    "annotation_path",
]
TYPE_COUNTS = {
    "wearing_annotation": 0,
    "pair_annotation": 0,
    "unknown": 0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build AIHub item index and pair manifest CSV files from annotation JSON."
    )
    parser.add_argument("--raw-root", required=True, help="JSON file or directory containing JSON files.")
    parser.add_argument("--out-items", required=True, help="Path to save items.csv.")
    parser.add_argument("--out-pairs", required=True, help="Path to save pairs.csv.")
    parser.add_argument("--save-report", required=True, help="Path to save report.json.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N JSON files.")
    args = parser.parse_args()

    raw_root = Path(args.raw_root)
    if not raw_root.exists():
        parser.error(f"--raw-root does not exist: {raw_root}")
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be zero or a positive integer.")

    return args


def find_json_files(raw_root: Path, limit: int | None) -> list[Path]:
    if raw_root.is_file():
        files = [raw_root] if raw_root.suffix.lower() == ".json" else []
    else:
        files = sorted(path for path in raw_root.rglob("*.json") if path.is_file())

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


def build_item_row(payload: dict[str, Any], path: Path) -> dict[str, str]:
    info = first_dict(payload.get("info"))
    annotation = first_dict(payload.get("annotation"))
    image = info.get("image") if isinstance(info.get("image"), dict) else {}

    return {
        "item_id": str(info.get("id", "")),
        "model_id": str(info.get("model_id", "")),
        "cloth_id": str(info.get("cloth_id", "")),
        "image_path": str(image.get("path", "")),
        "width": str(image.get("width", "")),
        "height": str(image.get("height", "")),
        "angle": str(image.get("angle", "")),
        "pose": str(image.get("pose", "")),
        "annotation_path": display_path(path),
        "has_segmentation": str("segmentation" in annotation).lower(),
        "has_keypoint": str("keypoint" in annotation).lower(),
    }


def build_pair_rows(payload: Any, path: Path, start_index: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for offset, pair in enumerate(pair_records(payload), start=start_index):
        rows.append(
            {
                "pair_id": f"case_{offset:06d}",
                "from_image": pair["from"],
                "to_image": pair["to"],
                "result_image": pair["result"],
                "annotation_path": display_path(path),
            }
        )
    return rows


def write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def build_index(json_files: list[Path]) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    item_rows: list[dict[str, str]] = []
    pair_rows: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    type_counts = dict(TYPE_COUNTS)
    parsed_files = 0
    failed_files = 0
    skipped_count = 0

    for path in json_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failed_files += 1
            errors.append({"path": display_path(path), "error": str(exc)})
            continue

        parsed_files += 1
        annotation_type = infer_annotation_type(payload)
        type_counts[annotation_type] += 1

        if annotation_type == "wearing_annotation" and isinstance(payload, dict):
            item_rows.append(build_item_row(payload, path))
        elif annotation_type == "pair_annotation":
            next_pair_index = len(pair_rows) + 1
            pair_rows.extend(build_pair_rows(payload, path, next_pair_index))
        else:
            skipped_count += 1

    report = {
        "total_json_files": len(json_files),
        "parsed_files": parsed_files,
        "failed_files": failed_files,
        "item_count": len(item_rows),
        "pair_count": len(pair_rows),
        "skipped_count": skipped_count,
        "type_counts": type_counts,
        "errors": errors,
    }
    return item_rows, pair_rows, report


def main() -> None:
    args = parse_args()
    raw_root = Path(args.raw_root)
    out_items = Path(args.out_items)
    out_pairs = Path(args.out_pairs)
    save_report = Path(args.save_report)

    json_files = find_json_files(raw_root, args.limit)
    item_rows, pair_rows, report = build_index(json_files)
    report = {"raw_root": display_path(raw_root), **report}

    write_csv(out_items, ITEM_COLUMNS, item_rows)
    write_csv(out_pairs, PAIR_COLUMNS, pair_rows)
    save_report.parent.mkdir(parents=True, exist_ok=True)
    save_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote items: {out_items}")
    print(f"Wrote pairs: {out_pairs}")
    print(f"Wrote report: {save_report}")


if __name__ == "__main__":
    main()
