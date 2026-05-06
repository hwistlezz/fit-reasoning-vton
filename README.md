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

## 현재 상태

초기 프로젝트 스캐폴드 단계입니다. 아직 feature extraction, training, inference pipeline, UI는 구현하지 않았습니다.

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
