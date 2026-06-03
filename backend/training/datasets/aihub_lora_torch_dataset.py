from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torch.utils.data import Dataset

from backend.training.datasets.aihub_lora_dataset import AihubLoraPilotDataset


if hasattr(Image, "Resampling"):
    RESAMPLE_BILINEAR = Image.Resampling.BILINEAR
else:
    RESAMPLE_BILINEAR = Image.BILINEAR


class AihubLoraTorchDataset(Dataset):
    """PyTorch Dataset adapter for the PC3 AIHub LoRA dry-run workflow."""

    def __init__(
        self,
        data_root: str | Path,
        *,
        image_height: int = 512,
        image_width: int = 384,
        manifest_name: str = "manifest.jsonl",
    ) -> None:
        if image_height <= 0:
            raise ValueError("image_height must be positive.")
        if image_width <= 0:
            raise ValueError("image_width must be positive.")

        self.base_dataset = AihubLoraPilotDataset(data_root, manifest_name=manifest_name)
        self.image_height = image_height
        self.image_width = image_width

    def __len__(self) -> int:
        return len(self.base_dataset)

    def __getitem__(self, index: int) -> dict[str, Any]:
        sample = self.base_dataset[index]
        pair_id = sample["pair_id"]

        return {
            "pair_id": pair_id,
            "person": self._load_image_tensor(sample["image_path"], pair_id, "person"),
            "cloth": self._load_image_tensor(sample["cloth_path"], pair_id, "cloth"),
            "target": self._load_image_tensor(sample["worn_path"], pair_id, "target"),
            "fit_label": str(sample.get("fit_label") or ""),
            "confidence": self._require_float(sample.get("confidence"), pair_id),
            "prompt": str(sample.get("prompt") or ""),
        }

    def _load_image_tensor(self, path: Path, pair_id: str, field_name: str) -> torch.Tensor:
        try:
            with Image.open(path) as image:
                image = image.convert("RGB")
                image = image.resize((self.image_width, self.image_height), RESAMPLE_BILINEAR)
                buffer = bytearray(image.tobytes())
        except OSError as exc:
            raise RuntimeError(
                f"failed to load {field_name} image for pair_id={pair_id}: {path}"
            ) from exc

        tensor = torch.frombuffer(buffer, dtype=torch.uint8)
        tensor = tensor.reshape(self.image_height, self.image_width, 3)
        tensor = tensor.permute(2, 0, 1).contiguous()
        return tensor.float().div(255.0)

    @staticmethod
    def _require_float(value: Any, pair_id: str) -> float:
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid confidence for pair_id={pair_id}: {value!r}") from exc
