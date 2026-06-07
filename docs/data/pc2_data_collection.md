# PC2 Data Collection Guide

## 목적

PC2에서 MVP에 필요한 raw image 후보를 수집하고, preprocessing / StableVITON demo pair / fit analyzer feature / low confidence case 용도로 분류한다.

## GitHub에 올리는 파일

- `*.example.csv`
- `.gitkeep`
- 데이터 수집 문서
- 데이터 다운로드/정리 스크립트

## GitHub에 올리지 않는 파일

- 실제 이미지
- 실제 `urls.csv`
- 실제 `sources.csv`
- 실제 `labels.csv`
- 실제 `test_cases.csv`
- preprocessing 결과
- log/output/checkpoint

## 주요 경로

| 목적 | 로컬 저장 경로 |
|---|---|
| 사람 이미지 후보 | `backend/datasets/raw/preprocess_people/` |
| 오버핏 후보 | `backend/datasets/raw/oversized_candidates/` |
| low confidence case | `backend/datasets/raw/low_confidence/` |
| demo person | `backend/datasets/raw/demo_person/` |
| demo cloth | `backend/datasets/raw/demo_cloth/` |
| StableVITON test pair | `backend/datasets/test_pairs/` |
| fit analyzer feature 후보 | `backend/datasets/raw/fit_feature_candidates/` |

## 권장 흐름

1. 노트북에서 후보 이미지 URL을 조사한다.
2. PC2 로컬에 `backend/datasets/urls/urls.csv`를 만든다.
3. PC2에서 `backend/scripts/download_raw_images.py`를 실행한다.
4. 실제 다운로드된 이미지만 `sources.csv`, `labels.csv`, `test_cases.csv`에 기록한다.
5. `git status`로 실제 이미지와 실제 CSV가 Git에 잡히지 않는지 확인한다.
