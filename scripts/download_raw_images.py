from __future__ import annotations

import csv
from pathlib import Path
from urllib.request import urlretrieve


CATEGORY_TO_DIR = {
    "demo_person": "raw/demo_person",
    "demo_cloth": "raw/demo_cloth",
    "preprocess_people": "raw/preprocess_people",
    "oversized_candidates": "raw/oversized_candidates",
    "low_confidence": "raw/low_confidence",
}


def guess_extension(url: str) -> str:
    suffix = Path(url.split("?")[0]).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return suffix
    return ".jpg"


def main() -> None:
    input_csv = Path("backend/datasets/urls/urls.csv")
    dataset_root = Path("backend/datasets")

    if not input_csv.exists():
        raise FileNotFoundError(
            "backend/datasets/urls/urls.csv not found. "
            "Create it locally from urls.example.csv. Do not commit urls.csv."
        )

    with input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            image_id = row["id"].strip()
            url = row["url"].strip()
            category = row["category"].strip()

            if category not in CATEGORY_TO_DIR:
                print(f"[SKIP] unsupported category: {category} ({image_id})")
                continue

            output_dir = dataset_root / CATEGORY_TO_DIR[category]
            output_dir.mkdir(parents=True, exist_ok=True)

            ext = guess_extension(url)
            output_path = output_dir / f"{image_id}{ext}"

            if output_path.exists():
                print(f"[SKIP] exists: {output_path}")
                continue

            print(f"[DOWNLOAD] {image_id} -> {output_path}")
            urlretrieve(url, output_path)

    print("Done. Check git status before committing.")


if __name__ == "__main__":
    main()