import argparse
import sys
from pathlib import Path

import cv2
import numpy as np


DEFAULT_DATA_ROOT = r"D:\GitHub\StableVITON\DATA\stableviton-smoke"
DEFAULT_GRAY_VALUE = 128

# VITON-HD/LIP-style parsing labels commonly used by preprocessing tools:
# 0 background, 1 hat, 2 hair, 3 glove, 4 sunglasses, 5 upper-clothes,
# 6 dress, 7 coat, 8 socks, 9 pants, 10 jumpsuits, 11 scarf, 12 skirt,
# 13 face, 14 left-arm, 15 right-arm, 16 left-leg, 17 right-leg,
# 18 left-shoe, 19 right-shoe.
DEFAULT_REMOVE_LABELS = {5, 6, 7, 10}
ARM_LABELS = {14, 15}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate approximate StableVITON agnostic inputs from VITON-HD image-parse files. "
            "This is only for smoke tests, not benchmark-quality preprocessing."
        )
    )
    parser.add_argument(
        "--data-root",
        default=DEFAULT_DATA_ROOT,
        help=f"Local smoke dataset root. Default: {DEFAULT_DATA_ROOT}",
    )
    parser.add_argument(
        "--include-arms",
        action="store_true",
        help="Also include LIP arm labels 14 and 15 in the removal mask.",
    )
    parser.add_argument(
        "--extra-label",
        action="append",
        type=int,
        default=[],
        help="Additional parsing label to include in the removal mask. Can be repeated.",
    )
    parser.add_argument(
        "--gray-value",
        type=int,
        default=DEFAULT_GRAY_VALUE,
        help=f"RGB/BGR value used to fill removed areas. Default: {DEFAULT_GRAY_VALUE}",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_data_root_outside_repo(data_root: Path) -> None:
    repo = repo_root().resolve()
    target = data_root.resolve()
    if target == repo or target.is_relative_to(repo):
        raise ValueError(f"Refusing to write generated data inside repository: {target}")


def print_status(status: str, label: str, detail: str = "") -> None:
    if detail:
        print(f"[{status}] {label}: {detail}")
    else:
        print(f"[{status}] {label}")


def read_pairs(data_root: Path) -> list[tuple[str, str]]:
    pair_path = data_root / "test_pairs.txt"
    if not pair_path.is_file():
        raise FileNotFoundError(f"Missing pair list: {pair_path}")

    pairs: list[tuple[str, str]] = []
    with pair_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) != 2:
                raise ValueError(f"Invalid pair line {line_number}: {stripped}")
            pairs.append((parts[0], parts[1]))

    if not pairs:
        raise ValueError(f"No pairs found in {pair_path}")
    return pairs


def find_parse_file(parse_dir: Path, person_name: str) -> Path | None:
    base = Path(person_name).stem
    candidates = [
        parse_dir / f"{base}.png",
        parse_dir / f"{base}.jpg",
        parse_dir / person_name,
    ]
    candidates.extend(sorted(parse_dir.glob(f"{base}.*")))
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            return candidate
    return None


def mask_filename(person_name: str) -> str:
    path = Path(person_name)
    if path.suffix.lower() == ".jpg":
        return person_name.replace(".jpg", "_mask.png")
    return f"{path.stem}_mask.png"


def build_remove_mask(parse_image: np.ndarray, labels: set[int]) -> np.ndarray:
    return np.isin(parse_image, list(labels)).astype(np.uint8) * 255


def generate_for_person(data_root: Path, person_name: str, labels: set[int], gray_value: int) -> bool:
    image_path = data_root / "test" / "image" / person_name
    parse_path = find_parse_file(data_root / "test" / "image-parse", person_name)
    if not image_path.is_file():
        print_status("WARN", "missing image", str(image_path))
        return False
    if parse_path is None:
        print_status("WARN", "missing image-parse", person_name)
        return False

    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    parse = cv2.imread(str(parse_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        print_status("WARN", "failed to read image", str(image_path))
        return False
    if parse is None:
        print_status("WARN", "failed to read image-parse", str(parse_path))
        return False

    height, width = image.shape[:2]
    if parse.shape[:2] != (height, width):
        parse = cv2.resize(parse, (width, height), interpolation=cv2.INTER_NEAREST)

    mask = build_remove_mask(parse, labels)
    agnostic = image.copy()
    agnostic[mask > 0] = (gray_value, gray_value, gray_value)

    agnostic_dir = data_root / "test" / "agnostic-v3.2"
    mask_dir = data_root / "test" / "agnostic-mask"
    agnostic_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)

    agnostic_path = agnostic_dir / person_name
    mask_path = mask_dir / mask_filename(person_name)
    ok_agnostic = cv2.imwrite(str(agnostic_path), agnostic)
    ok_mask = cv2.imwrite(str(mask_path), mask)
    if not ok_agnostic or not ok_mask:
        print_status("WARN", "failed to write agnostic outputs", person_name)
        return False

    print_status("OK", "generated agnostic", f"{agnostic_path.name}, {mask_path.name}")
    return True


def main() -> int:
    args = parse_args()
    data_root = Path(args.data_root).expanduser()
    gray_value = max(0, min(255, args.gray_value))
    labels = set(DEFAULT_REMOVE_LABELS)
    labels.update(args.extra_label)
    if args.include_arms:
        labels.update(ARM_LABELS)

    try:
        ensure_data_root_outside_repo(data_root)
        pairs = read_pairs(data_root)
    except Exception as exc:  # noqa: BLE001 - CLI should report concrete setup issues.
        print(f"[ERROR] {exc}")
        return 1

    print("Approximate agnostic generation for smoke tests only.")
    print(f"Removal labels: {sorted(labels)}")

    generated = 0
    warnings = 0
    seen_people: set[str] = set()
    for person_name, _cloth_name in pairs:
        if person_name in seen_people:
            continue
        seen_people.add(person_name)
        if generate_for_person(data_root, person_name, labels, gray_value):
            generated += 1
        else:
            warnings += 1

    print()
    print("Summary:")
    print(f"- pairs: {len(pairs)}")
    print(f"- people processed: {len(seen_people)}")
    print(f"- generated: {generated}")
    print(f"- warnings: {warnings}")
    print(f"- data root: {data_root}")
    return 0 if generated > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
