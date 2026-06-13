"""Evaluate StableVITON baseline and saved-LoRA outputs for a fixed pair set.

This script reads generated inference outputs and writes metric summaries under
ignored experiment output directories. It does not modify datasets or adapters.
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
        default=r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\fixed_eval_100_lora_comparison\fixed_eval_100_data",
    )
    parser.add_argument(
        "--output-root",
        default=r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\fixed_eval_100_lora_comparison",
    )
    parser.add_argument("--sample-count", type=int, default=20)
    parser.add_argument("--summary-json", default=None)
    parser.add_argument("--raw-csv", default=None)
    parser.add_argument("--contact-sheet", default=None)
    parser.add_argument("--tile-width", type=int, default=128)
    parser.add_argument("--tile-height", type=int, default=171)
    parser.add_argument("--label-height", type=int, default=20)
    parser.add_argument("--skip-lpips", action="store_true")
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


def maybe_lpips_model(skip_lpips: bool) -> tuple[Any | None, str | None]:
    if skip_lpips:
        return None, "disabled by --skip-lpips"
    try:
        import torch  # noqa: WPS433
        import lpips  # type: ignore  # noqa: WPS433
    except Exception as exc:  # pragma: no cover - environment dependent
        return None, f"lpips unavailable: {type(exc).__name__}: {exc}"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = lpips.LPIPS(net="alex").to(device)
    model.eval()
    return (model, device, torch), None


def compute_lpips(lpips_bundle: Any, pred: Image.Image, target: Image.Image) -> float:
    model, device, torch = lpips_bundle
    pred_arr = np.asarray(pred, dtype=np.float32).transpose(2, 0, 1) / 127.5 - 1.0
    target_arr = np.asarray(target, dtype=np.float32).transpose(2, 0, 1) / 127.5 - 1.0
    pred_tensor = torch.from_numpy(pred_arr).unsqueeze(0).to(device)
    target_tensor = torch.from_numpy(target_arr).unsqueeze(0).to(device)
    with torch.no_grad():
        value = model(pred_tensor, target_tensor)
    return float(value.detach().cpu().item())


def summarize(values: list[float]) -> dict[str, float | None]:
    finite_values = [value for value in values if math.isfinite(value)]
    if not finite_values:
        return {"mean": None, "min": None, "max": None}
    return {
        "mean": round(float(mean(finite_values)), 6),
        "min": round(float(min(finite_values)), 6),
        "max": round(float(max(finite_values)), 6),
    }


def method_specs(output_root: Path) -> list[MethodSpec]:
    return [
        MethodSpec("baseline", "StableVITON baseline", output_root / "rank4_module8" / "baseline" / "pair"),
        MethodSpec("rank4_module8", "rank4-module8", output_root / "rank4_module8" / "lora" / "pair"),
        MethodSpec("rank8_module8", "rank8-module8", output_root / "rank8_module8" / "lora" / "pair"),
        MethodSpec("rank8_module16", "rank8-module16", output_root / "rank8_module16" / "lora" / "pair"),
    ]


def evaluate(
    eval_root: Path,
    output_root: Path,
    pairs: list[tuple[str, str]],
    lpips_bundle: Any | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_rows: list[dict[str, Any]] = []
    methods: dict[str, Any] = {}
    for method in method_specs(output_root):
        psnr_values: list[float] = []
        ssim_values: list[float] = []
        lpips_values: list[float] = []
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
                lpips_value = compute_lpips(lpips_bundle, pred_img, target_img) if lpips_bundle else None
            except Exception as exc:  # noqa: BLE001
                load_errors.append({"pair_id": pair_id, "error": f"{type(exc).__name__}: {exc}"})
                continue
            output_count += 1
            psnr_values.append(psnr_value)
            ssim_values.append(ssim_value)
            if lpips_value is not None:
                lpips_values.append(lpips_value)
            raw_rows.append(
                {
                    "pair_id": pair_id,
                    "method": method.key,
                    "output_path": str(output_path),
                    "psnr": psnr_value,
                    "ssim": ssim_value,
                    "lpips": lpips_value,
                }
            )
        failure_count = len(pairs) - output_count
        methods[method.key] = {
            "label": method.label,
            "output_dir": str(method.output_dir),
            "output_count": output_count,
            "failure_count": failure_count,
            "success_rate": round(output_count / len(pairs), 6) if pairs else 0.0,
            "missing_outputs_sample": missing_outputs[:20],
            "load_errors_sample": load_errors[:20],
            "psnr": summarize(psnr_values),
            "ssim": summarize(ssim_values),
            "lpips": summarize(lpips_values),
        }
    return methods, raw_rows


def make_contact_sheet(
    eval_root: Path,
    output_root: Path,
    pairs: list[tuple[str, str]],
    contact_sheet_path: Path,
    sample_count: int,
    tile_width: int,
    tile_height: int,
    label_height: int,
) -> None:
    rows = pairs[:sample_count]
    columns = [
        ("person", eval_root / "test" / "image"),
        ("cloth", eval_root / "test" / "cloth"),
        ("target", eval_root / "test" / "worn"),
        ("baseline", output_root / "rank4_module8" / "baseline" / "pair"),
        ("rank4", output_root / "rank4_module8" / "lora" / "pair"),
        ("rank8-m8", output_root / "rank8_module8" / "lora" / "pair"),
        ("rank8-m16", output_root / "rank8_module16" / "lora" / "pair"),
    ]
    tile_w, tile_h = tile_width, tile_height
    label_h = label_height
    sheet = Image.new("RGB", (tile_w * len(columns), (tile_h + label_h) * (len(rows) + 1)), "white")
    draw = ImageDraw.Draw(sheet)
    for col_idx, (label, _) in enumerate(columns):
        draw.text((col_idx * tile_w + 4, 4), label, fill=(0, 0, 0))
    for row_idx, (person_name, cloth_name) in enumerate(rows, start=1):
        pair_id = pair_id_from_name(person_name)
        for col_idx, (label, base_dir) in enumerate(columns):
            if label == "cloth":
                path = base_dir / cloth_name
            elif label in {"baseline", "rank4", "rank8-m8", "rank8-m16"}:
                path = base_dir / output_name(person_name, cloth_name)
            else:
                path = base_dir / person_name
            x = col_idx * tile_w
            y = row_idx * (tile_h + label_h)
            if path.exists():
                img = load_rgb(path).resize((tile_w, tile_h), Image.Resampling.BILINEAR)
                sheet.paste(img, (x, y + label_h))
            else:
                draw.rectangle((x, y + label_h, x + tile_w - 1, y + label_h + tile_h - 1), outline=(180, 0, 0))
                draw.text((x + 4, y + label_h + 4), "missing", fill=(180, 0, 0))
            draw.text((x + 4, y + 2), pair_id if col_idx == 0 else label, fill=(0, 0, 0))
    contact_sheet_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet_path)


def write_raw_csv(path: Path, raw_rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["pair_id", "method", "output_path", "psnr", "ssim", "lpips"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(raw_rows)


def main() -> int:
    args = parse_args()
    eval_root = Path(args.eval_root)
    output_root = Path(args.output_root)
    summary_path = Path(args.summary_json) if args.summary_json else output_root / "metrics" / "fixed_eval_100_metrics_summary.json"
    raw_csv_path = Path(args.raw_csv) if args.raw_csv else output_root / "metrics" / "fixed_eval_100_metrics_raw.csv"
    contact_sheet_path = (
        Path(args.contact_sheet)
        if args.contact_sheet
        else output_root / "contact_sheet" / "fixed_eval_100_sample20_contact_sheet.jpg"
    )
    pairs = read_pairs(eval_root / "test_pairs.txt")
    lpips_bundle, lpips_skip_reason = maybe_lpips_model(args.skip_lpips)
    methods, raw_rows = evaluate(eval_root, output_root, pairs, lpips_bundle)
    make_contact_sheet(
        eval_root,
        output_root,
        pairs,
        contact_sheet_path,
        args.sample_count,
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        label_height=args.label_height,
    )
    write_raw_csv(raw_csv_path, raw_rows)

    summary: dict[str, Any] = {
        "task": "evaluate_lora_outputs",
        "eval_root": str(eval_root),
        "output_root": str(output_root),
        "pair_count": len(pairs),
        "methods": methods,
        "lpips_skip_reason": lpips_skip_reason,
        "raw_csv": str(raw_csv_path),
        "contact_sheet": str(contact_sheet_path),
        "contact_sheet_tile_size": [args.tile_width, args.tile_height],
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
