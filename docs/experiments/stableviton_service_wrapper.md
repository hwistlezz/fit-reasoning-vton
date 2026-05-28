# StableVITON Service Wrapper - Issue #14

## Purpose

Issue #14 connects the FastAPI backend to the external StableVITON CLI inference path through a small service wrapper.

This is a backend integration smoke path. It verifies that a Try-On job can move from `pending` to `running`, execute StableVITON with prepared smoke data, save logs, and expose `backend/outputs/{job_id}/result.png` through `/api/result/{job_id}`.

## External Repository Policy

The StableVITON repository, checkpoints, datasets, and generated images are not copied into this repository.

The backend only references StableVITON through local environment configuration such as `STABLEVITON_ROOT` and `STABLEVITON_PYTHON`. This avoids committing external code, model weights, VITON-HD data, or generated images into the capstone repository.

## Required Environment Variables

The defaults target the PC1 Windows smoke-test setup.

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
| `STABLEVITON_BATCH_SIZE` | `1` |
| `STABLEVITON_DENOISE_STEPS` | `50` |
| `STABLEVITON_IMG_H` | `512` |
| `STABLEVITON_IMG_W` | `384` |

## Preflight Checks

Before inference, the wrapper checks:

- StableVITON root directory
- `inference.py`
- `configs\VITONHD.yaml`
- `ckpts\VITONHD.ckpt`
- `ckpts\VITONHD_PBE_pose.ckpt`
- `ckpts\VITONHD_VAE_finetuning.ckpt`
- `DATA\stableviton-smoke`
- `test_pairs.txt`
- required smoke input folders under `test\`

Preflight failures set the job status to `failed` before running inference.

## Run Backend

```powershell
cd D:\GitHub\fit-reasoning-vton
D:\conda-envs\vton\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Health check:

```powershell
curl.exe http://localhost:8000/api/health
```

## API Smoke Test

Use local sample images for upload. Do not commit those files.

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/tryon" `
  -F "person_image=@D:\path\to\person.png" `
  -F "cloth_image=@D:\path\to\cloth.png" `
  -F "height=175" `
  -F "weight=70" `
  -F "usual_size=L"
```

The response returns a `job_id` while StableVITON runs in a FastAPI background task.

Check status:

```powershell
curl.exe http://127.0.0.1:8000/api/job/job_20260527_153000_ab12cd34
```

Check result:

```powershell
curl.exe http://127.0.0.1:8000/api/result/job_20260527_153000_ab12cd34
```

On success, `result_image_url` points to:

```text
/outputs/{job_id}/result.png
```

The wrapper also writes:

```text
backend/outputs/{job_id}/stableviton_stdout.log
backend/outputs/{job_id}/stableviton_stderr.log
```

The StableVITON raw save directory is job-scoped under:

```text
backend/outputs/stableviton_raw/{job_id}/
```

## Git Safety

Do not commit:

- checkpoints
- datasets
- generated images
- `DATA/`
- `samples_smoke/`
- `backend/outputs/`
- `backend/outputs/stableviton_raw/`
- `*.ckpt`
- `*.jpg`
- `*.png`

Only source files, documentation, and placeholder `.gitkeep` files should be tracked.

## Current Limitations

This wrapper uses the prepared StableVITON smoke data path. It does not yet transform arbitrary uploaded person and cloth images into the full StableVITON preprocessing structure.

Fit label, confidence score, fit explanation, and annotation hotspots remain mocked after `result.png` is produced.
