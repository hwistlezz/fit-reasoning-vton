# StableVITON preprocessing artifact 생성 pipeline 설계

## 1. 목적

이 문서는 이슈 #50의 설계 문서입니다. 목적은 StableVITON을 실제 업로드 이미지 기반으로 실행하기 전에 필요한 preprocessing artifact 생성 흐름을 정리하는 것입니다.

#14 service wrapper 이후 백엔드는 FastAPI에서 StableVITON CLI inference를 호출할 수 있고, prepared smoke data가 이미 준비되어 있으면 `result.png`를 생성한 뒤 `/api/result/{job_id}`에서 `result_image_url`을 반환할 수 있습니다.

하지만 prepared smoke data 기준 실행과 실제 `/api/tryon` 업로드 기반 inference는 다릅니다. StableVITON은 원본 person image와 cloth image 두 장만으로 바로 실행되지 않습니다. inference 전에 아래 artifact들이 StableVITON 입력 구조에 맞게 준비되어 있어야 합니다.

- `image-densepose`
- `agnostic-v3.2`
- `agnostic-mask`
- `cloth-mask`
- `test_pairs.txt`

따라서 이번 #50에서는 실제 DensePose, agnostic image, agnostic mask, cloth mask 생성 코드를 구현하지 않고, 어떤 단계에서 어떤 artifact가 만들어져야 하는지와 실패를 어떻게 처리할지 문서로 설계합니다.

## 2. StableVITON required input structure

StableVITON inference는 job별 data root가 아래 구조를 갖는다고 가정합니다.

```text
DATA/{job_data_root}/
  test_pairs.txt
  test/
    image/
    image-densepose/
    agnostic-v3.2/
    agnostic-mask/
    cloth/
    cloth-mask/
```

각 폴더의 역할은 다음과 같습니다.

| 경로 | 역할 |
| --- | --- |
| `test/image/` | 사용자가 업로드한 원본 person image를 저장합니다. StableVITON의 대상 인물 입력입니다. |
| `test/cloth/` | 사용자가 업로드한 원본 의류 image를 저장합니다. StableVITON이 입혀야 할 garment 입력입니다. |
| `test/cloth-mask/` | 의류 영역 mask를 저장합니다. StableVITON이 의류의 형태와 영역을 분리해서 사용하기 위해 필요합니다. |
| `test/image-densepose/` | person image의 DensePose 결과를 저장합니다. 인체 표면 대응 정보와 pose 조건으로 사용됩니다. |
| `test/agnostic-v3.2/` | 기존 옷 영역을 제거하거나 중립화한 person representation을 저장합니다. 새 의류를 합성할 수 있는 clothing-agnostic body context입니다. |
| `test/agnostic-mask/` | agnostic 영역 mask를 저장합니다. 기존 의류 또는 교체 대상 영역을 StableVITON에 알려주는 역할입니다. |
| `test_pairs.txt` | person image 파일명과 cloth image 파일명의 pair를 정의합니다. 업로드 job 1개 기준으로는 보통 한 줄만 생성합니다. |

job 하나에 대한 `test_pairs.txt` 예시는 다음과 같습니다.

```text
person.png cloth.png
```

## 3. 현재 #14 상태

#14 wrapper 기준 상태는 다음과 같습니다.

- FastAPI에서 StableVITON wrapper 호출이 가능합니다.
- prepared smoke data 기준으로 StableVITON inference를 실행할 수 있습니다.
- 성공 시 `backend/outputs/{job_id}/result.png` 생성 또는 복사가 가능합니다.
- `/api/result/{job_id}`에서 `result_image_url` 반환이 가능합니다.
- StableVITON 실행 stdout/stderr log 저장이 가능합니다.

아직 남은 문제는 upload image를 StableVITON-ready input으로 변환하는 pipeline이 없다는 점입니다.

현재 `/api/tryon`은 업로드된 person image와 cloth image를 backend output directory에 저장할 수 있지만, 이 파일들을 StableVITON이 요구하는 아래 artifact 구조로 자동 변환하지는 않습니다.

- `test/image/`
- `test/cloth/`
- `test/cloth-mask/`
- `test/image-densepose/`
- `test/agnostic-v3.2/`
- `test/agnostic-mask/`
- `test_pairs.txt`

즉 #14는 prepared smoke data를 대상으로 wrapper가 동작하는지 확인하는 단계이고, upload-based inference를 완성하려면 별도의 input adapter와 preprocessing pipeline이 필요합니다.

## 4. #48 input adapter와의 관계

#48은 StableVITON input adapter 구현 이슈로 분리하는 것이 적절합니다. #48의 책임은 model-dependent preprocessing이 아니라, 업로드 파일을 job별 StableVITON input root로 배치하고 검증하는 것입니다.

#48에서 담당할 작업:

- job별 StableVITON input root 생성
- uploaded person image를 `test/image/`로 복사
- uploaded cloth image를 `test/cloth/`로 복사
- `test_pairs.txt` 생성
- 필요한 artifact가 없으면 명확한 error 처리

#50에서 담당하는 설계 범위:

- DensePose / agnostic / mask artifact 생성 흐름 설계
- 어떤 artifact가 어떤 단계에서 만들어져야 하는지 정리
- 각 단계의 input/output/failure case 정리
- 향후 구현 단계를 나누기 위한 기준 제공

권장 분리는 다음과 같습니다.

```text
#48 input adapter
  upload 원본 파일
  -> job-scoped StableVITON input root skeleton
  -> test/image, test/cloth, test_pairs.txt

#50 preprocessing pipeline design
  DensePose / agnostic / cloth-mask / agnostic-mask 생성 흐름 정의
  -> artifact별 책임과 실패 처리 기준 정리

후속 preprocessing 구현
  실제 DensePose 실행
  실제 agnostic-v3.2 생성
  실제 agnostic-mask 생성
  실제 cloth-mask 생성
```

초기 구현에서는 #48 adapter가 `test/image`, `test/cloth`, `test_pairs.txt`까지만 만들고, 나머지 artifact가 없으면 명확한 missing artifact error를 반환하는 방식이 안전합니다. prepared smoke data로 조용히 fallback하면 upload 기반 inference가 실제로 준비되었는지 확인하기 어렵습니다.

## 5. preprocessing 단계 설계

| 단계 | Input | Output | Failure case |
| --- | --- | --- | --- |
| Step 1. Upload 저장 | `/api/tryon`의 `person_image`, `cloth_image` | `backend/outputs/{job_id}/person.*`, `backend/outputs/{job_id}/cloth.*` | 업로드 파일 누락, 빈 파일, 지원하지 않는 확장자이면 preprocessing 전에 실패합니다. |
| Step 2. Job-scoped StableVITON input root 생성 | `job_id`, 저장된 upload 파일 경로 | `DATA/{job_data_root}/test/...` 형태의 job별 입력 root | 디렉터리 생성 실패, 안전하지 않은 경로, 권한 문제 발생 시 `STABLEVITON_INPUT_ADAPTER_FAILED`로 처리합니다. |
| Step 3. `test_pairs.txt` 생성 | 정규화된 person filename, cloth filename | `test_pairs.txt` 한 줄 생성. 예: `person.png cloth.png` | 파일명 매핑 실패, 복사된 person/cloth 파일 누락 시 adapter validation에서 실패합니다. |
| Step 4. `cloth-mask` 준비 | uploaded cloth image | `test/cloth-mask/{cloth_filename}` | 의류 segmentation 실패, mask 파일 미생성, 빈 mask 생성 시 `PREPROCESS_CLOTH_MASK_FAILED`로 처리합니다. |
| Step 5. DensePose 생성 | uploaded person image | `test/image-densepose/{person_filename}` | DensePose 실행 실패, timeout, 결과 파일 미생성 시 `PREPROCESS_DENSEPOSE_FAILED`로 처리합니다. |
| Step 6. `agnostic-v3.2` 생성 | person image, pose/parse 정보, 의류 영역 추정 결과 | `test/agnostic-v3.2/{person_filename}` | parsing 정보 부족, 기존 의류 제거 실패, 결과 파일 미생성 시 `PREPROCESS_AGNOSTIC_IMAGE_FAILED`로 처리합니다. |
| Step 7. `agnostic-mask` 생성 | person image, pose/parse 정보, 의류 영역 추정 결과 | `test/agnostic-mask/{person_filename}` | mask 생성 실패, 빈 mask, 잘못된 크기의 mask 생성 시 `PREPROCESS_AGNOSTIC_MASK_FAILED`로 처리합니다. |
| Step 8. preflight check | job data root 전체 | StableVITON required input structure 검증 완료 | 필수 파일 또는 폴더가 하나라도 없으면 `PREPROCESS_REQUIRED_ARTIFACT_MISSING`으로 처리합니다. |
| Step 9. StableVITON inference 실행 | 검증된 job data root, StableVITON config/checkpoint | ignored runtime output 아래 StableVITON raw result image | StableVITON 실행 실패는 기존 `STABLEVITON_*` error code를 유지합니다. |
| Step 10. `result.png` 복사 및 `result.json` 업데이트 | StableVITON raw result image | `backend/outputs/{job_id}/result.png`, 성공 상태의 `result.json` | 생성 결과를 찾지 못하면 기존 `STABLEVITON_RESULT_NOT_FOUND`로 처리합니다. |

각 단계는 독립적으로 검증 가능해야 합니다. 특히 Step 8 preflight는 StableVITON subprocess 실행 전에 실패해야 하며, artifact 누락 상태로 inference를 실행하지 않아야 합니다.

## 6. failure case 설계

| Error code | 발생 조건 |
| --- | --- |
| `PREPROCESS_PERSON_IMAGE_MISSING` | job에 저장된 person image가 없거나, 파일이 비어 있거나, adapter가 `test/image/`로 복사하지 못한 경우 |
| `PREPROCESS_CLOTH_IMAGE_MISSING` | job에 저장된 cloth image가 없거나, 파일이 비어 있거나, adapter가 `test/cloth/`로 복사하지 못한 경우 |
| `PREPROCESS_CLOTH_MASK_FAILED` | cloth mask 생성이 실패했거나, 결과 파일이 없거나, mask가 비어 있거나 유효하지 않은 경우 |
| `PREPROCESS_DENSEPOSE_FAILED` | DensePose 실행이 실패했거나, timeout이 발생했거나, `image-densepose` artifact가 생성되지 않은 경우 |
| `PREPROCESS_AGNOSTIC_IMAGE_FAILED` | `agnostic-v3.2` 생성이 실패했거나, 결과 이미지가 없거나, person/parse/pose 입력 조합이 유효하지 않은 경우 |
| `PREPROCESS_AGNOSTIC_MASK_FAILED` | `agnostic-mask` 생성이 실패했거나, 결과 mask가 없거나, mask 크기/값이 유효하지 않은 경우 |
| `PREPROCESS_REQUIRED_ARTIFACT_MISSING` | 최종 preflight에서 StableVITON required input 파일 또는 폴더가 누락된 경우 |
| `STABLEVITON_INPUT_ADAPTER_FAILED` | job input root 생성, 파일 복사, `test_pairs.txt` 작성, filename mapping 중 adapter 단계가 실패한 경우 |

실패 응답은 기존 backend job result pattern과 맞추는 것이 좋습니다.

```json
{
  "job_id": "job_20260528_120000_ab12cd34",
  "status": "failed",
  "error": {
    "code": "PREPROCESS_REQUIRED_ARTIFACT_MISSING",
    "message": "StableVITON preprocessing artifact is missing: test/image-densepose/person.png"
  }
}
```

사용자에게 노출되는 message는 간단해야 하지만, 내부 log에는 어떤 artifact가 어느 단계에서 실패했는지 남겨야 합니다.

## 7. Git safety rule

아래 파일과 폴더는 절대 Git에 포함하지 않습니다.

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

- `docs/**` 아래 문서
- `scripts/**` 아래 source script
- `backend/app/**` 아래 backend source
- 실제 dataset row, 이미지, generated output, checkpoint, 개인 로컬 경로 자산이 들어 있지 않은 example template

preprocessing 구현 PR에서는 로컬 이미지 생성 후 반드시 아래를 확인해야 합니다.

```powershell
git status --ignored --short
git ls-files --others --exclude-standard
```

목표는 generated image / dataset / checkpoint가 staged file 목록에 절대 나타나지 않게 하는 것입니다.

## 8. 작업 분리 계획

관련 이슈:

- #48 Uploaded image 기반 StableVITON input adapter 구현
- #50 StableVITON preprocessing artifacts 생성 pipeline 설계
- #51 PC3 StableVITON batch evaluation 및 failure case 수집

실제 구현은 다음 순서로 나누는 것을 권장합니다.

1. #48 input adapter
2. cloth-mask 준비
3. DensePose 생성
4. `agnostic-v3.2` / `agnostic-mask` 생성
5. full upload-based inference smoke test
6. PC3 batch evaluation

이 순서가 필요한 이유는 각 boundary를 독립적으로 검증할 수 있기 때문입니다. 먼저 input adapter가 upload 파일을 StableVITON 구조로 정확히 배치하는지 확인하고, 이후 model-dependent preprocessing artifact를 하나씩 추가해야 실패 원인을 좁힐 수 있습니다.
