# PC3 LoRA 10k Dataset Smoke Test 및 Storage Cleanup 기록

## 1. 목적

PC2에서 전달한 AIHub LoRA 10k pilot dataset split archive를 PC3에서 압축 해제하고, #72에서 구현한 `AihubLoraPilotDataset` 및 `smoke_test_lora_dataset.py`로 dataset loader smoke test를 수행했다.

이번 작업은 실제 LoRA 학습이 아니라, 10k pilot dataset의 압축 무결성, manifest/file layout, 이미지 로드, fit JSON parse, backend fit analyzer loader 호환성, 그리고 smoke 성공 후 local archive cleanup을 확인하는 단계다.

## 2. 실행 환경

- Repo: `D:\GitHub\fit-reasoning-vton`
- Base branch: `dev`
- Work branch: `experiment/#74/pc3-lora-10k-smoke-cleanup`
- 7-Zip: `C:\Program Files\7-Zip\7z.exe`, 26.01 x64
- Python: `C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe`

## 3. 작업 전 D드라이브 용량

`System.IO.DriveInfo` 기준:

```text
TotalGB=1,863.000
FreeGB=498.062
UsedGB=1,364.938
```

## 4. Split Archive 목록 및 용량

확인 명령:

```powershell
Get-ChildItem backend\datasets\lora_pilot_aihub_10k_full_split.7z.* |
  Sort-Object Name |
  Select-Object Name, @{Name='SizeGB';Expression={[math]::Round($_.Length/1GB,3)}}, Length
```

결과:

| 파일 | 크기 |
| --- | ---: |
| `lora_pilot_aihub_10k_full_split.7z.001` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.002` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.003` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.004` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.005` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.006` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.007` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.008` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.009` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.010` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.011` | 5.000 GB |
| `lora_pilot_aihub_10k_full_split.7z.012` | 1.836 GB |

합계:

```text
parts=12
TotalArchiveGB=56.836
TotalArchiveBytes=61026765263
```

## 5. 7z Test 및 Split Archive 압축 해제 결과

별도 `7z t`는 장시간 실행되어 현재 shell 제한 내 완료 output을 얻지 못했다. 이후 `7z x` 압축 해제 단계에서 전체 split archive를 읽었고, 7-Zip output에 `Everything is Ok`가 출력됐다.

실행 명령:

```powershell
& 'C:\Program Files\7-Zip\7z.exe' x `
  backend\datasets\lora_pilot_aihub_10k_full_split.7z.001 `
  -obackend\datasets `
  -y
```

결과:

```text
Volumes = 12
Total Physical Size = 61026765263
Everything is Ok
Size:       65590737643
Compressed: 61026765263
```

archive 내부 경로가 `backend/datasets/lora_pilot_aihub_10k_full.zip` 형태라 최초 압축 해제 위치는 다음과 같았다.

```text
backend/datasets/backend/datasets/lora_pilot_aihub_10k_full.zip
```

요구 경로에 맞추기 위해 동일 drive 내에서 단일 zip 파일만 이동했다.

```text
backend/datasets/lora_pilot_aihub_10k_full.zip
```

내부 zip 크기:

```text
SizeGB=61.086
Length=65590737643
```

압축 해제 후 D드라이브 용량:

```text
FreeGB=437.374
UsedGB=1,425.626
```

## 6. 내부 Zip Test 결과

실행 명령:

```powershell
python -c "import zipfile; from pathlib import Path; path=Path('backend/datasets/lora_pilot_aihub_10k_full.zip'); z=zipfile.ZipFile(path); bad=z.testzip(); z.close(); print(f'bad_file={bad}')"
```

결과:

```text
bad_file=None
```

## 7. 내부 Zip 압축 해제 결과

zip 내부 최상위 entry:

```text
cloth/
fit/
image/
worn/
manifest.jsonl
```

실행 명령:

```powershell
python -c "import zipfile; from pathlib import Path; src=Path('backend/datasets/lora_pilot_aihub_10k_full.zip'); dst=Path('backend/datasets/lora_pilot_aihub_10k_full'); dst.mkdir(parents=True, exist_ok=False); z=zipfile.ZipFile(src); z.extractall(dst); z.close(); print(f'extracted_to={dst.as_posix()}')"
```

결과:

```text
extracted_to=backend/datasets/lora_pilot_aihub_10k_full
```

압축 해제 파일 크기:

```text
ExtractedFiles=39997
ExtractedGB=62.522
ExtractedBytes=67132326740
```

압축 해제 후 D드라이브 용량:

```text
FreeGB=374.321
UsedGB=1,488.679
```

## 8. 원본 데이터 개수 확인

확인 명령:

```powershell
python -c "from pathlib import Path; root=Path('backend/datasets/lora_pilot_aihub_10k_full'); [print(d,len(list((root/d).glob('*')))) for d in ['image','cloth','worn','fit']]; print('manifest lines=',len([x for x in (root/'manifest.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]))"
```

결과:

```text
image 9999
cloth 9999
worn 9999
fit 9999
manifest lines= 9999
```

명목상 10k archive지만 실제 manifest/file 기준 sample 수는 `9999`개다.

## 9. 원본 9999 Smoke Test 결과

실행 명령:

```powershell
python backend\training\scripts\smoke_test_lora_dataset.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_full `
  --limit 10000 `
  --sample-count 16 `
  --contact-sheet backend\training\outputs\lora_pilot_10k\contact_sheet.jpg `
  --summary-json backend\training\outputs\lora_pilot_10k\dataset_smoke_summary.json `
  --check-backend-loader
```

결과:

```json
{
  "data_root": "backend/datasets/lora_pilot_aihub_10k_full",
  "manifest_count": 9999,
  "checked_count": 9999,
  "missing_image": 0,
  "missing_cloth": 0,
  "missing_worn": 0,
  "missing_fit": 0,
  "image_load_errors": 4,
  "fit_json_errors": 0,
  "backend_loader_errors": 0,
  "metadata_errors": 0,
  "contact_sheet_errors": 0,
  "backend_loader_checked": true,
  "seed": 42,
  "sample_contact_sheet": "backend/training/outputs/lora_pilot_10k/contact_sheet.jpg"
}
```

원본 9999 smoke는 `image_load_errors=4`로 실패했다.

## 10. Known-bad 4개 진단

실패 파일:

```text
backend/datasets/lora_pilot_aihub_10k_full/image/EP00003620.jpg    OSError: image file is truncated (8 bytes not processed)
backend/datasets/lora_pilot_aihub_10k_full/image/EP00003937.jpg    OSError: image file is truncated (40 bytes not processed)
backend/datasets/lora_pilot_aihub_10k_full/cloth/EP00005080.jpg    OSError: image file is truncated (12 bytes not processed)
backend/datasets/lora_pilot_aihub_10k_full/worn/EP00007279.jpg     UnidentifiedImageError: cannot identify image file
```

추가 확인:

- `LOAD_TRUNCATED_IMAGES=True` 설정 시 truncated 3개는 PIL로 로드 가능하다.
- `worn/EP00007279.jpg`는 JPEG/PNG/WEBP/JFIF/Exif signature가 없다.
- `worn/EP00007279.jpg`는 zip 내부 entry와 추출본의 SHA-256이 동일하므로, 추출 중 손상된 것이 아니라 archive 내부 payload 자체가 이미지로 식별되지 않는다.

`worn/EP00007279.jpg` zip/extracted 비교:

```text
zip_entry_size=825450
zip_entry_crc=0x68fca967
zip_entry_sha256=5971f87f0468e308c57f2273ed8c47834b08d2a9ba45508576601f630aaf027d
extracted_size=825450
extracted_sha256=5971f87f0468e308c57f2273ed8c47834b08d2a9ba45508576601f630aaf027d
same_bytes=True
```

Raw AIHub archive 원본도 확인했다. `EP00007279`는 `Pair.json`의 7,279번째 row에서 다음 원본 mapping으로 생성된다.

```json
{
  "from": "/원천데이터/제품/드레스/KSOP6648M000P00A2.jpg",
  "to": "/원천데이터/모델/KSMD0000M487P02A2.jpg",
  "result": "/원천데이터/제품 착용/드레스/KSOP6648M487P02A2.jpg"
}
```

원본 raw zip entry도 추출본과 동일하게 이미지로 식별되지 않는다.

```text
zip=backend/datasets/raw/.../Training/01.원천데이터/TS_제품 착용_드레스_1.zip
entry=/KSOP6648M487P02A2.jpg
size=825450
sha256=5971f87f0468e308c57f2273ed8c47834b08d2a9ba45508576601f630aaf027d
head=62 3a 9a 56 fe f8 1d fa 0f 4a 69 f3 07 5f c7 fc
strict=UnidentifiedImageError
tolerant=UnidentifiedImageError
```

## 11. Filtered Manifest 생성

사용자 지시에 따라 원본 manifest를 local-only backup으로 보존하고, known-bad 4개를 제외한 filtered manifest로 교체했다.

```text
backup=backend/datasets/lora_pilot_aihub_10k_full/manifest.raw_9999.jsonl
filtered=backend/datasets/lora_pilot_aihub_10k_full/manifest.jsonl
```

제외한 `pair_id`:

```text
EP00003620
EP00003937
EP00005080
EP00007279
```

검증 결과:

```text
raw lines=9999
filtered manifest lines=9995
```

`manifest.raw_9999.jsonl`과 filtered `manifest.jsonl`은 dataset-local artifact이며 Git에 포함하지 않는다.

## 12. Filtered 9995 Smoke Test 결과

실행 명령:

```powershell
python backend\training\scripts\smoke_test_lora_dataset.py `
  --data-root backend\datasets\lora_pilot_aihub_10k_full `
  --limit 9995 `
  --sample-count 16 `
  --contact-sheet backend\training\outputs\lora_pilot_10k_filtered\contact_sheet.jpg `
  --summary-json backend\training\outputs\lora_pilot_10k_filtered\dataset_smoke_summary.json `
  --check-backend-loader
```

결과:

```json
{
  "data_root": "backend/datasets/lora_pilot_aihub_10k_full",
  "manifest_count": 9995,
  "checked_count": 9995,
  "missing_image": 0,
  "missing_cloth": 0,
  "missing_worn": 0,
  "missing_fit": 0,
  "image_load_errors": 0,
  "fit_json_errors": 0,
  "backend_loader_errors": 0,
  "metadata_errors": 0,
  "contact_sheet_errors": 0,
  "backend_loader_checked": true,
  "seed": 42,
  "sample_contact_sheet": "backend/training/outputs/lora_pilot_10k_filtered/contact_sheet.jpg"
}
```

Filtered 9995 smoke test는 성공했다.

## 13. Contact Sheet 및 Summary JSON 생성 여부

Filtered smoke test 결과물:

```text
backend/training/outputs/lora_pilot_10k_filtered/contact_sheet.jpg
backend/training/outputs/lora_pilot_10k_filtered/dataset_smoke_summary.json
```

이 파일들은 generated output이며 Git에 포함하지 않는다.

## 14. Backend Loader 호환 결과

`--check-backend-loader` 옵션을 켜고 filtered manifest 9,995개에 대해 확인했다.

```text
backend_loader_errors=0
```

즉 filtered set의 PC2 compact fit JSON은 backend fit analyzer loader와 호환된다.

## 15. Cleanup 수행 여부

Filtered smoke 성공과 generated output ignore 상태를 확인한 뒤 cleanup을 수행했다.

Cleanup 전 D드라이브 용량:

```text
CleanupBeforeFreeGB=337.865
CleanupBeforeUsedGB=1,525.135
```

삭제한 파일:

```text
backend/datasets/lora_pilot_aihub_10k_full_split.7z.001
backend/datasets/lora_pilot_aihub_10k_full_split.7z.002
backend/datasets/lora_pilot_aihub_10k_full_split.7z.003
backend/datasets/lora_pilot_aihub_10k_full_split.7z.004
backend/datasets/lora_pilot_aihub_10k_full_split.7z.005
backend/datasets/lora_pilot_aihub_10k_full_split.7z.006
backend/datasets/lora_pilot_aihub_10k_full_split.7z.007
backend/datasets/lora_pilot_aihub_10k_full_split.7z.008
backend/datasets/lora_pilot_aihub_10k_full_split.7z.009
backend/datasets/lora_pilot_aihub_10k_full_split.7z.010
backend/datasets/lora_pilot_aihub_10k_full_split.7z.011
backend/datasets/lora_pilot_aihub_10k_full_split.7z.012
backend/datasets/lora_pilot_aihub_10k_full.zip
```

삭제 후 확인:

```text
split archive count=0
internal zip exists=False
backend/datasets/lora_pilot_aihub_10k_full exists=True
backend/datasets/lora_pilot_aihub_1k exists=True
```

Cleanup 후 D드라이브 용량:

```text
CleanupAfterFreeGB=455.786
CleanupAfterUsedGB=1,407.214
```

## 16. Zalando Archive 후보 조사

`zalando`, `zalando-hd`, `zalando_hd` 이름을 포함하는 archive 후보를 조사했으나, 명확한 archive 파일은 발견하지 못했다.

삭제한 zalando 관련 파일은 없다.

## 17. Git Safety 확인

Dataset, archive, generated output은 Git에 포함하지 않는다.

추가 safety 조치:

- split archive 확장자인 `*.7z.*`가 기존 `.gitignore`의 `*.7z`에 걸리지 않아 ignore 패턴을 보강했다.
- 동일하게 split zip 가능성을 막기 위해 `*.zip.*`도 추가했다.

확인 기준:

```text
backend/datasets/lora_pilot_aihub_10k_full/    ignored
backend/training/outputs/lora_pilot_10k_filtered/    ignored
backend/datasets/lora_pilot_aihub_10k_full_split.7z.*    deleted
backend/datasets/lora_pilot_aihub_10k_full.zip    deleted
```

PR에는 문서와 Git safety ignore 보강만 포함한다.

## 18. 다음 단계

1. Filtered 9,995개 기준 LoRA training loader 연결을 준비한다.
2. PC2에는 known-bad 4개 pair를 공유해 원본 데이터 품질 이슈를 추적한다.
3. 실제 LoRA 학습은 별도 issue에서 수행한다.
