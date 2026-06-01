# 백엔드

Fit-aware Virtual Try-On 웹 프로토타입을 위한 FastAPI 백엔드입니다.

현재 백엔드는 런타임 디렉터리 생성, 이미지 업로드 저장, Try-On job 생성, job 상태/result 조회, StableVITON 실행 wrapper, 업로드 이미지 기반 StableVITON 입력 어댑터, 착장 신뢰도 임시 응답 구조를 제공합니다.

## 환경

- Python 3.10
- Conda env: `D:\conda-envs\vton`
- FastAPI
- Uvicorn
- 외부 StableVITON repo: `D:\GitHub\StableVITON`

StableVITON 외부 repo, checkpoint, dataset, generated image는 이 저장소에 복사하지 않습니다. 백엔드는 환경변수와 로컬 경로로만 StableVITON을 참조합니다.

## StableVITON 설정

백엔드는 아래 환경변수를 읽습니다. 설정하지 않으면 PC1 smoke-test 기본값을 사용합니다.

| 변수 | 기본값 |
| --- | --- |
| `STABLEVITON_ROOT` | `D:\GitHub\StableVITON` |
| `STABLEVITON_PYTHON` | `D:\conda-envs\vton\python.exe` |
| `STABLEVITON_CONFIG_PATH` | `configs\VITONHD.yaml` |
| `STABLEVITON_MODEL_LOAD_PATH` | `ckpts\VITONHD.ckpt` |
| `STABLEVITON_DATA_ROOT` | `DATA\stableviton-smoke` |
| `STABLEVITON_OUTPUT_DIR` | `D:\GitHub\fit-reasoning-vton\backend\outputs\stableviton_raw` |
| `STABLEVITON_TIMEOUT_SECONDS` | `300` |
| `STABLEVITON_USE_UNPAIR` | `true` |

## Fit Analyzer 설정

백엔드는 성공 result를 만들 때 먼저 job별 `fit.json`을 찾습니다.

탐색 순서는 다음과 같습니다.

1. `backend/outputs/{job_id}/fit.json`
2. `FIT_ANALYSIS_ROOT/{job_id}/fit.json`
3. 없으면 placeholder fit 분석 결과 반환

`FIT_ANALYSIS_ROOT` 기본값은 `backend/datasets/processed/fit_results`입니다. 이 경로는 PC2가 생성할 processed fit result를 로컬에서 연결하기 위한 위치이며, `backend/datasets/processed/**`는 Git에 포함하지 않습니다.

`fit.json`이 있으면 `confidence`, `fit`, `annotations`를 읽어 `/api/result/{job_id}` 응답에 사용합니다. `fit.json`이 없거나 invalid하면 서버를 중단하지 않고 기존 placeholder 결과를 반환합니다.

fit analyzer loader는 두 가지 fit result 형식을 지원합니다.

1. backend-compatible fit result format
   - `confidence.score`
   - `confidence.level`
   - `fit.label`
   - `fit.scores`
   - `annotations`
2. PC2 `batch_fit_features.py` compact format
   - `confidence: number`
   - `fit_label`
   - `features`
   - `annotations`

PC2 compact format은 confidence number를 `confidence.score`와 `confidence.level`로 변환하고, `fit_label`과 `features`를 각각 `fit.label`, `fit.scores`로 normalize합니다. `annotations`는 backend annotation schema와 같은 `key`, `label`, `text`, `x`, `y`, `value` 형식을 우선 그대로 사용하고, `part`, `message`, `severity` 형식도 기존 annotation schema로 변환합니다.

`docs/examples/fit_result.example.json`과 `docs/examples/pc2_fit_result.example.json`은 실제 AIHub 결과가 아닌 loader 검증용 예시입니다.

```powershell
python -c "from pathlib import Path; from backend.app.services.fit_analyzer import analyze_fit; r=analyze_fit('job_test', '/outputs/job_test/result.png', Path('docs/examples/fit_result.example.json')); print(r.confidence.score); print(r.fit.label); print(r.annotations)"
```

PC2 compact format 검증:

```powershell
python -c "from pathlib import Path; from backend.app.services.fit_analyzer import analyze_fit; r=analyze_fit('job_test', '/outputs/job_test/result.png', Path('docs/examples/pc2_fit_result.example.json')); print(r.confidence.score); print(r.fit.label); print(r.annotations)"
```

Conda 환경을 직접 지정해야 하는 경우 다음처럼 실행할 수 있습니다.

```powershell
D:\conda-envs\vton\python.exe -c "from pathlib import Path; from backend.app.services.fit_analyzer import analyze_fit; r=analyze_fit('job_test', '/outputs/job_test/result.png', Path('docs/examples/fit_result.example.json')); print(r.confidence.score); print(r.fit.label); print(r.annotations)"
```

## 설치

```powershell
cd D:\GitHub\fit-reasoning-vton
conda activate D:\conda-envs\vton
python -m pip install -r backend/requirements.txt
```

## 실행

```powershell
cd D:\GitHub\fit-reasoning-vton
conda activate D:\conda-envs\vton
D:\conda-envs\vton\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 상태 확인

```powershell
curl http://localhost:8000/api/health
```

예시 응답:

```json
{
  "status": "ok",
  "service": "fit-aware-vton-backend",
  "version": "0.1.0"
}
```

## Try-On 작업 API

`POST /api/tryon`은 pending job을 생성하고, 업로드된 입력 이미지를 `backend/outputs/{job_id}/`에 저장합니다. 이후 job별 StableVITON input root를 준비하고 FastAPI background task로 StableVITON 실행 흐름을 시작합니다.

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

아직 DensePose, `agnostic-v3.2`, `agnostic-mask`, `cloth-mask`는 자동 생성하지 않습니다. 필요한 artifact가 없으면 StableVITON 추론 실행 전에 job을 `failed`로 처리합니다. 전체 업로드 기반 추론은 preprocessing pipeline 구현 이후 가능합니다.

하위 StableVITON 실행 wrapper는 job별 data root를 넘기지 않는 경우 기존 `STABLEVITON_DATA_ROOT` 기반 prepared smoke data 실행을 계속 지원합니다.

### POST `/api/tryon`

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

preprocessing artifact가 생성되기 전까지 업로드 이미지 job의 최종 상태는 `failed`일 수 있습니다.

```json
{
  "job_id": "job_20260527_153000_ab12cd34",
  "status": "failed",
  "progress": 100,
  "message": "DensePose artifact is missing. Expected file: D:\\GitHub\\fit-reasoning-vton\\backend\\outputs\\job_20260527_153000_ab12cd34\\stableviton_input\\test\\image-densepose\\person.png"
}
```

### GET `/api/job/{job_id}`

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

### GET `/api/result/{job_id}`

```powershell
curl.exe http://127.0.0.1:8000/api/result/job_20260527_153000_ab12cd34
```

모든 StableVITON artifact가 준비되고 result image 생성까지 완료된 경우의 성공 예시는 다음과 같습니다.

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
  "message": "StableVITON result image was generated. Fit analysis was attached when available."
}
```

추론이 실패하면 `status.json`, `result.json`, `error.json`에 `failed` 상태와 error code를 기록합니다. StableVITON 실행 log는 아래 파일에 저장합니다.

```text
backend/outputs/{job_id}/stableviton_stdout.log
backend/outputs/{job_id}/stableviton_stderr.log
```

StableVITON 원본 저장 디렉터리는 job별로 `backend/outputs/stableviton_raw/{job_id}/` 아래에 생성됩니다.

## Fit 분석 임시 구현

현재 fit analyzer는 job별 `fit.json`이 있으면 해당 값을 응답에 사용하고, 없거나 invalid하면 placeholder를 반환합니다. placeholder의 `confidence.score`는 실제 CV 기반 계산값이 아니며, 기본값은 `60`, `level`은 `medium`입니다.

현재 level 기준:

- `0-39`: `low`
- `40-69`: `medium`
- `70-100`: `high`

placeholder에서는 `fit.label`을 `unknown`으로 반환합니다. `shoulder_ratio`, `torso_width_ratio`, `sleeve_length_ratio`, `garment_length_ratio`는 아직 계산하지 않으며 `null`로 반환합니다.

placeholder fallback의 `annotations`는 빈 배열입니다.

추후 annotation hotspot은 아래 형태를 고려할 수 있지만, 이번 임시 구현에서는 실제 annotation을 생성하지 않습니다.

```json
{
  "part": "shoulder",
  "x": 50,
  "y": 30,
  "severity": "medium",
  "message": "어깨선 정렬 신뢰도가 낮습니다."
}
```

실제 fit confidence 계산은 PC3 batch evaluation과 failure case 수집 후 규칙 또는 모델 기반 분석기로 확장합니다. 실제 AIHub raw data와 generated `fit.json`은 Git에 포함하지 않습니다.

## 현재 범위

- FastAPI 앱 진입점
- `/api/health`
- `/api/tryon`
- `/api/job/{job_id}`
- `/api/result/{job_id}`
- CORS 설정
- runtime path 설정
- `/outputs` 정적 파일 제공
- 업로드 이미지 저장
- job별 StableVITON 입력 어댑터
- `stableviton_input/test_pairs.txt` 생성
- preprocessing artifact 누락 사전 검사
- pending/running/done/failed job JSON 파일
- StableVITON 사전 검사
- StableVITON subprocess 실행 wrapper
- StableVITON stdout/stderr log 저장
- `result.png`를 `backend/outputs/{job_id}/`로 복사
- fit 분석기 임시 구현
- confidence 응답 임시 구현

## 아직 제외된 범위

- checkpoint
- dataset 파일
- 생성 이미지
- DensePose 생성
- `agnostic-v3.2` / `agnostic-mask` 생성
- `cloth-mask` 생성
- 전체 업로드 이미지 기반 StableVITON 전처리 파이프라인
- 실제 CV 기반 fit 분석기
- 실제 confidence 계산
- 프론트엔드 구현

## 저장소 안전 규칙

- `backend/outputs/**`는 commit하지 않습니다.
- `backend/logs/**`는 commit하지 않습니다.
- `DATA/**`, `samples_smoke/**`는 commit하지 않습니다.
- checkpoint, dataset, 생성 이미지는 commit하지 않습니다.
- runtime directory는 `.gitkeep` placeholder만 추적합니다.
