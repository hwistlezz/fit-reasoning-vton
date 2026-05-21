# Fit-aware Virtual Try-On Web Prototype

이 저장소는 **Fit-aware Virtual Try-On Web Prototype**을 위한 저장소입니다.

기존 프로젝트명인 **Fit-Confidence Virtual Try-On**의 방향을 이어받되, MVP는 StableVITON 기반 가상 착장 생성과 CV 기반 fit 분석을 결합한 웹 프로토타입으로 정리합니다.

한 줄로 요약하면 다음과 같습니다.

> StableVITON으로 생성한 VTON 결과를 CV 기반 fit analyzer로 분석하고, confidence score와 자연어 fit explanation을 웹에서 제공하는 제품형 프로토타입

본 프로젝트는 논문 수준의 신규 VTON 모델 개발이 아니라, RTX 4080 16GB GPU 환경에서 1개월 안에 실제 동작하는 제품형 AI 시스템을 만드는 것이 목표입니다.

## 문제의식

기존 가상 착장 모델은 그럴듯한 이미지를 생성하지만, 생성 결과가 얼마나 신뢰 가능한지 또는 어떤 부분이 어색한지 설명하지 못하는 경우가 많습니다. 사용자는 결과 이미지가 실패했는지, 포즈나 parsing 문제가 있는지, 옷의 형태가 충분히 보존되었는지 판단하기 어렵습니다.

본 프로젝트는 생성 이미지 자체만 보여주는 것을 넘어서, 컴퓨터비전 기반 분석 결과를 함께 제공하는 방향을 다룹니다.

## MVP 목표

MVP 핵심 기능은 다음과 같습니다.

- 사용자 전신 이미지 업로드
- 의류 이미지 업로드
- 키 / 몸무게 / 평소 사이즈 입력
- StableVITON 기반 Virtual Try-On 생성
- DWPose / SCHP 기반 CV preprocessing
- CV 기반 fit 분석
- confidence score 제공
- 자연어 fit explanation 제공
- 웹 기반 인터랙티브 결과 UI 제공

현재 단계는 계획 수정 및 문서화 단계입니다. StableVITON inference 성공, 성능 수치, 결과 이미지, 데모 영상은 아직 README에 기록하지 않습니다.

## 전체 Pipeline

```text
User Input
-> Input Quality Check
-> Pose Estimation, DWPose
-> Human Parsing, SCHP
-> StableVITON Inference
-> Fit Analyzer
-> Confidence Scoring
-> Fit Reasoning
-> Web UI Visualization
```

## 모델 전략

### StableVITON

StableVITON을 MVP main VTON backbone으로 사용합니다.

PC1에서 StableVITON inference와 FastAPI API server를 실행하고, `/api/tryon` 요청이 들어오면 StableVITON inference를 통해 result image를 생성하는 방향으로 갑니다.

StableVITON 외부 저장소, checkpoint, dataset, generated image는 본 저장소에 커밋하지 않습니다.

### IDM-VTON

IDM-VTON은 MVP에 통합하지 않습니다.

PR #8에서 정리한 IDM-VTON local Gradio demo smoke test 기록은 삭제하지 않고 비교 실험 자산으로 유지합니다. IDM-VTON은 PC3에서 comparison baseline으로 활용합니다.

PC3에서 IDM-VTON의 역할은 다음과 같습니다.

- 단일 inference 비교 실험
- StableVITON 대비 설치 난이도, VRAM 사용량, inference time, 결과 품질, API 통합 난이도 기록
- IDM-VTON 작업이 오래 막히면 MVP 보호를 위해 중단하고 PC3를 LoRA 실험용으로 전환

### CatVTON

CatVTON은 MVP 범위에서는 제외하며, 후속 optional baseline으로만 검토합니다.

### LoRA

LoRA는 MVP 필수 기능이 아니라 PC3에서 진행하는 후순위 feasibility 실험입니다.

PC3에서 oversized LoRA 1개를 feasibility 수준으로 검토할 수 있지만, 1개월 MVP의 핵심 기능은 `CV 기반 fit analyzer + confidence UX + 웹 데모`입니다.

## Fit-aware Reasoning Layer

Fit-aware Reasoning Layer는 StableVITON 결과를 그대로 신뢰하지 않고, 다음 컴퓨터비전 단서를 활용해 결과 품질과 핏 경향을 해석합니다.

- pose/keypoint 안정성
- DWPose 기반 pose extraction
- SCHP 기반 human parsing
- silhouette 변화
- garment preservation
- 입력 이미지 품질
- 착장 결과 왜곡 여부

정확한 신체 치수 측정이나 실제 의류 사이즈 추천은 목표로 하지 않습니다.

## 역할 분리

요약 역할은 다음과 같습니다. 자세한 내용은 [PC / 노트북 역할](docs/pc_roles.md)을 참고합니다.

- 노트북 1: Frontend, Next.js UI, localhost 개발, PC1 FastAPI 연결 테스트
- 노트북 2: Backend 코드 개발, Git / Issue / PR 관리, PC1 / PC2 / PC3 SSH 실행 관리
- PC1: StableVITON main inference server, FastAPI API server, demo API, batch job log
- PC2: DWPose, SCHP, input quality check, fit feature extraction
- PC3: IDM-VTON comparison, oversized LoRA feasibility

PC3는 PC1 MVP 서버가 어느 정도 잡힌 뒤 진행합니다.

## API 계획

FastAPI backend는 다음 endpoint를 기준으로 설계합니다. 자세한 contract는 [API Contract](docs/api_contract.md)를 참고합니다.

- `GET /api/health`
- `POST /api/tryon`
- `GET /api/job/{job_id}`
- `GET /api/result/{job_id}`

API response 예시는 실제 inference 결과가 아니라 프론트엔드 연동을 위한 contract example입니다.

## Backend 구조 계획

backend는 다음 구조를 목표로 합니다. 이번 문서 작업에서는 실제 backend 코드를 구현하지 않습니다.

```text
backend/
  app/
    main.py
    api/
      tryon.py
      health.py
    core/
      config.py
      paths.py
      job_store.py
      queue.py
    services/
      stableviton_service.py
      pose_service.py
      parsing_service.py
      quality_checker.py
      fit_analyzer.py
      confidence.py
      reasoning.py
    schemas/
      tryon.py
      result.py
    workers/
      tryon_worker.py
  scripts/
    run_test_jobs.py
    batch_preprocess.py
    batch_fit_features.py
  configs/
    stableviton.yaml
  datasets/
    raw/
    processed/
  outputs/
  logs/
  models/
```

`backend/outputs/`, datasets, logs, external model files, checkpoint, generated image는 git에 커밋하지 않는 방향으로 관리합니다.

## 데이터 후보

- 직접 촬영한 소규모 샘플 이미지
- VITON-HD 후보 검토
- DressCode 후보 검토
- FIT 데이터셋 기반 fit-aware scoring은 후속 검토 또는 참고 데이터셋 방향으로 유지

본 저장소에는 원본 데이터셋 이미지, annotation 파일, 생성 이미지를 포함하지 않습니다.

## 현재 범위와 하지 않을 것

이번 MVP에서 하지 않을 것은 다음과 같습니다.

- 정확한 신체 치수 예측
- 실제 의류 사이즈 추천
- VTON 모델을 처음부터 학습
- StableVITON 외부 저장소를 본 저장소에 복사
- checkpoint, dataset, generated image 커밋
- CatVTON을 MVP active baseline으로 통합
- LoRA를 MVP 필수 기능으로 포함
- 검증되지 않은 성능 수치 또는 fake result 작성

## 주요 문서

- [프로젝트 개요](docs/project_overview.md)
- [로드맵](docs/roadmap.md)
- [시스템 아키텍처](docs/system_architecture.md)
- [PC / 노트북 역할](docs/pc_roles.md)
- [API Contract](docs/api_contract.md)
- [환경 설정](docs/setup/environment.md)
- [IDM-VTON 외부 설정](docs/setup/idm_vton_external_setup.md)
- [IDM-VTON 4080 smoke test 로그](docs/experiments/idm_vton_smoke_test_4080_log.md)
- [데이터셋 계획](docs/data/dataset_plan.md)
- [실험 계획](docs/experiments/experiment_plan.md)

## 협업 규칙

- [Git Workflow](docs/conventions/git_workflow.md)
- [Branch Convention](docs/conventions/branch_convention.md)
- [Commit Convention](docs/conventions/commit_convention.md)
- [Issue / PR Convention](docs/conventions/issue_pr_convention.md)

## Third-Party Notice

본 프로젝트는 StableVITON을 MVP main VTON backbone으로 외부 참조하고, IDM-VTON을 PC3 comparison baseline으로 외부 참조합니다. CatVTON은 MVP 범위에서는 제외하며, 후속 optional baseline으로만 검토합니다.

외부 VTON 모델의 코드, checkpoint, demo 자료는 각 원저작자의 라이선스와 사용 조건을 확인해야 합니다. 외부 모델 코드, checkpoint, 생성 결과 이미지, 대용량 데이터셋은 본 저장소에 커밋하지 않습니다.

본 프로젝트의 핵심 기여는 VTON 모델 자체 구현이 아니라, VTON 결과를 해석하는 Fit-aware Reasoning Layer와 confidence UX입니다.

## Dataset Notice

VITON-HD와 DressCode 데이터셋은 각 원 배포처의 라이선스와 사용 조건을 확인해야 합니다. FIT 데이터셋 기반 fit-aware scoring은 후속 검토 또는 참고 데이터셋 방향으로 유지합니다.

사람 이미지가 포함될 수 있으므로 공개 범위와 사용 목적을 주의해서 관리합니다.
