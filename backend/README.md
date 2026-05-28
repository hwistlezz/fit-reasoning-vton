# Backend

FastAPI backend for the Fit-aware Virtual Try-On Web Prototype.

This backend provides the API skeleton, runtime directory setup, upload storage, Try-On job metadata, job status/result reads, and a StableVITON service wrapper for the prepared smoke-data path.

## Environment

- Python 3.10
- Conda env: `D:\conda-envs\vton`
- FastAPI
- Uvicorn
- External StableVITON repo: `D:\GitHub\StableVITON`

StableVITON is referenced by local path only. Do not copy the external repository, checkpoints, datasets, or generated images into this repository.

### StableVITON Settings

The backend reads these environment variables and falls back to the PC1 smoke-test defaults:

| Variable | Default |
| --- | --- |
| `STABLEVITON_ROOT` | `D:\GitHub\StableVITON` |
| `STABLEVITON_PYTHON` | `D:\conda-envs\vton\python.exe` |
| `STABLEVITON_CONFIG_PATH` | `configs\VITONHD.yaml` |
| `STABLEVITON_MODEL_LOAD_PATH` | `ckpts\VITONHD.ckpt` |
| `STABLEVITON_DATA_ROOT` | `DATA\stableviton-smoke` |
| `STABLEVITON_OUTPUT_DIR` | `D:\GitHub\fit-reasoning-vton\backend\outputs\stableviton_raw` |
| `STABLEVITON_TIMEOUT_SECONDS` | `300` |
| `STABLEVITON_USE_UNPAIR` | `true` |

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
D:\conda-envs\vton\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
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

`POST /api/tryon` creates a pending job, stores the uploaded input images under `backend/outputs/{job_id}/`, and queues StableVITON inference in a FastAPI background task.

The current wrapper runs StableVITON against the prepared smoke data configured by `STABLEVITON_DATA_ROOT`. It does not yet preprocess arbitrary uploaded images into StableVITON-ready inputs. The uploaded images are still stored and returned through the API so the frontend contract stays stable.

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
  "message": "Job created. StableVITON inference is queued."
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
  "status": "running",
  "progress": 20,
  "message": "StableVITON inference is running."
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
  "status": "done",
  "person_image_url": "/outputs/job_20260527_153000_ab12cd34/person.png",
  "cloth_image_url": "/outputs/job_20260527_153000_ab12cd34/cloth.png",
  "result_image_url": "/outputs/job_20260527_153000_ab12cd34/result.png",
  "confidence": {
    "score": 70,
    "level": "medium",
    "warnings": [
      "Current fit analysis is mocked. This job only verifies StableVITON result image generation."
    ]
  },
  "fit": {
    "label": "unknown",
    "scores": {
      "shoulder_ratio": null,
      "torso_width_ratio": null,
      "sleeve_length_ratio": null,
      "garment_length_ratio": null
    },
    "explanations": [
      "StableVITON generated a result image, but the real fit analyzer is not connected yet."
    ]
  },
  "annotations": [],
  "message": "StableVITON result image was generated. Fit analysis is still mocked."
}
```

If inference fails, `status.json`, `result.json`, and `error.json` are updated with a `failed` status and an error code. The wrapper writes StableVITON logs to:

```text
backend/outputs/{job_id}/stableviton_stdout.log
backend/outputs/{job_id}/stableviton_stderr.log
```

The StableVITON raw save directory is job-scoped under `backend/outputs/stableviton_raw/{job_id}/`.

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
- Pending/running/done/failed job JSON files
- StableVITON preflight checks
- StableVITON subprocess wrapper
- StableVITON stdout/stderr log capture
- `result.png` copy into `backend/outputs/{job_id}/`

## Excluded For Now

- Checkpoints
- Dataset files
- Generated images
- Full uploaded-image StableVITON preprocessing pipeline
- Fit analyzer
- Confidence scoring
- Frontend implementation

## Repository Safety

- `backend/outputs/**` must not be committed.
- `backend/logs/**` must not be committed.
- `DATA/**` and `samples_smoke/**` must not be committed.
- Checkpoints, datasets, and generated images must not be committed.
- Only `.gitkeep` placeholders are tracked for runtime directories.
