"""Compare fixed_eval_100 agnostic/mask ablation inference outputs."""

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
        "--backup-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\datasets"
            r"\fixed_eval_100_backup_agnostic_before_v2_20260618_190027"
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
        "--v2-output-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2\rank8_module8"
        ),
    )
    parser.add_argument(
        "--ablation-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_mask_ablation"
        ),
    )
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--raw-csv", default=None)
    parser.add_argument("--sample-sheet", default=None)
    parser.add_argument("--top-delta-sheet", default=None)
    parser.add_argument("--worst-delta-sheet", default=None)
    parser.add_argument("--sample-count", type=int, default=20)
    parser.add_argument("--tile-width", type=int, default=160)
    parser.add_argument("--tile-height", type=int, default=213)
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


def output_name(pair_id: str) -> str:
    return f"{pair_id}_{pair_id}.jpg"


def load_rgb(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
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


def method_specs(before_root: Path, v2_root: Path, ablation_root: Path) -> list[MethodSpec]:
    return [
        MethodSpec("baseline_original", "baseline original", before_root / "rank4_module8" / "baseline" / "pair"),
        MethodSpec("baseline_v2_full", "baseline v2 full", v2_root / "baseline" / "pair"),
        MethodSpec(
            "baseline_agnostic_v1_mask_v2",
            "baseline agn-v1 mask-v2",
            ablation_root / "inference" / "agnostic_v1_mask_v2" / "rank8_module8" / "baseline" / "pair",
        ),
        MethodSpec(
            "baseline_agnostic_v2_mask_v1",
            "baseline agn-v2 mask-v1",
            ablation_root / "inference" / "agnostic_v2_mask_v1" / "rank8_module8" / "baseline" / "pair",
        ),
        MethodSpec("rank8_module8_original", "rank8-module8 original", before_root / "rank8_module8" / "lora" / "pair"),
        MethodSpec("rank8_module8_v2_full", "rank8-module8 v2 full", v2_root / "lora" / "pair"),
        MethodSpec(
            "rank8_module8_agnostic_v1_mask_v2",
            "rank8-module8 agn-v1 mask-v2",
            ablation_root / "inference" / "agnostic_v1_mask_v2" / "rank8_module8" / "lora" / "pair",
        ),
        MethodSpec(
            "rank8_module8_agnostic_v2_mask_v1",
            "rank8-module8 agn-v2 mask-v1",
            ablation_root / "inference" / "agnostic_v2_mask_v1" / "rank8_module8" / "lora" / "pair",
        ),
    ]


def evaluate(eval_root: Path, pairs: list[tuple[str, str]], specs: list[MethodSpec]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    methods: dict[str, Any] = {}
    raw_rows: list[dict[str, Any]] = []
    for method in specs:
        psnr_values: list[float] = []
        ssim_values: list[float] = []
        missing_outputs: list[str] = []
        load_errors: list[dict[str, str]] = []
        output_count = 0
        for person_name, _ in pairs:
            pair_id = pair_id_from_name(person_name)
            target_path = eval_root / "test" / "worn" / person_name
            output_path = method.output_dir / output_name(pair_id)
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


def raw_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, float]]]:
    mapped: dict[str, dict[str, dict[str, float]]] = {}
    for row in rows:
        mapped.setdefault(row["pair_id"], {})[row["method"]] = {
            "psnr": float(row["psnr"]),
            "ssim": float(row["ssim"]),
        }
    return mapped


def sorted_pair_ids_by_delta(rows: list[dict[str, Any]], after_key: str, before_key: str, reverse: bool) -> list[str]:
    mapped = raw_map(rows)
    scored: list[tuple[float, str]] = []
    for pair_id, methods in mapped.items():
        if after_key not in methods or before_key not in methods:
            continue
        scored.append((methods[after_key]["ssim"] - methods[before_key]["ssim"], pair_id))
    scored.sort(reverse=reverse)
    return [pair_id for _, pair_id in scored]


def find_mask_path(base_dir: Path, pair_id: str) -> Path:
    preferred = base_dir / f"{pair_id}_mask.png"
    if preferred.exists():
        return preferred
    return base_dir / f"{pair_id}.png"


def image_path_for(
    *,
    label: str,
    pair_id: str,
    eval_root: Path,
    backup_root: Path,
    v2_root: Path,
    ablation_root: Path,
    before_root: Path,
) -> Path:
    if label == "image":
        return eval_root / "test" / "image" / f"{pair_id}.jpg"
    if label == "cloth":
        return eval_root / "test" / "cloth" / f"{pair_id}.jpg"
    if label == "target":
        return eval_root / "test" / "worn" / f"{pair_id}.jpg"
    if label == "agn-v1":
        return backup_root / "agnostic-v3.2" / f"{pair_id}.jpg"
    if label == "mask-v1":
        return find_mask_path(backup_root / "agnostic-mask", pair_id)
    if label == "agn-v2":
        return eval_root / "test" / "agnostic-v3.2" / f"{pair_id}.jpg"
    if label == "mask-v2":
        return find_mask_path(eval_root / "test" / "agnostic-mask", pair_id)
    if label == "base-orig":
        return before_root / "rank4_module8" / "baseline" / "pair" / output_name(pair_id)
    if label == "base-v2":
        return v2_root / "baseline" / "pair" / output_name(pair_id)
    if label == "base-v1m2":
        return ablation_root / "inference" / "agnostic_v1_mask_v2" / "rank8_module8" / "baseline" / "pair" / output_name(pair_id)
    if label == "base-v2m1":
        return ablation_root / "inference" / "agnostic_v2_mask_v1" / "rank8_module8" / "baseline" / "pair" / output_name(pair_id)
    if label == "r8-orig":
        return before_root / "rank8_module8" / "lora" / "pair" / output_name(pair_id)
    if label == "r8-v2":
        return v2_root / "lora" / "pair" / output_name(pair_id)
    if label == "r8-v1m2":
        return ablation_root / "inference" / "agnostic_v1_mask_v2" / "rank8_module8" / "lora" / "pair" / output_name(pair_id)
    if label == "r8-v2m1":
        return ablation_root / "inference" / "agnostic_v2_mask_v1" / "rank8_module8" / "lora" / "pair" / output_name(pair_id)
    raise ValueError(f"unknown label: {label}")


def make_contact_sheet(
    *,
    eval_root: Path,
    backup_root: Path,
    v2_root: Path,
    ablation_root: Path,
    before_root: Path,
    pair_ids: list[str],
    path: Path,
    tile_width: int,
    tile_height: int,
    label_height: int,
) -> None:
    columns = [
        "image",
        "cloth",
        "target",
        "agn-v1",
        "mask-v1",
        "agn-v2",
        "mask-v2",
        "base-orig",
        "base-v2",
        "base-v1m2",
        "base-v2m1",
        "r8-orig",
        "r8-v2",
        "r8-v1m2",
        "r8-v2m1",
    ]
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
            image_path = image_path_for(
                label=label,
                pair_id=pair_id,
                eval_root=eval_root,
                backup_root=backup_root,
                v2_root=v2_root,
                ablation_root=ablation_root,
                before_root=before_root,
            )
            x = col_idx * tile_width
            y = row_idx * (tile_height + label_height)
            if image_path.exists():
                image = load_rgb(image_path, size=(tile_width, tile_height))
                sheet.paste(image, (x, y + label_height))
            else:
                draw.rectangle((x, y + label_height, x + tile_width - 1, y + label_height + tile_height - 1), outline=(180, 0, 0))
                draw.text((x + 4, y + label_height + 4), "missing", fill=(180, 0, 0))
            draw.text((x + 4, y + 2), pair_id if col_idx == 0 else label, fill=(0, 0, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=95)


def deltas(methods: dict[str, Any]) -> dict[str, Any]:
    def delta(after_key: str, before_key: str, metric: str) -> float | None:
        after = methods[after_key][metric]["mean"]
        before = methods[before_key][metric]["mean"]
        if after is None or before is None:
            return None
        return round(float(after) - float(before), 6)

    return {
        "baseline_v2_full_minus_original": {
            "psnr": delta("baseline_v2_full", "baseline_original", "psnr"),
            "ssim": delta("baseline_v2_full", "baseline_original", "ssim"),
        },
        "baseline_agnostic_v1_mask_v2_minus_original": {
            "psnr": delta("baseline_agnostic_v1_mask_v2", "baseline_original", "psnr"),
            "ssim": delta("baseline_agnostic_v1_mask_v2", "baseline_original", "ssim"),
        },
        "baseline_agnostic_v2_mask_v1_minus_original": {
            "psnr": delta("baseline_agnostic_v2_mask_v1", "baseline_original", "psnr"),
            "ssim": delta("baseline_agnostic_v2_mask_v1", "baseline_original", "ssim"),
        },
        "rank8_module8_v2_full_minus_original": {
            "psnr": delta("rank8_module8_v2_full", "rank8_module8_original", "psnr"),
            "ssim": delta("rank8_module8_v2_full", "rank8_module8_original", "ssim"),
        },
        "rank8_module8_agnostic_v1_mask_v2_minus_original": {
            "psnr": delta("rank8_module8_agnostic_v1_mask_v2", "rank8_module8_original", "psnr"),
            "ssim": delta("rank8_module8_agnostic_v1_mask_v2", "rank8_module8_original", "ssim"),
        },
        "rank8_module8_agnostic_v2_mask_v1_minus_original": {
            "psnr": delta("rank8_module8_agnostic_v2_mask_v1", "rank8_module8_original", "psnr"),
            "ssim": delta("rank8_module8_agnostic_v2_mask_v1", "rank8_module8_original", "ssim"),
        },
    }


def main() -> None:
    args = parse_args()
    eval_root = Path(args.eval_root)
    backup_root = Path(args.backup_root)
    before_root = Path(args.before_output_root)
    v2_root = Path(args.v2_output_root)
    ablation_root = Path(args.ablation_root)
    pairs = read_pairs(eval_root / "test_pairs.txt")
    methods, raw_rows = evaluate(eval_root, pairs, method_specs(before_root, v2_root, ablation_root))

    raw_csv = Path(args.raw_csv) if args.raw_csv else ablation_root / "metrics" / "agnostic_mask_ablation_raw.csv"
    summary_json = Path(args.summary_json) if args.summary_json else ablation_root / "metrics" / "agnostic_mask_ablation_summary.json"
    sample_sheet = Path(args.sample_sheet) if args.sample_sheet else ablation_root / "contact_sheet" / "agnostic_mask_ablation_sample20.jpg"
    top_sheet = Path(args.top_delta_sheet) if args.top_delta_sheet else ablation_root / "contact_sheet" / "agnostic_mask_ablation_top_delta20.jpg"
    worst_sheet = Path(args.worst_delta_sheet) if args.worst_delta_sheet else ablation_root / "contact_sheet" / "agnostic_mask_ablation_worst_delta20.jpg"
    write_raw_csv(raw_csv, raw_rows)

    pair_ids = [pair_id_from_name(person_name) for person_name, _ in pairs]
    top_ids = sorted_pair_ids_by_delta(
        raw_rows,
        "baseline_agnostic_v1_mask_v2",
        "baseline_v2_full",
        reverse=True,
    )[: args.sample_count]
    worst_ids = sorted_pair_ids_by_delta(
        raw_rows,
        "baseline_agnostic_v1_mask_v2",
        "baseline_v2_full",
        reverse=False,
    )[: args.sample_count]
    for ids, path in ((pair_ids[: args.sample_count], sample_sheet), (top_ids, top_sheet), (worst_ids, worst_sheet)):
        make_contact_sheet(
            eval_root=eval_root,
            backup_root=backup_root,
            v2_root=v2_root,
            ablation_root=ablation_root,
            before_root=before_root,
            pair_ids=ids,
            path=path,
            tile_width=args.tile_width,
            tile_height=args.tile_height,
            label_height=args.label_height,
        )

    summary = {
        "eval_root": str(eval_root),
        "backup_root": str(backup_root),
        "before_output_root": str(before_root),
        "v2_output_root": str(v2_root),
        "ablation_root": str(ablation_root),
        "pair_count": len(pairs),
        "methods": methods,
        "deltas": deltas(methods),
        "raw_csv": str(raw_csv),
        "sample_sheet": str(sample_sheet),
        "top_delta_sheet": str(top_sheet),
        "worst_delta_sheet": str(worst_sheet),
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
