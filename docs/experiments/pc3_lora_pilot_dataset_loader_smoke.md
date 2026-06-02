# PC3 LoRA Pilot Dataset Loader Smoke Test

## 1. 목적

PC2에서 전달한 AIHub 기반 `lora_pilot_aihub_1k` pilot dataset을 PC3 환경에서 안정적으로 읽을 수 있는지 검증한다.

이번 작업은 실제 LoRA 학습이 아니라, `manifest.jsonl`과 `image`, `cloth`, `worn`, `fit` 파일을 loader가 정상적으로 읽고 backend fit analyzer loader와 호환되는지 확인하는 단계다.

## 2. PC3 데이터 위치

PC3 로컬 데이터 위치는 다음과 같다.

```text
backend/datasets/lora_pilot_aihub_1k
```

압축 파일 `lora_pilot_aihub_1k.zip`과 압축 해제된 실제 데이터는 Git에 포함하지 않는다.

## 3. 데이터 구조

```text
backend/datasets/lora_pilot_aihub_1k/
  image/
    *.jpg
  cloth/
    *.jpg
  worn/
    *.jpg
  fit/
    *.json
  manifest.jsonl
```

- `image/`: 모델/person 이미지
- `cloth/`: 제품 의류 이미지
- `worn/`: 모델이 해당 의류를 착용한 정답 이미지
- `fit/`: PC2에서 계산한 fit feature 및 hotspot annotation JSON
- `manifest.jsonl`: smoke test와 이후 학습 코드가 읽을 sample 목록

정상 기준은 `image`, `cloth`, `worn`, `fit` 각각 1,000개와 `manifest.jsonl` 1,000줄이다.

## 4. Loader 설계

`AihubLoraPilotDataset`은 torch에 의존하지 않는 Python loader다. backend 환경에 torch가 없을 수 있으므로, 이번 단계에서는 `torch.utils.data.Dataset`을 상속하지 않는다.

manifest 내부의 `image`, `cloth`, `worn`, `fit_json` 경로는 PC2 원본 경로일 수 있다. 따라서 loader는 manifest 경로를 그대로 믿지 않고 `pair_id` 기준으로 PC3 로컬 경로를 재조립한다.

```text
backend/datasets/lora_pilot_aihub_1k/image/{pair_id}.jpg
backend/datasets/lora_pilot_aihub_1k/cloth/{pair_id}.jpg
backend/datasets/lora_pilot_aihub_1k/worn/{pair_id}.jpg
backend/datasets/lora_pilot_aihub_1k/fit/{pair_id}.json
```

`load_sample(index)`는 `image`, `cloth`, `worn` 이미지를 `RGB`로 변환해 로드하고, `fit` JSON을 parse한다.

## 5. Smoke Test 실행 명령어

```powershell
python backend\training\scripts\smoke_test_lora_dataset.py `
  --data-root backend\datasets\lora_pilot_aihub_1k `
  --limit 1000 `
  --sample-count 16 `
  --contact-sheet backend\training\outputs\lora_pilot_1k\contact_sheet.jpg `
  --summary-json backend\training\outputs\lora_pilot_1k\dataset_smoke_summary.json `
  --check-backend-loader
```

`--check-backend-loader`를 켜면 각 `fit` JSON에 대해 `backend.app.services.fit_analyzer.analyze_fit` 호출을 추가로 확인한다.

## 6. 성공 기준

- `manifest_count=1000`
- `checked_count=1000`
- `missing_image=0`
- `missing_cloth=0`
- `missing_worn=0`
- `missing_fit=0`
- `image_load_errors=0`
- `fit_json_errors=0`
- `backend_loader_errors=0`
- contact sheet 생성
- summary JSON 생성

## 7. Generated Output 위치

Smoke test 결과물은 다음 위치에 생성한다.

```text
backend/training/outputs/lora_pilot_1k/contact_sheet.jpg
backend/training/outputs/lora_pilot_1k/dataset_smoke_summary.json
```

이 파일들은 실험 산출물이며 Git에 포함하지 않는다.

## 8. Git Safety Rule

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

이번 PR에는 실제 AIHub 데이터, `lora_pilot_aihub_1k.zip`, 압축 해제된 이미지, contact sheet, summary JSON, checkpoint를 포함하지 않는다.

## 9. 다음 단계

- PC3 LoRA 학습 코드에서 사용할 torch Dataset adapter 추가
- StableVITON 또는 후속 training runner 입력 format과 연결
- 작은 subset 기준 LoRA smoke training 수행
- checkpoint, sample image, training log는 local-only output으로 관리
