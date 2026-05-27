# StableVITON CLI Smoke Test Log - RTX 4080

## Purpose

Before connecting StableVITON to the FastAPI backend on PC1, verify that the external StableVITON repository can run standalone CLI inference.

## Scope

- Confirm external StableVITON repo clone
- Confirm conda environment
- Confirm CUDA / PyTorch
- Confirm key dependency imports
- Confirm checkpoint locations
- Confirm VITON-HD test data structure
- Confirm inference command
- Record success or failure logs

## Current Status

- External repo clone: done
- Conda env creation: done
- CUDA check: done
- Dependency import check: done
- Checkpoint download: done
- VITON-HD test data setup: pending
- Inference run: not started

## Environment

| Item | Value |
| --- | --- |
| OS | Windows |
| GPU | NVIDIA GeForce RTX 4080 |
| External repo | `D:\GitHub\StableVITON` |
| Project repo | `D:\GitHub\fit-reasoning-vton` |
| StableVITON commit | `1d8ef0d Update README.md` |
| Conda env | `D:\conda-envs\vton` |
| Python | `3.10.20` |
| PyTorch | `2.0.0+cu117` |
| CUDA available | `True` |
| pytorch-lightning | `1.5.0` |
| OpenCV | `4.7.0` |
| NumPy | `1.26.4` |
| Albumentations | `1.3.1` |
| Diffusers | `0.20.2` |
| Transformers | `4.33.2` |
| pip check | `No broken requirements found` |

## Known Warnings

### pkg_resources deprecation warning

`pytorch_lightning==1.5.0` prints a `pkg_resources` deprecation warning.

This is not an import failure, so it does not block the smoke test.

### Triton warning

The Windows environment prints a `triton` warning during dependency checks.

This is not a `diffusers` import failure, so it does not block the smoke test.

## Checkpoint Status

The following checkpoints are placed locally under `D:\GitHub\StableVITON\ckpts`.

| File | Status | Size |
| --- | --- | --- |
| `VITONHD.ckpt` | done | about 6.85 GB |
| `VITONHD_PBE_pose.ckpt` | done | about 6.85 GB |
| `VITONHD_VAE_finetuning.ckpt` | done | about 376 MB |

Checkpoints are large local assets and must not be committed to GitHub.

## Current Verification Result

```text
Summary:
- external repo: ready
- checkpoints: ready
- data root: pending
- imports: ready
```

## VITON-HD Test Data Structure

`configs/VITONHD.yaml` uses `dataset_name: VITONHDDataset`.

`dataset.py` reads `test_pairs.txt` from the data root and uses the `test` split during inference.

StableVITON inference requires the following local data structure.

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

The current pending item is `D:\GitHub\StableVITON\DATA\zalando-hd-resized`.

See [VITON-HD Test Data Setup](../setup/vitonhd_test_data_setup.md).

## Next Step: VITON-HD Test Data Setup

Checkpoints and dependencies are ready. The remaining bottleneck is the VITON-HD test data structure.

Prepare the test data according to the StableVITON `dataset.py` requirements, then run the dry-run wrapper again. Actual CLI inference should be executed with `run_stableviton_smoke.py --execute` only after the data root is reported as ready.

## Planned Inference Command

Run only after the VITON-HD test data structure is ready.

```powershell
cd D:\GitHub\StableVITON
conda activate D:\conda-envs\vton

python inference.py `
  --config_path .\configs\VITONHD.yaml `
  --batch_size 1 `
  --model_load_path .\ckpts\VITONHD.ckpt `
  --data_root_dir .\DATA\zalando-hd-resized `
  --save_dir .\samples_smoke
```

The safer dry-run wrapper from this repository can be used first.

```powershell
cd D:\GitHub\fit-reasoning-vton

D:\conda-envs\vton\python.exe .\scripts\run_stableviton_smoke.py `
  --stableviton-root D:\GitHub\StableVITON
```

Actual inference requires `--execute` and should only be run after the data root is ready.

## Verification Commands

External repo, checkpoint, data, and import check:

```powershell
cd D:\GitHub\fit-reasoning-vton

D:\conda-envs\vton\python.exe .\scripts\verify_external_stableviton.py `
  --stableviton-root D:\GitHub\StableVITON `
  --check-imports
```

Smoke command dry-run:

```powershell
cd D:\GitHub\fit-reasoning-vton

D:\conda-envs\vton\python.exe .\scripts\run_stableviton_smoke.py `
  --stableviton-root D:\GitHub\StableVITON
```

## Safety Notes

- Do not copy the external StableVITON repo into this repository.
- Do not commit checkpoints.
- Do not commit datasets.
- Do not commit generated images.
- Runtime and VRAM logs are local smoke-test notes, not official benchmark results.
- Record CLI inference success or failure only after the actual run happens.

## Next Steps

- Prepare VITON-HD test sample structure.
- Run `scripts/verify_external_stableviton.py`.
- Run `scripts/run_stableviton_smoke.py` dry-run.
- Run StableVITON CLI inference once test data is ready.
- Record success or failure logs.
