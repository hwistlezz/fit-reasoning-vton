"""Build a fixed_eval_100 copy with only agnostic-mask inverted.

The source fixed_eval_100 dataset is treated as read-only. This helper copies
the test layout to an ignored output directory, keeps agnostic-v3.2 unchanged,
and writes agnostic-mask files as 255 - original.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from statistics import mean
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageOps


COPY_DIRS = (
    "image",
    "cloth",
    "worn",
    "agnostic-v3.2",
    "cloth-mask",
    "image-densepose",
    "image-parse",
    "openpose-json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_exif_fixed\fixed_eval_100_data"
        ),
    )
    parser.add_argument(
        "--output-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2_mask_inverted"
            r"\fixed_eval_100_data"
        ),
    )
    parser.add_argument(
        "--summary-json",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2_mask_inverted"
            r"\metrics\mask_inversion_summary.json"
        ),
    )
    parser.add_argument(
        "--stats-csv",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2_mask_inverted"
            r"\metrics\mask_inversion_stats.csv"
        ),
    )
    parser.add_argument(
        "--diagnostic-sheet",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2_mask_inverted"
            r"\contact_sheet\mask_inversion_input_diagnostic5.jpg"
        ),
    )
    parser.add_argument("--sample-count", type=int, default=5)
    parser.add_argument("--tile-width", type=int, default=192)
    parser.add_argument("--tile-height", type=int, default=256)
    parser.add_argument("--label-height", type=int, default=22)
    return parser.parse_args()


def read_pairs(path: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        person_name, cloth_name = stripped.split()
        pairs.append((person_name, cloth_name))
    return pairs


def pair_id_from_name(name: str) -> str:
    return Path(name).stem


def copy_file(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"missing required source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def mask_source_path(source_test: Path, pair_id: str) -> Path:
    mask_dir = source_test / "agnostic-mask"
    preferred = mask_dir / f"{pair_id}_mask.png"
    if preferred.exists():
        return preferred
    fallback = mask_dir / f"{pair_id}.png"
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"missing agnostic mask for {pair_id}: {preferred} or {fallback}")


def invert_mask(src: Path, dst: Path) -> dict[str, Any]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as image:
        image = ImageOps.exif_transpose(image).convert("L")
        original = np.asarray(image, dtype=np.uint8)
    inverted = np.uint8(255 - original)
    Image.fromarray(inverted, mode="L").save(dst)

    total = int(original.size)
    before_nonzero = int(np.count_nonzero(original))
    after_nonzero = int(np.count_nonzero(inverted))
    return {
        "source": str(src),
        "output": str(dst),
        "nonzero_ratio_before": round(before_nonzero / total, 6),
        "nonzero_ratio_after": round(after_nonzero / total, 6),
        "mean_before": round(float(original.mean()), 6),
        "mean_after": round(float(inverted.mean()), 6),
        "min_before": int(original.min()),
        "max_before": int(original.max()),
        "min_after": int(inverted.min()),
        "max_after": int(inverted.max()),
    }


def load_rgb(path: Path, size: tuple[int, int]) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        if image.size != size:
            image = image.resize(size, Image.Resampling.BILINEAR)
        return image.copy()


def make_input_diagnostic_sheet(
    *,
    source_test: Path,
    output_test: Path,
    pairs: list[tuple[str, str]],
    path: Path,
    sample_count: int,
    tile_width: int,
    tile_height: int,
    label_height: int,
) -> None:
    columns = [
        "image",
        "cloth",
        "target",
        "agnostic-v2",
        "mask-v2",
        "mask-inverted",
    ]
    selected = pairs[:sample_count]
    sheet = Image.new(
        "RGB",
        (tile_width * len(columns), (tile_height + label_height) * (len(selected) + 1)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for col_idx, label in enumerate(columns):
        draw.text((col_idx * tile_width + 4, 4), label, fill=(0, 0, 0))

    for row_idx, (person_name, cloth_name) in enumerate(selected, start=1):
        pair_id = pair_id_from_name(person_name)
        paths = {
            "image": source_test / "image" / person_name,
            "cloth": source_test / "cloth" / cloth_name,
            "target": source_test / "worn" / person_name,
            "agnostic-v2": source_test / "agnostic-v3.2" / person_name,
            "mask-v2": mask_source_path(source_test, pair_id),
            "mask-inverted": output_test / "agnostic-mask" / f"{pair_id}_mask.png",
        }
        for col_idx, label in enumerate(columns):
            x = col_idx * tile_width
            y = row_idx * (tile_height + label_height)
            img = load_rgb(paths[label], (tile_width, tile_height))
            sheet.paste(img, (x, y + label_height))
            draw.text((x + 4, y + 2), pair_id if col_idx == 0 else label, fill=(0, 0, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=95)


def write_stats_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "pair_id",
        "source",
        "output",
        "nonzero_ratio_before",
        "nonzero_ratio_after",
        "mean_before",
        "mean_after",
        "min_before",
        "max_before",
        "min_after",
        "max_after",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def summarize_stats(rows: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "mean_nonzero_ratio_before": round(mean(float(row["nonzero_ratio_before"]) for row in rows), 6),
        "mean_nonzero_ratio_after": round(mean(float(row["nonzero_ratio_after"]) for row in rows), 6),
        "mean_pixel_before": round(mean(float(row["mean_before"]) for row in rows), 6),
        "mean_pixel_after": round(mean(float(row["mean_after"]) for row in rows), 6),
    }


def main() -> None:
    args = parse_args()
    source_root = Path(args.source_root)
    output_root = Path(args.output_root)
    source_test = source_root / "test"
    output_test = output_root / "test"
    pairs = read_pairs(source_root / "test_pairs.txt")
    if not pairs:
        raise ValueError(f"empty pair file: {source_root / 'test_pairs.txt'}")

    output_root.mkdir(parents=True, exist_ok=True)
    copy_file(source_root / "test_pairs.txt", output_root / "test_pairs.txt")
    if (source_root / "train_pairs.txt").exists():
        copy_file(source_root / "train_pairs.txt", output_root / "train_pairs.txt")
    else:
        (output_root / "train_pairs.txt").write_text("", encoding="utf-8")

    stats_rows: list[dict[str, Any]] = []
    for person_name, cloth_name in pairs:
        pair_id = pair_id_from_name(person_name)
        for dirname in COPY_DIRS:
            source_dir = source_test / dirname
            if not source_dir.exists():
                continue
            if dirname == "cloth":
                filename = cloth_name
            elif dirname == "cloth-mask":
                filename = cloth_name
            elif dirname == "openpose-json":
                filename = person_name.replace(".jpg", "_keypoints.json")
            elif dirname in {"image-parse", "agnostic-mask"}:
                filename = person_name.replace(".jpg", ".png")
            else:
                filename = person_name
            copy_file(source_dir / filename, output_test / dirname / filename)

        mask_stats = invert_mask(
            mask_source_path(source_test, pair_id),
            output_test / "agnostic-mask" / f"{pair_id}_mask.png",
        )
        stats_rows.append({"pair_id": pair_id, **mask_stats})

    write_stats_csv(Path(args.stats_csv), stats_rows)
    make_input_diagnostic_sheet(
        source_test=source_test,
        output_test=output_test,
        pairs=pairs,
        path=Path(args.diagnostic_sheet),
        sample_count=args.sample_count,
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        label_height=args.label_height,
    )

    summary = {
        "source_root": str(source_root),
        "output_root": str(output_root),
        "pair_count": len(pairs),
        "copied_dirs": list(COPY_DIRS),
        "mask_rule": "inverted = 255 - original",
        "stats": summarize_stats(stats_rows),
        "stats_csv": str(Path(args.stats_csv)),
        "diagnostic_sheet": str(Path(args.diagnostic_sheet)),
    }
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
