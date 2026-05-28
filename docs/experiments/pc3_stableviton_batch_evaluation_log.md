# PC3 StableVITON batch evaluation 및 failure case 수집 로그

## 1. 실험 목적

이 문서는 PC3에서 StableVITON batch evaluation을 수행할 때 사용할 실험 로그 템플릿입니다.

목적은 여러 person / garment pair에 대해 StableVITON 결과를 batch로 확인하고, 성공 케이스와 실패 케이스를 구분해서 기록하는 것입니다. 수집한 failure case는 이후 fit confidence score, fit explanation, annotation hotspot 설계에 활용합니다.

결과 이미지 자체는 Git에 올리지 않습니다. StableVITON output image, 중간 preprocessing artifact, dataset image는 로컬 ignored 경로에만 저장합니다.

## 2. 현재 전제

현재 프로젝트 상태는 다음과 같습니다.

- #14에서 StableVITON wrapper가 backend에 연결되었습니다.
- #48에서 uploaded image 기반 input adapter는 PR 리뷰 대기 중입니다.
- PC3 batch evaluation은 실제 대량 실험 전, 실험 기록 양식을 먼저 정리하는 단계입니다.
- DensePose / agnostic / mask artifact가 부족하면 성공 케이스가 아니라 실패 케이스로 기록해야 합니다.

이번 문서는 실제 batch inference 실행 결과가 아닙니다. 실행 환경, pair list, 성공/실패 케이스, failure type, confidence 설계 관찰 포인트를 일관되게 기록하기 위한 템플릿입니다.

## 3. 실행 환경 기록 양식

| 항목 | 값 |
| --- | --- |
| OS | TBD |
| GPU | TBD |
| Python | TBD |
| PyTorch | TBD |
| CUDA | TBD |
| conda env | TBD |
| StableVITON external repo path | TBD |
| StableVITON commit hash | TBD |
| fit-reasoning-vton commit hash | TBD |
| checkpoint path | TBD |
| data root | TBD |
| output root | TBD |

## 4. batch pair 목록 형식

batch pair list는 CSV로 관리합니다. 실제 이미지 경로나 private dataset 이름이 아니라, 실험 실행자가 로컬에서 해석할 수 있는 파일명 또는 로컬 상대 경로를 사용합니다.

권장 컬럼:

```csv
case_id,person_image,cloth_image,mode,expected_note
case_001,person_001.png,cloth_001.png,unpaired,basic smoke pair
case_002,person_002.png,cloth_002.png,unpaired,pose variation
```

컬럼 의미:

| 컬럼 | 설명 |
| --- | --- |
| `case_id` | 실험 케이스 식별자입니다. 결과 기록 표와 output directory 이름을 연결할 때 사용합니다. |
| `person_image` | 사람 이미지 파일명 또는 로컬 상대 경로입니다. 실제 이미지 파일은 Git에 포함하지 않습니다. |
| `cloth_image` | 의류 이미지 파일명 또는 로컬 상대 경로입니다. 실제 이미지 파일은 Git에 포함하지 않습니다. |
| `mode` | `paired` 또는 `unpaired`입니다. 서로 다른 person/cloth 조합이면 `unpaired`로 기록합니다. |
| `expected_note` | 예상 관찰 포인트입니다. 예: 기본 smoke pair, pose variation, fit confidence review candidate |

example template:

- [pc3_batch_pairs.example.csv](templates/pc3_batch_pairs.example.csv)

## 5. 실행 명령어 기록 양식

아래 명령어는 예정 명령어입니다. 실제 batch runner script는 아직 확정되지 않았습니다.

```powershell
# 예정 명령어
D:\conda-envs\vton\python.exe scripts\run_stableviton_batch_eval.py `
  --stableviton-root D:\GitHub\StableVITON `
  --pair-list <local_pair_list.csv> `
  --output-root <ignored_output_root>
```

실제 실행 시 기록할 항목:

| 항목 | 값 |
| --- | --- |
| 실행 일시 | TBD |
| 실행자 / PC | PC3 |
| 실행 명령어 | TBD |
| pair list path | TBD |
| output root | TBD |
| batch size | TBD |
| denoise steps | TBD |
| image size | TBD |
| mode | paired / unpaired / mixed |

## 6. 결과 기록 표

status 후보:

- `success`
- `failed_preprocess`
- `failed_inference`
- `failed_output_missing`
- `skipped`

failure_type 후보:

- `DENSEPOSE_MISSING`
- `AGNOSTIC_IMAGE_MISSING`
- `AGNOSTIC_MASK_MISSING`
- `CLOTH_MASK_MISSING`
- `INFERENCE_ERROR`
- `OUTPUT_NOT_FOUND`
- `LOW_QUALITY_RESULT`

결과 기록 표:

| case_id | person_image | cloth_image | status | output_path | elapsed_seconds | max_vram_mib | failure_type | failure_message | review_note |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| case_001 | person_001.png | cloth_001.png | TBD | `<ignored_output_root>/case_001/result.png` | TBD | TBD | TBD | TBD | TBD |
| case_002 | person_002.png | cloth_002.png | TBD | `<ignored_output_root>/case_002/result.png` | TBD | TBD | TBD | TBD | TBD |

`output_path`는 로컬 ignored 경로만 기록합니다. 결과 이미지를 Markdown image로 직접 삽입하거나 Git에 추가하지 않습니다.

## 7. failure case 분류 기준

| 분류 | 기준 |
| --- | --- |
| preprocessing artifact 부족 | DensePose, agnostic image, agnostic mask, cloth mask 등 StableVITON 필수 입력 artifact가 없는 경우 |
| inference 실행 오류 | StableVITON subprocess가 non-zero exit code로 종료되거나 CUDA/runtime error가 발생한 경우 |
| output image 미생성 | inference가 끝났지만 expected output image가 생성되지 않은 경우 |
| 품질 저하 결과 | output은 생성됐지만 착장 결과 품질이 낮아 confidence 설계에서 별도 처리해야 하는 경우 |
| 몸/옷 정렬 실패 | 의류 중심선, 어깨선, 몸통 위치가 person body와 맞지 않는 경우 |
| 팔/소매 영역 왜곡 | 팔이 사라지거나 소매가 팔 위치와 어긋나거나 피부/소매 경계가 비정상적인 경우 |
| 상체/몸통 영역 왜곡 | torso shape, waist, chest 영역이 과도하게 변형되는 경우 |
| 옷 길이/핏 판단이 어려운 결과 | 상의 총장, 소매 길이, 품/너비를 판단하기 어려운 경우 |

## 8. fit confidence 설계에 활용할 관찰 포인트

batch evaluation에서 아래 항목을 관찰하고, 이후 confidence score skeleton 또는 rule 설계에 반영합니다.

| 관찰 포인트 | 기록 기준 |
| --- | --- |
| 어깨선 정렬 | 의류 어깨선이 person shoulder 위치와 얼마나 잘 맞는지 기록합니다. |
| 몸통 폭과 의류 폭 | 옷의 torso width가 몸통에 비해 과도하게 넓거나 좁은지 확인합니다. |
| 소매 길이 | 소매 끝 위치가 팔 길이와 자연스럽게 맞는지 확인합니다. |
| 상의 총장 | 옷 밑단 위치가 torso / hip 기준에서 자연스러운지 확인합니다. |
| 팔/몸통 occlusion | 팔이 옷에 의해 비정상적으로 가려지거나 사라지는지 확인합니다. |
| 옷 영역 왜곡 | 로고, 패턴, 단추, 옷 주름이 심하게 찌그러지는지 기록합니다. |
| 배경/피부 영역 침범 | 옷 mask가 배경 또는 피부 영역을 과도하게 침범하는지 확인합니다. |
| 결과 이미지 신뢰도 | 사용자가 fit 판단에 활용할 수 있을 정도로 결과가 안정적인지 기록합니다. |

## 9. Git safety rule

아래 항목은 절대 Git에 포함하지 않습니다.

```text
*.ckpt
DATA/**
samples_smoke/**
backend/outputs/**
backend/logs/**
stableviton_raw/**
*.jpg
*.jpeg
*.png
*.webp
```

Git에 포함 가능한 항목:

- `docs/**`
- `*.example.csv`
- 실험 로그 템플릿
- 실제 경로가 제거된 예시 파일

실험 후 커밋 전에는 아래 명령으로 tracked 대상과 ignored output을 확인합니다.

```powershell
git status
git status --ignored -s
git ls-files --others --exclude-standard
```

## 10. 다음 단계

1. PC3 실행 환경 확인
2. batch pair list 준비
3. 소량 batch smoke test
4. 성공/실패 케이스 기록
5. failure pattern 분류
6. confidence score skeleton 또는 rule 설계에 반영
