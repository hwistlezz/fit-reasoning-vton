# AIHub Indexing Script 사용법

## 1. 목적

AIHub annotation JSON에서 item index와 pair manifest를 생성하기 위한 script 사용법을 정리한다.

이 script의 산출물은 PC2가 raw AIHub annotation을 분석해 PC3/backend 쪽으로 전달할 processed subset 후보를 만들기 위한 중간 결과다.

## 2. 현재 범위

이번 script는 skeleton 단계이며, `docs/examples`의 작은 예시 JSON으로 검증한다.

실제 AIHub 전체 데이터 실행은 PC2에서 진행한다. 이 저장소에는 실제 AIHub raw JSON, 원본 이미지, generated output, checkpoint를 포함하지 않는다.

## 3. inspect script 사용법

`scripts/inspect_aihub_raw.py`는 JSON 파일 또는 JSON 디렉터리를 탐색하고, wearing annotation인지 pair annotation인지 구조를 요약한다.

```powershell
python scripts\inspect_aihub_raw.py `
  --input docs\examples `
  --output backend\datasets\processed\index\raw_structure_report.example.json
```

필요하면 `--limit`으로 앞 N개 JSON만 확인할 수 있다.

```powershell
python scripts\inspect_aihub_raw.py `
  --input docs\examples `
  --output backend\datasets\processed\index\raw_structure_report.example.json `
  --limit 10
```

## 4. index script 사용법

`scripts/build_aihub_index.py`는 wearing annotation에서 `items.csv`를 만들고, pair annotation에서 `pairs.csv`를 만든다.

```powershell
python scripts\build_aihub_index.py `
  --raw-root docs\examples `
  --out-items backend\datasets\processed\index\aihub_items.example.csv `
  --out-pairs backend\datasets\processed\index\aihub_pairs.example.csv `
  --save-report backend\datasets\processed\index\aihub_index_report.example.json
```

필요하면 `--limit`으로 앞 N개 JSON만 처리할 수 있다.

## 5. 생성 결과

생성 결과는 아래 ignored 경로에 저장한다.

```text
backend/datasets/processed/index/
```

예상 산출물은 다음과 같다.

- `aihub_items.example.csv`
- `aihub_pairs.example.csv`
- `aihub_index_report.example.json`
- `raw_structure_report.example.json`

위 파일들은 generated output이므로 Git에 올리지 않는다.

## 6. PC2 실제 실행 시 주의사항

- raw root는 AIHub 압축 해제 경로를 지정한다.
- 원본 이미지와 원본 JSON은 Git에 올리지 않는다.
- 생성된 `items.csv`, `pairs.csv`, `report.json`도 기본적으로 Git에 올리지 않는다.
- 필요한 경우 docs에는 schema 또는 요약만 기록한다.
- 실제 AIHub 전체 데이터 구조가 예시와 다를 수 있으므로, 처음에는 `--limit`으로 소량 구조를 확인한 뒤 전체 실행한다.
- JSON parse 실패 파일은 script가 중단되지 않고 report의 `errors`에 기록된다.
