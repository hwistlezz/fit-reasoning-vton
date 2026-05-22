# 프로젝트 개요

## 프로젝트명

**Fit-Confidence Virtual Try-On**

**체형·핏 신뢰도 평가를 제공하는 가상 착장 웹 시스템**

## 프로젝트 목표

이 프로젝트는 사람 이미지와 의류 이미지를 입력받아 가상 착장 결과 이미지를 생성하고, 그 결과가 얼마나 신뢰 가능한지 컴퓨터비전 특징 기반으로 평가하는 웹 시스템을 목표로 한다.

기존 가상 착장 모델의 결과를 해석하는 **Fit-aware Reasoning Layer**이다.

## 문제 정의

기존 가상 착장 모델은 이미지를 생성하지만, 생성 결과가 신뢰 가능한지 또는 어떤 부분이 어색한지 설명하지 못하는 경우가 많다. 사용자는 결과 이미지가 성공적인지, 입력 이미지 품질이 낮아서 실패했는지, 포즈나 세그멘테이션이 불안정한지 판단하기 어렵다.

본 프로젝트는 생성 이미지와 함께 입력 품질 점수, 착장 결과 신뢰도 점수, 간단한 핏 해석, 실패 원인을 제공하는 방향을 다룬다.

## 핵심 파이프라인

1. 사람 이미지와 의류 이미지를 입력받는다.
2. IDM-VTON을 main baseline으로 사용해 가상 착장 이미지를 생성한다.
3. CatVTON은 optional comparison baseline으로 유지한다.
4. 포즈, 세그멘테이션, 실루엣, 의류 보존 정도를 분석한다.
5. 입력 품질 점수와 착장 결과 신뢰도 점수를 계산한다.
6. 기장감, 품 여유, 소매 길이, 어깨선 등 간단한 핏 해석을 제공한다.
7. 웹 화면에서 착장 이미지, 신뢰도 점수, 핏 해석, 실패 원인을 보여준다.

## Fit-Aware Reasoning Layer

초기 후보 분석 요소는 다음과 같다.

- `pose_quality`: 사람 이미지의 자세 안정성
- `segmentation_quality`: 사람/의류 영역 분리 안정성
- `silhouette_consistency`: 착장 전후 실루엣 변화의 자연스러움
- `garment_preservation`: 의류 색상, 패턴, 형태 보존 정도
- `length_tendency`: 기장감 경향
- `roominess_tendency`: 품 여유 경향
- `sleeve_length_tendency`: 소매 길이 경향
- `shoulder_line_tendency`: 어깨선 경향

현재 문서 단계에서는 feature extraction 알고리즘을 구현하지 않는다. 실제 계산 방식은 smoke test 결과와 사용 가능한 pose, segmentation, parsing 도구를 확인한 뒤 결정한다.

## 모델 사용 방향

### IDM-VTON

IDM-VTON은 이번 텀프로젝트의 main baseline이다. 한 달 안에 작동하는 웹 데모를 만들기 위해 우선 실행 대상으로 둔다.

### CatVTON

CatVTON은 삭제하지 않고 optional comparison baseline으로 유지한다. 가능하면 같은 샘플에 대해 IDM-VTON 결과와 비교하지만, 이번 텀프로젝트의 필수 구현 대상은 아니다.

### StableVITON

StableVITON은 이번 텀프로젝트의 필수 구현 대상이 아니다. 후속 캡스톤 확장 또는 research extension으로 언급한다.

## 명확한 비목표

- 실제 신체 치수 예측
- 정확한 의류 사이즈 추천
- VTON 모델을 처음부터 학습
- CatVTON 직접 파인튜닝
- 대규모 FIT 데이터셋 전체 학습
- StableVITON 필수 구현
- 검증되지 않은 성능 수치 제시

## 산출물

- proposal 제출용 README
- 외부 baseline 설정 문서
- smoke test 로그 템플릿
- 웹 데모 구현 계획
- 입력 품질 평가 및 fit confidence score 설계
- fit reasoning 문장 생성 계획
- 성공/실패 사례 정리 계획
