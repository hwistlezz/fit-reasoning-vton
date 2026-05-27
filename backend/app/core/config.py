from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Fit-aware VTON Backend"
    version: str = "0.1.0"
    api_prefix: str = "/api"
    output_dir: Path = REPO_ROOT / "backend" / "outputs"
    log_dir: Path = REPO_ROOT / "backend" / "logs"
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000"])


settings = Settings()
