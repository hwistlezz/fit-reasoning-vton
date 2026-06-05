# StableVITON LoRA fine-tuning 구조 조사 및 시간 측정 계획

## 1. 목적

이번 문서는 DensePose 포함 artifact patch를 기다리는 동안, 외부 StableVITON repo의 학습 구조를 읽기 전용으로 조사하고 실제 StableVITON fine-tuning 또는 LoRA tiny smoke 시간 측정 계획을 정리하기 위한 것이다.

이번 작업은 실제 fine-tuning 실행이 아니다. `D:\GitHub\StableVITON` repo는 수정하지 않았고, 구조 조사만 수행했다.

## 2. 현재 상황

현재 프로젝트 repo는 다음 경로를 사용한다.

```text
D:\GitHub\fit-reasoning-vton
```

외부 StableVITON repo는 다음 경로에 존재한다.

```text
D:\GitHub\StableVITON
```

현재 PC3의 AIHub 10k agnostic dataset은 다음 경로에 있다.

```text
backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full
```

현재 dataset 개수 확인 결과는 다음과 같다.

```text
root_exists True
image 9995
cloth 9995
worn 9995
fit 9995
agnostic-v3.2 9995
agnostic-mask 9995
cloth-mask missing
image-densepose missing
openpose-json missing
image-parse missing
manifest.jsonl True
train_pairs.txt False
test_pairs.txt False
```

즉 현재 dataset은 pre-LoRA smoke나 자체 DataLoader 검증에는 사용할 수 있지만, StableVITON 원본 `VITONHDDataset`에 바로 연결하기에는 아직 부족하다.

## 3. 조사 환경

조사 대상은 외부 repo의 로컬 체크아웃이다.

```text
D:\GitHub\StableVITON
```

확인된 주요 파일과 폴더는 다음과 같다.

```text
train.py
train.sh
inference.py
inference.sh
dataset.py
configs/VITONHD.yaml
cldm/
ldm/
ckpts/
```

`ckpts/`에는 다음 checkpoint 파일이 존재한다.

```text
VITONHD.ckpt
VITONHD_PBE_pose.ckpt
VITONHD_VAE_finetuning.ckpt
```

## 4. StableVITON repo 구조 요약

StableVITON repo는 inference-only repo가 아니다. 실제 training entrypoint가 존재한다.

주요 구성은 다음과 같다.

| 구분 | 파일 | 조사 결과 |
| --- | --- | --- |
| 학습 entrypoint | `train.py` | PyTorch Lightning `Trainer.fit()` 기반 학습 실행 |
| 학습 shell 예시 | `train.sh` | `CUDA_VISIBLE_DEVICES=... python train.py --config_name VITONHD ...` 예시 |
| 추론 entrypoint | `inference.py` | `PLMSSampler` 기반 inference |
| dataset | `dataset.py` | `VITONHDDataset` 구현 |
| config | `configs/VITONHD.yaml` | `ControlLDM`, `StableVITON`, `VITONHDDataset` 연결 |
| ControlLDM | `cldm/cldm.py` | optimizer 구성, control model, UNet 일부 block 학습 설정 |
| attention | `ldm/modules/attention.py` | `CrossAttention`, `MemoryEfficientCrossAttention`, `SpatialTransformer` 정의 |
| StableVITON UNet | `cldm/warping_cldm_network.py` | `StableVITON(UNetModel)`, warp block, SpatialTransformer 사용 |

## 5. train/inference entrypoint 조사 결과

`train.py`는 다음 특징을 가진다.

- `--config_name VITONHD`를 받아 `configs/VITONHD.yaml`을 로드한다.
- `cldm.model.create_model()`로 `ControlLDM` 모델을 생성한다.
- `configs/VITONHD.yaml`의 `resume_path` 기본값은 `./ckpts/VITONHD_PBE_pose.ckpt`이다.
- `--vae_load_path` 기본값은 `./ckpts/VITONHD_VAE_finetuning.ckpt`이다.
- dataset class는 config의 `dataset_name: VITONHDDataset`으로 결정된다.
- `train_dataset`, `valid_paired_dataset`, `valid_unpaired_dataset`을 만든다.
- `pytorch_lightning.Trainer`를 사용한다.
- checkpoint는 `ModelCheckpoint` callback으로 epoch 단위 저장한다.

`train.py`에서 주의할 점은 `CUDA_VISIBLE_DEVICES` 환경 변수를 직접 참조한다는 것이다. 이 값이 없으면 `args.n_gpus = len(os.environ["CUDA_VISIBLE_DEVICES"].split(","))`에서 실패할 수 있다. 시간 측정 smoke 명령은 PowerShell에서 `$env:CUDA_VISIBLE_DEVICES='0'`을 명시한 뒤 실행하는 방식이 안전하다.

`inference.py`는 `configs/VITONHD.yaml`과 checkpoint를 받아 `PLMSSampler`로 sample을 생성한다. 이번 #87 작업의 목적은 training 구조 조사이므로 inference는 entrypoint 존재와 dataset 공유 여부만 확인했다.

## 6. dataset artifact 요구사항

README 기준 StableVITON은 training과 inference 모두 다음 dataset 구조를 요구한다.

```text
train/
  image/
  image-densepose/
  agnostic-v3.2/
  agnostic-mask/
  cloth/
  cloth_mask/
  gt_cloth_warped_mask/   # ATV loss 사용 시

test/
  image/
  image-densepose/
  agnostic-v3.2/
  agnostic-mask/
  cloth/
  cloth_mask/
```

다만 실제 `dataset.py` 코드 기준으로는 cloth mask 폴더명이 `cloth-mask`이다.

```text
train_pairs.txt
test_pairs.txt
train/image/
train/cloth/
train/cloth-mask/
train/agnostic-v3.2/
train/agnostic-mask/
train/image-densepose/
train/gt_cloth_warped_mask/  # train + ATV loss일 때 필요
test/image/
test/cloth/
test/cloth-mask/
test/agnostic-v3.2/
test/agnostic-mask/
test/image-densepose/
```

`dataset.py`에서 확인한 필수 입력은 다음과 같다.

| 입력 | StableVITON key | 코드 기준 필수 여부 |
| --- | --- | --- |
| target image | `image` | train/test 모두 필요 |
| cloth image | `cloth` | train/test 모두 필요 |
| cloth mask | `cloth_mask` 반환, 경로는 `cloth-mask` | train/test 모두 필요 |
| agnostic image | `agn` | train/test 모두 필요 |
| agnostic mask | `agn_mask` | train/test 모두 필요 |
| DensePose image | `image_densepose` | train/test 모두 필요 |
| warped cloth GT mask | `gt_cloth_warped_mask` | train에서 필요. ATV loss 목적이며 현재 코드에서는 train일 때 로드 |
| openpose-json | 없음 | 원본 `VITONHDDataset` 직접 입력은 아님 |
| image-parse | 없음 | 원본 `VITONHDDataset` 직접 입력은 아님 |

`configs/VITONHD.yaml` 기준 조건부 입력은 다음과 같다.

```text
first_stage_key: image
first_stage_key_cond: [agn, agn_mask, image_densepose]
cond_stage_key: cloth
control_key: cloth
mask1_key: gt_cloth_warped_mask
mask2_key: agn_mask
```

따라서 StableVITON 원본 학습에 필요한 최소 artifact는 `image`, `cloth`, `cloth-mask`, `agnostic-v3.2`, `agnostic-mask`, `image-densepose`, `train_pairs.txt`이다. validation까지 켜면 `test/`와 `test_pairs.txt`도 필요하다. `--use_atv_loss`를 켜거나 원본 코드가 train에서 항상 `gt_cloth_warped_mask`를 로드하는 현재 구조를 유지한다면 `gt_cloth_warped_mask`도 준비해야 한다.

## 7. 우리 AIHub 10k dataset과의 차이

현재 AIHub 10k agnostic dataset은 flat 구조이다.

```text
backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full/
  image/
  cloth/
  worn/
  fit/
  agnostic-v3.2/
  agnostic-mask/
  manifest.jsonl
```

StableVITON 원본 `VITONHDDataset`은 flat manifest를 읽지 않는다. `train_pairs.txt`와 `test_pairs.txt`를 기준으로 `train/` 또는 `test/` 하위 폴더에서 파일을 읽는다.

추가로 의미 매핑도 확인이 필요하다.

- 우리 dataset의 `image/`는 person/model image이다.
- 우리 dataset의 `worn/`은 해당 의류를 착용한 정답 이미지이다.
- StableVITON 원본 train의 `image/`는 reconstruction target 이미지이다.

따라서 StableVITON용 staged dataset을 만들 때는 `worn/{pair_id}.jpg`를 `train/image/{pair_id}.jpg`로 매핑하는 것이 더 자연스러울 가능성이 높다. `agnostic-v3.2`와 `agnostic-mask`가 어떤 원본 이미지 기준으로 생성됐는지도 PC2 artifact patch 설명과 함께 다시 확인해야 한다.

현재 gap은 다음과 같다.

| StableVITON 요구 | 현재 10k agnostic dataset 상태 | 판단 |
| --- | --- | --- |
| `train/image` | flat `image/`, `worn/` 존재 | target 매핑 필요 |
| `train/cloth` | flat `cloth/` 존재 | staged copy/link 필요 |
| `train/cloth-mask` | 없음 | patch 필요 |
| `train/agnostic-v3.2` | flat `agnostic-v3.2/` 9995개 | staged copy/link 필요 |
| `train/agnostic-mask` | flat `agnostic-mask/` 9995개 | mask filename 규칙 확인 필요 |
| `train/image-densepose` | 없음 | DensePose patch 필요 |
| `train/gt_cloth_warped_mask` | 없음 | train 코드 유지 시 대체/생성/코드 옵션화 필요 |
| `train_pairs.txt` | 없음 | manifest 기반 생성 필요 |
| `test_pairs.txt` | 없음 | validation 사용 시 생성 필요 |
| `openpose-json` | 없음 | StableVITON 원본 직접 입력은 아니지만 artifact 생성 검증에는 유용 |
| `image-parse` | 없음 | StableVITON 원본 직접 입력은 아니지만 agnostic/mask 생성 검증에는 유용 |

patch 도착 후 우선 확인할 것은 다음이다.

- `image-densepose` 9995개 포함 여부
- `cloth-mask` 9995개 포함 여부
- `agnostic-mask` 파일명이 StableVITON 코드의 `{pair_id}_mask.png` 규칙과 맞는지
- `worn`을 target으로 쓰는 staged 구조가 맞는지
- `gt_cloth_warped_mask`를 만들 수 있는지, 또는 tiny smoke에서는 `--use_validation`/코드 옵션으로 우회할 수 있는지

## 8. LoRA 적용 후보 module

원본 코드에서 `LoRA` 또는 `lora` 키워드는 제한적으로만 확인된다.

- `ldm/modules/attention.py`의 `BasicTransformerBlock`과 `SpatialTransformer` 생성자에 `is_lora`, `lora_context_dim` 인자가 있다.
- 그러나 `CrossAttention`과 `MemoryEfficientCrossAttention` 내부의 `to_q`, `to_k`, `to_v`, `to_out`은 일반 `nn.Linear`이다.
- repo 전체에서 PEFT, low-rank adapter, LoRA weight save/load, LoRA rank 설정, LoRA optimizer param group은 확인되지 않았다.

LoRA 후보 module은 다음 순서가 현실적이다.

1. `ldm/modules/attention.py`
   - `CrossAttention.to_q`
   - `CrossAttention.to_k`
   - `CrossAttention.to_v`
   - `CrossAttention.to_out.0`
   - `MemoryEfficientCrossAttention.to_q`
   - `MemoryEfficientCrossAttention.to_k`
   - `MemoryEfficientCrossAttention.to_v`
   - `MemoryEfficientCrossAttention.to_out.0`

2. `SpatialTransformer` 내부 `BasicTransformerBlock`
   - self-attention `attn1`
   - cross-attention `attn2`

3. `cldm/warping_cldm_network.py`
   - `StableVITON`의 `input_blocks`, `middle_block`, `output_blocks`에 삽입되는 `SpatialTransformer`
   - `warp_flow_blks`의 `CustomSpatialTransformer`

4. `cldm/cldm.py`
   - `self.model.diffusion_model` 내부 attention module만 LoRA trainable로 두는 optimizer 구성
   - `control_model`까지 LoRA 적용할지 여부는 별도 실험 필요

원본 `configure_optimizers()`는 현재 다음 방식이다.

- 기본적으로 `control_model` parameters를 학습한다.
- `--sd_unlocked`이면 UNet output blocks와 out을 추가한다.
- input channel 조건에 따라 UNet input block 일부를 추가한다.
- `warp_flow_blks`, `warp_zero_convs`가 있으면 추가한다.
- 전체는 `torch.optim.AdamW(params, lr=lr)`로 묶는다.

따라서 실제 LoRA fine-tuning을 하려면 단순 config 옵션만으로는 부족하다. attention module에 low-rank adapter를 주입하고, base weight freeze와 LoRA parameter만 optimizer에 넣는 구현이 추가로 필요하다.

## 9. 구현 난이도 판단

결론 분류는 다음과 같다.

```text
D. 현재 artifact 부족으로 patch 도착 후 재검증 필요
```

보조 판단은 다음과 같다.

- StableVITON 원본 full fine-tuning 구조는 존재한다.
- 원본 train script를 바로 실행하려면 StableVITON형 dataset staging이 필요하다.
- LoRA는 이름 흔적은 있으나 실제 adapter 구현이 확인되지 않았다.
- patch 도착 후에도 LoRA fine-tuning은 별도 adapter 구현이 필요하므로 `B` 성격의 추가 작업이 남는다.

즉 현재 시점의 blocking factor는 artifact와 dataset contract이다. patch 수신 후 `image-densepose`, `cloth-mask`, filename rule, `train_pairs.txt` 생성까지 맞춘 뒤 원본 full fine-tuning tiny smoke부터 검증하고, 그 다음 LoRA adapter 구현 여부를 결정하는 순서가 안전하다.

## 10. patch 도착 후 tiny time measurement 계획

측정 목표는 실제 StableVITON 계열 학습 loop가 PC3에서 얼마나 걸리는지 확인하는 것이다. 처음부터 장시간 학습을 돌리지 않고 tiny subset으로 단계적으로 진행한다.

측정 subset:

- 10 samples
- 100 samples

측정 steps:

- 10-step smoke
- 100-step smoke

batch size:

- batch size 1 우선
- VRAM 여유가 있으면 batch size 2 추가

image size:

```text
512 x 384
```

기록할 값:

- `steps_completed`
- `batch_size`
- `avg_step_time`
- `elapsed_seconds`
- `peak_vram_mb`
- `loss_nan`
- 첫 loss / 마지막 loss
- checkpoint 저장 여부
- sample 또는 validation image 저장 여부
- 실패 시 exception type, failing pair_id, missing path, 마지막 완료 step

권장 실행 순서:

1. patch dataset count 확인
2. StableVITON용 staged tiny dataset 생성
3. `VITONHDDataset` 단독 item load smoke
4. 10 samples, batch size 1, 10-step forward/backward smoke
5. 10 samples, batch size 1, 100-step smoke
6. 100 samples, batch size 1, 100-step smoke
7. batch size 2 반복 여부 판단

실제 LoRA adapter가 준비되지 않았을 경우 대체 측정:

- 원본 full fine-tuning tiny smoke
- 또는 checkpoint 저장 없이 forward/backward smoke
- 단, 결과 문서에는 반드시 "LoRA fine-tuning 시간이 아니라 StableVITON training loop smoke 시간"으로 표기한다.

## 11. 실행 명령어 초안

아래 명령어는 patch 도착 후 사용할 초안이다. 이번 #87 작업에서는 실행하지 않았다.

StableVITON용 staged dataset 예시:

```text
backend/training/outputs/stableviton_tiny_10/
  train/
    image/
    cloth/
    cloth-mask/
    agnostic-v3.2/
    agnostic-mask/
    image-densepose/
    gt_cloth_warped_mask/
  test/
    image/
    cloth/
    cloth-mask/
    agnostic-v3.2/
    agnostic-mask/
    image-densepose/
  train_pairs.txt
  test_pairs.txt
```

PowerShell 실행 초안:

```powershell
Set-Location -LiteralPath D:\GitHub\StableVITON
$env:CUDA_VISIBLE_DEVICES='0'

D:\conda-envs\vton\python.exe train.py `
  --config_name VITONHD `
  --data_root_dir D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_tiny_10 `
  --batch_size 1 `
  --img_H 512 `
  --img_W 384 `
  --learning_rate 1e-5 `
  --max_epochs 1 `
  --save_every_n_epochs 1 `
  --valid_epoch_freq 1 `
  --logger_freq 10 `
  --num_sanity_val_steps 0 `
  --save_root_dir D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_train_time_smoke `
  --save_name tiny10_bs1_10step_candidate
```

주의:

- 원본 `train.py`는 step 단위 종료 옵션이 없다. 정확한 10-step/100-step 측정을 위해서는 별도 wrapper 또는 최소 patch가 필요할 수 있다.
- StableVITON repo를 수정하지 않는 조건이면, staged dataset의 길이를 줄이고 `max_epochs=1`로 제한해 sample 수 기반으로 근사 측정한다.
- 정확한 step 제한이 필요하면 fit-reasoning-vton repo 쪽에 wrapper를 추가하거나 별도 issue에서 StableVITON training wrapper를 구현한다.

## 12. Git safety

이번 PR에 포함하면 안 되는 항목은 다음과 같다.

```text
D:\GitHub\StableVITON/**
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

이번 작업의 Git 포함 대상은 문서 하나뿐이다.

```text
docs/experiments/stableviton_lora_finetuning_structure_plan.md
```

## 13. 다음 단계

1. DensePose 포함 artifact patch 수신
2. patch dataset count 및 strict artifact smoke 재실행
3. `cloth-mask`, `image-densepose`, `agnostic-mask` filename rule 확인
4. StableVITON용 staged tiny dataset 생성
5. `VITONHDDataset` item load smoke
6. 원본 full fine-tuning tiny smoke 또는 forward/backward smoke 시간 측정
7. LoRA adapter 주입 설계
8. LoRA parameter-only optimizer 구성
9. 10-step / 100-step LoRA smoke 측정
