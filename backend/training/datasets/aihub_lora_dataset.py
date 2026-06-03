from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image


ARTIFACT_PATH_PATTERNS: dict[str, tuple[str, ...]] = {
    "openpose-json": (
        "openpose-json/{pair_id}_keypoints.json",
        "openpose-json/{pair_id}.json",
    ),
    "image-parse": ("image-parse/{pair_id}.png",),
    "cloth-mask": ("cloth-mask/{pair_id}.png",),
    "agnostic-v3.2": (
        "agnostic-v3.2/{pair_id}.png",
        "agnostic-v3.2/{pair_id}.jpg",
    ),
    "agnostic-mask": ("agnostic-mask/{pair_id}.png",),
    "image-densepose": (
        "image-densepose/{pair_id}.jpg",
        "image-densepose/{pair_id}.png",
    ),
}


class AihubLoraPilotDataset:
    """Torch-free loader for the PC2 AIHub LoRA pilot dataset."""

    def __init__(self, data_root: str | Path, manifest_name: str = "manifest.jsonl") -> None:
        self.data_root = Path(data_root)
        self.manifest_path = self.data_root / manifest_name
        self._rows = self._read_manifest(self.manifest_path)

    def __len__(self) -> int:
        return len(self._rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self._rows[index]
        pair_id = self._require_pair_id(row, index)
        paths = self.get_paths(index)

        return {
            "pair_id": pair_id,
            "split": row.get("split"),
            "image_path": paths["image_path"],
            "cloth_path": paths["cloth_path"],
            "worn_path": paths["worn_path"],
            "fit_json_path": paths["fit_json_path"],
            "fit_label": row.get("fit_label"),
            "confidence": row.get("confidence"),
            "prompt": row.get("prompt"),
            "manifest_row": row,
        }

    def get_paths(self, index: int) -> dict[str, Path]:
        row = self._rows[index]
        pair_id = self._require_pair_id(row, index)

        return {
            "image_path": self.data_root / "image" / f"{pair_id}.jpg",
            "cloth_path": self.data_root / "cloth" / f"{pair_id}.jpg",
            "worn_path": self.data_root / "worn" / f"{pair_id}.jpg",
            "fit_json_path": self.data_root / "fit" / f"{pair_id}.json",
        }

    def get_artifact_paths(self, index: int) -> dict[str, Path]:
        row = self._rows[index]
        pair_id = self._require_pair_id(row, index)

        return {
            artifact_name: self._resolve_artifact_path(pair_id, patterns)
            for artifact_name, patterns in ARTIFACT_PATH_PATTERNS.items()
        }

    def get_artifact_candidates(self, index: int) -> dict[str, tuple[Path, ...]]:
        row = self._rows[index]
        pair_id = self._require_pair_id(row, index)

        return {
            artifact_name: tuple(self.data_root / pattern.format(pair_id=pair_id) for pattern in patterns)
            for artifact_name, patterns in ARTIFACT_PATH_PATTERNS.items()
        }

    def load_sample(self, index: int) -> dict[str, Any]:
        sample = self[index]
        return {
            **sample,
            "image": self._load_rgb(sample["image_path"]),
            "cloth": self._load_rgb(sample["cloth_path"]),
            "worn": self._load_rgb(sample["worn_path"]),
            "fit_json": self._load_fit_json(sample["fit_json_path"]),
        }

    @staticmethod
    def _read_manifest(manifest_path: Path) -> list[dict[str, Any]]:
        if not manifest_path.is_file():
            raise FileNotFoundError(f"manifest not found: {manifest_path}")

        rows: list[dict[str, Any]] = []
        with manifest_path.open("r", encoding="utf-8") as manifest_file:
            for line_number, line in enumerate(manifest_file, start=1):
                stripped = line.strip()
                if not stripped:
                    continue

                payload = json.loads(stripped)
                if not isinstance(payload, dict):
                    raise ValueError(f"manifest line {line_number} must be a JSON object.")
                if not isinstance(payload.get("pair_id"), str) or not payload["pair_id"]:
                    raise ValueError(f"manifest line {line_number} is missing pair_id.")
                rows.append(payload)

        return rows

    @staticmethod
    def _require_pair_id(row: dict[str, Any], index: int) -> str:
        pair_id = row.get("pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError(f"sample index {index} is missing pair_id.")
        return pair_id

    @staticmethod
    def _load_rgb(path: Path) -> Image.Image:
        with Image.open(path) as image:
            return image.convert("RGB").copy()

    @staticmethod
    def _load_fit_json(path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"fit json must be an object: {path}")
        return payload

    def _resolve_artifact_path(self, pair_id: str, patterns: tuple[str, ...]) -> Path:
        candidates = tuple(self.data_root / pattern.format(pair_id=pair_id) for pattern in patterns)
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return candidates[0]
