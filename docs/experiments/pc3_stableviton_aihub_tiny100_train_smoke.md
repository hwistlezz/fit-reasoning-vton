# PC3 StableVITON AIHub tiny train smoke

## 1. 목적

이번 작업은 PC3에서 준비한 AIHub 기반 StableVITON layout dataset을 외부 StableVITON repo의 `train.py` 계열 학습 루프가 실제로 읽고, CUDA에서 최소 1 train step까지 진입할 수 있는지 확인하는 compatibility smoke다.

이번 작업은 LoRA fine-tuning이 아니다. 정확한 성격은 다음 중 앞 단계에 해당한다.

```text
StableVITON train.py compatibility smoke
StableVITON full fine-tuning tiny smoke
```

## 2. #91 / PR #101 결과와의 차이

#91 / PR #101에서는 다음이 완료됐다.

- 10k full artifact dataset 준비
- strict artifact smoke 성공
- StableVITON layout dry-run 성공
- tiny100 layout copy 성공
- `train_lora_smoke.py` 기반 100/500-step training pilot 성공

하지만 `train_lora_smoke.py`는 실제 StableVITON 원본 `train.py` 학습이 아니다. 이번 #102 작업은 외부 StableVITON repo의 `train.py` 구조를 실제로 호출해 dataset, checkpoint, CUDA, training loop compatibility를 확인했다.

## 3. 경로

우리 repo:

```text
D:\GitHub\fit-reasoning-vton
```

외부 StableVITON repo:

```text
D:\GitHub\StableVITON
```

기존 tiny100 layout:

```text
D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_tiny100
```

이번 smoke에서 사용한 tiny10 layout:

```text
D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_tiny10
```

시간 제한 때문에 tiny100 전체가 아니라 tiny10을 사용했다.

## 4. tiny10 layout 준비 결과

실행 명령:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\prepare_stableviton_layout.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full `
  --output-root backend\datasets\stableviton_aihub_10k_layout_tiny10 `
  --limit 10 `
  --mode copy `
  --require-densepose `
  --summary-json backend\training\outputs\stableviton_layout_prepare_tiny10\summary.json
```

summary:

```text
mode=copy
total_manifest=9995
selected_count=10
train_count=9
test_count=1
ready_train_count=9
ready_test_count=1
ready_count=10
not_ready_count=0
require_densepose=True
copied_count=10
missing_counts all 0
```

pair file:

```text
train_pairs.txt count=9
test_pairs.txt count=1
pair format={pair_id}.jpg {pair_id}.jpg
```

train/test artifact count:

```text
train/image=9
train/cloth=9
train/cloth-mask=9
train/agnostic-v3.2=9
train/agnostic-mask=9
train/image-parse=9
train/image-densepose=9
train/openpose-json=9
train/worn=9
train/fit=9

test/image=1
test/cloth=1
test/cloth-mask=1
test/agnostic-v3.2=1
test/agnostic-mask=1
test/image-parse=1
test/image-densepose=1
test/openpose-json=1
test/worn=1
test/fit=1
```

## 5. StableVITON train.py / config 조사 결과

외부 repo 상태:

```text
repo=D:\GitHub\StableVITON
branch=master
train.py exists=True
torch=2.0.0+cu117
cuda=True
gpu=NVIDIA GeForce RTX 4080
```

`train.py --help`에서 확인한 주요 옵션:

```text
--config_name
--data_root_dir
--batch_size
--max_epochs
--save_root_dir
--save_name
--valid_epoch_freq
--save_every_n_epochs
--logger_freq
--precision
--num_sanity_val_steps
--resume_path
--vae_load_path
--use_validation
```

주의할 점:

- `train.py`는 `--max_steps`를 제공하지 않는다.
- step 수를 직접 제한하려면 코드 수정 또는 runtime wrapper가 필요하다.
- 기본 config path는 `./configs/{config_name}.yaml`이다.
- `configs/VITONHD.yaml`은 `dataset_name: VITONHDDataset`를 사용한다.
- `resume_path` 기본값은 `./ckpts/VITONHD_PBE_pose.ckpt`이다.
- `vae_load_path` 기본값은 `./ckpts/VITONHD_VAE_finetuning.ckpt`이다.

`VITONHDDataset`가 기대하는 구조:

```text
{data_root_dir}/train_pairs.txt
{data_root_dir}/test_pairs.txt
{data_root_dir}/train/image/{pair_id}.jpg
{data_root_dir}/train/cloth/{pair_id}.jpg
{data_root_dir}/train/cloth-mask/{pair_id}.jpg
{data_root_dir}/train/agnostic-v3.2/{pair_id}.jpg
{data_root_dir}/train/agnostic-mask/{pair_id}_mask.png
{data_root_dir}/train/image-densepose/{pair_id}.jpg
{data_root_dir}/train/gt_cloth_warped_mask/{pair_id}.jpg
```

train split에서는 `gt_cloth_warped_mask`가 필요하다. tiny10 layout 생성 script는 이 폴더를 기본 생성하지 않으므로, 이번 smoke에서는 ignored dataset 안에서 `train/cloth-mask`를 `train/gt_cloth_warped_mask`로 복사한 smoke-only 대체 mask를 사용했다.

또한 StableVITON dataset transform은 Albumentations shape check를 수행한다. tiny10의 원본 person/cloth/mask/densepose 해상도가 서로 달라 첫 batch에서 shape mismatch가 발생했으므로, 이번 smoke에서는 ignored tiny10 train split만 384x512로 정규화했다.

## 6. 실행 로그 위치

output root:

```text
backend/training/outputs/stableviton_tiny_train_smoke
```

주요 로그:

```text
backend/training/outputs/stableviton_tiny_train_smoke/logs/train_help.txt
backend/training/outputs/stableviton_tiny_train_smoke/logs/train_10step_stdout_initial.txt
backend/training/outputs/stableviton_tiny_train_smoke/logs/train_10step_stdout_no_vae_wrapper_retry3_resized.txt
backend/training/outputs/stableviton_tiny_train_smoke/logs/nvidia_smi_10step_no_vae_wrapper_retry3_resized.csv
```

GPU CSV logger는 `nvidia-smi` query option 호환 문제로 유효한 VRAM sample을 남기지 못했다. 대신 stdout에서 CUDA 사용 여부를 확인했다.

```text
GPU available: True, used: True
LOCAL_RANK: 0 - CUDA_VISIBLE_DEVICES: [0]
```

## 7. 실행한 명령과 조정 사항

원본 `train.py` CLI 형태:

```powershell
$env:CUDA_VISIBLE_DEVICES='0'
D:\conda-envs\vton\python.exe .\train.py `
  --config_name VITONHD `
  --data_root_dir D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_tiny10 `
  --batch_size 1 `
  --max_epochs 1 `
  --save_every_n_epochs 1 `
  --valid_epoch_freq 999 `
  --save_root_dir D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_tiny_train_smoke `
  --save_name tiny10_initial `
  --logger_freq 1 `
  --precision 32 `
  --num_sanity_val_steps 0 `
  --use_validation
```

원본 CLI 실행은 `VITONHD_VAE_finetuning.ckpt` 로드 단계에서 실패했다.

```text
RuntimeError: PytorchStreamReader failed reading zip archive: failed finding central directory
```

이후 외부 StableVITON repo 자체는 수정하지 않고, ignored output 경로의 local runner로 `train.py`의 `main_worker`를 호출했다. local runner에서 적용한 smoke-only 조정:

- `vae_load_path=None`으로 추가 VAE checkpoint 로드를 생략
- `DataLoader num_workers=0`
- `Trainer max_steps=10`
- `Trainer strategy` 인자 제거
- validation 비활성화

이 조정은 `backend/training/outputs/**` 아래 local smoke runner에만 적용했고 Git에는 포함하지 않는다.

## 8. 10-step smoke 결과

최종 상태:

```text
status=partial_success
stableviton_train_wrapper_executed=True
model_config_loaded=True
checkpoint_loaded=True
dataset_root_recognized=True
train_samples=9
cuda_execution=True
train_loop_entered=True
first_train_step_completed=True
loss=0.435
loss_nan=False
checkpoint_created=False
sample_created=False
```

stdout 근거:

```text
Loaded state_dict from [./ckpts/VITONHD_PBE_pose.ckpt]
GPU available: True, used: True
LOCAL_RANK: 0 - CUDA_VISIBLE_DEVICES: [0]
Training: 0it [00:00, ?it/s]
Epoch 0: 11%|#1        | 1/9 [09:18<1:14:25, 558.14s/it, loss=0.435, v_num=1, train_loss_step=0.435, global_step=0.000]
```

해석:

- StableVITON train loop는 실제로 시작됐다.
- 첫 train step이 완료됐고 loss가 출력됐다.
- loss는 NaN이 아니다.
- 1 step에 약 558초가 걸렸다.
- 매 train step마다 DDIM Sampling 50 timesteps가 실행되어 전체 tiny10 1 epoch는 약 1시간 20분 이상 걸릴 가능성이 있다.
- 오늘 시간 제한상 1-step 성공 기준으로 중단했다.

## 9. 실패/중단 지점 요약

원본 CLI에서 확인된 문제:

```text
failed_at=VAE checkpoint loading
error=PytorchStreamReader failed reading zip archive: failed finding central directory
candidate_cause=./ckpts/VITONHD_VAE_finetuning.ckpt file integrity issue
```

dataset compatibility에서 확인된 문제:

```text
missing=train/gt_cloth_warped_mask/{pair_id}.jpg
candidate_fix=prepare_stableviton_layout.py에서 smoke/train용 gt_cloth_warped_mask 생성 옵션 추가
```

shape compatibility에서 확인된 문제:

```text
error=Height and Width of image, mask or masks should be equal
candidate_cause=person/cloth/mask/densepose 원본 해상도 불일치
candidate_fix=StableVITON layout copy 단계에서 train/test artifact를 384x512 또는 StableVITON 기대 해상도로 정규화
```

runtime 중단 이유:

```text
reason=DDIM 50-step sampling per train step
observed_first_step_time=558.14 seconds
decision=1-step compatibility success로 문서화하고 중단
```

## 10. checkpoint / sample 생성 여부

checkpoint:

```text
created=False
reason=epoch completion 전에 중단되어 ModelCheckpoint가 저장되지 않음
```

sample:

```text
created=False
reason=first step의 DDIM sampling은 실행됐지만, 중단 시점 기준 저장된 sample file은 확인되지 않음
```

args/config/tensorboard 로그는 ignored output 아래 생성됐다.

```text
backend/training/outputs/stableviton_tiny_train_smoke/20260607_tiny10_no_vae_smoke/
```

## 11. Git safety

Git에 포함할 파일:

```text
docs/experiments/pc3_stableviton_aihub_tiny100_train_smoke.md
```

Git에 포함하지 않을 파일:

```text
backend/datasets/**
backend/training/outputs/**
backend/outputs/**
backend/logs/**
backend/demo/assets/**
*.jpg
*.jpeg
*.png
*.webp
*.pt
*.pth
*.ckpt
*.safetensors
*.zip
*.7z
*.part*
```

이번 작업의 tiny10 dataset, smoke-only mask, resized local assets, stdout/stderr logs, GPU logs, local runner, TensorBoard files, checkpoint/sample 후보 파일은 모두 Git에 포함하지 않는다.

## 12. 다음 단계

- `prepare_stableviton_layout.py`에 StableVITON train smoke용 `gt_cloth_warped_mask` 생성 또는 매핑 옵션을 추가한다.
- layout copy 단계에서 image/artifact 해상도 정규화를 명시적으로 수행한다.
- `VITONHD_VAE_finetuning.ckpt` 무결성을 재확인하거나, 실제 train smoke에서 VAE 추가 로드 생략 여부를 config/CLI로 제어할 방법을 만든다.
- DDIM sampling을 train smoke에서 끄거나 `logger_freq`/ImageLogger 동작을 조정해 step time을 줄인다.
- LoRA adapter 구현 후 LoRA 10-step smoke를 별도 작업으로 진행한다.
