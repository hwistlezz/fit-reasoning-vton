# AIHub 39k Chunk Pipeline

This document describes the PC2-side workflow for producing 39k StableVITON/LoRA/full-finetuning artifact data in 10k chunks. PC2 prepares validated final packages only. HTTP transfer to PC3 is manual.

## Goals

- Build clean 39k metadata from `aihub_pairs_explicit_pending.csv`.
- Exclude known bad pairs before any artifact work.
- Process, validate, review, and package one chunk at a time.
- Keep heavy intermediate work off the repository.
- Send only validation-passed final chunk packages to PC3.

## Fixed Paths

```text
Input metadata:
D:\projects\fit-reasoning-vton\backend\datasets\processed\index\aihub_pairs_explicit_pending.csv

Metadata output:
D:\fit_transfer\metadata_39k

Chunk work root:
C:\fit_transfer\work_39k_chunks

Final package root:
C:\fit_transfer\final_packages

Reports:
D:\fit_transfer\reports
```

## Known Bad Pairs

These pair IDs are always excluded:

```text
EP00003620
EP00003937
EP00005080
EP00007279
```

## Step 1: Build Metadata And Chunk Manifests

```powershell
python scripts\build_39k_chunk_manifest.py
```

Default outputs:

```text
D:\fit_transfer\metadata_39k\metadata_39k_clean_candidate.csv
D:\fit_transfer\metadata_39k\metadata_39k_train.csv
D:\fit_transfer\metadata_39k\metadata_39k_val.csv
D:\fit_transfer\metadata_39k\metadata_39k_fixed_eval_100.csv
D:\fit_transfer\metadata_39k\chunks\chunk_000.csv
D:\fit_transfer\metadata_39k\chunks\chunk_001.csv
D:\fit_transfer\metadata_39k\chunks\chunk_002.csv
D:\fit_transfer\metadata_39k\chunks\chunk_003.csv
D:\fit_transfer\metadata_39k\chunk_summary_39k.json
D:\fit_transfer\metadata_39k\bad_pairs_known.csv
```

The builder reuses existing chunk CSVs only when the stored `pair_id` order exactly matches the expected chunk. Use `--no-reuse-existing` to force regeneration.

## Step 2: Generate One Chunk Artifact

Artifact generation is intentionally outside this PR. The expected chunk root layout is:

```text
C:\fit_transfer\work_39k_chunks\chunk_000\
  image\
  cloth\
  worn\
  fit\
  openpose-json\
  image-parse\
  cloth-mask\
  image-densepose\
  agnostic-v3.2\
  agnostic-mask\
```

Intermediate preprocessing outputs should stay on PC2 and should not be transferred to PC3.

## Step 3: Validate The Chunk

```powershell
python scripts\validate_39k_chunk_artifact.py `
  --metadata D:\fit_transfer\metadata_39k\chunks\chunk_000.csv `
  --artifact-root C:\fit_transfer\work_39k_chunks\chunk_000 `
  --output-dir D:\fit_transfer\reports\chunks\chunk_000 `
  --required-densepose `
  --required-agnostic
```

Validation outputs:

```text
D:\fit_transfer\reports\chunks\chunk_000\validation_report.json
D:\fit_transfer\reports\chunks\chunk_000\validation_details.jsonl
D:\fit_transfer\reports\chunks\chunk_000\bad_pairs_auto.csv
D:\fit_transfer\reports\chunks\chunk_000\metadata_chunk_final.csv
D:\fit_transfer\reports\chunks\chunk_000\manifest_chunk_final.jsonl
```

The final package gate is `validation_report.json.status == passed` and `failed_count == 0`.

## Step 4: Make Contact Sheets

```powershell
python scripts\make_39k_chunk_contact_sheets.py `
  --metadata D:\fit_transfer\metadata_39k\chunks\chunk_000.csv `
  --artifact-root C:\fit_transfer\work_39k_chunks\chunk_000 `
  --output-dir D:\fit_transfer\reports\chunks\chunk_000 `
  --validation-details D:\fit_transfer\reports\chunks\chunk_000\validation_details.jsonl
```

Default sheets:

```text
contact_sheets_random_500.jpg
contact_sheets_upper_300.jpg
contact_sheets_vertical_200.jpg
contact_sheets_low_confidence_200.jpg
contact_sheets_densepose_suspicious_200.jpg
contact_sheets_agnostic_suspicious_200.jpg
```

## Step 5: Package The Chunk

Dry-run packaging:

```powershell
python scripts\package_39k_chunk.py `
  --chunk-id chunk_000 `
  --artifact-root C:\fit_transfer\work_39k_chunks\chunk_000 `
  --validation-dir D:\fit_transfer\reports\chunks\chunk_000 `
  --output-root C:\fit_transfer\final_packages
```

Actual packaging:

```powershell
python scripts\package_39k_chunk.py `
  --chunk-id chunk_000 `
  --artifact-root C:\fit_transfer\work_39k_chunks\chunk_000 `
  --validation-dir D:\fit_transfer\reports\chunks\chunk_000 `
  --output-root C:\fit_transfer\final_packages `
  --no-dry-run
```

Package name:

```text
aihub_39k_artifact_chunk_000_v1
```

The package includes only required artifact folders and validation-final metadata/report files. It also writes a transfer README with the 7z test command and manual HTTP server command.

## Chunk Execution Order

Recommended order:

```text
chunk_000
chunk_001
chunk_002
chunk_003
```

For each chunk:

1. Generate artifacts under `C:\fit_transfer\work_39k_chunks\<chunk_id>`.
2. Validate with strict densepose and agnostic requirements.
3. Review contact sheets.
4. Package only if validation passes.
5. Manually transfer only final package split parts, checksum, and transfer README.
6. Keep local reports and metadata on PC2.

## Space Notes

Full 39k packaging does not fit comfortably on the current PC2 disks. Chunked 10k or 5k processing is the supported path. Keep large zip/7z/split parts outside the repository.
