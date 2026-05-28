# PC3 StableVITON batch dry-run script 사용 메모

## 목적

`scripts/run_stableviton_batch_eval.py`는 PC3 StableVITON batch evaluation을 실행하기 전에 pair list CSV와 output 계획을 검증하기 위한 dry-run script입니다.

이번 script는 실제 StableVITON batch inference를 실행하지 않습니다. 실제 inference 실행은 후속 PR에서 구현합니다.

## 입력 CSV 형식

필수 컬럼:

- `case_id`
- `person_image`
- `cloth_image`

선택 컬럼:

- `mode`
- `expected_note`

예시:

```csv
case_id,person_image,cloth_image,mode,expected_note
case_001,person_001.png,cloth_001.png,unpaired,basic smoke pair
case_002,person_002.png,cloth_002.png,unpaired,pose variation
```

`mode`는 `paired` 또는 `unpaired`만 허용합니다. CSV row에 `mode`가 없거나 비어 있으면 command line의 `--mode` 기본값을 사용합니다.

## Dry-run 실행 예시

PR #54가 merge된 뒤에는 아래 example CSV를 사용할 수 있습니다.

```powershell
python scripts\run_stableviton_batch_eval.py `
  --stableviton-root D:\GitHub\StableVITON `
  --pair-list docs\experiments\templates\pc3_batch_pairs.example.csv `
  --output-root backend\outputs\pc3_batch_eval `
  --dry-run
```

현재 `dev`에 `docs\experiments\templates\pc3_batch_pairs.example.csv`가 없다면, 로컬 ignored 경로 또는 임시 경로에 같은 형식의 CSV를 만들어 dry-run만 검증합니다.

## 현재 한계

- 실제 StableVITON inference는 실행하지 않습니다.
- `--dry-run`이 없으면 안내 메시지를 출력하고 non-zero exit code로 종료합니다.
- `--output-root`는 계획 출력에만 사용하며, dry-run에서는 directory를 생성하지 않습니다.

## Git safety

아래 항목은 Git에 포함하지 않습니다.

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

이번 script는 source file만 추가하며, dataset image, generated image, checkpoint는 생성하거나 커밋하지 않습니다.
