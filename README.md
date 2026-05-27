# Fit-Confidence Virtual Try-On

**체형·핏 신뢰도 평가를 제공하는 가상 착장 웹 시스템**

사람 이미지와 의류 이미지를 입력받아 가상 착장 이미지를 생성하고, 생성 결과가 얼마나 신뢰 가능한지 컴퓨터비전 특징 기반으로 평가하는 텀프로젝트입니다.

기존 VTON 모델의 결과를 분석해 입력 품질, 착장 결과 신뢰도, 간단한 핏 해석을 제공하는 **Fit-aware Reasoning Layer**를 설계하고 웹 화면으로 보여주는 것이 목표입니다.

## 🧩 문제의식

기존 가상 착장 모델은 그럴듯한 착장 이미지를 생성하지만, 생성 결과가 얼마나 신뢰 가능한지 또는 어떤 부분이 어색한지 설명하지 못하는 경우가 많습니다. 사용자는 결과 이미지가 실패했는지, 포즈나 세그멘테이션 문제인지, 옷의 형태가 충분히 보존되었는지 판단하기 어렵습니다.

본 프로젝트는 생성 이미지 자체만 보여주는 것을 넘어서, 컴퓨터비전 기반 분석 결과를 함께 제공하는 방향을 다룹니다.

## 🎯 프로젝트 목표

- 사람 이미지와 옷 이미지를 입력받아 가상 착장 결과 이미지를 생성합니다.
- 입력 이미지의 품질을 평가합니다.
- 착장 결과의 신뢰도 점수를 계산합니다.
- 기장감, 품 여유, 소매 길이, 어깨선 등 간단한 핏 해석을 제공합니다.
- 웹 화면에서 착장 이미지, 신뢰도 점수, 핏 해석, 실패 원인을 함께 보여줍니다.

## ✨ 핵심 기능

이번 텀프로젝트에서 계획하는 기능은 다음과 같습니다.

- 입력 품질 평가: 사람 이미지의 포즈, 가림, 전신 여부, 의류 이미지 품질 확인
- 착장 결과 신뢰도 평가: 포즈 일관성, 세그멘테이션 안정성, 실루엣 변화, 의류 보존 정도 분석
- Fit-aware reasoning: 기장감, 품 여유, 소매 길이, 어깨선 등 시각적 핏 단서 해석
- 실패 원인 설명: 입력 문제, 생성 결과 왜곡, 의류 보존 실패 등 가능한 원인 표시
- 웹 UI: 입력 이미지, 생성 이미지, 점수, 해석 문장을 한 화면에서 확인

현재 단계에서는 위 기능이 모두 구현된 상태가 아니며, proposal과 외부 baseline 준비 문서를 정리한 상태입니다.

## 🧠 사용할 컴퓨터비전 요소

- Pose/keypoint 기반 자세 안정성 확인
- Segmentation 또는 human parsing 기반 사람/의류 영역 분석
- Silhouette 기반 착장 전후 형태 변화 분석
- Garment preservation 기반 의류 색상·패턴·형태 보존 정도 확인
- Feature-based confidence scoring
- Rule-based fit interpretation

정확한 신체 치수 측정이나 실제 의류 사이즈 추천은 목표로 하지 않습니다.

## 🧪 모델과 데이터

### 🚀 Main Baseline: IDM-VTON

IDM-VTON을 이번 텀프로젝트의 메인 가상 착장 baseline으로 사용합니다. 한 달 안에 작동하는 웹 데모를 만들기 위해 우선 실행 대상으로 둡니다.

IDM-VTON source code, checkpoint, dataset, generated image는 본 저장소에 복사하지 않고 외부 경로에서 관리합니다.

### 🔍 Optional Comparison Baseline: CatVTON

CatVTON은 삭제하지 않고 optional comparison baseline으로 유지합니다. 가능하면 비교 실험 또는 smoke test에 사용하지만, 이번 텀프로젝트의 메인 모델은 아닙니다.

CatVTON source code, checkpoint, dataset, generated image는 본 저장소에 복사하지 않습니다.

### 📦 데이터 후보

- 직접 촬영한 소규모 샘플 이미지
- VITON-HD 후보 검토
- DressCode 후보 검토
- FIT 데이터셋 기반 fit-aware scoring은 후속 확장 방향으로 검토


## 📌 예상 결과물

이번 proposal 기준 예상 산출물은 다음과 같습니다.

- 외부 IDM-VTON 실행 환경 구성 문서
- 샘플 이미지 기반 smoke test 로그
- 웹 데모 구조 초안
- 입력 품질 평가 모듈 계획 및 구현
- fit confidence score 산출 방식 초안 및 구현
- fit reasoning 문장 생성 규칙
- 성공/실패 사례 정리

결과 이미지, 성능 수치, 데모 영상은 아직 생성되지 않았습니다. 이후 구현 단계에서 실제 실행 결과를 근거와 함께 추가합니다.

## 🚫 현재 범위와 하지 않을 것

이번 텀프로젝트에서 하지 않을 것은 다음과 같습니다.

- 정확한 신체 치수 예측
- 실제 의류 사이즈 추천
- VTON 모델을 처음부터 학습
- CatVTON 직접 파인튜닝
- 대규모 FIT 데이터셋 전체 학습
- StableVITON 필수 구현
- 검증되지 않은 성능 수치 또는 fake result 작성

StableVITON, 2.5D 정보, FIT 데이터셋 기반 fit-aware scoring은 후속 캡스톤 또는 research extension 방향으로 남깁니다.

## ✅ 현재 진행 상태

현재 완료:

- 프로젝트 저장소 생성
- 기본 디렉터리 구조 생성
- 외부 baseline 사용 원칙 정리
- 라이선스 및 데이터셋 고지 추가
- IDM-VTON과 CatVTON을 외부 저장소로 참조하는 문서 구조 준비
- GPU 및 외부 baseline 경로 확인용 경량 스크립트 준비

앞으로 할 일:

- IDM-VTON 외부 실행 환경 구성
- 샘플 이미지 기반 smoke test
- 웹 인터페이스 구현
- 입력 품질 평가 모듈 구현
- fit confidence score 구현
- fit reasoning 문장 생성
- 성공/실패 사례 정리

## 🗺️ 향후 구현 계획

1. IDM-VTON 외부 저장소를 준비하고 smoke test를 수행합니다.
2. 직접 촬영 또는 공개 데이터 후보에서 소규모 샘플을 준비합니다.
3. 웹 입력 화면과 결과 화면의 최소 기능을 구현합니다.
4. 포즈, 세그멘테이션, 실루엣 기반 입력 품질 평가를 구현합니다.
5. 착장 결과 신뢰도 점수와 실패 원인 설명을 구현합니다.
6. 핏 해석 문장을 규칙 기반으로 생성합니다.
7. 성공/실패 사례를 정리하고 한계를 명확히 기록합니다.

## 📚 주요 문서

- [프로젝트 개요](docs/project_overview.md)
- [로드맵](docs/roadmap.md)
- [환경 설정](docs/setup/environment.md)
- [StableVITON 외부 설정](docs/setup/stableviton_external_setup.md)
- [StableVITON PC1 setup log template](docs/experiments/stableviton_pc1_setup_log_template.md)
- [IDM-VTON 외부 설정](docs/setup/idm_vton_external_setup.md)
- [IDM-VTON 4080 smoke test 준비 로그](docs/experiments/idm_vton_smoke_test_4080_log.md)
- [CatVTON 외부 설정](docs/setup/catvton_external_setup.md)
- [데이터셋 계획](docs/data/dataset_plan.md)
- [실험 계획](docs/experiments/experiment_plan.md)

## 🤝 협업 규칙

- [Git Workflow](docs/conventions/git_workflow.md)
- [Branch Convention](docs/conventions/branch_convention.md)
- [Commit Convention](docs/conventions/commit_convention.md)
- [Issue / PR Convention](docs/conventions/issue_pr_convention.md)

## 📄 Third-Party Notice

본 프로젝트는 IDM-VTON을 main virtual try-on baseline으로, [CatVTON](https://github.com/Zheng-Chong/CatVTON)을 optional comparison baseline으로 외부 참조합니다. 외부 모델 코드는 본 저장소에 포함하지 않으며, `../IDM-VTON`, `../CatVTON` 같은 외부 경로에 별도로 clone해서 사용합니다.

외부 VTON 모델의 코드, checkpoint, demo 자료는 각 원저작자의 라이선스와 사용 조건을 확인해야 합니다. CatVTON 공식 저장소 기준 라이선스는 Creative Commons BY-NC-SA 4.0으로 안내되어 있습니다. 본 프로젝트에서의 외부 baseline 사용 범위는 학업 및 비영리 연구 목적입니다.

외부 모델 코드, checkpoint, 생성 결과 이미지, 대용량 데이터셋은 본 저장소에 커밋하지 않습니다. 본 프로젝트의 핵심 기여는 VTON 모델 자체 구현이 아니라, VTON 결과를 해석하는 Fit-aware Reasoning Layer입니다.

## 🗃️ Dataset Notice

VITON-HD와 DressCode 데이터셋은 각 원 배포처의 라이선스와 사용 조건을 확인해야 합니다. 본 저장소에는 원본 데이터셋 이미지, annotation 파일, 생성 이미지를 포함하지 않습니다.

사람 이미지가 포함될 수 있으므로 공개 범위와 사용 목적을 주의해서 관리합니다.

## 🖥️ GPU 확인

```bash
python scripts/check_gpu.py
```
