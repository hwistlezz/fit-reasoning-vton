from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from backend.app.core.job_store import (
    EmptyUploadError,
    InvalidJobIdError,
    JobNotFoundError,
    UnsupportedImageTypeError,
    create_pending_job,
    read_job_result,
    read_job_status,
)
from backend.app.schemas.result import TryOnResultResponse
from backend.app.schemas.tryon import JobStatusResponse, TryOnCreateResponse


router = APIRouter(tags=["tryon"])


@router.post("/tryon", response_model=TryOnCreateResponse)
async def create_tryon_job(
    person_image: UploadFile = File(...),
    cloth_image: UploadFile = File(...),
    height: float = Form(...),
    weight: float = Form(...),
    usual_size: str = Form(...),
) -> TryOnCreateResponse:
    try:
        response = await create_pending_job(
            person_image=person_image,
            cloth_image=cloth_image,
            height=height,
            weight=weight,
            usual_size=usual_size,
        )
    except (UnsupportedImageTypeError, EmptyUploadError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create try-on job.",
        ) from exc

    return TryOnCreateResponse(**response)


@router.get("/job/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str) -> JobStatusResponse:
    try:
        response = read_job_status(job_id)
    except InvalidJobIdError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return JobStatusResponse(**response)


@router.get("/result/{job_id}", response_model=TryOnResultResponse)
def get_tryon_result(job_id: str) -> TryOnResultResponse:
    try:
        response = read_job_result(job_id)
    except InvalidJobIdError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except JobNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return TryOnResultResponse(**response)
