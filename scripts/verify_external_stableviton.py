import argparse
import importlib
import sys
from pathlib import Path
from typing import Dict, Iterable, Tuple


DEFAULT_STABLEVITON_ROOT = r"D:\GitHub\StableVITON"
DEFAULT_DATA_ROOT = r"D:\GitHub\StableVITON\DATA\zalando-hd-resized"

REQUIRED_REPO_FILES = [
    ("inference.py", "inference.py"),
    ("configs/VITONHD.yaml", "configs/VITONHD.yaml"),
]

CHECKPOINT_FILES = [
    "VITONHD.ckpt",
    "VITONHD_PBE_pose.ckpt",
    "VITONHD_VAE_finetuning.ckpt",
]

DATA_TEST_DIRS = [
    "test/image",
    "test/image-densepose",
    "test/agnostic-v3.2",
    "test/agnostic-mask",
    "test/cloth",
    "test/cloth-mask",
]

PAIR_LIST_FILE = "test_pairs.txt"

OPTIONAL_IMPORTS = [
    ("torch", "torch"),
    ("pytorch_lightning", "pytorch_lightning"),
    ("cv2", "cv2"),
    ("numpy", "numpy"),
    ("albumentations", "albumentations"),
    ("diffusers", "diffusers"),
    ("transformers", "transformers"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify an external StableVITON repo without running inference."
    )
    parser.add_argument(
        "--stableviton-root",
        default=DEFAULT_STABLEVITON_ROOT,
        help=f"External StableVITON repo path. Default: {DEFAULT_STABLEVITON_ROOT}",
    )
    parser.add_argument(
        "--data-root",
        default=DEFAULT_DATA_ROOT,
        help=f"VITON-HD data root path. Default: {DEFAULT_DATA_ROOT}",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Also import torch/cv2/diffusers and related packages.",
    )
    return parser.parse_args()


def print_status(status: str, label: str, detail: str = "") -> None:
    if detail:
        print(f"[{status}] {label}: {detail}")
    else:
        print(f"[{status}] {label}")


def file_size_text(path: Path) -> str:
    size = path.stat().st_size
    if size >= 1024**3:
        return f"{size / 1024**3:.2f} GB"
    if size >= 1024**2:
        return f"{size / 1024**2:.2f} MB"
    if size >= 1024:
        return f"{size / 1024:.2f} KB"
    return f"{size} B"


def check_required_repo(root: Path) -> Tuple[bool, Dict[str, bool]]:
    result = {"root": False, "inference": False, "config": False}

    if root.is_dir():
        print_status("OK", "StableVITON root", str(root))
        result["root"] = True
    else:
        print_status("MISSING", "StableVITON root", str(root))
        return False, result

    for key, relative_path in REQUIRED_REPO_FILES:
        path = root / relative_path
        if path.is_file():
            print_status("OK", relative_path)
            if key == "inference.py":
                result["inference"] = True
            elif key == "configs/VITONHD.yaml":
                result["config"] = True
        else:
            print_status("MISSING", relative_path)

    repo_ready = result["root"] and result["inference"] and result["config"]
    return repo_ready, result


def check_checkpoints(root: Path) -> bool:
    ckpt_dir = root / "ckpts"
    all_ready = True

    if ckpt_dir.is_dir():
        print_status("OK", "ckpts directory")
    else:
        print_status("MISSING", "ckpts directory")
        all_ready = False

    for filename in CHECKPOINT_FILES:
        path = ckpt_dir / filename
        display_path = f"ckpts/{filename}"
        if path.is_file() and path.stat().st_size > 0:
            print_status("OK", display_path, file_size_text(path))
        else:
            print_status("MISSING", display_path)
            all_ready = False

    return all_ready


def display_data_path(data_root: Path, relative_path: str) -> str:
    return str(Path("DATA") / data_root.name / relative_path)


def sample_names(paths: list[Path], limit: int = 3) -> str:
    return ", ".join(path.name for path in paths[:limit])


def list_immediate_files(path: Path) -> list[Path]:
    return sorted([child for child in path.iterdir() if child.is_file()], key=lambda item: item.name)


def check_pair_list(data_root: Path) -> bool:
    pair_path = data_root / PAIR_LIST_FILE
    display_path = display_data_path(data_root, PAIR_LIST_FILE)
    if not pair_path.is_file():
        print_status("MISSING", display_path)
        return False

    lines = [line.strip() for line in pair_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        print_status("EMPTY", display_path)
        return False

    invalid_lines = [line for line in lines if len(line.split()) != 2]
    if invalid_lines:
        print_status("INVALID", display_path, f"{len(invalid_lines)} invalid lines")
        return False

    samples = [f"{parts[0]} -> {parts[1]}" for parts in (line.split() for line in lines[:3])]
    print_status("OK", display_path, f"{len(lines)} pairs; samples: {', '.join(samples)}")
    return True


def check_data_dir(data_root: Path, relative_path: str) -> bool:
    path = data_root / relative_path
    display_path = display_data_path(data_root, relative_path)
    if not path.is_dir():
        print_status("MISSING", display_path)
        return False

    files = list_immediate_files(path)
    if not files:
        print_status("EMPTY", display_path)
        return False

    print_status("OK", display_path, f"{len(files)} files; samples: {sample_names(files)}")
    return True


def check_data_root(data_root: Path) -> str:
    data_root_exists = data_root.is_dir()

    if data_root_exists:
        print_status("OK", "data root", str(data_root))
    else:
        print_status("MISSING", "data root", str(data_root))

    pair_ready = check_pair_list(data_root)
    dirs_ready = True
    for relative_path in DATA_TEST_DIRS:
        dirs_ready = check_data_dir(data_root, relative_path) and dirs_ready

    if not data_root_exists:
        return "pending"
    if pair_ready and dirs_ready:
        return "ready"
    return "partial"


def get_version(module: object) -> str:
    return str(getattr(module, "__version__", "version unknown"))


def check_imports(imports: Iterable[Tuple[str, str]]) -> bool:
    all_ready = True
    for label, module_name in imports:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - import smoke test should show the concrete failure.
            print_status("MISSING", f"import {label}", f"{type(exc).__name__}: {exc}")
            all_ready = False
            continue
        print_status("OK", f"import {label}", get_version(module))
    return all_ready


def print_summary(repo_ready: bool, checkpoints_ready: bool, data_state: str, imports_ready: bool | None) -> None:
    print()
    print("Summary:")
    print(f"- external repo: {'ready' if repo_ready else 'missing'}")
    print(f"- checkpoints: {'ready' if checkpoints_ready else 'pending'}")
    print(f"- data root: {data_state}")
    if imports_ready is not None:
        print(f"- imports: {'ready' if imports_ready else 'failed'}")


def main() -> int:
    args = parse_args()
    stableviton_root = Path(args.stableviton_root).expanduser()
    data_root = Path(args.data_root).expanduser()

    repo_ready, required_result = check_required_repo(stableviton_root)
    checkpoints_ready = check_checkpoints(stableviton_root)
    data_state = check_data_root(data_root)

    imports_ready = None
    if args.check_imports:
        imports_ready = check_imports(OPTIONAL_IMPORTS)

    print_summary(repo_ready, checkpoints_ready, data_state, imports_ready)

    if not required_result["root"] or not required_result["inference"] or not required_result["config"]:
        return 1
    if imports_ready is False:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
