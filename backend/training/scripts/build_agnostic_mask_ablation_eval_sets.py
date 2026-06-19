"""Build fixed_eval_100 agnostic/mask cross-combination eval sets.

This helper keeps the source fixed_eval_100 dataset read-only and writes
combination-specific datasets under ignored output paths.
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
from PIL import Image, ImageOps


SHARED_DIRS = (
    "image",
    "cloth",
    "worn",
    "cloth-mask",
    "image-densepose",
    "image-parse",
    "openpose-json",
)

COMBOS = {
    "agnostic_v1_mask_v2": {
        "agnostic": "v1",
        "mask": "v2",
    },
    "agnostic_v2_mask_v1": {
        "agnostic": "v2",
        "mask": "v1",
    },
}


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
        "--backup-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\datasets"
            r"\fixed_eval_100_backup_agnostic_before_v2_20260618_190027"
        ),
    )
    parser.add_argument(
        "--output-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_mask_ablation"
        ),
    )
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--stats-csv", default=None)
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


def mask_path(mask_dir: Path, pair_id: str) -> Path:
    preferred = mask_dir / f"{pair_id}_mask.png"
    if preferred.exists():
        return preferred
    fallback = mask_dir / f"{pair_id}.png"
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"missing mask for {pair_id}: {preferred} or {fallback}")


def mask_stats(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        arr = np.asarray(ImageOps.exif_transpose(image).convert("L"), dtype=np.uint8)
    total = int(arr.size)
    return {
        "nonzero_ratio": round(float(np.count_nonzero(arr)) / total, 6),
        "mean_pixel": round(float(arr.mean()), 6),
        "min_pixel": int(arr.min()),
        "max_pixel": int(arr.max()),
    }


def source_for_shared_dir(source_test: Path, dirname: str, person_name: str, cloth_name: str) -> Path:
    if dirname == "cloth":
        filename = cloth_name
    elif dirname == "cloth-mask":
        filename = cloth_name
    elif dirname == "openpose-json":
        filename = person_name.replace(".jpg", "_keypoints.json")
    elif dirname == "image-parse":
        filename = person_name.replace(".jpg", ".png")
    else:
        filename = person_name
    return source_test / dirname / filename


def agnostic_source(combo: dict[str, str], source_test: Path, backup_root: Path, pair_id: str) -> Path:
    if combo["agnostic"] == "v1":
        return backup_root / "agnostic-v3.2" / f"{pair_id}.jpg"
    return source_test / "agnostic-v3.2" / f"{pair_id}.jpg"


def mask_source(combo: dict[str, str], source_test: Path, backup_root: Path, pair_id: str) -> Path:
    if combo["mask"] == "v1":
        return mask_path(backup_root / "agnostic-mask", pair_id)
    return mask_path(source_test / "agnostic-mask", pair_id)


def build_combo(
    *,
    combo_name: str,
    combo: dict[str, str],
    source_root: Path,
    backup_root: Path,
    output_root: Path,
    pairs: list[tuple[str, str]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    combo_root = output_root / "datasets" / combo_name
    source_test = source_root / "test"
    output_test = combo_root / "test"
    combo_root.mkdir(parents=True, exist_ok=True)
    copy_file(source_root / "test_pairs.txt", combo_root / "test_pairs.txt")
    if (source_root / "train_pairs.txt").exists():
        copy_file(source_root / "train_pairs.txt", combo_root / "train_pairs.txt")
    else:
        (combo_root / "train_pairs.txt").write_text("", encoding="utf-8")

    rows: list[dict[str, Any]] = []
    for person_name, cloth_name in pairs:
        pair_id = pair_id_from_name(person_name)
        for dirname in SHARED_DIRS:
            src = source_for_shared_dir(source_test, dirname, person_name, cloth_name)
            copy_file(src, output_test / dirname / src.name)

        agn_src = agnostic_source(combo, source_test, backup_root, pair_id)
        mask_src = mask_source(combo, source_test, backup_root, pair_id)
        copy_file(agn_src, output_test / "agnostic-v3.2" / f"{pair_id}.jpg")
        copy_file(mask_src, output_test / "agnostic-mask" / f"{pair_id}_mask.png")
        rows.append(
            {
                "combo": combo_name,
                "pair_id": pair_id,
                "agnostic_source": combo["agnostic"],
                "mask_source": combo["mask"],
                "agnostic_path": str(agn_src),
                "mask_path": str(mask_src),
                **{f"mask_{key}": value for key, value in mask_stats(mask_src).items()},
            }
        )

    summary = {
        "combo": combo_name,
        "dataset_root": str(combo_root),
        "pair_count": len(pairs),
        "agnostic_source": combo["agnostic"],
        "mask_source": combo["mask"],
        "mean_mask_nonzero_ratio": round(mean(row["mask_nonzero_ratio"] for row in rows), 6),
        "mean_mask_pixel": round(mean(row["mask_mean_pixel"] for row in rows), 6),
    }
    return summary, rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "combo",
        "pair_id",
        "agnostic_source",
        "mask_source",
        "agnostic_path",
        "mask_path",
        "mask_nonzero_ratio",
        "mask_mean_pixel",
        "mask_min_pixel",
        "mask_max_pixel",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    source_root = Path(args.source_root)
    backup_root = Path(args.backup_root)
    output_root = Path(args.output_root)
    pairs = read_pairs(source_root / "test_pairs.txt")
    summaries: dict[str, Any] = {}
    all_rows: list[dict[str, Any]] = []
    for combo_name, combo in COMBOS.items():
        combo_summary, rows = build_combo(
            combo_name=combo_name,
            combo=combo,
            source_root=source_root,
            backup_root=backup_root,
            output_root=output_root,
            pairs=pairs,
        )
        summaries[combo_name] = combo_summary
        all_rows.extend(rows)

    summary_path = Path(args.summary_json) if args.summary_json else output_root / "metrics" / "ablation_dataset_summary.json"
    stats_path = Path(args.stats_csv) if args.stats_csv else output_root / "metrics" / "ablation_dataset_mask_stats.csv"
    write_csv(stats_path, all_rows)
    summary = {
        "source_root": str(source_root),
        "backup_root": str(backup_root),
        "output_root": str(output_root),
        "pair_count": len(pairs),
        "combos": summaries,
        "stats_csv": str(stats_path),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
