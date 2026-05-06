# fit-reasoning-vton

CatVTON 기반 가상 착용 결과에서 시각적 핏 경향을 분석하고 설명하는 컴퓨터 비전 캡스톤 프로젝트입니다.

이 프로젝트는 실제 신체 치수나 정확한 의류 사이즈를 예측하지 않습니다. 생성된 virtual try-on 결과를 기준으로 `slim`, `regular`, `oversized` 같은 시각적 핏 경향과 근거를 분석하는 것을 목표로 합니다.

## 목표

- pretrained CatVTON을 기준 모델로 사용합니다.
- VITON-HD 및 선택적으로 DressCode 데이터셋으로 대규모 추론 결과를 생성합니다.
- NVIDIA A100 GPU 환경에서 baseline inference와 평가를 수행합니다.
- paired data 기반 fine-tuning 실험 계획을 준비합니다.
- real paired target과 CatVTON이 생성한 pseudo target을 명확히 구분합니다.
- `width_ratio`, `length_ratio`, `silhouette_ratio`, `shoulder_ratio`, `hem_position` 기반 fit-aware visual feature를 추출하고 pseudo fit label을 생성합니다.
- gold set을 기준으로 rule-based labeling과 feature-based classifier를 비교하고 분석 신뢰도를 계산합니다.
- overlay visualization과 자연어 설명을 제공하고, 이후 Fit Report UI로 확장합니다.

## 저장소 원칙

CatVTON 코드는 이 저장소에 직접 복사하지 않습니다. 별도 위치에 clone하거나 외부 경로로 참조합니다.

대용량 데이터셋, 체크포인트, 생성 이미지, 로그, 모델 가중치는 GitHub에 커밋하지 않습니다. 이 저장소에는 문서, 실험 계획, 경량 스크립트, 향후 구현될 분석 코드만 포함합니다.

## Third-Party Notice

본 프로젝트는 [CatVTON](https://github.com/Zheng-Chong/CatVTON)을 virtual try-on baseline으로 외부 참조합니다. CatVTON 코드는 본 저장소에 포함하지 않으며, `../CatVTON` 같은 외부 경로에 별도로 clone해서 사용합니다.

CatVTON의 코드, checkpoint, demo 자료는 원저작자의 라이선스와 사용 조건을 확인해야 합니다. CatVTON 공식 저장소 기준 라이선스는 Creative Commons BY-NC-SA 4.0으로 안내되어 있으며, 본 프로젝트에서의 CatVTON 사용 범위는 학업 및 비영리 연구 목적입니다.

CatVTON 코드, checkpoint, CatVTON으로 생성한 결과 이미지, 대용량 데이터셋은 본 저장소에 커밋하지 않습니다. 본 프로젝트의 핵심 기여는 CatVTON 자체 구현이 아니라, CatVTON 결과를 해석하는 Fit-aware Reasoning Layer입니다.

## Dataset Notice

VITON-HD와 DressCode 데이터셋은 각 원 배포처의 라이선스와 사용 조건을 확인해야 합니다. 본 저장소에는 원본 데이터셋 이미지, annotation 파일, 생성 이미지를 포함하지 않습니다.

해당 데이터셋과 생성 결과에는 사람 이미지가 포함될 수 있으므로, 공개 범위와 사용 목적을 주의해서 관리합니다.

## 현재 상태

초기 프로젝트 스캐폴드 단계입니다. 아직 feature extraction, training, inference pipeline, UI는 구현하지 않았습니다.

## Phase 1. 외부 CatVTON 준비

CatVTON은 본 저장소에 복사하지 않고 공식 저장소를 외부 작업 공간에 clone하여 사용합니다. Phase 1에서는 CatVTON 환경 설정, GPU 확인, Gradio smoke test, 첫 try-on 결과 생성 여부 확인만 수행합니다.

- [CatVTON 외부 저장소 설정](docs/setup/catvton_external_setup.md)
- [CatVTON smoke test 로그 템플릿](docs/experiments/catvton_smoke_test_log_template.md)

데이터셋, 체크포인트, 생성 결과, 로그, 모델 가중치는 GitHub에 커밋하지 않습니다.

## 주요 문서

- [프로젝트 개요](docs/project_overview.md)
- [로드맵](docs/roadmap.md)
- [환경 설정](docs/setup/environment.md)
- [CatVTON 설정](docs/setup/catvton_setup.md)
- [데이터셋 계획](docs/data/dataset_plan.md)
- [실험 계획](docs/experiments/experiment_plan.md)

## GPU 확인

```bash
python scripts/check_gpu.py
```
