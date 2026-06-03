# PC3 LoRA DataLoader dry-run 및 VRAM check

## 1. 목적

이번 작업의 목적은 PC2가 생성한 AIHub LoRA 10k filtered dataset을 실제 학습 전에 PyTorch `DataLoader`로 읽어 보고, batch 입력 구성이 정상인지 확인하는 것이다.

이번 단계에서는 실제 LoRA 학습, loss 계산, checkpoint 저장을 수행하지 않는다.

확인 대상은 다음과 같다.

- `image`, `cloth`, `worn` 이미지를 tensor로 변환
- `fit_label`, `confidence`, `prompt`, `pair_id` metadata 유지
- batch size 1 / 2 dry-run
- CUDA 사용 가능 여부 확인
- peak VRAM 기록
- batch loading time 기록
- summary json 생성

## 2. 입력 dataset

PC3 기준 입력 dataset 위치는 다음과 같다.

```text
backend/datasets/lora_pilot_aihub_10k_full
```

이 dataset은 Git에 포함하지 않는 로컬 데이터이다.

## 3. 기존 #74 filtered dataset 상태

#74에서 확인한 상태는 다음과 같다.

- 원본 manifest sample 수: 9999
- known-bad sample 수: 4
- filtered manifest sample 수: 9995
- filtered smoke test: 성공
- `missing_image=0`
- `missing_cloth=0`
- `missing_worn=0`
- `missing_fit=0`
- `image_load_errors=0`
- `fit_json_errors=0`
- `backend_loader_errors=0`

known-bad pair는 다음 네 개이다.

```text
EP00003620
EP00003937
EP00005080
EP00007279
```

현재 `manifest.raw_9999.jsonl`은 원본 manifest 백업이고, `manifest.jsonl`은 known-bad 4개를 제외한 filtered manifest이다.

## 4. Dataset adapter 구조

새 adapter는 다음 파일에 구현한다.

```text
backend/training/datasets/aihub_lora_torch_dataset.py
```

`AihubLoraTorchDataset`는 기존 torch-free loader를 재사용한다.

```python
from backend.training.datasets.aihub_lora_dataset import AihubLoraPilotDataset
```

역할 분리는 다음과 같다.

- `AihubLoraPilotDataset`: manifest 읽기, `pair_id` 기준 로컬 경로 재조립, metadata 유지
- `AihubLoraTorchDataset`: PIL RGB image 로드, resize, torch tensor 변환
- `dataloader_dry_run.py`: `Subset`, `DataLoader`, CUDA 이동, timing, VRAM 기록

반환 sample 구조는 다음과 같다.

```python
{
    "pair_id": str,
    "person": torch.Tensor,
    "cloth": torch.Tensor,
    "target": torch.Tensor,
    "fit_label": str,
    "confidence": float,
    "prompt": str,
}
```

기본 image size는 다음과 같다.

```text
height = 512
width = 384
```

따라서 단일 sample tensor shape은 다음과 같다.

```text
[3, 512, 384]
```

정규화는 현재 `[0, 1]` 범위를 사용한다.

```python
image_tensor.float() / 255.0
```

StableVITON 또는 diffusion 학습에서 `[-1, 1]` 정규화가 필요하면 별도 training PR에서 변경한다.

## 5. DataLoader dry-run 실행 명령어

기본 dry-run 명령은 다음과 같다.

```powershell
python backend\training\scripts\dataloader_dry_run.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_full `
  --limit 512 `
  --batch-sizes 1 2 `
  --num-workers 0 `
  --image-height 512 `
  --image-width 384 `
  --summary-json backend\training\outputs\lora_dataloader_dry_run\summary.json `
  --device cuda
```

CUDA가 없으면 script는 실패하지 않고 CPU dry-run으로 전환한다.

현재 PC3에서는 기본 `python` 환경에 `torch`가 없어서 검증 시 `D:\conda-envs\vton\python.exe`를 사용했다.

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\dataloader_dry_run.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_full `
  --limit 512 `
  --batch-sizes 1 2 `
  --num-workers 0 `
  --image-height 512 `
  --image-width 384 `
  --summary-json backend\training\outputs\lora_dataloader_dry_run\summary.json `
  --device cuda
```

## 6. Batch size 1/2 검증 기준

batch size 1의 첫 batch shape은 다음을 기대한다.

```text
person: [1, 3, 512, 384]
cloth:  [1, 3, 512, 384]
target: [1, 3, 512, 384]
```

batch size 2의 첫 batch shape은 다음을 기대한다.

```text
person: [2, 3, 512, 384]
cloth:  [2, 3, 512, 384]
target: [2, 3, 512, 384]
```

각 batch는 다음 metadata를 유지해야 한다.

- `pair_id`
- `fit_label`
- `confidence`
- `prompt`

## 7. VRAM 기록 기준

CUDA가 사용 가능하면 batch tensor를 GPU로 이동하고 다음 값을 기록한다.

- `cuda_available`
- `device_name`
- `peak_vram_mb`
- `elapsed_seconds`
- `avg_batch_seconds`

사용 API는 다음과 같다.

```python
torch.cuda.reset_peak_memory_stats()
torch.cuda.max_memory_allocated()
torch.cuda.get_device_name(0)
```

CUDA가 없으면 `device=cpu`로 기록하고 `peak_vram_mb=0.0`으로 둔다.

## 8. Generated output 위치

summary json은 다음 위치에 생성한다.

```text
backend/training/outputs/lora_dataloader_dry_run/summary.json
```

이 파일은 local generated output이며 Git에 포함하지 않는다.

## 9. 현재 PC3 dry-run 결과

2026-06-03 기준 PC3 `vton` conda 환경에서 확인한 결과는 다음과 같다.

- Python: `D:\conda-envs\vton\python.exe`
- torch: `2.0.0+cu117`
- CUDA 사용 가능: `true`
- GPU: `NVIDIA GeForce RTX 4080`
- dataset root: `backend/datasets/lora_pilot_aihub_10k_full`
- manifest count: 9995
- checked count: 512
- image size: `512 x 384`
- summary json: `backend/training/outputs/lora_dataloader_dry_run/summary.json`

batch size 1 결과는 다음과 같다.

- num batches: 512
- checked samples: 512
- first batch person shape: `[1, 3, 512, 384]`
- first batch cloth shape: `[1, 3, 512, 384]`
- first batch target shape: `[1, 3, 512, 384]`
- peak VRAM: `6.75 MB`
- elapsed seconds: `433.4711`
- avg batch seconds: `0.846623`

batch size 2 결과는 다음과 같다.

- num batches: 256
- checked samples: 512
- first batch person shape: `[2, 3, 512, 384]`
- first batch cloth shape: `[2, 3, 512, 384]`
- first batch target shape: `[2, 3, 512, 384]`
- peak VRAM: `13.5 MB`
- elapsed seconds: `207.656`
- avg batch seconds: `0.811156`

## 10. Git safety rule

아래 파일과 폴더는 Git에 포함하지 않는다.

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

이번 PR에 포함되는 파일은 보통 다음 세 개이다.

```text
backend/training/datasets/aihub_lora_torch_dataset.py
backend/training/scripts/dataloader_dry_run.py
docs/experiments/pc3_lora_dataloader_dry_run.md
```

dataset, image, archive, summary json, checkpoint는 포함하지 않는다.

## 11. 다음 단계

- artifact dataset strict smoke test
- batch size 1 / 2 / 4 확장 검증
- 100 step LoRA training smoke
- 500 step LoRA training smoke
