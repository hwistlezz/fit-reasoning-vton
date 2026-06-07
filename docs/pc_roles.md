# PC / 노트북 역할

## 노트북 1

노트북 1은 frontend 개발용이다.

- Frontend 개발
- Next.js UI 개발
- localhost 개발
- PC1 FastAPI API 연결 테스트
- `.env.local` 설정

```env
NEXT_PUBLIC_API_BASE_URL=http://PC1_IP:8000
```

## 노트북 2

노트북 2는 backend 개발과 운영 관리용이다.

- Backend 코드 개발
- FastAPI / pipeline 코드 수정
- Git / Issue / PR 관리
- PC1 / PC2 / PC3 SSH 접속 및 실행 관리

## PC1

PC1은 MVP의 핵심 서버이다.

- StableVITON main inference server
- FastAPI API server
- 실제 VTON 결과 생성
- 데모 API 서버
- `/api/health`
- `/api/tryon`
- `/api/job/{job_id}`
- `/api/result/{job_id}`
- test job batch 실행
- inference time / VRAM / success rate log 기록
- output path: `backend/outputs/`
- API port: `8000`

PC1에서 StableVITON 외부 저장소와 checkpoint를 관리하되, 해당 파일들은 본 저장소에 커밋하지 않는다.

## PC2

PC2는 AIHub 데이터 기반 CV preprocessing 및 fit analyzer 데이터 구축 전용 PC이다.

- AIHub "쉐이프리스 의류 및 포즈 데이터" 다운로드 및 로컬 관리
- DWPose pose extraction
- SCHP human parsing
- input quality check
- fit feature extraction
- `datasets/raw`
- `datasets/processed`
- `datasets/features.csv`
- `datasets/test_cases.csv`
- failure case 수집
- contact sheet 생성
- hotspot annotation 후보 생성
- PC1 / PC3로 processed data 동기화

PC2는 FastAPI 메인 서버나 프론트엔드를 담당하지 않는다. AIHub 원본 이미지, annotation, JSON 파일과 processed output, feature artifact는 저장소에 바로 커밋하지 않는다. 필요한 경우 작은 schema, example CSV, 로그 문서만 별도로 정리한다.

## PC3

PC3는 더 이상 LoRA 학습 전용 PC가 아니다.

PC3는 PC1 StableVITON API가 최소 동작한 뒤 StableVITON 결과를 대량으로 평가하고, failure case와 confidence 관련 실험을 수행하는 실험 / 평가 / 분석 PC이다.

- StableVITON batch test
- 대량 inference 결과 평가
- failure case 수집
- low confidence case 수집
- fit analyzer threshold 실험
- confidence scoring 실험
- 대체 VTON 모델 비교 실험
- 7개월 고도화용 후보 기술 정리

PC3 실험 결과는 다음 구조를 기준으로 관리한다.

```text
outputs/
  experiments/
    stableviton_batch/
    failure_cases/
    low_confidence_cases/
    fit_threshold_tests/
    confidence_tests/
    idm_test/
```

IDM-VTON은 시간이 남을 경우에만 진행하는 후순위 대체 VTON 비교 실험이다. IDM-VTON 작업이 오래 막히면 즉시 중단하고 StableVITON batch evaluation과 fit analyzer 실험을 우선한다.

LoRA는 한 달 MVP에서 제외하며, 7개월 고도화 단계에서 fit control 필요성이 명확해졌을 때 선택적으로 검토한다.

실제 output, generated image, dataset, checkpoint는 git에 커밋하지 않는다.
