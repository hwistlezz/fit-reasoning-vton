"""Audit readiness for a target-aligned StableVITON training layout.

StableVITON training uses the ``image`` field as the first-stage image. For a
correct target-reconstruction training layout, the target worn image and its
conditioning artifacts must be generated from the same target image. This script
checks whether such target-side artifacts exist in the current AIHub dataset and
summarizes why source-side artifacts should not be reused as target-side inputs.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageOps


DEFAULT_DATA_ROOT = Path(r"D:\GitHub\fit-reasoning-vton\backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full")
DEFAULT_OUTPUT_ROOT = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
    r"\fixed_eval_100_lora_comparison_exif_fixed\review"
)


TARGET_ARTIFACT_CANDIDATES: dict[str, tuple[str, ...]] = {
    "target_image": ("worn/{pair_id}.jpg",),
    "target_agnostic": (
        "worn-agnostic-v3.2/{pair_id}.jpg",
        "worn-agnostic-v3.2/{pair_id}.png",
        "target-agnostic-v3.2/{pair_id}.jpg",
        "target-agnostic-v3.2/{pair_id}.png",
    ),
    "target_agnostic_mask": (
        "worn-agnostic-mask/{pair_id}_mask.png",
        "worn-agnostic-mask/{pair_id}.png",
        "target-agnostic-mask/{pair_id}_mask.png",
        "target-agnostic-mask/{pair_id}.png",
    ),
    "target_densepose": (
        "worn-image-densepose/{pair_id}.jpg",
        "worn-image-densepose/{pair_id}.png",
        "target-image-densepose/{pair_id}.jpg",
        "target-image-densepose/{pair_id}.png",
    ),
    "target_parse": (
        "worn-image-parse/{pair_id}.png",
        "target-image-parse/{pair_id}.png",
    ),
    "target_openpose_json": (
        "worn-openpose-json/{pair_id}_keypoints.json",
        "worn-openpose-json/{pair_id}.json",
        "target-openpose-json/{pair_id}_keypoints.json",
        "target-openpose-json/{pair_id}.json",
    ),
}

SOURCE_ARTIFACT_CANDIDATES: dict[str, tuple[str, ...]] = {
    "source_image": ("image/{pair_id}.jpg",),
    "cloth": ("cloth/{pair_id}.jpg",),
    "source_agnostic": ("agnostic-v3.2/{pair_id}.jpg", "agnostic-v3.2/{pair_id}.png"),
    "source_agnostic_mask": ("agnostic-mask/{pair_id}_mask.png", "agnostic-mask/{pair_id}.png"),
    "source_densepose": ("image-densepose/{pair_id}.jpg", "image-densepose/{pair_id}.png"),
    "source_parse": ("image-parse/{pair_id}.png",),
    "source_openpose_json": ("openpose-json/{pair_id}_keypoints.json", "openpose-json/{pair_id}.json"),
}


@dataclass(frozen=True)
class TargetReadiness:
    pair_id: str
    source_artifacts_ready: bool
    target_artifacts_ready: bool
    missing_target_artifacts: tuple[str, ...]
    agnostic_mse_to_source_keep_region: float | None
    agnostic_mse_to_target_keep_region: float | None
    source_agnostic_closer_to: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether target-side StableVITON conditioning artifacts are available."
    )
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--sheet-count", type=int, default=12)
    parser.add_argument("--tile-width", type=int, default=180)
    parser.add_argument("--tile-height", type=int, default=240)
    parser.add_argument("--summary-json", type=Path, default=None)
    parser.add_argument("--raw-csv", type=Path, default=None)
    parser.add_argument("--sheet", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pair_ids = read_manifest_pair_ids(args.data_root / "manifest.jsonl")[: args.limit]
    rows = [audit_pair(args.data_root, pair_id) for pair_id in pair_ids]

    summary_json = args.summary_json or args.output_root / "target_aligned_readiness_summary.json"
    raw_csv = args.raw_csv or args.output_root / "target_aligned_readiness.csv"
    sheet_path = args.sheet or args.output_root / "target_aligned_readiness_sheet.jpg"

    write_csv(raw_csv, rows)
    summary = build_summary(args.data_root, rows)
    write_json(summary_json, summary)
    make_sheet(args.data_root, rows, sheet_path, args.sheet_count, args.tile_width, args.tile_height)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def read_manifest_pair_ids(path: Path) -> list[str]:
    pair_ids: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        row = json.loads(stripped)
        pair_id = row.get("pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError(f"manifest line {line_number} is missing pair_id")
        pair_ids.append(pair_id)
    return pair_ids


def first_existing(data_root: Path, pair_id: str, patterns: tuple[str, ...]) -> Path | None:
    for pattern in patterns:
        path = data_root / pattern.format(pair_id=pair_id)
        if path.is_file():
            return path
    return None


def paths_ready(data_root: Path, pair_id: str, specs: dict[str, tuple[str, ...]]) -> tuple[bool, list[str]]:
    missing: list[str] = []
    for name, patterns in specs.items():
        if first_existing(data_root, pair_id, patterns) is None:
            missing.append(name)
    return not missing, missing


def load_rgb(path: Path, size: tuple[int, int] = (384, 512)) -> np.ndarray:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        if image.size != size:
            image = image.resize(size, Image.Resampling.BILINEAR)
        return np.asarray(image, dtype=np.float32)


def load_mask(path: Path, size: tuple[int, int] = (384, 512)) -> np.ndarray:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("L")
        if image.size != size:
            image = image.resize(size, Image.Resampling.NEAREST)
        return np.asarray(image, dtype=np.uint8)


def mse(a: np.ndarray, b: np.ndarray) -> float:
    return float(((a - b) ** 2).mean())


def audit_pair(data_root: Path, pair_id: str) -> TargetReadiness:
    source_ready, _missing_source = paths_ready(data_root, pair_id, SOURCE_ARTIFACT_CANDIDATES)
    target_ready, missing_target = paths_ready(data_root, pair_id, TARGET_ARTIFACT_CANDIDATES)

    source_path = first_existing(data_root, pair_id, SOURCE_ARTIFACT_CANDIDATES["source_image"])
    target_path = first_existing(data_root, pair_id, TARGET_ARTIFACT_CANDIDATES["target_image"])
    agnostic_path = first_existing(data_root, pair_id, SOURCE_ARTIFACT_CANDIDATES["source_agnostic"])
    mask_path = first_existing(data_root, pair_id, SOURCE_ARTIFACT_CANDIDATES["source_agnostic_mask"])

    agn_to_source: float | None = None
    agn_to_target: float | None = None
    closer_to = "unavailable"
    if source_path and target_path and agnostic_path:
        source = load_rgb(source_path)
        target = load_rgb(target_path)
        agnostic = load_rgb(agnostic_path)
        if mask_path:
            mask = load_mask(mask_path)
            keep = mask < 128
        else:
            keep = np.ones(source.shape[:2], dtype=bool)
        if keep.any():
            agn_to_source = mse(agnostic[keep], source[keep])
            agn_to_target = mse(agnostic[keep], target[keep])
            closer_to = "source" if agn_to_source < agn_to_target else "target"
        else:
            closer_to = "no_keep_region"

    return TargetReadiness(
        pair_id=pair_id,
        source_artifacts_ready=source_ready,
        target_artifacts_ready=target_ready,
        missing_target_artifacts=tuple(missing_target),
        agnostic_mse_to_source_keep_region=agn_to_source,
        agnostic_mse_to_target_keep_region=agn_to_target,
        source_agnostic_closer_to=closer_to,
    )


def build_summary(data_root: Path, rows: list[TargetReadiness]) -> dict[str, Any]:
    missing_counts: dict[str, int] = {name: 0 for name in TARGET_ARTIFACT_CANDIDATES}
    for row in rows:
        for artifact_name in row.missing_target_artifacts:
            missing_counts[artifact_name] += 1

    source_mse = [
        row.agnostic_mse_to_source_keep_region
        for row in rows
        if row.agnostic_mse_to_source_keep_region is not None
    ]
    target_mse = [
        row.agnostic_mse_to_target_keep_region
        for row in rows
        if row.agnostic_mse_to_target_keep_region is not None
    ]
    source_closer_count = sum(1 for row in rows if row.source_agnostic_closer_to == "source")
    target_closer_count = sum(1 for row in rows if row.source_agnostic_closer_to == "target")
    target_ready_count = sum(1 for row in rows if row.target_artifacts_ready)

    return {
        "task": "target_aligned_stableviton_readiness",
        "data_root": str(data_root),
        "checked_count": len(rows),
        "source_artifacts_ready_count": sum(1 for row in rows if row.source_artifacts_ready),
        "target_artifacts_ready_count": target_ready_count,
        "target_artifacts_not_ready_count": len(rows) - target_ready_count,
        "missing_target_artifact_counts": missing_counts,
        "source_agnostic_closer_to_source_count": source_closer_count,
        "source_agnostic_closer_to_target_count": target_closer_count,
        "source_agnostic_closer_to_source_rate": round(source_closer_count / len(rows), 6) if rows else None,
        "mean_source_agnostic_mse_to_source_keep_region": round(mean(source_mse), 6) if source_mse else None,
        "mean_source_agnostic_mse_to_target_keep_region": round(mean(target_mse), 6) if target_mse else None,
        "can_build_correct_target_training_layout": target_ready_count == len(rows) and bool(rows),
        "recommendation": (
            "Do not reuse source-side agnostic/densepose/parse/openpose artifacts for target-aligned "
            "StableVITON training. Generate target-side artifacts from worn images first."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[TargetReadiness]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(TargetReadiness.__dataclass_fields__.keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def load_tile(path: Path | None, size: tuple[int, int]) -> Image.Image:
    if path is None or not path.exists():
        tile = Image.new("RGB", size, "white")
        draw = ImageDraw.Draw(tile)
        draw.rectangle((0, 0, size[0] - 1, size[1] - 1), outline=(180, 0, 0))
        draw.text((8, 8), "missing", fill=(180, 0, 0))
        return tile
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail(size, Image.Resampling.BILINEAR)
        tile = Image.new("RGB", size, "white")
        tile.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
        return tile


def make_sheet(
    data_root: Path,
    rows: list[TargetReadiness],
    sheet_path: Path,
    sheet_count: int,
    tile_width: int,
    tile_height: int,
) -> None:
    columns = [
        "source image",
        "target worn",
        "source agnostic",
        "source densepose",
        "target agnostic",
        "target densepose",
    ]
    label_h = 44
    tile_size = (tile_width, tile_height)
    shown = rows[:sheet_count]
    sheet = Image.new("RGB", (tile_width * len(columns), (tile_height + label_h) * (len(shown) + 1)), "white")
    draw = ImageDraw.Draw(sheet)
    for col_idx, label in enumerate(columns):
        draw.text((col_idx * tile_width + 6, 10), label, fill=(0, 0, 0))

    for row_idx, row in enumerate(shown, start=1):
        pair_id = row.pair_id
        paths = [
            first_existing(data_root, pair_id, SOURCE_ARTIFACT_CANDIDATES["source_image"]),
            first_existing(data_root, pair_id, TARGET_ARTIFACT_CANDIDATES["target_image"]),
            first_existing(data_root, pair_id, SOURCE_ARTIFACT_CANDIDATES["source_agnostic"]),
            first_existing(data_root, pair_id, SOURCE_ARTIFACT_CANDIDATES["source_densepose"]),
            first_existing(data_root, pair_id, TARGET_ARTIFACT_CANDIDATES["target_agnostic"]),
            first_existing(data_root, pair_id, TARGET_ARTIFACT_CANDIDATES["target_densepose"]),
        ]
        y = row_idx * (tile_height + label_h)
        for col_idx, path in enumerate(paths):
            x = col_idx * tile_width
            label = pair_id if col_idx == 0 else columns[col_idx]
            draw.text((x + 6, y + 4), label, fill=(0, 0, 0))
            sheet.paste(load_tile(path, tile_size), (x, y + label_h))

    sheet_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(sheet_path, quality=95)


if __name__ == "__main__":
    raise SystemExit(main())
