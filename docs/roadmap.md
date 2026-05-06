# 로드맵

## Phase 0. 프로젝트 스캐폴드

- 저장소 문서 구조 생성
- 데이터 및 모델 가중치 커밋 방지 규칙 정리
- GPU 확인 스크립트 추가
- CatVTON 외부 참조 방식 정리

## Phase 1. 외부 CatVTON 설정 및 Smoke Test

- 공식 CatVTON 저장소를 `fit-reasoning-vton/` 외부에 clone
- CatVTON README 기준 conda 환경 설정
- 외부 CatVTON 경로와 필수 파일 확인
- GPU 및 PyTorch CUDA 사용 가능 여부 확인
- Gradio smoke test 실행
- checkpoint 다운로드 또는 로딩 성공 여부 확인
- 첫 try-on 결과 생성 여부 확인
- smoke test command, CatVTON commit hash, GPU 정보 기록
- VITON-HD와 DressCode 로컬 데이터셋 경로 계획 정리

## Phase 2. Baseline Inference

- pretrained CatVTON으로 baseline 결과 생성
- inference 결과 저장 구조 확정
- 실패 케이스와 품질 이슈를 기록
- 생성 이미지와 원본 paired target을 구분하여 관리

## Phase 3. Baseline Evaluation

- 정량 평가 후보 지표 검토
- 정성 평가 기준 작성
- baseline 결과 샘플링 및 검수
- 향후 fine-tuning 비교 기준 확정

## Phase 4. Fit-Aware Feature 설계

- segmentation, pose, parsing 결과 활용 가능성 검토
- `width_ratio`, `length_ratio`, `silhouette_ratio`, `shoulder_ratio`, `hem_position` 정의
- feature 계산 단위와 예외 처리 규칙 설계
- 시각화 overlay 초안 작성

## Phase 5. Pseudo Labeling 및 Gold Set

- rule-based pseudo labeler 설계
- 사람이 검수할 gold set 샘플링 기준 수립
- 검수 기준표 작성
- pseudo label과 gold label의 차이 분석

## Phase 6. Classifier 비교

- rule-based labeling과 feature-based classifier 비교
- 학습/검증/테스트 분리 기준 확정
- 분석 신뢰도 계산 방식 정의
- 오류 유형을 카테고리화

## Phase 7. Fine-Tuning 실험

- real paired target 기반 fine-tuning 실험 계획 확정
- CatVTON pseudo target을 학습 정답으로 사용할 때의 한계 명시
- baseline과 fine-tuned 결과 비교
- 실험 로그와 재현성 정보 정리

## Phase 8. Explanation 및 UI

- overlay visualization 생성
- 자연어 설명 템플릿 설계
- Fit Report UI 요구사항 정리
- 사용자에게 과도한 사이즈 예측으로 오해되지 않는 표현 검토
