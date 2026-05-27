# [Experiment] PC3 IDM-VTON comparison 및 LoRA feasibility 계획

## 목적

PC3에서 나중에 진행할 IDM-VTON 비교 실험과 oversized LoRA feasibility 실험 계획을 정리한다.

## 우선순위

이 이슈는 바로 시작하지 않는다. PC1 StableVITON MVP 서버가 잡힌 뒤 시작한다.

PC3 작업은 MVP를 방해하지 않는 후순위 보조 실험이다.

## PC3 역할

- oversized LoRA feasibility 실험
- IDM-VTON 단일 inference 비교 실험
- IDM이 오래 막히면 바로 LoRA 실험용으로 전환
- StableVITON vs IDM-VTON 비교 샘플 저장

## 체크리스트

- [ ] IDM-VTON 비교 기준 정리
- [ ] StableVITON vs IDM-VTON 비교 항목 정리
- [ ] 설치 난이도 기록 항목 정리
- [ ] VRAM 사용량 기록 항목 정리
- [ ] inference time 기록 항목 정리
- [ ] oversized LoRA feasibility 범위 정의
- [ ] PC3 시작 조건 정의

## 완료 기준

- [ ] PC3 작업이 MVP를 방해하지 않도록 후순위 계획으로 정리된다.
- [ ] IDM-VTON과 LoRA가 각각 어떤 목적의 보조 실험인지 명확해진다.

## 주의사항

- PC1 StableVITON MVP 서버가 먼저다.
- LoRA는 1개월 MVP 핵심 기능이 아니라 PC3 feasibility 수준으로만 다룬다.
- 비교 결과 이미지, checkpoint, dataset은 git에 커밋하지 않는다.
