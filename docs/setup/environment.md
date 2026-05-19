# 환경 설정

## 목적

이 문서는 Fit-Confidence Virtual Try-On 프로젝트의 기본 환경 원칙을 정리한다. 현재 단계에서는 proposal과 외부 baseline 준비가 목적이며, 불필요한 의존성을 본 저장소에 추가하지 않는다.

## 기본 요구사항

- Python 3.10 이상 권장
- Git
- NVIDIA GPU 환경 권장
- 메인 baseline인 IDM-VTON 실행 환경은 외부 저장소에서 별도로 구성
- CatVTON은 optional comparison baseline으로 외부 저장소에서 별도로 구성

## 로컬 저장소 원칙

이 저장소에는 다음 파일만 커밋한다.

- 문서
- 경량 스크립트
- 설정 예시
- 향후 작성될 웹 데모와 Fit-aware Reasoning Layer 코드

다음 항목은 커밋하지 않는다.

- 외부 VTON 모델 source code
- 대용량 데이터셋
- checkpoint 및 model weight
- 생성 이미지
- 실험 로그 원본 파일
- 로컬 환경 파일

## 권장 디렉터리 배치

외부 baseline은 이 저장소에 직접 복사하지 않고 별도 위치에서 관리한다.

```text
workspace/
  fit-reasoning-vton/
  IDM-VTON/
  CatVTON/
  datasets/
    VITON-HD/
    DressCode/
  checkpoints/
    IDM-VTON/
    CatVTON/
```

이 방식은 본 프로젝트의 웹/분석 코드와 외부 VTON baseline 코드를 분리하여 유지보수성을 높인다.

## GPU 확인

다음 스크립트로 현재 Python, PyTorch, CUDA 상태를 확인한다.

```bash
python scripts/check_gpu.py
```

## 향후 추가 예정

- IDM-VTON 실행 환경 기록
- 샘플 이미지 smoke test 기록
- 웹 데모 실행 방법
- Fit confidence score 설정 파일
