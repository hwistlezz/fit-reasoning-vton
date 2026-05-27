# 시스템 아키텍처

## MVP 방향

Fit-aware Virtual Try-On Web Prototype은 StableVITON 기반 VTON 생성 결과를 CV 기반 fit analyzer로 분석하고, confidence score와 자연어 fit explanation을 웹에서 제공하는 제품형 프로토타입이다.

이번 문서는 구현 계획을 정리한다. StableVITON inference 성공, benchmark, 결과 이미지는 기록하지 않는다.

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

## 주요 컴포넌트

### Frontend

- Next.js 기반 UI
- 사용자 전신 이미지 업로드
- 의류 이미지 업로드
- 키 / 몸무게 / 평소 사이즈 입력
- job status polling
- result image, confidence score, fit explanation 표시

### Backend API

- FastAPI 기반 API server
- PC1에서 `0.0.0.0:8000`으로 실행
- `/api/health`
- `/api/tryon`
- `/api/job/{job_id}`
- `/api/result/{job_id}`
- output path: `backend/outputs/`

### StableVITON Service

- PC1에서 외부 StableVITON 저장소를 참조
- backend에서 service wrapper를 통해 inference command 호출
- result image를 `backend/outputs/{job_id}` 아래에 저장하는 방향으로 설계
- 외부 StableVITON 코드, checkpoint, generated image는 repository에 커밋하지 않음

### CV Preprocessing

- PC2에서 DWPose pose extraction 수행
- PC2에서 SCHP human parsing 수행
- input quality check 수행
- fit feature extraction 수행
- `datasets/raw`, `datasets/processed`, `datasets/features.csv`를 작업 경로로 사용

### Fit Analyzer

- pose/keypoint 안정성
- human parsing 안정성
- silhouette 변화
- garment preservation
- 입력 이미지 품질
- 착장 결과 왜곡 여부

위 feature를 기반으로 fit label, confidence score, warning, 자연어 explanation을 생성한다.

## Backend Folder 계획

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

이번 Issue #9에서는 실제 backend 코드를 구현하지 않는다.

## 저장소 관리 원칙

- 외부 모델 코드를 repository에 복사하지 않는다.
- checkpoint를 커밋하지 않는다.
- dataset을 커밋하지 않는다.
- generated image를 커밋하지 않는다.
- UI screenshot을 커밋하지 않는다.
- fake result를 작성하지 않는다.
- README에 결과 이미지나 benchmark처럼 보이는 성능 수치를 추가하지 않는다.
