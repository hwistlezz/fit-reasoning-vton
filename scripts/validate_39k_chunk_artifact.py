#!/usr/bin/env python
from __future__ import annotations

import argparse
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
    "cloth-mask",
    "image-densepose",
    "agnostic-v3.2",
    "agnostic-mask",
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


def load_image(path: Path) -> tuple[tuple[int, int] | None, str | None, Image.Image | None]:
    try:
        with Image.open(path) as image:
            image.load()
            return image.size, None, image.copy()
    except Exception as exc:
        return None, str(exc), None


def count_unique_labels(image: Image.Image, max_labels: int = 512) -> int:
    gray = image.convert("L")
    labels = set(gray.getdata())
    if len(labels) > max_labels:
        return len(labels)
    return len(labels)


def nonzero_pixels(image: Image.Image) -> int:
    gray = image.convert("L")
    return sum(1 for value in gray.getdata() if value != 0)


def openpose_valid_keypoints(path: Path, min_confidence: float) -> tuple[int, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        people = data.get("people") or []
        if not people:
            return 0, None
        values = people[0].get("pose_keypoints_2d") or people[0].get("keypoints") or []
        count = 0
        for index in range(2, len(values), 3):
            try:
                if float(values[index]) >= min_confidence:
                    count += 1
            except Exception:
                continue
        return count, None
    except Exception as exc:
        return 0, str(exc)


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
            openpose_count, error = openpose_valid_keypoints(path, min_confidence)
            if error:
                load_errors[folder] = error
            elif openpose_count < min_keypoints:
                errors.append(f"openpose_valid_keypoints<{min_keypoints}")
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

    person_sizes = {folder: size for folder, size in sizes.items() if folder in PERSON_SPACE_FOLDERS}
    if person_sizes:
        reference_folder, reference_size = next(iter(person_sizes.items()))
        for folder, size in person_sizes.items():
            if size != reference_size:
                errors.append(
                    f"size_mismatch:{folder}={size[0]}x{size[1]} vs "
                    f"{reference_folder}={reference_size[0]}x{reference_size[1]}"
                )

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
        "openpose_valid_keypoints": openpose_count,
        "image_parse_unique_labels": parse_unique_labels,
        "cloth_mask_nonzero_pixels": cloth_mask_nonzero,
        "densepose_nonzero_pixels": densepose_nonzero,
        "agnostic_mask_nonzero_pixels": agnostic_mask_nonzero,
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
    pair_ids = [normalize_pair_id(row.get("pair_id")) for row in rows]
    duplicate_pair_ids = sorted({pair_id for pair_id in pair_ids if pair_ids.count(pair_id) > 1})
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

    input_manifest = Path(args.input_manifest) if args.input_manifest else root / "manifest.jsonl"
    manifest_check = validate_manifest(input_manifest if input_manifest.exists() else None, pair_ids)
    generated_manifest_pair_ids = [item["pair_id"] for item in manifest_rows]
    generated_manifest_check = {
        "line_count": len(generated_manifest_pair_ids),
        "metadata_final_count": len(final_rows),
        "pair_id_strict_alignment": generated_manifest_pair_ids
        == [normalize_pair_id(row.get("pair_id")) for row in final_rows],
    }

    if duplicate_pair_ids:
        bad_rows.extend({"pair_id": pair_id, "reason": "duplicate_pair_id"} for pair_id in duplicate_pair_ids)

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
        "row_count": len(rows),
        "ok_count": len(final_rows),
        "failed_count": len(bad_rows),
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
    parser.add_argument("--min-openpose-keypoints", type=int, default=5)
    parser.add_argument("--min-openpose-confidence", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    report = validate(parse_args())
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
