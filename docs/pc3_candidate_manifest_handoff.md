# PC3 Candidate Manifest Handoff

## Purpose

This document defines the handoff contract PC3 should provide after chunk
generation sanity inference. The manifest lets PC2 run a small fit-aware
reranking smoke without touching image generation outputs, package files, or
protected transfer paths.

This is a handoff document only. It does not require running StableVITON, LoRA,
reranking, full extraction, or any backend/frontend integration.

## Recommended Manifest File

```text
pc3_chunk_001_sanity_candidate_manifest.jsonl
```

Recommended delivery location should be agreed by handoff message. Do not place
large images in Git. The manifest should reference image paths or URLs that
already exist on the PC3 output side.

## JSONL Format

Use one JSON object per generated candidate.

Example:

```json
{
  "pair_id": "EP00000000",
  "chunk_id": "chunk_001",
  "split": "train",
  "candidate_id": "EP00000000_baseline_stableviton_seed_1234",
  "generator": "baseline_stableviton",
  "generator_version": "stableviton_baseline_sanity",
  "seed": 1234,
  "image_path": "D:/pc3/output/chunk_001/EP00000000_baseline.png",
  "image_url": null,
  "person_path": "D:/pc3/input/chunk_001/image/EP00000000.jpg",
  "cloth_path": "D:/pc3/input/chunk_001/cloth/EP00000000.jpg",
  "artifact_root": "D:/pc3/output/chunk_001",
  "inference_status": "success",
  "error_code": null,
  "created_at": "2026-07-04T12:00:00+09:00",
  "checksum_optional": {
    "sha256": null
  }
}
```

## Required Fields

| field | required | notes |
| --- | --- | --- |
| `pair_id` | yes | AIHub or project pair id. |
| `chunk_id` | yes | Example: `chunk_001`. |
| `split` | yes | Dataset split if known. |
| `candidate_id` | yes | Unique and stable within the manifest. |
| `generator` | yes | Must use one of the allowed values below. |
| `generator_version` | yes | Human-readable generator/config version. |
| `seed` | yes | Use `null` only if no seed exists. |
| `image_path` or `image_url` | yes | At least one is required. |
| `person_path` | yes | Input person path or URL used by PC3. |
| `cloth_path` | yes | Input cloth path or URL used by PC3. |
| `artifact_root` | yes | Root of the candidate output artifact. |
| `inference_status` | yes | Must use one of the allowed values below. |
| `error_code` | yes | Null for success, stable string for failed/skipped. |
| `created_at` | yes | ISO-8601 timestamp with timezone when possible. |
| `checksum_optional` | yes | Object is required; individual checksum values may be null. |

## Allowed Generators

Allowed:

- `baseline_stableviton`
- `rank8_module8`
- `seed_variant_future`

Excluded:

- `rank8_module16`
- `rank8-module16`

If PC3 accidentally runs an excluded generator, the final handoff report must
state that clearly and PC2 should not include those candidates in reranking.

## Allowed Inference Status

- `success`
- `failed`
- `skipped`

Only `success` candidates are eligible for fit-aware selection. Failed and
skipped candidates should remain in the manifest for accounting and error
taxonomy.

## PC3 Final Report Requirements

PC3 final report must include:

- manifest path
- candidate count
- unique pair count
- success count
- failed count
- skipped count
- generator distribution
- output image root
- 3 sample records copied directly from the manifest
- whether `rank8-module16` or `rank8_module16` was executed

## PC2 Intake Checklist

Before PC2 runs any smoke:

1. Confirm the manifest path exists.
2. Confirm the manifest is JSONL, one object per line.
3. Confirm no large images need to be copied.
4. Confirm `generator` does not include excluded values.
5. Confirm `inference_status` uses only `success`, `failed`, or `skipped`.
6. Confirm `success` candidates have `image_path` or `image_url`.
7. Confirm there are at least 30 successful candidates before a 30-row smoke.
8. Confirm there are same-`pair_id` pairs with both `baseline_stableviton` and
   `rank8_module8` before pairwise comparison.

## Safety Rules

Do not modify:

- `D:\fit_transfer\final_packages`
- `C:\fit_transfer\work_39k_chunks`
- `backend\datasets\raw`
- `backend\datasets\processed`

Do not run:

- StableVITON inference
- LoRA
- rank8-module16
- full 39k extraction
- full CSV regeneration

Do not commit:

- dataset files
- generated images
- JSONL output manifests
- archives
- checksums
- package files
- report artifacts
