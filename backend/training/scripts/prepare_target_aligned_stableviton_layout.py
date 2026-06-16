"""Prepare a target-aligned StableVITON layout from AIHub artifacts.

This script intentionally differs from ``prepare_stableviton_layout.py``:
it maps ``worn/{pair_id}.jpg`` into StableVITON's ``image/{pair_id}.jpg``
because StableVITON uses the ``image`` field as the first-stage training image.

It requires target-side conditioning artifacts by default. Source-side artifacts
are not reused as a fallback because that creates a mismatched training sample.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


DEFAULT_DATA_ROOT = Path("backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full")
DEFAULT_OUTPUT_ROOT = Path("backend/datasets/stableviton_aihub_10k_target_aligned_layout")
DEFAULT_SUMMARY_JSON = Path("backend/training/outputs/target_aligned_layout_prepare/summary.json")


@dataclass(frozen=True)
class ArtifactSpec:
    name: str
    candidates: tuple[str, ...]
    destination: str
    is_image: bool = True
    is_mask: bool = False
    required: bool = True


ARTIFACT_SPECS: dict[str, ArtifactSpec] = {
    "image": ArtifactSpec("image", ("worn/{pair_id}.jpg",), "image/{pair_id}.jpg"),
    "cloth": ArtifactSpec("cloth", ("cloth/{pair_id}.jpg",), "cloth/{pair_id}.jpg"),
    "worn": ArtifactSpec("worn", ("worn/{pair_id}.jpg",), "worn/{pair_id}.jpg"),
    "fit": ArtifactSpec("fit", ("fit/{pair_id}.json",), "fit/{pair_id}.json", is_image=False, required=False),
    "agnostic-v3.2": ArtifactSpec(
        "agnostic-v3.2",
        (
            "target-agnostic-v3.2/{pair_id}.jpg",
            "target-agnostic-v3.2/{pair_id}.png",
            "worn-agnostic-v3.2/{pair_id}.jpg",
            "worn-agnostic-v3.2/{pair_id}.png",
        ),
        "agnostic-v3.2/{pair_id}.jpg",
    ),
    "agnostic-mask": ArtifactSpec(
        "agnostic-mask",
        (
            "target-agnostic-mask/{pair_id}_mask.png",
            "target-agnostic-mask/{pair_id}.png",
            "worn-agnostic-mask/{pair_id}_mask.png",
            "worn-agnostic-mask/{pair_id}.png",
        ),
        "agnostic-mask/{pair_id}_mask.png",
        is_mask=True,
    ),
    "cloth-mask": ArtifactSpec("cloth-mask", ("cloth-mask/{pair_id}.png",), "cloth-mask/{pair_id}.jpg", is_mask=True),
    "image-densepose": ArtifactSpec(
        "image-densepose",
        (
            "target-image-densepose/{pair_id}.jpg",
            "target-image-densepose/{pair_id}.png",
            "worn-image-densepose/{pair_id}.jpg",
            "worn-image-densepose/{pair_id}.png",
        ),
        "image-densepose/{pair_id}.jpg",
    ),
    "image-parse": ArtifactSpec(
        "image-parse",
        ("target-image-parse/{pair_id}.png", "worn-image-parse/{pair_id}.png"),
        "image-parse/{pair_id}.png",
        is_mask=True,
    ),
    "openpose-json": ArtifactSpec(
        "openpose-json",
        (
            "target-openpose-json/{pair_id}_keypoints.json",
            "target-openpose-json/{pair_id}.json",
            "worn-openpose-json/{pair_id}_keypoints.json",
            "worn-openpose-json/{pair_id}.json",
        ),
        "openpose-json/{source_name}",
        is_image=False,
    ),
}


@dataclass(frozen=True)
class SamplePlan:
    pair_id: str
    split: str
    paths: dict[str, Path | None]
    missing_required: tuple[str, ...]
    missing_optional: tuple[str, ...]

    @property
    def is_ready(self) -> bool:
        return not self.missing_required


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a target-aligned StableVITON training layout.")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", choices=("dry-run", "copy"), default="dry-run")
    parser.add_argument("--image-height", type=int, default=512)
    parser.add_argument("--image-width", type=int, default=384)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument(
        "--allow-gt-cloth-warped-mask-from-cloth-mask",
        action="store_true",
        help="In copy mode, populate gt_cloth_warped_mask from cloth-mask, matching the current smoke runner helper.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
        rows = read_manifest(args.data_root / "manifest.jsonl")
        selected_pair_ids = [row["pair_id"] for row in rows[: args.limit]]
        split_by_pair_id = build_split(selected_pair_ids, args.test_ratio, args.seed)
        plans = [build_plan(args.data_root, pair_id, split_by_pair_id[pair_id]) for pair_id in selected_pair_ids]

        if args.mode == "copy":
            copy_ready_samples(args, plans)

        summary = build_summary(args, len(rows), selected_pair_ids, split_by_pair_id, plans)
        write_json(args.summary_json, summary)
        if args.mode == "copy":
            write_json(args.output_root / "layout_summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def validate_args(args: argparse.Namespace) -> None:
    if args.limit < 0:
        raise ValueError("--limit must be non-negative")
    if not 0 <= args.test_ratio <= 1:
        raise ValueError("--test-ratio must be between 0 and 1")
    if not args.data_root.is_dir():
        raise FileNotFoundError(f"data root not found: {args.data_root}")
    if not (args.data_root / "manifest.jsonl").is_file():
        raise FileNotFoundError(f"manifest not found: {args.data_root / 'manifest.jsonl'}")


def read_manifest(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        row = json.loads(stripped)
        pair_id = row.get("pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError(f"manifest line {line_number} is missing pair_id")
        rows.append(row)
    return rows


def build_split(pair_ids: list[str], test_ratio: float, seed: int) -> dict[str, str]:
    shuffled = list(pair_ids)
    random.Random(seed).shuffle(shuffled)
    test_count = max(0, min(len(shuffled), int(round(len(shuffled) * test_ratio))))
    test_pair_ids = set(shuffled[:test_count])
    return {pair_id: ("test" if pair_id in test_pair_ids else "train") for pair_id in pair_ids}


def first_existing(data_root: Path, pair_id: str, spec: ArtifactSpec) -> Path | None:
    for pattern in spec.candidates:
        path = data_root / pattern.format(pair_id=pair_id)
        if path.is_file():
            return path
    return None


def build_plan(data_root: Path, pair_id: str, split: str) -> SamplePlan:
    paths: dict[str, Path | None] = {}
    missing_required: list[str] = []
    missing_optional: list[str] = []
    for artifact_name, spec in ARTIFACT_SPECS.items():
        path = first_existing(data_root, pair_id, spec)
        paths[artifact_name] = path
        if path is not None:
            continue
        if spec.required:
            missing_required.append(artifact_name)
        else:
            missing_optional.append(artifact_name)
    return SamplePlan(pair_id, split, paths, tuple(missing_required), tuple(missing_optional))


def copy_ready_samples(args: argparse.Namespace, plans: list[SamplePlan]) -> None:
    create_layout_dirs(args.output_root)
    pairs_by_split: dict[str, list[tuple[str, str]]] = {"train": [], "test": []}

    for plan in plans:
        if not plan.is_ready:
            continue
        for artifact_name, source in plan.paths.items():
            if source is None:
                continue
            spec = ARTIFACT_SPECS[artifact_name]
            relative_path = spec.destination.format(pair_id=plan.pair_id, source_name=source.name)
            destination = args.output_root / plan.split / relative_path
            copy_artifact(source, destination, spec, args.image_width, args.image_height)

        if args.allow_gt_cloth_warped_mask_from_cloth_mask:
            source = args.output_root / plan.split / "cloth-mask" / f"{plan.pair_id}.jpg"
            destination = args.output_root / plan.split / "gt_cloth_warped_mask" / f"{plan.pair_id}.jpg"
            copy_artifact(source, destination, ARTIFACT_SPECS["cloth-mask"], args.image_width, args.image_height)

        filename = f"{plan.pair_id}.jpg"
        pairs_by_split[plan.split].append((filename, filename))

    write_pairs(args.output_root / "train_pairs.txt", pairs_by_split["train"])
    write_pairs(args.output_root / "test_pairs.txt", pairs_by_split["test"])


def create_layout_dirs(output_root: Path) -> None:
    for split in ("train", "test"):
        for dirname in (*[spec.destination.split("/")[0] for spec in ARTIFACT_SPECS.values()], "gt_cloth_warped_mask"):
            (output_root / split / dirname).mkdir(parents=True, exist_ok=True)


def copy_artifact(source: Path, destination: Path, spec: ArtifactSpec, width: int, height: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not spec.is_image:
        shutil.copy2(source, destination)
        return
    mode = "L" if spec.is_mask else "RGB"
    resample = Image.Resampling.NEAREST if spec.is_mask else Image.Resampling.BILINEAR
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert(mode).resize((width, height), resample)
        image.save(destination)


def write_pairs(path: Path, pairs: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{image_name} {cloth_name}\n" for image_name, cloth_name in pairs), encoding="utf-8")


def build_summary(
    args: argparse.Namespace,
    total_manifest: int,
    selected_pair_ids: list[str],
    split_by_pair_id: dict[str, str],
    plans: list[SamplePlan],
) -> dict[str, Any]:
    ready = [plan for plan in plans if plan.is_ready]
    missing_counts = {artifact_name: 0 for artifact_name in ARTIFACT_SPECS}
    for plan in plans:
        for artifact_name in plan.missing_required:
            missing_counts[artifact_name] += 1
    return {
        "task": "prepare_target_aligned_stableviton_layout",
        "data_root": str(args.data_root),
        "output_root": str(args.output_root),
        "mode": args.mode,
        "total_manifest": total_manifest,
        "selected_count": len(selected_pair_ids),
        "train_count": sum(1 for split in split_by_pair_id.values() if split == "train"),
        "test_count": sum(1 for split in split_by_pair_id.values() if split == "test"),
        "ready_count": len(ready),
        "not_ready_count": len(plans) - len(ready),
        "missing_required_counts": missing_counts,
        "allow_gt_cloth_warped_mask_from_cloth_mask": args.allow_gt_cloth_warped_mask_from_cloth_mask,
        "copied_count": len(ready) if args.mode == "copy" else 0,
        "not_ready_examples": [
            {
                "pair_id": plan.pair_id,
                "missing_required": list(plan.missing_required),
            }
            for plan in plans
            if not plan.is_ready
        ][:20],
        "mapping": {
            "stableviton_image": "worn/{pair_id}.jpg",
            "stableviton_cloth": "cloth/{pair_id}.jpg",
            "target_agnostic_required": "target-agnostic-v3.2 or worn-agnostic-v3.2",
            "target_densepose_required": "target-image-densepose or worn-image-densepose",
            "source_side_artifacts_are_not_used_as_fallback": True,
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
