# Fit Analysis Attachment Step

## Purpose

Fit-aware reranking needs each generated try-on candidate to carry a
`fit_analysis.v2` payload. PC3 candidate manifests may initially contain only
candidate image metadata, so this document defines how to attach fit analysis
before running the evaluator.

This is a design document only. It does not change backend endpoints, frontend
code, schemas, or extraction code.

## Current Implementation Summary

Inspected files:

- `backend/app/services/fit_analyzer.py`
- `scripts/batch_fit_features.py`
- `backend/app/services/fit_aware_evaluator.py`
- `docs/fit_aware_candidate_schema.md`
- `docs/fit_aware_reranking_smoke_runbook.md`

### `fit_analyzer.py`

The backend fit analyzer is a loader and normalizer. It checks for existing
`fit.json` candidates:

```text
settings.output_dir / job_id / "fit.json"
settings.fit_analysis_root / job_id / "fit.json"
```

It supports:

- backend-compatible `fit_analysis.v2`
- PC2 compact `fit.json`
- placeholder result when no `fit.json` is available
- confidence warning calibration for compact payloads
- missing-ratio hotspot suppression
- sleeve proxy warning

It does not parse or inspect `result_image_url`. Passing a different generated
candidate image URL does not change measurements, confidence, fit label, or
hotspots unless a different `fit.json` is also supplied.

### `batch_fit_features.py`

The batch extractor computes feature rows from processed AIHub artifacts:

```text
processed_root/{split}/image/{pair_id}.jpg
processed_root/{split}/cloth/{pair_id}.jpg
processed_root/{split}/openpose-json/{pair_id}_keypoints.json
processed_root/{split}/image-parse/{pair_id}.png
```

It computes:

- `shoulder_ratio`
- `torso_width_ratio`
- `sleeve_length_ratio`
- `garment_length_ratio`
- `pose_quality`
- `parsing_quality`
- `body_visibility`
- `quality_score`
- `confidence`
- `fit_label`
- optional compact `fit_analysis.v2` JSON

Important limitation:

```text
cloth_alignment = 0.5
generation_consistency = 0.5
```

These are placeholders. The script does not read candidate generated try-on
images and therefore cannot distinguish `baseline_stableviton` from
`rank8_module8` for the same `pair_id`.

## Can Current Analyzer Score Generated Candidates Differently?

Partial, but not in a candidate-specific visual sense.

Current capabilities:

- It can attach an existing `fit_analysis.v2` payload to a candidate.
- It can normalize compact pair-level fit JSON into backend response format.
- It can rerank candidates if each candidate already has different
  `fit_analysis.v2`.

Current gap:

- It cannot compute different fit measurements from different generated
  candidate images.
- It does not inspect `candidate.image_path`.
- It does not run parsing, pose, garment boundary, or artifact checks on the
  generated try-on image.
- If two candidates for the same `pair_id` receive the same pair-level
  `fit_analysis.v2`, their fit-aware scores will be the same except for
  candidate-level warnings or auxiliary fields handled outside current
  `fit_analysis.v2`.

## Required Inputs For Attachment

### Common Inputs

Required for both attachment options:

- PC3 candidate manifest row
- `pair_id`
- `candidate_id`
- `generator`
- `generator_version`
- `seed`
- `image_path` or `image_url`
- `inference_status`
- original person path or pair-level processed person artifact
- original cloth path or pair-level processed cloth artifact
- split/category metadata if available

### Pair-Level Fit Inputs

Required for lightweight attachment:

- existing full feature CSV or compact fit JSON keyed by `pair_id`
- or processed artifacts:
  - `image`
  - `cloth`
  - `openpose-json`
  - `image-parse`

### Candidate-Specific Visual Inputs

Required for candidate-specific visual attachment:

- generated try-on image for each candidate
- candidate image dimensions
- pose/keypoints for generated image, or a decision to reuse original person
  keypoints with a warning
- parsing/segmentation for generated image
- original person keypoints and parse for comparison
- original cloth image and optional cloth mask
- optional generation metrics:
  - PSNR
  - SSIM
  - LPIPS or perceptual distance, future
  - artifact warnings, future

## Option A: Lightweight Attachment

Use existing pair-level fit analysis and attach it to every candidate with the
same `pair_id`.

### Flow

1. Read PC3 candidate manifest.
2. Filter `inference_status == "success"`.
3. For each candidate, look up pair-level `fit_analysis.v2` by `pair_id`.
4. Attach it to the candidate:

```json
{
  "candidate_id": "EP00000000_baseline_stableviton_seed_1234",
  "generator": "baseline_stableviton",
  "fit_analysis": {
    "schema_version": "fit_analysis.v2",
    "source": {
      "type": "pair_level_attachment",
      "pair_id": "EP00000000",
      "candidate_id": "EP00000000_baseline_stableviton_seed_1234",
      "generator": "baseline_stableviton",
      "candidate_specific": false
    }
  },
  "warnings": [
    "fit_analysis_pair_level_not_candidate_specific"
  ]
}
```

### Pros

- No new model inference.
- No generated image parsing.
- Very small disk impact.
- Good for validating manifest ingestion, evaluator shape, selected explanation
  rendering, and backend/frontend contract.

### Cons

- Does not compare actual visual quality between generators.
- Baseline and rank8-module8 candidates for the same `pair_id` will usually
  receive identical fit scores.
- Selection may fall back to tie-breakers unless auxiliary candidate warnings or
  metrics are added.

### Recommended Use

Use Option A for the first real reranking smoke only if the goal is pipeline
contract validation, not model quality selection.

Label the report clearly:

```text
fit_analysis_source = pair_level_attachment
candidate_specific_visual_analysis = false
```

## Option B: Candidate-Specific Visual Attachment

Compute fit analysis from each generated try-on candidate image.

### Flow

1. Read PC3 candidate manifest.
2. Filter `inference_status == "success"`.
3. For each generated image:
   - verify `image_path` exists
   - run or load generated-image parsing
   - run or load generated-image pose/keypoints, or reuse original keypoints
     with warning
   - compute candidate-specific garment/body ratios
   - compute candidate-specific parsing/body visibility quality
   - compute generation consistency or artifact warnings
   - write candidate-specific `fit_analysis.v2`
4. Attach the payload to that candidate.
5. Run fit-aware evaluator.

### Candidate-Specific Measurements

Candidate-specific ratios should be computed from generated-image parse and
pose whenever possible:

- `shoulder_ratio`: generated garment shoulder width / generated or original
  body shoulder width
- `torso_width_ratio`: generated garment torso width / body torso width
- `garment_length_ratio`: generated garment hem position / shoulder-hip length
- `sleeve_length_ratio`: still proxy until sleeve-end detection is calibrated

### Candidate-Specific Quality

Candidate-specific `quality` should include:

- `pose_quality`: generated pose/keypoint confidence or reused-original warning
- `parsing_quality`: generated parse coverage/stability
- `body_visibility`: generated body visibility
- `quality_score`: calibrated composite score
- `silhouette_score`: generated silhouette heuristic

Future candidate-level quality can include:

- cloth texture preservation
- body shape distortion
- skin bleed
- garment boundary artifacts
- background bleed

### Pros

- Actually differentiates baseline vs rank8-module8 outputs.
- Produces meaningful candidate-specific fit scores.
- Can feed future preference/fine-tuning data.

### Cons

- Requires generated-image parse/keypoint pipeline.
- Requires careful calibration to avoid measuring parser artifacts as fit.
- More moving parts and more disk/runtime cost.

### Recommended Use

Use Option B before backend/frontend product integration. This is the first
option that can support genuine fit-aware candidate selection.

## PSNR/SSIM As Auxiliary Signals

PC3 `metrics.json` may include PSNR/SSIM. These can be useful but should not be
treated as direct fit measurements.

Recommended use:

- Store PSNR/SSIM under candidate-level auxiliary metrics.
- Use them as tie-breakers or debug fields in smoke reports.
- Do not map PSNR/SSIM directly to `shoulder_ratio`, `torso_width_ratio`,
  `garment_length_ratio`, or `fit_label`.
- Do not include PSNR/SSIM inside `fit_analysis.measurements`.
- If used in reranking, apply a small adjustment outside `fit_analysis.v2`, for
  example through evaluator candidate warnings or a future `auxiliary_scores`
  field.

Reasoning:

- PSNR/SSIM are pixel similarity metrics.
- They may reward blurry or conservative outputs.
- They do not directly detect shoulder fit, torso width, sleeve length, or hem
  position.
- They are more appropriate as generation-quality or reconstruction auxiliary
  signals.

## Proposed Attachment Output Schema

Keep `fit_analysis.v2` unchanged. Add attachment metadata through `source` and
candidate-level fields.

Candidate after attachment:

```json
{
  "pair_id": "EP00000000",
  "candidate_id": "EP00000000_rank8_module8_seed_1234",
  "generator": "rank8_module8",
  "generator_version": "chunk_001_sanity",
  "seed": 1234,
  "image_path": "D:/portable/path/result.png",
  "inference_status": "success",
  "fit_analysis": {
    "schema_version": "fit_analysis.v2",
    "source": {
      "type": "generated_candidate_visual",
      "pair_id": "EP00000000",
      "candidate_id": "EP00000000_rank8_module8_seed_1234",
      "generator": "rank8_module8",
      "candidate_specific": true,
      "attachment_version": "fit_attachment.v1"
    },
    "fit_label": "regular",
    "measurements": {
      "shoulder_ratio": 1.04,
      "torso_width_ratio": 1.08,
      "sleeve_length_ratio": 1.0,
      "garment_length_ratio": 1.12
    },
    "confidence": {
      "score": 82.5,
      "level": "high",
      "warnings": [
        "sleeve_length_ratio is a wrist-alignment proxy, not a calibrated sleeve-end measurement."
      ]
    },
    "fit": {
      "label": "regular",
      "scores": {
        "shoulder_ratio": 1.04,
        "torso_width_ratio": 1.08,
        "sleeve_length_ratio": 1.0,
        "garment_length_ratio": 1.12
      },
      "explanations": []
    },
    "quality": {
      "pose_quality": 0.95,
      "parsing_quality": 0.88,
      "body_visibility": 0.91,
      "quality_score": 0.825,
      "silhouette_score": 0.83
    },
    "hotspots": [],
    "annotations": []
  },
  "attachment": {
    "schema_version": "fit_attachment.v1",
    "source": "generated_candidate_visual",
    "candidate_specific": true,
    "generated_image_parse": "available",
    "generated_image_pose": "available",
    "auxiliary_metrics": {
      "psnr": 24.7,
      "ssim": 0.842
    },
    "warnings": []
  },
  "warnings": []
}
```

For Option A, set:

```json
{
  "attachment": {
    "schema_version": "fit_attachment.v1",
    "source": "pair_level_attachment",
    "candidate_specific": false,
    "warnings": [
      "fit_analysis_pair_level_not_candidate_specific"
    ]
  }
}
```

## Future Fine-Tuning And Preference Dataset Impact

The attachment output should be stored in a way that can later become
preference data:

```json
{
  "pair_id": "EP00000000",
  "candidate_a": {
    "candidate_id": "baseline",
    "generator": "baseline_stableviton",
    "fit_score": 76.2,
    "fit_label": "slightly_oversized",
    "warnings": []
  },
  "candidate_b": {
    "candidate_id": "rank8_module8",
    "generator": "rank8_module8",
    "fit_score": 84.1,
    "fit_label": "regular",
    "warnings": []
  },
  "preferred_candidate_id": "rank8_module8",
  "preference_source": "fit_aware_rule_v1",
  "human_review_status": "unreviewed",
  "notes": []
}
```

Recommended future fields:

- `fit_score_delta`
- `confidence_delta`
- `generator_pair`
- `fit_analysis_source`
- `candidate_specific`
- `human_preference_label`
- `reviewer_notes`
- `artifact_warnings`

This structure can support:

- ranking evaluation
- human review queues
- preference dataset construction
- generator calibration
- future fine-tuning signal selection

## Recommended Next Step

Do not proceed directly to backend/frontend integration. First implement a small
attachment smoke that can do one of the following:

1. Option A: attach existing pair-level `fit_analysis.v2` and clearly mark it
   as not candidate-specific.
2. Option B: attach candidate-specific `fit_analysis.v2` after generated-image
   parse/keypoint inputs are available.

For the next real reranking smoke, Option A is acceptable only as a contract
test. Option B is required before using selected candidates as model quality
evidence.
