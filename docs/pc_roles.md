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

PC2는 CV preprocessing 전용이다.

- DWPose pose extraction
- SCHP human parsing
- input quality check
- fit feature extraction
- `datasets/raw`
- `datasets/processed`
- `datasets/features.csv`

PC2의 dataset, processed output, feature artifact는 저장소에 바로 커밋하지 않는다. 필요한 경우 작은 schema 또는 로그 문서만 별도로 정리한다.

## PC3

PC3는 후순위 보조 실험용이다.

- oversized LoRA feasibility 실험
- IDM-VTON 단일 inference 비교 실험
- StableVITON vs IDM-VTON 비교 샘플 저장

PC3는 PC1 MVP 서버가 어느 정도 잡힌 뒤 진행한다.

IDM-VTON 비교 실험에서는 StableVITON 대비 설치 난이도, VRAM 사용량, inference time, 결과 품질, API 통합 난이도를 기록한다. IDM-VTON 작업이 오래 막히면 MVP 보호를 위해 중단하고 PC3를 LoRA 실험용으로 전환한다.

LoRA는 MVP 필수 기능이 아니라 PC3에서 진행하는 후순위 feasibility 실험이다.
