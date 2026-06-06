# PC3 LoRA 1k training smoke 및 10k 시간 추정

## 1. 목적

이번 작업은 DensePose 포함 10k artifact patch를 기다리는 동안, 이미 검증 완료된 AIHub LoRA 1k pilot dataset으로 PC3 학습 파이프라인을 smoke test하는 것이다.

중요하게, 이번 작업은 실제 StableVITON LoRA fine-tuning이 아니다. `AihubLoraTorchDataset` 기반 pre-LoRA training smoke이며, 목표는 좋은 결과 이미지를 생성하는 것이 아니라 다음 흐름이 정상 동작하는지 확인하는 것이다.

```text
DataLoader -> GPU training loop -> loss 계산 -> checkpoint/sample/log 저장 -> 10k 예상 시간 계산
```

## 2. 입력 dataset

사용한 dataset root는 다음과 같다.

```text
backend/datasets/lora_pilot_aihub_1k
```

dataset 개수 확인 결과는 다음과 같다.

```text
image 1000
cloth 1000
worn 1000
fit 1000
manifest lines=1000
```

이 dataset은 로컬 검증용 데이터이며 Git에 포함하지 않는다.

## 3. 실행 환경

PC3 실행 환경은 다음과 같다.

```text
OS: Microsoft Windows NT 10.0.26200.0
Python: D:\conda-envs\vton\python.exe
Python version: 3.10.20
torch: 2.0.0+cu117
CUDA available: True
GPU: NVIDIA GeForce RTX 4080
D drive free: 216.89 GB
```

`nvidia-smi` 기준 주요 값은 다음과 같다.

```text
Driver Version: 591.86
CUDA Version: 13.1
GPU memory: 1019 MiB / 16376 MiB
```

## 4. Script 구조

추가한 script는 다음 파일이다.

```text
backend/training/scripts/train_lora_smoke.py
```

이 script는 기존 torch Dataset adapter를 재사용한다.

```python
from backend.training.datasets.aihub_lora_torch_dataset import AihubLoraTorchDataset
```

학습 smoke model은 실제 StableVITON이나 LoRA layer가 아니다. `person`과 `cloth` tensor를 channel 방향으로 concat한 뒤, 작은 CNN으로 `worn` target을 reconstruction하는 pre-LoRA pipeline smoke이다.

```text
input:  person [B, 3, H, W] + cloth [B, 3, H, W] -> [B, 6, H, W]
target: worn [B, 3, H, W]
loss:   L1 loss
```

기본 저장 항목은 다음과 같다.

- checkpoint: `checkpoints/checkpoint_step_XXXX.pt`
- sample image: `samples/sample_step_XXXX.jpg`
- summary: `train_summary.json`

## 5. 실행 명령

10-step quick smoke:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\train_lora_smoke.py `
  --data-root backend\datasets\lora_pilot_aihub_1k `
  --output-root backend\training\outputs\lora_1k_training_smoke_10step `
  --steps 10 `
  --batch-size 1 `
  --image-size 512 384 `
  --lr 1e-4 `
  --num-workers 0 `
  --save-every 10
```

100-step batch size 1:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\train_lora_smoke.py `
  --data-root backend\datasets\lora_pilot_aihub_1k `
  --output-root backend\training\outputs\lora_1k_training_smoke_100step_bs1 `
  --steps 100 `
  --batch-size 1 `
  --image-size 512 384 `
  --lr 1e-4 `
  --num-workers 0 `
  --save-every 50
```

100-step batch size 2:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\train_lora_smoke.py `
  --data-root backend\datasets\lora_pilot_aihub_1k `
  --output-root backend\training\outputs\lora_1k_training_smoke_100step_bs2 `
  --steps 100 `
  --batch-size 2 `
  --image-size 512 384 `
  --lr 1e-4 `
  --num-workers 0 `
  --save-every 50
```

500-step batch size 2:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\train_lora_smoke.py `
  --data-root backend\datasets\lora_pilot_aihub_1k `
  --output-root backend\training\outputs\lora_1k_training_smoke_500step_bs2 `
  --steps 500 `
  --batch-size 2 `
  --image-size 512 384 `
  --lr 1e-4 `
  --num-workers 0 `
  --save-every 100
```

## 6. 실행 결과

| run | steps_completed | batch_size | image_size | avg_step_time_sec | elapsed_sec | peak_vram_mb | first_loss | final_loss | loss_nan |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 10-step quick | 10 | 1 | 512 x 384 | 1.306214 | 13.0621 | 63.06 | 0.2199297696 | 0.2193625569 | False |
| 100-step bs1 | 100 | 1 | 512 x 384 | 0.350285 | 35.0285 | 63.06 | 0.2199297696 | 0.1868950129 | False |
| 100-step bs2 | 100 | 2 | 512 x 384 | 0.630775 | 63.0775 | 123.06 | 0.2177198231 | 0.1437589079 | False |
| 500-step bs2 | 500 | 2 | 512 x 384 | 0.667759 | 333.8794 | 123.06 | 0.2177198231 | 0.0803836212 | False |

모든 실행에서 다음 조건을 만족했다.

- loss NaN 없음
- requested steps 완료
- checkpoint 저장 확인
- sample image 저장 확인
- `train_summary.json` 저장 확인
- CUDA 사용 확인
- peak VRAM 기록 확인

## 7. Output 위치

10-step quick smoke output:

```text
backend/training/outputs/lora_1k_training_smoke_10step/checkpoints/checkpoint_step_0010.pt
backend/training/outputs/lora_1k_training_smoke_10step/samples/sample_step_0010.jpg
backend/training/outputs/lora_1k_training_smoke_10step/train_summary.json
```

100-step batch size 1 output:

```text
backend/training/outputs/lora_1k_training_smoke_100step_bs1/checkpoints/checkpoint_step_0050.pt
backend/training/outputs/lora_1k_training_smoke_100step_bs1/checkpoints/checkpoint_step_0100.pt
backend/training/outputs/lora_1k_training_smoke_100step_bs1/samples/sample_step_0050.jpg
backend/training/outputs/lora_1k_training_smoke_100step_bs1/samples/sample_step_0100.jpg
backend/training/outputs/lora_1k_training_smoke_100step_bs1/train_summary.json
```

100-step batch size 2 output:

```text
backend/training/outputs/lora_1k_training_smoke_100step_bs2/checkpoints/checkpoint_step_0050.pt
backend/training/outputs/lora_1k_training_smoke_100step_bs2/checkpoints/checkpoint_step_0100.pt
backend/training/outputs/lora_1k_training_smoke_100step_bs2/samples/sample_step_0050.jpg
backend/training/outputs/lora_1k_training_smoke_100step_bs2/samples/sample_step_0100.jpg
backend/training/outputs/lora_1k_training_smoke_100step_bs2/train_summary.json
```

500-step batch size 2 output:

```text
backend/training/outputs/lora_1k_training_smoke_500step_bs2/checkpoints/checkpoint_step_0100.pt
backend/training/outputs/lora_1k_training_smoke_500step_bs2/checkpoints/checkpoint_step_0200.pt
backend/training/outputs/lora_1k_training_smoke_500step_bs2/checkpoints/checkpoint_step_0300.pt
backend/training/outputs/lora_1k_training_smoke_500step_bs2/checkpoints/checkpoint_step_0400.pt
backend/training/outputs/lora_1k_training_smoke_500step_bs2/checkpoints/checkpoint_step_0500.pt
backend/training/outputs/lora_1k_training_smoke_500step_bs2/samples/sample_step_0100.jpg
backend/training/outputs/lora_1k_training_smoke_500step_bs2/samples/sample_step_0200.jpg
backend/training/outputs/lora_1k_training_smoke_500step_bs2/samples/sample_step_0300.jpg
backend/training/outputs/lora_1k_training_smoke_500step_bs2/samples/sample_step_0400.jpg
backend/training/outputs/lora_1k_training_smoke_500step_bs2/samples/sample_step_0500.jpg
backend/training/outputs/lora_1k_training_smoke_500step_bs2/train_summary.json
```

위 output은 모두 local generated artifact이며 Git에 포함하지 않는다.

## 8. 10k 시간 추정

10k sample 수는 현재 기준 `9995`로 가정했다.

계산식은 다음과 같다.

```text
steps_per_epoch = ceil(9995 / batch_size)
estimated_10k_epoch_time = steps_per_epoch * avg_step_time_sec
estimated_1000_step_time = 1000 * avg_step_time_sec
```

| 기준 run | batch_size | steps_per_10k_epoch | estimated_10k_epoch_time_min | estimated_1000_step_time_min |
| --- | ---: | ---: | ---: | ---: |
| 10-step quick | 1 | 9995 | 217.59 | 21.77 |
| 100-step bs1 | 1 | 9995 | 58.35 | 5.84 |
| 100-step bs2 | 2 | 4998 | 52.54 | 10.51 |
| 500-step bs2 | 2 | 4998 | 55.62 | 11.13 |

10-step quick run은 초기 CUDA warm-up과 파일 I/O 영향이 커서 시간 추정 기준으로는 보수적이다. 100-step 이상 결과가 더 참고할 만하다.

## 9. 검증

실행한 검증은 다음과 같다.

```powershell
git diff --check
python -m py_compile backend\training\scripts\train_lora_smoke.py
D:\conda-envs\vton\python.exe -m py_compile backend\training\scripts\train_lora_smoke.py
```

모두 통과했다.

추가로 네 개 smoke run의 `train_summary.json`을 읽어 다음을 확인했다.

- `steps_completed`가 요청 step과 일치
- `loss_nan=False`
- checkpoint 개수 확인
- sample image 개수 확인
- summary json 존재 확인
- 10k 예상 시간 기록 확인

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

```text
backend/training/scripts/train_lora_smoke.py
docs/experiments/pc3_lora_1k_training_smoke_time_estimate.md
```

dataset, checkpoint, sample image, summary json은 모두 local output으로만 보관한다.

## 11. 다음 단계

- DensePose 포함 10k artifact patch 수신
- strict artifact smoke 재실행
- 10k DataLoader dry-run 재실행
- 이번 script를 기준으로 10k pre-LoRA training smoke 확장
- 실제 StableVITON LoRA fine-tuning script는 별도 PR에서 구현
