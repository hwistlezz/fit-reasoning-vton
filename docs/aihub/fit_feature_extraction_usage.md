# AIHub Fit Feature Extraction 사용법

## 1. 목적

AIHub wearing annotation JSON에서 fit analyzer에 사용할 feature skeleton을 생성하는 방법을 설명한다.

이 script는 AIHub keypoint와 segmentation annotation을 읽어 `features.csv`와 backend fit result loader가 읽을 수 있는 `fit.json`을 생성한다.

## 2. 현재 범위

이번 script는 skeleton 단계다.

- 실제 fit score 확정 기준이 아니다.
- bbox 기반 proxy feature를 사용한다.
- `sleeve_length_ratio`는 팔 길이를 이미지 높이로 나눈 placeholder 값이다.
- `body_visibility_score`는 현재 `pose_quality_score`와 같은 placeholder 값이다.
- 실제 threshold는 PC2/PC3 실험 후 조정한다.

## 3. 실행 예시

```powershell
python scripts\build_fit_features.py `
  --input docs\examples\aihub_wearing_annotation.example.json `
  --out-features backend\datasets\processed\features\features.example.csv `
  --out-fit-result backend\datasets\processed\fit_results\example_case_001\fit.json `
  --case-id example_case_001
```

`--case-id`를 생략하면 `info[0].id`를 사용한다.

## 4. 생성 결과

생성 결과는 다음 두 파일이다.

```text
features.csv
fit_result.json
```

`features.csv`에는 `shoulder_ratio`, `torso_width_ratio`, `sleeve_length_ratio`, `garment_length_ratio`, `cloth_area_ratio`, `pose_quality_score`, `segmentation_quality_score`, `confidence_score`, `fit_label`이 포함된다.

`fit_result.json`은 #63에서 구현한 backend fit result loader가 읽을 수 있는 `confidence`, `fit`, `annotations` 구조를 따른다.

## 5. Backend 연결

#63에서 구현한 fit result loader는 아래 순서로 `fit.json`을 찾는다.

```text
backend/outputs/{job_id}/fit.json
FIT_ANALYSIS_ROOT/{job_id}/fit.json
```

따라서 실제 backend 테스트 시에는 생성된 `fit.json`을 job_id에 맞는 폴더에 복사하거나, `FIT_ANALYSIS_ROOT`를 맞춰서 사용할 수 있다.

예시:

```powershell
python -c "from pathlib import Path; from backend.app.services.fit_analyzer import analyze_fit; r=analyze_fit('example_case_001', '/outputs/example_case_001/result.png', Path('backend/datasets/processed/fit_results/example_case_001/fit.json')); print(r.confidence.score); print(r.fit.label); print(r.annotations)"
```

## 6. Git Safety

생성 결과는 아래 ignored 경로에 저장한다.

```text
backend/datasets/processed/features/
backend/datasets/processed/fit_results/
```

해당 generated output은 Git에 올리지 않는다.

이번 script와 문서는 실제 AIHub 원본 데이터, 이미지, checkpoint, generated image를 포함하지 않는다.
