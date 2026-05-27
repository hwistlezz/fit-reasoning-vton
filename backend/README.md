# Backend

FastAPI backend for the Fit-aware Virtual Try-On Web Prototype.

This backend currently provides the API skeleton, runtime directory setup, upload storage, pending Try-On job metadata, and job status/result reads. The StableVITON inference wrapper is not connected yet.

## Environment

- Python 3.10
- Conda env: `D:\conda-envs\vton`
- FastAPI
- Uvicorn

## Install

```powershell
cd D:\GitHub\fit-reasoning-vton
conda activate D:\conda-envs\vton
python -m pip install -r backend/requirements.txt
```

## Run

```powershell
cd D:\GitHub\fit-reasoning-vton
conda activate D:\conda-envs\vton
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Health Check

```powershell
curl http://localhost:8000/api/health
```

Example response:

```json
{
  "status": "ok",
  "service": "fit-aware-vton-backend",
  "version": "0.1.0"
}
```

## Try-On Job API

`POST /api/tryon` creates a pending job and stores the uploaded input images under `backend/outputs/{job_id}/`.

Because the StableVITON inference wrapper is not connected yet, the backend does not create `result.png`. The result response returns `result_image_url: null`, `confidence: null`, `fit: null`, and `annotations: []` so the frontend can handle the pending state safely.

### POST /api/tryon

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/tryon" `
  -F "person_image=@D:\path\to\person.png" `
  -F "cloth_image=@D:\path\to\cloth.png" `
  -F "height=175" `
  -F "weight=70" `
  -F "usual_size=L"
```

Example response:

```json
{
  "job_id": "job_20260527_153000_ab12cd34",
  "status": "pending",
  "message": "Job created. StableVITON inference wrapper is not connected yet."
}
```

### GET /api/job/{job_id}

```powershell
curl.exe http://127.0.0.1:8000/api/job/job_20260527_153000_ab12cd34
```

Example response:

```json
{
  "job_id": "job_20260527_153000_ab12cd34",
  "status": "pending",
  "progress": 0,
  "message": "StableVITON inference wrapper is not connected yet."
}
```

### GET /api/result/{job_id}

```powershell
curl.exe http://127.0.0.1:8000/api/result/job_20260527_153000_ab12cd34
```

Example response:

```json
{
  "job_id": "job_20260527_153000_ab12cd34",
  "status": "pending",
  "person_image_url": "/outputs/job_20260527_153000_ab12cd34/person.png",
  "cloth_image_url": "/outputs/job_20260527_153000_ab12cd34/cloth.png",
  "result_image_url": null,
  "confidence": null,
  "fit": null,
  "annotations": [],
  "message": "Result image is not available because StableVITON inference wrapper is not connected yet."
}
```

## Current Scope

- FastAPI app entrypoint
- `/api/health`
- `/api/tryon`
- `/api/job/{job_id}`
- `/api/result/{job_id}`
- CORS setup
- Runtime path setup
- Static serving for `/outputs`
- Upload image storage
- Pending job JSON files

## Excluded For Now

- StableVITON inference wrapper
- Checkpoints
- Dataset files
- Generated images
- `result.png` creation
- Fit analyzer
- Confidence scoring
- Frontend implementation

## Repository Safety

- `backend/outputs/**` must not be committed.
- `backend/logs/**` must not be committed.
- Checkpoints, datasets, and generated images must not be committed.
- Only `.gitkeep` placeholders are tracked for runtime directories.
