# Baseline 평가 계획

## 목적

IDM-VTON을 main baseline으로 사용해 생성한 virtual try-on 결과를 확인하고, Fit-aware Reasoning Layer가 분석할 수 있는 신뢰도 평가 항목을 정리한다.

CatVTON은 optional comparison baseline으로 유지한다.

## 입력과 출력

- 입력: person image, garment image
- main baseline 출력: IDM-VTON generated image
- optional comparison 출력: CatVTON generated image

## 평가 관점

### 입력 품질

- 사람 이미지에서 포즈가 안정적인지
- 신체 또는 의류 영역이 심하게 가려지지 않았는지
- 이미지가 지나치게 잘리거나 흐리지 않은지
- 의류 이미지에서 옷의 형태가 충분히 드러나는지

### 생성 결과 신뢰도

- 사람의 포즈와 실루엣이 크게 무너지지 않았는지
- 의류 색상, 패턴, 형태가 보존되었는지
- 어깨선, 소매, 밑단 등 주요 위치가 자연스러운지
- 생성 artifact가 설명 가능한 수준인지

### Fit-Aware 분석 가능성

- 기장감을 시각적으로 비교할 수 있는지
- 품 여유를 실루엣 기반으로 추정할 수 있는지
- 소매 길이와 어깨선이 안정적으로 관찰되는지
- segmentation 또는 parsing 오류가 confidence score에 미치는 영향이 큰지

## 정량 지표 후보

정량 지표는 실제 구현 후 확정한다. 후보는 다음과 같다.

- input quality score
- fit confidence score
- garment preservation score
- pose consistency score
- silhouette consistency score

현재 단계에서는 실제 수치를 작성하지 않는다.

## 정성 평가 기준

- 성공
- 부분 성공
- 실패
- 분석 제외

각 기준의 세부 정의는 실제 smoke test 샘플 검토 후 확정한다.

## 향후 작성 항목

- 평가 샘플링 기준
- confidence score 구현 파일
- 실제 baseline 결과 표
- 주요 실패 사례
