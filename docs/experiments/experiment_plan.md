# 실험 계획

## 목적

본 프로젝트의 실험은 IDM-VTON을 main baseline으로 실행하고, 생성 결과를 Fit-aware Reasoning Layer가 얼마나 설명 가능하게 분석할 수 있는지 확인하는 데 초점을 둔다.

CatVTON은 optional comparison baseline으로 유지한다. 비교 결과는 실제 smoke test 또는 inference를 수행한 뒤에만 기록한다.

## 실험 흐름

1. 외부 IDM-VTON 환경을 구성한다.
2. 샘플 person image와 garment image로 smoke test를 수행한다.
3. 생성된 착장 결과를 웹 화면에 표시한다.
4. 입력 품질 평가 후보 feature를 정의한다.
5. 착장 결과 신뢰도 평가 후보 feature를 정의한다.
6. 기장감, 품 여유, 소매 길이, 어깨선 등 rule-based fit reasoning을 설계한다.
7. 성공/실패 사례를 실제 실행 결과 기준으로 정리한다.
8. 시간이 허용되면 CatVTON 결과와 비교한다.

## 실험 A. IDM-VTON Smoke Test

- 입력: person image, garment image
- 출력: IDM-VTON generated image
- 목적: main baseline이 최소 샘플에서 실행 가능한지 확인
- 결과 기록: 실제 실행 후 로그 템플릿에 작성

## 실험 B. 입력 품질 평가

- 입력: person image, garment image
- 출력: input quality score 후보
- 목적: 입력 문제로 인한 실패 가능성을 설명

## 실험 C. 착장 결과 신뢰도 평가

- 입력: generated image와 필요 시 입력 이미지
- 출력: fit confidence score 후보
- 목적: 생성 결과가 사용자가 신뢰할 만한지 설명

## 실험 D. Fit Reasoning

- 입력: 컴퓨터비전 기반 feature
- 출력: 기장감, 품 여유, 소매 길이, 어깨선에 대한 간단한 설명
- 목적: 생성 결과의 핏 경향을 사람이 이해할 수 있는 문장으로 제공

## 실험 E. Optional CatVTON Comparison

- 입력: 같은 person image와 garment image
- 출력: CatVTON generated image
- 목적: main baseline인 IDM-VTON과 optional comparison baseline인 CatVTON의 결과를 비교
- 주의: 실제 실행 전에는 결과나 성능 수치를 작성하지 않는다.

## 결과 기록 원칙

현재 문서에는 실제 실험 결과를 작성하지 않는다. 실험 완료 후 결과, 수치, 실패 사례, 해석을 별도 로그에 기록한다.

## 향후 작성 항목

- smoke test 결과
- feature 정의 확정
- confidence score 계산 방식
- fit reasoning 문장 규칙
- 성공/실패 사례
