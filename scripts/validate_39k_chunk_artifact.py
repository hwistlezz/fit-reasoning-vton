#!/usr/bin/env python
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from typing import Any

from PIL import Image


PERSON_SPACE_FOLDERS = {
    "image",
    "worn",
    "fit",
    "image-parse",
    "image-densepose",
    "agnostic-v3.2",
    "agnostic-mask",
}
CLOTH_SPACE_FOLDERS = {
    "cloth",
    "cloth-mask",
}
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
MASK_EXTS = (".png", ".jpg", ".jpeg")


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader], list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_pair_id(value: str | None) -> str:
    return (value or "").strip().upper()


def candidate_names(folder: str, pair_id: str) -> list[str]:
    if folder == "openpose-json":
        return [f"{pair_id}_keypoints.json", f"{pair_id}.json"]
    if folder in {"image", "cloth", "worn", "fit", "agnostic-v3.2"}:
        return [f"{pair_id}{ext}" for ext in IMAGE_EXTS]
    return [f"{pair_id}{ext}" for ext in MASK_EXTS]


def split_aliases(split: str | None) -> list[str]:
    value = (split or "").strip().lower()
    aliases = [value] if value else []
    if value == "val":
        aliases.append("test")
    if value == "validation":
        aliases.extend(["val", "test"])
    return [item for item in aliases if item]


def find_artifact(root: Path, folder: str, pair_id: str, split: str | None) -> Path | None:
    roots = [root / folder]
    for alias in split_aliases(split):
        roots.append(root / alias / folder)
    for base in roots:
        for name in candidate_names(folder, pair_id):
            path = base / name
            if path.exists():
                return path
    return None


def find_fit_json(root: Path, pair_id: str, split: str | None) -> Path | None:
    roots = [root / "fit"]
    for alias in split_aliases(split):
        roots.append(root / alias / "fit")
    for base in roots:
        path = base / f"{pair_id}.json"
        if path.exists():
            return path
    return None


def load_image(path: Path) -> tuple[tuple[int, int] | None, str | None, Image.Image | None]:
    try:
        with Image.open(path) as image:
            image.load()
            return image.size, None, image.copy()
    except Exception as exc:
        return None, str(exc), None


def count_unique_labels(image: Image.Image, max_labels: int = 512) -> int:
    gray = image.convert("L")
    del max_labels
    return sum(1 for count in gray.histogram() if count)


def nonzero_pixels(image: Image.Image) -> int:
    gray = image.convert("L")
    return sum(gray.histogram()[1:])


def openpose_keypoint_stats(
    path: Path,
    min_confidence: float,
    image_size: tuple[int, int] | None,
) -> tuple[int, int, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        people = data.get("people") or []
        if not people:
            return 0, 0, None
        values = people[0].get("pose_keypoints_2d") or people[0].get("keypoints") or []
        count = 0
        out_of_bounds = 0
        width, height = image_size or (None, None)
        for index in range(2, len(values), 3):
            try:
                confidence = float(values[index])
            except Exception:
                continue
            if confidence < min_confidence:
                continue
            count += 1
            if width is None or height is None:
                continue
            try:
                x = float(values[index - 2])
                y = float(values[index - 1])
            except Exception:
                continue
            if not (0 <= x <= width and 0 <= y <= height):
                out_of_bounds += 1
        return count, out_of_bounds, None
    except Exception as exc:
        return 0, 0, str(exc)


def load_fit_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return None, str(exc)


def manifest_pair_ids(path: Path) -> list[str]:
    pair_ids: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            pair_ids.append(normalize_pair_id(item.get("pair_id")))
    return pair_ids


def validate_manifest(path: Path | None, expected_pair_ids: list[str]) -> dict[str, Any]:
    if not path:
        return {"status": "not_provided"}
    actual = manifest_pair_ids(path)
    return {
        "status": "ok" if actual == expected_pair_ids else "mismatch",
        "path": str(path),
        "line_count": len(actual),
        "expected_line_count": len(expected_pair_ids),
        "pair_id_strict_alignment": actual == expected_pair_ids,
    }


def row_required_folders(args: argparse.Namespace) -> list[str]:
    folders = ["image", "cloth", "worn", "fit", "openpose-json", "image-parse", "cloth-mask"]
    if args.required_densepose:
        folders.append("image-densepose")
    if args.required_agnostic:
        folders.extend(["agnostic-v3.2", "agnostic-mask"])
    return folders


def select_rows(rows: list[dict[str, str]], args: argparse.Namespace) -> list[dict[str, str]]:
    if not args.limit:
        return rows

    forced_pair_ids = [normalize_pair_id(value) for value in args.force_pair]
    rows_by_pair_id = {
        normalize_pair_id(row.get("pair_id")): row
        for row in rows
        if normalize_pair_id(row.get("pair_id"))
    }
    selected: list[dict[str, str]] = []
    selected_pair_ids: set[str] = set()
    for pair_id in forced_pair_ids:
        row = rows_by_pair_id.get(pair_id)
        if row and pair_id not in selected_pair_ids:
            selected.append(row)
            selected_pair_ids.add(pair_id)

    for row in rows:
        if len(selected) >= args.limit:
            break
        pair_id = normalize_pair_id(row.get("pair_id"))
        if pair_id in selected_pair_ids:
            continue
        selected.append(row)
        selected_pair_ids.add(pair_id)
    return selected


def validate_row(
    row: dict[str, str],
    root: Path,
    required_folders: list[str],
    min_keypoints: int,
    min_confidence: float,
) -> tuple[dict[str, Any], dict[str, str] | None, dict[str, Any] | None]:
    pair_id = normalize_pair_id(row.get("pair_id"))
    split = row.get("split")
    errors: list[str] = []
    missing: list[str] = []
    zero_byte: list[str] = []
    load_errors: dict[str, str] = {}
    sizes: dict[str, tuple[int, int]] = {}
    artifact_paths: dict[str, str] = {}
    parse_unique_labels: int | None = None
    cloth_mask_nonzero: int | None = None
    densepose_nonzero: int | None = None
    agnostic_mask_nonzero: int | None = None
    openpose_count: int | None = None
    openpose_out_of_bounds: int | None = None
    openpose_path: Path | None = None
    fit_json_path: Path | None = None
    fit_json_status: dict[str, Any] = {"exists": False}

    for folder in required_folders:
        path = find_artifact(root, folder, pair_id, split)
        if not path:
            missing.append(folder)
            continue
        artifact_paths[folder] = str(path)
        if path.stat().st_size == 0:
            zero_byte.append(folder)
            continue
        if folder == "openpose-json":
            openpose_path = path
            continue

        size, error, image = load_image(path)
        if error or image is None or size is None:
            load_errors[folder] = error or "unknown image load error"
            continue
        sizes[folder] = size
        if size[0] <= 0 or size[1] <= 0:
            errors.append(f"{folder}:invalid_width_height")
        if folder == "image-parse":
            parse_unique_labels = count_unique_labels(image)
            if parse_unique_labels <= 1:
                errors.append("image_parse_unique_label<=1")
        elif folder == "cloth-mask":
            cloth_mask_nonzero = nonzero_pixels(image)
            if cloth_mask_nonzero <= 0:
                errors.append("cloth_mask_empty")
        elif folder == "image-densepose":
            densepose_nonzero = nonzero_pixels(image)
            if densepose_nonzero <= 0:
                errors.append("image_densepose_empty")
        elif folder == "agnostic-mask":
            agnostic_mask_nonzero = nonzero_pixels(image)
            if agnostic_mask_nonzero <= 0:
                errors.append("agnostic_mask_empty")

    image_size = sizes.get("image")
    if openpose_path:
        openpose_count, openpose_out_of_bounds, error = openpose_keypoint_stats(
            openpose_path,
            min_confidence,
            image_size,
        )
        if error:
            load_errors["openpose-json"] = error
        elif openpose_count < min_keypoints:
            errors.append(f"openpose_valid_keypoints<{min_keypoints}")
        elif openpose_out_of_bounds:
            errors.append("openpose_keypoints_out_of_image_bounds")

    fit_json_path = find_fit_json(root, pair_id, split)
    if fit_json_path:
        fit_json_status = {"exists": True, "path": str(fit_json_path)}
        if fit_json_path.stat().st_size == 0:
            fit_json_status["zero_byte"] = True
            errors.append("fit_json_zero_byte")
        else:
            payload, error = load_fit_json(fit_json_path)
            if error:
                fit_json_status["load_error"] = error
                errors.append("fit_json_load_error")
            else:
                payload_pair_id = normalize_pair_id(str(payload.get("pair_id", ""))) if isinstance(payload, dict) else ""
                fit_json_status["pair_id"] = payload_pair_id
                if payload_pair_id and payload_pair_id != pair_id:
                    errors.append("fit_json_pair_id_mismatch")

    person_space_size_errors: list[str] = []
    cloth_space_size_errors: list[str] = []
    if image_size:
        for folder in sorted(PERSON_SPACE_FOLDERS):
            size = sizes.get(folder)
            if not size:
                continue
            if size != image_size:
                message = (
                    f"person_space_size_mismatch:{folder}={size[0]}x{size[1]} vs "
                    f"image={image_size[0]}x{image_size[1]}"
                )
                person_space_size_errors.append(message)
                errors.append(message)

    cloth_size = sizes.get("cloth")
    if cloth_size:
        for folder in sorted(CLOTH_SPACE_FOLDERS):
            size = sizes.get(folder)
            if not size:
                continue
            if size != cloth_size:
                message = (
                    f"cloth_space_size_mismatch:{folder}={size[0]}x{size[1]} vs "
                    f"cloth={cloth_size[0]}x{cloth_size[1]}"
                )
                cloth_space_size_errors.append(message)
                errors.append(message)

    if missing:
        errors.append("missing_required_file")
    if zero_byte:
        errors.append("zero_byte_file")
    if load_errors:
        errors.append("load_error")

    ok = not errors
    detail = {
        "pair_id": pair_id,
        "status": "ok" if ok else "failed",
        "missing_files": missing,
        "zero_byte_files": zero_byte,
        "image_load_errors": load_errors,
        "width_height": {key: f"{value[0]}x{value[1]}" for key, value in sizes.items()},
        "person_space_size_errors": person_space_size_errors,
        "cloth_space_size_errors": cloth_space_size_errors,
        "openpose_valid_keypoints": openpose_count,
        "openpose_out_of_bounds_keypoints": openpose_out_of_bounds,
        "image_parse_unique_labels": parse_unique_labels,
        "cloth_mask_nonzero_pixels": cloth_mask_nonzero,
        "densepose_nonzero_pixels": densepose_nonzero,
        "agnostic_mask_nonzero_pixels": agnostic_mask_nonzero,
        "fit_json": fit_json_status,
        "artifact_paths": artifact_paths,
        "reason": ";".join(errors),
    }
    bad_row = None
    manifest_row = None
    if ok:
        manifest_row = {"pair_id": pair_id, "split": split or "", "artifacts": artifact_paths}
    else:
        bad_row = {"pair_id": pair_id, "reason": detail["reason"]}
    return detail, bad_row, manifest_row


def validate(args: argparse.Namespace) -> dict[str, Any]:
    metadata = Path(args.metadata)
    root = Path(args.artifact_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows, fields = read_csv(metadata)
    source_row_count = len(rows)
    rows = select_rows(rows, args)
    pair_ids = [normalize_pair_id(row.get("pair_id")) for row in rows]
    pair_id_counts = Counter(pair_ids)
    duplicate_pair_ids = sorted(pair_id for pair_id, count in pair_id_counts.items() if count > 1)
    required = row_required_folders(args)

    details: list[dict[str, Any]] = []
    bad_rows: list[dict[str, str]] = []
    final_rows: list[dict[str, str]] = []
    manifest_rows: list[dict[str, Any]] = []
    for row in rows:
        detail, bad_row, manifest_row = validate_row(
            row,
            root,
            required,
            args.min_openpose_keypoints,
            args.min_openpose_confidence,
        )
        details.append(detail)
        if bad_row:
            bad_rows.append(bad_row)
        else:
            final_rows.append(row)
            if manifest_row:
                manifest_rows.append(manifest_row)

    input_manifest = Path(args.input_manifest) if args.input_manifest else None
    if input_manifest is None and args.limit is None:
        input_manifest = root / "manifest.jsonl"
    manifest_check = validate_manifest(input_manifest if input_manifest and input_manifest.exists() else None, pair_ids)
    generated_manifest_pair_ids = [item["pair_id"] for item in manifest_rows]
    generated_manifest_check = {
        "line_count": len(generated_manifest_pair_ids),
        "metadata_final_count": len(final_rows),
        "pair_id_strict_alignment": generated_manifest_pair_ids
        == [normalize_pair_id(row.get("pair_id")) for row in final_rows],
    }

    if duplicate_pair_ids:
        bad_rows.extend({"pair_id": pair_id, "reason": "duplicate_pair_id"} for pair_id in duplicate_pair_ids)

    person_space_size_error_count = sum(
        len(detail.get("person_space_size_errors") or [])
        for detail in details
    )
    cloth_space_size_error_count = sum(
        len(detail.get("cloth_space_size_errors") or [])
        for detail in details
    )

    details_path = output_dir / "validation_details.jsonl"
    with details_path.open("w", encoding="utf-8") as f:
        for detail in details:
            f.write(json.dumps(detail, ensure_ascii=False) + "\n")

    write_csv(output_dir / "bad_pairs_auto.csv", bad_rows, ["pair_id", "reason"])
    write_csv(output_dir / "metadata_chunk_final.csv", final_rows, fields)
    with (output_dir / "manifest_chunk_final.jsonl").open("w", encoding="utf-8") as f:
        for item in manifest_rows:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    report = {
        "metadata": str(metadata),
        "artifact_root": str(root),
        "required_folders": required,
        "source_row_count": source_row_count,
        "limit": args.limit,
        "forced_pairs": [normalize_pair_id(value) for value in args.force_pair],
        "row_count": len(rows),
        "ok_count": len(final_rows),
        "failed_count": len(bad_rows),
        "person_space_size_errors": person_space_size_error_count,
        "cloth_space_size_errors": cloth_space_size_error_count,
        "duplicate_pair_ids": duplicate_pair_ids,
        "input_manifest_check": manifest_check,
        "generated_manifest_check": generated_manifest_check,
        "outputs": {
            "validation_details": str(details_path),
            "bad_pairs_auto": str(output_dir / "bad_pairs_auto.csv"),
            "metadata_chunk_final": str(output_dir / "metadata_chunk_final.csv"),
            "manifest_chunk_final": str(output_dir / "manifest_chunk_final.jsonl"),
        },
        "status": "passed" if not bad_rows and not duplicate_pair_ids else "failed",
    }
    (output_dir / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one 39k artifact chunk.")
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--input-manifest")
    parser.add_argument("--required-densepose", action="store_true")
    parser.add_argument("--required-agnostic", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force-pair", action="append", default=[])
    parser.add_argument("--min-openpose-keypoints", type=int, default=5)
    parser.add_argument("--min-openpose-confidence", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    report = validate(parse_args())
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
