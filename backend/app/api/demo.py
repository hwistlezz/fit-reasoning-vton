from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.demo import DemoCompareResponse, DemoSamplesResponse
from backend.app.services.demo_loader import DemoNotFoundError, demo_loader


router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/samples", response_model=DemoSamplesResponse)
def list_demo_samples() -> DemoSamplesResponse:
    items = demo_loader.list_samples()
    return DemoSamplesResponse(items=items, count=len(items))


@router.get("/artifact-compare/{pair_id}", response_model=DemoCompareResponse)
def get_artifact_compare(pair_id: str) -> DemoCompareResponse:
    try:
        return demo_loader.build_artifact_compare(pair_id)
    except DemoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/model-compare/{pair_id}", response_model=DemoCompareResponse)
def get_model_compare(pair_id: str) -> DemoCompareResponse:
    try:
        return demo_loader.build_model_compare(pair_id)
    except DemoNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
