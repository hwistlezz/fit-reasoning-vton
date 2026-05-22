# 로드맵

## Phase 0. 프로젝트 스캐폴드

- 저장소 문서 구조 생성
- 데이터 및 모델 가중치 커밋 방지 규칙 정리
- GPU 확인 스크립트 추가
- 외부 baseline 참조 방식 정리
- 라이선스 및 데이터셋 고지 추가

## Phase 1. Proposal 및 외부 Baseline 준비

- README를 proposal 제출용 구조로 정리
- IDM-VTON을 main baseline으로 외부 clone
- CatVTON은 optional comparison baseline으로 외부 참조 유지
- 외부 baseline 경로와 필수 파일 확인
- GPU 및 PyTorch CUDA 사용 가능 여부 확인
- IDM-VTON smoke test 실행 계획 수립
- 첫 try-on 결과 생성 여부 확인 계획 수립
- smoke test command, 외부 저장소 commit hash, GPU 정보 기록

## Phase 2. 최소 웹 데모

- 사람 이미지와 의류 이미지 업로드 화면 구현
- IDM-VTON inference를 외부 프로세스 또는 별도 실행 경로로 연결
- 생성 결과 이미지 표시
- 실행 실패 시 사용자에게 실패 상태 표시
- generated image는 GitHub에 커밋하지 않도록 유지

## Phase 3. 입력 품질 평가

- 사람 이미지의 포즈 안정성 확인
- 전신 또는 상반신 포함 여부 확인
- 가림, 잘림, 해상도 문제 기록
- 의류 이미지의 배경, 형태, 품질 문제 기록
- 입력 품질 점수 초안 구현

## Phase 4. 착장 결과 신뢰도 평가

- 포즈 일관성 분석
- 세그멘테이션 또는 human parsing 안정성 검토
- 실루엣 변화 분석
- 의류 색상·패턴·형태 보존 정도 분석
- fit confidence score 초안 구현

## Phase 5. Fit-Aware Reasoning

- 기장감, 품 여유, 소매 길이, 어깨선 등 시각적 핏 단서 정의
- rule-based reasoning 문장 생성
- 실패 원인 설명 문구 작성
- 성공/실패 사례를 구분해 기록

## Phase 6. Optional Comparison

- 시간이 허용되면 CatVTON smoke test 수행
- 같은 샘플에 대한 IDM-VTON과 CatVTON 결과 비교 계획 수립
- 비교 결과는 실제 실행 후에만 기록

## Phase 7. 후속 확장

- StableVITON 검토
- 2.5D 정보 활용 가능성 검토
- FIT 데이터셋 기반 fit-aware scoring 검토
- fine-tuning은 별도 후속 연구 주제로 분리
