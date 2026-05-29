# AIHub 데이터 활용 계획

## 1. 목적

이 문서는 AIHub 쉐이프리스 의류 및 포즈 데이터를 Fit-aware Virtual Try-On 프로젝트에서 어떻게 사용할지 정리한다.

이번 방향의 핵심은 다음과 같다.

- AIHub 데이터는 `fit analyzer`의 기준 데이터로 사용한다.
- StableVITON은 사용자 이미지와 의류 이미지 기반 가상 착장 이미지 생성 backbone으로 유지한다.
- AIHub annotation을 활용해 fit feature, confidence score, fit explanation, annotation hotspot 기준을 설계한다.
- 가능하면 AIHub pair 구조를 LoRA smoke training 후보 manifest에도 활용한다.

이번 작업은 문서와 예시 schema 정리이며, 실제 AIHub raw parsing, StableVITON 실행, GPU inference, LoRA 학습은 수행하지 않는다.

## 2. 프로젝트 내 역할

### StableVITON

- 사용자 이미지와 의류 이미지를 입력으로 받아 result image를 생성한다.
- MVP에서는 VTON image generation backbone 역할을 담당한다.
- fit 판단 자체를 StableVITON 내부에 넣지 않고, 생성 결과 이후의 분석 단계와 분리한다.

### AIHub

- keypoint, segmentation, metadata, pair annotation 기반 fit feature 생성 기준으로 사용한다.
- confidence rule 설계에 활용한다.
- hotspot annotation 후보 생성에 활용한다.
- LoRA 학습 후보 pair manifest 설계에 활용할 수 있다.

### Backend

- PC2에서 전달한 `fit.json` 또는 `features.csv`를 읽어 `/api/result/{job_id}` 응답에 연결한다.
- 현재 backend의 fit analyzer는 placeholder이며, 실제 계산 결과를 읽는 loader는 후속 작업에서 설계한다.
- 조회 API 응답에는 confidence, fit label, fit score, explanation, annotation hotspot이 포함될 수 있다.

### Frontend

- result image를 표시한다.
- confidence score와 confidence level을 표시한다.
- fit label과 fit explanation을 표시한다.
- annotation hotspot overlay를 result image 위에 표시한다.

## 3. AIHub 데이터 구성 요약

AIHub 쉐이프리스 의류 및 포즈 데이터에서 fit analyzer 설계에 사용할 수 있는 주요 정보는 다음과 같다.

| 구분 | 사용 후보 |
| --- | --- |
| image path | 원본 또는 processed subset의 이미지 경로 참조 |
| model_id | 모델 단위 grouping, pair mapping, split 기준 |
| cloth_id | 의류 단위 grouping, pair mapping, category 기준 |
| angle | 정면, 측면, 좌우 회전 등 view 조건 |
| pose | pose class 또는 촬영 포즈 조건 |
| segmentation_class | 신체 부위와 의류 영역 class 정의 |
| keypoint_class | 어깨, 팔꿈치, 손목, 골반, 무릎, 발목 등 keypoint 정의 |
| annotation.segmentation | 의류 영역, 신체 영역 mask 기반 feature 계산 후보 |
| annotation.keypoint | 신체 keypoint 기반 shoulder, sleeve, torso, length feature 계산 후보 |
| pair annotation | 제품 이미지, 모델 이미지, 실제 착용 결과 이미지 연결 |
| model metadata | 모델 속성, pose 조건, 품질 필터 후보 |
| cloth metadata | 의류 type, fit, category, 소재 또는 기타 속성 후보 |

pair annotation 구조는 다음 개념으로 사용한다.

```text
from: 제품 이미지 경로
to: 모델 이미지 경로
result: to의 모델이 from 제품을 착용한 이미지 경로
```

이 구조는 fit analyzer의 기준 feature를 검토할 때 `제품 이미지`, `모델 이미지`, `실제 착용 결과 이미지`를 연결하는 근거가 된다. 단, 실제 파일과 원본 JSON은 GitHub에 포함하지 않는다.

## 4. 사용하지 않을 것

다음 항목은 본 저장소와 PR에 포함하지 않는다.

- 원본 AIHub 이미지
- 원본 AIHub JSON
- processed image
- StableVITON checkpoint
- LoRA checkpoint
- generated image
- 실제 dataset CSV
- 실제 annotation artifact

공개 저장소에는 문서, schema, example JSON/CSV만 포함한다. `docs/examples/*.json`, `docs/examples/*.csv`는 실제 데이터가 아닌 예시만 포함한다.

## 5. PC2에서 PC3 전달 방식

PC2는 AIHub raw 전체를 PC3로 넘기지 않고, 처리 목적이 명확한 processed subset만 전달한다.

전달 단계는 다음 순서로 확장한다.

| 단계 | 목적 |
| --- | --- |
| smoke10 | schema와 loader 연결을 검증하는 최소 subset |
| pilot1k | feature 계산과 label 분포를 확인하는 pilot subset |
| pilot5k | confidence rule과 hotspot 후보 품질을 점검하는 중간 규모 subset |
| pilot10k | backend와 frontend 연동 전 기준 분포를 확인하는 확장 subset |

PC2에서 PC3로 전달할 후보는 다음과 같다.

- `features.csv`
- `fit.json`
- hotspot annotations
- pair manifest
- contact sheet
- processed StableVITON input subset

전달하지 않을 것은 다음과 같다.

- AIHub raw 전체
- 원본 압축파일
- checkpoint
- generated image 전체

PC3는 전달받은 subset으로 backend loader와 `/api/result/{job_id}` 응답 연결을 테스트한다. StableVITON 실행 결과 전체를 GitHub에 올리지 않고, 필요한 경우 파일명과 관찰 로그만 문서화한다.

## 6. MVP 범위

MVP 필수 범위는 다음과 같다.

- AIHub annotation 기반 fit feature schema 정의
- `fit.json` schema 정의
- `features.csv` schema 정의
- backend fit analyzer loader 설계
- frontend result UI와 schema 정렬

가능하면 진행할 범위는 다음과 같다.

- AIHub pair 기반 LoRA smoke training 준비
- Base StableVITON vs LoRA 결과 비교 문서화

LoRA는 MVP 필수 범위가 아니라 optional experiment track이다. LoRA가 실패하거나 준비 비용이 커지면 MVP 일정에는 포함하지 않고, fit analyzer schema와 confidence UI 연결을 우선한다.

## 7. README 수정 필요 후보

현재 README는 StableVITON을 main backbone으로 두고, AIHub를 fit analyzer와 confidence 기준 설계에 활용하며, LoRA를 MVP 필수 기능에서 제외한다고 설명한다. 이번 문서 방향과 큰 충돌은 없다.

후속 PR에서 검토할 수 있는 후보는 다음과 같다.

- 주요 문서 목록에 `docs/aihub/aihub_dataset_usage_plan.md` 추가
- 주요 문서 목록에 `docs/aihub/aihub_annotation_schema_mapping.md` 추가
- LoRA 설명에 `optional experiment track`과 AIHub pair 기반 smoke training 가능성 추가
