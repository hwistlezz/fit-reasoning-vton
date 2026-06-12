#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Iterable


DEFAULT_INPUT = (
    r"D:\projects\fit-reasoning-vton\backend\datasets\processed\index"
    r"\aihub_pairs_explicit_pending.csv"
)
DEFAULT_OUTPUT_ROOT = r"D:\fit_transfer\metadata_39k"
KNOWN_BAD_PAIRS = ("EP00003620", "EP00003937", "EP00005080", "EP00007279")

ESTIMATE_39K_GB = {
    "unpacked_artifacts": 827.537,
    "final_zip_7z": 395.952,
    "split_parts": 395.952,
    "package_only_workspace": 975.426,
    "recommended_peak": 1802.964,
}


def normalize_pair_id(value: str | None) -> str:
    return (value or "").strip().upper()


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
        return rows, list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_bad_pairs(path: Path, bad_pairs: Iterable[str]) -> None:
    rows = [{"pair_id": normalize_pair_id(pair_id)} for pair_id in bad_pairs]
    write_csv(path, rows, ["pair_id"])


def ensure_fields(fieldnames: list[str], extra: Iterable[str]) -> list[str]:
    out = list(fieldnames)
    for name in extra:
        if name not in out:
            out.append(name)
    return out


def clean_rows(
    rows: list[dict[str, str]],
    bad_pairs: set[str],
) -> tuple[list[dict[str, str]], dict[str, int]]:
    seen: set[str] = set()
    clean: list[dict[str, str]] = []
    stats = {
        "input_rows": len(rows),
        "missing_pair_id": 0,
        "known_bad_removed": 0,
        "duplicate_pair_id_removed": 0,
    }
    for row in rows:
        pair_id = normalize_pair_id(row.get("pair_id"))
        if not pair_id:
            stats["missing_pair_id"] += 1
            continue
        if pair_id in bad_pairs:
            stats["known_bad_removed"] += 1
            continue
        if pair_id in seen:
            stats["duplicate_pair_id_removed"] += 1
            continue
        seen.add(pair_id)
        item = dict(row)
        item["pair_id"] = pair_id
        clean.append(item)
    stats["clean_rows"] = len(clean)
    return clean, stats


def split_train_val(
    rows: list[dict[str, str]],
    seed: int,
    val_ratio: float,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    source_has_split = any((row.get("split") or "").strip() for row in rows)
    if source_has_split:
        train: list[dict[str, str]] = []
        val: list[dict[str, str]] = []
        for row in rows:
            split = (row.get("split") or "").strip().lower()
            if split in {"val", "valid", "validation", "test", "eval"}:
                val.append(row)
            else:
                train.append(row)
        return train, val

    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    n_val = max(1, int(round(len(shuffled) * val_ratio))) if shuffled else 0
    return shuffled[n_val:], shuffled[:n_val]


def fixed_eval(rows: list[dict[str, str]], seed: int, count: int) -> list[dict[str, str]]:
    sample = list(rows)
    random.Random(seed).shuffle(sample)
    sample = sample[: min(count, len(sample))]
    return sorted(sample, key=lambda row: row["pair_id"])


def chunk_rows(rows: list[dict[str, str]], chunk_size: int) -> list[list[dict[str, str]]]:
    return [rows[i : i + chunk_size] for i in range(0, len(rows), chunk_size)]


def read_pair_ids(path: Path) -> list[str]:
    rows, _ = read_csv(path)
    return [normalize_pair_id(row.get("pair_id")) for row in rows]


def maybe_write_chunk(
    path: Path,
    rows: list[dict[str, str]],
    fieldnames: list[str],
    reuse_existing: bool,
) -> str:
    expected = [row["pair_id"] for row in rows]
    if path.exists() and reuse_existing:
        existing = read_pair_ids(path)
        if existing == expected:
            return "reused"
        raise ValueError(
            f"Existing chunk CSV does not match expected pair_id order: {path}"
        )
    write_csv(path, rows, fieldnames)
    return "written"


def estimate_for_rows(row_count: int, total_count: int) -> dict[str, float]:
    ratio = (row_count / total_count) if total_count else 0.0
    return {
        key: round(value * ratio, 3)
        for key, value in ESTIMATE_39K_GB.items()
    }


def build(args: argparse.Namespace) -> dict[str, object]:
    input_csv = Path(args.input_csv)
    output_root = Path(args.output_root)
    chunk_root = output_root / "chunks"
    bad_pairs = {normalize_pair_id(value) for value in args.bad_pair}

    rows, input_fields = read_csv(input_csv)
    clean, stats = clean_rows(rows, bad_pairs)
    fields = ensure_fields(input_fields, ["chunk_id", "chunk_index"])

    output_root.mkdir(parents=True, exist_ok=True)
    chunk_root.mkdir(parents=True, exist_ok=True)

    write_bad_pairs(output_root / "bad_pairs_known.csv", sorted(bad_pairs))
    write_csv(output_root / "metadata_39k_clean_candidate.csv", clean, fields)

    train_rows, val_rows = split_train_val(clean, args.seed, args.val_ratio)
    write_csv(output_root / "metadata_39k_train.csv", train_rows, fields)
    write_csv(output_root / "metadata_39k_val.csv", val_rows, fields)
    eval_source = val_rows if len(val_rows) >= args.fixed_eval_count else clean
    eval_rows = fixed_eval(eval_source, args.seed, args.fixed_eval_count)
    write_csv(output_root / "metadata_39k_fixed_eval_100.csv", eval_rows, fields)

    chunks = chunk_rows(clean, args.chunk_size)
    chunk_summaries = []
    for index, chunk in enumerate(chunks):
        chunk_id = f"chunk_{index:03d}"
        chunk_rows_with_id: list[dict[str, str]] = []
        for row_index, row in enumerate(chunk):
            item = dict(row)
            item["chunk_id"] = chunk_id
            item["chunk_index"] = str(row_index)
            chunk_rows_with_id.append(item)
        path = chunk_root / f"{chunk_id}.csv"
        status = maybe_write_chunk(path, chunk_rows_with_id, fields, args.reuse_existing)
        chunk_summaries.append(
            {
                "chunk_id": chunk_id,
                "path": str(path),
                "row_count": len(chunk_rows_with_id),
                "first_pair_id": chunk_rows_with_id[0]["pair_id"] if chunk_rows_with_id else "",
                "last_pair_id": chunk_rows_with_id[-1]["pair_id"] if chunk_rows_with_id else "",
                "write_status": status,
                "estimated_gb": estimate_for_rows(len(chunk_rows_with_id), len(clean)),
            }
        )

    summary = {
        "input_csv": str(input_csv),
        "output_root": str(output_root),
        "chunk_size": args.chunk_size,
        "seed": args.seed,
        "known_bad_pairs": sorted(bad_pairs),
        "stats": stats,
        "split_counts": {
            "train": len(train_rows),
            "val": len(val_rows),
            "fixed_eval_100": len(eval_rows),
        },
        "full_39k_estimate_gb": ESTIMATE_39K_GB,
        "chunks": chunk_summaries,
    }
    (output_root / "chunk_summary_39k.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build 39k clean metadata and 10k chunk manifests."
    )
    parser.add_argument("--input-csv", default=DEFAULT_INPUT)
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--chunk-size", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--val-ratio", type=float, default=0.05)
    parser.add_argument("--fixed-eval-count", type=int, default=100)
    parser.add_argument(
        "--bad-pair",
        action="append",
        default=list(KNOWN_BAD_PAIRS),
        help="Known bad pair_id to exclude. Can be passed multiple times.",
    )
    parser.add_argument(
        "--reuse-existing",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Reuse existing chunk CSVs only when pair_id order matches.",
    )
    return parser.parse_args()


def main() -> None:
    summary = build(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
