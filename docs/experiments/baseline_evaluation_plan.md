# Baseline 평가 계획

## 목적

pretrained CatVTON으로 생성한 baseline virtual try-on 결과를 평가한다. 평가는 생성 품질 자체와 fit-aware 분석 가능성을 함께 확인한다.

## 입력과 출력

- 입력: person image, garment image
- 생성 출력: CatVTON pseudo target
- 비교 기준: real paired target

## 평가 관점

### 생성 품질

- garment identity 유지 여부
- person identity 유지 여부
- 큰 왜곡 또는 artifact 여부
- 의류 영역 경계 품질
- 자세 변화에 대한 안정성

### Fit-Aware 분석 가능성

- 의류 폭을 시각적으로 비교할 수 있는지
- 밑단 위치가 안정적으로 관찰되는지
- 어깨선 또는 실루엣 경계가 추출 가능한지
- segmentation 또는 parsing 오류가 feature에 미치는 영향이 큰지

## 정량 지표 후보

정량 지표는 실제 실험 설계 후 확정한다. 후보는 다음과 같다.

- 이미지 유사도 계열 지표
- garment 영역 중심의 품질 지표
- gold set label과 pseudo label의 일치도
- feature 안정성 지표

현재 단계에서는 실제 수치를 작성하지 않는다.

## 정성 평가 기준

- 성공
- 부분 성공
- 실패
- 분석 제외

각 기준의 세부 정의는 baseline 샘플 검토 후 확정한다.

## 향후 작성 항목

- 평가 샘플링 기준
- metric 구현 파일
- gold set 평가 절차
- 실제 baseline 결과 표
- 주요 실패 사례
