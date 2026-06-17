"""Build a manifest for target-side StableVITON artifact generation.

The current AIHub 10k artifact dataset has source-side conditioning artifacts
for ``image/{pair_id}.jpg``. For target-aligned StableVITON training, the same
artifact types must be generated from ``worn/{pair_id}.jpg``. This helper does
not generate images; it writes a portable JSONL contract that a preprocessing
machine can consume.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_DATA_ROOT = Path("backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full")
DEFAULT_OUTPUT_JSONL = Path("backend/training/outputs/target_artifact_patch/target_artifact_patch_manifest.jsonl")
DEFAULT_SUMMARY_JSON = Path("backend/training/outputs/target_artifact_patch/target_artifact_patch_summary.json")

REQUIRED_INPUTS: dict[str, str] = {
    "target_worn": "worn/{pair_id}.jpg",
    "cloth": "cloth/{pair_id}.jpg",
    "source_person": "image/{pair_id}.jpg",
    "cloth_mask": "cloth-mask/{pair_id}.png",
}

EXPECTED_OUTPUTS: dict[str, str] = {
    "target_agnostic": "target-agnostic-v3.2/{pair_id}.jpg",
    "target_agnostic_mask": "target-agnostic-mask/{pair_id}_mask.png",
    "target_densepose": "target-image-densepose/{pair_id}.jpg",
    "target_parse": "target-image-parse/{pair_id}.png",
    "target_openpose_json": "target-openpose-json/{pair_id}_keypoints.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a JSONL manifest for target-side StableVITON artifact generation."
    )
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output-jsonl", type=Path, default=DEFAULT_OUTPUT_JSONL)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument(
        "--include-complete",
        action="store_true",
        help="Include rows whose target outputs already exist. By default, only incomplete rows are emitted.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validate_args(args)
        manifest_rows = read_manifest(args.data_root / "manifest.jsonl")
        if args.limit is not None:
            manifest_rows = manifest_rows[: args.limit]

        rows: list[dict[str, Any]] = []
        output_complete_count = 0
        input_ready_count = 0
        missing_input_counts = {name: 0 for name in REQUIRED_INPUTS}
        existing_output_counts = {name: 0 for name in EXPECTED_OUTPUTS}
        missing_output_counts = {name: 0 for name in EXPECTED_OUTPUTS}

        for manifest_row in manifest_rows:
            pair_id = manifest_row["pair_id"]
            required_inputs = {name: pattern.format(pair_id=pair_id) for name, pattern in REQUIRED_INPUTS.items()}
            expected_outputs = {name: pattern.format(pair_id=pair_id) for name, pattern in EXPECTED_OUTPUTS.items()}

            missing_inputs = [
                name for name, relative_path in required_inputs.items() if not (args.data_root / relative_path).is_file()
            ]
            existing_outputs = [
                name for name, relative_path in expected_outputs.items() if (args.data_root / relative_path).is_file()
            ]
            missing_outputs = [name for name in expected_outputs if name not in existing_outputs]

            if not missing_inputs:
                input_ready_count += 1
            for name in missing_inputs:
                missing_input_counts[name] += 1
            for name in existing_outputs:
                existing_output_counts[name] += 1
            for name in missing_outputs:
                missing_output_counts[name] += 1

            output_complete = not missing_outputs
            if output_complete:
                output_complete_count += 1
            if output_complete and not args.include_complete:
                continue

            rows.append(
                {
                    "pair_id": pair_id,
                    "status": "complete" if output_complete else "needs_target_artifacts",
                    "inputs": required_inputs,
                    "expected_outputs": expected_outputs,
                    "missing_inputs": missing_inputs,
                    "existing_outputs": existing_outputs,
                    "missing_outputs": missing_outputs,
                    "notes": {
                        "target_training_image": required_inputs["target_worn"],
                        "source_side_artifacts_are_not_valid_fallback": True,
                    },
                }
            )

        write_jsonl(args.output_jsonl, rows)
        summary = {
            "task": "build_target_artifact_patch_manifest",
            "data_root": str(args.data_root),
            "output_jsonl": str(args.output_jsonl),
            "total_manifest": len(read_manifest(args.data_root / "manifest.jsonl")),
            "selected_count": len(manifest_rows),
            "emitted_rows": len(rows),
            "input_ready_count": input_ready_count,
            "input_not_ready_count": len(manifest_rows) - input_ready_count,
            "output_complete_count": output_complete_count,
            "output_incomplete_count": len(manifest_rows) - output_complete_count,
            "missing_input_counts": missing_input_counts,
            "existing_output_counts": existing_output_counts,
            "missing_output_counts": missing_output_counts,
            "expected_target_output_dirs": sorted({Path(pattern).parts[0] for pattern in EXPECTED_OUTPUTS.values()}),
            "source_side_artifacts_are_not_used_as_fallback": True,
        }
        write_json(args.summary_json, summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def validate_args(args: argparse.Namespace) -> None:
    if args.limit is not None and args.limit < 0:
        raise ValueError("--limit must be non-negative")
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(payload, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
