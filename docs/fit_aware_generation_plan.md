# Fit-Aware Generation Plan

## Goal

Build a post-generation evaluator that can choose the best try-on image from
multiple generated candidates using `fit_analysis.v2`. The evaluator should
return the selected candidate, ranked alternatives, Korean user-facing
explanation text, measurements, hotspots, and warnings.

This document is a design plan only. It does not change backend or frontend
code.

## Current Repo Context

Inspected implementation files:

- `backend/app/schemas/result.py`
- `backend/app/services/fit_analyzer.py`
- `backend/app/core/job_store.py`
- `backend/app/api/tryon.py`
- `backend/app/schemas/demo.py`
- `backend/app/services/demo_loader.py`
- `frontend/src/lib/types.ts`
- `frontend/src/components/demo/HotspotOverlay.tsx`
- `frontend/src/components/demo/HotspotPanel.tsx`
- `frontend/src/components/demo/FitDetailsPanel.tsx`
- `docs/aihub/fit_analyzer_v2_schema.md`
- `docs/experiments/demo_backend_api_contract.md`

## Current Fit Analysis Summary

`fit_analysis.v2` is already represented by `FitAnalysisResponse`:

- `schema_version`
- `source`
- `fit_label`
- `measurements`
- `confidence`
- `fit`
- `quality`
- `hotspots`
- `annotations`

The backend result response keeps backward-compatible top-level fields:

- `confidence`
- `fit`
- `quality`
- `hotspots`
- `annotations`
- `fit_analysis`

The fit analyzer currently supports:

- backend-compatible `fit_analysis.v2` JSON
- PC2 compact `fit.json`
- confidence warnings
- missing core ratio calibration
- `cloth_type_unknown` handling
- missing-ratio hotspot suppression
- sleeve proxy warning

## Current Generation And Demo Result Summary

Runtime try-on result flow:

1. `POST /api/tryon` creates a job.
2. `backend/app/core/job_store.py` writes upload metadata and pending
   `result.json`.
3. Worker execution eventually calls `write_success_result`.
4. `write_success_result` stores `result_image_url` and attaches fit analysis
   from `analyze_fit`.
5. `GET /api/result/{job_id}` returns `TryOnResultResponse`.

Current runtime output shape is single-result oriented:

```json
{
  "job_id": "job_20260703_120000_ab12cd34",
  "status": "done",
  "person_image_url": "/outputs/job_id/person.png",
  "cloth_image_url": "/outputs/job_id/cloth.png",
  "result_image_url": "/outputs/job_id/result.png",
  "confidence": {},
  "fit": {},
  "quality": {},
  "hotspots": [],
  "annotations": [],
  "fit_analysis": {},
  "message": "StableVITON result image was generated. Fit analysis was attached when available."
}
```

Demo compare flow is separate:

- `DemoCompareResponse` has `images`, `metrics`, and `analysis`.
- `analysis.hotspots` drives overlay/panel display.
- `Hotspot.value` already accepts number, string, or null on the frontend.

## Proposed Flow

```text
person image + cloth image
-> generate N try-on candidates
-> run or attach fit_analysis.v2 for each candidate
-> build fit-aware candidate manifest
-> compute fit_score for each candidate
-> select best candidate
-> return selected image + fit_analysis + ranked candidates + explanation
```

The evaluator should be isolated from generation. It should not run
StableVITON, LoRA, preprocessing, or full feature extraction. It should only
consume generated candidate metadata and `fit_analysis.v2`.

## Candidate Manifest

The manifest schema is defined in:

```text
docs/fit_aware_candidate_schema.md
```

Required candidate fields:

- `pair_id`
- `candidate_id`
- `generator`
- `seed`
- `image_path` or `image_url`
- `source_artifact`
- `fit_analysis`
- `fit_score`
- `warnings`

## Scoring And Reranking

Scoring rules are defined in:

```text
docs/fit_aware_scoring_rules.md
```

High-level rule:

```text
fit_score = calibrated confidence
          + fit_label adjustment
          + core ratio coverage adjustment
          + ratio severity adjustment
          + warning adjustment
```

Selection should prefer:

1. higher `fit_score`
2. higher `confidence.score`
3. fewer warnings
4. fewer missing core ratios
5. stable `candidate_id` tie-break

If all candidates are low confidence, the evaluator may still select the best
available candidate, but the response must say that the fit judgment is low
confidence.

## Explanation Template

The evaluator should generate one Korean paragraph:

```text
{fit_label_sentence} 신뢰도는 {confidence_level_ko}입니다. {measurement_sentence} {sleeve_sentence} 이 후보는 {selection_reason_ko}
```

Rules:

- Translate `fit_label` to Korean.
- Explain confidence level.
- Mention only available shoulder, torso, sleeve, and length ratios.
- Hide missing ratios in normal/high confidence cases.
- In low confidence cases, mention that some core ratios are on hold.
- Always describe `sleeve_length_ratio` as a proxy when it is used.
- Explain why the selected candidate won.

## Backend API Contract Draft

Initial standalone evaluator endpoint:

```text
POST /api/fit-aware/rerank
```

Request:

```json
{
  "schema_version": "fit_aware_candidates.v1",
  "pair_id": "EP00000000",
  "request_id": "job_20260703_120000_ab12cd34",
  "candidates": []
}
```

Response:

```json
{
  "schema_version": "fit_aware_selection.v1",
  "pair_id": "EP00000000",
  "selected_candidate": {},
  "ranked_candidates": [],
  "selected_reason": "Selected because it has the highest calibrated fit_score.",
  "user_facing_explanation": "전체 핏은 보통 핏으로 판단됩니다...",
  "measurements": {},
  "hotspots": [],
  "warnings": []
}
```

Later integrated result response:

```json
{
  "job_id": "job_20260703_120000_ab12cd34",
  "status": "done",
  "result_image_url": "/outputs/job_id/result.png",
  "fit_analysis": {},
  "fit_selection": {
    "schema_version": "fit_aware_selection.v1"
  }
}
```

Do not remove existing top-level `confidence`, `fit`, `quality`, `hotspots`, or
`annotations`. `fit_selection` should be additive.

## Frontend Display Contract Draft

Frontend should render:

- selected candidate image from `selected_candidate.image_url`
- `user_facing_explanation`
- confidence score and level from selected candidate `fit_analysis.confidence`
- fit label from selected candidate `fit_analysis.fit_label`
- available measurements from `measurements`
- hotspot overlay from `hotspots`
- warning badge when `warnings` is non-empty
- optional ranked candidate list for debugging or advanced comparison

Fallback order for display:

1. `fit_selection.selected_candidate.fit_analysis`
2. `fit_selection.measurements` and `fit_selection.hotspots`
3. current `fit_analysis`
4. top-level `confidence`, `fit`, `hotspots`, `annotations`

## Implementation Plan

1. Add a pure Python evaluator module, for example
   `backend/app/services/fit_aware_evaluator.py`.
2. Add Pydantic schemas, for example `backend/app/schemas/fit_aware.py`.
3. Add unit tests using small inline candidate payloads.
4. Add CLI smoke script for manifest JSON reranking.
5. Add optional backend endpoint `POST /api/fit-aware/rerank`.
6. Add `fit_selection` to result response only after backend API tests pass.
7. Wire frontend to render `fit_selection` after backend integration is stable.

## Non-Goals For The First Evaluator

- Do not run StableVITON inference.
- Do not run LoRA.
- Do not regenerate 39k features.
- Do not copy large images.
- Do not create overlay images.
- Do not commit generated image, CSV, JSONL, archive, or checksum artifacts.

## Readiness

The repo is ready for evaluator implementation after this design because:

- `fit_analysis.v2` is present in backend schema.
- Current fit analyzer loader can normalize compact and backend-compatible
  payloads.
- Frontend hotspot value can already display numeric ratio values.
- Existing result response can accept additive fields without breaking current
  top-level compatibility.

Backend/frontend integration should wait until the pure evaluator module has
unit tests and a small manifest smoke test.

## Initial Evaluator Implementation Target

The first implementation should stay backend-internal and avoid API/frontend
changes:

- module: `backend/app/services/fit_aware_evaluator.py`
- synthetic smoke: `scripts/smoke_fit_aware_evaluator.py`
- input: Python dict manifest following `fit_aware_candidates.v1`
- output: Python dict selection payload following `fit_aware_selection.v1`
- selection eligibility: `inference_status == "success"` and image path or URL
  exists

## Online Visual Proxy Layer

The first candidate visual scorer uses offline worn/target references for
evaluation smoke tests. Production cannot depend on those references. The
production path should add a separate online visual proxy layer that uses only:

- generated try-on image
- person image
- cloth image
- agnostic-mask
- agnostic-v3.2
- image-parse
- openpose-json
- cloth-mask
- optional densepose
- candidate manifest metadata

The online score should be attached at the candidate layer, not inside
`fit_analysis.v2`, with fields such as:

- `online_visual_score`
- `online_visual_score_source`
- `online_visual_score_mode`
- `online_visual_components`
- `online_visual_warnings`
- `candidate_specific_online_score`
- `production_safe`

Detailed contract:

```text
docs/online_candidate_visual_proxy_scorer.md
```

Integration principle:

```text
combined_score = 0.75 * fit_score + 0.25 * online_visual_score - warning_penalty
```

The online score should act as a production-safe candidate-specific visual
guardrail and tie-breaker. It should not replace calibrated fit measurements.
