# StableVITON AIHub layout 준비 script

## 1. 목적

이번 작업은 AIHub LoRA 10k dataset을 StableVITON 학습 포맷에 맞게 변환하기 전에, 필요한 artifact와 train/test layout readiness를 검증하기 위한 준비 script를 추가하는 것이다.

이번 작업은 실제 StableVITON fine-tuning 실행이 아니다. DensePose 포함 patch가 도착했을 때 바로 tiny fine-tuning smoke를 준비할 수 있도록 pair file, split layout, missing artifact summary를 먼저 만든다.

## 2. 현재 dataset 구조

현재 dataset root는 다음과 같다.

```text
backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full
```

현재 확인된 구조는 다음과 같다.

```text
image/            9995
cloth/            9995
worn/             9995
fit/              9995
agnostic-v3.2/    9995
agnostic-mask/    9995
manifest.jsonl    9995 lines
```

현재 없거나 patch 도착 전에는 없을 수 있는 artifact는 다음과 같다.

```text
openpose-json/
image-parse/
cloth-mask/
image-densepose/
```

## 3. StableVITON 학습 layout 준비 이유

StableVITON 원본 `VITONHDDataset`은 manifest 기반 dataset을 직접 읽지 않는다. 원본 코드는 `train_pairs.txt`, `test_pairs.txt`와 `train/`, `test/` 하위 폴더를 기준으로 image, cloth, agnostic, mask, DensePose를 읽는다.

따라서 AIHub manifest 기반 10k dataset을 그대로 fine-tuning script에 연결하기보다, 먼저 StableVITON식 staged layout을 만들고 artifact readiness를 검증해야 한다.

준비 script는 다음 두 모드를 제공한다.

- `dry-run`: 파일 복사 없이 manifest와 artifact 존재 여부만 검사하고 summary를 저장한다.
- `copy`: ready sample만 StableVITON식 train/test layout으로 복사하고 pair file을 생성한다.

## 4. image/person, worn/target 매핑 주의점

현재 AIHub dataset의 의미는 다음과 같다.

- `image/`: person/model image
- `cloth/`: product clothing image
- `worn/`: 해당 의류 착용 정답 후보 image

StableVITON 원본 VITON-HD 학습에서 `image/`는 보통 target 착용 이미지 역할을 한다. 따라서 실제 training smoke 전에는 AIHub `image/`를 StableVITON `image/`로 둘지, AIHub `worn/`을 StableVITON target `image/`로 매핑해야 하는지 반드시 재확인해야 한다.

이번 script는 fine-tuning 매핑을 확정하지 않는다. `copy` mode에서는 현재 source `image/`를 `train|test/image/`로 복사하고, `worn/`은 target 후보로 함께 복사한다. 실제 StableVITON 학습 연결 전에는 이 mapping을 별도 issue에서 확정해야 한다.

## 5. 추가된 script

추가된 script는 다음 파일이다.

```text
backend/training/scripts/prepare_stableviton_layout.py
```

주요 인자:

```text
--data-root
--output-root
--limit
--test-ratio
--seed
--mode dry-run|copy
--require-densepose
--summary-json
```

기본값:

```text
--data-root backend/datasets/lora_pilot_aihub_10k_agnostic_v3_full
--output-root backend/datasets/stableviton_aihub_10k_layout
--limit 100
--test-ratio 0.1
--seed 42
--mode dry-run
--summary-json backend/training/outputs/stableviton_layout_prepare/summary.json
```

## 6. dry-run 명령어

현재 patch 전 dataset에서 실행한 dry-run 명령은 다음과 같다.

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\prepare_stableviton_layout.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full `
  --output-root backend\datasets\stableviton_aihub_10k_layout `
  --limit 100 `
  --mode dry-run `
  --summary-json backend\training\outputs\stableviton_layout_prepare\summary.json
```

dry-run은 파일을 복사하지 않고 readiness summary만 생성한다.

## 7. 현재 missing artifact 결과

현재 dry-run 결과는 다음과 같다.

```text
total_manifest=9995
selected_count=100
train_count=90
test_count=10
ready_count=0
not_ready_count=100
require_densepose=False
copied_count=0
```

missing artifact summary:

```text
image=0
cloth=0
worn=0
fit=0
agnostic-v3.2=0
agnostic-mask=0
openpose-json=100
image-parse=100
cloth-mask=100
image-densepose=100
```

현재 `image-densepose`는 `--require-densepose`를 주지 않았기 때문에 optional missing으로 기록된다. 반면 `openpose-json`, `image-parse`, `cloth-mask`는 required missing으로 잡혀 `ready_count=0`이다.

이 결과는 patch 도착 전 상태에서는 정상이다.

## 8. copy 명령어 예시

patch 도착 후 tiny 100개 layout을 실제로 만들 때의 예시는 다음과 같다.

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\prepare_stableviton_layout.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full `
  --output-root backend\datasets\stableviton_aihub_10k_layout_tiny100 `
  --limit 100 `
  --mode copy `
  --require-densepose `
  --summary-json backend\training\outputs\stableviton_layout_prepare_tiny100\summary.json
```

`copy` mode는 required artifact가 없는 sample을 skip한다. symlink는 Windows 권한 문제를 피하기 위해 사용하지 않고, 실제 파일을 복사한다.

생성 layout:

```text
output-root/
  train/
    image/
    cloth/
    worn/
    fit/
    agnostic-v3.2/
    agnostic-mask/
    openpose-json/
    image-parse/
    cloth-mask/
    image-densepose/
  test/
    image/
    cloth/
    worn/
    fit/
    agnostic-v3.2/
    agnostic-mask/
    openpose-json/
    image-parse/
    cloth-mask/
    image-densepose/
  train_pairs.txt
  test_pairs.txt
  layout_summary.json
```

## 9. patch 도착 후 실행할 명령어

patch 도착 직후에는 먼저 dry-run으로 full readiness를 확인한다.

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\prepare_stableviton_layout.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full `
  --output-root backend\datasets\stableviton_aihub_10k_layout `
  --limit 9995 `
  --mode dry-run `
  --require-densepose `
  --summary-json backend\training\outputs\stableviton_layout_prepare_full\summary.json
```

full readiness에서 `missing_counts`가 0인지 확인한 뒤 tiny copy를 실행한다.

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\prepare_stableviton_layout.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_agnostic_v3_full `
  --output-root backend\datasets\stableviton_aihub_10k_layout_tiny10 `
  --limit 10 `
  --mode copy `
  --require-densepose `
  --summary-json backend\training\outputs\stableviton_layout_prepare_tiny10\summary.json
```

이후 tiny 10개 layout으로 `VITONHDDataset` item load smoke를 먼저 확인하고, 그 다음 StableVITON training tiny smoke로 넘어간다.

## 10. train_pairs.txt / test_pairs.txt 생성 방식

pair file은 우선 다음 형식으로 생성한다.

```text
person_image cloth_image
```

예:

```text
EP00000001.jpg EP00000001.jpg
```

`--test-ratio`와 `--seed`를 사용해 선택된 pair를 train/test로 나눈다. 기본값 `--limit 100 --test-ratio 0.1 --seed 42`에서는 planned split 기준 train 90개, test 10개가 된다.

StableVITON 원본 `dataset.py`는 pair file의 첫 번째 filename을 `image`, `agnostic-v3.2`, `agnostic-mask`, `image-densepose` 경로에 같이 사용한다. 이를 맞추기 위해 copy mode는 StableVITON 호환 filename을 우선 사용한다.

```text
agnostic-mask/{pair_id}_mask.png
cloth-mask/{pair_id}.jpg
image-densepose/{pair_id}.jpg
```

단, `cloth-mask` 원본 artifact는 `cloth-mask/{pair_id}.png` 후보로 검사한다. 실제 StableVITON 원본 코드가 cloth filename과 동일한 mask filename을 요구하므로, patch 도착 후 mask 확장자와 OpenCV load 여부는 별도 smoke에서 확인해야 한다.

## 11. Git safety

이번 PR에 포함하면 안 되는 항목은 다음과 같다.

```text
backend/datasets/**
backend/training/outputs/**
backend/outputs/**
backend/logs/**
DATA/**
samples_smoke/**
stableviton_raw/**
*.jpg
*.jpeg
*.png
*.webp
*.ckpt
*.pth
*.pt
*.safetensors
*.zip
*.7z
```

이번 작업의 Git 포함 대상은 다음 두 파일이다.

```text
backend/training/scripts/prepare_stableviton_layout.py
docs/experiments/stableviton_aihub_layout_prepare.md
```

dry-run summary는 아래 ignored output에 생성되며 Git에 포함하지 않는다.

```text
backend/training/outputs/stableviton_layout_prepare/summary.json
```

## 12. 다음 단계

1. DensePose 포함 artifact patch 수신
2. full dry-run readiness 재실행
3. `cloth-mask`, `image-densepose`, `agnostic-mask` filename rule 확인
4. tiny 10/100 copy layout 생성
5. StableVITON `VITONHDDataset` item load smoke
6. image/person과 worn/target mapping 확정
7. StableVITON tiny fine-tuning 또는 forward/backward smoke 실행
