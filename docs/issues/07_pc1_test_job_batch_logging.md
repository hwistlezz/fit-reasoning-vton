# [Experiment] PC1 test job batch 및 성능 로그 기록

## 목적

PC1에서 여러 샘플 job을 실행하고 inference time, VRAM, success/failure를 기록한다.

## 범위

StableVITON API가 단일 요청을 처리할 수 있게 된 뒤, 3~5개 sample pair를 대상으로 batch 실행과 로그 기록을 진행한다.

## 체크리스트

- [ ] 3~5개 sample pair 준비
- [ ] batch 실행 스크립트 작성
- [ ] inference time 기록
- [ ] peak VRAM 또는 `nvidia-smi` 로그 기록
- [ ] success/failure 기록
- [ ] 실패 사례 원인 기록
- [ ] 결과 이미지는 저장소에 커밋하지 않음
- [ ] 실험 로그 문서화

## 완료 기준

- [ ] PC1에서 StableVITON API가 여러 샘플 요청을 처리할 수 있다.
- [ ] 최소 3개 이상의 샘플 job 결과가 로그로 정리된다.
- [ ] output image는 repository가 아니라 ignored output path에 저장된다.

## 주의사항

- 기록된 실행 시간과 VRAM은 개발 환경 smoke/batch log이며 공식 benchmark가 아니다.
- dataset, generated image, UI screenshot을 커밋하지 않는다.
