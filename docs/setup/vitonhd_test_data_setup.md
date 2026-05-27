# VITON-HD Test Data Setup

## Purpose

Prepare the VITON-HD test data structure required for the StableVITON CLI inference smoke test.

## Required Root

StableVITON `inference.py` uses the following local data root for the planned smoke test.

```text
D:\GitHub\StableVITON\DATA\zalando-hd-resized
```

## Required Test Structure

```text
DATA/zalando-hd-resized/
  test/
    image/
    image-densepose/
    agnostic-v3.2/
    agnostic-mask/
    cloth/
    cloth_mask/
```

## Safety Notes

- Do not upload original VITON-HD data to public GitHub.
- Keep test images, cloth images, densepose files, agnostic images, and mask files local only.
- This repository should contain only data structure notes and smoke-test logs.
- Do not upload generated images to GitHub.

## Minimum Smoke-Test Recommendation

If the full dataset is too large, prepare only 1 to 3 test samples first.

For each person sample, these files should match:

```text
test/image/{person_file}
test/image-densepose/{same_person_file}
test/agnostic-v3.2/{same_person_file}
test/agnostic-mask/{same_person_file}
```

For each cloth sample, these files should match:

```text
test/cloth/{cloth_file}
test/cloth_mask/{cloth_file}
```

Check the StableVITON dataset loader in the external repository to confirm whether it also requires a pair list file or a specific filename convention.

## Verification Command

```powershell
cd D:\GitHub\fit-reasoning-vton

D:\conda-envs\vton\python.exe .\scripts\verify_external_stableviton.py `
  --stableviton-root D:\GitHub\StableVITON `
  --check-imports
```

Expected state after data setup:

```text
Summary:
- external repo: ready
- checkpoints: ready
- data root: ready
- imports: ready
```
