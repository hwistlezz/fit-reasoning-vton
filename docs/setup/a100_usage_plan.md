# GPU 사용 계획

## 목적

GPU는 외부 VTON baseline smoke test와 이후 웹 데모 inference에 사용한다. 이번 텀프로젝트의 우선 대상은 IDM-VTON이며, CatVTON은 optional comparison baseline으로 필요한 경우에만 실행한다.

## 사용 범위

- IDM-VTON smoke test
- 샘플 이미지 기반 virtual try-on inference
- 웹 데모용 단일 또는 소규모 batch inference
- 입력 품질 평가와 착장 결과 신뢰도 분석에 필요한 경량 컴퓨터비전 처리
- 선택적 CatVTON smoke test 또는 비교 실험

## 실행 전 확인 항목

- GPU 사용 가능 여부
- CUDA 및 PyTorch 호환 여부
- 외부 IDM-VTON 경로
- checkpoint 경로
- 샘플 person image와 garment image 경로
- 출력 디렉터리 용량

## 리소스 관리 원칙

- 원본 데이터셋과 생성 이미지는 GitHub에 커밋하지 않는다.
- 실험별 출력 경로를 분리한다.
- 동일 실험을 반복 실행할 때 기존 결과를 덮어쓰지 않도록 run id를 사용한다.
- GPU 메모리 사용량과 처리 시간을 실험 로그에 기록한다.

## 실험 로그에 기록할 항목

- 날짜
- 실행자
- GPU 종류
- GPU 개수
- PyTorch 버전
- CUDA 사용 가능 여부
- 외부 baseline 이름
- 외부 baseline commit hash
- checkpoint 이름
- 샘플 수
- 입력 이미지 경로
- 출력 경로
- 실행 시간
- 실패 여부

## 향후 작성 항목

- 실제 GPU 서버 접속 방식
- IDM-VTON inference command
- mixed precision 사용 여부
- 실패 시 재시작 전략
