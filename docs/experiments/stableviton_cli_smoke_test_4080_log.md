# StableVITON CLI Smoke Test Log - RTX 4080

## 목적

PC1에서 StableVITON을 FastAPI backend에 연결하기 전, 외부 StableVITON repo가 단독 CLI inference를 수행할 수 있는지 확인한다.

## 작업 범위

- StableVITON 외부 repo clone 확인
- conda environment 확인
- CUDA / PyTorch 확인
- 주요 dependency import 확인
- checkpoint 위치 확인
- VITON-HD test data 구조 확인
- inference command 확인
- 성공 또는 실패 로그 기록

## 현재 상태

- 외부 repo clone: 완료
- conda env 생성: 완료
- CUDA 확인: 완료
- dependency import 확인: 완료
- checkpoint 다운로드: 진행 중
- VITON-HD test data 준비: 미완료
- inference 실행: 미실행

## 환경 정보

| 항목 | 값 |
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

## 확인된 경고

### pkg_resources deprecation warning

`pytorch_lightning==1.5.0`에서 `pkg_resources` deprecation warning이 출력된다.

현재는 import 실패가 아니므로 smoke test 진행을 막지 않는다.

### Triton warning

Windows 환경에서 `triton` 관련 경고가 출력된다.

현재는 `diffusers` import 실패가 아니므로 smoke test 진행을 막지 않는다.

## checkpoint 준비 상태

아래 파일을 `D:\GitHub\StableVITON\ckpts`에 로컬로 배치한다.

- `VITONHD.ckpt`
- `VITONHD_PBE_pose.ckpt`
- `VITONHD_VAE_finetuning.ckpt`

checkpoint는 크기가 매우 크므로 GitHub에 절대 업로드하지 않는다.

현재 checkpoint 다운로드가 진행 중이며, 아직 위 세 파일은 준비되지 않았다.

## VITON-HD test data 구조

StableVITON inference에는 아래 구조가 필요하다.

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

현재 VITON-HD test data는 아직 준비되지 않았다.

## 예정 inference command

checkpoint와 test data 준비 후 아래 형식으로 실행한다.

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

## 검증 스크립트

checkpoint 다운로드 전에도 외부 repo 준비 상태를 확인할 수 있도록 우리 repo에서 아래 명령을 실행한다.

```powershell
python .\scripts\verify_external_stableviton.py --stableviton-root D:\GitHub\StableVITON
```

dependency import까지 확인하려면 아래 명령을 실행한다.

```powershell
D:\conda-envs\vton\python.exe .\scripts\verify_external_stableviton.py --stableviton-root D:\GitHub\StableVITON --check-imports
```

## 주의사항

- StableVITON 외부 repo는 우리 repo 안에 복사하지 않는다.
- checkpoint는 Git에 포함하지 않는다.
- dataset은 Git에 포함하지 않는다.
- generated image는 Git에 포함하지 않는다.
- 실행 시간과 VRAM 기록은 개발 환경 smoke log이며 공식 benchmark가 아니다.
- inference 성공이나 실패는 실제 실행 후에만 기록한다.

## 다음 작업

- checkpoint 다운로드 완료 확인
- VITON-HD test sample 구조 준비
- `scripts/verify_external_stableviton.py` 실행
- StableVITON CLI inference 1차 실행
- 성공/실패 로그 기록
