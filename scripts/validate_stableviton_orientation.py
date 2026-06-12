#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from stableviton_orientation import EXIF_ORIENTATION_TAG


IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
MASK_EXTS = (".png", ".jpg", ".jpeg")
BASE_FOLDERS = ("image", "cloth", "worn", "openpose-json", "image-parse", "cloth-mask")
PERSON_SPACE_FOLDERS = ("image", "worn", "image-parse", "agnostic-v3.2", "agnostic-mask", "image-densepose")
CONTACT_FOLDERS = ("image", "worn", "agnostic-v3.2", "image-densepose", "image-parse", "cloth")


def normalize_pair_id(value: str | None) -> str:
    return (value or "").strip().upper()


def read_metadata(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return [dict(row) for row in csv.DictReader(f)]


def candidate_names(folder: str, pair_id: str) -> list[str]:
    if folder == "openpose-json":
        return [f"{pair_id}_keypoints.json", f"{pair_id}.json"]
    if folder in {"image", "cloth", "worn", "agnostic-v3.2"}:
        return [f"{pair_id}{ext}" for ext in IMAGE_EXTS]
    return [f"{pair_id}{ext}" for ext in MASK_EXTS] + [f"{pair_id}_mask.png", f"{pair_id}.0001.png"]


def split_aliases(split: str | None) -> list[str]:
    value = (split or "").strip().lower()
    aliases = [value] if value else []
    if value == "val":
        aliases.append("test")
    if value == "validation":
        aliases.extend(["val", "test"])
    return [alias for alias in aliases if alias]


def find_artifact(root: Path, folder: str, pair_id: str, split: str | None = None) -> Path | None:
    roots = [root / folder]
    for alias in split_aliases(split):
        roots.append(root / alias / folder)
    for base in roots:
        for name in candidate_names(folder, pair_id):
            path = base / name
            if path.is_file():
                return path
    return None


def infer_pair_ids(root: Path) -> list[str]:
    image_dir = root / "image"
    if not image_dir.is_dir():
        return []
    return sorted(path.stem.upper() for path in image_dir.iterdir() if path.is_file())


def orientation(width: int | None, height: int | None) -> str:
    if not width or not height:
        return "missing"
    if width > height:
        return "landscape"
    if height > width:
        return "portrait"
    return "square"


def image_header(path: Path | None) -> dict[str, Any]:
    if not path:
        return {"exists": False}
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            exif_orientation = exif.get(EXIF_ORIENTATION_TAG) if exif else None
            width, height = image.size
            if exif_orientation in {5, 6, 7, 8}:
                transposed = (height, width)
            else:
                transposed = (width, height)
            return {
                "exists": True,
                "path": str(path),
                "width": width,
                "height": height,
                "mode": image.mode,
                "orientation": orientation(width, height),
                "exif_orientation": exif_orientation,
                "exif_transposed_width": transposed[0],
                "exif_transposed_height": transposed[1],
                "exif_transposed_orientation": orientation(*transposed),
            }
    except Exception as exc:
        return {"exists": True, "path": str(path), "load_error": repr(exc)}


def openpose_bounds(path: Path | None, width: int | None, height: int | None) -> dict[str, Any]:
    if not path:
        return {"exists": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        people = payload.get("people") or []
        values = []
        if people:
            values = people[0].get("pose_keypoints_2d") or people[0].get("keypoints") or []
        valid = 0
        out_of_bounds = 0
        for index in range(0, len(values) - 2, 3):
            try:
                x = float(values[index])
                y = float(values[index + 1])
                confidence = float(values[index + 2])
            except (TypeError, ValueError):
                continue
            if confidence <= 0.05:
                continue
            valid += 1
            if width and height and not (0 <= x <= width and 0 <= y <= height):
                out_of_bounds += 1
        return {
            "exists": True,
            "path": str(path),
            "valid_keypoints": valid,
            "out_of_bounds_keypoints": out_of_bounds,
        }
    except Exception as exc:
        return {"exists": True, "path": str(path), "load_error": repr(exc)}


def build_sample(rows: list[dict[str, str]], args: argparse.Namespace) -> list[dict[str, str]]:
    forced_values = args.force_pair or ["EP00000002"]
    forced = {normalize_pair_id(value) for value in forced_values}
    by_pair = {normalize_pair_id(row.get("pair_id")): row for row in rows if normalize_pair_id(row.get("pair_id"))}
    selected: list[dict[str, str]] = []
    for pair_id in sorted(forced):
        if pair_id in by_pair:
            selected.append(by_pair[pair_id])
    selected.extend(row for row in rows[: args.first_count] if row not in selected)
    remaining = [row for row in rows if row not in selected]
    random.Random(args.seed).shuffle(remaining)
    selected.extend(remaining[: max(0, args.sample_size - len(selected))])
    return selected[: args.sample_size]


def check_pair(root: Path, row: dict[str, str], folders: tuple[str, ...]) -> dict[str, Any]:
    pair_id = normalize_pair_id(row.get("pair_id"))
    split = row.get("split")
    headers: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for folder in folders:
        if folder == "openpose-json":
            continue
        headers[folder] = image_header(find_artifact(root, folder, pair_id, split))
        if not headers[folder].get("exists"):
            errors.append(f"{folder}:missing")
        elif headers[folder].get("load_error"):
            errors.append(f"{folder}:load_error")

    for folder in ("image", "cloth", "worn"):
        header = headers.get(folder, {})
        if header.get("exif_orientation") not in (None, 1):
            errors.append(f"{folder}:exif_orientation_not_normalized")
        if header.get("orientation") != "portrait":
            errors.append(f"{folder}:not_portrait")

    for folder in ("agnostic-v3.2", "image-densepose", "image-parse", "agnostic-mask", "cloth-mask"):
        header = headers.get(folder, {})
        if header and header.get("orientation") != "portrait":
            errors.append(f"{folder}:not_portrait")

    person_sizes = {
        folder: (headers[folder].get("width"), headers[folder].get("height"))
        for folder in PERSON_SPACE_FOLDERS
        if folder in headers and headers[folder].get("exists")
    }
    if person_sizes:
        reference = person_sizes.get("image") or next(iter(person_sizes.values()))
        for folder, size in person_sizes.items():
            if size != reference:
                errors.append(f"{folder}:person_space_size_mismatch")

    if headers.get("cloth", {}).get("exists") and headers.get("cloth-mask", {}).get("exists"):
        cloth_size = (headers["cloth"].get("width"), headers["cloth"].get("height"))
        cloth_mask_size = (headers["cloth-mask"].get("width"), headers["cloth-mask"].get("height"))
        if cloth_size != cloth_mask_size:
            errors.append("cloth-mask:cloth_size_mismatch")

    image_header_data = headers.get("image", {})
    openpose = openpose_bounds(
        find_artifact(root, "openpose-json", pair_id, split),
        image_header_data.get("width"),
        image_header_data.get("height"),
    )
    if openpose.get("load_error"):
        errors.append("openpose-json:load_error")
    elif openpose.get("out_of_bounds_keypoints", 0) > 0:
        errors.append("openpose-json:keypoints_out_of_image_bounds")

    return {
        "pair_id": pair_id,
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "headers": headers,
        "openpose": openpose,
    }


def write_header_csv(path: Path, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "pair_id",
        "status",
        "errors",
        "folder",
        "exists",
        "width",
        "height",
        "mode",
        "orientation",
        "exif_orientation",
        "exif_transposed_width",
        "exif_transposed_height",
        "exif_transposed_orientation",
        "path",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for result in results:
            for folder, header in result["headers"].items():
                row = {
                    "pair_id": result["pair_id"],
                    "status": result["status"],
                    "errors": "|".join(result["errors"]),
                    "folder": folder,
                    **header,
                }
                writer.writerow(row)


def paste_thumb(sheet: Image.Image, draw: ImageDraw.ImageDraw, path: Path | None, box: tuple[int, int, int, int]) -> None:
    if not path:
        draw.rectangle(box, fill=(245, 245, 245), outline=(180, 180, 180))
        draw.text((box[0] + 4, box[1] + 4), "missing", fill=(80, 80, 80))
        return
    try:
        with Image.open(path) as image:
            thumb = image.convert("RGB")
            thumb.thumbnail((box[2] - box[0], box[3] - box[1]))
            x = box[0] + ((box[2] - box[0]) - thumb.width) // 2
            y = box[1] + ((box[3] - box[1]) - thumb.height) // 2
            sheet.paste(thumb, (x, y))
            draw.rectangle(box, outline=(210, 210, 210))
    except Exception:
        draw.rectangle(box, fill=(245, 245, 245), outline=(180, 180, 180))
        draw.text((box[0] + 4, box[1] + 4), "load error", fill=(80, 80, 80))


def write_contact_sheet(path: Path, root: Path, rows: list[dict[str, str]], title: str) -> None:
    rows = rows[:40] or [{"pair_id": "NO_ROWS"}]
    tile_w, tile_h = 128, 176
    left_w = 170
    row_h = tile_h + 40
    width = left_w + len(CONTACT_FOLDERS) * tile_w
    height = 40 + len(rows) * row_h
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
    draw.text((8, 10), title, fill=(0, 0, 0), font=font)
    for index, row in enumerate(rows):
        pair_id = normalize_pair_id(row.get("pair_id"))
        split = row.get("split")
        y = 40 + index * row_h
        draw.text((6, y + 6), pair_id, fill=(0, 0, 0), font=font)
        for col, folder in enumerate(CONTACT_FOLDERS):
            x = left_w + col * tile_w
            box = (x, y, x + tile_w - 3, y + tile_h)
            paste_thumb(sheet, draw, find_artifact(root, folder, pair_id, split), box)
            draw.text((x + 4, y + tile_h + 3), folder, fill=(70, 70, 70), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=90)


def run(args: argparse.Namespace) -> dict[str, Any]:
    artifact_root = Path(args.artifact_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    folders = list(BASE_FOLDERS)
    if args.required_agnostic:
        folders.extend(["agnostic-v3.2", "agnostic-mask"])
    if args.required_densepose:
        folders.append("image-densepose")

    if args.metadata:
        rows = read_metadata(Path(args.metadata))
    else:
        rows = [{"pair_id": pair_id, "split": ""} for pair_id in infer_pair_ids(artifact_root)]
    sample_rows = build_sample(rows, args)
    results = [check_pair(artifact_root, row, tuple(folders)) for row in sample_rows]
    failed = [result for result in results if result["status"] != "passed"]

    header_csv = output_dir / args.header_csv_name
    write_header_csv(header_csv, results)
    contact_sheet = output_dir / args.contact_sheet_name
    write_contact_sheet(contact_sheet, artifact_root, sample_rows, "StableVITON orientation sanity")

    report = {
        "status": "passed" if not failed else "failed",
        "artifact_root": str(artifact_root),
        "metadata": str(args.metadata) if args.metadata else "",
        "row_count": len(rows),
        "sample_count": len(sample_rows),
        "failed_count": len(failed),
        "required_folders": folders,
        "forced_pairs": args.force_pair or ["EP00000002"],
        "failed_pairs": [
            {"pair_id": result["pair_id"], "errors": result["errors"]}
            for result in failed[:100]
        ],
        "outputs": {
            "header_csv": str(header_csv),
            "contact_sheet": str(contact_sheet),
        },
    }
    (output_dir / args.report_name).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fast EXIF/orientation sanity gate for StableVITON layouts.")
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--metadata")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--sample-size", type=int, default=300)
    parser.add_argument("--first-count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force-pair", action="append", default=[])
    parser.add_argument("--required-densepose", action="store_true")
    parser.add_argument("--required-agnostic", action="store_true")
    parser.add_argument("--report-name", default="orientation_sanity_report.json")
    parser.add_argument("--header-csv-name", default="orientation_header_sample.csv")
    parser.add_argument("--contact-sheet-name", default="orientation_sanity_contact_sheet.jpg")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
