"""Audit whether StableVITON layout artifacts align with source or target.

The current AIHub layout keeps both a source person image and a target/worn
image. StableVITON, however, uses the ``image`` field as the first-stage image.
This helper checks whether agnostic artifacts are visually closer to the source
``image`` or to the ``worn`` target and writes an ignored diagnostic report.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageOps


DEFAULT_EVAL_ROOT = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
    r"\fixed_eval_100_lora_comparison_exif_fixed\fixed_eval_100_data"
)
DEFAULT_OUTPUT_ROOT = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
    r"\fixed_eval_100_lora_comparison_exif_fixed\review"
)


@dataclass(frozen=True)
class PairMetric:
    pair_id: str
    agnostic_mse_to_source_keep_region: float | None
    agnostic_mse_to_target_keep_region: float | None
    agnostic_closer_to: str
    keep_region_ratio: float
    mask_region_ratio: float
    source_target_mse: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit source/target alignment in a StableVITON-style layout."
    )
    parser.add_argument("--eval-root", type=Path, default=DEFAULT_EVAL_ROOT)
    parser.add_argument("--pairs-file", type=Path, default=None)
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
    eval_root = args.eval_root
    pairs_file = args.pairs_file or eval_root / "test_pairs.txt"
    summary_json = args.summary_json or args.output_root / "layout_alignment_audit_summary.json"
    raw_csv = args.raw_csv or args.output_root / "layout_alignment_audit.csv"
    sheet_path = args.sheet or args.output_root / "layout_alignment_audit_sheet.jpg"

    pairs = read_pairs(pairs_file)[: args.limit]
    metrics = [audit_pair(eval_root, pair_id) for pair_id in pairs]
    write_csv(raw_csv, metrics)
    summary = build_summary(eval_root, pairs_file, metrics)
    write_json(summary_json, summary)
    make_sheet(eval_root, metrics, sheet_path, args.sheet_count, args.tile_width, args.tile_height)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def read_pairs(path: Path) -> list[str]:
    pair_ids: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        image_name, _cloth_name = stripped.split()
        pair_ids.append(Path(image_name).stem)
    return pair_ids


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


def first_existing(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def artifact_path(eval_root: Path, split: str, dirname: str, pair_id: str, suffixes: tuple[str, ...]) -> Path | None:
    return first_existing([eval_root / split / dirname / f"{pair_id}{suffix}" for suffix in suffixes])


def mse(a: np.ndarray, b: np.ndarray) -> float:
    return float(((a - b) ** 2).mean())


def audit_pair(eval_root: Path, pair_id: str) -> PairMetric:
    source = load_rgb(eval_root / "test" / "image" / f"{pair_id}.jpg")
    target = load_rgb(eval_root / "test" / "worn" / f"{pair_id}.jpg")
    agnostic = load_rgb(eval_root / "test" / "agnostic-v3.2" / f"{pair_id}.jpg")

    mask_path = artifact_path(eval_root, "test", "agnostic-mask", pair_id, ("_mask.png", ".png", ".jpg"))
    if mask_path is None:
        keep_mask = np.ones(source.shape[:2], dtype=bool)
        mask_region_ratio = 0.0
    else:
        mask = load_mask(mask_path)
        # Raw AIHub agnostic-mask white area corresponds to the erased/unknown
        # region in our prepared layout. Compare the known keep-region only.
        keep_mask = mask < 128
        mask_region_ratio = float((mask >= 128).mean())

    if not keep_mask.any():
        agn_to_source = None
        agn_to_target = None
        closer_to = "no_keep_region"
        keep_region_ratio = 0.0
    else:
        agn_to_source = mse(agnostic[keep_mask], source[keep_mask])
        agn_to_target = mse(agnostic[keep_mask], target[keep_mask])
        closer_to = "source" if agn_to_source < agn_to_target else "target"
        keep_region_ratio = float(keep_mask.mean())

    return PairMetric(
        pair_id=pair_id,
        agnostic_mse_to_source_keep_region=agn_to_source,
        agnostic_mse_to_target_keep_region=agn_to_target,
        agnostic_closer_to=closer_to,
        keep_region_ratio=keep_region_ratio,
        mask_region_ratio=mask_region_ratio,
        source_target_mse=mse(source, target),
    )


def build_summary(eval_root: Path, pairs_file: Path, metrics: list[PairMetric]) -> dict[str, Any]:
    source_count = sum(1 for item in metrics if item.agnostic_closer_to == "source")
    target_count = sum(1 for item in metrics if item.agnostic_closer_to == "target")
    source_values = [
        item.agnostic_mse_to_source_keep_region
        for item in metrics
        if item.agnostic_mse_to_source_keep_region is not None
    ]
    target_values = [
        item.agnostic_mse_to_target_keep_region
        for item in metrics
        if item.agnostic_mse_to_target_keep_region is not None
    ]
    return {
        "task": "stableviton_layout_alignment_audit",
        "eval_root": str(eval_root),
        "pairs_file": str(pairs_file),
        "pair_count": len(metrics),
        "agnostic_closer_to_source_count": source_count,
        "agnostic_closer_to_target_count": target_count,
        "agnostic_closer_to_source_rate": round(source_count / len(metrics), 6) if metrics else None,
        "mean_agnostic_mse_to_source_keep_region": round(mean(source_values), 6) if source_values else None,
        "mean_agnostic_mse_to_target_keep_region": round(mean(target_values), 6) if target_values else None,
        "mean_mask_region_ratio": round(mean(item.mask_region_ratio for item in metrics), 6) if metrics else None,
        "mean_source_target_mse": round(mean(item.source_target_mse for item in metrics), 6) if metrics else None,
        "interpretation": (
            "If agnostic_closer_to_source_rate is near 1.0, prepared agnostic artifacts are aligned "
            "with source person images, while StableVITON training uses the image field as first_stage_key."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, metrics: list[PairMetric]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(PairMetric.__dataclass_fields__.keys()))
        writer.writeheader()
        for item in metrics:
            writer.writerow(item.__dict__)


def load_pil(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail(size, Image.Resampling.BILINEAR)
        canvas = Image.new("RGB", size, "white")
        x = (size[0] - image.width) // 2
        y = (size[1] - image.height) // 2
        canvas.paste(image, (x, y))
        return canvas


def maybe_tile(path: Path | None, size: tuple[int, int]) -> Image.Image:
    if path is None or not path.exists():
        tile = Image.new("RGB", size, "white")
        draw = ImageDraw.Draw(tile)
        draw.rectangle((0, 0, size[0] - 1, size[1] - 1), outline=(180, 0, 0))
        draw.text((8, 8), "missing", fill=(180, 0, 0))
        return tile
    return load_pil(path, size)


def output_path(output_root: Path, method: str, pair_id: str) -> Path:
    if method == "baseline":
        return output_root / "rank4_module8" / "baseline" / "pair" / f"{pair_id}_{pair_id}.jpg"
    if method == "rank8_module16":
        return output_root / "rank8_module16" / "lora" / "pair" / f"{pair_id}_{pair_id}.jpg"
    raise ValueError(f"unknown method: {method}")


def make_sheet(
    eval_root: Path,
    metrics: list[PairMetric],
    sheet_path: Path,
    sheet_count: int,
    tile_width: int,
    tile_height: int,
) -> None:
    output_root = eval_root.parent
    tile_size = (tile_width, tile_height)
    label_h = 44
    columns = [
        "source image",
        "target worn",
        "agnostic",
        "agn-mask",
        "parse",
        "densepose",
        "baseline",
        "rank8-m16",
    ]
    ranked = sorted(
        metrics,
        key=lambda item: (
            -math.inf
            if item.agnostic_mse_to_target_keep_region is None or item.agnostic_mse_to_source_keep_region is None
            else item.agnostic_mse_to_target_keep_region - item.agnostic_mse_to_source_keep_region
        ),
        reverse=True,
    )[:sheet_count]
    sheet = Image.new("RGB", (tile_width * len(columns), (tile_height + label_h) * (len(ranked) + 1)), "white")
    draw = ImageDraw.Draw(sheet)
    for col_idx, label in enumerate(columns):
        draw.text((col_idx * tile_width + 6, 10), label, fill=(0, 0, 0))

    for row_idx, item in enumerate(ranked, start=1):
        pair_id = item.pair_id
        row_y = row_idx * (tile_height + label_h)
        paths = [
            eval_root / "test" / "image" / f"{pair_id}.jpg",
            eval_root / "test" / "worn" / f"{pair_id}.jpg",
            eval_root / "test" / "agnostic-v3.2" / f"{pair_id}.jpg",
            artifact_path(eval_root, "test", "agnostic-mask", pair_id, ("_mask.png", ".png", ".jpg")),
            artifact_path(eval_root, "test", "image-parse", pair_id, (".png", ".jpg")),
            artifact_path(eval_root, "test", "image-densepose", pair_id, (".jpg", ".png")),
            output_path(output_root, "baseline", pair_id),
            output_path(output_root, "rank8_module16", pair_id),
        ]
        score_text = (
            f"{pair_id} src={fmt(item.agnostic_mse_to_source_keep_region)} "
            f"tgt={fmt(item.agnostic_mse_to_target_keep_region)}"
        )
        for col_idx, path in enumerate(paths):
            x = col_idx * tile_width
            draw.text((x + 6, row_y + 4), score_text if col_idx == 0 else columns[col_idx], fill=(0, 0, 0))
            sheet.paste(maybe_tile(path, tile_size), (x, row_y + label_h))

    sheet_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(sheet_path, quality=95)


def fmt(value: float | None) -> str:
    if value is None:
        return "na"
    return f"{value:.1f}"


if __name__ == "__main__":
    raise SystemExit(main())
