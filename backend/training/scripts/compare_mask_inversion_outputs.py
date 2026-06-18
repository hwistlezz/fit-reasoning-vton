"""Compare fixed_eval_100 outputs for agnostic-v2 mask inversion test."""

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
        "--inverted-eval-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2_mask_inverted"
            r"\fixed_eval_100_data"
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
        "--inverted-output-root",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2_mask_inverted\rank8_module8"
        ),
    )
    parser.add_argument(
        "--summary-json",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2_mask_inverted"
            r"\metrics\mask_inversion_comparison_summary.json"
        ),
    )
    parser.add_argument(
        "--raw-csv",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2_mask_inverted"
            r"\metrics\mask_inversion_comparison_raw.csv"
        ),
    )
    parser.add_argument(
        "--contact-sheet",
        default=(
            r"D:\GitHub\fit-reasoning-vton\backend\training\outputs"
            r"\fixed_eval_100_lora_comparison_agnostic_v2_mask_inverted"
            r"\contact_sheet\mask_inversion_before_v2_inverted_sample20.jpg"
        ),
    )
    parser.add_argument("--sample-count", type=int, default=20)
    parser.add_argument("--tile-width", type=int, default=176)
    parser.add_argument("--tile-height", type=int, default=235)
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


def output_name(person_name: str, cloth_name: str) -> str:
    return f"{pair_id_from_name(person_name)}_{pair_id_from_name(cloth_name)}.jpg"


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


def method_specs(before_output_root: Path, v2_output_root: Path, inverted_output_root: Path) -> list[MethodSpec]:
    return [
        MethodSpec("baseline_before", "baseline before", before_output_root / "rank4_module8" / "baseline" / "pair"),
        MethodSpec("baseline_v2", "baseline agnostic-v2", v2_output_root / "baseline" / "pair"),
        MethodSpec("baseline_inverted", "baseline mask-inverted", inverted_output_root / "baseline" / "pair"),
        MethodSpec("rank8_module8_before", "rank8-module8 before", before_output_root / "rank8_module8" / "lora" / "pair"),
        MethodSpec("rank8_module8_v2", "rank8-module8 agnostic-v2", v2_output_root / "lora" / "pair"),
        MethodSpec("rank8_module8_inverted", "rank8-module8 mask-inverted", inverted_output_root / "lora" / "pair"),
    ]


def evaluate(eval_root: Path, pairs: list[tuple[str, str]], specs: list[MethodSpec]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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
                psnr_value = psnr(image_to_float_array(pred_img), image_to_float_array(target_img))
                ssim_value = ssim_global(image_to_float_array(pred_img), image_to_float_array(target_img))
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


def find_mask_path(root: Path, pair_id: str) -> Path:
    preferred = root / "test" / "agnostic-mask" / f"{pair_id}_mask.png"
    if preferred.exists():
        return preferred
    return root / "test" / "agnostic-mask" / f"{pair_id}.png"


def path_for_column(
    *,
    label: str,
    pair_id: str,
    eval_root: Path,
    inverted_eval_root: Path,
    before_output_root: Path,
    v2_output_root: Path,
    inverted_output_root: Path,
) -> Path:
    if label == "image":
        return eval_root / "test" / "image" / f"{pair_id}.jpg"
    if label == "cloth":
        return eval_root / "test" / "cloth" / f"{pair_id}.jpg"
    if label == "target":
        return eval_root / "test" / "worn" / f"{pair_id}.jpg"
    if label == "agnostic-v2":
        return eval_root / "test" / "agnostic-v3.2" / f"{pair_id}.jpg"
    if label == "mask-v2":
        return find_mask_path(eval_root, pair_id)
    if label == "mask-inv":
        return find_mask_path(inverted_eval_root, pair_id)
    if label == "base-before":
        return before_output_root / "rank4_module8" / "baseline" / "pair" / f"{pair_id}_{pair_id}.jpg"
    if label == "base-v2":
        return v2_output_root / "baseline" / "pair" / f"{pair_id}_{pair_id}.jpg"
    if label == "base-inv":
        return inverted_output_root / "baseline" / "pair" / f"{pair_id}_{pair_id}.jpg"
    if label == "r8-before":
        return before_output_root / "rank8_module8" / "lora" / "pair" / f"{pair_id}_{pair_id}.jpg"
    if label == "r8-v2":
        return v2_output_root / "lora" / "pair" / f"{pair_id}_{pair_id}.jpg"
    if label == "r8-inv":
        return inverted_output_root / "lora" / "pair" / f"{pair_id}_{pair_id}.jpg"
    raise ValueError(f"unknown column label: {label}")


def make_contact_sheet(
    *,
    eval_root: Path,
    inverted_eval_root: Path,
    before_output_root: Path,
    v2_output_root: Path,
    inverted_output_root: Path,
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
        "mask-inv",
        "base-before",
        "base-v2",
        "base-inv",
        "r8-before",
        "r8-v2",
        "r8-inv",
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

    for row_idx, (person_name, _) in enumerate(selected, start=1):
        pair_id = pair_id_from_name(person_name)
        for col_idx, label in enumerate(columns):
            image_path = path_for_column(
                label=label,
                pair_id=pair_id,
                eval_root=eval_root,
                inverted_eval_root=inverted_eval_root,
                before_output_root=before_output_root,
                v2_output_root=v2_output_root,
                inverted_output_root=inverted_output_root,
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


def build_deltas(methods: dict[str, Any]) -> dict[str, Any]:
    def delta(after_key: str, before_key: str, metric: str) -> float | None:
        after = methods[after_key][metric]["mean"]
        before = methods[before_key][metric]["mean"]
        if after is None or before is None:
            return None
        return round(float(after) - float(before), 6)

    return {
        "baseline_v2_minus_before": {
            "psnr_mean": delta("baseline_v2", "baseline_before", "psnr"),
            "ssim_mean": delta("baseline_v2", "baseline_before", "ssim"),
        },
        "baseline_inverted_minus_before": {
            "psnr_mean": delta("baseline_inverted", "baseline_before", "psnr"),
            "ssim_mean": delta("baseline_inverted", "baseline_before", "ssim"),
        },
        "baseline_inverted_minus_v2": {
            "psnr_mean": delta("baseline_inverted", "baseline_v2", "psnr"),
            "ssim_mean": delta("baseline_inverted", "baseline_v2", "ssim"),
        },
        "rank8_module8_v2_minus_before": {
            "psnr_mean": delta("rank8_module8_v2", "rank8_module8_before", "psnr"),
            "ssim_mean": delta("rank8_module8_v2", "rank8_module8_before", "ssim"),
        },
        "rank8_module8_inverted_minus_before": {
            "psnr_mean": delta("rank8_module8_inverted", "rank8_module8_before", "psnr"),
            "ssim_mean": delta("rank8_module8_inverted", "rank8_module8_before", "ssim"),
        },
        "rank8_module8_inverted_minus_v2": {
            "psnr_mean": delta("rank8_module8_inverted", "rank8_module8_v2", "psnr"),
            "ssim_mean": delta("rank8_module8_inverted", "rank8_module8_v2", "ssim"),
        },
    }


def main() -> None:
    args = parse_args()
    eval_root = Path(args.eval_root)
    inverted_eval_root = Path(args.inverted_eval_root)
    before_output_root = Path(args.before_output_root)
    v2_output_root = Path(args.v2_output_root)
    inverted_output_root = Path(args.inverted_output_root)
    pairs = read_pairs(eval_root / "test_pairs.txt")
    methods, raw_rows = evaluate(
        eval_root,
        pairs,
        method_specs(before_output_root, v2_output_root, inverted_output_root),
    )
    write_raw_csv(Path(args.raw_csv), raw_rows)
    make_contact_sheet(
        eval_root=eval_root,
        inverted_eval_root=inverted_eval_root,
        before_output_root=before_output_root,
        v2_output_root=v2_output_root,
        inverted_output_root=inverted_output_root,
        pairs=pairs,
        path=Path(args.contact_sheet),
        sample_count=args.sample_count,
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        label_height=args.label_height,
    )
    summary = {
        "eval_root": str(eval_root),
        "inverted_eval_root": str(inverted_eval_root),
        "before_output_root": str(before_output_root),
        "v2_output_root": str(v2_output_root),
        "inverted_output_root": str(inverted_output_root),
        "pair_count": len(pairs),
        "methods": methods,
        "deltas": build_deltas(methods),
        "raw_csv": str(Path(args.raw_csv)),
        "contact_sheet": str(Path(args.contact_sheet)),
    }
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
