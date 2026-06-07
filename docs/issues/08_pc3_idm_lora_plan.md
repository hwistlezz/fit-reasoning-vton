# [Experiment] PC3 StableVITON batch evaluation 및 confidence 실험 계획

## 목적

PC3를 StableVITON 결과 대량 평가, failure case 수집, fit analyzer threshold 실험, confidence scoring 실험용 PC로 정리한다.

## 우선순위

PC3는 PC1 StableVITON API가 최소 동작한 뒤 시작한다.

한 달 MVP에서는 LoRA 학습을 제외하고, StableVITON 결과 평가와 fit analyzer / confidence 실험을 우선한다.

## PC3 역할

- StableVITON batch test
- 대량 inference 결과 평가
- failure case 수집
- low confidence case 수집
- fit analyzer threshold 실험
- confidence scoring 실험
- 시간이 남을 경우에만 IDM-VTON 등 대체 VTON 모델 비교
- 7개월 고도화용 후보 기술 정리

## 체크리스트

- [ ] StableVITON batch test 실행 계획 정리
- [ ] `outputs/experiments/` 실험 결과 폴더 구조 정리
- [ ] inference time 기록 방식 정리
- [ ] VRAM 사용량 기록 방식 정리
- [ ] failure case 수집 기준 정리
- [ ] low confidence case 수집 기준 정리
- [ ] fit analyzer threshold 실험 계획 정리
- [ ] confidence score calibration 실험 계획 정리
- [ ] 발표용 성공 샘플 / 실패 샘플 분리 기준 정리
- [ ] IDM-VTON 비교 실험을 후순위 실험으로 정리
- [ ] LoRA를 7개월 고도화 optional 실험으로 이동

## 완료 기준

- [ ] PC3 역할이 LoRA 학습 전용이 아니라 batch evaluation / failure analysis / confidence experiment 중심으로 정리된다.
- [ ] StableVITON batch test 결과 저장 경로가 문서화된다.
- [ ] failure case와 low confidence case 수집 기준이 정리된다.
- [ ] fit threshold 실험 계획이 정리된다.
- [ ] confidence score 실험 계획이 정리된다.
- [ ] inference time / VRAM 로그 기록 방식이 정리된다.
- [ ] IDM-VTON은 시간이 남을 경우에만 진행하는 후순위 비교 실험으로 정리된다.
- [ ] LoRA는 MVP에서 제외되고 7개월 고도화 optional 실험으로 정리된다.

## 주의사항

- PC1 StableVITON API 최소 동작이 먼저다.
- LoRA는 한 달 MVP 핵심 기능이 아니다.
- IDM-VTON 설치나 실행이 오래 막히면 즉시 중단하고 StableVITON batch evaluation과 fit analyzer 실험을 우선한다.
- 실제 output, generated image, checkpoint, dataset은 git에 커밋하지 않는다.
