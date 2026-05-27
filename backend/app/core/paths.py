from pathlib import Path

from backend.app.core.config import settings


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_output_dir() -> Path:
    return ensure_directory(settings.output_dir)


def ensure_log_dir() -> Path:
    return ensure_directory(settings.log_dir)


def ensure_runtime_dirs() -> None:
    ensure_output_dir()
    ensure_log_dir()
