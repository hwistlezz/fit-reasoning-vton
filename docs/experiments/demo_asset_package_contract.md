# Demo asset package contract

## 1. 목적

이번 문서는 발표용 demo compare API에 연결할 실제 asset package의 폴더 구조와 검증 방법을 정의한다.

#92에서 demo compare API skeleton이 추가되었고, frontend는 다음 endpoint를 사용한다.

```text
GET /api/demo/samples
GET /api/demo/artifact-compare/{pair_id}
GET /api/demo/model-compare/{pair_id}
```

#94 작업은 실제 이미지나 모델 output을 생성하지 않는다. 나중에 실제 결과 이미지와 artifact가 `backend/demo/assets/**` 아래에 들어왔을 때, pair_id 기준으로 필요한 파일이 모두 있는지 확인하는 validation script와 asset package contract를 준비한다.

## 2. Git safety

`backend/demo/assets/**`는 실제 발표 asset을 둘 위치지만 Git에 포함하지 않는다.

Git에 포함하면 안 되는 항목:

```text
backend/demo/assets/**
backend/datasets/**
backend/training/outputs/**
backend/outputs/**
backend/logs/**
*.jpg
*.jpeg
*.png
*.webp
*.ckpt
*.pth
*.pt
*.safetensors
*.zip
*.7z
```

현재 `.gitignore`에는 이미 다음 유사 규칙이 있다.

```text
backend/demo/assets/**
backend/training/outputs/**
```

따라서 이번 작업에서는 중복 ignore rule을 추가하지 않았다.

## 3. Asset root 구조

실제 asset package는 다음 구조를 사용한다.

```text
backend/demo/assets/
  image/
    {pair_id}.jpg
  cloth/
    {pair_id}.jpg
  worn/
    {pair_id}.jpg
  basic_lora/
    {pair_id}.png
  stableviton/
    {pair_id}.png
  artifact_lora/
    {pair_id}.png
  agnostic-v3.2/
    {pair_id}.jpg
  agnostic-mask/
    {pair_id}.png
  image-densepose/
    {pair_id}.png
  skeleton-preview/
    {pair_id}.png
```

analysis JSON은 #92에서 추가한 위치를 사용한다.

```text
backend/demo/analysis/{pair_id}.json
backend/demo/analysis/{pair_id}.example.json
```

validation script는 실제 `{pair_id}.json`과 example suffix가 붙은 `{pair_id}.example.json` 중 하나라도 있으면 analysis가 존재한다고 본다.

## 4. pair_id별 required asset

Artifact Compare와 Model Compare를 모두 렌더링하기 위한 최종 required asset은 다음 여섯 개다.

```text
assets/image/{pair_id}.jpg
assets/cloth/{pair_id}.jpg
assets/worn/{pair_id}.jpg
assets/basic_lora/{pair_id}.png
assets/stableviton/{pair_id}.png
assets/artifact_lora/{pair_id}.png
```

의미:

- `image`: 입력 person 이미지
- `cloth`: 입력 의류 이미지
- `worn`: target worn reference 이미지
- `basic_lora`: 10k Basic LoRA 결과 이미지
- `stableviton`: StableVITON Original 결과 이미지
- `artifact_lora`: 10k Artifact LoRA 또는 AIHub 10k Artifact Fine-tuned 결과 이미지

## 5. optional asset

optional asset은 화면 보조 설명이나 artifact preview에 사용한다.

```text
assets/agnostic-v3.2/{pair_id}.jpg
assets/agnostic-mask/{pair_id}.png
assets/image-densepose/{pair_id}.png
assets/skeleton-preview/{pair_id}.png
analysis/{pair_id}.json
analysis/{pair_id}.example.json
```

analysis는 실제 JSON 또는 example JSON 중 하나가 있으면 optional 존재로 처리한다.

## 6. validation script 사용법

script 위치:

```text
scripts/validate_demo_assets.py
```

non-strict 실행:

```powershell
python scripts/validate_demo_assets.py `
  --demo-root backend/demo `
  --index backend/demo/samples/demo_index.example.json `
  --output-json backend/training/outputs/demo_asset_validation/report.json
```

strict 실행:

```powershell
python scripts/validate_demo_assets.py `
  --demo-root backend/demo `
  --index backend/demo/samples/demo_index.example.json `
  --output-json backend/training/outputs/demo_asset_validation/report_strict.json `
  --strict
```

옵션:

- `--demo-root`: demo root. 기본값은 `backend/demo`
- `--index`: demo index JSON. 기본값은 `backend/demo/samples/demo_index.example.json`
- `--output-json`: report 저장 위치
- `--strict`: required asset missing이 있으면 exit code 1
- `--limit`: 앞에서부터 일부 pair만 검사

## 7. strict / non-strict 차이

non-strict mode:

- required asset missing이 있어도 exit code 0
- 현재 asset 준비 상태를 report로 남길 때 사용
- 실제 asset package가 아직 없는 개발 단계에 적합

strict mode:

- required asset missing이 하나라도 있으면 exit code 1
- 발표 직전 또는 frontend 연결 전 gate로 사용
- optional missing은 strict 실패 조건이 아니다

## 8. 현재 검증 결과

현재 실제 image asset은 추가하지 않았으므로 non-strict 결과는 다음과 같다.

```text
exit_code=0
total_pairs=1
checked_pairs=1
required_missing_count=6
optional_missing_count=4
```

missing required:

```text
assets/image/EP00000000.jpg
assets/cloth/EP00000000.jpg
assets/worn/EP00000000.jpg
assets/basic_lora/EP00000000.png
assets/stableviton/EP00000000.png
assets/artifact_lora/EP00000000.png
```

missing optional:

```text
assets/agnostic-v3.2/EP00000000.jpg
assets/agnostic-mask/EP00000000.png
assets/image-densepose/EP00000000.png
assets/skeleton-preview/EP00000000.png
```

existing optional:

```text
backend/demo/analysis/EP00000000.example.json
```

strict mode 결과는 expected failure다.

```text
exit_code=1
required_missing_count=6
stderr=[STRICT] required assets missing: 6
```

현재 실제 assets가 없으므로 이 실패는 정상이며, 작업 전체 검증 실패로 보지 않는다.

## 9. Frontend 연결 전 체크리스트

frontend 연결 전에 다음을 확인한다.

- `GET /api/demo/samples`의 모든 pair_id가 asset package에 존재하는지
- required asset missing count가 0인지
- Artifact Compare에 필요한 `basic_lora`와 `artifact_lora`가 있는지
- Model Compare에 필요한 `stableviton`과 `artifact_lora`가 있는지
- target worn reference가 `worn/{pair_id}.jpg`로 준비되어 있는지
- optional artifact preview를 사용할 경우 agnostic, DensePose, skeleton preview가 있는지
- analysis JSON이 실제 값인지 example 값인지 구분되어 있는지
- strict validation이 exit code 0으로 통과하는지

## 10. Metric 값 주의사항

#92에서 추가한 metrics JSON은 demo/example 값이다.

```text
backend/demo/samples/artifact_compare_metrics.example.json
backend/demo/samples/model_compare_metrics.example.json
```

실제 측정값이 준비되기 전까지는 발표 화면이나 문서에서 `demo score`, `example metric`, `illustrative value`처럼 표시해야 한다. 실측값처럼 과장하거나 과학적 평가 결과처럼 해석하면 안 된다.

실제 측정값으로 교체할 때는 다음을 함께 확인한다.

- metric 계산 기준
- baseline/method label
- higher/lower direction
- pair_id별 값의 출처
- example JSON인지 measured JSON인지 파일명 또는 문서에서 명확히 구분
