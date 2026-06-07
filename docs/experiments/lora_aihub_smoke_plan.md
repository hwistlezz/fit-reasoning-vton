# AIHub 기반 LoRA Smoke Training 계획

## 1. 목적

AIHub pair annotation을 활용해 StableVITON 또는 관련 VTON 모델에 LoRA smoke training을 적용할 수 있는지 조사한다.

LoRA는 MVP 필수 작업이 아니라 optional experiment track이다. MVP의 중심은 StableVITON result image 생성, AIHub 기반 fit analyzer schema, confidence, explanation, hotspot UI 연결이다.

## 2. LoRA를 메인 MVP와 분리하는 이유

LoRA를 MVP 필수 범위로 넣지 않는 이유는 다음과 같다.

- 학습 포맷 변환이 필요하다.
- checkpoint와 dataset 용량이 크다.
- preprocessing artifact가 필요하다.
- 실패 시 MVP 일정이 밀릴 수 있다.

따라서 LoRA 작업은 문서화, manifest 설계, config skeleton 수준을 최소 성공 기준으로 두고, 실제 학습은 PC3에서 시간이 남을 때 smoke training으로만 시도한다.

## 3. AIHub Pair Annotation 활용 가능성

AIHub pair annotation은 다음 구조를 가진다.

```text
from: 제품 이미지
to: 모델 이미지
result: 실제 착용 결과 이미지
```

이 구조는 VTON 학습 pair 후보로 활용할 수 있다.

- `from`은 garment image 후보가 된다.
- `to`는 person image 후보가 된다.
- `result`는 target 착장 이미지 후보가 된다.

다만 StableVITON의 실제 학습 포맷은 모델이 요구하는 segmentation, agnostic image, densepose 또는 pose artifact, mask naming convention을 요구할 수 있다. AIHub pair가 바로 StableVITON training sample이 된다고 가정하지 않는다.

PC3는 먼저 pair manifest만 설계하고, StableVITON 학습 입력 포맷과의 차이를 확인한 뒤 smoke training 가능성을 판단한다.

## 4. LoRA Smoke Training 단계

| 단계 | 작업 | 산출물 후보 |
| --- | --- | --- |
| LoRA-0 | 학습 가능성 문서화 | 모델 요구 input, 필요한 preprocessing artifact 목록 |
| LoRA-1 | AIHub pair manifest에서 100개 subset 후보 생성 | `lora_pair_manifest.example.csv` 또는 local-only manifest |
| LoRA-2 | StableVITON 학습 입력 포맷 차이 확인 | format gap note |
| LoRA-3 | `config/example.yaml` 작성 | local config skeleton |
| LoRA-4 | `train_lora_smoke.py` skeleton 작성 | 실행 전 skeleton 또는 pseudo runner |
| LoRA-5 | PC3에서 10~100개 smoke training 시도 | local log, checkpoint는 Git 제외 |
| LoRA-6 | Base vs LoRA 결과 3~10개 비교 | 파일명과 관찰 로그만 문서화 |

실제 데이터, checkpoint, generated image는 GitHub에 올리지 않는다.

## 5. 성공 기준

### 최소 성공

- LoRA 학습 가능성 문서화
- subset manifest 설계
- config skeleton 작성

### 좋은 성공

- 10~100개 subset으로 smoke training 1회 실행
- checkpoint는 Git에 올리지 않음
- Base vs LoRA 결과 파일명과 관찰 로그만 기록

LoRA 결과가 MVP 품질을 보장하지 않아도 된다. 이 track의 목적은 가능성과 비용을 확인하는 것이다.

## 6. Git Safety

다음 항목은 Git에 포함하지 않는다.

- `*.ckpt`
- `*.pth`
- `*.pt`
- `*.safetensors`
- AIHub raw dataset
- AIHub 원본 JSON
- processed dataset
- generated image
- LoRA output image
- training logs 중 대용량 artifact

Git에 포함 가능한 것은 다음으로 제한한다.

- 계획 문서
- example schema
- 실제 데이터가 없는 config example
- 실제 경로를 제거한 manifest example
- 관찰 로그 문서

실제 smoke training을 수행하더라도 checkpoint와 결과 이미지는 local 또는 별도 storage에서 관리하고, PR에는 파일명과 관찰 내용만 남긴다.
