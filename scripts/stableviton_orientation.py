from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps


EXIF_ORIENTATION_TAG = 274
RGB_EXTS = {".jpg", ".jpeg", ".webp"}


def exif_orientation(path: Path) -> int | None:
    with Image.open(path) as image:
        exif = image.getexif()
        value = exif.get(EXIF_ORIENTATION_TAG) if exif else None
        return int(value) if value is not None else None


def open_rgb_exif_transposed(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB").copy()


def open_mask_exif_transposed(path: Path) -> Image.Image:
    with Image.open(path) as image:
        transposed = ImageOps.exif_transpose(image)
        if transposed.mode in {"1", "L", "P"}:
            return transposed.copy()
        return transposed.convert("L")


def save_without_exif(image: Image.Image, path: Path, **save_kwargs: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kwargs = dict(save_kwargs)
    kwargs.pop("exif", None)
    if path.suffix.lower() in RGB_EXTS and image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    image.save(path, **kwargs)


def copy_rgb_exif_transposed(source: Path, destination: Path, quality: int = 95) -> None:
    image = open_rgb_exif_transposed(source)
    kwargs: dict[str, Any] = {}
    if destination.suffix.lower() in {".jpg", ".jpeg"}:
        kwargs.update({"quality": quality, "subsampling": 0})
    save_without_exif(image, destination, **kwargs)


def copy_mask_exif_transposed(source: Path, destination: Path) -> None:
    image = open_mask_exif_transposed(source)
    save_without_exif(image, destination)


def copy_without_exif(source: Path, destination: Path, artifact_name: str) -> None:
    if artifact_name in {"image", "cloth", "worn", "agnostic-v3.2", "image-densepose", "openpose-img"}:
        copy_rgb_exif_transposed(source, destination)
    elif artifact_name in {"image-parse", "cloth-mask", "agnostic-mask"}:
        copy_mask_exif_transposed(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def header_after_exif_transpose(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        orientation = image.getexif().get(EXIF_ORIENTATION_TAG)
        width, height = image.size
        if orientation in {5, 6, 7, 8}:
            transposed_size = (height, width)
        else:
            transposed_size = (width, height)
        return {
            "width": width,
            "height": height,
            "mode": image.mode,
            "exif_orientation": orientation,
            "exif_transposed_width": transposed_size[0],
            "exif_transposed_height": transposed_size[1],
        }


def transform_point_for_exif_orientation(
    x: float,
    y: float,
    width: int,
    height: int,
    orientation: int | None,
) -> tuple[float, float]:
    if orientation in (None, 1):
        return x, y
    if orientation == 2:
        return width - x, y
    if orientation == 3:
        return width - x, height - y
    if orientation == 4:
        return x, height - y
    if orientation == 5:
        return y, x
    if orientation == 6:
        return height - y, x
    if orientation == 7:
        return height - y, width - x
    if orientation == 8:
        return y, width - x
    return x, y


def transform_openpose_keypoints_for_exif(
    payload: dict[str, Any],
    width: int,
    height: int,
    orientation: int | None,
) -> dict[str, Any]:
    if orientation in (None, 1):
        return payload

    out = json.loads(json.dumps(payload))
    for person in out.get("people") or []:
        values = person.get("pose_keypoints_2d") or person.get("keypoints")
        if not isinstance(values, list):
            continue
        for index in range(0, len(values) - 2, 3):
            try:
                x = float(values[index])
                y = float(values[index + 1])
            except (TypeError, ValueError):
                continue
            if x <= 0 and y <= 0:
                continue
            nx, ny = transform_point_for_exif_orientation(x, y, width, height, orientation)
            values[index] = nx
            values[index + 1] = ny
    return out
