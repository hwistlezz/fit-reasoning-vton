# Fit-Aware Reranking Smoke Runbook

## Purpose

This runbook describes how to run a small fit-aware reranking smoke after PC3
delivers a candidate manifest. It is intentionally limited to a 30-50 candidate
sample and should not run generation, LoRA, full extraction, or backend/frontend
integration.

Do not execute this runbook until the PC3 manifest exists.

## Inputs

Expected PC3 handoff manifest:

```text
pc3_chunk_001_sanity_candidate_manifest.jsonl
```

The manifest contract is documented in:

```text
docs/pc3_candidate_manifest_handoff.md
```

Evaluator implementation:

```text
backend/app/services/fit_aware_evaluator.py
```

Synthetic smoke reference:

```text
scripts/smoke_fit_aware_evaluator.py
```

## Preflight

Before any reranking smoke:

1. Confirm Git worktree status.
2. Confirm C and D free space remain above the active reserved threshold.
3. Confirm the PC3 manifest path is outside Git-tracked dataset/output
   artifacts unless explicitly intended.
4. Confirm no image copy is needed.
5. Confirm `D:\fit_transfer\final_packages` and
   `C:\fit_transfer\work_39k_chunks` are not touched.
6. Confirm `rank8_module16` and `rank8-module16` are absent from the manifest.
7. Confirm this is a small sample smoke, not a full chunk rerank.

Suggested status checks:

```powershell
git status --short --branch

[pscustomobject]@{
  CFreeGB=[math]::Round(([System.IO.DriveInfo]::new('C:\')).AvailableFreeSpace/1GB,3)
  DFreeGB=[math]::Round(([System.IO.DriveInfo]::new('D:\')).AvailableFreeSpace/1GB,3)
} | ConvertTo-Json
```

## Manifest Validation

Validate the manifest before scoring:

- File exists and is readable.
- Every non-empty line is valid JSON.
- Required fields are present.
- `generator` is one of:
  - `baseline_stableviton`
  - `rank8_module8`
  - `seed_variant_future`
- `inference_status` is one of:
  - `success`
  - `failed`
  - `skipped`
- Excluded generators are absent:
  - `rank8_module16`
  - `rank8-module16`
- For `success` rows, `image_path` or `image_url` is present.
- If `image_path` is local and available to PC2, verify existence without
  copying images.

Manifest summary to report:

- total candidate count
- unique pair count
- success count
- failed count
- skipped count
- generator distribution
- count of success candidates with existing `image_path`
- count of success candidates with `image_url`

## Sample Selection

Use a small 30-50 candidate sample:

1. Prefer pair IDs that have both `baseline_stableviton` and `rank8_module8`.
2. Include only `inference_status == "success"` for reranking eligibility.
3. Keep failed/skipped rows only for taxonomy summary.
4. Do not copy images or create overlay images.
5. Do not write large JSONL/CSV reports.

Suggested sample policy:

```text
target_pair_count = 15 to 25
target_candidate_count = 30 to 50
prefer paired generators:
  baseline_stableviton + rank8_module8
fallback:
  any success candidate groups by pair_id
```

## Fit Analysis Attachment

The fit-aware evaluator expects each candidate to include `fit_analysis.v2`.
When PC3 only provides image manifest rows, a bridge step is needed before
reranking:

1. Locate existing fit analysis for the same `pair_id` if available.
2. Attach it under candidate `fit_analysis`.
3. If no fit analysis is available, mark candidate warning
   `fit_analysis_missing`.
4. Do not run full feature extraction during this smoke.

If per-candidate generated-image fit analysis is not available yet, treat this
smoke as a manifest and evaluator contract smoke, not as final model quality
evaluation.

## Reranking Smoke Procedure

For each sampled `pair_id`:

1. Build an in-memory manifest:
   - `schema_version`: `fit_aware_candidates.v1`
   - `pair_id`
   - `request_id`: smoke id
   - `candidates`: sampled candidate rows with attached `fit_analysis`
2. Call `evaluate_fit_aware_candidates(manifest)`.
3. Capture only small summary fields:
   - selected candidate id
   - selected generator
   - selected fit score
   - fit label
   - confidence score
   - selected reason
   - warning list
4. Verify `ranked_candidates` is sorted by fit score and tie-break rules.
5. Verify selected candidate is eligible and has `inference_status == "success"`.
6. Verify `user_facing_explanation` is non-empty Korean text.
7. Verify sleeve proxy warning appears when sleeve ratio is used.

Do not execute the synthetic smoke as a replacement for PC3 manifest smoke. The
synthetic smoke only verifies the evaluator module.

## Pairwise Comparison

When the same `pair_id` contains both baseline and rank8-module8 candidates:

1. Compare selected generator against all available candidates.
2. Record whether selected candidate is:
   - baseline
   - rank8_module8
   - other allowed generator
3. Compare fit scores:
   - `baseline_fit_score`
   - `rank8_module8_fit_score`
   - `delta_fit_score`
4. Inspect selected reason and warnings.

Pairwise smoke summary:

```json
{
  "pair_id": "EP00000000",
  "selected_generator": "rank8_module8",
  "baseline_fit_score": 78.4,
  "rank8_module8_fit_score": 84.2,
  "delta_fit_score": 5.8,
  "selected_reason": "Selected because it has the highest calibrated fit_score with reliable fit analysis.",
  "warnings": []
}
```

## Fit Score Distribution

For the 30-50 candidate smoke, summarize:

- min fit score
- p25 fit score
- median fit score
- p75 fit score
- max fit score
- selected candidate count by generator
- low confidence selected count
- candidates with `fit_analysis_missing`
- candidates with `cloth_type_unknown`
- candidates with `missing_core_ratio_count`
- candidates with sleeve proxy warning

## Selected Candidate Validation

A selected candidate is acceptable for backend/frontend integration only if:

- it is eligible
- `inference_status == "success"`
- `image_path` exists or `image_url` is present
- `fit_analysis.schema_version == "fit_analysis.v2"`
- `fit_score` is numeric in `0..100`
- `selected_reason` is non-empty
- `user_facing_explanation` is non-empty
- `measurements` mirrors selected `fit_analysis.measurements`
- `hotspots` mirrors selected `fit_analysis.hotspots`

If every candidate is low confidence, the result may still be accepted as
`best_available`, but the UI integration must show a warning.

## Error Taxonomy

Use these stable error/warning labels in the smoke report:

- `manifest_missing`
- `manifest_invalid_jsonl`
- `required_field_missing`
- `excluded_generator_present`
- `invalid_inference_status`
- `image_reference_missing`
- `image_path_not_found`
- `fit_analysis_missing`
- `fit_analysis_schema_invalid`
- `no_success_candidates`
- `no_pairwise_candidates`
- `all_candidates_low_confidence`
- `reranking_exception`

## Backend/Frontend Integration Gate

Proceed to backend/frontend integration only when:

1. PC3 manifest validates cleanly.
2. 30-50 candidate smoke completes without reranking exceptions.
3. At least one pairwise baseline vs rank8-module8 case is evaluated, if such
   pairs exist.
4. Selected candidate output has stable `fit_aware_selection.v1` shape.
5. User-facing Korean explanation is acceptable.
6. No large artifact files are created or staged.
7. No protected paths were modified or deleted.

Hold integration when:

- PC3 manifest is missing.
- Success candidate count is below 30.
- Most selected candidates are `unknown_low_confidence`.
- `fit_analysis.v2` is missing for most candidates.
- Image references are unavailable from PC2.

## Final Smoke Report Template

```text
- reranking smoke completed:
- manifest path:
- candidate count:
- unique pair count:
- success count:
- failed count:
- skipped count:
- generator distribution:
- sample size:
- pairwise comparison count:
- selected generator distribution:
- fit_score distribution:
- selected_candidate validation:
- selected_reason/user_facing_explanation validation:
- error taxonomy:
- large image copy created: must be no
- actual StableVITON inference run: must be no
- LoRA run: must be no
- protected paths modified: must be no
- protected paths deleted: must be no
- backend/frontend integration gate: pass/hold
- next recommended action:
```
