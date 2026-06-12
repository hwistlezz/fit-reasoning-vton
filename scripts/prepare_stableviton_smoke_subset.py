import argparse
import sys
from pathlib import Path

from stableviton_orientation import copy_without_exif


DEFAULT_SOURCE_ROOT = r"D:\GitHub\StableVITON\DATA\zalando-hd-resized"
DEFAULT_TARGET_ROOT = r"D:\GitHub\StableVITON\DATA\stableviton-smoke"
DEFAULT_NUM_SAMPLES = 3

PERSON_DIRS = [
    "image",
    "image-parse",
    "openpose-img",
    "openpose-json",
]
CLOTH_DIRS = [
    "cloth",
    "cloth-mask",
]
STABLEVITON_EXTRA_DIRS = [
    "image-densepose",
    "agnostic-v3.2",
    "agnostic-mask",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare a tiny local VITON-HD subset for StableVITON smoke tests."
    )
    parser.add_argument(
        "--source-root",
        default=DEFAULT_SOURCE_ROOT,
        help=f"Source VITON-HD data root. Default: {DEFAULT_SOURCE_ROOT}",
    )
    parser.add_argument(
        "--target-root",
        default=DEFAULT_TARGET_ROOT,
        help=f"Target local smoke dataset root. Default: {DEFAULT_TARGET_ROOT}",
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=DEFAULT_NUM_SAMPLES,
        help=f"Number of pair lines to copy. Default: {DEFAULT_NUM_SAMPLES}",
    )
    return parser.parse_args()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def ensure_target_outside_repo(target_root: Path) -> None:
    repo = repo_root().resolve()
    target = target_root.resolve()
    if target == repo or target.is_relative_to(repo):
        raise ValueError(f"Refusing to write dataset files inside repository: {target}")


def print_status(status: str, label: str, detail: str = "") -> None:
    if detail:
        print(f"[{status}] {label}: {detail}")
    else:
        print(f"[{status}] {label}")


def read_pairs(source_root: Path, num_samples: int) -> list[tuple[str, str]]:
    pair_path = source_root / "test_pairs.txt"
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
            if len(pairs) >= num_samples:
                break

    if not pairs:
        raise ValueError(f"No pairs found in {pair_path}")
    return pairs


def candidate_files(directory: Path, filename: str, variants: list[str]) -> list[Path]:
    base = Path(filename).stem
    suffix = Path(filename).suffix
    candidates = [directory / filename]
    for variant in variants:
        candidates.append(directory / variant.format(base=base, suffix=suffix, filename=filename))
    candidates.extend(sorted(directory.glob(f"{base}.*")))
    return candidates


def find_first_existing(directory: Path, filename: str, variants: list[str]) -> Path | None:
    seen: set[Path] = set()
    for candidate in candidate_files(directory, filename, variants):
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            return candidate
    return None


def copy_file(source: Path, target: Path, label: str) -> bool:
    if not source.is_file():
        print_status("WARN", f"missing {label}", str(source))
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    copy_without_exif(source, target, label)
    print_status("OK", f"copied {label}", target.name)
    return True


def prepare_target_dirs(target_root: Path) -> None:
    for directory in PERSON_DIRS + CLOTH_DIRS + STABLEVITON_EXTRA_DIRS:
        (target_root / "test" / directory).mkdir(parents=True, exist_ok=True)


def copy_person_files(source_root: Path, target_root: Path, person_name: str) -> tuple[int, int]:
    copied = 0
    warnings = 0
    specs = [
        (
            "image",
            person_name,
            [],
            "image",
            person_name,
        ),
        (
            "image-parse",
            person_name,
            ["{base}.png", "{base}.jpg"],
            "image-parse",
            None,
        ),
        (
            "openpose-img",
            person_name,
            ["{base}_rendered.png", "{base}.png", "{base}.jpg"],
            "openpose-img",
            None,
        ),
        (
            "openpose-json",
            person_name,
            ["{base}_keypoints.json", "{base}.json"],
            "openpose-json",
            None,
        ),
    ]
    for source_dir, lookup_name, variants, target_dir, canonical_name in specs:
        directory = source_root / "test" / source_dir
        source = find_first_existing(directory, lookup_name, variants)
        if source is None:
            print_status("WARN", f"missing {source_dir}", str(directory / lookup_name))
            warnings += 1
            continue
        target_name = canonical_name or source.name
        copied += int(copy_file(source, target_root / "test" / target_dir / target_name, source_dir))
    return copied, warnings


def copy_cloth_files(source_root: Path, target_root: Path, cloth_name: str) -> tuple[int, int]:
    copied = 0
    warnings = 0
    specs = [
        ("cloth", cloth_name, [], "cloth", cloth_name),
        ("cloth-mask", cloth_name, ["{base}.png", "{base}.jpg"], "cloth-mask", cloth_name),
    ]
    for source_dir, lookup_name, variants, target_dir, canonical_name in specs:
        directory = source_root / "test" / source_dir
        source = find_first_existing(directory, lookup_name, variants)
        if source is None:
            print_status("WARN", f"missing {source_dir}", str(directory / lookup_name))
            warnings += 1
            continue
        copied += int(copy_file(source, target_root / "test" / target_dir / canonical_name, source_dir))
    return copied, warnings


def write_pair_list(target_root: Path, pairs: list[tuple[str, str]]) -> None:
    pair_path = target_root / "test_pairs.txt"
    pair_path.parent.mkdir(parents=True, exist_ok=True)
    pair_path.write_text("".join(f"{person} {cloth}\n" for person, cloth in pairs), encoding="utf-8")
    print_status("OK", "wrote test_pairs.txt", f"{len(pairs)} pairs")


def main() -> int:
    args = parse_args()
    if args.num_samples < 1:
        print("[ERROR] --num-samples must be at least 1")
        return 1

    source_root = Path(args.source_root).expanduser()
    target_root = Path(args.target_root).expanduser()

    try:
        ensure_target_outside_repo(target_root)
        pairs = read_pairs(source_root, args.num_samples)
    except Exception as exc:  # noqa: BLE001 - CLI should report concrete setup issues.
        print(f"[ERROR] {exc}")
        return 1

    prepare_target_dirs(target_root)
    write_pair_list(target_root, pairs)

    copied = 0
    warnings = 0
    unpaired_count = 0
    for person_name, cloth_name in pairs:
        if person_name != cloth_name:
            unpaired_count += 1
        person_copied, person_warnings = copy_person_files(source_root, target_root, person_name)
        cloth_copied, cloth_warnings = copy_cloth_files(source_root, target_root, cloth_name)
        copied += person_copied + cloth_copied
        warnings += person_warnings + cloth_warnings

    if unpaired_count:
        print_status(
            "WARN",
            "unpaired pair lines",
            "Use run_stableviton_smoke.py --unpair so StableVITON uses cloth filenames from column 2.",
        )

    print()
    print("Summary:")
    print(f"- pairs: {len(pairs)}")
    print(f"- copied: {copied}")
    print(f"- warnings: {warnings + int(bool(unpaired_count))}")
    print(f"- target root: {target_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
