#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageOps, ImageStat


IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
MASK_EXTS = (".png", ".jpg", ".jpeg")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose StableVITON agnostic-v3.2 / agnostic-mask semantic coverage."
    )
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--artifact-root-before", required=True)
    parser.add_argument("--artifact-root-after", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--force-pair", action="append", default=[])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--target-min-ratio", type=float, default=0.12)
    parser.add_argument("--target-max-ratio", type=float, default=0.28)
    parser.add_argument("--too-small-ratio", type=float, default=0.10)
    parser.add_argument("--too-large-ratio", type=float, default=0.40)
    return parser.parse_args()


def normalize_pair_id(value: str | None) -> str:
    return (value or "").strip().upper()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader], list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def select_rows(rows: list[dict[str, str]], limit: int | None, force_pairs: list[str], seed: int) -> list[dict[str, str]]:
    del seed
    forced = {normalize_pair_id(value) for value in force_pairs}
    by_pair = {normalize_pair_id(row.get("pair_id")): row for row in rows}
    selected: list[dict[str, str]] = []
    seen: set[str] = set()
    for pair_id in forced:
        row = by_pair.get(pair_id)
        if row and pair_id not in seen:
            selected.append(row)
            seen.add(pair_id)
    for row in rows:
        if limit is not None and len(selected) >= limit:
            break
        if normalize_pair_id(row.get("pair_id")) in seen:
            continue
        selected.append(row)
        seen.add(normalize_pair_id(row.get("pair_id")))
    return selected


def candidate_names(folder: str, pair_id: str) -> list[str]:
    if folder == "openpose-json":
        return [f"{pair_id}_keypoints.json", f"{pair_id}.json"]
    if folder in {"image", "cloth", "worn", "fit", "agnostic-v3.2"}:
        return [f"{pair_id}{ext}" for ext in IMAGE_EXTS]
    return [f"{pair_id}{ext}" for ext in MASK_EXTS] + [f"{pair_id}_mask.png"]


def find_artifact(root: Path, folder: str, pair_id: str) -> Path | None:
    base = root / folder
    for name in candidate_names(folder, pair_id):
        path = base / name
        if path.exists():
            return path
    return None


def fallback_artifact(before: Path, after: Path, folder: str, pair_id: str) -> Path | None:
    return find_artifact(after, folder, pair_id) or find_artifact(before, folder, pair_id)


def open_rgb(path: Path, size: tuple[int, int] = (192, 256)) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        return image.resize(size, Image.Resampling.BILINEAR)


def open_mask(path: Path, size: tuple[int, int] = (192, 256)) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("L")
        image = image.resize(size, Image.Resampling.NEAREST)
        return image.point(lambda value: 255 if value > 0 else 0)


def open_parse(path: Path, size: tuple[int, int] = (192, 256)) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("L")
        return image.resize(size, Image.Resampling.NEAREST)


def mask_ratio(path: Path | None) -> float | None:
    if not path:
        return None
    mask = open_mask(path)
    hist = mask.histogram()
    total = sum(hist)
    return (total - hist[0]) / total if total else None


def bbox_stats(path: Path | None) -> dict[str, float | None]:
    if not path:
        return {"bbox_w_ratio": None, "bbox_h_ratio": None, "bbox_area_ratio": None}
    mask = open_mask(path)
    bbox = mask.getbbox()
    if not bbox:
        return {"bbox_w_ratio": 0.0, "bbox_h_ratio": 0.0, "bbox_area_ratio": 0.0}
    x0, y0, x1, y1 = bbox
    w, h = mask.size
    bw = (x1 - x0) / w
    bh = (y1 - y0) / h
    return {"bbox_w_ratio": bw, "bbox_h_ratio": bh, "bbox_area_ratio": bw * bh}


def parse_unique_labels(path: Path | None) -> int | None:
    if not path:
        return None
    parse = open_parse(path)
    colors = parse.getcolors(maxcolors=65536) or []
    return len(colors)


def diff_metrics(image_path: Path | None, agnostic_path: Path | None, mask_path: Path | None) -> dict[str, float | None]:
    if not image_path or not agnostic_path or not mask_path:
        return {
            "inside_mask_image_vs_agnostic_diff": None,
            "outside_mask_image_vs_agnostic_diff": None,
            "global_image_vs_agnostic_diff": None,
        }
    image = open_rgb(image_path)
    agnostic = open_rgb(agnostic_path)
    mask = open_mask(mask_path)
    inv = ImageOps.invert(mask)
    diff = ImageChops.difference(image, agnostic).convert("L")
    inside = ImageStat.Stat(diff, mask=mask).mean[0] / 255 if mask.getbbox() else 0.0
    outside = ImageStat.Stat(diff, mask=inv).mean[0] / 255 if inv.getbbox() else 0.0
    global_diff = ImageStat.Stat(diff).mean[0] / 255
    return {
        "inside_mask_image_vs_agnostic_diff": inside,
        "outside_mask_image_vs_agnostic_diff": outside,
        "global_image_vs_agnostic_diff": global_diff,
    }


def diagnose_row(row: dict[str, str], before: Path, after: Path, args: argparse.Namespace) -> dict[str, Any]:
    pair_id = normalize_pair_id(row.get("pair_id"))
    image = find_artifact(before, "image", pair_id)
    parse = find_artifact(before, "image-parse", pair_id)
    before_mask = find_artifact(before, "agnostic-mask", pair_id)
    after_mask = find_artifact(after, "agnostic-mask", pair_id)
    before_agnostic = find_artifact(before, "agnostic-v3.2", pair_id)
    after_agnostic = find_artifact(after, "agnostic-v3.2", pair_id)
    before_ratio = mask_ratio(before_mask)
    after_ratio = mask_ratio(after_mask)
    bbox = bbox_stats(after_mask)
    diffs = diff_metrics(image, after_agnostic, after_mask)
    unique_labels = parse_unique_labels(parse)
    reasons: list[str] = []
    if after_ratio is None:
        reasons.append("missing_after_mask")
    else:
        if after_ratio < args.too_small_ratio:
            reasons.append("after_mask_too_small")
        if after_ratio > args.too_large_ratio:
            reasons.append("after_mask_too_large")
        if after_ratio < args.target_min_ratio:
            reasons.append("below_target_min")
        if after_ratio > args.target_max_ratio:
            reasons.append("above_target_max")
    if unique_labels is not None and unique_labels < 4:
        reasons.append("parse_unique_label_count_low")
    if (diffs["inside_mask_image_vs_agnostic_diff"] or 0) < 0.035:
        reasons.append("agnostic_too_similar_inside_mask")
    if (diffs["outside_mask_image_vs_agnostic_diff"] or 0) > 0.08:
        reasons.append("agnostic_changes_outside_mask")
    return {
        "pair_id": pair_id,
        "category": row.get("category", ""),
        "pose": row.get("pose", ""),
        "angle": row.get("angle", ""),
        "before_mask_ratio": before_ratio,
        "after_mask_ratio": after_ratio,
        "ratio_delta": (after_ratio - before_ratio) if before_ratio is not None and after_ratio is not None else None,
        "parse_unique_labels": unique_labels,
        **bbox,
        **diffs,
        "reasons": "|".join(reasons),
        "before_mask_path": str(before_mask) if before_mask else "",
        "after_mask_path": str(after_mask) if after_mask else "",
        "after_agnostic_path": str(after_agnostic) if after_agnostic else "",
    }


def stat(values: list[float | None]) -> dict[str, float | int | None]:
    data = sorted(value for value in values if value is not None)
    if not data:
        return {"count": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "count": len(data),
        "min": data[0],
        "median": median(data),
        "mean": mean(data),
        "max": data[-1],
    }


def tile(path: Path | None, mode: str, cell: tuple[int, int]) -> Image.Image:
    canvas = Image.new("RGB", cell, (245, 245, 245))
    if not path or not path.exists():
        return canvas
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        if mode == "mask":
            image = image.convert("L").point(lambda value: 255 if value > 0 else 0).convert("RGB")
        elif mode == "parse":
            image = image.convert("P").convert("RGB")
        else:
            image = image.convert("RGB")
        image.thumbnail((cell[0] - 8, cell[1] - 26), Image.Resampling.BILINEAR)
        x = (cell[0] - image.width) // 2
        y = 22 + (cell[1] - 26 - image.height) // 2
        canvas.paste(image, (x, y))
    return canvas


def contact_sheet(path: Path, rows: list[dict[str, Any]], before: Path, after: Path, title: str) -> None:
    columns = [
        ("image", "image", "rgb", before),
        ("agnostic-v3.2", "before agn", "rgb", before),
        ("agnostic-mask", "before mask", "mask", before),
        ("agnostic-v3.2", "after agn", "rgb", after),
        ("agnostic-mask", "after mask", "mask", after),
        ("image-parse", "parse", "parse", before),
        ("cloth", "cloth", "rgb", before),
    ]
    cell = (145, 190)
    header = 46
    height = header + cell[1] * max(1, len(rows))
    width = cell[0] * len(columns)
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    draw.rectangle([0, 0, width, header], fill=(35, 35, 35))
    draw.text((8, 6), title, fill=(255, 255, 255))
    for idx, (_, label, _, _) in enumerate(columns):
        draw.text((idx * cell[0] + 6, 26), label, fill=(230, 230, 230))
    for ridx, row in enumerate(rows):
        pair_id = row["pair_id"]
        y = header + ridx * cell[1]
        for cidx, (folder, _label, mode, root) in enumerate(columns):
            x = cidx * cell[0]
            image = tile(find_artifact(root, folder, pair_id), mode, cell)
            sheet.paste(image, (x, y))
            draw.rectangle([x, y, x + cell[0] - 1, y + cell[1] - 1], outline=(220, 220, 220))
        label = (
            f"{pair_id} before={row.get('before_mask_ratio'):.3f} "
            f"after={row.get('after_mask_ratio'):.3f} {row.get('reasons', '')}"
        )
        draw.rectangle([0, y, min(width, 760), y + 17], fill=(255, 255, 255))
        draw.text((4, y + 2), label[:150], fill=(0, 0, 0))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=88)


def write_summary(output_dir: Path, rows: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    before = stat([row.get("before_mask_ratio") for row in rows])
    after = stat([row.get("after_mask_ratio") for row in rows])
    reason_counts: dict[str, int] = {}
    for row in rows:
        for reason in str(row.get("reasons") or "").split("|"):
            if reason:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
    summary = {
        "metadata": args.metadata,
        "artifact_root_before": args.artifact_root_before,
        "artifact_root_after": args.artifact_root_after,
        "output_dir": str(output_dir),
        "row_count": len(rows),
        "before_mask_ratio": before,
        "after_mask_ratio": after,
        "too_small_before_lt_0_10": sum(1 for row in rows if (row.get("before_mask_ratio") or 0) < args.too_small_ratio),
        "too_small_after_lt_0_10": sum(1 for row in rows if (row.get("after_mask_ratio") or 0) < args.too_small_ratio),
        "too_large_after_gt_0_40": sum(1 for row in rows if (row.get("after_mask_ratio") or 0) > args.too_large_ratio),
        "target_min_ratio": args.target_min_ratio,
        "target_max_ratio": args.target_max_ratio,
        "reason_counts": dict(sorted(reason_counts.items(), key=lambda item: item[1], reverse=True)),
        "semantic_gate": "passed" if after["median"] is not None and after["median"] >= args.target_min_ratio and summary_safe_large(rows, args) else "failed",
        "outputs": {
            "summary_md": str(output_dir / "summary.md"),
            "summary_json": str(output_dir / "summary.json"),
            "mask_ratio_before_after_csv": str(output_dir / "mask_ratio_before_after.csv"),
            "contact_agnostic_before_after": str(output_dir / "contact_agnostic_before_after.jpg"),
            "contact_mask_ratio_extremes_after": str(output_dir / "contact_mask_ratio_extremes_after.jpg"),
            "contact_semantic_suspicious_after": str(output_dir / "contact_semantic_suspicious_after.jpg"),
        },
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Agnostic Mask Rule v2 Smoke Summary",
        "",
        f"- Rows: `{len(rows)}`",
        f"- Before median mask ratio: `{before['median']}`",
        f"- After median mask ratio: `{after['median']}`",
        f"- Before too small `<0.10`: `{summary['too_small_before_lt_0_10']}`",
        f"- After too small `<0.10`: `{summary['too_small_after_lt_0_10']}`",
        f"- After too large `>0.40`: `{summary['too_large_after_gt_0_40']}`",
        f"- Semantic gate: `{summary['semantic_gate']}`",
        "",
        "## Reason Counts",
    ]
    for reason, count in summary["reason_counts"].items():
        lines.append(f"- `{reason}`: {count}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Rule v2 is considered ready for fixed_eval export only when the after median mask ratio is at least the target minimum, too-small masks are substantially reduced, and too-large masks remain rare.",
        ]
    )
    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def summary_safe_large(rows: list[dict[str, Any]], args: argparse.Namespace) -> bool:
    if not rows:
        return False
    too_large = sum(1 for row in rows if (row.get("after_mask_ratio") or 0) > args.too_large_ratio)
    return too_large / len(rows) <= 0.05


def run(args: argparse.Namespace) -> dict[str, Any]:
    metadata = Path(args.metadata)
    before = Path(args.artifact_root_before)
    after = Path(args.artifact_root_after)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, _ = read_csv(metadata)
    selected = select_rows(rows, args.limit, args.force_pair, args.seed)
    diagnostics = [diagnose_row(row, before, after, args) for row in selected]
    fields = [
        "pair_id",
        "category",
        "pose",
        "angle",
        "before_mask_ratio",
        "after_mask_ratio",
        "ratio_delta",
        "parse_unique_labels",
        "bbox_w_ratio",
        "bbox_h_ratio",
        "bbox_area_ratio",
        "inside_mask_image_vs_agnostic_diff",
        "outside_mask_image_vs_agnostic_diff",
        "global_image_vs_agnostic_diff",
        "reasons",
        "before_mask_path",
        "after_mask_path",
        "after_agnostic_path",
    ]
    write_csv(output_dir / "mask_ratio_before_after.csv", diagnostics, fields)
    random_rows = diagnostics[: min(100, len(diagnostics))]
    extremes = sorted(diagnostics, key=lambda row: row.get("after_mask_ratio") or 0)
    extremes = extremes[:25] + extremes[-25:]
    suspicious = sorted(
        diagnostics,
        key=lambda row: (
            len(str(row.get("reasons") or "")),
            abs((row.get("after_mask_ratio") or 0) - args.target_min_ratio),
        ),
        reverse=True,
    )[:80]
    contact_sheet(output_dir / "contact_agnostic_before_after.jpg", random_rows, before, after, "Agnostic before/after random smoke")
    contact_sheet(output_dir / "contact_mask_ratio_extremes_after.jpg", extremes, before, after, "Agnostic-mask ratio extremes after")
    contact_sheet(output_dir / "contact_semantic_suspicious_after.jpg", suspicious, before, after, "Agnostic semantic suspicious after")
    return write_summary(output_dir, diagnostics, args)


def main() -> None:
    print(json.dumps(run(parse_args()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
