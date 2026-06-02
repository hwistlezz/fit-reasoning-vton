from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.training.datasets.aihub_lora_dataset import AihubLoraPilotDataset


DEFAULT_DATA_ROOT = Path("backend/datasets/lora_pilot_aihub_1k")
DEFAULT_CONTACT_SHEET = Path("backend/training/outputs/lora_pilot_1k/contact_sheet.jpg")
DEFAULT_SUMMARY_JSON = Path("backend/training/outputs/lora_pilot_1k/dataset_smoke_summary.json")
IMAGE_KEYS = ("image_path", "cloth_path", "worn_path")
FIT_JSON_KEY = "fit_json_path"
TILE_SIZE = (160, 213)
LABEL_HEIGHT = 18


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-test the AIHub LoRA pilot dataset loader.")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--sample-count", type=int, default=16)
    parser.add_argument("--contact-sheet", type=Path, default=DEFAULT_CONTACT_SHEET)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--check-backend-loader", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset = AihubLoraPilotDataset(args.data_root)
    checked_count = _checked_count(len(dataset), args.limit)

    summary: dict[str, Any] = {
        "data_root": _display_path(args.data_root),
        "manifest_count": len(dataset),
        "checked_count": checked_count,
        "missing_image": 0,
        "missing_cloth": 0,
        "missing_worn": 0,
        "missing_fit": 0,
        "image_load_errors": 0,
        "fit_json_errors": 0,
        "backend_loader_errors": 0,
        "metadata_errors": 0,
        "contact_sheet_errors": 0,
        "backend_loader_checked": bool(args.check_backend_loader),
        "seed": args.seed,
        "sample_contact_sheet": _display_path(args.contact_sheet),
    }

    for index in range(checked_count):
        sample = dataset[index]
        _check_required_metadata(sample, summary)
        _check_files(sample, summary)
        _check_image_loads(sample, summary)
        _check_fit_json_load(dataset, index, summary)
        if args.check_backend_loader:
            _check_backend_loader(sample, summary)

    _write_contact_sheet(dataset, checked_count, args.sample_count, args.seed, args.contact_sheet, summary)
    _write_summary(args.summary_json, summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if _is_success(summary) else 1


def _checked_count(manifest_count: int, limit: int) -> int:
    if limit < 0:
        raise ValueError("--limit must be non-negative.")
    return min(manifest_count, limit)


def _check_required_metadata(sample: dict[str, Any], summary: dict[str, Any]) -> None:
    if not isinstance(sample.get("fit_label"), str) or not sample["fit_label"]:
        summary["metadata_errors"] += 1
        return
    if not isinstance(sample.get("confidence"), int | float):
        summary["metadata_errors"] += 1
        return
    if not isinstance(sample.get("prompt"), str) or not sample["prompt"]:
        summary["metadata_errors"] += 1


def _check_files(sample: dict[str, Any], summary: dict[str, Any]) -> None:
    if not sample["image_path"].is_file():
        summary["missing_image"] += 1
    if not sample["cloth_path"].is_file():
        summary["missing_cloth"] += 1
    if not sample["worn_path"].is_file():
        summary["missing_worn"] += 1
    if not sample["fit_json_path"].is_file():
        summary["missing_fit"] += 1


def _check_image_loads(sample: dict[str, Any], summary: dict[str, Any]) -> None:
    for key in IMAGE_KEYS:
        path = sample[key]
        if not path.is_file():
            continue
        try:
            with Image.open(path) as image:
                image.convert("RGB").load()
        except OSError:
            summary["image_load_errors"] += 1


def _check_fit_json_load(dataset: AihubLoraPilotDataset, index: int, summary: dict[str, Any]) -> None:
    fit_json_path = dataset[index][FIT_JSON_KEY]
    try:
        payload = json.loads(fit_json_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"fit json must be an object: {fit_json_path}")
    except (OSError, json.JSONDecodeError, ValueError):
        summary["fit_json_errors"] += 1


def _check_backend_loader(sample: dict[str, Any], summary: dict[str, Any]) -> None:
    if not sample["fit_json_path"].is_file():
        return
    try:
        from backend.app.services.fit_analyzer import analyze_fit

        analyze_fit(
            job_id=sample["pair_id"],
            result_image_url=None,
            fit_result_path=sample["fit_json_path"],
        )
    except Exception:
        summary["backend_loader_errors"] += 1


def _write_contact_sheet(
    dataset: AihubLoraPilotDataset,
    checked_count: int,
    sample_count: int,
    seed: int,
    contact_sheet_path: Path,
    summary: dict[str, Any],
) -> None:
    if checked_count == 0 or sample_count <= 0:
        summary["contact_sheet_errors"] += 1
        return

    rng = random.Random(seed)
    indices = rng.sample(range(checked_count), k=min(sample_count, checked_count))

    rows = []
    for index in indices:
        try:
            sample = dataset.load_sample(index)
            rows.append(_make_contact_sheet_row(sample))
        except (OSError, json.JSONDecodeError, ValueError):
            summary["contact_sheet_errors"] += 1

    if not rows:
        summary["contact_sheet_errors"] += 1
        return

    width = TILE_SIZE[0] * 3
    height = (TILE_SIZE[1] + LABEL_HEIGHT) * len(rows)
    sheet = Image.new("RGB", (width, height), "white")

    y = 0
    for row in rows:
        sheet.paste(row, (0, y))
        y += row.height

    contact_sheet_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet_path, quality=95)


def _make_contact_sheet_row(sample: dict[str, Any]) -> Image.Image:
    row = Image.new("RGB", (TILE_SIZE[0] * 3, TILE_SIZE[1] + LABEL_HEIGHT), "white")
    draw = ImageDraw.Draw(row)

    for column, image_key in enumerate(("image", "cloth", "worn")):
        tile = _fit_tile(sample[image_key])
        row.paste(tile, (column * TILE_SIZE[0], 0))

    label = str(sample["pair_id"])
    draw.text((4, TILE_SIZE[1] + 2), label, fill=(0, 0, 0))
    return row


def _fit_tile(image: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", TILE_SIZE, "white")
    thumbnail = ImageOps.contain(image, TILE_SIZE)
    x = (TILE_SIZE[0] - thumbnail.width) // 2
    y = (TILE_SIZE[1] - thumbnail.height) // 2
    canvas.paste(thumbnail, (x, y))
    return canvas


def _write_summary(summary_path: Path, summary: dict[str, Any]) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _display_path(path: Path) -> str:
    return path.as_posix()


def _is_success(summary: dict[str, Any]) -> bool:
    error_keys = (
        "missing_image",
        "missing_cloth",
        "missing_worn",
        "missing_fit",
        "image_load_errors",
        "fit_json_errors",
        "backend_loader_errors",
        "metadata_errors",
        "contact_sheet_errors",
    )
    return all(summary[key] == 0 for key in error_keys)


if __name__ == "__main__":
    raise SystemExit(main())
