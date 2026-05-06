# Fine-Tuning 계획

## 목적

paired data를 활용하여 CatVTON baseline 대비 fine-tuning의 효과를 평가할 실험 계획을 수립한다. 이 문서는 계획 단계이며 실제 fine-tuning 코드는 아직 구현하지 않는다.

## 학습 데이터 원칙

fine-tuning 정답으로 사용할 수 있는 데이터는 real paired target을 우선한다.

필수 구성:

- person image
- garment image
- real target image

CatVTON pseudo target은 baseline 결과 또는 보조 실험용 데이터로 구분한다. pseudo target을 real target처럼 사용하지 않는다.

## 실험 구분

### 실험 1. Baseline

- pretrained CatVTON 사용
- 추가 학습 없음
- fine-tuning 비교 기준으로 사용

### 실험 2. Real Paired Target Fine-Tuning

- real paired target 기반 학습
- validation set으로 과적합 여부 확인
- baseline 대비 생성 품질 및 fit-aware 분석 안정성 비교

### 실험 3. Pseudo Target 보조 실험

- CatVTON pseudo target 사용 가능성을 별도 검토
- real target 기반 학습과 분리하여 기록
- pseudo target 오류 전파 가능성을 명시

## 평가 계획

- baseline과 fine-tuned 결과를 같은 입력 pair로 비교한다.
- real paired target과의 차이를 평가한다.
- fit-aware feature의 안정성을 비교한다.
- gold set 기준으로 label reliability를 비교한다.

## 리스크

- paired data 규모 부족
- CatVTON 생성 오류가 pseudo label에 반영될 가능성
- segmentation 또는 pose estimation 오류가 feature 계산에 영향을 줄 가능성
- 특정 의류 카테고리에 편향될 가능성

## 향후 작성 항목

- 학습 설정
- checkpoint 저장 정책
- validation metric
- early stopping 기준
- 실제 fine-tuning 결과
