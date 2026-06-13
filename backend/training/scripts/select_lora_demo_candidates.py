"""Select review candidates from fixed LoRA comparison metrics.

This script is a triage helper. It uses PSNR/SSIM only to reduce the number of
pairs that need visual review; it does not decide final demo quality.
Generated CSV/JSON/contact sheets should be written under ignored output paths.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps


METHOD_ORDER = ("baseline", "rank4_module8", "rank8_module8", "rank8_module16")
METHOD_LABELS = {
    "baseline": "baseline",
    "rank4_module8": "rank4",
    "rank8_module8": "rank8-m8",
    "rank8_module16": "rank8-m16",
}


@dataclass(frozen=True)
class PairMetric:
    pair_id: str
    method: str
    psnr: float
    ssim: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--eval-root",
        default=r"backend\training\outputs\fixed_eval_100_lora_comparison_exif_fixed\fixed_eval_100_data",
    )
    parser.add_argument(
        "--output-root",
        default=r"backend\training\outputs\fixed_eval_100_lora_comparison_exif_fixed",
    )
    parser.add_argument(
        "--raw-csv",
        default=r"backend\training\outputs\fixed_eval_100_lora_comparison_exif_fixed\metrics\fixed_eval_100_metrics_raw.csv",
    )
    parser.add_argument(
        "--summary-json",
        default=r"backend\training\outputs\fixed_eval_100_lora_comparison_exif_fixed\review\candidate_summary.json",
    )
    parser.add_argument(
        "--review-csv",
        default=r"backend\training\outputs\fixed_eval_100_lora_comparison_exif_fixed\review\candidate_review.csv",
    )
    parser.add_argument(
        "--candidate-sheet",
        default=r"backend\training\outputs\fixed_eval_100_lora_comparison_exif_fixed\review\candidate_top20_sheet.jpg",
    )
    parser.add_argument("--candidate-count", type=int, default=20)
    parser.add_argument("--tile-width", type=int, default=256)
    parser.add_argument("--tile-height", type=int, default=341)
    parser.add_argument("--label-height", type=int, default=24)
    return parser.parse_args()


def pair_filename(pair_id: str) -> str:
    return f"{pair_id}.jpg"


def output_name(pair_id: str) -> str:
    return f"{pair_id}_{pair_id}.jpg"


def load_rgb(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
        if size is not None and image.size != size:
            image = image.resize(size, Image.Resampling.BILINEAR)
        return image.copy()


def read_metrics(path: Path) -> dict[str, dict[str, PairMetric]]:
    rows: dict[str, dict[str, PairMetric]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            pair_id = row["pair_id"]
            method = row["method"]
            rows.setdefault(pair_id, {})[method] = PairMetric(
                pair_id=pair_id,
                method=method,
                psnr=float(row["psnr"]),
                ssim=float(row["ssim"]),
            )
    return rows


def bucket_for(best_psnr: float, best_ssim: float) -> str:
    if best_psnr >= 20.0 and best_ssim >= 0.78:
        return "success"
    if best_psnr >= 18.0 and best_ssim >= 0.62:
        return "usable"
    return "fail"


def method_output_dirs(output_root: Path) -> dict[str, Path]:
    return {
        "baseline": output_root / "rank4_module8" / "baseline" / "pair",
        "rank4_module8": output_root / "rank4_module8" / "lora" / "pair",
        "rank8_module8": output_root / "rank8_module8" / "lora" / "pair",
        "rank8_module16": output_root / "rank8_module16" / "lora" / "pair",
    }


def summarize_pairs(metrics: dict[str, dict[str, PairMetric]]) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    for pair_id in sorted(metrics):
        pair_metrics = metrics[pair_id]
        if not all(method in pair_metrics for method in METHOD_ORDER):
            continue
        best_metric = max(pair_metrics.values(), key=lambda metric: (metric.ssim, metric.psnr))
        baseline = pair_metrics["baseline"]
        rank8_m16 = pair_metrics["rank8_module16"]
        best_psnr = best_metric.psnr
        best_ssim = best_metric.ssim
        summary_rows.append(
            {
                "pair_id": pair_id,
                "bucket": bucket_for(best_psnr, best_ssim),
                "best_method": best_metric.method,
                "best_psnr": round(best_psnr, 6),
                "best_ssim": round(best_ssim, 6),
                "baseline_psnr": round(baseline.psnr, 6),
                "baseline_ssim": round(baseline.ssim, 6),
                "rank8_module16_psnr": round(rank8_m16.psnr, 6),
                "rank8_module16_ssim": round(rank8_m16.ssim, 6),
                "best_minus_baseline_ssim": round(best_ssim - baseline.ssim, 6),
                "needs_visual_review": True,
                "visual_tag": "",
                "review_note": "",
            }
        )
    summary_rows.sort(key=lambda row: (row["bucket"] != "success", -row["best_ssim"], -row["best_psnr"]))
    return summary_rows


def write_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "pair_id",
        "bucket",
        "best_method",
        "best_psnr",
        "best_ssim",
        "baseline_psnr",
        "baseline_ssim",
        "rank8_module16_psnr",
        "rank8_module16_ssim",
        "best_minus_baseline_ssim",
        "needs_visual_review",
        "visual_tag",
        "review_note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def make_candidate_sheet(
    *,
    eval_root: Path,
    output_root: Path,
    rows: list[dict[str, Any]],
    path: Path,
    candidate_count: int,
    tile_width: int,
    tile_height: int,
    label_height: int,
) -> None:
    selected = rows[:candidate_count]
    output_dirs = method_output_dirs(output_root)
    columns = [
        ("person", eval_root / "test" / "image"),
        ("cloth", eval_root / "test" / "cloth"),
        ("target", eval_root / "test" / "worn"),
        ("baseline", output_dirs["baseline"]),
        ("rank4", output_dirs["rank4_module8"]),
        ("rank8-m8", output_dirs["rank8_module8"]),
        ("rank8-m16", output_dirs["rank8_module16"]),
    ]
    sheet = Image.new(
        "RGB",
        (tile_width * len(columns), (tile_height + label_height) * (len(selected) + 1)),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    for col_idx, (label, _) in enumerate(columns):
        draw.text((col_idx * tile_width + 4, 4), label, fill=(0, 0, 0))

    for row_idx, row in enumerate(selected, start=1):
        pair_id = row["pair_id"]
        for col_idx, (label, base_dir) in enumerate(columns):
            if label in {"person", "cloth", "target"}:
                image_path = base_dir / pair_filename(pair_id)
            else:
                image_path = base_dir / output_name(pair_id)
            x = col_idx * tile_width
            y = row_idx * (tile_height + label_height)
            if image_path.exists():
                image = load_rgb(image_path).resize((tile_width, tile_height), Image.Resampling.BILINEAR)
                sheet.paste(image, (x, y + label_height))
            else:
                draw.rectangle((x, y + label_height, x + tile_width - 1, y + label_height + tile_height - 1), outline=(180, 0, 0))
                draw.text((x + 4, y + label_height + 4), "missing", fill=(180, 0, 0))
            if col_idx == 0:
                title = f"{pair_id} {row['bucket']} {row['best_method']}"
            else:
                title = label
            draw.text((x + 4, y + 2), title, fill=(0, 0, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def main() -> int:
    args = parse_args()
    eval_root = Path(args.eval_root)
    output_root = Path(args.output_root)
    raw_csv = Path(args.raw_csv)
    summary_json = Path(args.summary_json)
    review_csv = Path(args.review_csv)
    candidate_sheet = Path(args.candidate_sheet)

    metrics = read_metrics(raw_csv)
    rows = summarize_pairs(metrics)
    write_review_csv(review_csv, rows)
    make_candidate_sheet(
        eval_root=eval_root,
        output_root=output_root,
        rows=rows,
        path=candidate_sheet,
        candidate_count=args.candidate_count,
        tile_width=args.tile_width,
        tile_height=args.tile_height,
        label_height=args.label_height,
    )

    bucket_counts: dict[str, int] = {"success": 0, "usable": 0, "fail": 0}
    for row in rows:
        bucket_counts[row["bucket"]] += 1

    summary = {
        "task": "select_lora_demo_candidates",
        "eval_root": str(eval_root),
        "output_root": str(output_root),
        "raw_csv": str(raw_csv),
        "review_csv": str(review_csv),
        "candidate_sheet": str(candidate_sheet),
        "pair_count": len(rows),
        "bucket_counts": bucket_counts,
        "candidate_count": args.candidate_count,
        "top_candidates": rows[: args.candidate_count],
        "note": "Metric-based triage only. Final demo choice requires visual review.",
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
