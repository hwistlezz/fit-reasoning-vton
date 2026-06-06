# PC3 10k pre-LoRA training smoke

## 1. 목적

이번 작업은 현재 PC3에 준비된 10k dataset으로 pre-LoRA training smoke를 실행해 학습 파이프라인이 정상 동작하는지 확인하는 것이다.

중요하게, 이번 작업은 실제 StableVITON LoRA fine-tuning이 아니다. #82에서 추가된 `AihubLoraTorchDataset` 기반 smoke script를 10k dataset에 적용해 다음 항목을 검증했다.

- DataLoader 로딩
- GPU training loop
- L1 reconstruction loss 계산
- loss NaN 여부
- step time 측정
- peak VRAM 측정
- checkpoint 저장
- sample image 저장
- `train_summary.json` 저장

## 2. 입력 dataset

사용한 dataset root는 다음과 같다.

```text
backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full
```

이번 작업은 artifact strict smoke가 아니라 현재 10k dataset으로 training smoke만 수행한다. 따라서 `openpose-json`, `image-parse`, `cloth-mask`, `image-densepose` 누락은 이번 training smoke의 중단 조건으로 보지 않았다.

dataset 개수 확인 결과는 다음과 같다.

```text
root exists=True
image 9995
cloth 9995
worn 9995
fit 9995
agnostic-v3.2 9995
agnostic-mask 9995
openpose-json missing_dir
image-parse missing_dir
cloth-mask missing_dir
image-densepose missing_dir
manifest=9995
```

## 3. 실행 환경

실행 환경은 다음과 같다.

```text
OS: Microsoft Windows NT 10.0.26200.0
Python: D:\conda-envs\vton\python.exe
torch: 2.0.0+cu117
CUDA available: True
GPU: NVIDIA GeForce RTX 4080
D drive free: 216.89 GB
```

`nvidia-smi` 주요 값은 다음과 같다.

```text
Driver Version: 591.86
CUDA Version: 13.1
GPU memory: 911 MiB / 16376 MiB
```

## 4. 실행 명령

100-step batch size 2:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\train_lora_smoke.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full `
  --output-root backend\training\outputs\lora_10k_pre_lora_smoke_100step_bs2 `
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
  --data-root backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full `
  --output-root backend\training\outputs\lora_10k_pre_lora_smoke_500step_bs2 `
  --steps 500 `
  --batch-size 2 `
  --image-size 512 384 `
  --lr 1e-4 `
  --num-workers 0 `
  --save-every 100
```

## 5. 100-step 결과

100-step batch size 2 결과는 성공이다.

```text
steps_completed=100
batch_size=2
image_size=512 x 384
avg_step_time_sec=0.65239
elapsed_sec=65.239
peak_vram_mb=123.06
first_loss=0.1615839303
final_loss=0.1158259436
loss_nan=False
error=None
```

저장 확인:

```text
checkpoint count=2
sample count=2
train_summary.json=True
```

저장 위치:

```text
backend/training/outputs/lora_10k_pre_lora_smoke_100step_bs2/checkpoints/checkpoint_step_0050.pt
backend/training/outputs/lora_10k_pre_lora_smoke_100step_bs2/checkpoints/checkpoint_step_0100.pt
backend/training/outputs/lora_10k_pre_lora_smoke_100step_bs2/samples/sample_step_0050.jpg
backend/training/outputs/lora_10k_pre_lora_smoke_100step_bs2/samples/sample_step_0100.jpg
backend/training/outputs/lora_10k_pre_lora_smoke_100step_bs2/train_summary.json
```

10k 예상 시간:

```text
assumed_10k_sample_count=9995
steps_per_10k_epoch=4998
estimated_10k_epoch_time_sec=3260.65
estimated_10k_epoch_time_min=54.34
estimated_1000_step_time_sec=652.39
estimated_1000_step_time_min=10.87
```

## 6. 500-step 결과

500-step batch size 2 결과도 성공이다.

```text
steps_completed=500
batch_size=2
image_size=512 x 384
avg_step_time_sec=0.677244
elapsed_sec=338.6218
peak_vram_mb=123.06
first_loss=0.1615839303
final_loss=0.0936324373
loss_nan=False
error=None
```

저장 확인:

```text
checkpoint count=5
sample count=5
train_summary.json=True
```

저장 위치:

```text
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/checkpoints/checkpoint_step_0100.pt
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/checkpoints/checkpoint_step_0200.pt
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/checkpoints/checkpoint_step_0300.pt
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/checkpoints/checkpoint_step_0400.pt
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/checkpoints/checkpoint_step_0500.pt
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/samples/sample_step_0100.jpg
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/samples/sample_step_0200.jpg
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/samples/sample_step_0300.jpg
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/samples/sample_step_0400.jpg
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/samples/sample_step_0500.jpg
backend/training/outputs/lora_10k_pre_lora_smoke_500step_bs2/train_summary.json
```

10k 예상 시간:

```text
assumed_10k_sample_count=9995
steps_per_10k_epoch=4998
estimated_10k_epoch_time_sec=3384.87
estimated_10k_epoch_time_min=56.41
estimated_1000_step_time_sec=677.24
estimated_1000_step_time_min=11.29
```

## 7. #82 1k 결과와 비교

#82에서 같은 script로 1k pilot dataset을 검증한 결과와 비교하면 다음과 같다.

| dataset | run | steps | batch_size | avg_step_time_sec | elapsed_sec | peak_vram_mb | first_loss | final_loss | 10k epoch min |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1k pilot | 100-step bs2 | 100 | 2 | 0.630775 | 63.0775 | 123.06 | 0.2177198231 | 0.1437589079 | 52.54 |
| 10k agnostic | 100-step bs2 | 100 | 2 | 0.65239 | 65.239 | 123.06 | 0.1615839303 | 0.1158259436 | 54.34 |
| 1k pilot | 500-step bs2 | 500 | 2 | 0.667759 | 333.8794 | 123.06 | 0.2177198231 | 0.0803836212 | 55.62 |
| 10k agnostic | 500-step bs2 | 500 | 2 | 0.677244 | 338.6218 | 123.06 | 0.1615839303 | 0.0936324373 | 56.41 |

관찰:

- 10k dataset에서도 step time과 peak VRAM은 #82 1k 결과와 거의 같은 수준이다.
- batch size 2 기준 peak VRAM은 두 dataset 모두 `123.06 MB`로 기록됐다.
- 500-step 기준 10k 1 epoch 예상 시간은 약 `56.41분`이다.
- 이번 수치는 작은 CNN 기반 pre-LoRA smoke observation이며 실제 StableVITON LoRA 학습 시간으로 해석하면 안 된다.

## 8. 한계점

- 실제 StableVITON LoRA fine-tuning은 수행하지 않았다.
- 이번 smoke model은 작은 CNN reconstruction model이다.
- `openpose-json`, `image-parse`, `cloth-mask`, `image-densepose`는 현재 dataset에 없다.
- sample image는 품질 평가 목적이 아니라 저장 경로와 pipeline 검증 목적이다.
- `num_workers=0` 기준 결과라 worker 수를 늘렸을 때의 I/O 성능은 별도 확인이 필요하다.

## 9. Git safety

이번 실행에서 생성된 dataset/output/checkpoint/sample image는 Git에 포함하지 않는다.

금지 대상:

```text
backend/datasets/**
backend/training/outputs/**
backend/outputs/**
backend/logs/**
*.jpg
*.jpeg
*.png
*.webp
*.ckpt
*.pth
*.pt
*.safetensors
*.zip
*.7z
```

이번 PR에는 문서만 포함한다.

```text
docs/experiments/pc3_lora_10k_pre_lora_training_smoke.md
```

## 10. 다음 단계

- DensePose patch 수신
- `openpose-json`, `image-parse`, `cloth-mask`, `image-densepose` 포함 여부 확인
- strict artifact smoke 재실행
- artifact 포함 10k DataLoader dry-run
- 실제 StableVITON LoRA fine-tuning script는 별도 PR에서 구현
