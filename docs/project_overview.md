# 프로젝트 개요

## 프로젝트 목표

이 프로젝트는 CatVTON 기반 가상 착용 결과를 분석하여, 의류가 사람 이미지에서 어떤 시각적 핏 경향을 보이는지 설명하는 시스템을 구축하는 것을 목표로 한다.

핵심 목표는 실제 신체 치수나 정확한 의류 사이즈 예측이 아니다. 본 프로젝트는 생성된 virtual try-on 결과에서 관찰 가능한 시각적 패턴을 바탕으로 `slim`, `regular`, `oversized`와 같은 핏 경향을 분석한다.

## 문제 정의

가상 착용 모델은 착용 결과 이미지를 생성하지만, 사용자가 그 결과를 해석하기 위해서는 별도의 설명이 필요하다. 본 프로젝트는 생성 이미지에서 의류의 폭, 길이, 실루엣, 어깨선, 밑단 위치 등 시각적 단서를 추출하고 이를 사람이 이해할 수 있는 설명으로 변환한다.

## 핵심 파이프라인

1. pretrained CatVTON을 baseline으로 사용한다.
2. NVIDIA A100 GPU에서 대규모 inference를 수행한다.
3. VITON-HD 및 선택적으로 DressCode 데이터셋을 사용해 virtual try-on 결과를 생성한다.
4. CatVTON baseline 결과를 평가한다.
5. paired data 기반 fine-tuning 실험 계획을 수립한다.
6. real paired target과 CatVTON pseudo target을 명확히 구분한다.
7. fit-aware visual feature를 추출한다.
8. pseudo fit label을 생성한다.
9. 사람이 검수한 gold set을 구축한다.
10. rule-based labeling과 feature-based classifier를 비교한다.
11. 분석 신뢰도를 계산한다.
12. overlay visualization과 자연어 설명을 제공한다.
13. 이후 Fit Report UI로 확장한다.

## Fit-Aware Visual Features

초기 후보 특징은 다음과 같다.

- `width_ratio`: 의류 폭과 기준 인체 영역의 상대 비율
- `length_ratio`: 의류 길이와 기준 인체 영역의 상대 비율
- `silhouette_ratio`: 착용 결과의 실루엣 확장 정도
- `shoulder_ratio`: 어깨선 또는 상의 어깨 폭의 상대 비율
- `hem_position`: 밑단 위치의 상대적 위치

이 문서 단계에서는 특징 추출 알고리즘을 구현하지 않는다. 실제 계산 방식은 segmentation, keypoint, garment parsing 결과를 검토한 뒤 별도 설계한다.

## Pseudo Fit Labels

초기 pseudo label 후보는 다음과 같다.

- `overall_fit`: `slim`, `regular`, `oversized`
- `length_label`: `short`, `normal`, `long`
- `roominess_label`: `tight`, `regular`, `roomy`

pseudo label은 실제 정답이 아니라 실험용 약한 라벨이다. 최종 평가에는 사람이 검수한 gold set을 사용한다.

## 명확한 비목표

- 실제 신체 치수 예측
- 정확한 의류 사이즈 추천
- 의료적 또는 인체 측정학적 판단
- 검증되지 않은 수치 결과 제시
- CatVTON 원본 코드를 이 저장소에 복사하는 방식

## 산출물

- 데이터셋 구성 및 정책 문서
- CatVTON baseline 평가 계획
- fine-tuning 실험 계획
- fit-aware feature 설계 문서
- pseudo label 및 gold set 구축 계획
- overlay visualization 및 자연어 설명 설계
- 향후 Fit Report UI 설계 기반
