# 데이터셋 계획

## 기본 데이터셋

초기 baseline inference와 평가에는 VITON-HD를 우선 사용한다. DressCode는 프로젝트 일정과 데이터 사용 조건을 검토한 뒤 선택적으로 사용한다.

## VITON-HD 사용 목적

- CatVTON baseline inference 입력
- person image와 garment image 조합 구성
- real paired target이 있는 샘플의 평가 기준 확보
- fit-aware feature와 pseudo label 분석용 샘플 생성

## DressCode 사용 목적

DressCode는 다양한 의류 카테고리 분석이 필요한 경우 선택적으로 사용한다. 사용 전 라이선스, 데이터 구조, CatVTON 입력 호환성을 확인한다.

## 데이터 구분

본 프로젝트에서는 target 데이터를 다음처럼 구분한다.

- real paired target: 실제 사람이 해당 garment를 착용한 원본 정답 이미지
- pseudo target: CatVTON이 생성한 virtual try-on 결과 이미지

이 두 항목은 실험 의미가 다르므로 같은 정답처럼 취급하지 않는다.

## 데이터 분할 원칙

- train, validation, test 분리를 명확히 기록한다.
- 같은 person 또는 같은 garment가 서로 다른 split에 중복되어 누수되는지 확인한다.
- gold set은 별도로 관리하고, 최종 신뢰도 평가에 사용한다.

## 커밋 금지 항목

- 원본 데이터셋 이미지
- 생성된 virtual try-on 이미지
- segmentation mask, pose map 등 대용량 중간 산출물
- annotation 원본 파일 중 공개가 제한된 파일
- 압축 데이터셋 파일

## 향후 작성 항목

- 실제 데이터셋 다운로드 경로
- 데이터 사용 허가 조건
- 샘플 수
- split 기준
- 전처리 규칙
