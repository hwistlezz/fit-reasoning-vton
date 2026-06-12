# AIHub 39k Chunk Transfer

This document covers the handoff boundary between PC2 package preparation and manual HTTP transfer to PC3.

## Scope

Codex/PC2 prepares final chunk packages only. A human starts the HTTP server, downloads from PC3, runs checksums, and confirms receipt.

Do not transfer preprocessing intermediates. Transfer only validation-passed final chunk package files.

## Package Contents

Each package is named like:

```text
aihub_39k_artifact_chunk_000_v1
```

Expected files under `C:\fit_transfer\final_packages`:

```text
aihub_39k_artifact_chunk_000_v1.7z.001
aihub_39k_artifact_chunk_000_v1.7z.002
...
aihub_39k_artifact_chunk_000_v1.sha256.txt
aihub_39k_artifact_chunk_000_v1_transfer_readme.md
```

The archive should include:

```text
image
cloth
worn
fit
openpose-json
image-parse
cloth-mask
image-densepose
agnostic-v3.2
agnostic-mask
metadata_chunk_final.csv
manifest_chunk_final.jsonl
validation_report.json
package_summary.json
```

## PC2 Preflight

Validate before packaging:

```powershell
python scripts\validate_39k_chunk_artifact.py `
  --metadata D:\fit_transfer\metadata_39k\chunks\chunk_000.csv `
  --artifact-root C:\fit_transfer\work_39k_chunks\chunk_000 `
  --output-dir D:\fit_transfer\reports\chunks\chunk_000 `
  --required-densepose `
  --required-agnostic
```

Package dry-run:

```powershell
python scripts\validate_stableviton_orientation.py `
  --metadata D:\fit_transfer\reports\chunks\chunk_000\metadata_chunk_final.csv `
  --artifact-root C:\fit_transfer\work_39k_chunks\chunk_000 `
  --output-dir D:\fit_transfer\reports\chunks\chunk_000 `
  --required-densepose `
  --required-agnostic `
  --force-pair EP00000002

python scripts\package_39k_chunk.py `
  --chunk-id chunk_000 `
  --artifact-root C:\fit_transfer\work_39k_chunks\chunk_000 `
  --validation-dir D:\fit_transfer\reports\chunks\chunk_000 `
  --output-root C:\fit_transfer\final_packages
```

Actual package:

```powershell
python scripts\package_39k_chunk.py `
  --chunk-id chunk_000 `
  --artifact-root C:\fit_transfer\work_39k_chunks\chunk_000 `
  --validation-dir D:\fit_transfer\reports\chunks\chunk_000 `
  --output-root C:\fit_transfer\final_packages `
  --no-dry-run
```

## 7z Test

Run this on PC2 before starting transfer:

```powershell
7z t "C:\fit_transfer\final_packages\aihub_39k_artifact_chunk_000_v1.7z.001"
```

The package helper writes the exact command into:

```text
C:\fit_transfer\final_packages\aihub_39k_artifact_chunk_000_v1_transfer_readme.md
```

Do not start this step if `orientation_sanity_report.json` is missing or failed.

## HTTP Server

Start the HTTP server manually on PC2:

```powershell
python -m http.server 8000 --directory "C:\fit_transfer\final_packages"
```

Transfer is manual. Do not commit package files or generated artifacts to git.

## PC3 Receipt Checklist

On PC3:

1. Download every `.7z.*` split part.
2. Download `.sha256.txt`.
3. Download `_transfer_readme.md`.
4. Verify SHA256 for every split part.
5. Run `7z t` on the first split part.
6. Extract to the PC3 dataset staging area.
7. Confirm `manifest_chunk_final.jsonl` line count equals `metadata_chunk_final.csv` row count.
8. Confirm the chunk is registered as received before PC2 deletes any local transfer copy.

## What Not To Transfer

Do not transfer:

- Raw AIHub source data.
- Processed master directories.
- Chunk work directories before validation.
- Failed validation outputs as training data.
- Contact sheets unless requested for review.
- Repo source code as part of dataset package.

## Deletion Policy

PC2 may delete old split parts or smoke/test copies only after PC3 confirms package extraction and validation. `review_delete` items require explicit approval.
