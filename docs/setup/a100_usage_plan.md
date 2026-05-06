# A100 GPU 사용 계획

## 목적

NVIDIA A100 GPU는 CatVTON baseline inference, baseline evaluation, fine-tuning 실험, 대규모 이미지 생성 실험에 사용한다. 본 프로젝트는 A100을 통해 여러 데이터셋 샘플에 대해 안정적으로 virtual try-on 결과를 생성하고, 이후 fit-aware 분석과 batch feature extraction을 수행할 수 있도록 준비한다.

## 사용 범위

- pretrained CatVTON baseline inference
- CatVTON baseline evaluation을 위한 대규모 결과 생성 및 샘플링
- VITON-HD 전체 또는 샘플 subset inference
- 선택적 DressCode inference
- fine-tuning 실험 준비 및 제한적 학습 실험
- fit-aware feature 후보 검증을 위한 batch feature extraction 준비
- 생성 결과 품질 점검용 batch inference

## 실행 전 확인 항목

- GPU 사용 가능 여부
- CUDA 및 PyTorch 호환 여부
- CatVTON 환경 설치 여부
- checkpoint 경로
- 입력 데이터 경로
- 출력 디렉터리 용량
- batch size와 image resolution 설정

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
- CatVTON commit 또는 버전
- checkpoint 이름
- 데이터셋 이름
- 샘플 수
- batch size
- resolution
- 실행 시간
- 실패 샘플 수

## 향후 작성 항목

- 실제 A100 서버 접속 방식
- job scheduler 사용 여부
- batch inference command
- mixed precision 사용 여부
- 실패 시 재시작 전략
