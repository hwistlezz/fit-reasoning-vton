"""Compare fixed_eval_100 outputs before and after agnostic-v2 replacement.

This script is an evaluation/report helper. It reads generated inference
outputs and writes raw summaries/contact sheets under ignored output
directories. It does not modify datasets, adapters, or model checkpoints.
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


@dataclass(frozen=True)
class MethodSpec:
    key: str
    label: str
    output_dir: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--eval-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_exif_fixed\fixed_eval_100_data"
        ),
    )
    parser.add_argument(
        "--before-output-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_exif_fixed"
        ),
    )
    parser.add_argument(
        "--after-output-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2\rank8_module8"
        ),
    )
    parser.add_argument(
        "--before-agnostic-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\datasets"
            r"\fixed_eval_100_backup_agnostic_before_v2_20260618_190027"
        ),
    )
    parser.add_argument(
        "--summary-json",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2\metrics"
            r"\agnostic_v2_before_after_summary.json"
        ),
    )
    parser.add_argument(
        "--raw-csv",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2\metrics"
            r"\agnostic_v2_before_after_raw.csv"
        ),
    )
    parser.add_argument(
        "--sample-sheet",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2\contact_sheet"
            r"\agnostic_v2_before_after_sample20.jpg"
        ),
    )
    parser.add_argument(
        "--top-delta-sheet",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2\contact_sheet"
            r"\agnostic_v2_top_delta20.jpg"
        ),
    )
    parser.add_argument(
        "--diagnostic-sheet",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2\contact_sheet"
            r"\agnostic_v2_diagnostic_sample5.jpg"
        ),
    )
    parser.add_argument("--sample-count", type=int, default=20)
    parser.add_argument("--diagnostic-count", type=int, default=5)
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


def pair_jpg(pair_id: str) -> str:
    return f"{pair_id}.jpg"


def pair_png(pair_id: str) -> str:
    return f"{pair_id}.png"


def pair_mask_png(pair_id: str) -> str:
    return f"{pair_id}_mask.png"


def output_name(person_name: str, cloth_name: str) -> str:
    return f"{pair_id_from_name(person_name)}_{pair_id_from_name(cloth_name)}.jpg"


def load_rgb(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        if size is not None and image.size != size:
            image = image.resize(size, Image.Resampling.BILINEAR)
        return image.copy()


def image_to_float_array(image: Image.Image) -> np.ndarray:
    return np.asarray(image, dtype=np.float32) / 255.0


def psnr(pred: np.ndarray, target: np.ndarray) -> float:
    mse = float(np.mean((pred - target) ** 2))
    if mse == 0:
        return float("inf")
    return 20.0 * math.log10(1.0 / math.sqrt(mse))


def ssim_global(pred: np.ndarray, target: np.ndarray) -> float:
    c1 = 0.01**2
    c2 = 0.03**2
    values: list[float] = []
    for channel in range(pred.shape[2]):
        x = pred[:, :, channel]
        y = target[:, :, channel]
        mu_x = float(x.mean())
        mu_y = float(y.mean())
        sigma_x = float(((x - mu_x) ** 2).mean())
        sigma_y = float(((y - mu_y) ** 2).mean())
        sigma_xy = float(((x - mu_x) * (y - mu_y)).mean())
        numerator = (2 * mu_x * mu_y + c1) * (2 * sigma_xy + c2)
        denominator = (mu_x**2 + mu_y**2 + c1) * (sigma_x + sigma_y + c2)
        values.append(numerator / denominator if denominator else 0.0)
    return float(mean(values))


def summarize(values: list[float]) -> dict[str, float | None]:
    finite_values = [value for value in values if math.isfinite(value)]
    if not finite_values:
        return {"mean": None, "min": None, "max": None}
    return {
        "mean": round(float(mean(finite_values)), 6),
        "min": round(float(min(finite_values)), 6),
        "max": round(float(max(finite_values)), 6),
    }


def method_specs(before_output_root: Path, after_output_root: Path) -> list[MethodSpec]:
    return [
        MethodSpec(
            "baseline_before",
            "baseline before",
            before_output_root / "rank4_module8" / "baseline" / "pair",
        ),
        MethodSpec(
            "baseline_after",
            "baseline after",
            after_output_root / "baseline" / "pair",
        ),
        MethodSpec(
            "rank8_module8_before",
            "rank8-module8 before",
            before_output_root / "rank8_module8" / "lora" / "pair",
        ),
        MethodSpec(
            "rank8_module8_after",
            "rank8-module8 after",
            after_output_root / "lora" / "pair",
        ),
    ]


def evaluate(
    eval_root: Path,
    pairs: list[tuple[str, str]],
    specs: list[MethodSpec],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_rows: list[dict[str, Any]] = []
    methods: dict[str, Any] = {}
    for method in specs:
        psnr_values: list[float] = []
        ssim_values: list[float] = []
        missing_outputs: list[str] = []
        load_errors: list[dict[str, str]] = []
        output_count = 0
        for person_name, cloth_name in pairs:
            pair_id = pair_id_from_name(person_name)
            target_path = eval_root / "test" / "worn" / person_name
            output_path = method.output_dir / output_name(person_name, cloth_name)
            if not output_path.exists():
                missing_outputs.append(pair_id)
                continue
            try:
                target_img = load_rgb(target_path)
                pred_img = load_rgb(output_path, size=target_img.size)
                target_arr = image_to_float_array(target_img)
                pred_arr = image_to_float_array(pred_img)
                psnr_value = psnr(pred_arr, target_arr)
                ssim_value = ssim_global(pred_arr, target_arr)
            except Exception as exc:  # noqa: BLE001
                load_errors.append({"pair_id": pair_id, "error": f"{type(exc).__name__}: {exc}"})
                continue
            output_count += 1
            psnr_values.append(psnr_value)
            ssim_values.append(ssim_value)
            raw_rows.append(
                {
                    "pair_id": pair_id,
                    "method": method.key,
                    "output_path": str(output_path),
                    "psnr": psnr_value,
                    "ssim": ssim_value,
                }
            )
        methods[method.key] = {
            "label": method.label,
            "output_dir": str(method.output_dir),
            "output_count": output_count,
            "failure_count": len(pairs) - output_count,
            "success_rate": round(output_count / len(pairs), 6) if pairs else 0.0,
            "missing_outputs_sample": missing_outputs[:20],
            "load_errors_sample": load_errors[:20],
            "psnr": summarize(psnr_values),
            "ssim": summarize(ssim_values),
        }
    return methods, raw_rows


def write_raw_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["pair_id", "method", "output_path", "psnr", "ssim"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def per_pair_metric_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, float]]]:
    mapped: dict[str, dict[str, dict[str, float]]] = {}
    for row in rows:
        mapped.setdefault(row["pair_id"], {})[row["method"]] = {
            "psnr": float(row["psnr"]),
            "ssim": float(row["ssim"]),
        }
    return mapped


def sorted_by_after_delta(rows: list[dict[str, Any]]) -> list[str]:
    mapped = per_pair_metric_map(rows)
    scored: list[tuple[float, str]] = []
    for pair_id, methods in mapped.items():
        before = methods.get("baseline_before")
        after = methods.get("baseline_after")
        if before is None or after is None:
            continue
        scored.append((after["ssim"] - before["ssim"], pair_id))
    scored.sort(reverse=True)
    return [pair_id for _, pair_id in scored]


def find_mask_path(base_dir: Path, pair_id: str) -> Path:
    mask_path = base_dir / pair_mask_png(pair_id)
    if mask_path.exists():
        return mask_path
    return base_dir / pair_png(pair_id)


def path_for_column(
    *,
    label: str,
    pair_id: str,
    eval_root: Path,
    before_output_root: Path,
    after_output_root: Path,
    before_agnostic_root: Path,
) -> Path:
    if label == "person":
        return eval_root / "test" / "image" / pair_jpg(pair_id)
    if label == "cloth":
        return eval_root / "test" / "cloth" / pair_jpg(pair_id)
    if label == "target":
        return eval_root / "test" / "worn" / pair_jpg(pair_id)
    if label == "agn-before":
        return before_agnostic_root / "agnostic-v3.2" / pair_jpg(pair_id)
    if label == "agn-after":
        return eval_root / "test" / "agnostic-v3.2" / pair_jpg(pair_id)
    if label == "mask-before":
        return find_mask_path(before_agnostic_root / "agnostic-mask", pair_id)
    if label == "mask-after":
        return find_mask_path(eval_root / "test" / "agnostic-mask", pair_id)
    if label == "baseline-before":
        return before_output_root / "rank4_module8" / "baseline" / "pair" / f"{pair_id}_{pair_id}.jpg"
    if label == "baseline-after":
        return after_output_root / "baseline" / "pair" / f"{pair_id}_{pair_id}.jpg"
    if label == "rank8-before":
        return before_output_root / "rank8_module8" / "lora" / "pair" / f"{pair_id}_{pair_id}.jpg"
    if label == "rank8-after":
        return after_output_root / "lora" / "pair" / f"{pair_id}_{pair_id}.jpg"
    raise ValueError(f"unknown column label: {label}")


def make_sheet(
    *,
    eval_root: Path,
    before_output_root: Path,
    after_output_root: Path,
    before_agnostic_root: Path,
    pair_ids: list[str],
    columns: list[str],
    path: Path,
    tile_width: int,
    tile_height: int,
    label_height: int,
) -> None:
    sheet = Image.new(
        "RGB",
        (tile_width * len(columns), (tile_height + label_height) * (len(pair_ids) + 1)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for col_idx, label in enumerate(columns):
        draw.text((col_idx * tile_width + 4, 4), label, fill=(0, 0, 0))

    for row_idx, pair_id in enumerate(pair_ids, start=1):
        for col_idx, label in enumerate(columns):
            image_path = path_for_column(
                label=label,
                pair_id=pair_id,
                eval_root=eval_root,
                before_output_root=before_output_root,
                after_output_root=after_output_root,
                before_agnostic_root=before_agnostic_root,
            )
            x = col_idx * tile_width
            y = row_idx * (tile_height + label_height)
            if image_path.exists():
                image = load_rgb(image_path).resize((tile_width, tile_height), Image.Resampling.BILINEAR)
                sheet.paste(image, (x, y + label_height))
            else:
                draw.rectangle((x, y + label_height, x + tile_width - 1, y + label_height + tile_height - 1), outline=(180, 0, 0))
                draw.text((x + 4, y + label_height + 4), "missing", fill=(180, 0, 0))
            draw.text((x + 4, y + 2), pair_id if col_idx == 0 else label, fill=(0, 0, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=95)


def build_deltas(methods: dict[str, Any]) -> dict[str, Any]:
    def metric_delta(after_key: str, before_key: str, metric: str) -> float | None:
        after = methods[after_key][metric]["mean"]
        before = methods[before_key][metric]["mean"]
        if after is None or before is None:
            return None
        return round(float(after) - float(before), 6)

    return {
        "baseline_after_minus_before": {
            "psnr_mean": metric_delta("baseline_after", "baseline_before", "psnr"),
            "ssim_mean": metric_delta("baseline_after", "baseline_before", "ssim"),
        },
        "rank8_module8_after_minus_before": {
            "psnr_mean": metric_delta("rank8_module8_after", "rank8_module8_before", "psnr"),
            "ssim_mean": metric_delta("rank8_module8_after", "rank8_module8_before", "ssim"),
        },
    }


def main() -> None:
    args = parse_args()
    eval_root = Path(args.eval_root)
    before_output_root = Path(args.before_output_root)
    after_output_root = Path(args.after_output_root)
    before_agnostic_root = Path(args.before_agnostic_root)
    pairs = read_pairs(eval_root / "test_pairs.txt")
    specs = method_specs(before_output_root, after_output_root)
    methods, raw_rows = evaluate(eval_root, pairs, specs)
    write_raw_csv(Path(args.raw_csv), raw_rows)

    pair_ids = [pair_id_from_name(person_name) for person_name, _ in pairs]
    top_delta_ids = sorted_by_after_delta(raw_rows)
    sample_ids = pair_ids[: args.sample_count]
    top_ids = top_delta_ids[: args.sample_count]
    diagnostic_ids = top_delta_ids[: args.diagnostic_count] or pair_ids[: args.diagnostic_count]

    common_columns = [
        "person",
        "cloth",
        "target",
        "agn-before",
        "agn-after",
        "baseline-before",
        "baseline-after",
        "rank8-before",
        "rank8-after",
    ]
    diagnostic_columns = [
        "person",
        "cloth",
        "target",
        "agn-before",
        "agn-after",
        "mask-before",
        "mask-after",
        "baseline-before",
        "baseline-after",
        "rank8-before",
        "rank8-after",
    ]

    make_sheet(
        eval_root=eval_root,
        before_output_root=before_output_root,
        after_output_root=after_output_root,
        before_agnostic_root=before_agnostic_root,
        pair_ids=sample_ids,
        columns=common_columns,
        path=Path(args.sample_sheet),
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        label_height=args.label_height,
    )
    make_sheet(
        eval_root=eval_root,
        before_output_root=before_output_root,
        after_output_root=after_output_root,
        before_agnostic_root=before_agnostic_root,
        pair_ids=top_ids,
        columns=common_columns,
        path=Path(args.top_delta_sheet),
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        label_height=args.label_height,
    )
    make_sheet(
        eval_root=eval_root,
        before_output_root=before_output_root,
        after_output_root=after_output_root,
        before_agnostic_root=before_agnostic_root,
        pair_ids=diagnostic_ids,
        columns=diagnostic_columns,
        path=Path(args.diagnostic_sheet),
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        label_height=args.label_height,
    )

    summary = {
        "eval_root": str(eval_root),
        "before_output_root": str(before_output_root),
        "after_output_root": str(after_output_root),
        "before_agnostic_root": str(before_agnostic_root),
        "pair_count": len(pairs),
        "methods": methods,
        "deltas": build_deltas(methods),
        "raw_csv": str(Path(args.raw_csv)),
        "sample_sheet": str(Path(args.sample_sheet)),
        "top_delta_sheet": str(Path(args.top_delta_sheet)),
        "diagnostic_sheet": str(Path(args.diagnostic_sheet)),
        "top_delta_pair_ids": top_delta_ids[:20],
    }
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
