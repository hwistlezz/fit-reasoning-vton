# 로드맵

## Phase 0. 프로젝트 방향 전환 및 문서 정리

- StableVITON 중심 MVP 방향으로 README와 주요 문서 수정
- PC3를 StableVITON batch evaluation, failure case 수집, fit threshold / confidence 실험 중심으로 역할 변경
- IDM-VTON을 시간이 남을 경우에만 진행하는 후순위 대체 VTON 비교 실험으로 정리
- LoRA를 한 달 MVP에서 제외하고 7개월 고도화 optional 실험으로 이동
- CatVTON을 MVP 범위에서 제외하고 후속 optional baseline으로 정리
- PC1 / PC2 / PC3 / 노트북 1 / 노트북 2 역할 문서화
- 전체 pipeline, API contract, backend 구조 계획 문서화
- 외부 모델 코드, checkpoint, dataset, generated image 커밋 방지 원칙 재확인

## Phase 1. PC1 StableVITON external setup

- PC1에 Git / Python / conda 상태 확인
- PC1에 `fit-reasoning-vton` clone
- StableVITON 외부 저장소 clone
- StableVITON commit hash 기록
- `vton` conda environment 생성
- PyTorch CUDA 사용 가능 여부 확인
- RTX 4080 GPU 인식 확인
- StableVITON 필수 패키지 설치
- setup log 문서화

이 단계에서는 StableVITON inference 성공처럼 기록하지 않는다.

## Phase 2. PC1 StableVITON CLI smoke test

- StableVITON checkpoint 준비
- sample person image 준비
- sample garment image 준비
- CLI inference command 확인
- 첫 실행 시도
- 성공 또는 실패 로그 기록
- inference time, VRAM 사용량, output path 기록
- generated image는 repository 밖 또는 ignored output 경로에 저장
- troubleshooting 문서화

실행 시간이나 VRAM 기록은 개발 환경 smoke test log이며 공식 benchmark로 표현하지 않는다.

## Phase 3. FastAPI backend skeleton

- `backend/` 폴더 구조 생성
- FastAPI app entrypoint 생성
- `/api/health` 구현
- CORS 설정
- output directory 설정
- `.gitignore`에 generated outputs 제외 확인
- backend 실행 방법 문서화
- `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000` 실행 확인

이 단계에서는 StableVITON 실제 inference와 연결하지 않아도 된다.

## Phase 4. Try-On job API 및 outputs 구조

- `POST /api/tryon` 구현
- `GET /api/job/{job_id}` 구현
- `GET /api/result/{job_id}` 구현
- `backend/outputs/{job_id}` 구조 구현
- job status 저장 방식 구현
- mock pipeline으로 frontend 연동 가능 상태 확인
- generated outputs git 제외 확인

API response example은 실제 결과가 아니라 contract example로만 사용한다.

## Phase 5. StableVITON service wrapper 연결

- 외부 StableVITON path 설정
- inference command wrapper 작성
- input image path, cloth image path 전달
- output image path 수집
- subprocess error handling
- timeout 처리
- GPU busy 상태 고려
- inference log 저장
- 실패 시 job status를 `failed`로 변경
- 성공 시 result image path 저장

외부 StableVITON 코드와 checkpoint는 repository에 복사하지 않는다.

## Phase 6. PC2 CV preprocessing 및 fit feature extraction

- AIHub "쉐이프리스 의류 및 포즈 데이터"를 fit analyzer / keypoint / segmentation / confidence scoring 기준 설계에 활용
- DWPose pose extraction
- SCHP human parsing
- input quality check
- fit feature extraction
- `datasets/raw`
- `datasets/processed`
- `datasets/features.csv`
- `datasets/test_cases.csv`
- failure case 후보 수집
- hotspot annotation 후보 생성

AIHub 원본 이미지, annotation, JSON 파일과 generated intermediate output은 repository에 커밋하지 않는다. 공개 저장소에는 schema, example CSV, 문서만 포함한다.

## Phase 7. Fit Analyzer, Confidence Scoring, Fit Reasoning

- pose quality 기반 입력 품질 점수 초안
- parsing quality 기반 segmentation 안정성 점수 초안
- silhouette 기반 착장 전후 형태 변화 분석
- garment preservation 기반 의류 보존 정도 분석
- confidence score 산출 규칙 설계
- oversized / regular / tight 등 fit label 후보 정의
- 자연어 fit explanation 생성 규칙 작성
- 실패 원인 설명 문구 작성

정확한 신체 치수 측정이나 실제 사이즈 추천은 하지 않는다.

## Phase 8. Next.js frontend 및 인터랙티브 결과 UI

- 노트북 1에서 Next.js UI 개발
- `.env.local`에 `NEXT_PUBLIC_API_BASE_URL=http://PC1_IP:8000` 설정
- 사용자 전신 이미지 업로드 UI
- 의류 이미지 업로드 UI
- 키 / 몸무게 / 평소 사이즈 입력 UI
- job status polling
- result image, confidence score, fit explanation 표시
- warning 또는 failure state 표시

README에 결과 이미지나 성능 수치를 추가하지 않는다.

## Phase 9. PC1 test job batch 및 MVP 검증 로그

- 3~5개 sample pair 준비
- batch 실행 스크립트 작성
- inference time 기록
- peak VRAM 또는 `nvidia-smi` 로그 기록
- success/failure 기록
- 실패 사례 원인 기록
- 실험 로그 문서화

output image는 repository가 아니라 ignored output path에 저장한다.

## Phase 10. PC3 batch evaluation 및 confidence 실험

PC3는 PC1 StableVITON API가 최소 동작한 뒤, batch evaluation과 confidence 실험을 담당한다.

- StableVITON batch test
- 대량 inference 결과 평가
- failure case 수집
- low confidence case 수집
- fit analyzer threshold 실험
- confidence scoring 실험
- `outputs/experiments/stableviton_batch/` 정리
- `outputs/experiments/failure_cases/` 정리
- `outputs/experiments/low_confidence_cases/` 정리
- `outputs/experiments/fit_threshold_tests/` 정리
- `outputs/experiments/confidence_tests/` 정리
- 시간이 남을 경우에만 IDM-VTON 등 대체 VTON 모델 비교 실험

IDM-VTON은 시간이 남을 경우에만 진행하는 후순위 대체 VTON 비교 실험이다. LoRA는 한 달 MVP에서 제외하며, 7개월 고도화 단계에서 fit control 필요성이 명확해졌을 때 선택적으로 검토한다.

## 후속 검토

- CatVTON은 MVP 범위에서는 제외하며, 후속 optional baseline으로만 검토
- VITON-HD / DressCode / FIT 데이터셋은 후속 검토 또는 참고 데이터셋으로 유지
- AIHub "쉐이프리스 의류 및 포즈 데이터"는 fit analyzer와 confidence scoring 설계용으로 활용하되, 원본 데이터는 공개 저장소에 업로드하지 않음
- FIT 데이터셋 기반 fit-aware scoring은 캡스톤 또는 research extension 방향으로 분리
