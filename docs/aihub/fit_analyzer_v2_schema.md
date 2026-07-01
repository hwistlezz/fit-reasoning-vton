# Fit Analyzer v2 Schema

## 목적

`fit_analysis.v2`는 StableVITON try-on image 결과에 AIHub keypoint/segmentation 기반 fit 분석을 붙이기 위한 통합 schema다.

목표 응답은 다음 값을 안정적으로 포함한다.

- `fit_label`
- `confidence`
- `shoulder_ratio`
- `torso_width_ratio`
- `sleeve_length_ratio`
- `garment_length_ratio`
- `pose_quality`
- `parsing_quality`
- `body_visibility`
- frontend hotspot annotation

## 입력 artifact

현재 PC2 batch feature extractor 기준 입력은 processed AIHub layout이다.

```text
processed_root/{split}/image/{pair_id}.jpg
processed_root/{split}/cloth/{pair_id}.jpg
processed_root/{split}/openpose-json/{pair_id}_keypoints.json
processed_root/{split}/image-parse/{pair_id}.png
```

StableVITON try-on image는 fit ratio 계산의 필수 입력으로 아직 쓰지 않는다. v2 MVP에서는 StableVITON 결과 이미지 URL과 fit analysis JSON을 같은 backend result에 묶어 표시한다.

## PC2 compact `fit.json`

`scripts/batch_fit_features.py --save-fit-json --save-annotations`가 생성하는 compact format은 backend loader와 호환된다.

```json
{
  "schema_version": "fit_analysis.v2",
  "pair_id": "EP00000000",
  "split": "train",
  "fit_label": "slightly_oversized",
  "confidence": 76.36,
  "quality_score": 0.76362,
  "features": {
    "shoulder_ratio": 2.018622,
    "torso_width_ratio": 1.0,
    "sleeve_length_ratio": 1.0,
    "garment_length_ratio": 2.724377,
    "silhouette_score": 0.354479,
    "pose_quality": 1.0,
    "parsing_quality": 1.0,
    "body_visibility": 0.443099,
    "quality_score": 0.76362
  },
  "hotspots": [
    {
      "key": "shoulder",
      "label": "Shoulder",
      "text": "Shoulder hotspot generated from shoulder_ratio.",
      "x": 50.0,
      "y": 27.0,
      "value": 2.018622
    }
  ],
  "annotations": []
}
```

`annotations`는 기존 backend/front 호환용 alias다. v2 frontend에서는 `hotspots`를 우선 사용한다.

## Backend response

`GET /api/result/{job_id}`는 기존 top-level field를 유지하면서 `fit_analysis`를 추가한다.

```json
{
  "job_id": "job_20260626_120000_ab12cd34",
  "status": "done",
  "person_image_url": "/outputs/job_20260626_120000_ab12cd34/person.png",
  "cloth_image_url": "/outputs/job_20260626_120000_ab12cd34/cloth.png",
  "result_image_url": "/outputs/job_20260626_120000_ab12cd34/result.png",
  "confidence": {
    "score": 76.36,
    "level": "medium",
    "warnings": []
  },
  "fit": {
    "label": "slightly_oversized",
    "scores": {
      "shoulder_ratio": 2.018622,
      "torso_width_ratio": 1.0,
      "sleeve_length_ratio": 1.0,
      "garment_length_ratio": 2.724377
    },
    "explanations": []
  },
  "quality": {
    "pose_quality": 1.0,
    "parsing_quality": 1.0,
    "body_visibility": 0.443099,
    "quality_score": 0.76362,
    "silhouette_score": 0.354479
  },
  "hotspots": [],
  "annotations": [],
  "fit_analysis": {
    "schema_version": "fit_analysis.v2",
    "source": {
      "type": "pc2_compact",
      "pair_id": "EP00000000",
      "split": "train"
    },
    "fit_label": "slightly_oversized",
    "measurements": {
      "shoulder_ratio": 2.018622,
      "torso_width_ratio": 1.0,
      "sleeve_length_ratio": 1.0,
      "garment_length_ratio": 2.724377
    },
    "confidence": {
      "score": 76.36,
      "level": "medium",
      "warnings": []
    },
    "fit": {
      "label": "slightly_oversized",
      "scores": {
        "shoulder_ratio": 2.018622,
        "torso_width_ratio": 1.0,
        "sleeve_length_ratio": 1.0,
        "garment_length_ratio": 2.724377
      },
      "explanations": []
    },
    "quality": {
      "pose_quality": 1.0,
      "parsing_quality": 1.0,
      "body_visibility": 0.443099,
      "quality_score": 0.76362,
      "silhouette_score": 0.354479
    },
    "hotspots": [],
    "annotations": []
  },
  "message": "StableVITON result image was generated. Fit analysis was attached when available."
}
```

## Frontend hotspot schema

Frontend overlay 좌표는 percent 단위다.

```ts
type FitHotspot = {
  key: "shoulder" | "torso" | "sleeve" | "length" | "cloth_region" | "pose" | string;
  label: string;
  text: string;
  x: number;
  y: number;
  value?: number | string | null;
};
```

표시 규칙:

- `fit_analysis.hotspots`를 우선 사용한다.
- 없으면 top-level `hotspots`, 그 다음 `annotations`를 fallback으로 사용한다.
- `x`, `y`는 result image 기준 0-100 percent다.
- `value`는 ratio 또는 score이며, UI에서는 소수 2자리 정도로 표시한다.

## 현재 계산 가능한 feature와 한계

| feature | 현재 계산 | 한계 |
| --- | --- | --- |
| `shoulder_ratio` | OpenPose shoulder keypoint와 upper/body parse band width 기반 | 10k coverage가 낮고 후면/측면 pose에서 누락 가능 |
| `torso_width_ratio` | shoulder-hip 사이 torso band의 garment/body width 비율 | parse class 품질에 의존 |
| `sleeve_length_ratio` | shoulder-wrist가 있으면 1.0 proxy | 실제 sleeve end detection 아님 |
| `garment_length_ratio` | upper mask bottom과 shoulder-hip 거리 비율 | outer/long top에서 threshold 재보정 필요 |
| `pose_quality` | valid keypoint count 기반 | pose 난이도 자체를 충분히 반영하지 않음 |
| `parsing_quality` | upper/body mask area heuristic | SCHP/AIHub parse 품질 검증 전까지 pseudo score |
| `body_visibility` | body mask area heuristic | occlusion semantic을 직접 보지 않음 |
| `confidence` | pose/parsing/body visibility + placeholder alignment/consistency | StableVITON generation consistency는 아직 0.5 placeholder |
| `fit_label` | ratio threshold rule | 분포 기반 threshold calibration 필요 |

## Smoke test

기존 10k feature CSV 기준:

```powershell
python scripts\smoke_fit_analysis_v2_from_csv.py `
  --features-csv backend\datasets\features_fit_10k_v3.csv `
  --limit 25
```

기존 30k feature CSV 기준:

```powershell
python scripts\smoke_fit_analysis_v2_from_csv.py `
  --features-csv backend\datasets\features_fit_30k_v3.csv `
  --limit 25
```

이 smoke는 CSV를 읽고 임시 compact `fit.json`을 만들어 backend fit analyzer loader를 통과시키는 테스트다. repo 안에 generated output을 남기지 않는다.
