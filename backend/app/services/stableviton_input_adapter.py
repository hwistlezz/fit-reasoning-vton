from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from backend.app.core.job_store import get_existing_job_dir, read_json


STABLEVITON_INPUT_DIRNAME = "stableviton_input"
PERSON_FILENAME = "person.png"
CLOTH_FILENAME = "cloth.png"

REQUIRED_TEST_DIRS = (
    "image",
    "cloth",
    "image-densepose",
    "agnostic-v3.2",
    "agnostic-mask",
    "cloth-mask",
)


@dataclass(frozen=True)
class StableVitonInput:
    data_root: Path
    person_filename: str
    cloth_filename: str
    pair_list_path: Path


class StableVitonInputAdapterError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _test_dir(data_root: Path, name: str) -> Path:
    return data_root / "test" / name


def _ensure_input_dirs(data_root: Path) -> None:
    for dirname in REQUIRED_TEST_DIRS:
        _test_dir(data_root, dirname).mkdir(parents=True, exist_ok=True)


def _read_uploaded_path(job_dir: Path, meta: dict, image_key: str, error_code: str) -> Path:
    stored_filename = meta.get(image_key, {}).get("stored_filename")
    if not stored_filename:
        raise StableVitonInputAdapterError(
            error_code,
            f"Stored {image_key} filename is missing from meta.json.",
        )

    source_path = job_dir / stored_filename
    if not source_path.is_file() or source_path.stat().st_size == 0:
        raise StableVitonInputAdapterError(
            error_code,
            f"Stored {image_key} file is missing or empty: {source_path}",
        )
    return source_path


def _save_as_png(source_path: Path, target_path: Path, error_code: str) -> None:
    try:
        with Image.open(source_path) as image:
            image.convert("RGB").save(target_path, format="PNG")
    except Exception as exc:  # noqa: BLE001 - expose deterministic adapter failure.
        raise StableVitonInputAdapterError(
            error_code,
            f"Failed to copy uploaded image into StableVITON input root: {source_path}",
        ) from exc


def _write_pair_list(data_root: Path, person_filename: str, cloth_filename: str) -> Path:
    pair_list_path = data_root / "test_pairs.txt"
    pair_list_path.write_text(f"{person_filename} {cloth_filename}\n", encoding="utf-8")
    return pair_list_path


def prepare_stableviton_input(job_id: str) -> StableVitonInput:
    job_dir = get_existing_job_dir(job_id)
    meta = read_json(job_dir / "meta.json")
    data_root = job_dir / STABLEVITON_INPUT_DIRNAME

    try:
        _ensure_input_dirs(data_root)
        person_source = _read_uploaded_path(
            job_dir,
            meta,
            "person_image",
            "PREPROCESS_PERSON_IMAGE_MISSING",
        )
        cloth_source = _read_uploaded_path(
            job_dir,
            meta,
            "cloth_image",
            "PREPROCESS_CLOTH_IMAGE_MISSING",
        )

        person_target = _test_dir(data_root, "image") / PERSON_FILENAME
        cloth_target = _test_dir(data_root, "cloth") / CLOTH_FILENAME
        _save_as_png(person_source, person_target, "STABLEVITON_INPUT_ADAPTER_FAILED")
        _save_as_png(cloth_source, cloth_target, "STABLEVITON_INPUT_ADAPTER_FAILED")
        pair_list_path = _write_pair_list(data_root, PERSON_FILENAME, CLOTH_FILENAME)
    except StableVitonInputAdapterError:
        raise
    except Exception as exc:  # noqa: BLE001 - collapse unexpected filesystem issues.
        raise StableVitonInputAdapterError(
            "STABLEVITON_INPUT_ADAPTER_FAILED",
            f"Failed to prepare StableVITON input root for job {job_id}: {exc}",
        ) from exc

    return StableVitonInput(
        data_root=data_root,
        person_filename=PERSON_FILENAME,
        cloth_filename=CLOTH_FILENAME,
        pair_list_path=pair_list_path,
    )


def preflight_required_artifacts(stableviton_input: StableVitonInput) -> None:
    data_root = stableviton_input.data_root
    required_files = (
        (
            "PREPROCESS_DENSEPOSE_MISSING",
            _test_dir(data_root, "image-densepose") / stableviton_input.person_filename,
            "DensePose artifact is missing.",
        ),
        (
            "PREPROCESS_AGNOSTIC_IMAGE_MISSING",
            _test_dir(data_root, "agnostic-v3.2") / stableviton_input.person_filename,
            "Agnostic person image artifact is missing.",
        ),
        (
            "PREPROCESS_AGNOSTIC_MASK_MISSING",
            _test_dir(data_root, "agnostic-mask") / stableviton_input.person_filename,
            "Agnostic mask artifact is missing.",
        ),
        (
            "PREPROCESS_CLOTH_MASK_MISSING",
            _test_dir(data_root, "cloth-mask") / stableviton_input.cloth_filename,
            "Cloth mask artifact is missing.",
        ),
    )

    base_required_files = (
        data_root / "test_pairs.txt",
        _test_dir(data_root, "image") / stableviton_input.person_filename,
        _test_dir(data_root, "cloth") / stableviton_input.cloth_filename,
    )
    for path in base_required_files:
        if not path.is_file() or path.stat().st_size == 0:
            raise StableVitonInputAdapterError(
                "STABLEVITON_REQUIRED_ARTIFACT_MISSING",
                f"Required StableVITON input file is missing or empty: {path}",
            )

    for code, path, message in required_files:
        if not path.is_file() or path.stat().st_size == 0:
            raise StableVitonInputAdapterError(code, f"{message} Expected file: {path}")
