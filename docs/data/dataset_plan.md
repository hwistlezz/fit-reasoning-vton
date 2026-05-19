# 데이터셋 계획

## 목적

이번 텀프로젝트에서는 완성된 대규모 학습 데이터셋을 구축하는 것이 아니라, 웹 데모와 Fit-aware Reasoning Layer 검증에 필요한 소규모 샘플을 준비하는 것을 우선한다.

## 데이터 사용 방향

우선순위는 다음과 같다.

1. 직접 촬영한 소규모 person image와 garment image
2. 공개 데이터셋 후보 검토
3. 필요한 경우 VITON-HD 또는 DressCode 일부 샘플 검토
4. FIT 데이터셋 기반 fit-aware scoring은 후속 확장 방향으로 검토

FIT 데이터셋을 이번 텀프로젝트에서 바로 사용할 수 있다고 단정하지 않는다. 사용 가능 여부, 접근 조건, 라이선스, 데이터 구조를 먼저 확인해야 한다.

## VITON-HD와 DressCode

VITON-HD와 DressCode는 후보 데이터셋이다. 사용 전 각 원 배포처의 라이선스와 사용 조건을 확인한다.

이 데이터셋들은 다음 목적으로 검토할 수 있다.

- 외부 VTON baseline 입력 형식 확인
- person image와 garment image pair 예시 검토
- pseudo target과 real paired target 개념 정리
- 후속 비교 실험 계획 수립

## 데이터 구분

본 프로젝트에서는 target 데이터를 다음처럼 구분한다.

- real paired target: 실제 사람이 해당 garment를 착용한 원본 정답 이미지
- pseudo target: IDM-VTON 또는 CatVTON 같은 VTON 모델이 생성한 virtual try-on 결과 이미지

두 항목은 실험 의미가 다르므로 같은 정답처럼 취급하지 않는다.

## 커밋 금지 항목

- 원본 데이터셋 이미지
- 직접 촬영한 원본 이미지 중 공개 권한이 불명확한 파일
- 생성된 virtual try-on 이미지
- segmentation mask, pose map 등 대용량 중간 산출물
- annotation 원본 파일 중 공개가 제한된 파일
- checkpoint 및 model weight
- 압축 데이터셋 파일

## 향후 작성 항목

- 직접 촬영 샘플 수집 기준
- 샘플 이미지 공개 가능 여부
- 데이터 사용 허가 조건
- 전처리 규칙
- 웹 데모용 최소 샘플 구성
