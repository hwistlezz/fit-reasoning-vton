# 실험 계획

## 목적

본 프로젝트의 실험은 CatVTON baseline 생성 결과를 분석하고, fit-aware visual feature와 pseudo label이 얼마나 신뢰할 수 있는지 검증하는 데 초점을 둔다.

## 실험 흐름

1. pretrained CatVTON으로 baseline 결과를 생성한다.
2. baseline 결과를 real paired target과 비교한다.
3. fit-aware visual feature 후보를 정의한다.
4. rule-based pseudo label을 생성한다.
5. 사람이 검수한 gold set을 구축한다.
6. rule-based labeling과 feature-based classifier를 비교한다.
7. 분석 신뢰도를 계산한다.
8. overlay visualization과 자연어 설명을 생성한다.

## 실험 A. CatVTON Baseline 평가

- 입력: person image, garment image
- 출력: CatVTON generated image
- 비교 대상: real paired target
- 목적: baseline의 생성 품질과 fit-aware 분석 가능성 확인

## 실험 B. Rule-Based Labeling

- 입력: fit-aware visual feature
- 출력: pseudo fit label
- 목적: 해석 가능한 규칙 기반 라벨링 기준 수립

## 실험 C. Feature-Based Classifier

- 입력: fit-aware visual feature vector
- 출력: fit label prediction
- 목적: 규칙 기반 방식과 학습 기반 방식 비교

## 실험 D. Gold Set Reliability

- 입력: 사람이 검수한 gold label
- 출력: pseudo label 또는 classifier prediction과의 일치도
- 목적: 분석 결과의 신뢰도 측정

## 결과 기록 원칙

현재 문서에는 실제 실험 결과를 작성하지 않는다. 실험 완료 후 결과, 수치, 실패 사례, 해석을 별도 로그에 기록한다.

## 향후 작성 항목

- feature 정의 확정
- metric 정의
- gold set 규모
- classifier 후보 모델
- reliability 계산 방식
- 실제 실험 결과
