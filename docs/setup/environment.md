# 환경 설정

## 목적

이 문서는 프로젝트 개발 및 실험을 위한 기본 환경 원칙을 정리한다. 현재 단계에서는 불필요한 의존성을 추가하지 않는다.

## 기본 요구사항

- Python 3.10 이상 권장
- Git
- NVIDIA GPU 환경 권장
- 대규모 inference는 NVIDIA A100 GPU 환경에서 수행
- PyTorch는 CatVTON 실행 환경에 맞춰 별도로 설치

## 로컬 저장소 원칙

이 저장소에는 다음 파일만 커밋한다.

- 문서
- 경량 스크립트
- 향후 작성될 feature extraction 및 분석 코드
- 실험 설정 템플릿

다음 항목은 커밋하지 않는다.

- 대용량 데이터셋
- CatVTON 체크포인트
- 생성 이미지
- 실험 로그
- 모델 가중치
- 외부 저장소를 복사한 코드

## 권장 디렉터리 배치

CatVTON은 이 저장소에 직접 복사하지 않고 별도 위치에서 관리한다.

예시:

```text
workspace/
  fit-reasoning-vton/
  CatVTON/
  datasets/
    VITON-HD/
    DressCode/
```

이 방식은 본 프로젝트의 분석 코드와 baseline 모델 코드를 분리하여 유지보수성을 높인다.

## GPU 확인

다음 스크립트로 현재 Python, PyTorch, CUDA 상태를 확인한다.

```bash
python scripts/check_gpu.py
```

## 향후 추가 예정

- Conda 또는 venv 기반 환경 파일
- CatVTON 실행용 PyTorch/CUDA 버전 기록
- inference job 실행 스크립트
- 실험별 설정 파일
