# StableVITON CLI Smoke Test Log - RTX 4080

## Purpose

Verify that the external StableVITON repository can run standalone CLI inference on PC1 before connecting it to the FastAPI backend.

This is a CLI smoke test, not a full VITON-HD benchmark.

## Final Result

StableVITON CLI smoke test succeeded on the PC1 RTX 4080 environment.

| Item | Value |
| --- | --- |
| Sample pairs | `3` |
| Mode | `unpaired` |
| Batch size | `1` |
| Denoise steps | `50` |
| Image size | `512 x 384` |
| Data root | `D:\GitHub\StableVITON\DATA\stableviton-smoke` |
| Output path | `D:\GitHub\StableVITON\samples_smoke\unpair` |
| Total elapsed seconds | `51.6623159` |
| Max VRAM used | `9679 MiB` (`9.45 GB`) |
| Generated result images | `3` |

The elapsed time and VRAM values are observed smoke-test measurements for a 3-pair mini dataset on PC1. They are not official benchmark numbers.

Measurement files committed to this repository:

- [stableviton_smoke_inference_time_4080.txt](stableviton_smoke_inference_time_4080.txt)
- [stableviton_smoke_vram_4080.csv](stableviton_smoke_vram_4080.csv)

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

## Preflight Result

The following items were checked before inference:

- StableVITON root
- `inference.py`
- `configs/VITONHD.yaml`
- `ckpts/VITONHD.ckpt`
- `DATA\stableviton-smoke`
- `test_pairs.txt`: 3 pairs
- `test\image`
- `test\image-densepose`
- `test\agnostic-v3.2`
- `test\agnostic-mask`
- `test\cloth`
- `test\cloth-mask`

Verification summary:

```text
Summary:
- external repo: ready
- checkpoints: ready
- data root: ready
- imports: ready
```

## Checkpoint Status

The following checkpoints are placed locally under `D:\GitHub\StableVITON\ckpts`.

| File | Status | Size |
| --- | --- | --- |
| `VITONHD.ckpt` | done | about 6.85 GB |
| `VITONHD_PBE_pose.ckpt` | done | about 6.85 GB |
| `VITONHD_VAE_finetuning.ckpt` | done | about 376 MB |

Checkpoints are local assets and must not be committed to GitHub.

## StableVITON Dataset Requirements

`configs/VITONHD.yaml` uses:

```yaml
dataset_name: VITONHDDataset
```

`dataset.py` reads `test_pairs.txt` from the data root and uses the `test` split during inference.

The StableVITON inference structure is:

```text
DATA/{data_root}/
  test_pairs.txt
  test/
    image/
    image-densepose/
    agnostic-v3.2/
    agnostic-mask/
    cloth/
    cloth-mask/
```

The official VITON-HD `test.zip` does not include every StableVITON-specific input. The missing preprocessing artifacts were handled with a mini smoke dataset.

See [VITON-HD Test Data Setup](../setup/vitonhd_test_data_setup.md).

## Mini Smoke Dataset

The mini smoke dataset path is:

```text
D:\GitHub\StableVITON\DATA\stableviton-smoke
```

It was prepared from the first 3 pairs in `test_pairs.txt`:

```text
08909_00.jpg -> 02783_00.jpg
00891_00.jpg -> 01430_00.jpg
03615_00.jpg -> 09933_00.jpg
```

The mini dataset includes:

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
    agnostic-v3.2/
    agnostic-mask/
    image-densepose/
```

`agnostic-v3.2` and `agnostic-mask` were generated with approximate smoke-test preprocessing from `image-parse`. These are not official StableVITON benchmark preprocessing outputs.

`image-densepose` was generated with WSL Ubuntu + Detectron2 DensePose and renamed so the StableVITON dataset loader could find `{person_name}.jpg`.

## Execution Command

The smoke test was executed through the repository wrapper:

```powershell
D:\conda-envs\vton\python.exe D:\GitHub\fit-reasoning-vton\scripts\run_stableviton_smoke.py `
  --stableviton-root D:\GitHub\StableVITON `
  --data-root DATA\stableviton-smoke `
  --unpair `
  --execute
```

The wrapper emitted this StableVITON command:

```powershell
D:\conda-envs\vton\python.exe inference.py `
  --config_path .\configs\VITONHD.yaml `
  --batch_size 1 `
  --model_load_path .\ckpts\VITONHD.ckpt `
  --data_root_dir .\DATA\stableviton-smoke `
  --save_dir .\samples_smoke `
  --denoise_steps 50 `
  --img_H 512 `
  --img_W 384 `
  --unpair
```

## Generated Result Files

StableVITON CLI smoke test result images were generated and checked locally.

Generated files:

```text
samples_smoke/unpair/00891_00_01430_00.jpg
samples_smoke/unpair/03615_00_09933_00.jpg
samples_smoke/unpair/08909_00_02783_00.jpg
```

Latest local file sizes:

| File | Size |
| --- | ---: |
| `00891_00_01430_00.jpg` | `33206 bytes` |
| `03615_00_09933_00.jpg` | `40695 bytes` |
| `08909_00_02783_00.jpg` | `49030 bytes` |

The result images were not uploaded to GitHub to avoid VITON-HD dataset and generated-image license/copyright issues.

## Inference Time

The run was measured with:

```powershell
$elapsed = Measure-Command {
  D:\conda-envs\vton\python.exe D:\GitHub\fit-reasoning-vton\scripts\run_stableviton_smoke.py --stableviton-root D:\GitHub\StableVITON --data-root DATA\stableviton-smoke --unpair --execute
}

"Elapsed seconds: $($elapsed.TotalSeconds)" | Tee-Object -FilePath D:\GitHub\fit-reasoning-vton\docs\experiments\stableviton_smoke_inference_time_4080.txt
```

Observed result:

```text
Elapsed seconds: 51.6623159
```

This is a smoke-test observation, not an official benchmark.

## VRAM Observation

VRAM was sampled with:

```powershell
nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv -l 1 > docs\experiments\stableviton_smoke_vram_4080.csv
```

Observed result:

- CSV rows: `79`
- Max VRAM used: `9679 MiB` (`9.45 GB`)

This is a smoke-test observation, not an official benchmark.

## Troubleshooting

### 1. VITON-HD default test.zip structure

The official VITON-HD `test.zip` provided this base structure:

```text
DATA/zalando-hd-resized/
  test_pairs.txt
  test/
    image/
    cloth/
    cloth-mask/
    image-parse/
    openpose-img/
    openpose-json/
```

StableVITON inference required:

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

The missing items were:

```text
test/image-densepose
test/agnostic-v3.2
test/agnostic-mask
```

The issue was not the checkpoint. Checkpoints, CUDA, PyTorch, and dependency imports were ready. The issue was that StableVITON expects preprocessed DensePose, agnostic image, and agnostic mask inputs at inference time.

### 2. Mini smoke dataset

Instead of preprocessing the full VITON-HD test set, the first 3 pairs from `test_pairs.txt` were copied into:

```text
D:\GitHub\StableVITON\DATA\stableviton-smoke
```

This kept the smoke test small and isolated from the default dataset root.

### 3. Approximate agnostic preprocessing

`generate_stableviton_agnostic_from_parse.py` generated approximate `agnostic-v3.2` and `agnostic-mask` files from `image-parse`.

This is not identical to official StableVITON benchmark preprocessing. It is only for smoke testing whether CLI inference can run end to end.

### 4. DensePose image-densepose

DensePose was generated in WSL Ubuntu with Detectron2 DensePose and `apply_net.py show`.

The raw DensePose output names looked like `08909_00.0001.png`, so outputs were converted/renamed to `{person_name}.jpg` for the StableVITON dataset loader.

### 5. Dependency issue: cleanfid

StableVITON inference initially failed with:

```text
ModuleNotFoundError: No module named 'cleanfid'
```

It was resolved with:

```powershell
D:\conda-envs\vton\python.exe -m pip install clean-fid
```

The `No module named 'triton'` warning remained, but it did not stop inference.

### 6. Unpaired mode

The mini smoke `test_pairs.txt` uses different person and cloth filenames, so inference had to run with `--unpair`.

## Safety Notes

- Do not copy the external StableVITON repo into this repository.
- Do not commit checkpoints.
- Do not commit datasets.
- Do not commit generated images.
- Runtime and VRAM values are local smoke-test notes, not official benchmark results.

## Remaining Work

- Full VITON-HD batch inference is not done.
- Official benchmark-quality preprocessing is not done.
- Fit analyzer and confidence scoring are not connected.
- FastAPI backend does not yet call StableVITON automatically.
