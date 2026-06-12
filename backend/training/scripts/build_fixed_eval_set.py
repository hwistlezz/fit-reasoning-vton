"""Build a fixed StableVITON evaluation subset from an existing layout.

The generated pair list and resized evaluation layout are experiment artifacts
and should be written under ignored output directories.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        default=r"D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train",
    )
    parser.add_argument(
        "--output-root",
        default=r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\fixed_eval_100_lora_comparison",
    )
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--seed", type=int, default=124)
    parser.add_argument("--source-split", default="train")
    parser.add_argument("--image-height", type=int, default=512)
    parser.add_argument("--image-width", type=int, default=384)
    parser.add_argument("--summary-json", default=None)
    return parser.parse_args()


def read_pairs(path: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        image_name, cloth_name = stripped.split()
        pairs.append((image_name, cloth_name))
    return pairs


def pair_id_from_name(name: str) -> str:
    return Path(name).stem


def candidate_artifacts(root: Path, split: str, image_name: str, cloth_name: str) -> dict[str, Path]:
    pair_id = pair_id_from_name(image_name)
    split_root = root / split
    return {
        "person_image": split_root / "image" / image_name,
        "cloth_image": split_root / "cloth" / cloth_name,
        "agnostic_person": split_root / "agnostic-v3.2" / image_name,
        "agnostic_mask": split_root / "agnostic-mask" / image_name.replace(".jpg", "_mask.png"),
        "cloth_mask": split_root / "cloth-mask" / cloth_name,
        "densepose": split_root / "image-densepose" / image_name,
        "human_parsing": split_root / "image-parse" / image_name.replace(".jpg", ".png"),
        "openpose_json": split_root / "openpose-json" / f"{pair_id}_keypoints.json",
        "target_worn": split_root / "worn" / image_name,
    }


def resize_copy(src: Path, dst: Path, width: int, height: int, is_mask: bool = False) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    mode = "L" if is_mask else "RGB"
    resample = Image.Resampling.NEAREST if is_mask else Image.Resampling.BILINEAR
    with Image.open(src) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert(mode).resize((width, height), resample)
        image.save(dst)


def copy_json(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_eval_layout(
    data_root: Path,
    output_root: Path,
    selected_pairs: list[tuple[str, str]],
    source_split: str,
    width: int,
    height: int,
) -> Path:
    eval_root = output_root / "fixed_eval_100_data"
    test_root = eval_root / "test"
    eval_root.mkdir(parents=True, exist_ok=True)
    (eval_root / "train_pairs.txt").write_text("", encoding="utf-8")
    (eval_root / "test_pairs.txt").write_text(
        "".join(f"{image_name} {cloth_name}\n" for image_name, cloth_name in selected_pairs),
        encoding="utf-8",
    )

    for image_name, cloth_name in selected_pairs:
        artifacts = candidate_artifacts(data_root, source_split, image_name, cloth_name)
        resize_copy(artifacts["person_image"], test_root / "image" / image_name, width, height)
        resize_copy(artifacts["cloth_image"], test_root / "cloth" / cloth_name, width, height)
        resize_copy(artifacts["agnostic_person"], test_root / "agnostic-v3.2" / image_name, width, height)
        resize_copy(artifacts["agnostic_mask"], test_root / "agnostic-mask" / image_name.replace(".jpg", "_mask.png"), width, height, is_mask=True)
        resize_copy(artifacts["cloth_mask"], test_root / "cloth-mask" / cloth_name, width, height, is_mask=True)
        resize_copy(artifacts["densepose"], test_root / "image-densepose" / image_name, width, height)
        resize_copy(artifacts["human_parsing"], test_root / "image-parse" / image_name.replace(".jpg", ".png"), width, height, is_mask=True)
        resize_copy(artifacts["target_worn"], test_root / "worn" / image_name, width, height)
        copy_json(artifacts["openpose_json"], test_root / "openpose-json" / artifacts["openpose_json"].name)
    return eval_root


def main() -> int:
    args = parse_args()
    data_root = Path(args.data_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    summary_path = Path(args.summary_json) if args.summary_json else output_root / "fixed_eval_100_summary.json"
    pair_list_path = output_root / "fixed_eval_100_pairs.txt"

    source_pair_file = data_root / f"{args.source_split}_pairs.txt"
    if not source_pair_file.exists():
        raise FileNotFoundError(f"pair file not found: {source_pair_file}")

    pairs = read_pairs(source_pair_file)
    seen: set[str] = set()
    ready_pairs: list[tuple[str, str]] = []
    missing_examples: list[dict[str, Any]] = []
    for image_name, cloth_name in pairs:
        pair_id = pair_id_from_name(image_name)
        if pair_id in seen:
            continue
        seen.add(pair_id)
        artifacts = candidate_artifacts(data_root, args.source_split, image_name, cloth_name)
        missing = [name for name, path in artifacts.items() if not path.exists()]
        if missing:
            if len(missing_examples) < 20:
                missing_examples.append({"pair_id": pair_id, "missing": missing})
            continue
        ready_pairs.append((image_name, cloth_name))

    rng = random.Random(args.seed)
    rng.shuffle(ready_pairs)
    selected_pairs = sorted(ready_pairs[: args.count], key=lambda item: pair_id_from_name(item[0]))
    eval_root = build_eval_layout(
        data_root=data_root,
        output_root=output_root,
        selected_pairs=selected_pairs,
        source_split=args.source_split,
        width=args.image_width,
        height=args.image_height,
    )
    pair_list_path.write_text(
        "".join(f"{pair_id_from_name(image_name)}\n" for image_name, _ in selected_pairs),
        encoding="utf-8",
    )

    summary: dict[str, Any] = {
        "task": "build_fixed_eval_set",
        "data_root": str(data_root),
        "source_split": args.source_split,
        "output_root": str(output_root),
        "eval_root": str(eval_root),
        "pair_list_path": str(pair_list_path),
        "seed": args.seed,
        "requested_count": args.count,
        "source_pair_count": len(pairs),
        "ready_pair_count": len(ready_pairs),
        "selected_count": len(selected_pairs),
        "evaluation_type": "train-seen",
        "holdout": False,
        "missing_examples": missing_examples,
        "selected_pair_ids": [pair_id_from_name(image_name) for image_name, _ in selected_pairs],
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
