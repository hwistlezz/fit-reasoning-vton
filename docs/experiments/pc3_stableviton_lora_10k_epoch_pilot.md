# PC3 StableVITON LoRA 10k epoch pilot

## 1. 목적

PR #105에서 구현한 StableVITON LoRA tiny10 1-step smoke runner를 10k StableVITON layout dataset으로 확장하여, PC3 환경에서 LoRA 10k 1 epoch pilot이 실제로 끝까지 실행 가능한지 확인했다.

이번 작업은 StableVITON 전체 full fine-tuning이 아니다. StableVITON 모델 내부 일부 Linear attention module에 lightweight LoRA adapter를 삽입하고, LoRA parameter만 trainable 상태로 둔 pilot 실행이다.

## 2. 선행 결과

PR #105의 tiny10 1-step smoke에서 아래를 확인했다.

- StableVITON checkpoint load 성공
- tiny10 dataset load 성공
- LoRA adapter 삽입 성공
- inserted_lora_module_count=8
- total_params=1,838,680,959
- trainable_params_after_lora=30,720
- loss_nan=false
- checkpoint/sample/generated image 저장 비활성화

## 3. 10k layout 준비 결과

입력 dataset:

```text
backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full
```

출력 layout:

```text
backend/datasets/stableviton_aihub_10k_layout_10k_train
```

처음에는 `prepare_stableviton_layout.py --mode copy --limit 9995 --test-ratio 0 --require-densepose`로 full copy를 시도했지만, 약 30분 후 timeout이 발생했다. timeout 시점에는 약 2,313개 sample만 일부 복사됐고 `train_pairs.txt`, `test_pairs.txt`, `layout_summary.json`은 아직 생성되지 않았다.

제출 시간 내 학습 로그 확보를 우선하기 위해 optimized layout 생성을 사용했다. 단, 원본 dataset은 수정하지 않았다.

- source dataset 내부 파일 resize/overwrite/delete/rename 금지 유지
- image 계열 파일은 output layout에 별도 resize/copy 파일로 생성
- `--no-prepare-smoke-data`를 학습 실행에 사용하여 runner가 data-root를 다시 resize하지 않게 처리
- 이후 hardlink 정책 재확인 후 `worn`, `image-parse` output 파일은 실제 copy로 교체
- 최종 hardlink 사용은 수정되지 않는 metadata 계열인 `fit`, `openpose-json`으로 제한

최종 layout summary:

| 항목 | 값 |
| --- | ---: |
| selected_count | 9995 |
| train_count | 9995 |
| test_count | 0 |
| ready_count | 9995 |
| not_ready_count | 0 |
| copied_count | 9995 |
| layout_prepare_elapsed_sec | 3534.8355 |

## 4. Runner 변경

수정 파일:

```text
backend/training/scripts/run_stableviton_lora_tiny_smoke.py
```

추가한 옵션:

```text
--no-prepare-smoke-data
```

이 옵션은 이미 준비된 10k layout을 다시 resize하지 않기 위해 추가했다. 1-step sanity, 100-step benchmark, 9995-step 1 epoch pilot 모두 이 옵션을 사용했다.

## 5. 1-step sanity 결과

실행:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_10k_1step_sanity `
  --max-steps 1 `
  --batch-size 1 `
  --max-lora-modules 8 `
  --no-prepare-smoke-data
```

결과:

| 항목 | 값 |
| --- | ---: |
| status | success |
| train_dataset_len | 9995 |
| steps_completed | 1 |
| first_loss | 0.019643109291791916 |
| final_loss | 0.019643109291791916 |
| loss_nan | false |
| elapsed_sec | 83.1632 |
| avg_step_time_sec | 83.1632 |
| peak_vram_mb | 8887.85 |
| checkpoint_created | false |
| sample_created | false |

1-step의 `avg_step_time_sec`는 model/config/checkpoint loading 비용을 포함한다.

## 6. 100-step benchmark 결과

실행:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_10k_100step_benchmark `
  --max-steps 100 `
  --batch-size 1 `
  --max-lora-modules 8 `
  --no-prepare-smoke-data
```

결과:

| 항목 | 값 |
| --- | ---: |
| status | success |
| train_dataset_len | 9995 |
| steps_completed | 100 |
| first_loss | 0.006902378983795643 |
| final_loss | 0.3011031448841095 |
| loss_nan | false |
| elapsed_sec | 140.859 |
| avg_step_time_sec | 1.4086 |
| peak_vram_mb | 8887.85 |
| checkpoint_created | false |
| sample_created | false |

100-step 결과 기준 estimated_full_9995_epoch_time:

```text
9995 * 1.4086 sec = 14078.957 sec = 약 234.65분 = 약 3시간 55분
```

## 7. 10k 1 epoch 결과

100-step benchmark 이후 1000-step pilot을 시작했지만, 10k 1 epoch 완료를 우선하기 위해 중단하고 9995-step 실행으로 전환했다.

실행:

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_10k_1epoch_pilot `
  --max-steps 9995 `
  --batch-size 1 `
  --max-lora-modules 8 `
  --no-prepare-smoke-data
```

결과:

| 항목 | 값 |
| --- | ---: |
| status | success |
| train_dataset_len | 9995 |
| target_steps | 9995 |
| steps_completed | 9995 |
| callback_steps_seen | 9995 |
| first_loss | 0.06275913864374161 |
| final_loss | 0.626366138458252 |
| loss_nan | false |
| elapsed_sec | 9946.5927 |
| avg_step_time_sec | 0.9952 |
| peak_vram_mb | 8887.85 |
| checkpoint_created | false |
| sample_created | false |
| error | null |

9995-step 1 epoch pilot은 완료됐다.

## 8. Parameter 상태

LoRA 삽입 및 trainable parameter 상태:

| 항목 | 값 |
| --- | ---: |
| total_params | 1,838,680,959 |
| trainable_params_after_lora | 30,720 |
| inserted_lora_module_count | 8 |

StableVITON 전체 모델이 아니라 LoRA adapter parameter만 학습 대상으로 둔 상태다.

## 9. 결론

- 10k train-only StableVITON layout 9995개가 valid 상태로 준비됐다.
- 1-step sanity가 성공했다.
- 100-step benchmark가 성공했다.
- 9995-step 1 epoch LoRA pilot이 성공했다.
- loss_nan=false로 확인됐다.
- peak_vram_mb=8887.85로 기록됐다.
- checkpoint/sample/generated image 저장은 비활성화했다.

이번 결과는 성능 개선 결과가 아니라, PC3 환경에서 StableVITON LoRA 10k 1 epoch pilot 실행이 가능한지 확인한 compatibility/training pipeline 결과다.

## 10. 현재 한계

- LoRA target module은 최대 8개 Linear module로 제한했다.
- 저장된 checkpoint가 없으므로 inference 성능 비교에는 바로 사용할 수 없다.
- generated sample image도 저장하지 않았다.
- 실제 발표용 이미지 생성은 별도 저장 정책과 demo asset validation을 적용해야 한다.
- LoRA target module 확장, rank/alpha 조정, checkpoint 저장 정책은 후속 작업에서 결정해야 한다.

## 11. 다음 단계

- LoRA checkpoint 저장 옵션 추가
- 동일 test pair 기반 inference/sample 생성
- StableVITON Original / 10k Basic Baseline / 10k Artifact LoRA 결과 비교
- `backend/demo/assets/**`에 발표용 asset 배치
- `scripts/validate_demo_assets.py --strict` 실행
- frontend demo compare 화면 연결

## 12. Git 미포함 확인

아래 항목은 Git에 포함하지 않는다.

- `backend/datasets/**`
- `backend/training/outputs/**`
- `backend/outputs/**`
- `backend/logs/**`
- checkpoint
- generated image
- logs
- summary json
- archive

Git 포함 대상은 아래 두 파일로 제한한다.

- `backend/training/scripts/run_stableviton_lora_tiny_smoke.py`
- `docs/experiments/pc3_stableviton_lora_10k_epoch_pilot.md`
