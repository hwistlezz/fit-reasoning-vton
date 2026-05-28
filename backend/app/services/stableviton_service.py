import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from backend.app.core.config import settings


REQUIRED_CHECKPOINTS = (
    r"ckpts\VITONHD_PBE_pose.ckpt",
    r"ckpts\VITONHD_VAE_finetuning.ckpt",
)
REQUIRED_DATA_DIRS = (
    r"test\image",
    r"test\image-densepose",
    r"test\agnostic-v3.2",
    r"test\agnostic-mask",
    r"test\cloth",
    r"test\cloth-mask",
)
RESULT_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class StableVitonRunResult:
    result_path: Path
    source_image_path: Path
    command: list[str]


class StableVitonServiceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _stableviton_root() -> Path:
    return settings.stableviton_root.expanduser()


def _resolve_stableviton_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return _stableviton_root() / path


def _cli_path(value: str | Path) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    normalized = str(path).replace("/", "\\")
    if normalized.startswith(".\\"):
        return normalized
    return f".\\{normalized}"


def _output_root(job_id: str | None = None) -> Path:
    output_root = _resolve_stableviton_path(settings.stableviton_output_dir)
    if job_id:
        return output_root / job_id
    return output_root


def _output_mode_dir(output_root: Path) -> Path:
    mode = "unpair" if settings.stableviton_use_unpair else "pair"
    return output_root / mode


def _required_checkpoint_paths() -> list[Path]:
    checkpoint_values = [settings.stableviton_model_load_path, *REQUIRED_CHECKPOINTS]
    unique_values = list(dict.fromkeys(checkpoint_values))
    return [_resolve_stableviton_path(value) for value in unique_values]


def _format_command(command: Sequence[str]) -> str:
    return " ".join(f'"{item}"' if " " in item else item for item in command)


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def write_stableviton_logs(job_dir: Path, stdout: str | bytes | None, stderr: str | bytes | None) -> None:
    (job_dir / "stableviton_stdout.log").write_text(_as_text(stdout), encoding="utf-8")
    (job_dir / "stableviton_stderr.log").write_text(_as_text(stderr), encoding="utf-8")


def preflight_stableviton() -> None:
    stableviton_root = _stableviton_root()
    if not stableviton_root.is_dir():
        raise StableVitonServiceError(
            "STABLEVITON_ROOT_NOT_FOUND",
            f"StableVITON root was not found: {stableviton_root}",
        )

    if not settings.stableviton_python.is_file():
        raise StableVitonServiceError(
            "STABLEVITON_PYTHON_NOT_FOUND",
            f"StableVITON Python executable was not found: {settings.stableviton_python}",
        )

    inference_path = stableviton_root / "inference.py"
    if not inference_path.is_file():
        raise StableVitonServiceError(
            "STABLEVITON_INFERENCE_SCRIPT_NOT_FOUND",
            f"StableVITON inference.py was not found: {inference_path}",
        )

    config_path = _resolve_stableviton_path(settings.stableviton_config_path)
    if not config_path.is_file():
        raise StableVitonServiceError(
            "STABLEVITON_CONFIG_NOT_FOUND",
            f"StableVITON config file was not found: {config_path}",
        )

    missing_checkpoints = [path for path in _required_checkpoint_paths() if not path.is_file()]
    if missing_checkpoints:
        missing = ", ".join(str(path) for path in missing_checkpoints)
        raise StableVitonServiceError(
            "STABLEVITON_CHECKPOINT_MISSING",
            f"Required StableVITON checkpoint file(s) were not found: {missing}",
        )

    data_root = _resolve_stableviton_path(settings.stableviton_data_root)
    if not data_root.is_dir():
        raise StableVitonServiceError(
            "STABLEVITON_DATA_ROOT_NOT_FOUND",
            f"StableVITON data root was not found: {data_root}",
        )

    pair_list = data_root / "test_pairs.txt"
    missing_data = [str(pair_list)] if not pair_list.is_file() else []
    if pair_list.is_file():
        pair_lines = [line.strip() for line in pair_list.read_text(encoding="utf-8").splitlines() if line.strip()]
        invalid_lines = [line for line in pair_lines if len(line.split()) != 2]
        if not pair_lines:
            missing_data.append(f"{pair_list} is empty")
        if invalid_lines:
            missing_data.append(f"{pair_list} has invalid pair lines")

    for relative_dir in REQUIRED_DATA_DIRS:
        input_dir = data_root / relative_dir
        if not input_dir.is_dir():
            missing_data.append(str(input_dir))
            continue
        if not any(child.is_file() for child in input_dir.iterdir()):
            missing_data.append(f"{input_dir} is empty")

    if missing_data:
        raise StableVitonServiceError(
            "STABLEVITON_DATA_ROOT_NOT_FOUND",
            "StableVITON smoke data is incomplete: " + ", ".join(missing_data),
        )


def build_stableviton_command(output_dir: str | Path | None = None) -> list[str]:
    save_dir = output_dir or settings.stableviton_output_dir
    command = [
        str(settings.stableviton_python),
        "inference.py",
        "--config_path",
        _cli_path(settings.stableviton_config_path),
        "--batch_size",
        str(settings.stableviton_batch_size),
        "--model_load_path",
        _cli_path(settings.stableviton_model_load_path),
        "--data_root_dir",
        _cli_path(settings.stableviton_data_root),
        "--save_dir",
        _cli_path(save_dir),
        "--denoise_steps",
        str(settings.stableviton_denoise_steps),
        "--img_H",
        str(settings.stableviton_img_height),
        "--img_W",
        str(settings.stableviton_img_width),
    ]
    if settings.stableviton_use_unpair:
        command.append("--unpair")
    return command


def _find_latest_result_image(output_root: Path, start_time: float) -> Path | None:
    mode_dir = _output_mode_dir(output_root)
    if not mode_dir.is_dir():
        return None

    candidates = [
        path
        for path in mode_dir.iterdir()
        if path.is_file() and path.suffix.lower() in RESULT_EXTENSIONS
    ]
    fresh_candidates = [path for path in candidates if path.stat().st_mtime >= start_time - 5]
    if not fresh_candidates:
        return None
    return max(fresh_candidates, key=lambda path: path.stat().st_mtime)


def _copy_result_image_as_png(source_path: Path, target_path: Path) -> None:
    try:
        from PIL import Image

        with Image.open(source_path) as image:
            image.save(target_path, format="PNG")
    except Exception as exc:  # noqa: BLE001 - preserve a clear API-facing error code.
        raise StableVitonServiceError(
            "STABLEVITON_RESULT_COPY_FAILED",
            f"Failed to copy StableVITON result image to result.png: {exc}",
        ) from exc


def run_stableviton_inference(job_id: str, job_dir: Path) -> StableVitonRunResult:
    preflight_stableviton()

    output_root = _output_root(job_id)
    output_root.mkdir(parents=True, exist_ok=True)
    command = build_stableviton_command(output_root)
    command_header = (
        f"job_id: {job_id}\n"
        f"cwd: {_stableviton_root()}\n"
        f"command: {_format_command(command)}\n\n"
    )
    start_time = time.time()

    try:
        completed = subprocess.run(
            command,
            cwd=_stableviton_root(),
            capture_output=True,
            text=True,
            timeout=settings.stableviton_timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        write_stableviton_logs(
            job_dir,
            command_header + _as_text(exc.stdout),
            _as_text(exc.stderr) + f"\nStableVITON timed out after {settings.stableviton_timeout_seconds} seconds.\n",
        )
        raise StableVitonServiceError(
            "STABLEVITON_TIMEOUT",
            f"StableVITON inference timed out after {settings.stableviton_timeout_seconds} seconds.",
        ) from exc

    write_stableviton_logs(
        job_dir,
        command_header + completed.stdout,
        completed.stderr,
    )

    if completed.returncode != 0:
        raise StableVitonServiceError(
            "STABLEVITON_INFERENCE_FAILED",
            "StableVITON inference failed. Check logs for details.",
        )

    source_image_path = _find_latest_result_image(output_root, start_time)
    if source_image_path is None:
        raise StableVitonServiceError(
            "STABLEVITON_RESULT_NOT_FOUND",
            f"StableVITON result image was not found under {_output_mode_dir(output_root)}.",
        )

    result_path = job_dir / "result.png"
    _copy_result_image_as_png(source_image_path, result_path)
    return StableVitonRunResult(result_path=result_path, source_image_path=source_image_path, command=command)
