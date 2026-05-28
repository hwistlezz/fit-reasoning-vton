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

`POST /api/tryon`은 pending job을 생성하고, 업로드된 입력 이미지를 `backend/outputs/{job_id}/`에 저장한 뒤, job별 StableVITON input root를 준비하고 FastAPI background task로 StableVITON 흐름을 시작합니다.

현재 `/api/tryon` 흐름은 업로드 이미지를 아래 구조로 복사합니다.

```text
backend/outputs/{job_id}/stableviton_input/
  test_pairs.txt
  test/
    image/person.png
    cloth/cloth.png
    image-densepose/
    agnostic-v3.2/
    agnostic-mask/
    cloth-mask/
```

아직 DensePose, `agnostic-v3.2`, `agnostic-mask`, `cloth-mask`는 자동 생성하지 않습니다. 필요한 artifact가 없으면 StableVITON inference 실행 전에 job을 `failed`로 처리합니다. full upload-based inference는 preprocessing pipeline 구현 이후 가능합니다.

하위 StableVITON wrapper는 job-specific data root를 넘기지 않는 경우 기존 `STABLEVITON_DATA_ROOT` 기반 prepared smoke data 실행을 계속 지원합니다.

### POST /api/tryon

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/tryon" `
  -F "person_image=@D:\path\to\person.png" `
  -F "cloth_image=@D:\path\to\cloth.png" `
  -F "height=175" `
  -F "weight=70" `
  -F "usual_size=L"
```

예시 응답:

```json
{
  "job_id": "job_20260527_153000_ab12cd34",
  "status": "pending",
  "message": "Job created. StableVITON inference is queued."
}
```

preprocessing artifact가 생성되기 전까지는 업로드 이미지 job의 최종 상태가 `failed`일 수 있습니다.

```json
{
  "job_id": "job_20260527_153000_ab12cd34",
  "status": "failed",
  "progress": 100,
  "message": "DensePose artifact is missing. Expected file: D:\\GitHub\\fit-reasoning-vton\\backend\\outputs\\job_20260527_153000_ab12cd34\\stableviton_input\\test\\image-densepose\\person.png"
}
```

### GET /api/job/{job_id}

```powershell
curl.exe http://127.0.0.1:8000/api/job/job_20260527_153000_ab12cd34
```

예시 응답:

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

모든 StableVITON artifact가 준비된 뒤의 성공 예시:

```json
{
  "job_id": "job_20260527_153000_ab12cd34",
  "status": "done",
  "person_image_url": "/outputs/job_20260527_153000_ab12cd34/person.png",
  "cloth_image_url": "/outputs/job_20260527_153000_ab12cd34/cloth.png",
  "result_image_url": "/outputs/job_20260527_153000_ab12cd34/result.png",
  "confidence": {
    "score": 60,
    "level": "medium",
    "warnings": [
      "현재 fit 분석은 placeholder입니다. 실제 신뢰도 계산은 아직 연결되지 않았습니다.",
      "StableVITON 결과 이미지 생성 여부와 응답 schema 연동만 검증합니다."
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
      "StableVITON 결과 이미지는 생성되었지만, 실제 fit analyzer는 아직 연결되지 않았습니다."
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

## Fit Analyzer Placeholder

현재 fit analyzer는 placeholder입니다. `confidence.score`는 실제 CV 기반 계산값이 아니며, 기본값은 `60`, `level`은 `medium`입니다.

현재 기준:

- `0-39`: `low`
- `40-69`: `medium`
- `70-100`: `high`

현재 `fit.label`은 `unknown`으로 고정됩니다. `shoulder_ratio`, `torso_width_ratio`, `sleeve_length_ratio`, `garment_length_ratio`는 아직 계산하지 않으며 `null`로 반환합니다.

`annotations`는 현재 빈 배열입니다.

추후 annotation hotspot은 아래 형태를 고려할 수 있지만, 이번 skeleton에서는 실제 annotation을 생성하지 않습니다.

```json
{
  "part": "shoulder",
  "x": 50,
  "y": 30,
  "severity": "medium",
  "message": "어깨선 정렬 신뢰도가 낮습니다."
}
```

실제 fit confidence 계산은 PC3 batch evaluation과 failure case 수집 후 rule 또는 model 기반 analyzer로 확장합니다.

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
- Job-scoped StableVITON input adapter
- `stableviton_input/test_pairs.txt` creation
- Missing preprocessing artifact preflight
- Pending/running/done/failed job JSON files
- StableVITON preflight checks
- StableVITON subprocess wrapper
- StableVITON stdout/stderr log capture
- `result.png` copy into `backend/outputs/{job_id}/`
- Fit analyzer placeholder
- Confidence response placeholder

## Excluded For Now

- Checkpoints
- Dataset files
- Generated images
- DensePose generation
- `agnostic-v3.2` / `agnostic-mask` generation
- `cloth-mask` generation
- Full uploaded-image StableVITON preprocessing pipeline
- CV-based fit analyzer
- Real confidence scoring
- Frontend implementation

## Repository Safety

- `backend/outputs/**` must not be committed.
- `backend/logs/**` must not be committed.
- `DATA/**` and `samples_smoke/**` must not be committed.
- Checkpoints, datasets, and generated images must not be committed.
- Only `.gitkeep` placeholders are tracked for runtime directories.
