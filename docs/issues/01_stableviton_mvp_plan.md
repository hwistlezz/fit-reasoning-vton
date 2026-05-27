# [Docs] StableVITON 중심 MVP 계획 및 PC 역할 정리

## 목적

팀의 새 운영 계획에 맞춰 README와 주요 문서를 StableVITON 중심 MVP 구조로 수정합니다.

기존 문서에서는 IDM-VTON이 main baseline으로 표현되어 있었지만, 수정된 계획에서는 StableVITON을 MVP main backbone으로 사용하고, IDM-VTON은 PC3 비교 실험용으로 역할을 변경합니다.

## 배경

프로젝트의 최종 방향은 `Fit-aware Virtual Try-On Web Prototype`입니다. 논문 수준의 신규 모델 개발보다 RTX 4080 16GB GPU 환경에서 1개월 안에 실제 동작하는 제품형 AI 웹 프로토타입을 만드는 것이 목표입니다.

MVP 핵심은 LoRA가 아니라 `CV 기반 fit analyzer + confidence UX + 웹 데모`입니다.

## 체크리스트

- [ ] README의 모델 사용 방향 수정
- [ ] StableVITON을 MVP main backbone으로 명시
- [ ] IDM-VTON을 PC3 comparison baseline으로 변경
- [ ] CatVTON을 MVP 제외 또는 future optional baseline으로 정리
- [ ] docs/project_overview.md 수정
- [ ] docs/roadmap.md 수정
- [ ] PC별 역할 문서 추가 또는 수정
- [ ] 전체 pipeline 문서화
- [ ] fake result, checkpoint, dataset, generated image가 추가되지 않았는지 확인

## 전체 pipeline

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

## 완료 기준

- [ ] README와 주요 문서에서 StableVITON이 MVP main backbone으로 명확히 보인다.
- [ ] IDM-VTON은 PC3 비교 실험용으로 정리된다.
- [ ] PC1/PC2/PC3 역할과 전체 pipeline이 문서에 반영된다.
- [ ] 기존 IDM-VTON smoke test 기록은 삭제하지 않고 비교 실험 자산으로 유지된다.

## 주의사항

- 외부 모델 코드, checkpoint, dataset, generated image를 추가하지 않는다.
- StableVITON inference 성공이라고 쓰지 않는다.
- README에 생성 결과 이미지나 성능 수치를 추가하지 않는다.
