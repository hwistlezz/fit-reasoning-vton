# PC3 LoRA rank / module ablation

## 1. 목적

이번 작업은 StableVITON saved LoRA adapter의 고도화 가능성을 보기 위해 LoRA rank와 target module 수를 바꾼 ablation experiment를 실행한 기록이다.

이번 작업은 제출 이후 고도화 실험이며, dataset/output/checkpoint/adapter/generated image/log/summary json은 Git에 포함하지 않는다.

## 2. 선행 상태

- PR #107: StableVITON LoRA 10k 9995-step 1 epoch-equivalent training 성공
- PR #110: LoRA adapter save/load smoke 성공
- 9995-step adapter save 성공
- PR #116: saved LoRA inference comparison 성공
- 기존 adapter 설정:
  - rank=4
  - alpha=4
  - max_lora_modules=8
  - lora_state_dict_key_count=16
  - adapter_file_size_mb=0.1236

## 3. 실험 설정

| Adapter | rank | alpha | max_lora_modules | 설명 |
| --- | ---: | ---: | ---: | --- |
| rank4-module8 | 4 | 4 | 8 | 기존 saved adapter |
| rank8-module8 | 8 | 8 | 8 | rank만 2배로 확장 |
| rank8-module16 | 8 | 8 | 16 | rank와 target module 수를 함께 확장 |

공통 학습 조건:

- data_root: `backend/datasets/stableviton_aihub_10k_layout_10k_train`
- train_dataset_len: 9995
- max_steps: 9995
- batch_size: 1
- no_prepare_smoke_data: true
- checkpoint/sample/generated image 저장 비활성화
- LoRA adapter만 `lora_adapter.pt`로 저장

## 4. Fixed evaluation pairs

같은 입력 pair 기준으로 baseline / rank4 / rank8-module8 / rank8-module16 결과를 비교하기 위해 `stableviton_aihub_10k_layout_tiny100`의 test split 10개 pair를 fixed evaluation set으로 사용했다.

| # | pair_id |
| ---: | --- |
| 1 | EP00000001 |
| 2 | EP00000013 |
| 3 | EP00000019 |
| 4 | EP00000048 |
| 5 | EP00000049 |
| 6 | EP00000057 |
| 7 | EP00000075 |
| 8 | EP00000080 |
| 9 | EP00000089 |
| 10 | EP00000102 |

## 5. Adapter training summaries

| Metric | rank4-module8 | rank8-module8 | rank8-module16 |
| --- | ---: | ---: | ---: |
| status | success | success | success |
| rank | 4 | 8 | 8 |
| alpha | 4 | 8 | 8 |
| max_lora_modules | 8 | 8 | 16 |
| inserted_lora_module_count | 8 | 8 | 16 |
| trainable_params_after_lora | 30720 | 61440 | 194560 |
| lora_state_dict_key_count | 16 | 16 | 32 |
| adapter_file_size_mb | 0.1236 | 0.2408 | 0.7546 |
| steps_completed | 9995 | 9995 | 9995 |
| elapsed_sec | 10720.0626 | 9961.6849 | 9835.1007 |
| avg_step_time_sec | 1.0725 | 0.9967 | 0.9840 |
| first_loss | 0.9184726476669312 | 0.5117183923721313 | 0.2956969141960144 |
| final_loss | 0.3207787275314331 | 0.2951800227165222 | 0.004082299303263426 |
| loss_nan | false | false | false |
| peak_vram_mb | 8887.85 | 8887.96 | 8898.78 |
| checkpoint_created | false | false | false |
| sample_created | false | false | false |

결과 해석:

- rank8-module8은 기존 rank4-module8보다 trainable parameter와 adapter size가 약 2배로 증가했다.
- rank8-module16은 trainable parameter가 194,560으로 증가했고, adapter size도 0.7546MB로 커졌다.
- 세 실험 모두 `loss_nan=false`로 9995-step을 완료했다.
- rank8-module16은 final_loss가 가장 낮았지만, 이것만으로 try-on 품질 개선을 단정하지 않는다.

## 6. Inference comparison summaries

기존 `run_saved_lora_inference_comparison.py`를 사용해 fixed 10 pair에 대해 inference를 실행했다. Baseline StableVITON은 rank4-module8 run에서 한 번 생성했고, rank8-module8과 rank8-module16 run에서는 `--skip-baseline`으로 LoRA output만 생성했다.

| Metric | baseline | rank4-module8 | rank8-module8 | rank8-module16 |
| --- | ---: | ---: | ---: | ---: |
| status | success | success | success | success |
| dataset_len | 10 | 10 | 10 | 10 |
| output_count | 10 | 10 | 10 | 10 |
| denoise_steps | 50 | 50 | 50 | 50 |
| elapsed_sec | 110.7644 | 105.4671 | 110.5635 | 110.6305 |
| peak_vram_mb | 7841.9 | 7859.35 | 7842.14 | 7842.65 |
| lora_adapter_loaded | false | true | true | true |
| lora_adapter_loaded_key_count | 0 | 16 | 16 | 32 |
| inserted_lora_module_count | 0 | 8 | 8 | 16 |
| load_missing_keys | - | `[]` | `[]` | `[]` |
| load_unexpected_keys | - | `[]` | `[]` | `[]` |
| load_shape_mismatch_keys | - | `[]` | `[]` | `[]` |

Output roots:

```text
backend/training/outputs/stableviton_lora_ablation_inference_rank4_module8
backend/training/outputs/stableviton_lora_ablation_inference_rank8_module8
backend/training/outputs/stableviton_lora_ablation_inference_rank8_module16
```

## 7. Contact sheet

Contact sheet 구성:

```text
person | cloth | target/worn | baseline | rank4-module8 | rank8-module8 | rank8-module16
```

생성 위치:

```text
backend/training/outputs/stableviton_lora_ablation_contact_sheet/rank_module_ablation_contact_sheet.jpg
```

Contact sheet generation 결과:

- pair_count: 10
- missing input/generated image: 0
- generated image는 Git에 포함하지 않음

## 8. Qualitative observation

정성 관찰은 contact sheet 기준의 육안 확인이다.

- rank4-module8과 rank8-module8은 대부분의 pair에서 baseline과 유사한 배경/인물 구조를 유지했다.
- rank8-module8은 일부 pair에서 의류 경계가 조금 더 드러나지만, 입력 의류 보존이 항상 개선된다고 단정하기는 어렵다.
- rank8-module16은 일부 pair에서 강한 색 번짐, 의류/배경 혼입, 과한 texture artifact가 더 눈에 띄었다.
- rank8-module16의 final_loss는 가장 낮지만, 낮은 training loss가 곧바로 더 좋은 try-on 품질을 의미하지는 않았다.

현재 관찰 기준으로는 rank8-module8이 rank8-module16보다 안정적인 후보로 보인다. 단, 최종 판단은 더 많은 pair와 정량/정성 평가를 함께 봐야 한다.

## 9. 다음 단계

- rank8-module8을 우선 후보로 두고 demo pair를 추가 생성
- rank8-module16은 target module 수를 줄이거나 dropout을 추가한 변형 실험 검토
- 30개 이상 fixed pair로 inference comparison 확장
- garment boundary, body distortion, color shift, pose artifact 기준의 수동/반자동 평가표 작성
- demo asset package에 selected result만 복사한 뒤 `validate_demo_assets.py --strict` 실행

## 10. Git safety

Git 포함 대상:

- `docs/experiments/pc3_lora_rank_module_ablation.md`
- `README.md`

Git에 포함하지 않는 항목:

- `backend/datasets/**`
- `backend/training/outputs/**`
- `backend/outputs/**`
- `backend/logs/**`
- `*.pt`
- `*.pth`
- `*.ckpt`
- `*.jpg`
- `*.png`
- logs
- summary json
- generated image
