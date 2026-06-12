#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import math
import random
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
MASK_EXTS = (".png", ".jpg", ".jpeg")
SHEET_FOLDERS = ("image", "cloth", "worn", "fit", "image-densepose", "agnostic-v3.2")


def normalize_pair_id(value: str | None) -> str:
    return (value or "").strip().upper()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader], list(reader.fieldnames or [])


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


def numeric(row: dict[str, str], names: tuple[str, ...], default: float = 0.0) -> float:
    for name in names:
        value = row.get(name)
        if value in (None, ""):
            continue
        try:
            return float(value)
        except ValueError:
            continue
    return default


def load_details(path: Path | None) -> dict[str, dict[str, Any]]:
    if not path or not path.exists():
        return {}
    details: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            pair_id = normalize_pair_id(item.get("pair_id"))
            if pair_id:
                details[pair_id] = item
    return details


def is_upper(row: dict[str, str]) -> bool:
    text = " ".join(
        str(row.get(name, ""))
        for name in ("category", "cloth_type", "class", "label", "item_category")
    ).lower()
    markers = (
        "upper",
        "top",
        "shirt",
        "tee",
        "t-shirt",
        "blouse",
        "sweater",
        "hoodie",
        "jacket",
        "outer",
        "cardigan",
    )
    return any(marker in text for marker in markers)


def is_vertical(row: dict[str, str]) -> bool:
    text = " ".join(str(row.get(name, "")) for name in ("angle", "pose", "view")).lower()
    markers = ("front", "back", "vertical", "standing", "정면", "후면", "p10", "p11")
    return any(marker in text for marker in markers)


def image_nonzero(path: Path | None) -> int:
    if not path or not path.exists():
        return 0
    try:
        with Image.open(path) as image:
            gray = image.convert("L")
            return sum(1 for value in gray.getdata() if value != 0)
    except Exception:
        return 0


def suspicious_rows(
    rows: list[dict[str, str]],
    details: dict[str, dict[str, Any]],
    artifact_root: Path,
    folder: str,
) -> list[dict[str, str]]:
    scored: list[tuple[int, dict[str, str]]] = []
    for row in rows:
        pair_id = normalize_pair_id(row.get("pair_id"))
        detail = details.get(pair_id, {})
        score = 0
        reason = detail.get("reason", "")
        if folder in reason:
            score += 100
        if folder in detail.get("missing_files", []):
            score += 100
        if folder in detail.get("zero_byte_files", []):
            score += 100
        if folder == "image-densepose":
            value = detail.get("densepose_nonzero_pixels")
            if value == 0:
                score += 50
        if folder == "agnostic-v3.2":
            path = find_artifact(artifact_root, folder, pair_id, row.get("split"))
            if image_nonzero(path) == 0:
                score += 25
        if score:
            scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], normalize_pair_id(item[1].get("pair_id"))))
    return [row for _, row in scored]


def sample_rows(rows: list[dict[str, str]], count: int, seed: int) -> list[dict[str, str]]:
    data = list(rows)
    random.Random(seed).shuffle(data)
    return data[: min(count, len(data))]


def draw_placeholder(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str) -> None:
    x0, y0, x1, y1 = box
    draw.rectangle(box, outline=(180, 180, 180), fill=(245, 245, 245))
    draw.text((x0 + 6, y0 + 6), text, fill=(80, 80, 80))


def paste_thumb(sheet: Image.Image, draw: ImageDraw.ImageDraw, path: Path | None, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    if not path or not path.exists():
        draw_placeholder(draw, box, "missing")
        return
    try:
        with Image.open(path) as image:
            thumb = image.convert("RGB")
            thumb.thumbnail((x1 - x0, y1 - y0))
            px = x0 + ((x1 - x0) - thumb.width) // 2
            py = y0 + ((y1 - y0) - thumb.height) // 2
            sheet.paste(thumb, (px, py))
            draw.rectangle(box, outline=(210, 210, 210))
    except Exception:
        draw_placeholder(draw, box, "load error")


def make_sheet(
    rows: list[dict[str, str]],
    artifact_root: Path,
    output: Path,
    title: str,
    columns: int,
    tile_w: int,
    tile_h: int,
) -> None:
    rows = list(rows)
    if not rows:
        rows = [{"pair_id": "NO_ROWS"}]
    folder_count = len(SHEET_FOLDERS)
    row_h = tile_h + 56
    cell_w = tile_w * folder_count
    sheet_w = cell_w * columns
    sheet_h = 48 + row_h * math.ceil(len(rows) / columns)
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((8, 8), title, fill=(0, 0, 0), font=font)
    for index, row in enumerate(rows):
        col = index % columns
        grid_row = index // columns
        x = col * cell_w
        y = 48 + grid_row * row_h
        pair_id = normalize_pair_id(row.get("pair_id"))
        for folder_index, folder in enumerate(SHEET_FOLDERS):
            bx = x + folder_index * tile_w
            box = (bx, y, bx + tile_w - 2, y + tile_h)
            path = find_artifact(artifact_root, folder, pair_id, row.get("split"))
            paste_thumb(sheet, draw, path, box)
            draw.text((bx + 4, y + tile_h + 2), folder, fill=(80, 80, 80), font=font)
        label = f"{pair_id} | {row.get('category', '')} | {row.get('angle', '')}"
        draw.text((x + 4, y + tile_h + 18), label[:120], fill=(0, 0, 0), font=font)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=90)


def build_groups(
    rows: list[dict[str, str]],
    details: dict[str, dict[str, Any]],
    artifact_root: Path,
    seed: int,
) -> dict[str, list[dict[str, str]]]:
    low_conf = sorted(
        rows,
        key=lambda row: numeric(row, ("confidence", "score", "fit_score"), default=1.0),
    )
    upper_rows = [row for row in rows if is_upper(row)]
    vertical_rows = [row for row in rows if is_vertical(row)]
    densepose_rows = suspicious_rows(rows, details, artifact_root, "image-densepose")
    agnostic_rows = suspicious_rows(rows, details, artifact_root, "agnostic-v3.2")
    return {
        "random_500": sample_rows(rows, 500, seed),
        "upper_300": sample_rows(upper_rows or rows, 300, seed + 1),
        "vertical_200": sample_rows(vertical_rows or rows, 200, seed + 2),
        "low_confidence_200": low_conf[: min(200, len(low_conf))],
        "densepose_suspicious_200": (densepose_rows or sample_rows(rows, 200, seed + 3))[:200],
        "agnostic_suspicious_200": (agnostic_rows or sample_rows(rows, 200, seed + 4))[:200],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    metadata = Path(args.metadata)
    artifact_root = Path(args.artifact_root)
    output_dir = Path(args.output_dir)
    rows, _ = read_csv(metadata)
    details = load_details(Path(args.validation_details) if args.validation_details else None)
    groups = build_groups(rows, details, artifact_root, args.seed)
    outputs: dict[str, str] = {}
    for name, group_rows in groups.items():
        output = output_dir / f"contact_sheets_{name}.jpg"
        make_sheet(
            group_rows,
            artifact_root,
            output,
            f"{metadata.stem} {name} ({len(group_rows)} rows)",
            args.columns,
            args.tile_width,
            args.tile_height,
        )
        outputs[name] = str(output)
    summary = {
        "metadata": str(metadata),
        "artifact_root": str(artifact_root),
        "output_dir": str(output_dir),
        "row_count": len(rows),
        "outputs": outputs,
    }
    (output_dir / "contact_sheet_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create review contact sheets for one 39k chunk.")
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--validation-details")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--columns", type=int, default=2)
    parser.add_argument("--tile-width", type=int, default=128)
    parser.add_argument("--tile-height", type=int, default=176)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run(parse_args()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
