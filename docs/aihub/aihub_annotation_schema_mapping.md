# AIHub Annotation Schema Mapping

## 1. 목적

이 문서는 AIHub JSON annotation을 우리 프로젝트의 fit analyzer feature로 어떻게 변환할지 정리한다.

현재 목표는 실제 parsing 구현이 아니라, PC2가 생성할 `features.csv`, `fit.json`, hotspot annotation이 backend와 frontend에서 어떤 의미로 사용될지 먼저 맞추는 것이다.

## 2. 주요 JSON 구조

AIHub JSON에서 확인해야 할 주요 필드는 다음과 같다. 실제 필드명과 중첩 구조는 PC2의 raw data 분석 결과에 따라 보정될 수 있다.

| AIHub 필드 | 설명 | 우리 프로젝트 사용 후보 |
| --- | --- | --- |
| `info[0].id` | annotation item id | case_id 또는 source item id 후보 |
| `info[0].model_id` | 모델 식별자 | 모델 단위 split, pair grouping |
| `info[0].cloth_id` | 의류 식별자 | 의류 단위 split, cloth category 연결 |
| `info[0].image.path` | 이미지 경로 | raw reference, processed subset mapping |
| `info[0].image.width` | 이미지 너비 | 좌표 정규화, bbox/mask ratio 계산 |
| `info[0].image.height` | 이미지 높이 | 좌표 정규화, length ratio 계산 |
| `info[0].image.angle` | 촬영 각도 | confidence penalty, view filter |
| `info[0].image.pose` | pose class | pose quality rule, subset filter |
| `info[0].segmentation_class` | segmentation class 정의 | 의류 영역, 신체 영역 grouping |
| `info[0].keypoint_class` | keypoint class 정의 | 어깨, 팔, 골반, 다리 기준점 mapping |
| `annotation[0].segmentation` | segmentation annotation | mask area, silhouette, body visibility feature |
| `annotation[0].keypoint` | keypoint annotation | shoulder, sleeve, torso, garment length feature |

예시 변환 흐름은 다음과 같다.

```text
AIHub raw JSON
-> item index
-> pair mapping
-> keypoint / segmentation feature calculation
-> features.csv
-> fit.json
-> backend fit analyzer loader
-> /api/result/{job_id}
```

## 3. Keypoint Mapping

| AIHub keypoint | fit feature 후보 | 계산 목적 |
| --- | --- | --- |
| `Left_shoulder` / `Right_shoulder` | `shoulder_width`, `shoulder_ratio` | 어깨 폭과 의류 어깨선 정렬 정도를 추정 |
| `Left_hip` / `Right_hip` | `torso_width_ratio` 후보 | 몸통 하단 기준 폭과 의류 mask 폭의 비율 후보 |
| `Left_elbow` / `Right_elbow` | `arm pose`, `sleeve reference` | 팔 자세가 소매 길이 판단에 적절한지 확인 |
| `Left_wrist` / `Right_wrist` | `sleeve_length_ratio` 후보 | 소매 끝 위치와 손목 기준점의 거리 비교 |
| `Left_hip` / `Right_hip` + garment mask | `garment_length_ratio` 후보 | 상의 또는 outer 길이를 골반 기준과 비교 |

keypoint는 단독으로 fit을 확정하지 않는다. pose, angle, segmentation 품질과 함께 confidence에 반영한다.

## 4. Segmentation Mapping

AIHub segmentation class를 우리 프로젝트 기준으로 다음 그룹에 묶는다.

| 프로젝트 그룹 | AIHub class 후보 |
| --- | --- |
| `upper_body_clothes` | `Top`, `T-shirt`, `shirts`, `Sweater`, `Blouse` |
| `outer` | `Coat`, `jacket`, `Jumper`, `Padding`, `vest`, `Cardigan` |
| `bottom` | `Pants`, `Skirt` |
| `one_piece` | `Dress`, `jumpsuit` |
| `body_parts` | `Face`, `Left-arm`, `Right-arm`, `Left-leg`, `Right-leg` |
| `base_clothes` | `Normal_top`, `Normal_bottom` |

class 명칭은 AIHub 원본 표기와 대소문자가 섞여 있을 수 있다. PC2 preprocessing 단계에서 canonical name을 만들고, backend에는 canonical group을 전달하는 방향이 유지보수에 유리하다.

## 5. Fit Feature 후보

아래 feature는 현재 확정 구현이 아니라 planned 또는 example only 상태다.

| feature_name | 입력 데이터 | 계산 아이디어 | 결과 범위 | confidence에 쓰는 방식 | 현재 구현 여부 |
| --- | --- | --- | --- | --- | --- |
| `shoulder_ratio` | shoulder keypoint, upper/outer mask | 의류 어깨선 후보 폭을 신체 어깨 폭과 비교 | 보통 `0.8`에서 `1.5` 예시 | 정상 범위 이탈 시 fit confidence 하락 | planned |
| `torso_width_ratio` | hip keypoint, torso 주변 garment mask | 몸통 기준 폭 대비 의류 mask 폭 비교 | 보통 `0.8`에서 `1.6` 예시 | slim, regular, loose rule 후보 | planned |
| `sleeve_length_ratio` | wrist/elbow keypoint, sleeve mask | 소매 끝 후보가 손목 기준에 가까운지 비교 | 보통 `0.7`에서 `1.3` 예시 | 짧거나 긴 소매 hotspot 후보 | planned |
| `garment_length_ratio` | hip/knee keypoint, garment mask | 의류 하단 위치를 골반 또는 무릎 기준과 비교 | 보통 `0.7`에서 `1.5` 예시 | 길이 관련 fit label 보조 | planned |
| `cloth_area_ratio` | garment segmentation mask, image size | 이미지 또는 body bbox 대비 의류 mask area 비율 | `0.0`에서 `1.0` | segmentation 과소/과대 감지 | example only |
| `body_visibility_score` | body part segmentation mask | 얼굴, 팔, 다리 등 주요 신체 영역 가시성 점수 | `0.0`에서 `1.0` | 낮으면 low confidence 후보 | planned |
| `pose_quality_score` | keypoint visibility, pose class | 주요 keypoint 누락 여부와 pose 난이도 반영 | `0.0`에서 `1.0` | pose가 불리하면 confidence 하락 | planned |
| `segmentation_quality_score` | segmentation mask coverage | mask 누락, 과도한 조각, body overlap 점검 | `0.0`에서 `1.0` | mask 품질이 낮으면 confidence 하락 | planned |
| `silhouette_score` | body mask, garment mask | 착장 전후 또는 기준 mask의 silhouette 자연스러움 평가 | `0.0`에서 `1.0` | 왜곡 의심 시 warning 생성 | example only |

## 6. Fit Label 후보

아래 label은 확정값이 아니라 rule 초안이다.

| label | 의미 |
| --- | --- |
| `unknown` | 분석에 필요한 feature가 부족하거나 아직 판단하지 않음 |
| `slim` | 몸통 또는 어깨 기준으로 타이트하게 보이는 후보 |
| `regular` | 주요 ratio가 기준 범위 안에 있는 후보 |
| `loose` | 몸통 또는 의류 영역이 여유 있게 보이는 후보 |
| `oversized` | 어깨, 몸통, 길이 중 여러 지표가 크게 여유 있는 후보 |
| `low_confidence` | pose, segmentation, visibility 품질이 낮아 fit 판단 신뢰도가 낮은 후보 |

MVP에서는 label을 먼저 단순하게 유지하고, feature 분포를 확인한 뒤 threshold를 조정한다.

## 7. Hotspot Annotation 후보

| hotspot part | 생성 상황 후보 |
| --- | --- |
| `shoulder` | shoulder_ratio가 기준 범위를 벗어나거나 어깨 keypoint와 의류 mask 정렬이 불안정한 경우 |
| `torso` | torso_width_ratio가 slim 또는 loose 후보로 판단되는 경우 |
| `sleeve` | sleeve_length_ratio가 짧거나 길게 계산되는 경우, wrist keypoint 신뢰도가 낮은 경우 |
| `length` | garment_length_ratio가 기준 길이보다 짧거나 긴 경우 |
| `cloth_region` | cloth_area_ratio 또는 segmentation_quality_score가 불안정한 경우 |
| `pose` | pose_quality_score가 낮아 전체 fit 판단을 제한해야 하는 경우 |

hotspot은 실제 결함 판정이 아니라 사용자가 결과를 검토해야 할 위치를 알려주는 UI 단서로 사용한다.

## 8. `fit.json` 변환 방향

PC2는 AIHub에서 계산한 feature를 backend가 읽을 수 있는 `fit.json` 또는 `features.csv`로 변환한다.

권장 흐름은 다음과 같다.

```text
AIHub item
-> case_id 생성
-> model_id / cloth_id / pose / angle 보존
-> keypoint feature 계산
-> segmentation feature 계산
-> confidence score 초안 계산
-> fit label 초안 계산
-> explanation 후보 생성
-> hotspot annotation 후보 생성
-> fit.json / features.csv 출력
```

`fit.json`은 `/api/result/{job_id}`의 fit 분석 부분과 연결될 수 있어야 한다. 현재 backend schema는 `confidence`, `fit`, `annotations`를 응답에 포함할 수 있으므로, loader는 외부 artifact의 필드를 backend response model에 맞게 변환해야 한다.

현재 backend annotation schema는 `key`, `label`, `text`, `x`, `y`, `value`를 사용한다. AIHub 기반 hotspot 후보가 `part`, `severity`, `message` 형태로 먼저 생성된다면, backend loader 또는 후속 DTO 정리에서 두 표현 중 하나로 통일해야 한다.
