import json
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from backend.app.core.config import settings
from backend.app.core.paths import ensure_output_dir
from backend.app.services.fit_analyzer import analyze_fit


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
JOB_ID_PATTERN = re.compile(r"^job_\d{8}_\d{6}_[a-f0-9]{8}$")
PENDING_MESSAGE = "StableVITON inference is queued."
RUNNING_MESSAGE = "StableVITON inference is running."
DONE_MESSAGE = "StableVITON inference completed."
RESULT_PENDING_MESSAGE = (
    "Result image is not available yet because StableVITON inference is queued."
)
RESULT_DONE_MESSAGE = "StableVITON result image was generated. Fit analysis was attached when available."


class JobStoreError(Exception):
    """Base class for expected job store errors."""


class InvalidJobIdError(JobStoreError):
    pass


class JobNotFoundError(JobStoreError):
    pass


class UnsupportedImageTypeError(JobStoreError):
    pass


class EmptyUploadError(JobStoreError):
    pass


def generate_job_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"job_{timestamp}_{short_uuid}"


def validate_job_id(job_id: str) -> None:
    if not JOB_ID_PATTERN.fullmatch(job_id):
        raise InvalidJobIdError("Invalid job_id format.")


def get_job_dir(job_id: str) -> Path:
    validate_job_id(job_id)
    return settings.output_dir / job_id


def get_existing_job_dir(job_id: str) -> Path:
    job_dir = get_job_dir(job_id)
    if not job_dir.is_dir():
        raise JobNotFoundError(f"Job not found: {job_id}")
    return job_dir


def validate_upload_extension(upload: UploadFile) -> str:
    filename = upload.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
        raise UnsupportedImageTypeError(f"Unsupported image extension '{extension}'. Allowed: {allowed}")
    return extension


async def save_upload_file(upload: UploadFile, destination: Path) -> None:
    content = await upload.read()
    if not content:
        raise EmptyUploadError(f"Uploaded file is empty: {upload.filename}")
    destination.write_bytes(content)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise JobNotFoundError(f"Missing job file: {path.name}")
    return json.loads(path.read_text(encoding="utf-8"))


def public_output_url(job_id: str, filename: str) -> str:
    return f"/outputs/{job_id}/{filename}"


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_job_meta(job_id: str) -> dict[str, Any]:
    job_dir = get_existing_job_dir(job_id)
    return read_json(job_dir / "meta.json")


def _image_urls_from_meta(job_id: str, meta: dict[str, Any]) -> tuple[str | None, str | None]:
    person_filename = meta.get("person_image", {}).get("stored_filename")
    cloth_filename = meta.get("cloth_image", {}).get("stored_filename")
    person_url = public_output_url(job_id, person_filename) if person_filename else None
    cloth_url = public_output_url(job_id, cloth_filename) if cloth_filename else None
    return person_url, cloth_url


def write_job_status(job_id: str, status: str, progress: int, message: str) -> None:
    job_dir = get_existing_job_dir(job_id)
    existing_status_path = job_dir / "status.json"
    existing_status = read_json(existing_status_path) if existing_status_path.is_file() else {}
    status_data = {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "message": message,
        "created_at": existing_status.get("created_at", _timestamp()),
        "updated_at": _timestamp(),
    }
    write_json(existing_status_path, status_data)


def mark_job_running(job_id: str) -> None:
    write_job_status(job_id, "running", 20, RUNNING_MESSAGE)


def write_success_result(job_id: str, result_filename: str = "result.png") -> None:
    job_dir = get_existing_job_dir(job_id)
    meta = _read_job_meta(job_id)
    person_url, cloth_url = _image_urls_from_meta(job_id, meta)
    result_image_url = public_output_url(job_id, result_filename)
    analysis = analyze_fit(job_id=job_id, result_image_url=result_image_url).to_response_payload()
    result = {
        "job_id": job_id,
        "status": "done",
        "person_image_url": person_url,
        "cloth_image_url": cloth_url,
        "result_image_url": result_image_url,
        "confidence": analysis["confidence"],
        "fit": analysis["fit"],
        "annotations": analysis["annotations"],
        "message": RESULT_DONE_MESSAGE,
    }
    write_json(job_dir / "result.json", result)
    write_job_status(job_id, "done", 100, DONE_MESSAGE)


def write_failed_result(job_id: str, code: str, message: str) -> None:
    job_dir = get_existing_job_dir(job_id)
    meta = _read_job_meta(job_id)
    person_url, cloth_url = _image_urls_from_meta(job_id, meta)
    error = {
        "code": code,
        "message": message,
    }
    result = {
        "job_id": job_id,
        "status": "failed",
        "person_image_url": person_url,
        "cloth_image_url": cloth_url,
        "result_image_url": None,
        "confidence": None,
        "fit": None,
        "annotations": [],
        "message": message,
        "error": error,
    }
    write_json(job_dir / "result.json", result)
    write_json(job_dir / "error.json", {"job_id": job_id, "status": "failed", "error": error})
    write_job_status(job_id, "failed", 100, message)


async def create_pending_job(
    *,
    person_image: UploadFile,
    cloth_image: UploadFile,
    height: float,
    weight: float,
    usual_size: str,
) -> dict[str, str]:
    person_extension = validate_upload_extension(person_image)
    cloth_extension = validate_upload_extension(cloth_image)

    ensure_output_dir()
    job_id = generate_job_id()
    job_dir = settings.output_dir / job_id
    job_dir.mkdir(parents=False, exist_ok=False)

    person_filename = f"person{person_extension}"
    cloth_filename = f"cloth{cloth_extension}"

    try:
        await save_upload_file(person_image, job_dir / person_filename)
        await save_upload_file(cloth_image, job_dir / cloth_filename)

        created_at = datetime.now().isoformat(timespec="seconds")
        meta = {
            "job_id": job_id,
            "height": height,
            "weight": weight,
            "usual_size": usual_size,
            "person_image": {
                "stored_filename": person_filename,
                "original_filename": person_image.filename,
            },
            "cloth_image": {
                "stored_filename": cloth_filename,
                "original_filename": cloth_image.filename,
            },
            "created_at": created_at,
        }
        status = {
            "job_id": job_id,
            "status": "pending",
            "progress": 0,
            "message": PENDING_MESSAGE,
            "created_at": created_at,
        }
        result = {
            "job_id": job_id,
            "status": "pending",
            "person_image_url": public_output_url(job_id, person_filename),
            "cloth_image_url": public_output_url(job_id, cloth_filename),
            "result_image_url": None,
            "confidence": None,
            "fit": None,
            "annotations": [],
            "message": RESULT_PENDING_MESSAGE,
        }

        write_json(job_dir / "meta.json", meta)
        write_json(job_dir / "status.json", status)
        write_json(job_dir / "result.json", result)
    except Exception:
        for path in job_dir.glob("*"):
            if path.is_file():
                path.unlink()
        job_dir.rmdir()
        raise

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Job created. StableVITON inference is queued.",
    }


def read_job_status(job_id: str) -> dict[str, Any]:
    job_dir = get_existing_job_dir(job_id)
    return read_json(job_dir / "status.json")


def read_job_result(job_id: str) -> dict[str, Any]:
    job_dir = get_existing_job_dir(job_id)
    result = read_json(job_dir / "result.json")
    result["annotations"] = result.get("annotations") or []
    result.setdefault("confidence", None)
    result.setdefault("fit", None)
    result.setdefault("result_image_url", None)
    result.setdefault("message", "")
    result.setdefault("error", None)
    return result
