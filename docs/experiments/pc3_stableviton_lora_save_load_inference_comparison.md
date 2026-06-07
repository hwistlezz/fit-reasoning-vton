# PC3 StableVITON LoRA save/load smoke and inference comparison prep

## 1. 목적

PR #107에서 StableVITON LoRA 10k 1 epoch-equivalent training pilot은 성공했지만, `checkpoint_created=false`, `sample_created=false`였기 때문에 학습된 LoRA adapter weight 파일은 남지 않았다.

이번 작업의 목적은 StableVITON 전체 checkpoint가 아니라 LoRA adapter parameter만 저장하고, 같은 runner에서 다시 load할 수 있는지 확인하는 것이다. 이후 StableVITON baseline 결과와 LoRA adapter 적용 결과를 같은 pair 기준으로 비교하기 위한 준비 단계다.

이번 작업은 최종 성능 비교가 아니다. save/load contract와 smoke 실행 가능성을 확인한 작업이다.

## 2. PR #107 선행 결과

PR #107에서 확인한 10k LoRA 1 epoch-equivalent pilot 결과:

| 항목 | 값 |
| --- | ---: |
| train_count | 9995 |
| ready_count | 9995 |
| inserted_lora_module_count | 8 |
| trainable_params_after_lora | 30,720 |
| steps_completed | 9995 |
| elapsed_sec | 9946.5927 |
| avg_step_time_sec | 0.9952 |
| final_loss | 0.626366138458252 |
| loss_nan | false |
| peak_vram_mb | 8887.85 |
| checkpoint_created | false |
| sample_created | false |

PR #107은 PC3 환경에서 10k LoRA training loop가 끝까지 도는지 확인한 작업이다. adapter weight 저장은 포함하지 않았다.

## 3. 구현 내용

수정 파일:

```text
backend/training/scripts/run_stableviton_lora_tiny_smoke.py
```

추가 옵션:

```text
--save-lora-path
--load-lora-path
```

저장 방식:

- `model.named_parameters()`에서 `.lora_down.` 또는 `.lora_up.`을 포함하는 parameter만 수집
- 전체 StableVITON checkpoint는 저장하지 않음
- `torch.save()` payload에 rank, alpha, dropout, max_lora_modules, inserted_lora_module_names, LoRA state_dict 기록

저장 payload 개념:

```python
{
    "rank": args.rank,
    "alpha": args.alpha,
    "dropout": args.dropout,
    "max_lora_modules": args.max_lora_modules,
    "inserted_lora_module_names": inserted_lora_module_names,
    "state_dict": lora_state_dict,
}
```

Load 방식:

- 기존과 동일하게 StableVITON checkpoint load
- 기존과 동일한 LoRA target module에 adapter 삽입
- 저장된 `state_dict`를 현재 LoRA parameter key와 비교
- matching key만 tensor copy
- missing/unexpected/shape mismatch key를 summary에 기록

추가 summary field:

- `save_lora_path`
- `load_lora_path`
- `lora_adapter_saved`
- `lora_adapter_loaded`
- `lora_state_dict_key_count`
- `lora_adapter_file_size_mb`
- `lora_adapter_loaded_key_count`
- `load_missing_keys`
- `load_unexpected_keys`
- `load_shape_mismatch_keys`

## 4. 1-step save smoke

실행:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_save_load_1step_save `
  --max-steps 1 `
  --batch-size 1 `
  --max-lora-modules 8 `
  --no-prepare-smoke-data `
  --save-lora-path D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_save_load_1step_save\lora_adapter.pt
```

결과:

| 항목 | 값 |
| --- | ---: |
| status | success |
| steps_completed | 1 |
| first_loss | 0.6681870222091675 |
| final_loss | 0.6681870222091675 |
| loss_nan | false |
| lora_adapter_saved | true |
| lora_state_dict_key_count | 16 |
| lora_adapter_file_size_mb | 0.1236 |
| peak_vram_mb | 8887.85 |
| error | null |

생성된 adapter:

```text
backend/training/outputs/stableviton_lora_save_load_1step_save/lora_adapter.pt
```

위 파일은 generated model artifact이므로 Git에 포함하지 않는다.

## 5. 1-step load smoke

실행:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_save_load_1step_load `
  --max-steps 1 `
  --batch-size 1 `
  --max-lora-modules 8 `
  --no-prepare-smoke-data `
  --load-lora-path D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_save_load_1step_save\lora_adapter.pt
```

결과:

| 항목 | 값 |
| --- | ---: |
| status | success |
| steps_completed | 1 |
| first_loss | 0.037538886070251465 |
| final_loss | 0.037538886070251465 |
| loss_nan | false |
| lora_adapter_loaded | true |
| lora_adapter_loaded_key_count | 16 |
| lora_state_dict_key_count | 16 |
| lora_adapter_file_size_mb | 0.1236 |
| load_missing_keys | [] |
| load_unexpected_keys | [] |
| load_shape_mismatch_keys | [] |
| peak_vram_mb | 8887.85 |
| error | null |

Load smoke 기준으로 저장된 adapter key와 현재 삽입된 LoRA module key가 정확히 맞았다.

## 6. 9995-step adapter save 결과

1-step save/load smoke 이후 같은 runner로 9995-step adapter save run을 실행했다. 이 실행은 전체 StableVITON checkpoint나 generated sample을 저장하지 않고, LoRA adapter parameter만 `lora_adapter.pt`로 저장하는 목적이다.

실행 명령:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_10k_adapter_save `
  --max-steps 9995 `
  --batch-size 1 `
  --max-lora-modules 8 `
  --no-prepare-smoke-data `
  --save-lora-path D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_10k_adapter_save\lora_adapter.pt
```

결과:

| 항목 | 값 |
| --- | ---: |
| status | success |
| train_dataset_len | 9995 |
| steps_completed | 9995 |
| first_loss | 0.9184726476669312 |
| final_loss | 0.3207787275314331 |
| loss_nan | false |
| elapsed_sec | 10720.0626 |
| avg_step_time_sec | 1.0725 |
| peak_vram_mb | 8887.85 |
| lora_adapter_saved | true |
| lora_state_dict_key_count | 16 |
| lora_adapter_file_size_mb | 0.1236 |
| checkpoint_created | false |
| sample_created | false |
| error | null |

생성된 adapter:

```text
backend/training/outputs/stableviton_lora_10k_adapter_save/lora_adapter.pt
```

이 파일은 generated model artifact이므로 Git에 포함하지 않는다. Summary JSON, stdout/stderr log, checkpoint/sample output도 Git에 포함하지 않는다.

## 7. Baseline vs LoRA inference comparison 준비

이번 작업으로 LoRA adapter 저장/로드 contract와 9995-step adapter 저장 결과를 확보했다. 다음 단계에서 필요한 작업은 아래와 같다.

- StableVITON inference path에서 LoRA adapter 삽입 후 load 가능하도록 runner 분리
- 동일 pair 기준 StableVITON baseline output 생성
- 동일 pair 기준 LoRA adapter loaded output 생성
- 결과 이미지를 `backend/demo/assets/**`에 배치
- `scripts/validate_demo_assets.py --strict` 실행
- Artifact Compare / Model Compare API와 frontend에 연결

이번 문서의 9995-step adapter save 결과는 adapter 파일 생성과 load 가능한 학습 artifact 확보를 의미한다. 실제 착장 품질 개선 여부는 아직 baseline vs LoRA inference comparison으로 검증해야 한다.

## 8. Git safety

Git 포함 대상:

- `README.md`
- `docs/experiments/pc3_stableviton_lora_save_load_inference_comparison.md`

Git에 포함하지 않는 항목:

- `backend/datasets/**`
- `backend/training/outputs/**`
- `backend/outputs/**`
- `backend/logs/**`
- `*.pt`
- checkpoint
- generated image
- logs
- summary json
