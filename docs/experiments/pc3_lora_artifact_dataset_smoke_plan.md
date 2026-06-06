# PC3 LoRA Artifact Dataset Smoke Test 계획

## 1. 목적

PC2에서 새로 전달할 AIHub LoRA 10k artifact dataset을 받기 전에, PC3에서 dataset loader와 smoke test script가 추가 artifact 디렉토리를 검증할 수 있도록 준비한다.

이번 작업은 실제 LoRA 학습이 아니다. 기존 `image`, `cloth`, `worn`, `fit` 기본 검증은 유지하면서, `openpose-json`, `image-parse`, `cloth-mask`, `agnostic-v3.2`, `agnostic-mask`, `image-densepose` 같은 training artifact를 required 또는 optional로 확인할 수 있게 만드는 사전 준비 작업이다.

## 2. 현재 10k Filtered Dataset 상태

현재 PC3 로컬 dataset 위치:

```text
backend/datasets/lora_pilot_aihub_10k_full
```

#74 결과로 원본 9,999개 manifest에서 known-bad 4개 pair를 제외했다.

```text
manifest.raw_9999.jsonl = 원본 9,999개 manifest 백업
manifest.jsonl = known-bad 4개 제외 filtered 9,995개 manifest
```

제외된 pair:

```text
EP00003620
EP00003937
EP00005080
EP00007279
```

현재 filtered dataset은 기본 `image`, `cloth`, `worn`, `fit` smoke test를 통과한다.

## 3. 새 Artifact Dataset 기대 구조

새 dataset은 다음 구조를 후보로 둔다.

```text
backend/datasets/<new_10k_artifact_dataset>/
  image/
  cloth/
  worn/
  fit/
  openpose-json/
  image-parse/
  cloth-mask/
  agnostic-v3.2/
  agnostic-mask/
  image-densepose/
  manifest.jsonl
```

`image-densepose/`는 아직 없을 수 있다.

## 4. Artifact 경로 규칙

Artifact 경로는 manifest 내부 경로가 아니라 `pair_id` 기준으로 조립한다.

| artifact | 후보 파일 | 검증 |
| --- | --- | --- |
| `openpose-json` | `{pair_id}_keypoints.json`, `{pair_id}.json` | JSON parse |
| `image-parse` | `{pair_id}.png` | image load |
| `cloth-mask` | `{pair_id}.png` | image load |
| `agnostic-v3.2` | `{pair_id}.png`, `{pair_id}.jpg` | image load |
| `agnostic-mask` | `{pair_id}.png` | image load |
| `image-densepose` | `{pair_id}.jpg`, `{pair_id}.png` | image load |

## 5. Required Artifact와 Optional Artifact 차이

`--required-artifacts`로 지정한 artifact는 누락되면 error로 집계한다.

`--optional-artifacts`로 지정한 artifact는 누락 count를 summary에 기록하지만 smoke 실패로 보지 않는다. 단, optional artifact 파일이 실제로 존재하는데 JSON parse 또는 image load가 실패하면 load error로 집계한다.

summary JSON에는 다음 필드가 추가된다.

```json
{
  "required_artifacts": ["openpose-json", "image-parse"],
  "optional_artifacts": ["image-densepose"],
  "artifact_summary": {
    "openpose-json": {
      "required": true,
      "checked": 9995,
      "missing": 0,
      "load_errors": 0
    },
    "image-densepose": {
      "required": false,
      "checked": 9995,
      "missing": 9995,
      "load_errors": 0
    }
  },
  "artifact_errors": 0
}
```

기존 success 조건에 `artifact_errors=0`을 추가한다.

## 6. DensePose를 Optional로 두는 이유

현재 PC2 artifact dataset 준비 단계에서 densepose는 아직 제외될 수 있다. 따라서 `image-densepose`는 새 dataset 수신 직후 strict smoke에서도 optional로 두고, 나머지 artifact가 안정화된 뒤 required로 승격할지 판단한다.

## 7. 현재 Dataset Basic Smoke Test

현재 filtered dataset에서 기존 동작이 깨지지 않는지 다음 명령으로 확인했다.

```powershell
python backend\training\scripts\smoke_test_lora_dataset.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_full `
  --limit 100 `
  --sample-count 8 `
  --contact-sheet backend\training\outputs\lora_artifact_smoke_current\basic_contact_sheet.jpg `
  --summary-json backend\training\outputs\lora_artifact_smoke_current\basic_summary.json `
  --check-backend-loader
```

결과:

```text
manifest_count=9995
checked_count=100
missing_image=0
missing_cloth=0
missing_worn=0
missing_fit=0
image_load_errors=0
fit_json_errors=0
backend_loader_errors=0
artifact_errors=0
```

## 8. 현재 Dataset Optional Artifact 검증 결과

현재 filtered dataset은 artifact 디렉토리가 없으므로 모든 artifact를 optional로 검증했다.

```powershell
python backend\training\scripts\smoke_test_lora_dataset.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_full `
  --limit 100 `
  --sample-count 8 `
  --contact-sheet backend\training\outputs\lora_artifact_smoke_current\artifact_contact_sheet.jpg `
  --summary-json backend\training\outputs\lora_artifact_smoke_current\artifact_summary.json `
  --check-backend-loader `
  --optional-artifacts openpose-json image-parse cloth-mask agnostic-v3.2 agnostic-mask image-densepose
```

결과:

```text
manifest_count=9995
checked_count=100
missing_image=0
missing_cloth=0
missing_worn=0
missing_fit=0
image_load_errors=0
fit_json_errors=0
backend_loader_errors=0
artifact_errors=0
```

Artifact summary:

| artifact | required | checked | missing | load_errors |
| --- | --- | ---: | ---: | ---: |
| `openpose-json` | false | 100 | 100 | 0 |
| `image-parse` | false | 100 | 100 | 0 |
| `cloth-mask` | false | 100 | 100 | 0 |
| `agnostic-v3.2` | false | 100 | 100 | 0 |
| `agnostic-mask` | false | 100 | 100 | 0 |
| `image-densepose` | false | 100 | 100 | 0 |

Optional artifact missing은 실패로 처리하지 않는다.

Required artifact missing이 실패로 집계되는지도 `limit=1`로 확인했다.

```text
required_artifacts=["openpose-json"]
checked=1
missing=1
artifact_errors=1
exit_code=1
```

## 9. 새 Dataset 수신 후 Strict 검증 명령어

새 artifact dataset을 받은 뒤에는 densepose를 optional로 두고 나머지 artifact를 required로 검증한다.

```powershell
python backend\training\scripts\smoke_test_lora_dataset.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_artifacts `
  --limit 9995 `
  --sample-count 16 `
  --contact-sheet backend\training\outputs\lora_artifact_smoke\contact_sheet.jpg `
  --summary-json backend\training\outputs\lora_artifact_smoke\summary.json `
  --check-backend-loader `
  --required-artifacts openpose-json image-parse cloth-mask agnostic-v3.2 agnostic-mask `
  --optional-artifacts image-densepose
```

성공 기준:

```text
checked_count=9995
missing_image=0
missing_cloth=0
missing_worn=0
missing_fit=0
image_load_errors=0
fit_json_errors=0
backend_loader_errors=0
artifact_errors=0
```

`image-densepose` missing은 optional missing으로만 기록한다.

## 10. Git Safety Rule

다음 파일과 폴더는 Git에 포함하지 않는다.

- `backend/datasets/**`
- `backend/training/outputs/**`
- `backend/outputs/**`
- `backend/logs/**`
- `DATA/**`
- `samples_smoke/**`
- `stableviton_raw/**`
- `*.jpg`
- `*.jpeg`
- `*.png`
- `*.webp`
- `*.ckpt`
- `*.pth`
- `*.pt`
- `*.safetensors`
- `*.zip`
- `*.7z`

이번 PR에는 실제 dataset, output JSON, contact sheet, checkpoint, sample image를 포함하지 않는다.

## 11. 다음 단계

1. 새 artifact 10k dataset 다운로드
2. required artifact strict smoke test 실행
3. artifact missing/load error 확인
4. artifact 포함 10k DataLoader dry-run
5. 100 step training smoke
