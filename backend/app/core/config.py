from dataclasses import dataclass, field
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _env_path(name: str, default: str | Path) -> Path:
    return Path(os.getenv(name, str(default))).expanduser()


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "Fit-aware VTON Backend"
    version: str = "0.1.0"
    api_prefix: str = "/api"
    output_dir: Path = REPO_ROOT / "backend" / "outputs"
    log_dir: Path = REPO_ROOT / "backend" / "logs"
    stableviton_root: Path = field(
        default_factory=lambda: _env_path("STABLEVITON_ROOT", r"D:\GitHub\StableVITON")
    )
    stableviton_python: Path = field(
        default_factory=lambda: _env_path("STABLEVITON_PYTHON", r"D:\conda-envs\vton\python.exe")
    )
    stableviton_config_path: str = field(
        default_factory=lambda: os.getenv("STABLEVITON_CONFIG_PATH", r"configs\VITONHD.yaml")
    )
    stableviton_model_load_path: str = field(
        default_factory=lambda: os.getenv("STABLEVITON_MODEL_LOAD_PATH", r"ckpts\VITONHD.ckpt")
    )
    stableviton_data_root: str = field(
        default_factory=lambda: os.getenv("STABLEVITON_DATA_ROOT", r"DATA\stableviton-smoke")
    )
    stableviton_output_dir: str = field(
        default_factory=lambda: os.getenv(
            "STABLEVITON_OUTPUT_DIR",
            str(REPO_ROOT / "backend" / "outputs" / "stableviton_raw"),
        )
    )
    stableviton_timeout_seconds: int = field(
        default_factory=lambda: _env_int("STABLEVITON_TIMEOUT_SECONDS", 300)
    )
    stableviton_use_unpair: bool = field(
        default_factory=lambda: _env_bool("STABLEVITON_USE_UNPAIR", True)
    )
    stableviton_batch_size: int = field(default_factory=lambda: _env_int("STABLEVITON_BATCH_SIZE", 1))
    stableviton_denoise_steps: int = field(default_factory=lambda: _env_int("STABLEVITON_DENOISE_STEPS", 50))
    stableviton_img_height: int = field(default_factory=lambda: _env_int("STABLEVITON_IMG_H", 512))
    stableviton_img_width: int = field(default_factory=lambda: _env_int("STABLEVITON_IMG_W", 384))
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000"])


settings = Settings()
