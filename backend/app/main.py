from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.demo import router as demo_router
from backend.app.api.health import router as health_router
from backend.app.api.tryon import router as tryon_router
from backend.app.core.config import REPO_ROOT, settings
from backend.app.core.paths import ensure_runtime_dirs


ensure_runtime_dirs()
DEMO_ASSETS_DIR = REPO_ROOT / "backend" / "demo" / "assets"

app = FastAPI(title=settings.app_name, version=settings.version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(tryon_router, prefix=settings.api_prefix)
app.include_router(demo_router, prefix=settings.api_prefix)
app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")
if DEMO_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DEMO_ASSETS_DIR), name="demo-assets")


@app.on_event("startup")
def on_startup() -> None:
    ensure_runtime_dirs()
