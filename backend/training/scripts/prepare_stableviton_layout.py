from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_DATA_ROOT = Path("backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full")
DEFAULT_OUTPUT_ROOT = Path("backend/datasets/stableviton_aihub_10k_layout")
DEFAULT_SUMMARY_JSON = Path("backend/training/outputs/stableviton_layout_prepare/summary.json")

BASE_REQUIRED_ARTIFACTS = (
    "image",
    "cloth",
    "worn",
    "fit",
    "agnostic-v3.2",
    "agnostic-mask",
    "openpose-json",
    "image-parse",
    "cloth-mask",
)
OPTIONAL_DENSEPOSE_ARTIFACT = "image-densepose"
ALL_ARTIFACTS = (*BASE_REQUIRED_ARTIFACTS, OPTIONAL_DENSEPOSE_ARTIFACT)


@dataclass(frozen=True)
class ArtifactSpec:
    name: str
    candidates: tuple[str, ...]
    stableviton_destination: str | None


ARTIFACT_SPECS: dict[str, ArtifactSpec] = {
    "image": ArtifactSpec("image", ("image/{pair_id}.jpg",), "image/{pair_id}.jpg"),
    "cloth": ArtifactSpec("cloth", ("cloth/{pair_id}.jpg",), "cloth/{pair_id}.jpg"),
    "worn": ArtifactSpec("worn", ("worn/{pair_id}.jpg",), "worn/{pair_id}.jpg"),
    "fit": ArtifactSpec("fit", ("fit/{pair_id}.json",), "fit/{pair_id}.json"),
    "agnostic-v3.2": ArtifactSpec(
        "agnostic-v3.2",
        ("agnostic-v3.2/{pair_id}.jpg", "agnostic-v3.2/{pair_id}.png"),
        "agnostic-v3.2/{pair_id}.jpg",
    ),
    "agnostic-mask": ArtifactSpec(
        "agnostic-mask",
        ("agnostic-mask/{pair_id}_mask.png", "agnostic-mask/{pair_id}.png"),
        "agnostic-mask/{pair_id}_mask.png",
    ),
    "openpose-json": ArtifactSpec(
        "openpose-json",
        ("openpose-json/{pair_id}_keypoints.json", "openpose-json/{pair_id}.json"),
        "openpose-json/{source_name}",
    ),
    "image-parse": ArtifactSpec("image-parse", ("image-parse/{pair_id}.png",), "image-parse/{pair_id}.png"),
    "cloth-mask": ArtifactSpec(
        "cloth-mask",
        ("cloth-mask/{pair_id}.png",),
        "cloth-mask/{pair_id}.jpg",
    ),
    "image-densepose": ArtifactSpec(
        "image-densepose",
        ("image-densepose/{pair_id}.jpg", "image-densepose/{pair_id}.png"),
        "image-densepose/{pair_id}.jpg",
    ),
}


@dataclass(frozen=True)
class SampleReadiness:
    pair_id: str
    split: str
    paths: dict[str, Path | None]
    missing_required: tuple[str, ...]
    missing_optional: tuple[str, ...]

    @property
    def is_ready(self) -> bool:
        return not self.missing_required


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare or dry-run an AIHub 10k dataset in a StableVITON-style training layout."
    )
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", choices=("dry-run", "copy"), default="dry-run")
    parser.add_argument("--require-densepose", action="store_true")
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        _validate_args(args)
        rows = _read_manifest(args.data_root / "manifest.jsonl")
        selected_pair_ids = [row["pair_id"] for row in rows[: args.limit]]
        split_by_pair_id = _build_split(selected_pair_ids, args.test_ratio, args.seed)
        required_artifacts = _required_artifacts(args.require_densepose)
        optional_artifacts = _optional_artifacts(args.require_densepose)
        readiness = [
            _check_sample(args.data_root, pair_id, split_by_pair_id[pair_id], required_artifacts, optional_artifacts)
            for pair_id in selected_pair_ids
        ]

        if args.mode == "copy":
            _copy_ready_samples(args.output_root, readiness, optional_artifacts)

        summary = _build_summary(
            args=args,
            total_manifest=len(rows),
            selected_count=len(selected_pair_ids),
            split_by_pair_id=split_by_pair_id,
            required_artifacts=required_artifacts,
            optional_artifacts=optional_artifacts,
            readiness=readiness,
        )
        _write_json(args.summary_json, summary)
        if args.mode == "copy":
            _write_json(args.output_root / "layout_summary.json", summary)

        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


def _validate_args(args: argparse.Namespace) -> None:
    if args.limit < 0:
        raise ValueError("--limit must be non-negative.")
    if not 0 <= args.test_ratio <= 1:
        raise ValueError("--test-ratio must be between 0 and 1.")
    if not args.data_root.is_dir():
        raise FileNotFoundError(f"data root not found: {args.data_root}")
    manifest_path = args.data_root / "manifest.jsonl"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")


def _read_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        for line_number, line in enumerate(manifest_file, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            payload = json.loads(stripped)
            if not isinstance(payload, dict):
                raise ValueError(f"manifest line {line_number} must be a JSON object.")
            pair_id = payload.get("pair_id")
            if not isinstance(pair_id, str) or not pair_id:
                raise ValueError(f"manifest line {line_number} is missing pair_id.")
            rows.append(payload)
    return rows


def _build_split(pair_ids: list[str], test_ratio: float, seed: int) -> dict[str, str]:
    shuffled = list(pair_ids)
    random.Random(seed).shuffle(shuffled)
    test_count = int(round(len(shuffled) * test_ratio))
    test_count = max(0, min(test_count, len(shuffled)))
    test_pair_ids = set(shuffled[:test_count])
    return {pair_id: ("test" if pair_id in test_pair_ids else "train") for pair_id in pair_ids}


def _required_artifacts(require_densepose: bool) -> tuple[str, ...]:
    if require_densepose:
        return (*BASE_REQUIRED_ARTIFACTS, OPTIONAL_DENSEPOSE_ARTIFACT)
    return BASE_REQUIRED_ARTIFACTS


def _optional_artifacts(require_densepose: bool) -> tuple[str, ...]:
    if require_densepose:
        return ()
    return (OPTIONAL_DENSEPOSE_ARTIFACT,)


def _check_sample(
    data_root: Path,
    pair_id: str,
    split: str,
    required_artifacts: tuple[str, ...],
    optional_artifacts: tuple[str, ...],
) -> SampleReadiness:
    paths: dict[str, Path | None] = {}
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for artifact_name in ALL_ARTIFACTS:
        artifact_path = _first_existing_path(data_root, pair_id, ARTIFACT_SPECS[artifact_name])
        paths[artifact_name] = artifact_path
        if artifact_path is not None:
            continue
        if artifact_name in required_artifacts:
            missing_required.append(artifact_name)
        elif artifact_name in optional_artifacts:
            missing_optional.append(artifact_name)

    return SampleReadiness(
        pair_id=pair_id,
        split=split,
        paths=paths,
        missing_required=tuple(missing_required),
        missing_optional=tuple(missing_optional),
    )


def _first_existing_path(data_root: Path, pair_id: str, spec: ArtifactSpec) -> Path | None:
    for pattern in spec.candidates:
        candidate = data_root / pattern.format(pair_id=pair_id)
        if candidate.is_file():
            return candidate
    return None


def _copy_ready_samples(
    output_root: Path,
    readiness: list[SampleReadiness],
    optional_artifacts: tuple[str, ...],
) -> None:
    _create_layout_dirs(output_root)
    pairs_by_split: dict[str, list[tuple[str, str]]] = {"train": [], "test": []}

    for sample in readiness:
        if not sample.is_ready:
            continue

        for artifact_name in ALL_ARTIFACTS:
            source = sample.paths[artifact_name]
            if source is None:
                if artifact_name in optional_artifacts:
                    continue
                raise FileNotFoundError(f"ready sample missing required path: {sample.pair_id} {artifact_name}")
            destination = _destination_path(output_root, sample.split, sample.pair_id, artifact_name, source)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        image_filename = f"{sample.pair_id}.jpg"
        cloth_filename = f"{sample.pair_id}.jpg"
        pairs_by_split[sample.split].append((image_filename, cloth_filename))

    _write_pairs(output_root / "train_pairs.txt", pairs_by_split["train"])
    _write_pairs(output_root / "test_pairs.txt", pairs_by_split["test"])


def _create_layout_dirs(output_root: Path) -> None:
    for split in ("train", "test"):
        for artifact_name in ALL_ARTIFACTS:
            (output_root / split / artifact_name).mkdir(parents=True, exist_ok=True)


def _destination_path(output_root: Path, split: str, pair_id: str, artifact_name: str, source: Path) -> Path:
    destination_pattern = ARTIFACT_SPECS[artifact_name].stableviton_destination
    if destination_pattern is None:
        raise ValueError(f"artifact has no destination pattern: {artifact_name}")
    relative_path = destination_pattern.format(pair_id=pair_id, source_name=source.name)
    return output_root / split / relative_path


def _write_pairs(path: Path, pairs: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{image_filename} {cloth_filename}" for image_filename, cloth_filename in pairs]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _build_summary(
    args: argparse.Namespace,
    total_manifest: int,
    selected_count: int,
    split_by_pair_id: dict[str, str],
    required_artifacts: tuple[str, ...],
    optional_artifacts: tuple[str, ...],
    readiness: list[SampleReadiness],
) -> dict[str, Any]:
    ready_samples = [sample for sample in readiness if sample.is_ready]
    not_ready_samples = [sample for sample in readiness if not sample.is_ready]
    planned_train_count = sum(1 for split in split_by_pair_id.values() if split == "train")
    planned_test_count = sum(1 for split in split_by_pair_id.values() if split == "test")

    missing_counts = {
        artifact_name: sum(1 for sample in readiness if sample.paths[artifact_name] is None)
        for artifact_name in ALL_ARTIFACTS
    }
    ready_counts_by_split = {
        "train": sum(1 for sample in ready_samples if sample.split == "train"),
        "test": sum(1 for sample in ready_samples if sample.split == "test"),
    }

    return {
        "data_root": _display_path(args.data_root),
        "output_root": _display_path(args.output_root),
        "mode": args.mode,
        "total_manifest": total_manifest,
        "selected_count": selected_count,
        "train_count": planned_train_count,
        "test_count": planned_test_count,
        "ready_train_count": ready_counts_by_split["train"],
        "ready_test_count": ready_counts_by_split["test"],
        "required_artifacts": list(required_artifacts),
        "optional_artifacts": list(optional_artifacts),
        "missing_counts": missing_counts,
        "ready_count": len(ready_samples),
        "not_ready_count": len(not_ready_samples),
        "require_densepose": bool(args.require_densepose),
        "test_ratio": args.test_ratio,
        "seed": args.seed,
        "copied_count": len(ready_samples) if args.mode == "copy" else 0,
        "not_ready_examples": [
            {
                "pair_id": sample.pair_id,
                "split": sample.split,
                "missing_required": list(sample.missing_required),
                "missing_optional": list(sample.missing_optional),
            }
            for sample in not_ready_samples[:20]
        ],
        "stableviton_filename_notes": {
            "pair_file_format": "{pair_id}.jpg {pair_id}.jpg",
            "agnostic_mask_destination": "agnostic-mask/{pair_id}_mask.png",
            "cloth_mask_destination": "cloth-mask/{pair_id}.jpg",
            "densepose_destination": "image-densepose/{pair_id}.jpg",
            "worn_target_note": "worn is copied as a target candidate, but StableVITON image/worn mapping must be rechecked before training.",
        },
    }


def _display_path(path: Path) -> str:
    return path.as_posix()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
