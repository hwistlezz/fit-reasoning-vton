# Fine-Tuning 데이터셋 계획

## 목적

fine-tuning 실험은 paired data를 기반으로 준비한다. paired data는 같은 사람과 같은 garment에 대해 입력 person image, garment image, 실제 착용 target image가 연결된 데이터를 의미한다.

## 필수 구성

각 샘플은 다음 항목을 가진다.

- person image
- garment image
- real target image of the person wearing the garment

real target image는 실제 정답 이미지로 취급할 수 있다. CatVTON으로 생성한 pseudo target은 real target과 구분하여 저장한다.

## Real Target과 Pseudo Target

| 구분 | 의미 | 사용 목적 |
| --- | --- | --- |
| real paired target | 실제 사람이 해당 garment를 착용한 이미지 | fine-tuning 정답, 평가 기준 |
| CatVTON pseudo target | CatVTON이 생성한 virtual try-on 결과 | baseline 분석, pseudo label 생성, 보조 실험 |

CatVTON pseudo target을 real target처럼 취급하지 않는다. pseudo target 기반 학습은 모델의 오류가 다시 학습될 수 있으므로 별도 실험으로 분리한다.

## Split 원칙

- train, validation, test 분리를 명확히 한다.
- gold set은 test와 목적을 구분한다.
- 같은 person 또는 garment로 인한 누수를 점검한다.
- fine-tuning 실험과 fit classifier 실험의 split을 혼동하지 않는다.

## Annotation 계획

fine-tuning 자체에는 이미지 pair가 필요하지만, fit-aware 분석에는 추가 annotation이 필요할 수 있다.

후보 annotation:

- `overall_fit`
- `length_label`
- `roominess_label`
- 검수자 메모
- 품질 플래그
- 생성 실패 여부

## 향후 작성 항목

- 최종 paired manifest schema
- real target 확보 기준
- pseudo target 생성 기준
- 검수 샘플링 방식
- annotation tool 또는 검수 UI 사용 여부
