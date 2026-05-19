# Fine-Tuning 데이터셋 계획

## 현재 범위

이번 텀프로젝트의 필수 목표는 fine-tuning 데이터셋 구축이 아니다. 메인 목표는 IDM-VTON을 main baseline으로 실행하고, 그 결과를 해석하는 Fit-aware Reasoning Layer와 웹 데모를 만드는 것이다.

fine-tuning 데이터셋은 후속 캡스톤 또는 research extension에서 검토한다.

## 후속 확장 시 필요한 구성

fine-tuning을 검토하려면 각 샘플에 다음 항목이 필요하다.

- person image
- garment image
- real target image of the person wearing the garment

real target image는 실제 정답 이미지로 취급할 수 있다. IDM-VTON 또는 CatVTON으로 생성한 pseudo target은 real target과 구분하여 저장한다.

## Real Target과 Pseudo Target

| 구분 | 의미 | 사용 목적 |
| --- | --- | --- |
| real paired target | 실제 사람이 해당 garment를 착용한 이미지 | 후속 fine-tuning 정답, 평가 기준 |
| pseudo target | VTON 모델이 생성한 virtual try-on 결과 | baseline 분석, confidence scoring, 보조 비교 |

pseudo target을 real target처럼 취급하지 않는다. pseudo target 기반 학습은 모델의 오류가 다시 학습될 수 있으므로 별도 실험으로 분리해야 한다.

## Split 원칙

후속 fine-tuning을 수행하는 경우 다음 원칙을 따른다.

- train, validation, test 분리를 명확히 한다.
- 같은 person 또는 garment로 인한 누수를 점검한다.
- 웹 데모용 샘플과 학습용 샘플을 혼동하지 않는다.
- fit confidence 평가용 샘플과 fine-tuning용 샘플을 구분한다.

## 향후 작성 항목

- paired manifest schema
- real target 확보 기준
- pseudo target 생성 기준
- 검수 샘플링 방식
- annotation tool 또는 검수 UI 사용 여부
