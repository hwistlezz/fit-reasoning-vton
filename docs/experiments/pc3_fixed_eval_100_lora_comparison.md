# PC3 fixed_eval_100 LoRA comparison

## 0. Follow-up: EXIF orientation issue

대표 contact sheet를 확인한 뒤 `EP00000002`를 포함한 일부 입력 이미지가 왼쪽으로 회전된 상태로 평가셋에 들어간 것을 확인했다. raw AIHub 이미지에는 EXIF orientation이 남아 있었지만, 기존 layout/fixed_eval 생성 과정에서 `ImageOps.exif_transpose()`를 적용하지 않고 resize/save하면서 person/target 이미지의 실제 픽셀 방향이 잘못 고정됐다.

확인한 대표 사례:

- raw `image/EP00000002.jpg`: EXIF orientation `6`
- raw `worn/EP00000002.jpg`: EXIF orientation `6`
- raw `cloth/EP00000002.jpg`: EXIF orientation `8`
- 기존 `stableviton_aihub_10k_layout_10k_train/train/image/EP00000002.jpg`: EXIF 제거 후 왼쪽 회전 상태
- agnostic / densepose 계열 artifact는 upright 상태

따라서 기존 fixed_eval_100 inference와 PSNR/SSIM 표는 **실행 파이프라인이 100개 pair를 처리했다는 기록**으로만 유지한다. 입력 이미지와 artifact의 좌표계가 섞인 상태였기 때문에, 아래 수치는 최종 adapter 선택 근거로 사용하지 않는다. fixed_eval_100은 EXIF orientation 보정이 반영된 layout으로 재생성한 뒤 다시 inference/metric/contact sheet를 만들어야 한다.

보정 내용:

- `prepare_stableviton_layout.py`: copy mode에서 image-like artifact를 `ImageOps.exif_transpose()` 후 384x512로 저장
- `build_fixed_eval_set.py`: fixed eval layout 생성 시 EXIF orientation 적용
- `run_saved_lora_inference_comparison.py`: inference data 준비 시 EXIF orientation 적용
- `run_stableviton_lora_tiny_smoke.py`: smoke dataset shape 보정 시 EXIF orientation 적용
- `evaluate_lora_outputs.py`: metric 계산용 이미지 로드 시 EXIF orientation 적용

sanity 확인:

- raw artifact dataset에서 tiny3 layout을 재생성했고, `EP00000002`의 person / worn / agnostic / densepose가 모두 upright 상태로 저장되는 것을 확인했다.
- 보정된 tiny3 layout으로 baseline / rank4 LoRA inference가 성공했다.
- 다만 보정된 3개 pair에서도 garment alignment 품질은 아직 안정적이지 않았으므로, 방향 문제 수정과 별개로 inference quality는 후속 재평가가 필요하다.

## 1. 목적

이번 작업은 현재 보유한 StableVITON LoRA adapters를 같은 100개 pair 기준으로 비교하기 위한 fixed evaluation set을 구축하고, baseline StableVITON / rank4-module8 / rank8-module8 / rank8-module16 결과를 같은 조건에서 생성한 기록이다.

새 학습은 수행하지 않았다. 저장된 LoRA adapter를 load해서 inference만 수행했고, generated image, raw CSV, raw summary JSON, adapter, checkpoint, log는 Git에 포함하지 않았다.

## 2. 왜 10개 pair만으로는 부족한가

이전 rank/module ablation은 fixed 10 pair 기준으로 빠르게 확인하는 목적이었다. 하지만 10개 pair는 pose, cloth color, garment boundary, body orientation, occlusion 케이스를 충분히 포함하지 못한다.

이번 fixed_eval_100은 다음 목적을 가진다.

- 같은 입력 pair에서 4개 method를 반복 비교한다.
- single demo pair 중심의 관찰 편향을 줄인다.
- PSNR/SSIM 같은 기본 정량 지표를 계산한다.
- representative contact sheet로 visual review를 쉽게 한다.

## 3. Pair 선정 기준

사용 source layout:

```text
D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train
```

선정 스크립트:

```text
backend/training/scripts/build_fixed_eval_set.py
```

선정 조건:

- source split: `train`
- seed: `124`
- requested_count: `100`
- source_pair_count: `9995`
- ready_pair_count: `9995`
- selected_count: `100`
- duplicated pair_id 제거
- person image / cloth image / target worn / agnostic / agnostic mask / cloth mask / densepose / human parsing / openpose json 존재 확인

현재 10k layout은 `test_count=0`인 train-only layout이므로 이번 평가는 holdout이 아니다. 따라서 evaluation type은 **train-seen eval**이다. 이 결과는 adapter 간 동일 조건 비교에는 사용할 수 있지만, unseen generalization 성능으로 해석하면 안 된다.

생성된 local pair list:

```text
D:\GitHub\fit-reasoning-vton\backend\training\outputs\fixed_eval_100_lora_comparison\fixed_eval_100_pairs.txt
```

선정된 pair_id:

```text
EP00000002, EP00000044, EP00000111, EP00000163, EP00000303,
EP00000428, EP00000471, EP00000505, EP00000810, EP00000811,
EP00001115, EP00001295, EP00001302, EP00001488, EP00001539,
EP00001551, EP00002069, EP00002147, EP00002370, EP00002584,
EP00002949, EP00003066, EP00003117, EP00003183, EP00003224,
EP00003295, EP00003306, EP00003460, EP00003541, EP00003679,
EP00003936, EP00004219, EP00004365, EP00004542, EP00004707,
EP00004787, EP00004881, EP00005874, EP00005999, EP00006178,
EP00006567, EP00006584, EP00006762, EP00007299, EP00007376,
EP00007386, EP00007481, EP00007521, EP00007581, EP00007861,
EP00008089, EP00008205, EP00008371, EP00008465, EP00008636,
EP00008661, EP00008752, EP00008798, EP00009285, EP00009336,
EP00009387, EP00009391, EP00009420, EP00009433, EP00010150,
EP00011927, EP00013267, EP00015159, EP00015771, EP00016417,
EP00018861, EP00018979, EP00019633, EP00022673, EP00023236,
EP00023609, EP00023814, EP00023955, EP00025089, EP00025167,
EP00025276, EP00025402, EP00025408, EP00025716, EP00025819,
EP00025946, EP00026009, EP00026074, EP00026131, EP00026186,
EP00026195, EP00026253, EP00026370, EP00026439, EP00026521,
EP00026524, EP00026977, EP00027054, EP00027284, EP00027558
```

## 4. 비교 대상 method

| Method | Adapter path | Role |
| --- | --- | --- |
| baseline StableVITON | - | StableVITON checkpoint only |
| rank4-module8 | `backend/training/outputs/stableviton_lora_10k_adapter_save/lora_adapter.pt` | 기존 10k saved LoRA adapter |
| rank8-module8 | `backend/training/outputs/stableviton_lora_ablation_rank8_module8/lora_adapter.pt` | rank 8, 8 target modules |
| rank8-module16 | `backend/training/outputs/stableviton_lora_ablation_rank8_module16/lora_adapter.pt` | rank 8, 16 target modules |

각 adapter 파일은 local output에만 존재하며 Git에는 포함하지 않는다.

## 5. Inference 실행 결과

공통 조건:

- data_root: `backend/training/outputs/fixed_eval_100_lora_comparison/fixed_eval_100_data`
- pair_count: `100`
- denoise_steps: `50`
- batch_size: `1`
- output_root: `backend/training/outputs/fixed_eval_100_lora_comparison`

| Method | output_count | failure_count | success_rate | adapter_loaded | missing_keys | unexpected_keys | shape_mismatch |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| baseline StableVITON | 100 | 0 | 1.0 | false | - | - | - |
| rank4-module8 | 100 | 0 | 1.0 | true | `[]` | `[]` | `[]` |
| rank8-module8 | 100 | 0 | 1.0 | true | `[]` | `[]` | `[]` |
| rank8-module16 | 100 | 0 | 1.0 | true | `[]` | `[]` | `[]` |

Runtime summary:

| Method | elapsed_sec | avg_inference_time_sec | peak_vram_mb | loaded_lora_keys | adapter_file_size_mb |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline StableVITON | 1225.9229 | 12.2592 | 7841.9 | 0 | - |
| rank4-module8 | 1140.6531 | 11.4065 | 7859.35 | 16 | 0.1236 |
| rank8-module8 | 1138.9761 | 11.3898 | 7842.14 | 16 | 0.2408 |
| rank8-module16 | 1358.0731 | 13.5807 | 7842.65 | 32 | 0.7546 |

## 6. 정량 지표

평가 스크립트:

```text
backend/training/scripts/evaluate_lora_outputs.py
```

기준 이미지:

```text
fixed_eval_100_data/test/worn/{pair_id}.jpg
```

계산 조건:

- generated output과 target/worn image 크기가 다르면 target 크기에 맞게 resize한 뒤 계산했다.
- PSNR/SSIM은 RGB 이미지 기준으로 계산했다.
- SSIM은 lightweight global SSIM으로 계산했다.
- LPIPS는 현재 `D:\conda-envs\vton` 환경에 설치되어 있지 않아 skip했다. 새 package나 pretrained metric weight는 설치하지 않았다.

| Method | PSNR mean | SSIM mean | LPIPS |
| --- | ---: | ---: | --- |
| baseline StableVITON | 14.990364 | 0.130425 | skipped |
| rank4-module8 | 14.965571 | 0.124778 | skipped |
| rank8-module8 | 14.966314 | 0.123503 | skipped |
| rank8-module16 | 15.294206 | 0.160138 | skipped |

이번 fixed_eval_100의 PSNR/SSIM 기준으로는 rank8-module16이 가장 높은 평균값을 보였다. 다만 위 Follow-up에서 확인한 EXIF orientation mismatch 때문에 이 표는 최종 adapter 선택 근거로 사용하지 않는다. 또한 PSNR/SSIM은 target/worn image와의 pixel-level 유사도에 가까운 지표이며, garment boundary, identity preservation, texture artifact, body distortion 같은 visual quality와 항상 일치하지 않는다.

## 7. Representative contact sheet

대표 20개 pair contact sheet 구성:

```text
person | cloth | target/worn | baseline | rank4-module8 | rank8-module8 | rank8-module16
```

생성 위치:

```text
D:\GitHub\fit-reasoning-vton\backend\training\outputs\fixed_eval_100_lora_comparison\contact_sheet\fixed_eval_100_sample20_contact_sheet.jpg
```

contact sheet 이미지 파일은 generated output이므로 Git에 포함하지 않았다.

## 8. Best adapter 후보

이번 100-pair 정량 평가 기준:

- PSNR mean 최고: rank8-module16
- SSIM mean 최고: rank8-module16
- inference success rate: 네 method 모두 1.0

기존 결과만 보면 fixed_eval_100의 정량 지표 기준 best adapter 후보는 **rank8-module16**이었다. 그러나 EXIF orientation mismatch가 확인되었으므로 이 결론은 **provisional**로만 남기고, 최종 후보 재선정은 보정된 fixed_eval_100 재실행 후 진행한다.

다만 이전 10-pair qualitative ablation에서는 rank8-module16이 일부 pair에서 texture artifact가 더 눈에 띈다는 관찰이 있었다. 최종 demo model을 고르려면 fixed_eval_100 contact sheet를 기준으로 사람 검수 visual review를 함께 수행해야 한다.

## 9. 다음 단계

- EXIF orientation 보정이 반영된 layout으로 fixed_eval_100을 재생성한다.
- 보정된 fixed_eval_100으로 baseline / rank4 / rank8-module8 / rank8-module16 inference를 다시 실행한다.
- 보정된 fixed_eval_100 contact sheet를 사람 기준으로 review한다.
- rank8-module16과 rank8-module8의 visual failure case를 pair별로 분류한다.
- LPIPS 또는 perceptual metric 환경을 별도로 준비해 재평가한다.
- demo에 사용할 pair 3-5개를 fixed_eval_100에서 선별한다.
- selected result만 `backend/demo/assets/**`에 배치하고 `validate_demo_assets.py --strict`를 실행한다.
- README에는 fixed_eval_100의 요약 결과만 유지하고 raw output은 Git에 포함하지 않는다.

## 10. Git safety

Git 포함 대상:

- `backend/training/scripts/build_fixed_eval_set.py`
- `backend/training/scripts/evaluate_lora_outputs.py`
- `docs/experiments/pc3_fixed_eval_100_lora_comparison.md`
- `README.md`

Git 미포함 대상:

- `backend/datasets/**`
- `backend/training/outputs/**`
- `backend/outputs/**`
- `*.pt`, `*.pth`, `*.ckpt`, `*.safetensors`
- generated `*.jpg`, `*.png`, `*.webp`
- raw metric `*.csv`
- raw summary `*.json`
- logs
