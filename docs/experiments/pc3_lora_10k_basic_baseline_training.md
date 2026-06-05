# PC3 10k Basic Baseline training pilot

## 1. 목적

이번 작업은 PC3에 준비된 AIHub 10k basic dataset으로 10k Basic Baseline training pilot을 수행하고, 이후 10k Artifact-enhanced Model과 비교할 기준 실행 결과를 남기는 것이다.

이 문서의 결과는 실제 StableVITON LoRA fine-tuning 완료 결과가 아니다. 현재 실행은 `AihubLoraTorchDataset` 기반의 training smoke 계열 baseline이며, 발표용 비교 구조에서 다음 위치를 담당할 후보 결과를 만들기 위한 사전 pilot이다.

```text
Target Worn / 10k Basic Baseline / 10k Artifact-enhanced Model
```

## 2. baseline이 필요한 이유

Artifact-enhanced dataset이 도착한 뒤 결과를 바로 비교하려면, artifact를 학습 조건으로 쓰지 않은 basic baseline이 먼저 필요하다.

이번 baseline은 사람 이미지, 의류 이미지, 착용 정답 이미지 중심으로 학습 loop, checkpoint 저장, sample 저장, loss NaN 여부, step time, peak VRAM을 확인하는 실행이다. 따라서 결과 해석은 모델 품질 평가가 아니라 동일 training smoke 계열에서 basic 기준 run을 확보했다는 의미로 제한한다.

## 3. 사용 dataset root

우선순위 1번 dataset이 존재해서 아래 경로를 사용했다.

```text
backend/datasets/lora_pilot_aihub_10k_full
```

fallback dataset도 존재했지만 사용하지 않았다.

```text
backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full
```

`lora_pilot_aihub_10k_full`은 #74에서 known-bad 4개 pair를 제외한 filtered manifest 기준으로 smoke test를 통과한 dataset이다. 폴더 안에는 원본 파일 9999개가 남아 있지만, loader는 `manifest.jsonl`의 9995개 pair를 기준으로 읽는다.

데이터 개수 확인 결과:

```text
root=backend/datasets/lora_pilot_aihub_10k_full
exists=True
image=9999
cloth=9999
worn=9999
fit=9999
agnostic-v3.2=missing_dir
agnostic-mask=missing_dir
manifest lines=9995
```

이번 baseline training에서는 artifact를 학습 조건으로 사용하지 않았다.

## 4. 실행 환경

실행 환경:

```text
OS: Windows 10.0.26200
Python: D:\conda-envs\vton\python.exe
torch: 2.0.0+cu117
CUDA available: True
GPU: NVIDIA GeForce RTX 4080
Driver Version: 591.86
CUDA Version shown by nvidia-smi: 13.1
GPU memory: 16376 MiB
```

## 5. 실행 명령어

100-step:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\train_lora_smoke.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_full `
  --output-root backend\training\outputs\lora_10k_basic_baseline_100step_bs2 `
  --steps 100 `
  --batch-size 2 `
  --image-size 512 384 `
  --lr 1e-4 `
  --num-workers 0 `
  --save-every 50
```

500-step:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\train_lora_smoke.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_full `
  --output-root backend\training\outputs\lora_10k_basic_baseline_500step_bs2 `
  --steps 500 `
  --batch-size 2 `
  --image-size 512 384 `
  --lr 1e-4 `
  --num-workers 0 `
  --save-every 100
```

1000-step:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\train_lora_smoke.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_full `
  --output-root backend\training\outputs\lora_10k_basic_baseline_1000step_bs2 `
  --steps 1000 `
  --batch-size 2 `
  --image-size 512 384 `
  --lr 1e-4 `
  --num-workers 0 `
  --save-every 200
```

## 6. 100-step 결과

100-step batch size 2 run은 성공했다.

```text
steps_completed=100
batch_size=2
image_size=512 x 384
avg_step_time_sec=0.712904
elapsed_sec=71.2904
peak_vram_mb=123.06
first_loss=0.1615839303
final_loss=0.1158259735
loss_nan=False
error=None
checkpoint count=2
sample count=2
train_summary.json=True
```

저장 위치:

```text
backend/training/outputs/lora_10k_basic_baseline_100step_bs2/checkpoints/
backend/training/outputs/lora_10k_basic_baseline_100step_bs2/samples/
backend/training/outputs/lora_10k_basic_baseline_100step_bs2/train_summary.json
```

## 7. 500-step 결과

500-step batch size 2 run은 성공했다.

```text
steps_completed=500
batch_size=2
image_size=512 x 384
avg_step_time_sec=0.694542
elapsed_sec=347.2711
peak_vram_mb=123.06
first_loss=0.1615839303
final_loss=0.0936279818
loss_nan=False
error=None
checkpoint count=5
sample count=5
train_summary.json=True
```

저장 위치:

```text
backend/training/outputs/lora_10k_basic_baseline_500step_bs2/checkpoints/
backend/training/outputs/lora_10k_basic_baseline_500step_bs2/samples/
backend/training/outputs/lora_10k_basic_baseline_500step_bs2/train_summary.json
```

## 8. 1000-step 결과

500-step run이 성공했고 시간이 충분해서 1000-step batch size 2 run도 수행했다. 1000-step run은 성공했다.

```text
steps_completed=1000
batch_size=2
image_size=512 x 384
avg_step_time_sec=0.614585
elapsed_sec=614.585
peak_vram_mb=123.06
first_loss=0.1615839303
final_loss=0.0654512644
loss_nan=False
error=None
checkpoint count=5
sample count=5
train_summary.json=True
```

저장 위치:

```text
backend/training/outputs/lora_10k_basic_baseline_1000step_bs2/checkpoints/
backend/training/outputs/lora_10k_basic_baseline_1000step_bs2/samples/
backend/training/outputs/lora_10k_basic_baseline_1000step_bs2/train_summary.json
```

## 9. #84 10k pre-LoRA 500-step 결과와 비교

아래 비교는 실제 StableVITON LoRA 성능 비교가 아니다. 같은 `train_lora_smoke.py` 계열의 training smoke 결과끼리 step time, VRAM, loss 기록을 비교한 것이다.

| run | dataset root | steps | batch size | avg_step_time_sec | elapsed_sec | peak_vram_mb | first_loss | final_loss | loss_nan |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| #84 10k pre-LoRA smoke | `backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full` | 500 | 2 | 0.677244 | 338.6218 | 123.06 | 0.1615839303 | 0.0936324373 | False |
| #96 10k Basic Baseline | `backend/datasets/lora_pilot_aihub_10k_full` | 500 | 2 | 0.694542 | 347.2711 | 123.06 | 0.1615839303 | 0.0936279818 | False |

관찰:

- 두 run 모두 batch size 2, image size 512 x 384, `num_workers=0` 기준이다.
- peak VRAM은 두 run 모두 `123.06 MB`로 기록됐다.
- 500-step 기준 `loss_nan=False`이며, error는 없었다.
- #96 10k Basic Baseline 500-step의 평균 step time은 #84 10k pre-LoRA smoke보다 약간 느리지만 같은 smoke 계열의 범위로 볼 수 있다.

## 10. 현재 한계

- 이번 작업은 실제 StableVITON LoRA fine-tuning이 아니다.
- 이번 작업은 artifact 조건을 사용하지 않은 10k Basic Baseline training pilot이다.
- `agnostic-v3.2`, `agnostic-mask`, `openpose-json`, `image-parse`, `cloth-mask`, `image-densepose`는 이번 baseline 학습 조건으로 사용하지 않았다.
- 저장된 checkpoint와 sample 이미지는 training smoke 산출물이며, 품질 평가 또는 최종 모델 산출물로 해석하면 안 된다.
- checkpoint, sample, `train_summary.json`은 `backend/training/outputs/**` 아래에만 생성했고 Git에는 포함하지 않는다.

## 11. 다음 단계

- DensePose 포함 artifact patch 수신 후 artifact dataset readiness를 다시 확인한다.
- 같은 script 계열에서 10k Artifact-enhanced Model training pilot을 수행한다.
- 같은 test pair를 기준으로 Target Worn, 10k Basic Baseline, 10k Artifact-enhanced Model demo asset을 생성한다.
- 발표용 비교 API의 `backend/demo/assets/**` asset contract에 맞춰 실제 이미지를 배치하기 전 validation script로 누락 여부를 확인한다.
