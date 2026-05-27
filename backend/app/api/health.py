from fastapi import APIRouter

from backend.app.core.config import settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "fit-aware-vton-backend",
        "version": settings.version,
    }
