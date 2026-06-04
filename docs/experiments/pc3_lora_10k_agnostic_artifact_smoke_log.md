# PC3 LoRA 10k agnostic artifact smoke log

## 1. 목적

PC2에서 전달한 10k agnostic artifact dataset을 PC3에서 검증하고, 학습 전 단계의 DataLoader dry-run 가능 여부를 확인한다.

이번 검증의 기준 dataset root는 다음과 같다.

```text
backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full
```

이번 단계는 실제 StableVITON LoRA 학습이 아니다. strict artifact smoke와 DataLoader dry-run을 먼저 확인하고, 두 단계가 모두 성공하면 작은 torch reconstruction model 기반 100-step pre-LoRA training smoke로 넘어가는 흐름이다.

## 2. 환경

PC3 환경 확인 결과는 다음과 같다.

```text
torch 2.0.0+cu117
cuda_available True
GPU NVIDIA GeForce RTX 4080
```

`nvidia-smi` 기준 GPU 상태는 다음과 같았다.

```text
Driver Version: 591.86
CUDA Version: 13.1
GPU: NVIDIA GeForce RTX 4080
Memory: 911 MiB / 16376 MiB
```

검증에 사용한 Python은 다음과 같다.

```text
D:\conda-envs\vton\python.exe
```

## 3. Dataset 수신 및 배치

incoming zip 위치는 다음과 같다.

```text
backend/datasets/incoming_10k_agnostic/lora_pilot_aihub_10k_agnostic_v3_full.zip
```

zip 검증 결과는 다음과 같다.

```text
exists=True
size_gib=83.61
bad_file=None
num_files=59971
```

zip 내부에는 최상위 폴더가 한 번 더 포함되어 있었다.

```text
lora_pilot_aihub_10k_agnostic_v3_full/manifest.jsonl
lora_pilot_aihub_10k_agnostic_v3_full/agnostic-mask/...
```

따라서 nested directory의 내용을 목표 dataset root로 한 단계 올렸다.

## 4. Artifact 개수 확인

최종 dataset root 기준 개수는 다음과 같다.

```text
root=backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full exists=True
image 9995
cloth 9995
worn 9995
fit 9995
openpose-json missing_dir
image-parse missing_dir
cloth-mask missing_dir
agnostic-v3.2 9995
agnostic-mask 9995
image-densepose missing_dir
manifest lines=9995
```

이번 전달본에는 `agnostic-v3.2`와 `agnostic-mask`는 포함되어 있지만, strict artifact smoke에서 required로 지정한 `openpose-json`, `image-parse`, `cloth-mask`는 포함되어 있지 않다.

`agnostic-mask` 파일명은 다음 형태였다.

```text
agnostic-mask/EP00000000_mask.png
```

기존 smoke helper는 `agnostic-mask/{pair_id}.png`만 확인했기 때문에, 실제 전달본과 호환되도록 `agnostic-mask/{pair_id}_mask.png` fallback을 추가했다.

## 5. Strict artifact smoke

실행 명령은 다음과 같다.

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\smoke_test_lora_dataset.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full `
  --limit 9995 `
  --sample-count 16 `
  --contact-sheet backend\training\outputs\lora_10k_agnostic_artifact_smoke\contact_sheet.jpg `
  --summary-json backend\training\outputs\lora_10k_agnostic_artifact_smoke\dataset_smoke_summary.json `
  --check-backend-loader `
  --required-artifacts openpose-json image-parse cloth-mask agnostic-v3.2 agnostic-mask `
  --optional-artifacts image-densepose
```

결과는 실패이다.

기본 dataset 검증 결과는 모두 통과했다.

```text
manifest_count=9995
checked_count=9995
missing_image=0
missing_cloth=0
missing_worn=0
missing_fit=0
image_load_errors=0
fit_json_errors=0
backend_loader_errors=0
metadata_errors=0
contact_sheet_errors=0
```

artifact 검증 결과는 다음과 같다.

```text
openpose-json: checked=9995, missing=9995, load_errors=0, required=True
image-parse: checked=9995, missing=9995, load_errors=0, required=True
cloth-mask: checked=9995, missing=9995, load_errors=0, required=True
agnostic-v3.2: checked=9995, missing=0, load_errors=0, required=True
agnostic-mask: checked=9995, missing=0, load_errors=0, required=True
image-densepose: checked=9995, missing=9995, load_errors=0, required=False
artifact_errors=29985
```

`image-densepose`는 optional이므로 missing이어도 실패 원인으로 보지 않는다.

실패 원인은 required artifact인 다음 세 디렉터리가 누락된 것이다.

```text
openpose-json
image-parse
cloth-mask
```

## 6. DataLoader dry-run

strict artifact smoke는 실패했지만, 기본 image / cloth / worn / fit과 manifest는 정상이라 학습 전 batch 구성 가능 여부를 별도로 확인했다.

실행 명령은 다음과 같다.

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\dataloader_dry_run.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full `
  --limit 512 `
  --batch-size 2 `
  --image-size 512 384 `
  --summary-json backend\training\outputs\lora_10k_agnostic_dataloader_dry_run\summary.json
```

결과는 성공이다.

```text
manifest_count=9995
checked_count=512
errors=0
device=cuda
cuda_available=True
device_name=NVIDIA GeForce RTX 4080
```

batch size 2 결과는 다음과 같다.

```text
num_batches=256
checked_samples=512
person_shape=[2, 3, 512, 384]
cloth_shape=[2, 3, 512, 384]
target_shape=[2, 3, 512, 384]
peak_vram_mb=13.5
elapsed_seconds=178.8019
avg_batch_seconds=0.698445
```

첫 batch metadata는 다음처럼 유지됐다.

```text
pair_id=EP00000000
fit_label=slightly_oversized
confidence=76.36
prompt=virtual try-on clothing fit, slightly_oversized, agnostic body input, confidence 76.4
```

## 7. 100-step pre-LoRA training smoke 여부

100-step pre-LoRA training smoke는 수행하지 않았다.

이유는 strict artifact smoke가 required artifact 누락으로 실패했기 때문이다. 이번 training smoke는 실제 StableVITON LoRA 학습은 아니지만, #80 기준에서는 artifact smoke와 DataLoader dry-run이 모두 성공한 뒤 진행하는 단계로 둔다.

따라서 다음 output은 생성하지 않았다.

```text
backend/training/outputs/lora_10k_agnostic_training_smoke/checkpoint
backend/training/outputs/lora_10k_agnostic_training_smoke/sample
backend/training/outputs/lora_10k_agnostic_training_smoke/train_summary.json
```

## 8. 코드 보정 사항

이번 검증에서 받은 dataset과 기존 script의 인터페이스 차이를 줄이기 위해 다음을 보정했다.

- `agnostic-mask/{pair_id}_mask.png` artifact fallback 추가
- `dataloader_dry_run.py`에 `--batch-size` alias 추가
- `dataloader_dry_run.py`에 `--image-size HEIGHT WIDTH` alias 추가

기존 `--batch-sizes`, `--image-height`, `--image-width` 인자도 유지한다.

## 9. Generated output 위치

이번 검증에서 생성된 output은 다음 위치에 있다.

```text
backend/training/outputs/lora_10k_agnostic_artifact_smoke/contact_sheet.jpg
backend/training/outputs/lora_10k_agnostic_artifact_smoke/dataset_smoke_summary.json
backend/training/outputs/lora_10k_agnostic_dataloader_dry_run/summary.json
```

이 파일들은 모두 local generated output이며 Git에 포함하지 않는다.

## 10. Git safety

아래 항목은 Git에 포함하지 않는다.

```text
backend/datasets/**
backend/training/outputs/**
backend/outputs/**
backend/logs/**
DATA/**
samples_smoke/**
stableviton_raw/**
*.jpg
*.jpeg
*.png
*.webp
*.zip
*.7z
*.ckpt
*.pth
*.pt
*.safetensors
```

이번 PR에는 코드와 문서만 포함한다.

## 11. 다음 시도 제안

PC2에서 다음 artifact를 포함한 dataset을 다시 전달해야 strict artifact smoke가 통과할 수 있다.

```text
openpose-json/{pair_id}_keypoints.json
image-parse/{pair_id}.png
cloth-mask/{pair_id}.png
```

새 전달본을 받은 뒤에는 다음 순서로 다시 진행한다.

1. zip 무결성 검사
2. root 중첩 여부 확인 및 정리
3. artifact 개수 확인
4. strict artifact smoke 재실행
5. DataLoader dry-run 재실행
6. 100-step pre-LoRA training smoke 실행
