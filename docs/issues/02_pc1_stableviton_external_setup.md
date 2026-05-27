# [Experiment] PC1 StableVITON external setup 준비

## 목적

PC1에 StableVITON 외부 저장소와 `vton` conda environment를 준비하고, 우리 저장소에서 외부 StableVITON을 참조할 수 있는 기본 구조를 만든다.

## PC1 역할

- StableVITON main inference server
- FastAPI API server
- 실제 VTON 결과 생성
- 데모 API 서버
- test job batch 실행
- inference 시간 / VRAM / 성공률 로그 기록
- API port: `8000`
- output path: `backend/outputs/`

## 체크리스트

- [ ] PC1에 Git / Python / conda 상태 확인
- [ ] PC1에 fit-reasoning-vton clone
- [ ] dev 기준 작업 브랜치 생성
- [ ] StableVITON 외부 저장소 clone
- [ ] StableVITON commit hash 기록
- [ ] `vton` conda environment 생성
- [ ] PyTorch CUDA 사용 가능 여부 확인
- [ ] RTX 4080 GPU 인식 확인
- [ ] StableVITON 필수 패키지 설치
- [ ] 외부 모델 코드가 우리 repo에 들어가지 않았는지 확인
- [ ] setup log 문서화

## 완료 기준

- [ ] PC1에서 PyTorch CUDA가 정상 확인된다.
- [ ] 외부 StableVITON 저장소가 우리 repo 밖에 clone되어 있다.
- [ ] StableVITON commit hash와 환경 정보가 문서에 기록되어 있다.

## 주의사항

- 외부 StableVITON 코드는 우리 저장소 밖에 둔다.
- checkpoint, dataset, generated image를 커밋하지 않는다.
- 아직 inference 성공으로 기록하지 않는다.
