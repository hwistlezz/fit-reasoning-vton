# Online Candidate Visual Proxy Scorer

## Purpose

The offline candidate visual scorer can use worn/target references for
evaluation-only reranking and preference data. Production does not have a
ground-truth worn image, so production reranking needs an online visual proxy
scorer that uses only request-time artifacts.

This document defines the design and contract for that online scorer. It is a
documentation-only design. It does not add code, backend endpoints, frontend UI,
or breaking schema changes.

## Current Baseline

Merged components:

- `fit_analysis.v2` response schema
- fit analyzer calibration patch
- pure Python fit-aware evaluator
- offline candidate visual scorer

Offline scorer files:

- `backend/app/services/candidate_visual_scorer.py`
- `scripts/smoke_candidate_visual_scorer.py`

Current offline scorer behavior:

- If a reference image is available, it computes PSNR/SSIM against that
  reference and returns `visual_score_mode = "offline_eval"`.
- If no reference is available, it falls back to image sanity checks only.
- Its docstring explicitly states that production should not depend on
  target/worn ground truth images.

Chunk 001 sanity result:

- baseline candidates selected by offline reranking: 13
- rank8-module8 candidates selected by offline reranking: 17

This result is useful for evaluation and preference data, but not directly
portable to production because production lacks the worn/target reference.

## Production-Safe Inputs

The online scorer may use only artifacts available at request time or generated
by the production preprocessing path:

- generated try-on image
- person image
- cloth image
- agnostic-mask
- agnostic-v3.2
- image-parse
- openpose-json
- cloth-mask
- optional densepose
- optional candidate manifest metadata

It must not require:

- worn image
- target image
- paired ground truth image
- offline PSNR/SSIM against ground truth

## Proposed Output Fields

Attach online visual fields at the candidate layer:

```json
{
  "online_visual_score": 82.4,
  "online_visual_score_source": "online_visual_proxy",
  "online_visual_score_mode": "production_proxy_v1",
  "online_visual_components": {
    "image_readable": 1.0,
    "dimension_sanity": 1.0,
    "blankness_score": 1.0,
    "exposure_score": 0.96,
    "artifact_score": 0.82,
    "cloth_mask_alignment_proxy": 0.76,
    "agnostic_boundary_consistency": 0.81,
    "body_preservation_proxy": 0.88,
    "pose_visibility_sanity": 0.92,
    "garment_boundary_proxy": 0.79
  },
  "online_visual_warnings": [
    "sleeve_boundary_proxy_low"
  ],
  "candidate_specific_online_score": true,
  "production_safe": true
}
```

Field rules:

- `online_visual_score`: numeric `0..100`, or `null` if unavailable.
- `online_visual_score_source`: stable scorer source label.
- `online_visual_score_mode`: versioned mode, for example
  `production_proxy_v1`.
- `online_visual_components`: normalized component scores and debug metrics.
- `online_visual_warnings`: stable warning strings.
- `candidate_specific_online_score`: true only when generated candidate image
  was inspected.
- `production_safe`: true only if no GT/worn reference is required.

Do not put online visual proxy fields inside `fit_analysis.measurements`.
Keep them at the candidate layer so `fit_analysis.v2` remains stable.

## Proposed Components

### Image Readability

Purpose: reject missing or unreadable generated image files.

Signals:

- image path/url present
- local image readable when available
- RGB conversion succeeds
- file size is above minimal threshold

Warnings:

- `candidate_image_missing`
- `candidate_image_load_failed`
- `candidate_image_too_small`

### Dimension Sanity

Purpose: ensure candidate output has plausible dimensions.

Signals:

- width and height are positive
- dimensions match expected generated output size or person image size
- aspect ratio is in a reasonable range

Warnings:

- `invalid_dimensions`
- `unexpected_output_dimensions`
- `aspect_ratio_outlier`

### Blank, Dark, And Bright Detection

Purpose: catch hard generation failures.

Signals:

- pixel mean
- pixel standard deviation
- min/max pixel range
- percentage of near-black or near-white pixels

Warnings:

- `near_blank_image`
- `extreme_dark_image`
- `extreme_bright_image`
- `low_dynamic_range`

### Artifact Detection Proxy

Purpose: detect obvious generated-image failures without a reference.

Signals:

- local high-frequency spikes near garment/person boundary
- large single-color blocks in non-background regions
- checkerboard-like frequency artifacts
- abrupt color discontinuities around agnostic-mask boundary
- suspicious sharp rectangular borders

Warnings:

- `generation_artifact_mild`
- `generation_artifact_severe`
- `visible_border_artifact`
- `checkerboard_artifact_proxy`

### Cloth-Mask Alignment Proxy

Purpose: verify the generated garment region roughly follows the supplied cloth
mask and expected garment extent.

Production-safe inputs:

- cloth image
- cloth-mask
- generated image
- person parse or agnostic mask

Signals:

- cloth-mask coverage sanity
- expected garment aspect/area compared with changed/generated region
- color/texture presence in expected garment area
- missing garment region proxy

Warnings:

- `cloth_region_missing_proxy`
- `cloth_mask_alignment_low`
- `cloth_area_outlier`

### Agnostic-Mask Boundary Consistency

Purpose: verify the generated change is concentrated near the area StableVITON
was supposed to edit.

Production-safe inputs:

- person image
- generated image
- agnostic-mask

Signals:

- difference image between person and generated candidate
- proportion of change inside agnostic-mask
- change leakage outside agnostic-mask
- boundary smoothness around agnostic-mask edge

Warnings:

- `agnostic_change_leakage`
- `agnostic_region_under_changed`
- `boundary_discontinuity_proxy`

### Body Preservation Proxy

Purpose: avoid selecting candidates that distort face, arms, legs, or visible
body outside the garment area.

Production-safe inputs:

- person image
- generated image
- image-parse
- optional densepose

Signals:

- low change outside garment/agnostic region
- face region preservation
- exposed arm/leg region preservation
- densepose/body silhouette consistency when available

Warnings:

- `body_region_distortion_proxy`
- `face_region_changed`
- `skin_bleed_proxy`
- `densepose_mismatch_proxy`

### OpenPose Visibility Sanity

Purpose: ensure keypoint-supported areas remain plausible for fit reasoning.

Production-safe inputs:

- openpose-json
- image-parse
- generated image

Signals:

- required upper body keypoints exist for upper garments
- shoulder/hip/wrist visibility is sufficient
- generated image is not blank around keypoint neighborhoods
- person silhouette remains visible around core keypoints

Warnings:

- `pose_visibility_low`
- `shoulder_keypoints_missing`
- `wrist_keypoints_missing`
- `upper_body_visibility_low`

### Sleeve, Torso, And Garment Boundary Proxy

Purpose: add candidate-specific visual warnings related to garment fit areas.

Production-safe inputs:

- generated image
- image-parse
- openpose-json
- agnostic-mask
- cloth-mask

Signals:

- garment boundary edge continuity around shoulder line
- torso region fill consistency
- hem/garment lower boundary stability
- wrist neighborhood garment continuity for sleeves

Warnings:

- `shoulder_boundary_proxy_low`
- `torso_boundary_proxy_low`
- `garment_length_boundary_proxy_low`
- `sleeve_boundary_proxy_low`

Sleeve remains a proxy. Do not convert sleeve boundary proxy into a hard fit
label unless sleeve-end detection is separately calibrated.

## Component Weight Draft

Draft production score:

```text
online_visual_score =
  0.10 * image_readability
+ 0.10 * dimension_exposure_sanity
+ 0.15 * artifact_score
+ 0.15 * cloth_mask_alignment_proxy
+ 0.15 * agnostic_boundary_consistency
+ 0.15 * body_preservation_proxy
+ 0.10 * pose_visibility_sanity
+ 0.10 * garment_boundary_proxy
```

Each component should be normalized to `0..100` before weighting.

Hard floor rules:

- unreadable image: score `null`, `candidate_specific_online_score=false`
- blank image: cap score at `35`
- severe artifact: cap score at `55`
- body distortion severe: cap score at `60`

Generator-specific warnings should be recorded but should not apply strong
penalty by generator name alone. Penalize measured artifacts, not generator id.

## Fit-Aware Combination Rule

Keep the existing pair-level fit-aware evaluator as the primary fit reasoning
layer. Add online visual proxy as a candidate-specific production tie-breaker
and moderate score adjustment.

Recommended combined candidate score:

```text
base_fit_score = fit_aware_evaluator.fit_score
online_score = online_visual_score

if online_score is unavailable:
  combined_score = base_fit_score - 5
else:
  combined_score =
    0.75 * base_fit_score
  + 0.25 * online_score
  - warning_penalty
```

Warning penalty:

- `generation_artifact_mild`: `-3`
- `generation_artifact_severe`: `-12`
- `agnostic_change_leakage`: `-6`
- `body_region_distortion_proxy`: `-8`
- `candidate_image_missing`: ineligible

Tie-break order:

1. eligible success candidate
2. higher `combined_score`
3. higher `fit_score`
4. higher `online_visual_score`
5. higher confidence score
6. fewer warnings
7. fewer missing core ratios
8. stable `candidate_id`

When pair-level `fit_analysis.v2` is identical across generators, online visual
score can decide the selected candidate. When candidate-specific `fit_analysis`
becomes available, the online score should remain a visual-quality companion
signal rather than replacing fit measurements.

## Offline vs Online Separation

### Offline Scorer

Purpose:

- evaluation
- preference dataset creation
- future fine-tuning labels
- sanity comparison between baseline and rank8-module8

Allowed inputs:

- generated image
- worn/target reference
- metrics JSON with PSNR/SSIM
- offline artifact roots

Not production-safe:

- depends on ground-truth reference
- may reward pixel similarity rather than user-visible fit quality

### Online Proxy Scorer

Purpose:

- production reranking
- user-facing candidate selection
- visual quality guardrails

Allowed inputs:

- generated image
- person image
- cloth image
- production preprocessing artifacts
- candidate manifest metadata

Production-safe:

- no ground-truth worn/target reference
- no offline PSNR/SSIM requirement

## Preference And Fine-Tuning Dataset Plan

Use both scorers, but keep their source labels separate.

Offline preference pair:

```json
{
  "schema_version": "fit_preference_pair.v1",
  "pair_id": "EP00000000",
  "candidate_a": {
    "candidate_id": "baseline",
    "generator": "baseline_stableviton",
    "offline_visual_score": 78.2,
    "online_visual_score": 74.5,
    "fit_score": 81.0
  },
  "candidate_b": {
    "candidate_id": "rank8_module8",
    "generator": "rank8_module8",
    "offline_visual_score": 84.1,
    "online_visual_score": 80.3,
    "fit_score": 81.0
  },
  "preferred_candidate_id": "rank8_module8",
  "preference_source": "offline_visual_scorer_v1",
  "production_proxy_agreement": true,
  "human_review_status": "unreviewed"
}
```

Recommended fields:

- `offline_visual_score`
- `online_visual_score`
- `fit_score`
- `combined_score`
- `preference_source`
- `production_proxy_agreement`
- `human_review_status`
- `artifact_warnings`
- `reviewer_notes`

Future usage:

- compare offline preference with online proxy selection
- build human review queues for disagreement cases
- create preference pairs for rank8-module8 or later LoRA tuning
- calibrate online proxy weights against human labels

## Implementation Gate

Proceed to online proxy implementation only after:

1. portable PC3 manifest paths are accessible from the scoring environment
2. production-safe artifact paths are present in the manifest or derivable by
   pair id
3. the scorer contract above is accepted
4. output remains candidate-level and non-breaking
5. smoke plan limits sample size and does not copy large images

Hold backend/frontend integration until:

- online score is implemented and smoked on 30-pair chunk_001 candidates
- combined score behavior is reviewed
- warning taxonomy is stable enough for UI display
