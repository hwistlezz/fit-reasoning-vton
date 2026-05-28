# PC3 StableVITON batch evaluation preflight 로그

## 1. 목적

이 문서는 PC3 학교 컴퓨터에서 StableVITON batch evaluation을 실제로 수행할 수 있는 환경인지 확인하기 위한 preflight 로그이다.

이번 단계에서는 대량 inference를 실행하지 않는다. 실제 실행 전에 repo / branch / Python / CUDA / GPU / StableVITON external repo / checkpoint / batch dry-run 상태를 먼저 확인한다.

결과 이미지, dataset, checkpoint, generated output은 Git에 포함하지 않고 로컬 ignored 경로에만 둔다.

## 2. 실행 환경

| 항목 | 확인 결과 |
| --- | --- |
| OS | Microsoft Windows NT 10.0.26200.0 |
| GPU | NVIDIA GeForce RTX 4080 |
| nvidia-smi 결과 요약 | Driver 591.86, CUDA 13.1, GPU memory 857 MiB / 16376 MiB 사용 중 |
| Python executable | `D:\conda-envs\vton\python.exe` |
| Python version | Python 3.10.20 |
| PyTorch version | 2.0.0+cu117 |
| CUDA available | True |
| CUDA device name | NVIDIA GeForce RTX 4080 |
| conda env | `D:\conda-envs\vton` |
| StableVITON external repo path | `D:\GitHub\StableVITON` |
| StableVITON commit hash | `1d8ef0d8df15ad2aa2a0eb77508f4bb80aa37fa8` |
| fit-reasoning-vton commit hash | `d7a32ca` |

확인한 repo 상태:

```text
branch: experiment/#43/pc3-batch-evaluation-preflight
latest commit: d7a32ca Merge pull request #56 from hwistlezz/feat/#49/fit-confidence-skeleton
working tree: clean
```

## 3. StableVITON preflight 결과

| 항목 | 경로 | 결과 |
| --- | --- | --- |
| StableVITON root | `D:\GitHub\StableVITON` | 존재 |
| inference.py | `D:\GitHub\StableVITON\inference.py` | 존재 |
| checkpoint 1 | `D:\GitHub\StableVITON\ckpts\VITONHD.ckpt` | 존재 |
| checkpoint 2 | `D:\GitHub\StableVITON\ckpts\VITONHD_PBE_pose.ckpt` | 존재 |
| checkpoint 3 | `D:\GitHub\StableVITON\ckpts\VITONHD_VAE_finetuning.ckpt` | 존재 |
| smoke dataset | `D:\GitHub\StableVITON\DATA\stableviton-smoke` | 존재 |

checkpoint와 smoke dataset은 외부 StableVITON repo 아래에만 존재하며, `fit-reasoning-vton` repo에는 포함하지 않는다.

## 4. batch dry-run 결과

실행 명령어:

```powershell
D:\conda-envs\vton\python.exe scripts\run_stableviton_batch_eval.py `
  --stableviton-root D:\GitHub\StableVITON `
  --pair-list docs\experiments\templates\pc3_batch_pairs.example.csv `
  --output-root backend\outputs\pc3_batch_eval `
  --dry-run
```

dry-run 요약:

| 항목 | 결과 |
| --- | --- |
| pair list path | `docs\experiments\templates\pc3_batch_pairs.example.csv` |
| output root | `backend\outputs\pc3_batch_eval` |
| total cases | 3 |
| selected cases | 3 |
| dry-run | true |
| 성공 여부 | 성공 |
| 실패 메시지 | 없음 |

case별 output plan:

| case_id | person_image | cloth_image | mode | expected_note | expected output directory |
| --- | --- | --- | --- | --- | --- |
| case_001 | `person_001.png` | `cloth_001.png` | unpaired | basic smoke pair | `backend\outputs\pc3_batch_eval\case_001` |
| case_002 | `person_002.png` | `cloth_002.png` | unpaired | pose variation | `backend\outputs\pc3_batch_eval\case_002` |
| case_003 | `person_003.png` | `cloth_003.png` | unpaired | fit confidence review candidate | `backend\outputs\pc3_batch_eval\case_003` |

dry-run은 실제 directory나 generated image를 생성하지 않는다.

## 5. 실제 inference 실행 가능 여부

결론: 부분 가능.

GPU, CUDA, Python 환경, StableVITON external repo, checkpoint 3개, smoke dataset은 준비되어 있다. 따라서 StableVITON 실행 환경 자체는 준비된 상태로 볼 수 있다.

다만 이번에 확인한 `scripts/run_stableviton_batch_eval.py`는 dry-run 중심 script이며, 실제 batch inference 실행은 아직 구현하지 않은 상태이다. 또한 example CSV는 실제 dataset image가 아닌 예시 파일명을 사용한다. 실제 소량 batch 실행 전에는 실제 pair list와 output root를 확정하고, 실제 inference command 또는 후속 batch runner 구현을 연결해야 한다.

## 6. 다음 작업

- 소량 batch 실제 실행 command 확정
- 실제 batch evaluation pair list 준비
- smoke dataset 또는 별도 local dataset의 preprocessing artifact 확인
- batch runner의 실제 inference 실행 단계 구현 여부 결정
- inference time / VRAM 기록 방식 확정
- 성공/실패 케이스를 `pc3_stableviton_batch_evaluation_log.md` 형식에 맞춰 기록
- low confidence case와 발표용 성공/실패 샘플 후보 분리

## 7. Git safety 확인

확인할 명령어:

```powershell
git status
git status --ignored -s
git ls-files --others --exclude-standard
```

이번 preflight 작업에서 Git에 포함하면 안 되는 항목:

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

확인 결과:

- `git status`: 새 로그 문서 1개만 추가 대상이며, backend code 변경은 없다.
- `git status --ignored -s`: `backend/outputs/**`, `backend/logs/**`, `backend/outputs/stableviton_raw/**`, `__pycache__/**`가 ignored 상태로 확인되었다.
- `git ls-files --others --exclude-standard`: 출력 없음.
- checkpoint는 Git에 포함하지 않는다.
- dataset은 Git에 포함하지 않는다.
- generated image는 Git에 포함하지 않는다.
- `backend/outputs/**`는 ignored output 경로로 유지한다.
- `backend/logs/**`는 ignored log 경로로 유지한다.
- `stableviton_raw/**`는 Git에 포함하지 않는다.

이번 PR에 포함되는 파일은 이 preflight 로그 문서뿐이다.
