# Demo compare backend API contract

## 1. 목적

이번 문서는 발표용 웹의 `Artifact Compare`와 `Model Compare` 페이지에서 사용할 backend demo API contract를 정리한다.

이번 demo API는 실제 모델 추론이나 실제 결과 이미지 생성을 수행하지 않는다. 이미 생성된 결과 이미지와 analysis JSON을 frontend가 같은 schema로 받을 수 있도록 skeleton endpoint, loader, schema, example JSON을 준비하는 작업이다.

## 2. 페이지 구성

두 페이지는 같은 response schema를 사용한다. 차이는 `page`, `images`, `metrics` 내용이다.

| page | 비교 대상 |
| --- | --- |
| `artifact-compare` | Target Worn / 10k Basic LoRA / 10k Artifact LoRA |
| `model-compare` | Target Worn / StableVITON Original / AIHub 10k Artifact Fine-tuned |

## 3. Endpoint 목록

모든 endpoint는 기존 backend prefix를 따라 `/api` 아래에 붙는다.

```text
GET /api/demo/samples
GET /api/demo/artifact-compare/{pair_id}
GET /api/demo/model-compare/{pair_id}
```

동작:

- `/api/demo/samples`: demo index의 pair 목록과 count 반환
- `/api/demo/artifact-compare/{pair_id}`: artifact compare용 image URL, metrics, analysis 반환
- `/api/demo/model-compare/{pair_id}`: model compare용 image URL, metrics, analysis 반환
- 없는 `pair_id`: 404 반환

## 4. Response schema

비교 endpoint의 최상위 response는 다음 구조를 가진다.

```json
{
  "page": "artifact-compare",
  "pair_id": "EP00000000",
  "case": {
    "category": "upper-body",
    "pose_type": "standing_frontal",
    "difficulty": "medium",
    "gt_fit_label": "regular",
    "input_confidence": 0.92
  },
  "images": {
    "person": "/assets/image/EP00000000.jpg",
    "cloth": "/assets/cloth/EP00000000.jpg",
    "target_worn": "/assets/worn/EP00000000.jpg",
    "basic_lora": "/assets/basic_lora/EP00000000.png",
    "stableviton": null,
    "artifact_lora": "/assets/artifact_lora/EP00000000.png",
    "agnostic": "/assets/agnostic-v3.2/EP00000000.jpg",
    "agnostic_mask": "/assets/agnostic-mask/EP00000000.png",
    "densepose": "/assets/image-densepose/EP00000000.png",
    "skeleton_preview": "/assets/skeleton-preview/EP00000000.png"
  },
  "metrics": [],
  "analysis": {
    "fit": {},
    "pose": {},
    "hotspots": [],
    "keypoints": [],
    "reliability": {}
  }
}
```

Pydantic schema 파일:

```text
backend/app/schemas/demo.py
```

## 5. Example JSON 위치

이번 PR에는 실제 이미지 asset을 추가하지 않는다. API contract 검증을 위한 example JSON만 추가한다.

```text
backend/demo/samples/demo_index.example.json
backend/demo/samples/artifact_compare_metrics.example.json
backend/demo/samples/model_compare_metrics.example.json
backend/demo/analysis/EP00000000.example.json
```

현재 example pair:

```text
EP00000000
```

## 6. Asset URL 규칙

loader는 실제 파일 존재 여부를 검사하지 않고 URL만 조립한다. 실제 asset 검증은 추후 validation script에서 수행한다.

```text
person: /assets/image/{pair_id}.jpg
cloth: /assets/cloth/{pair_id}.jpg
target_worn: /assets/worn/{pair_id}.jpg
basic_lora: /assets/basic_lora/{pair_id}.png
stableviton: /assets/stableviton/{pair_id}.png
artifact_lora: /assets/artifact_lora/{pair_id}.png
agnostic: /assets/agnostic-v3.2/{pair_id}.jpg
agnostic_mask: /assets/agnostic-mask/{pair_id}.png
densepose: /assets/image-densepose/{pair_id}.png
skeleton_preview: /assets/skeleton-preview/{pair_id}.png
```

`backend/demo/assets/` 폴더가 존재하면 backend가 `/assets`로 mount한다. 폴더가 없어도 서버는 실패하지 않는다.

## 7. Demo metric 주의

이번 example metrics는 demo/example 값이다.

다음 파일의 metric 값은 발표 화면과 frontend wiring을 위한 placeholder이며, 과학적 실측값이나 논문 수준 평가 지표로 해석하면 안 된다.

```text
backend/demo/samples/artifact_compare_metrics.example.json
backend/demo/samples/model_compare_metrics.example.json
```

발표 자료나 UI에서는 `demo score`, `example metric`, `illustrative value`처럼 표시해야 한다.

## 8. Frontend 연결 방식

frontend는 먼저 sample 목록을 조회한다.

```text
GET /api/demo/samples
```

사용자가 pair를 선택하면 페이지 종류에 따라 아래 중 하나를 호출한다.

```text
GET /api/demo/artifact-compare/EP00000000
GET /api/demo/model-compare/EP00000000
```

두 endpoint는 같은 schema를 반환하므로 frontend component는 같은 renderer를 공유할 수 있다.

권장 처리:

- `page` 값으로 탭 또는 페이지 title 결정
- `images`에서 존재하는 URL만 렌더링
- `metrics`는 `direction`에 따라 개선 방향 표시
- `analysis.hotspots`는 percent 좌표 `x`, `y`로 overlay marker 표시
- 404는 demo sample missing 상태로 표시

## 9. Git safety

이번 PR에 포함한 것은 API skeleton과 example JSON뿐이다.

실제 asset은 향후 아래 경로에 둘 수 있지만 Git에는 포함하지 않는다.

```text
backend/demo/assets/**
```

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

## 10. 다음 단계

1. demo asset 파일을 로컬 `backend/demo/assets/`에 배치
2. asset existence validation script 추가
3. frontend Artifact Compare 페이지 연결
4. frontend Model Compare 페이지 연결
5. 실제 측정값이 준비되면 demo/example metric JSON을 measured metric으로 별도 교체
