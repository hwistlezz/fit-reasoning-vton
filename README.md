# 🧥 Fit-Reasoning VTON

StableVITON 기반 virtual try-on 결과에 fit reasoning과 confidence를 결합하기 위한 프로젝트입니다.

이 프로젝트의 목표는 사람 이미지와 의류 이미지를 입력받아 가상 착장 결과를 만들고, 단순히 이미지만 보여주는 것이 아니라 fit label, confidence score, fit explanation, hotspot annotation까지 연결 가능한 Virtual Try-On 시스템을 만드는 것입니다.

## 💡 프로젝트 시작 배경

온라인 의류 구매에서는 실제로 옷을 입어보기 전까지 착용감과 핏을 정확히 판단하기 어렵습니다.  
상품 상세 페이지의 모델 착용 사진이나 사이즈 표만으로는 내 체형에 어울리는지, 어깨선이 맞는지, 소매와 기장이 적절한지, 전체 실루엣이 원하는 느낌인지 확인하기 어렵습니다.

특히 온라인 쇼핑 사용자는 다음과 같은 불확실성을 자주 겪습니다.

- 같은 사이즈라도 브랜드와 의류 종류에 따라 실제 핏이 다름
- 모델 착용 사진과 내 체형의 차이로 인해 결과를 예상하기 어려움
- 오프라인 매장에 직접 방문하지 않으면 착용감을 확인하기 어려움
- 구매 후 사이즈 실패로 교환/반품이 발생할 수 있음
- 단순 가상 착장 이미지만으로는 결과가 얼마나 믿을 만한지 판단하기 어려움

Fit-Reasoning VTON은 이러한 문제를 줄이기 위해 시작한 프로젝트입니다.  
단순히 “옷을 입힌 이미지”를 생성하는 것을 넘어서, 생성된 결과가 얼마나 안정적인지, 어떤 부위의 핏이 좋은지 또는 불안정한지, 사용자가 결과를 어느 정도 신뢰할 수 있는지를 함께 설명하는 Virtual Try-On 시스템을 목표로 했습니다.

## 👥 대상 사용자

이 프로젝트는 온라인에서 의류를 구매하기 전에 착용 결과와 핏을 미리 확인하고 싶은 사용자를 주요 대상으로 합니다.

| 대상 사용자 | 사용자가 겪는 문제 | 제공하려는 가치 |
| --- | --- | --- |
| 온라인 쇼핑몰 사용자 | 구매 전 실제 착용 모습을 확인하기 어려움 | person image와 cloth image 기반 착장 시각화 제공 |
| 사이즈 선택에 고민하는 사용자 | S/M/L 같은 표기만으로 실제 핏을 판단하기 어려움 | fit label과 fit explanation 제공 |
| 오프라인 매장 방문이 번거로운 사용자 | 직접 입어보기 위해 매장에 가야 하는 불편함 | 온라인에서 사전 착용 경험 제공 |
| 반품/교환을 줄이고 싶은 사용자 | 구매 후 사이즈 실패 가능성 존재 | 구매 전 불확실성 감소 |
| VTON 결과를 신뢰하고 싶은 사용자 | 생성 이미지가 그럴듯해도 실패 부위를 알기 어려움 | confidence score와 hotspot annotation 제공 |

## 🎯 핵심 문제 정의

일반적인 Virtual Try-On은 주로 다음 질문에 답합니다.

> “이 옷을 입히면 어떤 이미지가 나오는가?”

하지만 실제 사용자는 그 다음 질문까지 알고 싶어 합니다.

> “이 결과를 믿어도 되는가?”  
> “어깨, 소매, 몸통, 기장 중 어디가 안정적인가?”  
> “내 체형 기준으로 이 옷은 타이트한가, 레귤러한가, 루즈한가?”  
> “가상 착장 결과에서 실패 가능성이 높은 부위는 어디인가?”

따라서 이 프로젝트의 문제 정의는 단순 이미지 생성이 아니라, **가상 착장 결과에 대한 설명 가능한 핏 분석**입니다.

## 🧭 서비스 목표

Fit-Reasoning VTON의 서비스 목표는 다음과 같습니다.

1. 사용자가 사람 이미지와 의류 이미지를 입력한다.
2. StableVITON 기반으로 가상 착장 이미지를 생성한다.
3. 생성 결과에 대해 fit label을 제공한다.
4. confidence score를 통해 결과 신뢰도를 보여준다.
5. 어깨, 소매, 그래픽 중심, 밑단 등 주요 부위별 hotspot annotation을 제공한다.
6. 사용자가 구매 전에 착용 결과와 핏 안정성을 판단할 수 있도록 돕는다.

결과적으로 이 프로젝트의 핵심 가치는 **온라인 의류 구매 전 불확실성 감소**입니다.

## 🔍 기존 Virtual Try-On과의 차별점

기존 Virtual Try-On 시스템은 보통 최종 착장 이미지를 생성하는 데 집중합니다.  
반면 Fit-Reasoning VTON은 생성 결과를 사용자 관점에서 해석할 수 있도록 다음 정보를 함께 제공하는 방향으로 설계했습니다.

| 구분 | 일반 Virtual Try-On | Fit-Reasoning VTON |
| --- | --- | --- |
| 주요 출력 | 착장 이미지 | 착장 이미지 + 핏 분석 |
| 사용자 관점 설명 | 제한적 | fit explanation 제공 |
| 결과 신뢰도 | 판단하기 어려움 | confidence score 제공 |
| 실패 부위 확인 | 어려움 | hotspot annotation 제공 |
| 분석 기준 | 이미지 생성 품질 중심 | 어깨, 소매, 기장, 그래픽 보존, 포즈 안정성까지 고려 |
| 목표 | 착장 시각화 | 구매 전 의사결정 보조 |

이 프로젝트는 “그럴듯한 착장 이미지”를 만드는 것에서 끝나지 않고, 사용자가 결과를 해석하고 신뢰할 수 있도록 만드는 것을 목표로 합니다.

## 🎬 Demo

현재 Git에는 실제 데모 영상, 결과 이미지, dataset을 포함하지 않습니다.

데모 영상 링크: https://drive.google.com/drive/u/0/folders/1ohD0kGGElCdoHZPtS9bWI1p0Qaeqj_XA

## 🖥️ Demo UI Preview

<img width="1196" height="756" alt="image" src="https://github.com/user-attachments/assets/221bf1af-b2bc-484d-8704-6bafc3d219e1" />

위 화면은 Fit-Reasoning VTON의 데모용 비교 페이지입니다.  
사용자는 person image(사람 이미지), cloth image(의류 이미지), worn image(정답 착용 이미지)를 업로드한 뒤, 동일한 입력에 대해 `Target Worn`, `StableVITON`, `StableVITON LoRA` 결과를 나란히 비교할 수 있습니다.
  
상단의 `StableVITON`, `IDM VTON`, `CAT VITON` 탭은 StableVITON 중심 실험 결과를 확장하여 후속 baseline comparison을 진행하기 위한 비교 모델 후보를 나타냅니다.

### 🧥🆚👕 Demo Flow: Model Comparison and Fit Reasoning

아래 화면들은 동일한 person image(사람 이미지), cloth image(의류 이미지), target worn image(정답 착용 이미지)를 기준으로 StableVITON baseline과 StableVITON + LoRA 결과를 비교하는 데모 흐름입니다.

이 데모는 단순히 결과 이미지만 보여주는 것이 아니라, 다음 정보를 함께 확인할 수 있도록 구성했습니다.

- 입력 이미지와 정답 착용 이미지
- StableVITON baseline 결과
- StableVITON + LoRA 결과
- confidence score(신뢰도 점수)
- fit score details(핏 세부 점수)
- hotspot annotation(위험 부위 표시)
- skeleton(포즈 정렬)
- DensePose(신체 표면 구조)
- agnostic mask / parsing / cloth mask(조건부 artifact)
- reliability analysis(결과 신뢰도 분석)

> 현재 화면의 정량 점수는 demo pair 기준의 UI-level comparison score입니다.  
> 전체 test set에 대한 정량 benchmark가 아니라, 데모 입력 쌍에서 StableVITON baseline과 LoRA-enhanced 결과의 차이를 설명하기 위한 비교 지표입니다.

#### 1. Input / Target / Baseline / LoRA Result Comparison

<img width="936" height="605" alt="스크린샷 2026-06-07 021810" src="https://github.com/user-attachments/assets/7c3756fe-2aaf-4413-9051-a96921a496db" />


첫 번째 화면은 전체 비교 화면입니다.  
좌측에는 입력으로 사용한 person image, cloth image, target worn image가 표시되고, 중앙과 우측에는 각각 StableVITON baseline과 StableVITON + LoRA 결과가 표시됩니다.

이 예시에서 baseline 결과는 `confidence=72`, `level=Medium`으로 평가되었고, LoRA-enhanced 결과는 `confidence=86`, `level=High`로 평가되었습니다.  
즉, 동일 입력 조건에서 LoRA 결과가 더 안정적인 착장 경계와 그래픽 보존을 보인다는 흐름을 보여줍니다.

#### 2. Hotspot-based Fit and Quality Analysis

<img width="904" height="604" alt="스크린샷 2026-06-07 021925" src="https://github.com/user-attachments/assets/b872d800-0564-4255-86f4-2dbdb99d7740" />


두 번째 화면은 hotspot 기반 상세 분석 화면입니다.  
결과 이미지 위에 어깨, 그래픽 중심, 소매, 밑단 등 주요 위치를 시각적으로 표시하고, 각 부위별 안정성 점수를 함께 보여줍니다.

상단 카드에서는 다음 항목을 baseline과 LoRA로 비교합니다.

| Metric | StableVITON | StableVITON + LoRA | Diff |
| --- | ---: | ---: | ---: |
| Shoulder Alignment | 74 | 88 | +14 |
| Graphic Preservation | 69 | 87 | +18 |
| Sleeve Boundary | 68 | 84 | +16 |
| Hem Stability | 71 | 85 | +14 |
| Color Consistency | 76 | 88 | +12 |
| Pose Robustness | 70 | 84 | +14 |

이 화면은 LoRA 적용 후 어떤 부위의 품질이 개선되었는지 사용자가 직관적으로 확인할 수 있게 합니다.

#### 3. Skeleton-based Pose Alignment

<img width="887" height="585" alt="스크린샷 2026-06-07 021953" src="https://github.com/user-attachments/assets/44db8d7a-0e23-459a-bfc7-172384304cbd" />


세 번째 화면은 skeleton 기반 포즈 정렬 분석입니다.  
OpenPose-style keypoint를 이용해 어깨, 팔꿈치, 손목, 골반 위치가 결과 이미지에서 얼마나 안정적으로 유지되는지 확인합니다.

특히 VTON 결과에서 중요한 부분은 다음입니다.

- 어깨선과 의류 어깨선의 정렬
- 팔 위치와 소매 경계의 일관성
- 골반/몸통 중심선과 의류 중심의 정렬
- 비정면 자세에서 포즈 artifact가 결과 안정성에 주는 영향

이 화면은 단순 이미지 품질이 아니라, 신체 구조 기반으로 결과를 분석한다는 점을 보여줍니다.

#### 4. DensePose-based Conditioning Analysis

<img width="900" height="592" alt="스크린샷 2026-06-07 022007" src="https://github.com/user-attachments/assets/a6667870-d2fa-462e-91bb-8b0a0a4172e9" />


네 번째 화면은 DensePose 기반 conditioning 분석입니다.  
비정면 자세나 손에 든 물체처럼 occlusion(가림)이 있는 입력에서도 신체 표면 구조와 의류 위치가 얼마나 안정적으로 정렬되는지 확인합니다.

이 프로젝트에서는 DensePose, skeleton, enhanced result를 함께 보여주어 다음 질문에 답할 수 있도록 했습니다.

- 비정면 자세에서도 상체 영역이 안정적으로 유지되는가?
- 팔이나 물체가 의류 영역을 가리는 경우에도 결과가 무너지지 않는가?
- LoRA 적용 결과가 baseline보다 의류 위치와 그래픽 중심을 더 잘 유지하는가?

#### 5. Agnostic Mask / Parsing / Cloth Mask Analysis

<img width="897" height="607" alt="스크린샷 2026-06-07 022021" src="https://github.com/user-attachments/assets/fd5760fe-8301-4009-a276-23716f68f2cb" />


다섯 번째 화면은 StableVITON 학습과 inference에 필요한 artifact를 시각적으로 보여줍니다.

화면에는 다음 artifact가 포함됩니다.

| Artifact | Description |
| --- | --- |
| Agnostic Person | 기존 의류 영역을 제거한 사람 이미지 |
| Upper-body Mask | 상체 의류 영역을 나타내는 mask |
| Human Parsing Map | 사람 신체 부위별 parsing 결과 |
| Cloth Mask | 입력 의류의 영역 mask |

이 화면은 StableVITON 계열 VTON이 단순히 `person image + cloth image`만 사용하는 것이 아니라, pose, parsing, mask, DensePose 같은 조건부 artifact 정합성이 중요하다는 점을 보여줍니다.

#### 6. Reliability and Confidence Analysis

<img width="904" height="601" alt="스크린샷 2026-06-07 022033" src="https://github.com/user-attachments/assets/8e81236c-9858-4e51-8fbf-5df7d4cdb365" />


여섯 번째 화면은 결과 신뢰도 분석 화면입니다.  
최종 result reliability score는 `86`으로 표시되며, 입력 품질, pose confidence, garment alignment, boundary stability를 함께 평가합니다.

| Reliability Item | Score |
| --- | ---: |
| Result Reliability | 86 |
| Input Quality | 82 |
| Pose Confidence | 78 |
| Garment Alignment | 86 |
| Boundary Stability | 84 |

이 화면은 결과가 그럴듯하게 보이는지뿐 아니라, 입력 조건과 artifact 안정성을 기준으로 사용자가 결과를 얼마나 신뢰할 수 있는지 설명하기 위한 UI입니다.

#### 7. Fit Details and Metric Comparison

<img width="916" height="587" alt="스크린샷 2026-06-07 022137" src="https://github.com/user-attachments/assets/75892b19-72eb-4a1e-8334-e77b64d0b2f8" />


마지막 화면은 fit details 분석입니다.  
StableVITON baseline은 `slightly unstable oversized fit`으로, StableVITON + LoRA는 `stable oversized fit`으로 표시됩니다.

또한 앞에서 보여준 6개 세부 지표를 표 형태로 다시 정리하여, LoRA 적용 전후의 차이를 명확히 보여줍니다.

| Metric | Baseline | LoRA | Diff |
| --- | ---: | ---: | ---: |
| Shoulder Alignment | 74 | 88 | +14 |
| Graphic Preservation | 69 | 87 | +18 |
| Sleeve Boundary | 68 | 84 | +16 |
| Hem Stability | 71 | 85 | +14 |
| Color Consistency | 76 | 88 | +12 |
| Pose Robustness | 70 | 84 | +14 |

이 흐름을 통해 사용자는 단순히 “결과 이미지가 좋아 보인다”가 아니라, 어느 부위에서 어떤 점수가 개선되었는지 확인할 수 있습니다.



---

## 🧠 Technical Motivation

서비스 관점에서는 온라인 의류 구매 전 착용감과 핏에 대한 불확실성을 줄이는 것이 목표입니다.  
기술 관점에서는 일반적인 Virtual Try-On 결과 이미지에 reasoning layer를 연결하여, 결과 이미지가 얼마나 신뢰 가능한지와 어떤 부위가 안정적인지 설명하는 것이 핵심입니다.

일반적인 Virtual Try-On(VTON)은 “옷이 입혀진 이미지”를 보여주는 데 집중합니다. 하지만 실제 사용자는 다음 질문을 함께 알고 싶어 합니다.

- 생성 결과가 어느 정도 믿을 만한가?
- 핏이 타이트한지, 레귤러한지, 루즈한지 설명할 수 있는가?
- 어깨, 소매, 몸통, 기장 중 어느 부분이 실패했거나 위험한가?
- 입력 pose, parsing, dense pose 같은 artifact가 결과 안정성에 어떤 영향을 주는가?

Fit-Reasoning VTON은 VTON 결과 이미지에 fit reasoning layer를 연결하는 방향으로 설계했습니다. StableVITON 호환 dataset layout, artifact readiness, LoRA training pipeline, LoRA adapter save/load smoke, 10k adapter save run까지 검증했습니다.  



## 🎯 Problem Definition

### Input

- Person image
- Cloth image
- Optional user body info: height, weight, usual size

### Target Output

- Try-on result image
- Fit label
- Confidence score
- Fit score details
- Natural language fit explanation
- Hotspot annotation for visible risk areas

### Current Implementation Stage

현재 구현/검증의 중심은 StableVITON/LoRA training pipeline입니다.

- StableVITON-compatible AIHub 10k artifact dataset layout 준비 완료
- StableVITON `train.py` compatibility smoke 성공
- 일부 attention Linear module 대상 LoRA runner 구현
- 10k 9995-step 1 epoch-equivalent LoRA training loop 성공
- LoRA adapter save/load smoke 성공
- 10k 9995-step LoRA adapter save run 완료
- Demo compare API와 frontend compare page 구조 준비
- 10k adapter 기반 inference comparison
- StableVITON baseline vs LoRA 실제 이미지 비교
- demo pair 기준 StableVITON baseline 대비 LoRA 결과의 정성/정량 보조 지표 개선 확인
- 최종 demo video 업로드



## ✨ Key Contributions

1. AIHub 10k full artifact dataset readiness를 검증했습니다.
2. StableVITON 학습 포맷에 맞는 9995개 train-only layout을 구성했습니다.
3. StableVITON external repo를 수정하지 않고 import하는 LoRA runner를 구축했습니다.
4. 전체 모델 full fine-tuning이 아니라 일부 attention Linear module에 LoRA adapter를 삽입했습니다.
5. 9995-step 1 epoch-equivalent LoRA training loop를 RTX 4080 환경에서 완료했습니다.
6. LoRA parameter만 저장/로드하는 adapter save/load smoke를 검증했습니다.
7. Dataset, output, checkpoint, generated image를 Git에 포함하지 않는 실험 문서화 체계를 유지했습니다.



## 🧩 System Overview

```mermaid
flowchart LR
  A[Person Image] --> C[Artifact Preparation]
  B[Cloth Image] --> C
  C --> D[StableVITON Layout]
  D --> E[StableVITON Baseline]
  D --> F[LoRA Training]
  F --> G[Adapter Save / Load]
  G --> H[Inference Comparison]
  H --> I[Fit Reasoning UI]
```  

## 🔄 Image-to-Result Pipeline

이 프로젝트에서 중요한 부분은 단순히 두 이미지를 입력받아 바로 합성하는 것이 아니라, 사람 이미지와 의류 이미지를 StableVITON이 사용할 수 있는 형태로 정리하고, 생성된 결과를 다시 사용자가 이해할 수 있는 정보로 바꾸는 과정입니다.

전체 흐름은 다음과 같습니다.

```mermaid
flowchart LR
  A[Person Image] --> B[Preprocessing]
  C[Cloth Image] --> B
  B --> D[StableVITON-compatible Artifacts]
  D --> E[Baseline Inference]
  D --> F[LoRA-enhanced Inference]
  E --> G[Result Comparison]
  F --> G
  G --> H[Fit / Confidence / Hotspot UI]
```

### 1. 입력 이미지 정리

Virtual Try-On에서는 사람 이미지와 의류 이미지만 준비한다고 바로 학습이나 추론이 가능한 것은 아닙니다.  
모델이 사람의 자세, 상체 영역, 기존 의류 영역, 새로 입힐 의류 영역을 구분할 수 있도록 여러 보조 파일을 같은 pair 기준으로 맞춰야 합니다.

이 프로젝트에서는 다음 요소들을 하나의 sample 단위로 정리했습니다.

- 사람 원본 이미지
- 의류 상품 이미지
- 정답 착용 이미지 후보
- 기존 의류 영역을 제거한 사람 이미지
- 상체 의류 영역 mask
- 의류 mask
- 사람 부위 parsing 결과
- pose keypoint JSON
- DensePose-style artifact
- fit annotation JSON

이 과정의 목적은 “이미지를 많이 모으는 것”이 아니라, StableVITON이 기대하는 입력 구조에 맞게 파일명, 해상도, 폴더 구조, pair 관계를 일관되게 맞추는 것입니다.

### 2. Artifact 기반 조건 정리

StableVITON 계열 모델은 입력 이미지를 단순한 RGB 이미지로만 보지 않습니다.  
사람 이미지에서 어떤 영역을 유지해야 하는지, 어떤 영역을 새 옷으로 바꿔야 하는지, 팔과 몸통이 어디에 있는지 같은 정보를 함께 사용합니다.

따라서 이 프로젝트에서는 artifact를 다음과 같은 역할로 사용했습니다.

| Artifact | 사용 목적 |
| --- | --- |
| `agnostic-v3.2/` | 기존 상의 정보를 줄이고, 사람의 체형과 자세 정보는 유지 |
| `agnostic-mask/` | 새 의류가 적용될 상체 영역 지정 |
| `cloth-mask/` | 입력 의류에서 실제 옷 영역만 분리 |
| `image-parse/` | 팔, 몸통, 상의 등 사람 부위 구분 |
| `openpose-json/` | 어깨, 팔꿈치, 손목 등 주요 관절 위치 확인 |
| `image-densepose/` | 사람의 표면 구조를 더 안정적으로 참고하기 위한 조건 정보 |
| `gt_cloth_warped_mask/` | 의류 정렬 및 warping 관련 학습 보조 정보 |

이 artifact들은 최종 사용자에게 직접 보이는 데이터라기보다는, 모델이 착장 위치와 경계를 더 안정적으로 판단하도록 돕는 내부 조건 정보입니다.

### 3. 결과 비교 기준

StableVITON baseline과 StableVITON + LoRA 결과는 단순히 “더 좋아 보이는지”만으로 비교하기 어렵습니다.  
그래서 데모 UI에서는 결과 이미지를 몇 가지 관점으로 나누어 확인하도록 구성했습니다.

| 비교 항목 | 확인하려는 내용 |
| --- | --- |
| Shoulder Alignment | 생성된 의류 어깨선이 사람의 어깨 위치와 자연스럽게 맞는지 |
| Graphic Preservation | 입력 의류의 전면 그래픽이 결과 이미지에서도 중심과 형태를 유지하는지 |
| Sleeve Boundary | 팔 영역과 소매 경계가 섞이지 않고 분리되는지 |
| Hem Stability | 상의 밑단이 몸통 하단에서 어색하게 흐트러지지 않는지 |
| Color Consistency | 입력 의류의 색감이 결과 이미지에서 크게 변하지 않는지 |
| Pose Robustness | 비정면 자세나 팔 위치 변화에도 결과가 안정적인지 |

이 기준들은 모델의 일반적인 성능을 확정적으로 주장하기 위한 지표가 아니라, 데모 pair에서 baseline과 LoRA 결과의 차이를 사용자가 이해하기 쉽게 보여주기 위한 보조 기준입니다.

### 4. LoRA 적용 방향

이번 프로젝트에서는 StableVITON 전체 모델을 다시 학습하지 않고, 일부 attention Linear module에만 LoRA adapter를 삽입했습니다.

전체 모델을 fine-tuning하면 parameter 수와 VRAM 부담이 크고, 제한된 시간 안에 여러 실험을 반복하기 어렵습니다.  
반면 LoRA는 기존 모델의 대부분 parameter를 고정한 상태에서 작은 adapter parameter만 학습하므로, 실험 비용을 줄이면서도 특정 데이터셋에 대한 적응 가능성을 확인할 수 있습니다.

이번 실험에서는 다음 방향을 유지했습니다.

- StableVITON 외부 repository는 직접 수정하지 않음
- 우리 repository의 runner에서 StableVITON을 import하여 실행
- 전체 checkpoint가 아니라 LoRA adapter parameter만 저장
- dataset, output, checkpoint, generated image는 Git에 포함하지 않음
- 1-step smoke → 100-step benchmark → 9995-step run 순서로 안정성 확인

이를 통해 단순 실행 성공이 아니라, 학습 가능성, adapter 저장/로드, inference 비교까지 이어지는 최소 실험 흐름을 구성했습니다.

### 5. 이미지 정렬 관점에서의 주요 처리 포인트

Virtual Try-On 결과의 품질은 모델 구조뿐만 아니라 입력 이미지와 artifact가 얼마나 잘 정렬되어 있는지에도 크게 영향을 받습니다.  
특히 사람 이미지와 의류 이미지가 서로 다른 촬영 조건, 자세, 비율을 가지기 때문에 다음과 같은 정렬 문제가 발생할 수 있습니다.

| 처리 포인트 | 설명 |
| --- | --- |
| Person-Cloth Scale | 사람 상체 크기와 의류 이미지의 크기 차이를 맞추는 문제 |
| Body Center Alignment | 사람의 몸통 중심과 의류의 중심이 어긋나지 않도록 하는 문제 |
| Shoulder Line Alignment | 사람 어깨 위치와 의류 어깨선이 자연스럽게 대응되는지 확인 |
| Sleeve-Arm Boundary | 팔 영역과 소매 영역이 섞이지 않도록 경계를 유지 |
| Texture Preservation | 의류의 그래픽, 로고, 패턴이 생성 결과에서 과하게 변형되지 않도록 유지 |
| Occlusion Handling | 팔, 가방, 손에 든 물체처럼 상체를 가리는 요소가 있을 때 결과 안정성 확인 |

이 프로젝트에서는 이러한 문제를 직접 수식으로 해결하기보다는, pose, parsing, mask, DensePose-style artifact를 StableVITON 입력 구조에 맞게 정리하고, LoRA 학습 결과를 같은 pair 기준으로 비교하는 방식으로 접근했습니다.

   
## 👥 팀 역할 및 협업 방식

이 프로젝트는 백엔드/API, 프론트엔드 UI, 데이터 전처리, StableVITON/LoRA 학습 실험을 PC별로 나누어 진행했습니다.  
대용량 dataset, checkpoint, generated output은 Git에 포함하지 않고, 각 PC의 local workspace에서 처리한 뒤 코드와 실험 문서만 repository에 기록했습니다.

| 팀원 | 담당 영역 | 담당 PC / 환경 | 주요 작업 |
| --- | --- | --- | --- |
| 김성휘 | Backend, PC 1, PC 3, LoRA training | PC 1, PC 3 | FastAPI backend 구조 설계, Try-On job API, StableVITON wrapper, PC 3 dataset 검증, StableVITON-compatible layout 구성, LoRA runner 구현, 10k 9995-step training, LoRA adapter save/load 검증, 실험 문서화 |
| 정경재 | Frontend, PC 2, Data preprocessing, Demo pipeline planning | Frontend local dev, PC 2 preprocessing environment | Next.js demo UI, model/artifact comparison page, 업로드/결과 비교 화면 구성, AIHub 기반 preprocessing artifact 생성, PC 2 dataset 정리, PC 3 전달용 dataset archive 준비, 실시간 업로드형 데모 플로우 기획, frontend-backend 응답 schema 및 전체 demo pipeline 구조 정리 |

### PC별 작업 흐름

```mermaid
flowchart LR
  A[PC2: AIHub data preprocessing] --> B[Dataset archive / split files]
  B --> C[HTTP transfer to PC3]
  C --> D[PC3: 압축 해제 및 dataset smoke test]
  D --> E[StableVITON-compatible 10k layout]
  E --> F[PC3: LoRA training / adapter save]
  F --> G[PC1: Backend API / StableVITON service]
  G --> H[Frontend: demo compare UI]
```

### PC 1: Backend / StableVITON API Server

PC 1은 사용자가 업로드한 person image와 cloth image를 받아 StableVITON inference 흐름에 연결하기 위한 backend server 역할을 담당했습니다.

주요 작업은 다음과 같습니다.

- FastAPI backend skeleton 구성
- `/api/health`, `/api/tryon`, `/api/job/{job_id}`, `/api/result/{job_id}` API 구조 준비
- 외부 StableVITON repository를 직접 수정하지 않고 호출하는 wrapper 구조 설계
- Demo compare API skeleton 구성
- result schema, confidence, fit explanation, hotspot annotation을 연결할 수 있는 API 응답 구조 준비

### PC 2: Frontend / Data Preprocessing

PC 2는 AIHub dataset 기반 preprocessing과 frontend UI 구현을 담당했습니다.

주요 작업은 다음과 같습니다.

- AIHub 원본 데이터 기반 preprocessing artifact 준비
- pose, parsing, mask, DensePose 계열 artifact 정리
- PC 3에서 사용할 수 있도록 dataset archive 구성
- HTTP server를 통해 PC 3로 dataset 전달
- Next.js 기반 demo UI 구현
- person image, cloth image, target worn, StableVITON, StableVITON LoRA 결과를 비교할 수 있는 model comparison page 구성
- 실시간 업로드형 demo flow 기획
- frontend에서 사용할 backend response schema, result card 구조, detailed analysis tab 구성 방향 정리
- person / cloth / worn 입력과 Target Worn / StableVITON / StableVITON LoRA 출력 비교 구조 설계

### PC 3: Dataset Validation / LoRA Training

PC 3는 PC 2에서 전달받은 dataset을 이용해 StableVITON-compatible layout을 만들고, LoRA training 실험을 수행하는 역할을 담당했습니다.

작업 흐름은 다음과 같습니다.

1. PC 2에서 전처리한 dataset archive를 HTTP로 전달받음
2. PC 3 local workspace에서 압축 해제
3. dataset file count, manifest, required artifact 존재 여부 검증
4. StableVITON-compatible 10k train layout 구성
5. 1-step sanity → 100-step benchmark → 9995-step run 순서로 학습 가능성 검증
6. StableVITON 일부 attention Linear module에 LoRA adapter 삽입
7. 10k 9995-step 1 epoch-equivalent LoRA training 수행
8. LoRA adapter save/load smoke 및 9995-step adapter save run 수행

  
## 🌿 Git Flow

이 프로젝트는 `dev` branch를 기준 통합 브랜치로 사용하는 Git Flow 방식으로 작업했습니다.  
`main`에 직접 작업하지 않고, 기능/실험/문서 단위로 issue branch를 만든 뒤 PR을 통해 `dev`에 병합하는 흐름을 유지했습니다.

### Branch Strategy

| Branch Type | Purpose | Example |
| --- | --- | --- |
| `dev` | 통합 개발 브랜치 | `dev` |
| `feat/#이슈번호/...` | 기능 구현 | `feat/#12/backend-skeleton` |
| `experiment/#이슈번호/...` | 실험 및 학습 검증 | `experiment/#106/stableviton-lora-10k-epoch-pilot` |
| `docs/#이슈번호/...` | 문서 작성 및 README 수정 | `docs/#111/readme-final-polish` |
| `chore/#이슈번호/...` | 환경 설정, 정리 작업 | `chore/#3/backend-folder-setup` |

### 작업 순서

```text
1. dev 최신화
2. issue 단위 branch 생성
3. 작업 수행
4. 실험 결과 또는 구현 내용 문서화
5. git diff --check 검증
6. dataset/output/checkpoint/generated image가 Git에 포함되지 않았는지 확인
7. commit
8. origin에 push
9. Pull Request 생성
10. review 후 dev에 merge
```

### 실제 작업 예시

```powershell
git switch dev
git pull origin dev
git switch -c "experiment/#106/stableviton-lora-10k-epoch-pilot"
```

작업 완료 후에는 다음과 같은 형식으로 commit message를 작성했습니다.

```text
feat(#106/stableviton): LoRA 10k epoch pilot 실행 기록
docs(#111): README 고도화
```

### 협업 원칙

- 모든 작업은 issue 단위로 분리했습니다.
- 실험성 작업은 `experiment/#이슈번호/...` branch에서 진행했습니다.
- 문서 작업은 `docs/#이슈번호/...` branch에서 진행했습니다.
- `dev` branch를 기준으로 최신 상태를 맞춘 뒤 새 branch를 생성했습니다.
- dataset, checkpoint, generated image, `.pt` adapter file은 Git에 포함하지 않았습니다.
- 실험 결과는 `docs/experiments/`에 기록하고, README에는 핵심 결과만 요약했습니다.
- 팀원별 작업 내역이 Git log와 PR 기록에 남도록 기능/문서/실험 단위로 commit과 PR을 나누어 진행했습니다.




  
## 📦 Dataset and Artifacts

사용 dataset은 AIHub 쉐이프리스 의류 및 포즈 데이터 기반으로 PC2/PC3 작업 흐름에서 구성한 10k artifact dataset입니다.

Dataset은 용량과 라이선스 문제로 Git에 포함하지 않습니다.

### Why AIHub Dataset?

이 프로젝트에서는 임의로 웹에서 수집한 쇼핑몰 이미지나 개인 착용 사진 대신, AIHub 기반 의류/포즈 데이터를 사용했습니다.

Virtual Try-On 실험에서는 단순히 이미지 수가 많은 것보다, 사람 이미지와 의류 이미지가 일정한 기준으로 정리되어 있고, pose, mask, parsing, DensePose-style artifact로 확장할 수 있는지가 중요합니다. AIHub 데이터는 이러한 전처리 흐름을 구성하기에 적합하다고 판단했습니다.

| 선택 이유 | 설명 |
| --- | --- |
| 데이터 출처 명확성 | 웹 크롤링 이미지보다 출처와 사용 범위를 명확히 관리할 수 있음 |
| 의류/사람 이미지 기반 실험에 적합 | person image와 cloth image를 사용하는 VTON 실험 구조와 잘 맞음 |
| 10k scale 실험 가능 | tiny smoke 수준을 넘어 9995개 train layout 기준의 실제 학습 실험까지 확장 가능 |
| artifact 확장 가능 | agnostic image, mask, parsing, pose, DensePose-style artifact를 함께 구성할 수 있음 |
| StableVITON layout 변환 가능 | StableVITON이 요구하는 VITON-HD style folder structure로 재구성 가능 |
| 재현 가능한 실험 관리 | manifest, pair file, folder count, strict artifact smoke로 데이터 준비 상태를 검증하기 좋음 |
| Git 관리 부담 감소 | raw dataset은 local workspace에 두고, repository에는 코드와 실험 문서만 기록하는 방식과 잘 맞음 |

AIHub 데이터를 그대로 사용하는 것만으로 StableVITON 학습이 바로 가능한 것은 아니었습니다.  
원본 데이터는 StableVITON이 기대하는 폴더 구조, 파일명 규칙, 이미지 크기, mask 형식과 차이가 있었기 때문에 별도의 layout 변환과 artifact 검증 과정이 필요했습니다.

이 프로젝트에서는 AIHub 기반 데이터를 다음 흐름으로 정리했습니다.

```mermaid
flowchart LR
  A[AIHub Raw Data] --> B[PC2 Preprocessing]
  B --> C[Artifact Generation / Organization]
  C --> D[PC3 Dataset Smoke Test]
  D --> E[StableVITON-compatible 10k Layout]
  E --> F[LoRA Training / Adapter Save]
```

결과적으로 AIHub 데이터셋을 선택한 이유는 단순히 “사용 가능한 데이터가 있었기 때문”이 아니라,  
**Virtual Try-On 학습에 필요한 사람-의류 pair, artifact 구성, 10k scale 실험, 재현 가능한 검증 흐름을 만들기 적합했기 때문**입니다.

### StableVITON Layout Summary

| Item | Value |
| --- | ---: |
| train_count | 9995 |
| test_count | 0 |
| ready_count | 9995 |
| not_ready_count | 0 |
| original dataset modified | false |

### Artifact Folders

StableVITON-compatible layout에서 사용한 주요 artifact는 다음과 같습니다.

| Artifact | Role |
| --- | --- |
| `image/` | 착장 대상이 되는 사람 이미지 |
| `cloth/` | 새로 입힐 의류 이미지 |
| `worn/` | 비교 기준으로 사용할 수 있는 실제 착용 이미지 후보 |
| `fit/` | fit feature 또는 annotation JSON |
| `agnostic-v3.2/` | 기존 상의 정보를 줄인 사람 이미지 |
| `agnostic-mask/` | 새 의류가 들어갈 상체 영역 mask |
| `openpose-json/` | 사람의 주요 관절 위치 정보 |
| `image-parse/` | 사람 영역을 부위별로 나눈 parsing 결과 |
| `cloth-mask/` | 입력 의류 영역 mask |
| `image-densepose/` | 사람의 자세와 표면 구조를 보조적으로 표현한 artifact |
| `gt_cloth_warped_mask/` | 의류 정렬 및 warping 관련 학습 보조 mask |

이 구조를 맞추는 과정에서 가장 중요했던 점은 각 artifact가 같은 `pair_id` 기준으로 정확히 대응되어야 한다는 점입니다.  
하나의 sample에서 이미지, mask, parsing, pose 정보가 서로 맞지 않으면 학습은 실행되더라도 결과 비교나 품질 해석이 어려워질 수 있습니다.

### Preprocessing Notes

StableVITON-compatible layout을 구성할 때는 단순히 파일을 복사하는 것보다, 이미지 계열과 mask 계열을 다르게 처리하는 것이 중요했습니다.

| 항목 | 처리 기준 |
| --- | --- |
| RGB image | 사람 이미지, 의류 이미지, agnostic image, DensePose-style image는 모델 입력 크기에 맞게 resize |
| Mask image | agnostic mask, cloth mask, warped mask는 label boundary가 깨지지 않도록 nearest-neighbor 방식으로 resize |
| JSON artifact | pose keypoint, fit annotation은 같은 `pair_id` 기준으로 연결 |
| Pair file | StableVITON이 읽을 수 있도록 person-cloth pair 관계를 명시 |
| Source dataset | 원본 데이터는 수정하지 않고, 학습용 output layout만 별도로 생성 |

특히 mask 계열 이미지는 일반 이미지처럼 보간하면 경계가 흐려지거나 label 값이 섞일 수 있습니다.  
따라서 RGB 이미지와 mask 이미지를 구분해서 처리했고, 이 점을 strict artifact smoke와 layout validation으로 확인했습니다.


### Strict Artifact Smoke

| Metric | Value |
| --- | ---: |
| checked_count | 9995 |
| artifact_errors | 0 |
| backend_loader_errors | 0 |


    
## 🧠 Model and Training

### Base Model

- Base VTON backbone: StableVITON
- External checkout: `D:\GitHub\StableVITON`
- Repo-side runner: `backend/training/scripts/run_stableviton_lora_tiny_smoke.py`

StableVITON source code, pretrained weights, generated images, and dataset 파일들은 이 저장소에 커밋하지 않습니다.

### Why StableVITON?

StableVITON은 사람 이미지와 의류 이미지를 함께 사용해 가상 착장 결과를 생성하는 diffusion 기반 VTON 모델입니다.  
이 프로젝트에서는 StableVITON을 직접 새로 구현하기보다, 공개된 StableVITON 구조를 기반으로 dataset layout 구성, LoRA 삽입, adapter 저장/로드, inference comparison 흐름을 검증하는 데 집중했습니다.

선택 이유는 다음과 같습니다.

- 사람 이미지와 의류 이미지를 함께 사용하는 VTON 구조를 갖고 있음
- pose, mask, parsing, DensePose-style artifact를 활용하는 실험 흐름과 잘 맞음
- baseline 결과와 LoRA 적용 결과를 같은 입력 pair 기준으로 비교하기 좋음
- 전체 모델을 수정하지 않고도 외부 repository 기반 runner로 실험을 확장할 수 있음

### LoRA Strategy

이번 실험은 StableVITON 전체 모델을 full fine-tuning하지 않습니다. StableVITON 내부 일부 attention Linear module에 lightweight LoRA adapter를 삽입하고 LoRA parameter만 학습 대상으로 둡니다.

| Metric | Value |
| --- | ---: |
| inserted_lora_module_count | 8 |
| total_params | 1,838,680,959 |
| trainable_params_after_lora | 30,720 |
| trainable_ratio | about 0.00167% |

LoRA target module은 StableVITON UNet diffusion model 내부 transformer attention의 `to_q` Linear layer입니다.

Example target pattern:

```text
model.diffusion_model.input_blocks.*.transformer_blocks.0.attn*.to_q
```

   
## 🧪 Compared / Referenced VTON Models

이번 프로젝트는 StableVITON을 중심으로 학습 pipeline을 구축했지만, VTON 모델 후보를 검토하는 과정에서 IDM-VTON과 CATVITON/CATVTON 계열도 비교 대상으로 참고했습니다.

| Model | Role in This Project | Status |
| --- | --- | --- |
| StableVITON | Main training backbone | 10k layout, LoRA training, save/load smoke 검증 |
| IDM-VTON | Reference / baseline candidate | 구조 및 결과 비교 후보로 검토 |
| CATVITON / CATVTON | Reference / baseline candidate | artifact-aware VTON 비교 후보로 검토 |

현재 README 기준으로 실제 10k LoRA 학습과 실험 로그가 정리된 모델은 StableVITON입니다. IDM-VTON과 CATVITON/CATVTON은 후속 baseline comparison 대상으로 남겨둡니다.

## 📊 Experiments / Results

### Experiment 1. 10k Layout Validation

| Metric | Value |
| --- | ---: |
| train_count | 9995 |
| test_count | 0 |
| ready_count | 9995 |
| not_ready_count | 0 |

### Experiment 2. LoRA 100-Step Benchmark

| Metric | Value |
| --- | ---: |
| steps_completed | 100 |
| avg_step_time_sec | 1.4086 |
| final_loss | 0.3011031448841095 |
| loss_nan | false |
| peak_vram_mb | 8887.85 |

### Experiment 3. LoRA 9995-Step 1 Epoch-Equivalent Training

이 실행은 학습 루프가 정상적으로 동작하는지 검증하기 위한 실험입니다. 이 단계에서는 LoRA adapter나 생성 이미지를 저장하지 않았습니다.

| Metric | Value |
| --- | ---: |
| train_dataset_len | 9995 |
| steps_completed | 9995 |
| elapsed_sec | 9946.5927 |
| avg_step_time_sec | 0.9952 |
| first_loss | 0.06275913864374161 |
| final_loss | 0.626366138458252 |
| loss_nan | false |
| peak_vram_mb | 8887.85 |
| checkpoint_created | false |
| sample_created | false |

### Experiment 4. LoRA Adapter Save/Load Smoke

이 실행은 1-step 간단 검증을 통해 LoRA adapter가 저장되고 다시 불러와지는지 확인한 실험입니다. 착장 품질 비교 실험은 아닙니다.

| Metric | Save | Load |
| --- | ---: | ---: |
| status | success | success |
| steps_completed | 1 | 1 |
| loss_nan | false | false |
| lora_adapter_saved | true | false |
| lora_adapter_loaded | false | true |
| key_count | 16 | 16 |
| file_size_mb | 0.1236 | 0.1236 |
| missing_keys | - | `[]` |
| unexpected_keys | - | `[]` |
| shape_mismatch_keys | - | `[]` |
| peak_vram_mb | 8887.85 | 8887.85 |

### Experiment 5. 10k 9995-Step LoRA Adapter Save

이 실험은 9995개 train layout에서 LoRA adapter를 저장하는 run입니다.  
전체 StableVITON checkpoint를 저장하지 않고, `.lora_down`, `.lora_up`에 해당하는 LoRA parameter만 저장했습니다.

생성된 `lora_adapter.pt`는 Git에 포함하지 않습니다.

| Metric | Value |
| --- | ---: |
| status | success |
| train_dataset_len | 9995 |
| steps_completed | 9995 |
| elapsed_sec | 10720.0626 |
| avg_step_time_sec | 1.0725 |
| first_loss | 0.9184726476669312 |
| final_loss | 0.3207787275314331 |
| loss_nan | false |
| lora_adapter_saved | true |
| lora_state_dict_key_count | 16 |
| adapter_file_size_mb | 0.1236 |
| peak_vram_mb | 8887.85 |
| checkpoint_created | false |
| sample_created | false |
| Git included | false |

### Experiment 6. Demo Pair Quality Score Comparison

이 실험은 동일한 demo pair에 대해 StableVITON baseline과 StableVITON + LoRA 결과를 비교한 UI-level quality score입니다.

Saved LoRA adapter inference smoke도 같은 pair 기준으로 실행했습니다. 생성된 결과 이미지는 `backend/training/outputs/**` 하위 로컬 경로에만 저장되며, 저장소에는 포함하지 않습니다.

| Inference Item | StableVITON Baseline | StableVITON + Saved LoRA |
| --- | ---: | ---: |
| pair_id | `EP00000011` | `EP00000011` |
| status | success | success |
| denoise_steps | 50 | 50 |
| output_count | 1 | 1 |
| elapsed_sec | 22.5637 | 18.5134 |
| peak_vram_mb | 7839.65 | 7857.1 |
| lora_adapter_loaded | false | true |
| lora_adapter_loaded_key_count | 0 | 16 |
 
> LoRA가 일반적으로 모든 입력에서 성능을 개선한다고 결론 내리기 위해서는 추가적인 test set 기반 정량 평가가 필요합니다.

| Metric | StableVITON | StableVITON + LoRA | Diff |
| --- | ---: | ---: | ---: |
| Overall Confidence | 72 | 86 | +14 |
| Shoulder Alignment | 74 | 88 | +14 |
| Graphic Preservation | 69 | 87 | +18 |
| Sleeve Boundary | 68 | 84 | +16 |
| Hem Stability | 71 | 85 | +14 |
| Color Consistency | 76 | 88 | +12 |
| Pose Robustness | 70 | 84 | +14 |

#### Interpretation

StableVITON + LoRA 결과는 demo pair 기준으로 모든 세부 항목에서 baseline보다 높은 점수를 보였습니다.

가장 큰 차이는 `Graphic Preservation(+18)`과 `Sleeve Boundary(+16)`에서 나타났습니다.  
이는 LoRA 결과가 전면 그래픽의 중심 위치와 선명도, 소매 경계 분리에서 더 안정적인 결과를 보였다는 것을 의미합니다.

다만 이 결과는 하나의 demo pair 기준 비교이므로, 모델의 일반적인 성능 향상을 주장하기보다는 “artifact-aware LoRA 결과를 설명 가능한 UI로 비교할 수 있다”는 점을 보여주는 근거로 사용합니다.

#### Metric Meaning

이번 데모에서 사용한 score는 모델 성능을 일반화하기 위한 공식 benchmark가 아니라, 결과 이미지의 차이를 설명하기 위한 보조 지표입니다.

특히 VTON 결과에서는 다음과 같은 실패가 자주 발생할 수 있습니다.

- 의류 어깨선이 사람 어깨 위치와 맞지 않음
- 소매와 팔 영역이 섞여 경계가 흐려짐
- 전면 그래픽이 찌그러지거나 중심에서 벗어남
- 상의 밑단이 몸통 형태와 맞지 않게 깨짐
- 입력 의류 색상이 결과에서 과하게 변함
- 비정면 자세나 가림이 있는 경우 옷의 위치가 불안정해짐

따라서 `Shoulder Alignment`, `Graphic Preservation`, `Sleeve Boundary`, `Hem Stability` 같은 항목은 단순 점수라기보다, 사용자가 결과 이미지를 볼 때 확인해야 하는 주요 실패 지점을 정리한 기준입니다.

#### Visual Failure Cases Considered

Demo pair comparison에서는 단순히 confidence score만 비교하지 않고, VTON 결과에서 자주 발생하는 시각적 실패 유형을 기준으로 결과를 확인했습니다.

| Failure Type | Description |
| --- | --- |
| Shoulder Drift | 생성된 의류 어깨선이 사람 어깨보다 위/아래 또는 좌/우로 밀리는 현상 |
| Sleeve Bleeding | 소매 영역이 팔이나 배경과 섞여 경계가 흐려지는 현상 |
| Texture Distortion | 입력 의류의 그래픽, 로고, 패턴이 찌그러지거나 사라지는 현상 |
| Hem Collapse | 상의 밑단이 몸통 형태와 맞지 않게 접히거나 무너지는 현상 |
| Color Shift | 입력 의류의 색상이 생성 결과에서 크게 달라지는 현상 |
| Pose-sensitive Artifacts | 팔 위치, 비정면 자세, 가림 요소에 따라 결과가 불안정해지는 현상 |

이 기준들은 모델의 절대 성능을 평가하기 위한 공식 metric은 아니지만, 사용자가 실제 결과 이미지를 볼 때 어느 부분을 확인해야 하는지 설명하기 위한 기준으로 사용했습니다.

### Experiment 7. LoRA Rank / Module Ablation

고도화 실험으로 LoRA rank와 target module 수를 조정한 ablation을 진행했습니다.
학습 과정에서 생성된 LoRA 어댑터, 로그, 요약 파일, contact sheet 이미지는 `backend/training/outputs/**` 하위 로컬 경로에만 저장되며, 저장소에는 포함하지 않습니다.

| Metric | rank4-module8 | rank8-module8 | rank8-module16 |
| --- | ---: | ---: | ---: |
| steps_completed | 9995 | 9995 | 9995 |
| trainable_params_after_lora | 30720 | 61440 | 194560 |
| adapter_file_size_mb | 0.1236 | 0.2408 | 0.7546 |
| final_loss | 0.3207787275314331 | 0.2951800227165222 | 0.004082299303263426 |
| loss_nan | false | false | false |
| inference_pairs | 10 | 10 | 10 |
| inference_output_count | 10 | 10 | 10 |

Contact sheet 기준 정성 확인에서는 rank8-module16이 일부 pair에서 색 번짐과 과한 texture artifact가 더 눈에 띄었습니다. 현재 관찰 기준으로는 rank8-module8이 더 안정적인 후속 후보입니다.


## 🛠️ Troubleshooting / Lessons Learned

이번 프로젝트는 단순히 모델을 실행하는 것보다, 외부 VTON 모델과 자체 dataset/artifact pipeline을 실제 학습 흐름에 연결하는 과정이 핵심이었습니다.  
특히 데이터 수집, 이미지 전처리, StableVITON-compatible layout 구성, LoRA 학습 안정화, adapter 저장/로드 과정에서 여러 문제를 해결했습니다.

### 1. 데이터셋 확보와 artifact 구성 문제

| Item | Description |
| --- | --- |
| Problem | VTON 학습에는 사람 이미지와 의류 이미지만으로는 부족했고, pose, parsing, mask, DensePose 계열 artifact가 함께 필요했습니다. |
| Cause | StableVITON 계열 모델은 단순 image/cloth pair가 아니라 agnostic image, agnostic mask, cloth mask, densepose, openpose-json, image-parse 등 여러 보조 입력을 기대합니다. |
| Fix | AIHub 10k 기반으로 필요한 artifact를 수집/정리하고, strict artifact smoke를 통해 9995개 sample의 필수 파일 존재 여부를 검증했습니다. |
| Result | `checked_count=9995`, `artifact_errors=0`, `backend_loader_errors=0` 상태를 확보했습니다. |

### 2. 이미지 사이즈와 파일명 규칙 불일치

| Item | Description |
| --- | --- |
| Problem | AIHub 원본 이미지와 artifact의 해상도, 확장자, 파일명 규칙이 StableVITON 학습 코드가 기대하는 형식과 맞지 않았습니다. |
| Cause | StableVITON은 VITON-HD 스타일 layout과 특정 파일명 규칙을 기준으로 `image`, `cloth`, `agnostic-v3.2`, `agnostic-mask`, `cloth-mask`, `image-densepose`, `openpose-json`, `image-parse`, pair file을 읽습니다. |
| Fix | `prepare_stableviton_layout.py`를 통해 이미지 계열 파일을 StableVITON 입력 크기에 맞게 resize하고, mask 계열은 nearest-neighbor 방식으로 처리하여 label boundary가 깨지지 않도록 했습니다. 또한 pair file과 폴더 구조를 StableVITON-compatible format으로 재구성했습니다. |
| Result | `train_count=9995`, `ready_count=9995`, `not_ready_count=0`인 10k train-only layout을 구성했습니다. |

### 3. 10k layout 생성 중 전처리 속도 문제

| Item | Description |
| --- | --- |
| Problem | 9995개 sample 전체 artifact를 순수 copy 방식으로 생성할 때 시간이 오래 걸리고 timeout이 발생했습니다. |
| Cause | 이미지, mask, densepose, parsing, JSON 등 다수의 artifact를 모두 복사하면서 디스크 I/O 병목이 발생했습니다. |
| Fix | 학습 중 resize가 필요한 이미지 계열은 output layout에 실제 resized file로 저장하고, metadata 계열은 빠르게 처리하는 방식으로 최적화했습니다. 이후 runner가 이미 준비된 layout을 다시 수정하지 않도록 `--no-prepare-smoke-data` 옵션을 추가했습니다. |
| Result | 10k layout 준비 시간을 줄이고, 학습 단계와 전처리 단계를 분리했습니다. |

### 4. Source dataset 보호 문제

| Item | Description |
| --- | --- |
| Problem | 전처리 최적화 과정에서 hardlink를 사용할 경우 output layout 수정이 source dataset에 영향을 줄 수 있었습니다. |
| Cause | hardlink는 서로 다른 경로의 파일이 같은 실제 파일 데이터를 참조할 수 있기 때문에, output 쪽 파일을 수정하면 원본 dataset까지 영향을 받을 가능성이 있습니다. |
| Fix | runner가 resize/수정할 가능성이 있는 이미지 계열은 output layout에 별도 파일로 저장하고, source dataset은 read-only 기준으로만 사용했습니다. |
| Result | 실험 문서와 README에 `original dataset modified=false`를 명확히 기록했습니다. |

### 5. StableVITON 학습 환경과 checkpoint load 문제

| Item | Description |
| --- | --- |
| Problem | StableVITON 원본 학습 코드를 그대로 실행했을 때 local 환경에서 config, checkpoint, VAE load 관련 문제가 발생했습니다. |
| Cause | 외부 StableVITON repo의 checkpoint 경로, 모델 load 순서, local dependency version, dataset path가 우리 프로젝트 구조와 바로 맞지 않았습니다. |
| Fix | 외부 StableVITON repo는 직접 수정하지 않고, 우리 repo의 runner에서 StableVITON config와 checkpoint를 load하는 방식으로 smoke runner를 구성했습니다. 필요한 경우 smoke 실험에서는 VAE 추가 load를 생략했습니다. |
| Result | `VITONHD_PBE_pose.ckpt` load, model config load, 10k dataset load, train step 진입을 검증했습니다. |

### 6. 전체 fine-tuning 대신 LoRA로 학습 범위 축소

| Item | Description |
| --- | --- |
| Problem | StableVITON 전체 모델은 약 1.8B parameter 규모라서 전체 fine-tuning은 시간과 VRAM 부담이 컸습니다. |
| Cause | 전체 모델을 학습하면 실험 반복이 어렵고, 제한된 시간 안에 10k 학습을 완료하기 어렵습니다. |
| Fix | 일부 attention Linear module에만 LoRA adapter를 삽입하고, 기존 StableVITON parameter는 freeze했습니다. |
| Result | `inserted_lora_module_count=8`, `trainable_params_after_lora=30,720`, `trainable_ratio=about 0.00167%`로 학습 대상을 크게 줄였습니다. |

### 7. 9995-step 학습 가능 여부 판단 문제

| Item | Description |
| --- | --- |
| Problem | 10k 전체 9995-step 학습을 시간 안에 완료할 수 있을지 처음에는 불확실했습니다. |
| Cause | 1-step sanity는 model load 시간이 포함되어 실제 step time을 판단하기 어려웠습니다. |
| Fix | `1-step sanity → 100-step benchmark → 9995-step run` 순서로 단계적으로 검증했습니다. |
| Result | 100-step benchmark에서 `avg_step_time_sec=1.4086`을 확인했고, 이후 9995-step 1 epoch-equivalent training을 완료했습니다. 최종 결과는 `steps_completed=9995`, `avg_step_time_sec=0.9952`, `loss_nan=false`였습니다. |

### 8. Training loop는 성공했지만 adapter가 저장되지 않은 문제

| Item | Description |
| --- | --- |
| Problem | PR #107에서 9995-step LoRA training loop는 성공했지만, 학습된 LoRA adapter 파일은 생성되지 않았습니다. |
| Cause | 당시 runner는 training loop 검증에 집중했고, checkpoint/sample 저장을 비활성화한 상태였습니다. |
| Fix | 후속 작업에서 `--save-lora-path`, `--load-lora-path` 옵션을 추가하고, 전체 StableVITON checkpoint가 아니라 `.lora_down`, `.lora_up` parameter만 저장하도록 구현했습니다. |
| Result | 1-step save smoke에서 `lora_adapter_saved=true`, `lora_state_dict_key_count=16`, `adapter file size=0.1236MB`를 확인했고, 1-step load smoke에서 missing/unexpected/shape mismatch key 없이 load를 검증했습니다. |

### 9. Git에 대용량 artifact가 포함되는 문제 방지

| Item | Description |
| --- | --- |
| Problem | dataset, output, checkpoint, generated image, adapter `.pt` 파일이 Git에 포함되면 repository가 비대해지고 라이선스/제출 문제가 생길 수 있었습니다. |
| Cause | 실험 과정에서 `backend/datasets/**`, `backend/training/outputs/**`, generated image, checkpoint, `.pt` 파일이 계속 생성됩니다. |
| Fix | 각 PR마다 `git ls-files --others --exclude-standard`, `git status --ignored -s`, `git diff --check`를 확인하고, 코드와 문서만 commit했습니다. |
| Result | 실험 결과는 문서화하되, raw dataset/output/checkpoint/generated image는 Git에 포함하지 않는 정책을 유지했습니다. |

### Key Takeaways

- VTON 모델은 단순히 `person image + cloth image`만 준비한다고 바로 학습할 수 없고, pose, parsing, mask, DensePose 등 artifact 정합성이 중요했습니다.
- 외부 모델을 활용할 때는 모델 구조보다도 dataset layout, file naming rule, checkpoint path를 맞추는 과정이 큰 비중을 차지했습니다.
- 이미지 resize와 mask resize는 같은 방식으로 처리하면 안 되며, mask 계열은 label boundary가 깨지지 않도록 별도 처리해야 했습니다.
- 10k 전체 학습은 바로 실행하지 않고 `1-step sanity → 100-step benchmark → full run` 순서로 진행한 것이 안정적이었습니다.
- LoRA를 적용해 전체 StableVITON을 학습하지 않고도 trainable parameter를 크게 줄여 10k scale 실험을 완료할 수 있었습니다.
- Training loop success, adapter save/load success, inference quality improvement는 서로 다른 단계이므로 README에서 명확히 구분했습니다.



### Experiment 8. Fixed 100-Pair LoRA Comparison

10개 pair 중심의 빠른 ablation을 넘어, 동일한 `fixed_eval_100` pair set에서 4개 method를 비교했습니다.
이번 평가는 새 학습 없이 saved adapter inference만 수행한 결과입니다.

후속 contact sheet review에서 일부 person/target 입력 이미지가 EXIF orientation을 반영하지 못한 채 왼쪽으로 회전된 상태로 평가셋에 들어간 것을 확인했습니다. 이후 raw AIHub artifact dataset에서 `fixed_eval_100` 100개 pair만 직접 EXIF 보정해 평가셋을 재생성했고, baseline / rank4 / rank8-module8 / rank8-module16 inference와 metric을 다시 실행했습니다.

| Method | output_count | failure_count | success_rate | PSNR mean | SSIM mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| StableVITON baseline | 100 | 0 | 1.0 | 18.863788 | 0.634995 |
| rank4-module8 | 100 | 0 | 1.0 | 18.813872 | 0.628672 |
| rank8-module8 | 100 | 0 | 1.0 | 18.874149 | 0.635203 |
| rank8-module16 | 100 | 0 | 1.0 | 18.964847 | 0.636894 |

LPIPS는 현재 PC3 `vton` 환경에 설치되어 있지 않아 skip했습니다. EXIF 보정 후 PSNR/SSIM 기준으로는 `rank8-module16`이 가장 높지만, 2x contact sheet 기준 visual review에서는 일부 pair에서 haze, side ghost, floating garment patch가 보였습니다. 따라서 최종 demo 후보는 metric top만으로 고르지 않고 pair별 visual pass/fail을 함께 봐야 합니다.

Generated output, raw metric CSV/JSON, contact sheet image, adapter file은 모두 `backend/training/outputs/**` 하위 local path에만 저장했고 Git에는 포함하지 않았습니다.

상세 기록: [fixed 100-pair LoRA comparison](docs/experiments/pc3_fixed_eval_100_lora_comparison.md)

## ✅ Results Status

### 완료한 작업

- AIHub 10k full artifact dataset readiness
- StableVITON-compatible 9995-sample train layout
- StableVITON `train.py` compatibility smoke
- LoRA runner with 8 inserted modules
- 9995-step 1 epoch-equivalent training loop
- LoRA adapter save/load 1-step smoke
- Demo compare backend API skeleton
- Next.js demo compare page structure
- 9995-step adapter save result
- Saved 10k adapter based inference
- Baseline StableVITON vs LoRA generated image comparison
- LoRA rank/module ablation training
- fixed_eval_100 4-method inference comparison
- 10-pair baseline/rank4/rank8 inference comparison
- Final demo video in README

## 🚀 실행 방법

아래 명령은 다음 환경을 기준으로 합니다.

- 운영체제: Windows / PowerShell
- Conda 환경: `D:\conda-envs\vton`
- 외부 StableVITON 저장소: `D:\GitHub\StableVITON`
- 로컬 dataset root는 별도로 준비되어 있어야 하며 Git에는 포함하지 않습니다.

### 1-step LoRA adapter 저장 smoke

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_save_load_1step_save `
  --max-steps 1 `
  --batch-size 1 `
  --max-lora-modules 8 `
  --no-prepare-smoke-data `
  --save-lora-path D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_save_load_1step_save\lora_adapter.pt
```

### 1-step LoRA adapter load smoke

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_save_load_1step_load `
  --max-steps 1 `
  --batch-size 1 `
  --max-lora-modules 8 `
  --no-prepare-smoke-data `
  --load-lora-path D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_save_load_1step_save\lora_adapter.pt
```

### 9995-step LoRA adapter 저장 run

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py `
  --data-root D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_10k_train `
  --output-root D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_10k_adapter_save `
  --max-steps 9995 `
  --batch-size 1 `
  --max-lora-modules 8 `
  --no-prepare-smoke-data `
  --save-lora-path D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_10k_adapter_save\lora_adapter.pt
```

생성되는 `lora_adapter.pt`는 Git에 포함하지 않습니다.

### Backend API 실행

```powershell
cd backend
python -m uvicorn backend.app.main:app --reload
```

현재 준비된 API route는 다음과 같습니다.

- `GET /api/health`
- `POST /api/tryon`
- `GET /api/job/{job_id}`
- `GET /api/result/{job_id}`
- `GET /api/demo/samples`
- `GET /api/demo/artifact-compare/{pair_id}`
- `GET /api/demo/model-compare/{pair_id}`

### Frontend 실행

```powershell
cd frontend
npm install
npm run dev
```

현재 frontend 방향은 다음과 같습니다.

- Next.js 기반 demo UI
- `/model-compare` route
- `/model-compare` 중심의 StableVITON baseline vs StableVITON LoRA comparison UI
- confidence badge, fit explanation, detailed analysis tab, hotspot overlay 구조 준비
- 실제 생성 비교 이미지는 아직 Git에 포함하지 않음
- 
## 🗂️ 프로젝트 구조

```text
fit-reasoning-vton/
  README.md
  backend/
    app/
      api/
        demo.py
        health.py
        tryon.py
      schemas/
      services/
      workers/
    demo/
      analysis/
      samples/
      assets/
    training/
      datasets/
      scripts/
        prepare_stableviton_layout.py
        run_stableviton_lora_tiny_smoke.py
        smoke_test_lora_dataset.py
        dataloader_dry_run.py
  frontend/
    src/
      app/
        model-compare/
        artifact-compare/
      components/
        demo/
  docs/
    experiments/
    setup/
    aihub/
    data/
  scripts/
```

## 📚 문서 링크

- [StableVITON LoRA 10k epoch pilot](docs/experiments/pc3_stableviton_lora_10k_epoch_pilot.md)
- [LoRA save/load smoke and inference comparison prep](docs/experiments/pc3_stableviton_lora_save_load_inference_comparison.md)
- [fixed 100-pair LoRA comparison](docs/experiments/pc3_fixed_eval_100_lora_comparison.md)
- [10k full artifact smoke and training log](docs/experiments/pc3_lora_10k_full_artifact_smoke_and_training.md)
- [StableVITON AIHub layout prepare](docs/experiments/stableviton_aihub_layout_prepare.md)
- [Demo backend API contract](docs/experiments/demo_backend_api_contract.md)
- [Demo asset package contract](docs/experiments/demo_asset_package_contract.md)

## 🔒 Git 및 데이터 관리 정책

이 저장소에는 다음 항목을 포함하지 않습니다.

- `backend/datasets/**`
- `backend/training/outputs/**`
- `backend/outputs/**`
- `backend/logs/**`
- `backend/demo/assets/**`
- `*.pt`, `*.pth`, `*.ckpt`, `*.safetensors`
- generated image
- large archive
- raw AIHub data

Git에는 source code, schema, script, 문서, 작은 예시 JSON만 포함하는 것을 원칙으로 합니다.

## ⚠️ 한계점

- 현재 결과는 demo pair 중심의 비교이므로, 더 다양한 pose, category, occlusion 조건에서의 추가 평가는 향후 작업으로 남겨둡니다.
- Fit confidence, fit explanation, hotspot annotation은 시스템 목표와 UI/API 방향으로 준비되어 있지만, 최종 모델 기반 reasoning output과의 통합은 추가 작업이 필요합니다.
- Dataset과 output artifact는 용량 및 라이선스 문제로 Git에 포함하지 않습니다.
- Demo pair quality score는 특정 입력 쌍에 대한 UI-level 비교 결과이며, 전체 test set에 대한 정량 benchmark는 아직 수행하지 않았습니다.
- 현재 화면의 fit/reliability score는 demo comparison을 설명하기 위한 지표이므로, 모델의 일반적인 성능 개선을 주장하려면 더 많은 pair에 대한 반복 평가가 필요합니다.

## 🛣️ 향후 작업

- 동일 person-cloth pair 기준 StableVITON, IDM-VTON, CATVITON/CATVTON 비교
- StableVITON baseline, StableVITON+LoRA, IDM-VTON, CATVITON/CATVTON 정성 비교표 작성
- 의류 경계, pose alignment, body distortion, failure case 분석
- 최소 3개 demo pair를 local `backend/demo/assets/**`에 구성
- demo asset strict validation 실행
- 최종 비교 이미지를 demo compare UI에 연결
- README에 demo GIF 또는 video link 추가
- fit confidence, explanation, hotspot annotation을 최종 user flow와 연결


## 🙏 참고자료 및 출처

이 프로젝트는 아래 연구와 도구를 참고하거나 기반으로 구성했습니다.  
외부 model code, pretrained weight, dataset, generated asset은 이 저장소에 재배포하지 않습니다.

- StableVITON: Kim et al., “StableVITON: Learning Semantic Correspondence with Latent Diffusion Model for Virtual Try-On,” CVPR 2024. [GitHub](https://github.com/rlawjdghek/StableVITON), [arXiv](https://arxiv.org/abs/2312.01725)
- IDM-VTON: Choi et al., “Improving Diffusion Models for Authentic Virtual Try-on in the Wild,” ECCV 2024. 후속 baseline comparison 후보로 참고했습니다. [Project](https://idm-vton.github.io/), [GitHub](https://github.com/yisol/IDM-VTON), [arXiv](https://arxiv.org/abs/2403.05139)
- CatVTON / CATVITON: “CatVTON: Concatenation Is All You Need for Virtual Try-On with Diffusion Models,” ICLR 2025. 후속 artifact-aware VTON comparison 후보로 참고했습니다. [GitHub](https://github.com/Zheng-Chong/CatVTON), [arXiv](https://arxiv.org/abs/2407.15886)
- LoRA: Hu et al., “LoRA: Low-Rank Adaptation of Large Language Models,” ICLR 2022. [arXiv](https://arxiv.org/abs/2106.09685)
- AIHub 쉐이프리스 의류 및 포즈 데이터. [AIHub dataset page](https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=115&dataSetSn=71535&topMenu=)
- DensePose: Guler et al., “DensePose: Dense Human Pose Estimation In The Wild,” CVPR 2018. [Project page](https://densepose.org/), [arXiv](https://arxiv.org/abs/1802.00434)
- OpenPose: CMU Perceptual Computing Lab OpenPose repository and related pose estimation papers. [GitHub](https://github.com/CMU-Perceptual-Computing-Lab/openpose)
- PyTorch, PyTorch Lightning, FastAPI, Next.js, React, TypeScript 등 open-source tooling을 training/backend/frontend pipeline 구성에 사용했습니다.


## 📄 License

The source code and documentation written in this repository are released under the MIT License.

External model code, pretrained weights, datasets, and generated assets are not redistributed in this repository and remain subject to their original licenses or terms of use.

See [LICENSE](LICENSE) for details. 
