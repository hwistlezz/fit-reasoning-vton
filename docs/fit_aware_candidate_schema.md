# Fit-Aware Candidate Schema

## Purpose

This document defines the draft manifest schema for post-generation fit-aware
selection. It is intended for an evaluator that receives multiple try-on
generation candidates for the same person/garment pair, reads each candidate's
`fit_analysis.v2` payload, computes a `fit_score`, and returns the selected
candidate plus a ranked list.

The schema is a design contract only. It does not change the current backend or
frontend implementation.

## Current Compatible Inputs

The current backend result model is `TryOnResultResponse` in
`backend/app/schemas/result.py`. It already supports:

- `result_image_url`
- top-level `confidence`
- top-level `fit`
- top-level `quality`
- top-level `hotspots`
- top-level `annotations`
- canonical `fit_analysis`

The canonical nested payload is `fit_analysis.v2`:

```json
{
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
    "warnings": [
      "sleeve_length_ratio is a wrist-alignment proxy, not a calibrated sleeve-end measurement."
    ]
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
}
```

## Candidate Manifest

Use this input when reranking several generated try-on images for one pair.

```json
{
  "schema_version": "fit_aware_candidates.v1",
  "pair_id": "EP00000000",
  "request_id": "job_20260703_120000_ab12cd34",
  "created_at": "2026-07-03T12:00:00+09:00",
  "candidates": [
    {
      "pair_id": "EP00000000",
      "candidate_id": "stableviton_seed_000001",
      "generator": "stableviton",
      "seed": 1,
      "inference_status": "success",
      "image_path": null,
      "image_url": "/outputs/job_20260703_120000_ab12cd34/candidates/stableviton_seed_000001.png",
      "source_artifact": {
        "type": "stableviton_result",
        "path": null,
        "url": "/outputs/job_20260703_120000_ab12cd34/candidates/stableviton_seed_000001.png",
        "metadata": {
          "chunk_id": "chunk_001",
          "pipeline": "pc3_chunk_inference"
        }
      },
      "fit_analysis": {
        "schema_version": "fit_analysis.v2"
      },
      "fit_score": null,
      "warnings": []
    }
  ]
}
```

## Candidate Fields

| field | type | required | notes |
| --- | --- | --- | --- |
| `pair_id` | string | yes | Must match manifest `pair_id`. |
| `candidate_id` | string | yes | Stable deterministic id within one pair. |
| `generator` | string | yes | Example: `stableviton`, `stableviton_lora`, `catvton`. |
| `seed` | integer or null | no | Null for deterministic or unknown seed. |
| `inference_status` | string | no | `success` candidates are eligible for selection. Missing status is treated as `success` for older manifests. |
| `image_path` | string or null | no | Local evaluator path. Do not expose directly to frontend. |
| `image_url` | string or null | no | Public URL for backend/frontend display. |
| `source_artifact` | object | yes | Provenance for the generated image. |
| `fit_analysis` | object or null | yes | Canonical `fit_analysis.v2` payload. |
| `fit_score` | number or null | no | Filled by evaluator, range `0..100`. |
| `warnings` | string[] | yes | Candidate-level warnings, including future generation artifact warnings. |

At least one of `image_path` or `image_url` must be present. Backend API output
should prefer `image_url`; offline evaluator output may keep both.

Candidates with `inference_status` other than `success` remain in debug output
but are not eligible for `selected_candidate`.

## Source Artifact

```json
{
  "type": "stableviton_result",
  "path": "D:/local/non_repo_path/result.png",
  "url": "/outputs/job_id/result.png",
  "metadata": {
    "stableviton_commit": null,
    "chunk_id": null,
    "inference_profile": null
  }
}
```

`source_artifact.metadata` is intentionally open-ended. Future generation
artifact warnings should be stored as candidate `warnings`, not inside
`fit_analysis.v2`, unless the fit analyzer itself produces them.

## Selection Output

```json
{
  "schema_version": "fit_aware_selection.v1",
  "pair_id": "EP00000000",
  "selected_candidate": {
    "candidate_id": "stableviton_seed_000001",
    "generator": "stableviton",
    "seed": 1,
    "image_url": "/outputs/job_20260703_120000_ab12cd34/candidates/stableviton_seed_000001.png",
    "fit_score": 82.4,
    "fit_analysis": {
      "schema_version": "fit_analysis.v2"
    },
    "warnings": []
  },
  "ranked_candidates": [
    {
      "rank": 1,
      "candidate_id": "stableviton_seed_000001",
      "generator": "stableviton",
      "seed": 1,
      "image_url": "/outputs/job_20260703_120000_ab12cd34/candidates/stableviton_seed_000001.png",
      "fit_score": 82.4,
      "fit_label": "regular",
      "confidence": {
        "score": 84.0,
        "level": "high",
        "warnings": []
      },
      "warnings": []
    }
  ],
  "selected_reason": "Selected because it has the highest calibrated fit_score with complete core measurements.",
  "user_facing_explanation": "전체 핏은 보통 핏으로 판단됩니다. 신뢰도는 높음이며, 어깨와 몸통 비율이 안정적으로 확인되어 이 후보를 선택했습니다.",
  "measurements": {
    "shoulder_ratio": 1.05,
    "torso_width_ratio": 1.08,
    "sleeve_length_ratio": 1.0,
    "garment_length_ratio": 1.12
  },
  "hotspots": [],
  "warnings": []
}
```

## Output Field Rules

- `selected_candidate` is the full candidate object after scoring, trimmed only
  if the backend needs a smaller response.
- `ranked_candidates` should include enough metadata for debugging and optional
  frontend comparison UI.
- `measurements` and `hotspots` should mirror the selected candidate's
  `fit_analysis.measurements` and `fit_analysis.hotspots`.
- `warnings` is the union of selection warnings, selected candidate warnings,
  and selected candidate `fit_analysis.confidence.warnings`.
- `user_facing_explanation` is Korean user-facing copy. It should avoid exposing
  missing raw fields unless the confidence is low.

## Versioning

- Candidate manifest: `fit_aware_candidates.v1`
- Selection output: `fit_aware_selection.v1`
- Embedded fit analysis: `fit_analysis.v2`

Do not change `fit_analysis.v2` for reranking-only metadata. Add reranking
metadata at the candidate or selection layer.
