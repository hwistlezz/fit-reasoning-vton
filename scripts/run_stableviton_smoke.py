import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_STABLEVITON_ROOT = r"D:\GitHub\StableVITON"
DEFAULT_CONFIG_PATH = r"configs\VITONHD.yaml"
DEFAULT_MODEL_LOAD_PATH = r"ckpts\VITONHD.ckpt"
DEFAULT_DATA_ROOT = r"DATA\zalando-hd-resized"
DEFAULT_SAVE_DIR = "samples_smoke"
DEFAULT_BATCH_SIZE = 1

REQUIRED_TEST_DIRS = [
    r"test\image",
    r"test\image-densepose",
    r"test\agnostic-v3.2",
    r"test\agnostic-mask",
    r"test\cloth",
    r"test\cloth_mask",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build and optionally run the StableVITON CLI smoke-test command."
    )
    parser.add_argument(
        "--stableviton-root",
        default=DEFAULT_STABLEVITON_ROOT,
        help=f"External StableVITON repo path. Default: {DEFAULT_STABLEVITON_ROOT}",
    )
    parser.add_argument(
        "--config-path",
        default=DEFAULT_CONFIG_PATH,
        help=f"Config path relative to StableVITON root. Default: {DEFAULT_CONFIG_PATH}",
    )
    parser.add_argument(
        "--model-load-path",
        default=DEFAULT_MODEL_LOAD_PATH,
        help=f"Checkpoint path relative to StableVITON root. Default: {DEFAULT_MODEL_LOAD_PATH}",
    )
    parser.add_argument(
        "--data-root",
        default=DEFAULT_DATA_ROOT,
        help=f"Data root path relative to StableVITON root. Default: {DEFAULT_DATA_ROOT}",
    )
    parser.add_argument(
        "--save-dir",
        default=DEFAULT_SAVE_DIR,
        help=f"Output directory relative to StableVITON root. Default: {DEFAULT_SAVE_DIR}",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Inference batch size. Default: {DEFAULT_BATCH_SIZE}",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run StableVITON inference. Without this flag, only print the command.",
    )
    return parser.parse_args()


def resolve_path(root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def cli_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    normalized = value.replace("/", "\\")
    if normalized.startswith(".\\"):
        return normalized
    return f".\\{normalized}"


def print_status(status: str, label: str, detail: str = "") -> None:
    if detail:
        print(f"[{status}] {label}: {detail}")
    else:
        print(f"[{status}] {label}")


def quote_for_powershell(value: str) -> str:
    if not value:
        return '""'
    if any(char.isspace() for char in value):
        return f'"{value}"'
    return value


def format_powershell_command(command: Sequence[str]) -> str:
    return " ".join(quote_for_powershell(item) for item in command)


def check_directory(path: Path, label: str) -> bool:
    if path.is_dir():
        print_status("OK", label, str(path))
        return True
    print_status("MISSING", label, str(path))
    return False


def check_file(path: Path, label: str) -> bool:
    if path.is_file():
        print_status("OK", label, str(path))
        return True
    print_status("MISSING", label, str(path))
    return False


def check_test_dirs(data_root: Path, relative_dirs: Iterable[str]) -> bool:
    ready = True
    for relative_dir in relative_dirs:
        path = data_root / relative_dir
        display = str(Path("DATA") / "zalando-hd-resized" / relative_dir)
        if path.is_dir():
            print_status("OK", display)
        else:
            print_status("MISSING", display)
            ready = False
    return ready


def build_command(args: argparse.Namespace) -> list[str]:
    return [
        sys.executable,
        "inference.py",
        "--config_path",
        cli_path(args.config_path),
        "--batch_size",
        str(args.batch_size),
        "--model_load_path",
        cli_path(args.model_load_path),
        "--data_root_dir",
        cli_path(args.data_root),
        "--save_dir",
        cli_path(args.save_dir),
    ]


def main() -> int:
    args = parse_args()
    stableviton_root = Path(args.stableviton_root).expanduser()
    inference_path = stableviton_root / "inference.py"
    config_path = resolve_path(stableviton_root, args.config_path)
    checkpoint_path = resolve_path(stableviton_root, args.model_load_path)
    data_root = resolve_path(stableviton_root, args.data_root)

    print("StableVITON smoke preflight:")
    root_ready = check_directory(stableviton_root, "StableVITON root")
    inference_ready = check_file(inference_path, "inference.py")
    config_ready = check_file(config_path, "config")
    checkpoint_ready = check_file(checkpoint_path, "checkpoint")
    data_root_ready = check_directory(data_root, "data root")
    test_dirs_ready = check_test_dirs(data_root, REQUIRED_TEST_DIRS)

    command = build_command(args)
    print()
    print("StableVITON smoke command:")
    print(format_powershell_command(command))
    print()

    required_ready = root_ready and inference_ready and config_ready and checkpoint_ready
    data_ready = data_root_ready and test_dirs_ready

    if not args.execute:
        if data_ready:
            print("Dry-run only. Add --execute to run inference.")
        else:
            print("Dry-run only. Data root is pending; add --execute only after test data is ready.")
        return 0 if required_ready else 1

    if not required_ready or not data_ready:
        print("Preflight failed. StableVITON inference was not executed.")
        return 1

    print("Executing StableVITON inference...")
    completed = subprocess.run(command, cwd=stableviton_root, check=False)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
