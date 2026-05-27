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
- Mini VITON-HD smoke data setup: done
- DensePose image-densepose setup: done
- StableVITON CLI inference run: done
- Result images: 3 local files generated

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
- data root: ready
- imports: ready
```

The ready data root is the local mini smoke dataset:

```text
D:\GitHub\StableVITON\DATA\stableviton-smoke
```

The default VITON-HD test data root exists locally, but the official `test.zip` structure was partial for StableVITON because `image-densepose`, `agnostic-v3.2`, and `agnostic-mask` were missing.

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

The default VITON-HD `test.zip` may not include the StableVITON-specific `image-densepose`, `agnostic-v3.2`, and `agnostic-mask` inputs. For the first smoke test, use a mini local subset:

```powershell
cd D:\GitHub\fit-reasoning-vton

D:\conda-envs\vton\python.exe .\scripts\prepare_stableviton_smoke_subset.py `
  --source-root D:\GitHub\StableVITON\DATA\zalando-hd-resized `
  --target-root D:\GitHub\StableVITON\DATA\stableviton-smoke `
  --num-samples 3

D:\conda-envs\vton\python.exe .\scripts\generate_stableviton_agnostic_from_parse.py `
  --data-root D:\GitHub\StableVITON\DATA\stableviton-smoke
```

The generated agnostic files are approximate smoke-test inputs based on `image-parse`; they are not official StableVITON preprocessing outputs. DensePose files still need to be prepared separately before actual inference.

## Planned Inference Command

The smoke test was executed with the mini smoke data root and unpaired mode.

```powershell
D:\conda-envs\vton\python.exe D:\GitHub\fit-reasoning-vton\scripts\run_stableviton_smoke.py `
  --stableviton-root D:\GitHub\StableVITON `
  --data-root DATA\stableviton-smoke `
  --unpair `
  --execute
```

The wrapper emitted this StableVITON inference command:

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

## Smoke Test Result

StableVITON CLI smoke test result images were generated and checked locally.

Generated files:

```text
samples_smoke/unpair/00891_00_01430_00.jpg
samples_smoke/unpair/03615_00_09933_00.jpg
samples_smoke/unpair/08909_00_02783_00.jpg
```

The result images were not uploaded to GitHub to avoid VITON-HD dataset and generated-image license/copyright issues.

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

## Troubleshooting: StableVITON test data preprocessing 문제 해결

### 문제 상황

StableVITON CLI inference를 실행하기 위해 VITON-HD 공식 Google Drive에서 `datasets/test.zip`을 다운로드했다.

압축 해제 후 기본 구조는 다음과 같았다.

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

하지만 StableVITON `dataset.py`와 `inference.py` 구조에서 요구하는 입력은 다음과 달랐다.

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

즉, 공식 VITON-HD 기본 `test.zip`만으로는 StableVITON inference를 바로 실행할 수 없었다.

부족했던 항목은 다음과 같다.

```text
test/image-densepose
test/agnostic-v3.2
test/agnostic-mask
```

### 원인

`VITONHD.ckpt` checkpoint 문제는 아니었다.

checkpoint 3개는 정상적으로 준비되어 있었고, CUDA / PyTorch / dependency import도 통과했다.

실제 문제는 StableVITON이 inference 단계에서 이미 전처리된 DensePose image, agnostic image, agnostic mask를 요구하는데, VITON-HD 기본 test data에는 해당 파일들이 포함되어 있지 않았다는 점이었다.

### 해결 방법

전체 VITON-HD test set을 바로 처리하지 않고, 먼저 `test_pairs.txt` 앞 3개 pair만 사용해 mini smoke dataset을 만들었다.

사용한 mini smoke dataset 경로:

```text
D:\GitHub\StableVITON\DATA\stableviton-smoke
```

mini dataset 구조:

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

처리 과정은 다음과 같다.

1. `prepare_stableviton_smoke_subset.py`로 VITON-HD test data에서 앞 3개 pair만 복사했다.
2. `generate_stableviton_agnostic_from_parse.py`로 image-parse 기반 approximate `agnostic-v3.2`, `agnostic-mask`를 생성했다.
3. WSL Ubuntu 환경에서 Detectron2 DensePose를 설치했다.
4. DensePose `apply_net.py show`를 이용해 3개 person image에 대한 `image-densepose`를 생성했다.
5. 생성된 DensePose output의 파일명을 StableVITON dataset loader가 찾을 수 있도록 `{person_name}.jpg` 형태로 맞췄다.
6. `--unpair` 옵션을 사용해 StableVITON CLI smoke test를 실행했다.

### 추가로 해결한 dependency 문제

StableVITON inference 실행 중 다음 에러가 발생했다.

```text
ModuleNotFoundError: No module named 'cleanfid'
```

아래 명령어로 해결했다.

```powershell
D:\conda-envs\vton\python.exe -m pip install clean-fid
```

또한 다음 경고가 출력되었지만 실행을 중단시키는 문제는 아니었다.

```text
No module named 'triton'
```

### 최종 실행 명령

```powershell
D:\conda-envs\vton\python.exe D:\GitHub\fit-reasoning-vton\scripts\run_stableviton_smoke.py `
  --stableviton-root D:\GitHub\StableVITON `
  --data-root DATA\stableviton-smoke `
  --unpair `
  --execute
```

### 실행 결과

StableVITON inference가 3개 unpaired pair에 대해 정상 완료되었다.

생성된 결과 파일:

```text
samples_smoke/unpair/00891_00_01430_00.jpg
samples_smoke/unpair/03615_00_09933_00.jpg
samples_smoke/unpair/08909_00_02783_00.jpg
```

### 주의사항

이번 전처리는 smoke test 목적의 approximate preprocessing이다.

특히 `agnostic-v3.2`와 `agnostic-mask`는 공식 StableVITON benchmark preprocessing과 완전히 동일하다고 볼 수 없다.

따라서 이번 결과는 정량 평가용 결과가 아니라, StableVITON CLI inference가 로컬 RTX 4080 환경에서 정상 실행되는지 확인하기 위한 smoke test 결과로 기록한다.

단, VITON-HD dataset 및 generated image의 라이선스/저작권 이슈를 피하기 위해 결과 이미지는 GitHub에 업로드하지 않았다.

또한 checkpoint, dataset, generated image는 GitHub에 업로드하지 않는다.

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
