#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def read_csv(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--processed-root", required=True)
    args = parser.parse_args()

    root = Path(args.processed_root)
    progress = read_csv(root / "preprocess_progress.csv")
    failures = read_csv(root / "failures.csv")
    elapsed = [float(r.get("elapsed_sec", 0) or 0) for r in progress if r.get("status") != "skipped"]

    report = {
        "num_progress_rows": len(progress),
        "progress_status_counts": dict(Counter(r.get("status") for r in progress)),
        "num_failures": len(failures),
        "failure_error_counts": dict(Counter(r.get("error_code") for r in failures)),
        "avg_elapsed_sec": round(sum(elapsed) / max(1, len(elapsed)), 3),
        "total_elapsed_sec_recorded": round(sum(elapsed), 3),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
