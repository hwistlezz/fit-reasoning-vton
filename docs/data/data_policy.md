# Dataset Policy

## 목적

이 문서는 PC2에서 수집하거나 생성하는 이미지, CSV, preprocessing 결과, 로그, checkpoint 파일이 GitHub에 올라가지 않도록 관리 기준을 정리한다.

## 원칙

실제 데이터는 GitHub에 커밋하지 않는다.

GitHub에는 다음만 포함한다.

- 폴더 구조 유지를 위한 `.gitkeep`
- 형식 공유를 위한 `*.example.csv`
- 데이터 수집/관리 문서
- 데이터 다운로드 또는 정리용 코드

## Git에 올리지 않는 것

- 실제 이미지 파일
  - `.jpg`
  - `.jpeg`
  - `.png`
  - `.webp`
- 실제 데이터 CSV
  - `urls.csv`
  - `sources.csv`
  - `labels.csv`
  - `test_cases.csv`
  - `features.csv`
  - `features_test.csv`
- preprocessing 결과
  - `backend/datasets/processed/**`
- raw dataset
  - `backend/datasets/raw/**`
  - `backend/datasets/raw_test/**`
  - `backend/datasets/test_pairs/**`
  - `backend/datasets/lora_oversized/images/**`
- 로그
  - `backend/logs/**`
- 출력 결과
  - `backend/outputs/**`
- 모델 및 checkpoint
  - `backend/models/**`
  - `backend/checkpoints/**`

## Git에 올릴 수 있는 것

- `*.example.csv`
- `docs/data/*.md`
- `backend/scripts/*.py`
- `.gitkeep`

## 확인 방법

작업 전후로 반드시 아래 명령어를 확인한다.

```bash
git status