# [Experiment] PC1 StableVITON CLI inference smoke test

## 목적

PC1에서 StableVITON을 CLI 또는 최소 실행 방식으로 smoke test하고, 사람 이미지 + 의류 이미지로 result image 생성 가능 여부를 확인한다.

## 범위

이 이슈는 StableVITON을 FastAPI backend에 연결하기 전, PC1에서 단독 실행 가능 여부를 확인하는 작업이다. 성공 또는 실패 모두 실험 로그로 기록한다.

## 체크리스트

- [ ] StableVITON checkpoint 준비
- [ ] sample person image 준비
- [ ] sample garment image 준비
- [ ] CLI inference command 확인
- [ ] 첫 실행 시도
- [ ] 성공 또는 실패 로그 기록
- [ ] inference time 기록
- [ ] VRAM 사용량 기록
- [ ] output path 기록
- [ ] generated image는 git에 커밋하지 않음
- [ ] troubleshooting 문서화

## 완료 기준

- [ ] StableVITON inference 명령어가 확인된다.
- [ ] 성공 시 result image가 repo 밖 또는 ignored output 경로에 생성된다.
- [ ] 실패 시 오류 로그와 다음 조치가 문서화된다.

## 주의사항

- 실행 시간이 기록되더라도 공식 benchmark처럼 표현하지 않는다.
- generated image, UI screenshot, checkpoint를 커밋하지 않는다.
- README에는 결과 이미지나 성능 수치를 추가하지 않는다.
