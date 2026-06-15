# AIHub Agnostic Mask Rule v2

This note documents the PC2 rule for regenerating AIHub `agnostic-v3.2` and `agnostic-mask` artifacts before 39k chunk packaging.

## Problem

The first `chunk_000` artifact passed file-level validation and orientation checks, but PC3 fixed-eval results showed weak garment replacement: haze, ghosting, and new clothing blending into the original body/clothing. PC2 semantic diagnosis found that most `agnostic-mask` files were too small for StableVITON top/outer replacement.

## Rule

`scripts/generate_keypoint_agnostic_v3.py` now builds the replacement mask from:

- OpenPose shoulder, hip, elbow, and wrist keypoints.
- AIHub segmentation polygons when `annotation_json` is available.
- A broader torso box from shoulder to hip with horizontal padding.
- Sleeve corridors that stop before the wrist to preserve hands.
- Face, hand, lower-body, and background preservation masks.
- Morphological close, hole fill, dilation, and adaptive dilation until the mask reaches the target range.

For top/outer garments:

```text
target mask ratio: 0.12 to 0.28
suspicious too small: < 0.10
suspicious too large: > 0.40
```

The saved `agnostic-mask` remains binary. Any feathering or blur should be limited to debug visualization, not the training artifact.

## Smoke Command

```powershell
python scripts\generate_keypoint_agnostic_v3.py `
  --data-root C:\fit_transfer\work_39k_chunks\chunk_000 `
  --layout chunk-flat `
  --metadata D:\fit_transfer\reports\chunks\chunk_000\metadata_chunk_final.csv `
  --output-root D:\fit_transfer\reports\agnostic_mask_rule_v2_smoke\artifact_after `
  --limit 100 `
  --force-pair EP00000002 `
  --diagnostics-json D:\fit_transfer\reports\agnostic_mask_rule_v2_smoke\generation_diagnostics.json
```

Then run:

```powershell
python scripts\diagnose_agnostic_mask_semantics.py `
  --metadata D:\fit_transfer\reports\chunks\chunk_000\metadata_chunk_final.csv `
  --artifact-root-before C:\fit_transfer\work_39k_chunks\chunk_000 `
  --artifact-root-after D:\fit_transfer\reports\agnostic_mask_rule_v2_smoke\artifact_after `
  --output-dir D:\fit_transfer\reports\agnostic_mask_rule_v2_smoke `
  --limit 100 `
  --force-pair EP00000002
```

## Package Gate

Do not package a chunk unless the semantic report is reviewed:

```text
D:\fit_transfer\reports\agnostic_mask_rule_v2_smoke\summary.json
D:\fit_transfer\reports\agnostic_mask_rule_v2_smoke\contact_agnostic_before_after.jpg
D:\fit_transfer\reports\agnostic_mask_rule_v2_smoke\contact_mask_ratio_extremes_after.jpg
D:\fit_transfer\reports\agnostic_mask_rule_v2_smoke\contact_semantic_suspicious_after.jpg
```

If the semantic gate fails, regenerate only `agnostic-v3.2` and `agnostic-mask` first. `image`, `cloth`, `worn`, `image-densepose`, `image-parse`, and `openpose-json` do not need full regeneration when their validation still passes.
