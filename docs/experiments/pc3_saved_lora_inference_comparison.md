# PC3 saved LoRA inference comparison

## 1. 목적

이번 작업의 목적은 9995-step run에서 저장한 LoRA adapter를 StableVITON inference 경로에 실제로 load하고, 같은 pair에 대해 baseline StableVITON 결과와 LoRA 적용 결과를 모두 생성할 수 있는지 확인하는 것이다.

이번 작업은 추가 학습이 아니다. k-fold, 추가 epoch, 추가 step 학습은 수행하지 않았다.

## 2. 사용 경로

| 항목 | 경로 |
| --- | --- |
| 우리 repo | `D:\GitHub\fit-reasoning-vton` |
| 외부 StableVITON repo | `D:\GitHub\StableVITON` |
| inference dataset | `backend/datasets/stableviton_aihub_10k_layout_tiny10` |
| saved LoRA adapter | `backend/training/outputs/stableviton_lora_10k_adapter_save/lora_adapter.pt` |
| output root | `backend/training/outputs/stableviton_saved_lora_inference_comparison` |

`lora_adapter.pt`, generated images, summary JSON은 모두 local output artifact이므로 Git에 포함하지 않는다.

## 3. StableVITON inference 구조 확인

외부 StableVITON repo에는 원본 inference entrypoint가 있다.

```text
D:\GitHub\StableVITON\inference.py
```

확인한 원본 inference 인자:

- `--config_path`
- `--model_load_path`
- `--batch_size`
- `--data_root_dir`
- `--save_dir`
- `--denoise_steps`
- `--img_H`
- `--img_W`
- `--repaint`
- `--unpair`

원본 `inference.py`는 baseline StableVITON checkpoint load와 image generation은 지원하지만, LoRA adapter load 옵션은 제공하지 않는다. 따라서 외부 repo를 수정하지 않고 우리 repo에 helper script를 추가했다.

추가한 helper:

```text
backend/training/scripts/run_saved_lora_inference_comparison.py
```

helper 동작:

- StableVITON 원본 config/checkpoint load
- baseline inference 실행
- 기존 LoRA smoke runner의 LoRA insertion/load helper 재사용
- saved `lora_adapter.pt` load
- 같은 pair로 LoRA inference 실행
- output image와 summary를 ignored output path에 저장

## 4. 실행 전 이슈와 수정

첫 번째 실행은 checkpoint strict load에서 실패했다.

```text
Unexpected key(s) in state_dict: "cond_stage_model.transformer.vision_model.embeddings.position_ids"
```

StableVITON training smoke에서 사용한 방식과 동일하게 checkpoint를 non-strict로 load하도록 helper를 조정했다. 이후 baseline/LoRA 모두 같은 unexpected key를 기록하되 실행은 정상 진행됐다.

두 번째 실행은 source dataset의 일부 image/mask 해상도 불일치로 Albumentations shape check에서 실패했다.

```text
ValueError: Height and Width of image, mask or masks should be equal.
```

원본 dataset을 수정하지 않기 위해 helper가 `backend/training/outputs/**` 아래에 inference 전용 resized copy를 만들도록 수정했다.

effective data root:

```text
backend/training/outputs/stableviton_saved_lora_inference_comparison/prepared_inference_data
```

## 5. 실행 명령

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_saved_lora_inference_comparison.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_tiny10 `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_saved_lora_inference_comparison `
  --lora-adapter-path D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_10k_adapter_save\lora_adapter.pt `
  --batch-size 1 `
  --denoise-steps 50 `
  --max-lora-modules 8
```

## 6. 사용 pair

| 항목 | 값 |
| --- | --- |
| pair_id | `EP00000011` |
| person image | `EP00000011.jpg` |
| cloth image | `EP00000011.jpg` |
| split | tiny10 test |
| denoise_steps | 50 |

## 7. Baseline inference 결과

| 항목 | 값 |
| --- | ---: |
| status | success |
| dataset_len | 1 |
| output_count | 1 |
| elapsed_sec | 22.5637 |
| peak_vram_mb | 7839.65 |
| checkpoint_strict_load | false |

output image:

```text
backend/training/outputs/stableviton_saved_lora_inference_comparison/baseline/pair/EP00000011_EP00000011.jpg
```

image check:

| 항목 | 값 |
| --- | ---: |
| image_size | 384 x 512 |
| file_size_bytes | 33161 |
| mean_rgb | `[155.37, 154.65, 154.47]` |

## 8. Saved LoRA inference 결과

| 항목 | 값 |
| --- | ---: |
| status | success |
| dataset_len | 1 |
| output_count | 1 |
| elapsed_sec | 18.5134 |
| peak_vram_mb | 7857.1 |
| lora_adapter_loaded | true |
| lora_adapter_loaded_key_count | 16 |
| inserted_lora_module_count | 8 |
| load_missing_keys | `[]` |
| load_unexpected_keys | `[]` |
| load_shape_mismatch_keys | `[]` |
| lora_adapter_file_size_mb | 0.1236 |

output image:

```text
backend/training/outputs/stableviton_saved_lora_inference_comparison/lora/pair/EP00000011_EP00000011.jpg
```

image check:

| 항목 | 값 |
| --- | ---: |
| image_size | 384 x 512 |
| file_size_bytes | 33351 |
| mean_rgb | `[156.31, 155.37, 154.26]` |

## 9. 결과 해석

이번 작업으로 saved LoRA adapter를 inference graph에 삽입하고, baseline과 LoRA 적용 결과 이미지를 같은 pair 기준으로 생성할 수 있음을 확인했다.

이번 문서는 inference 실행 가능성과 output 확보를 기록하는 문서다. Generated image는 local output artifact이므로 Git에 포함하지 않는다.

## 10. 다음 단계

- demo pair 수를 3개 이상으로 확장
- generated images를 local `backend/demo/assets/**`에 배치
- `scripts/validate_demo_assets.py --strict` 실행
- Artifact Compare / Model Compare UI에서 실제 이미지 연결
- 필요 시 같은 pair 기준 정성/정량 평가 표 보강

## 11. Git safety

Git 포함 대상:

- `backend/training/scripts/run_saved_lora_inference_comparison.py`
- `docs/experiments/pc3_saved_lora_inference_comparison.md`
- `README.md`

Git에 포함하지 않는 항목:

- `backend/datasets/**`
- `backend/training/outputs/**`
- `backend/outputs/**`
- `backend/logs/**`
- `*.pt`
- `*.jpg`
- `*.png`
- checkpoint
- generated image
- logs
- summary json
