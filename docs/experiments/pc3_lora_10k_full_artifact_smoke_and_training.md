# PC3 10k full artifact dataset smoke 및 training pilot 결과

## 1. 목적

이번 작업은 PC2가 전달한 10k artifact patch를 PC3의 기존 AIHub 10k agnostic dataset에 병합한 뒤, full artifact dataset readiness와 PC3 training pipeline 동작 여부를 문서화하는 것이다.

기록 대상은 다음 네 단계다.

- strict artifact smoke test
- StableVITON layout dry-run
- StableVITON tiny100 layout copy
- `train_lora_smoke.py` 기반 100-step / 500-step training pilot

중요하게, 이번 결과는 실제 StableVITON LoRA fine-tuning 완료 결과가 아니다. 현재 training 결과는 `train_lora_smoke.py` 기반 pre-LoRA training smoke / training pilot이며, artifact를 실제 StableVITON attention 또는 conditioning 경로에 넣어 학습한 결과로 해석하면 안 된다.

## 2. 사용 dataset root

사용한 dataset root:

```text
backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full
```

이 dataset은 기존 10k agnostic dataset에 PC2 artifact patch를 병합한 결과다.

## 3. patch 수신 및 병합 요약

patch summary:

```text
base_dataset=lora_pilot_aihub_10k_agnostic_v3_full
pair_count=9995
openpose_json_count=9995
image_parse_count=9995
cloth_mask_count=9995
image_densepose_count=9995
```

#74에서 확인한 known-bad 4개 pair는 filtered manifest에서 제외된 상태를 유지했다.

```text
EP00003620
EP00003937
EP00005080
EP00007279
```

## 4. filename normalization

처음 strict smoke에서는 일부 artifact가 missing으로 잡혔다. 실제 누락이 아니라 파일명 패턴 차이였다.

수정한 파일명 규칙:

```text
agnostic-mask: {pair_id}_mask.png -> {pair_id}.png
image-densepose: {pair_id}.0001.png -> {pair_id}.png
```

위 normalization 이후 strict artifact smoke가 성공했다.

## 5. 최종 dataset count

최종 dataset count:

```text
image 9995
cloth 9995
worn 9995
fit 9995
agnostic-v3.2 9995
agnostic-mask 9995
openpose-json 9995
image-parse 9995
cloth-mask 9995
image-densepose 9995
manifest lines 9995
```

## 6. strict artifact smoke 결과

summary path:

```text
backend/training/outputs/lora_10k_full_artifact_smoke/dataset_smoke_summary.json
```

contact sheet:

```text
backend/training/outputs/lora_10k_full_artifact_smoke/contact_sheet.jpg
```

핵심 결과:

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
artifact_errors=0
```

required artifacts:

```text
openpose-json
image-parse
cloth-mask
agnostic-v3.2
agnostic-mask
image-densepose
```

artifact별 결과:

| artifact | checked | missing | load_errors |
| --- | ---: | ---: | ---: |
| openpose-json | 9995 | 0 | 0 |
| image-parse | 9995 | 0 | 0 |
| cloth-mask | 9995 | 0 | 0 |
| agnostic-v3.2 | 9995 | 0 | 0 |
| agnostic-mask | 9995 | 0 | 0 |
| image-densepose | 9995 | 0 | 0 |

strict smoke 기준으로 full artifact dataset은 PC3 loader와 backend fit analyzer loader 모두 통과했다.

## 7. StableVITON layout dry-run 결과

summary path:

```text
backend/training/outputs/stableviton_layout_prepare_full_artifact/summary.json
```

핵심 결과:

```text
mode=dry-run
total_manifest=9995
selected_count=100
train_count=90
test_count=10
ready_train_count=90
ready_test_count=10
ready_count=100
not_ready_count=0
require_densepose=True
copied_count=0
missing_counts all 0
```

dry-run에서는 파일을 복사하지 않고 100개 subset의 StableVITON layout readiness만 확인했다.

## 8. StableVITON tiny100 layout copy 결과

summary path:

```text
backend/training/outputs/stableviton_layout_prepare_tiny100/summary.json
```

output root:

```text
backend/datasets/stableviton_aihub_10k_layout_tiny100
```

핵심 결과:

```text
mode=copy
total_manifest=9995
selected_count=100
train_count=90
test_count=10
ready_train_count=90
ready_test_count=10
ready_count=100
not_ready_count=0
require_densepose=True
copied_count=100
missing_counts all 0
```

`backend/datasets/stableviton_aihub_10k_layout_tiny100`는 dataset/output 성격이므로 Git에 포함하지 않는다.

## 9. 100-step training pilot 결과

summary path:

```text
backend/training/outputs/lora_10k_full_artifact_training_100step_bs2/train_summary.json
```

핵심 결과:

```text
task=pre_lora_training_smoke
note=This is not StableVITON LoRA fine-tuning.
manifest_count=9995
steps_requested=100
steps_completed=100
batch_size=2
image_size=[512, 384]
lr=0.0001
num_workers=0
cuda_available=True
device=cuda
device_name=NVIDIA GeForce RTX 4080
first_loss=0.16158393025398254
final_loss=0.11582594364881516
loss_nan=False
elapsed_sec=93.1824
avg_step_time_sec=0.931824
peak_vram_mb=123.06
checkpoints=2
samples=2
error=None
estimated_10k_epoch_time_min=77.62
estimated_1000_step_time_min=15.53
```

100-step training pilot은 정상 종료됐고, checkpoint / sample / `train_summary.json`이 생성됐다. 생성물은 모두 `backend/training/outputs/**` 아래에 있으며 Git에는 포함하지 않는다.

## 10. 500-step training pilot 결과

summary path:

```text
backend/training/outputs/lora_10k_full_artifact_training_500step_bs2/train_summary.json
```

핵심 결과:

```text
task=pre_lora_training_smoke
note=This is not StableVITON LoRA fine-tuning.
manifest_count=9995
steps_completed=500
batch_size=2
image_size=[512, 384]
avg_step_time_sec=0.712915
elapsed_sec=356.4574
peak_vram_mb=123.06
first_loss=0.16158393025398254
final_loss=0.09362810105085373
loss_nan=False
error=None
checkpoints=5
samples=5
```

500-step training pilot도 정상 종료됐다.

## 11. 1000-step 생략 사유

1000-step run은 시간 제약으로 생략했다.

이번 작업의 목적은 최종 성능 학습이 아니라 full artifact dataset readiness와 PC3 training pipeline 검증이다. strict smoke, StableVITON layout dry-run/copy, 100-step 및 500-step training pilot이 모두 성공했으므로 이번 문서화 범위에서는 충분하다고 판단했다.

## 12. #96 10k Basic Baseline과 비교

아래 비교는 실제 StableVITON LoRA 성능 비교가 아니다. 두 실험 모두 같은 `train_lora_smoke.py` 계열이며, PC3 training pipeline이 10k basic dataset과 10k full artifact dataset에서 안정적으로 동작하는지 확인하기 위한 관찰이다.

| run | dataset | steps | batch size | avg_step_time_sec | peak_vram_mb | final_loss | loss_nan |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| #96 10k Basic Baseline | `lora_pilot_aihub_10k_full` | 500 | 2 | 0.694542 | 123.06 | 0.0936279818 | False |
| #91 10k Full Artifact Dataset | `lora_pilot_aihub_10k_agnostic_v3_full` | 500 | 2 | 0.712915 | 123.06 | 0.0936281011 | False |

해석:

- 두 run 모두 `loss_nan=False`이고 error는 없었다.
- peak VRAM은 두 run 모두 `123.06 MB`로 기록됐다.
- #91 full artifact dataset 500-step run은 #96 basic baseline보다 평균 step time이 약간 길다.
- 이 차이는 현재 smoke script 계열의 실행 관찰이며, 실제 StableVITON LoRA 품질 또는 성능 차이로 해석하면 안 된다.

## 13. 현재 한계

- `train_lora_smoke.py`는 실제 StableVITON LoRA fine-tuning script가 아니다.
- 이번 training pilot은 artifact를 실제 StableVITON attention 또는 conditioning에 넣어 학습한 결과가 아니다.
- 실제 StableVITON LoRA adapter 구현과 `train.py` tiny smoke는 후속 작업이 필요하다.
- StableVITON 원본 학습에서 `image`와 `worn` 매핑은 실제 train 전에 다시 확인해야 한다.
- 이번 문서의 checkpoint와 sample은 pipeline 검증 산출물이며 최종 모델 품질 산출물이 아니다.

## 14. Git safety

Git에 포함할 파일:

```text
docs/experiments/pc3_lora_10k_full_artifact_smoke_and_training.md
```

Git에 포함하지 않는 파일:

```text
backend/datasets/**
backend/training/outputs/**
backend/outputs/**
backend/logs/**
backend/demo/assets/**
*.jpg
*.png
*.pt
*.pth
*.ckpt
*.zip
*.7z
*.part*
```

이번 작업의 dataset, layout copy output, contact sheet, checkpoint, sample image, summary json은 모두 로컬에만 두고 Git에는 포함하지 않는다.

## 15. 다음 단계

- StableVITON `train.py` tiny smoke를 준비한다.
- LoRA adapter 주입 후보를 구현하고 작은 subset으로 forward/backward smoke를 확인한다.
- 같은 test pair로 StableVITON Original / Basic Baseline / Artifact-enhanced 결과를 생성한다.
- 결과 이미지를 `backend/demo/assets/**` contract에 맞춰 배치한다.
- `validate_demo_assets.py --strict`로 발표용 asset 누락 여부를 확인한다.
- 프론트의 Artifact Compare / Model Compare 화면과 연결한다.
