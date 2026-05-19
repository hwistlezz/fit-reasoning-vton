# Fine-Tuning 계획

## 현재 범위

이번 텀프로젝트에서는 VTON 모델을 처음부터 학습하거나 CatVTON을 직접 파인튜닝하지 않는다. 우선순위는 IDM-VTON을 main baseline으로 실행하고, 생성 결과를 분석하는 Fit-aware Reasoning Layer와 웹 데모를 만드는 것이다.

fine-tuning은 후속 캡스톤 또는 research extension에서 검토한다.

## 후속 연구 방향

후속 연구에서 fine-tuning을 검토한다면 real paired target 기반 데이터를 우선해야 한다.

필수 구성:

- person image
- garment image
- real target image

pseudo target은 VTON 모델이 생성한 결과이므로 real target처럼 취급하지 않는다.

## 가능한 확장 실험

### Real Paired Target 기반 Fine-Tuning

- real paired target 기반 학습
- validation set으로 과적합 여부 확인
- baseline 대비 생성 품질 및 fit confidence 안정성 비교

### Pseudo Target 보조 실험

- IDM-VTON 또는 CatVTON pseudo target 사용 가능성을 별도 검토
- real target 기반 학습과 분리하여 기록
- pseudo target 오류 전파 가능성을 명시

## 리스크

- paired data 규모 부족
- pseudo target 오류가 학습에 반영될 가능성
- segmentation 또는 pose estimation 오류가 feature 계산에 영향을 줄 가능성
- 특정 의류 카테고리에 편향될 가능성

## 향후 작성 항목

- 후속 연구용 학습 설정
- checkpoint 저장 정책
- validation metric
- 실제 fine-tuning 결과
