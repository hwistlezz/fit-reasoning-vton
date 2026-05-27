# [Feat] StableVITON service wrapper 연결

## 목적

FastAPI backend에서 외부 StableVITON inference를 호출하는 service wrapper를 구현한다.

## 범위

외부 StableVITON 저장소는 우리 repo 밖에 둔다. backend는 설정된 외부 경로와 command wrapper를 통해 inference를 호출한다.

## 체크리스트

- [ ] 외부 StableVITON path 설정
- [ ] inference command wrapper 작성
- [ ] input image path 전달
- [ ] cloth image path 전달
- [ ] output image path 수집
- [ ] subprocess error handling
- [ ] timeout 처리
- [ ] GPU busy 상태 고려
- [ ] inference log 저장
- [ ] 실패 시 job status를 `failed`로 변경
- [ ] 성공 시 result image path 저장

## 완료 기준

- [ ] `/api/tryon` 요청이 StableVITON inference wrapper까지 연결된다.
- [ ] 성공 시 `result.png`가 `backend/outputs/{job_id}` 아래에 저장된다.
- [ ] 실패 시 오류 메시지가 job status에 기록된다.

## 주의사항

- 외부 StableVITON 코드, checkpoint, dataset을 우리 저장소에 복사하지 않는다.
- output image는 git ignored 경로에만 저장한다.
