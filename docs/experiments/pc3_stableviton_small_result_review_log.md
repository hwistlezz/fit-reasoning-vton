# PC3 StableVITON 소량 결과 리뷰 로그

## 1. 목적

이 문서는 StableVITON 소량 smoke 결과 이미지 3개를 로컬에서 확인하고, fit confidence score / fit explanation / annotation hotspot 설계에 필요한 관찰 기준을 정리하기 위한 결과 리뷰 로그이다.

실제 결과 이미지는 Git에 포함하지 않는다. 이 문서에는 결과 파일명, 로컬 output path, 관찰 메모만 기록한다.

## 2. 입력 및 결과 요약

| case_id | result_filename | status | local_output_path | review_status |
| --- | --- | --- | --- | --- |
| case_001 | `00891_00_01430_00.jpg` | success | `D:\GitHub\StableVITON\samples_smoke\unpair\00891_00_01430_00.jpg` | reviewed |
| case_002 | `03615_00_09933_00.jpg` | success | `D:\GitHub\StableVITON\samples_smoke\unpair\03615_00_09933_00.jpg` | reviewed |
| case_003 | `08909_00_02783_00.jpg` | success | `D:\GitHub\StableVITON\samples_smoke\unpair\08909_00_02783_00.jpg` | reviewed |

확인한 output root:

```text
D:\GitHub\StableVITON\samples_smoke\unpair
```

## 3. case별 관찰 로그

confidence 후보:

- `high`
- `medium`
- `low`
- `unknown`

failure_type 후보:

- `none`
- `SHOULDER_MISALIGNMENT`
- `TORSO_WIDTH_DISTORTION`
- `SLEEVE_LENGTH_UNCLEAR`
- `GARMENT_LENGTH_UNCLEAR`
- `ARM_OCCLUSION`
- `CLOTH_REGION_DISTORTION`
- `BACKGROUND_OR_SKIN_LEAK`
- `LOW_QUALITY_RESULT`

| case_id | 어깨선 정렬 | 몸통 폭 | 소매 길이 | 상의 총장 | 팔/몸통 왜곡 | 옷 영역 왜곡 | 배경/피부 침범 | 전체 신뢰도 메모 | confidence 후보 | failure_type 후보 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| case_001 | 반팔 상의의 어깨선이 실제 어깨 위치와 크게 어긋나지 않음 | 상의 폭이 몸통 범위 안에서 자연스럽게 보임 | 반팔 소매 끝 위치가 팔 위치와 대체로 맞음 | 허리선 근처에서 자연스럽게 마감되지만 정량 기준은 아직 없음 | 팔과 몸통 경계에 큰 붕괴 없음 | 흰색 상의 영역이 비교적 안정적임 | 배경/피부 침범은 눈에 띄지 않음 | smoke 기준 성공 케이스로 사용 가능 | high | none |
| case_002 | 긴팔 상의의 어깨선이 무너지지 않음 | 몸통 폭이 자연스럽게 유지됨 | 소매가 손목 근처까지 이어져 팔 위치와 대체로 맞음 | 상의가 바지 안으로 들어간 형태라 총장 판단은 제한적임 | 팔과 몸통 경계가 비교적 안정적임 | 흰색 상의와 밝은 배경 경계가 일부 애매함 | 뚜렷한 침범은 없지만 흰색 배경 때문에 경계 확인이 어려움 | 전체 착장은 안정적이나 배경/상의 경계는 주의 메모 필요 | medium | BACKGROUND_OR_SKIN_LEAK |
| case_003 | 어깨와 목 주변 레이스 패턴 경계가 비교적 유지됨 | 몸통 폭은 자연스럽게 보임 | 긴팔 소매 길이가 팔 위치와 대체로 맞음 | 허리선 위쪽에서 상의가 자연스럽게 들어간 형태로 보임 | 팔/몸통의 큰 구조 붕괴는 없음 | 복잡한 레이스 패턴은 일부 경계 왜곡 가능성이 있어 후속 확인 필요 | 뚜렷한 배경/피부 침범은 보이지 않음 | 패턴이 복잡해 confidence rule 검증 후보로 적합함 | medium | CLOTH_REGION_DISTORTION |

## 4. fit confidence rule 초안

### high confidence 후보

- 어깨선이 실제 어깨 위치에서 크게 무너지지 않음.
- 몸통 폭이 사람의 상체 폭과 자연스럽게 맞음.
- 소매 끝 위치와 팔 위치가 크게 어긋나지 않음.
- 옷 영역이 배경이나 피부 영역을 과도하게 침범하지 않음.
- 사용자가 결과 이미지를 보고 fit 판단에 참고할 수 있음.

### medium confidence 후보

- 전체 착장은 가능하지만 소매, 상의 길이, 패턴 왜곡, 배경 경계 중 일부가 애매함.
- fit explanation에서 주의 문구를 줄 필요가 있음.
- 결과 이미지는 사용할 수 있지만 annotation hotspot 또는 warning으로 불확실한 부위를 표시하는 것이 좋음.

### low confidence 후보

- 어깨선, 몸통, 팔 영역 중 하나 이상이 크게 무너짐.
- 옷 영역이 사람 또는 배경과 심하게 섞임.
- 소매 길이 또는 상의 총장을 판단하기 어려움.
- 사용자가 fit 판단에 쓰기 어려운 결과임.

## 5. annotation hotspot 후보

이번 작업에서는 실제 annotation hotspot을 생성하지 않는다. 다만 추후 analyzer가 annotation을 만들 수 있는 후보 부위와 조건을 정리한다.

| part | annotation 생성 후보 조건 |
| --- | --- |
| `shoulder` | 어깨선이 실제 어깨 위치보다 크게 위/아래로 이동하거나 좌우 정렬이 무너진 경우 |
| `torso` | 몸통 폭이 과도하게 넓거나 좁게 합성되어 의류 fit 판단을 흐리는 경우 |
| `sleeve` | 소매 끝 위치가 팔 위치와 맞지 않거나 팔 영역을 비정상적으로 덮는 경우 |
| `length` | 상의 밑단이 비정상적으로 길거나 짧아 총장 판단이 어려운 경우 |
| `cloth_region` | 옷 영역이 배경이나 피부 영역을 침범하거나 복잡한 패턴이 크게 왜곡된 경우 |

예상 annotation schema 후보:

```json
{
  "part": "shoulder",
  "x": 50,
  "y": 30,
  "severity": "medium",
  "message": "어깨선 정렬 신뢰도가 낮습니다."
}
```

## 6. 다음 작업

1. 더 많은 pair로 batch evaluation 확장
2. low confidence 후보 수집
3. failure_type 기준 확정
4. confidence score skeleton의 score / level 기준 조정
5. annotation hotspot schema 확장

## 7. Git safety 확인

확인할 명령어:

```powershell
git status
git status --ignored -s
git ls-files --others --exclude-standard
```

Git에 포함하지 않는 항목:

- 결과 이미지
- checkpoint
- dataset
- `backend/outputs/**`
- `backend/logs/**`
- StableVITON `samples_smoke/**`

StableVITON smoke 결과는 외부 repo 로컬 경로에만 존재한다.

```text
D:\GitHub\StableVITON\samples_smoke\unpair
```

확인 결과:

- `git diff --check`: 통과.
- `git status`: 새 결과 리뷰 로그 문서 1개만 추가 대상이며 backend code 변경은 없다.
- `git status --ignored -s`: `backend/outputs/**`, `backend/logs/**`, `backend/outputs/stableviton_raw/**`, `__pycache__/**`가 ignored 상태로 확인되었다.
- `git ls-files --others --exclude-standard`: 출력 없음.
- generated image / dataset / checkpoint는 Git 포함 대상에 없음.
