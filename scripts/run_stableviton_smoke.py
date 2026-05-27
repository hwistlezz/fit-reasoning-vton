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
DEFAULT_DENOISE_STEPS = 50
DEFAULT_IMG_H = 512
DEFAULT_IMG_W = 384

PAIR_LIST_FILE = "test_pairs.txt"
REQUIRED_TEST_DIRS = [
    r"test\image",
    r"test\image-densepose",
    r"test\agnostic-v3.2",
    r"test\agnostic-mask",
    r"test\cloth",
    r"test\cloth-mask",
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
        "--denoise-steps",
        type=int,
        default=DEFAULT_DENOISE_STEPS,
        help=f"StableVITON denoise steps. Default: {DEFAULT_DENOISE_STEPS}",
    )
    parser.add_argument(
        "--img-H",
        dest="img_H",
        type=int,
        default=DEFAULT_IMG_H,
        help=f"Input image height passed to inference.py. Default: {DEFAULT_IMG_H}",
    )
    parser.add_argument(
        "--img-W",
        dest="img_W",
        type=int,
        default=DEFAULT_IMG_W,
        help=f"Input image width passed to inference.py. Default: {DEFAULT_IMG_W}",
    )
    parser.add_argument(
        "--unpair",
        action="store_true",
        help="Pass --unpair to StableVITON inference.py and use cloth names from test_pairs.txt column 2.",
    )
    parser.add_argument(
        "--repaint",
        action="store_true",
        help="Pass --repaint to StableVITON inference.py.",
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


def display_data_path(relative_path: str) -> str:
    return str(Path("DATA") / "zalando-hd-resized" / relative_path)


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


def format_one_line_command(command: Sequence[str]) -> str:
    return " ".join(quote_for_powershell(item) for item in command)


def format_multiline_powershell(command: Sequence[str]) -> str:
    if not command:
        return ""
    if len(command) == 1:
        return quote_for_powershell(command[0])

    lines = [f"{quote_for_powershell(command[0])} {quote_for_powershell(command[1])}"]
    index = 2
    while index < len(command):
        item = command[index]
        if item.startswith("--") and index + 1 < len(command) and not command[index + 1].startswith("--"):
            lines.append(f"  {quote_for_powershell(item)} {quote_for_powershell(command[index + 1])}")
            index += 2
        else:
            lines.append(f"  {quote_for_powershell(item)}")
            index += 1

    for line_index in range(len(lines) - 1):
        lines[line_index] = f"{lines[line_index]} `"
    return "\n".join(lines)


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


def list_immediate_files(path: Path) -> list[Path]:
    return sorted([child for child in path.iterdir() if child.is_file()], key=lambda item: item.name)


def sample_names(paths: list[Path], limit: int = 3) -> str:
    return ", ".join(path.name for path in paths[:limit])


def check_pair_list(data_root: Path) -> bool:
    pair_path = data_root / PAIR_LIST_FILE
    display_path = display_data_path(PAIR_LIST_FILE)
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


def check_test_dirs(data_root: Path, relative_dirs: Iterable[str]) -> bool:
    ready = True
    for relative_dir in relative_dirs:
        path = data_root / relative_dir
        display = display_data_path(relative_dir)
        if not path.is_dir():
            print_status("MISSING", display)
            ready = False
            continue

        files = list_immediate_files(path)
        if not files:
            print_status("EMPTY", display)
            ready = False
            continue

        print_status("OK", display, f"{len(files)} files; samples: {sample_names(files)}")
    return ready


def get_data_state(data_root_exists: bool, pair_ready: bool, test_dirs_ready: bool) -> str:
    if not data_root_exists:
        return "pending"
    if pair_ready and test_dirs_ready:
        return "ready"
    return "partial"


def build_command(args: argparse.Namespace) -> list[str]:
    command = [
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
        "--denoise_steps",
        str(args.denoise_steps),
        "--img_H",
        str(args.img_H),
        "--img_W",
        str(args.img_W),
    ]
    if args.unpair:
        command.append("--unpair")
    if args.repaint:
        command.append("--repaint")
    return command


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
    data_root_exists = check_directory(data_root, "data root")
    pair_ready = check_pair_list(data_root)
    test_dirs_ready = check_test_dirs(data_root, REQUIRED_TEST_DIRS)
    data_state = get_data_state(data_root_exists, pair_ready, test_dirs_ready)

    command = build_command(args)
    print()
    print("StableVITON smoke command:")
    print(format_one_line_command(command))
    print()
    print("PowerShell copy-paste command:")
    print(f"cd {quote_for_powershell(str(stableviton_root))}")
    print(format_multiline_powershell(command))
    print()
    print("Summary:")
    print(f"- required files: {'ready' if root_ready and inference_ready and config_ready and checkpoint_ready else 'missing'}")
    print(f"- data root: {data_state}")
    print(f"- mode: {'unpaired' if args.unpair else 'paired'}")

    required_ready = root_ready and inference_ready and config_ready and checkpoint_ready

    if not args.execute:
        if data_state == "ready":
            print("Dry-run only. Add --execute to run inference.")
        else:
            print(f"Dry-run only. Data root is {data_state}; add --execute only after test data is ready.")
        return 0 if required_ready else 1

    if not required_ready:
        print("Preflight failed. StableVITON inference was not executed.")
        return 1
    if data_state != "ready":
        print(f"Data root is {data_state}. StableVITON inference was not executed.")
        return 1

    print("Executing StableVITON inference...")
    completed = subprocess.run(command, cwd=stableviton_root, check=False)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
