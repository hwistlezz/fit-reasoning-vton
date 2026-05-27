# 데이터 구조

## 목적

이 문서는 로컬 실험 환경에서 사용할 데이터와 산출물의 권장 구조를 정리한다. 실제 대용량 파일은 GitHub에 커밋하지 않는다.

## 권장 로컬 구조

```text
data/
  samples/
    person/
    garment/
  raw/
    VITON-HD/
    DressCode/
  manifests/
    sample_pairs.csv

outputs/
  stableviton/
    run_YYYYMMDD_HHMM/
      generated/
      logs/
  experiments/
    stableviton_batch/
    failure_cases/
    low_confidence_cases/
    fit_threshold_tests/
    confidence_tests/
    idm_test/
  catvton/
    run_YYYYMMDD_HHMM/
      generated/
      logs/
  analysis/
    run_YYYYMMDD_HHMM/
      reports/
      overlays/
```

`data/`와 `outputs/` 내부의 실제 파일은 `.gitignore`로 제외한다. 디렉터리 존재를 위해 `.gitkeep`만 커밋한다.

## Manifest 필드 초안

향후 manifest는 다음 필드를 포함할 수 있다.

| 필드 | 설명 |
| --- | --- |
| `sample_id` | 샘플 고유 ID |
| `person_image_path` | person image 경로 |
| `garment_image_path` | garment image 경로 |
| `stableviton_output_path` | StableVITON 생성 결과 경로 |
| `optional_comparison_output_path` | IDM-VTON 또는 CatVTON 생성 결과 경로 |
| `real_target_image_path` | real paired target이 있는 경우의 경로 |
| `dataset_name` | 직접 촬영, VITON-HD, DressCode 등 |
| `split` | demo, validation, test 등 |
| `notes` | 검수 또는 예외 사항 |

## Real Target과 Pseudo Target 구분

`real_target_image_path`는 실제 착용 이미지이고, VTON output 경로는 모델이 생성한 pseudo target이다. 두 경로를 하나의 `target` 필드로 합치지 않는다.

## 향후 작성 항목

- 최종 manifest schema
- 파일명 규칙
- sample id 생성 규칙
- 직접 촬영 데이터 관리 방식
- 공개 가능 샘플 구분 방식
