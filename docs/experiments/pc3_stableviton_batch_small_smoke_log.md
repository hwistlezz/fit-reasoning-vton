# PC3 StableVITON 소량 batch smoke test 로그

## 1. 목적

이 문서는 PC3 컴퓨터에서 StableVITON 소량 batch smoke test를 실제 실행하고, 성공/실패 여부, 실행 시간, VRAM 관찰값, 결과 경로를 기록하기 위한 로그이다.

이번 작업은 대량 batch evaluation이 아니다. 이미 준비된 `DATA\stableviton-smoke` 기준 3개 pair만 실행해 StableVITON 실행 가능 여부와 결과 이미지 생성 여부를 확인했다.

결과 이미지는 로컬에서만 확인하며 Git에 포함하지 않는다. 문서에는 결과 이미지 파일명과 로컬 ignored 경로만 기록한다.

## 2. 실행 환경

| 항목 | 확인 결과 |
| --- | --- |
| OS | Microsoft Windows NT 10.0.26200.0 |
| GPU | NVIDIA GeForce RTX 4080 |
| Python | Python 3.10.20 |
| PyTorch | 2.0.0+cu117 |
| CUDA available | True |
| CUDA device | NVIDIA GeForce RTX 4080 |
| StableVITON external repo path | `D:\GitHub\StableVITON` |
| fit-reasoning-vton commit hash | `d7a32ca` |
| StableVITON commit hash | `1d8ef0d8df15ad2aa2a0eb77508f4bb80aa37fa8` |
| checkpoint 상태 | 3개 모두 존재 |

checkpoint 확인 결과:

| checkpoint | 결과 |
| --- | --- |
| `D:\GitHub\StableVITON\ckpts\VITONHD.ckpt` | 존재 |
| `D:\GitHub\StableVITON\ckpts\VITONHD_PBE_pose.ckpt` | 존재 |
| `D:\GitHub\StableVITON\ckpts\VITONHD_VAE_finetuning.ckpt` | 존재 |

실행 전 `nvidia-smi` 요약:

```text
Driver Version: 591.86
CUDA Version: 13.1
GPU memory: 964 MiB / 16376 MiB
GPU utilization: 1%
```

실행 직후 `nvidia-smi` 요약:

```text
GPU memory: 751 MiB / 16376 MiB
GPU utilization: 12%
```

## 3. dry-run 재확인

실행 명령어:

```powershell
D:\conda-envs\vton\python.exe scripts\run_stableviton_batch_eval.py `
  --stableviton-root D:\GitHub\StableVITON `
  --pair-list docs\experiments\templates\pc3_batch_pairs.example.csv `
  --output-root backend\outputs\pc3_batch_eval `
  --dry-run
```

dry-run 결과:

| 항목 | 결과 |
| --- | --- |
| StableVITON root | `D:\GitHub\StableVITON` |
| pair list | `docs\experiments\templates\pc3_batch_pairs.example.csv` |
| output root | `backend\outputs\pc3_batch_eval` |
| total cases | 3 |
| selected cases | 3 |
| dry-run | true |
| 결과 | 성공 |

## 4. 실행 명령어

실제로 실행한 명령어:

```powershell
D:\conda-envs\vton\python.exe scripts\run_stableviton_smoke.py `
  --stableviton-root D:\GitHub\StableVITON `
  --data-root DATA\stableviton-smoke `
  --unpair `
  --execute
```

위 wrapper가 구성한 StableVITON inference 명령어:

```powershell
cd D:\GitHub\StableVITON
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

## 5. 실행 결과

| 항목 | 결과 |
| --- | --- |
| sample pairs | 3 |
| mode | unpaired |
| elapsed seconds | 약 128.5초 |
| elapsed seconds 측정 기준 | shell command wall time. script 자체 출력값은 없음 |
| max VRAM MiB | 미측정 |
| VRAM 기록 기준 | 실행 전/직후 `nvidia-smi`만 확인. peak VRAM은 별도 monitor가 없어 기록하지 않음 |
| success count | 3 |
| failed count | 0 |
| output path | `D:\GitHub\StableVITON\samples_smoke\unpair` |

생성된 결과 파일명:

```text
00891_00_01430_00.jpg
03615_00_09933_00.jpg
08909_00_02783_00.jpg
```

`Get-ChildItem D:\GitHub\StableVITON\samples_smoke\unpair` 확인 결과:

| filename | size bytes |
| --- | ---: |
| `00891_00_01430_00.jpg` | 33131 |
| `03615_00_09933_00.jpg` | 40723 |
| `08909_00_02783_00.jpg` | 49477 |

## 6. failure case

이번 소량 smoke test에서는 실패 케이스 없음.

| 항목 | 결과 |
| --- | --- |
| failed case filename | 해당 없음 |
| error message | 해당 없음 |
| preprocessing artifact 문제 | 발견되지 않음 |
| checkpoint 문제 | 발견되지 않음 |
| CUDA/runtime 문제 | 발견되지 않음 |
| 다음 확인 작업 | peak VRAM 측정용 monitor를 붙인 소량 batch 실행, 실제 batch pair list 준비 |

## 7. fit confidence 관찰 메모

정량 평가는 아직 수행하지 않았다. 아래 내용은 로컬 결과 이미지를 눈으로 확인한 qualitative smoke 관찰값이다. 결과 이미지는 Git에 포함하지 않는다.

| 파일명 | 관찰 메모 |
| --- | --- |
| `00891_00_01430_00.jpg` | 반팔 흰색 상의가 상체에 자연스럽게 배치됨. 어깨선과 몸통 폭은 큰 붕괴 없이 맞아 보임. 왼쪽 소매와 팔 경계는 비교적 자연스럽지만, 상의 밑단과 허리 주변은 실제 fit 판단을 위해 추가 기준이 필요함. |
| `03615_00_09933_00.jpg` | 긴팔 흰색 상의가 팔과 몸통에 일관되게 적용됨. 소매 길이는 손목 근처까지 자연스럽게 내려오며 큰 runtime artifact는 보이지 않음. 흰색 상의와 배경 경계가 가까워 confidence 판단 시 배경 침범 여부를 별도 확인할 필요가 있음. |
| `08909_00_02783_00.jpg` | 검정 레이스/회색 상의 패턴이 보존되어 결과 신뢰도 관찰에 유용함. 어깨와 목 주변 패턴 경계는 비교적 뚜렷하지만, 복잡한 패턴이 팔/몸통 경계에서 왜곡되는지 후속 정량 기준이 필요함. |

confidence 설계에 연결할 관찰 포인트:

- 어깨선 정렬: 3개 결과 모두 큰 어깨 위치 붕괴는 보이지 않음.
- 몸통 폭: 상의 폭이 몸통 범위를 크게 벗어나지는 않음.
- 소매 길이: 반팔/긴팔 케이스 모두 후속 rule 후보로 사용할 수 있음.
- 상의 총장: 허리선 근처에서 실제 fit 판단 기준이 필요함.
- 팔/몸통 왜곡: 이번 3개 결과에서는 명확한 실패는 없음.
- 옷 영역 왜곡: 복잡한 패턴 상의 케이스에서 후속 확인 필요.
- 결과 신뢰도: smoke 기준으로 모두 성공 케이스 후보. 공식 benchmark 수치로 해석하지 않는다.

## 8. Git safety 확인

확인할 명령어:

```powershell
git status
git status --ignored -s
git ls-files --others --exclude-standard
```

Git에 포함하지 않는 항목:

```text
*.ckpt
DATA/**
samples_smoke/**
backend/outputs/**
backend/logs/**
stableviton_raw/**
*.jpg
*.jpeg
*.png
*.webp
```

이번 작업의 Git 포함 대상은 이 문서 1개뿐이다.

확인 결과:

- `git diff --check`: 통과.
- `git status`: 새 로그 문서 1개만 추가 대상이며 backend code 변경은 없다.
- `git status --ignored -s`: `backend/outputs/**`, `backend/logs/**`, `backend/outputs/stableviton_raw/**`, `__pycache__/**`가 ignored 상태로 확인되었다.
- `git ls-files --others --exclude-standard`: 출력 없음.

명시적으로 제외하는 항목:

- checkpoint
- dataset
- generated image
- `backend/outputs/**`
- `backend/logs/**`
- `D:\GitHub\StableVITON\samples_smoke\unpair\*.jpg`
