# VITON-HD Test Data Setup

## Purpose

Prepare the VITON-HD test data structure required for the StableVITON CLI inference smoke test.

This guide is based on the external StableVITON files below:

- `D:\GitHub\StableVITON\dataset.py`
- `D:\GitHub\StableVITON\inference.py`
- `D:\GitHub\StableVITON\configs\VITONHD.yaml`

## Download Source

Use the preprocessed VITON-HD dataset from the official VITON-HD project instructions.

Official VITON-HD repository:
https://github.com/shadow2496/VITON-HD

Do not copy dataset files into this repository. Keep them under the external StableVITON workspace.

## Local Target Path

The smoke test expects the local data root below.

```text
D:\GitHub\StableVITON\DATA\zalando-hd-resized
```

## StableVITON Dataset Loader Findings

`configs/VITONHD.yaml` sets:

```yaml
dataset_name: VITONHDDataset
```

`inference.py` creates the dataset with:

```python
is_paired=not args.unpair
is_test=True
is_sorted=True
```

`dataset.py` then reads:

```text
{data_root_dir}/test_pairs.txt
```

Each non-empty line in `test_pairs.txt` must contain two whitespace-separated columns:

```text
person_image_name cloth_image_name
```

Because `is_test=True`, the loader uses the `test` split.

## Required Test Structure

The required test structure is:

```text
DATA/zalando-hd-resized/
  test_pairs.txt
  test/
    image/
    image-densepose/
    agnostic-v3.2/
    agnostic-mask/
    cloth/
    cloth-mask/
```

Note that the cloth mask directory is `cloth-mask`, not `cloth_mask`.

## File Lookup Rules

For a pair line:

```text
person.jpg cloth.jpg
```

StableVITON reads person-side files from:

```text
test/image/person.jpg
test/image-densepose/person.jpg
test/agnostic-v3.2/person.jpg
test/agnostic-mask/person_mask.png
```

The agnostic mask filename is built by replacing `.jpg` with `_mask.png`.

In default paired mode, the loader ignores the second column for the cloth filename and uses the person image filename:

```text
test/cloth/person.jpg
test/cloth-mask/person.jpg
```

With `--unpair`, the loader uses the second column for the cloth filename:

```text
test/cloth/cloth.jpg
test/cloth-mask/cloth.jpg
```

## Minimum Smoke-Test Recommendation

For a minimal smoke test, prepare 1 to 3 lines in `test_pairs.txt`.

If using default paired mode, each line can still include two columns, but the person filename must also exist under `test/cloth/` and `test/cloth-mask/`.

If using unpaired mode, pass `--unpair` to `scripts/run_stableviton_smoke.py` so the cloth filename from column 2 is used.

## Mini Smoke Dataset Strategy

The default VITON-HD `test.zip` does not include every StableVITON inference input. In particular, `image-densepose`, `agnostic-v3.2`, and `agnostic-mask` may be missing.

Instead of preparing the full VITON-HD test set at once, first copy only the first 1 to 3 pairs from `test_pairs.txt` into a separate local mini dataset.

Target path:

```text
D:\GitHub\StableVITON\DATA\stableviton-smoke
```

The helper below copies the available base test files:

```powershell
cd D:\GitHub\fit-reasoning-vton

D:\conda-envs\vton\python.exe .\scripts\prepare_stableviton_smoke_subset.py `
  --source-root D:\GitHub\StableVITON\DATA\zalando-hd-resized `
  --target-root D:\GitHub\StableVITON\DATA\stableviton-smoke `
  --num-samples 3
```

It creates:

```text
DATA/stableviton-smoke/
  test_pairs.txt
  test/
    image/
    image-parse/
    openpose-img/
    openpose-json/
    cloth/
    cloth-mask/
    image-densepose/
    agnostic-v3.2/
    agnostic-mask/
```

Then generate approximate agnostic inputs from `image-parse`:

```powershell
D:\conda-envs\vton\python.exe .\scripts\generate_stableviton_agnostic_from_parse.py `
  --data-root D:\GitHub\StableVITON\DATA\stableviton-smoke
```

This approximate preprocessing fills upper-garment parsing labels with gray and writes:

```text
test/agnostic-v3.2/{person_file}
test/agnostic-mask/{person_base}_mask.png
```

This is not official StableVITON preprocessing and must only be used for CLI smoke-test preparation. It is not suitable for benchmark reporting or qualitative claims.

After this step, `image-densepose` is still required. Generate or copy DensePose files for the same person filenames before running actual StableVITON inference.

## PowerShell Placement Checks

```powershell
cd D:\GitHub\StableVITON

Get-ChildItem .\DATA\zalando-hd-resized
Get-ChildItem .\DATA\zalando-hd-resized\test

Get-ChildItem .\DATA\zalando-hd-resized\test\image | Select-Object -First 5 Name
Get-ChildItem .\DATA\zalando-hd-resized\test\cloth | Select-Object -First 5 Name
Get-ChildItem .\DATA\zalando-hd-resized\test\cloth-mask | Select-Object -First 5 Name
Get-Content .\DATA\zalando-hd-resized\test_pairs.txt -TotalCount 5
```

Mini smoke dataset checks:

```powershell
Get-ChildItem .\DATA\stableviton-smoke
Get-ChildItem .\DATA\stableviton-smoke\test
Get-ChildItem .\DATA\stableviton-smoke\test\agnostic-v3.2 | Select-Object -First 5 Name
Get-ChildItem .\DATA\stableviton-smoke\test\agnostic-mask | Select-Object -First 5 Name
Get-ChildItem .\DATA\stableviton-smoke\test\image-densepose | Select-Object -First 5 Name
Get-Content .\DATA\stableviton-smoke\test_pairs.txt -TotalCount 5
```

## Project Verification Commands

```powershell
cd D:\GitHub\fit-reasoning-vton

D:\conda-envs\vton\python.exe .\scripts\verify_external_stableviton.py `
  --stableviton-root D:\GitHub\StableVITON `
  --check-imports

D:\conda-envs\vton\python.exe .\scripts\run_stableviton_smoke.py `
  --stableviton-root D:\GitHub\StableVITON
```

To verify the mini smoke dataset instead of the default data root:

```powershell
D:\conda-envs\vton\python.exe .\scripts\verify_external_stableviton.py `
  --stableviton-root D:\GitHub\StableVITON `
  --data-root D:\GitHub\StableVITON\DATA\stableviton-smoke `
  --check-imports

D:\conda-envs\vton\python.exe .\scripts\run_stableviton_smoke.py `
  --stableviton-root D:\GitHub\StableVITON `
  --data-root DATA\stableviton-smoke `
  --unpair
```

Expected state after data setup:

```text
Summary:
- external repo: ready
- checkpoints: ready
- data root: ready
- imports: ready
```

## Absolute Prohibitions

- Do not upload original VITON-HD data to GitHub.
- Do not upload checkpoints to GitHub.
- Do not upload generated outputs to GitHub.
- Do not copy datasets into `D:\GitHub\fit-reasoning-vton`.
- Do not commit images, masks, densepose files, agnostic files, or generated samples.
