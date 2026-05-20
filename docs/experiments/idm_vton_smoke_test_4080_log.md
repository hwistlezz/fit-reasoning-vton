# IDM-VTON Smoke Test 4080 환경 준비 로그

## 실험 개요

- 프로젝트명: Fit-Confidence Virtual Try-On
- 한국어 제목: 체형·핏 신뢰도 평가를 제공하는 가상 착장 웹 시스템
- 실험 목적: RTX 4080 GPU 컴퓨터에서 IDM-VTON smoke test를 실행하기 위한 환경 세팅과 실행 준비 상태를 기록한다.
- 현재 상태: IDM-VTON inference 실행 전 준비 단계
- 기록일: 2026-05-20

본 프로젝트의 핵심 기여는 VTON 모델 자체 구현이 아니라, 기존 VTON 결과를 컴퓨터비전 특징 기반으로 분석하는 Fit-aware Reasoning Layer이다. 이번 로그에는 모델 실행 결과나 생성 이미지가 아니라, RTX 4080 환경에서 IDM-VTON을 실행하기 위한 준비 상태만 기록한다.

## 작업 브랜치

- 현재 작업 브랜치: `experiment/#1/idm-vton-smoke-test`
- 브랜치 목적: RTX 4080 GPU 컴퓨터에서 IDM-VTON smoke test를 준비하고, 환경 세팅 및 실행 준비 과정을 문서화한다.

## 저장소 구조

우리 프로젝트 저장소와 외부 IDM-VTON 저장소는 같은 상위 폴더 아래에 분리해서 둔다.

```text
D:\GitHub
├── fit-reasoning-vton
└── IDM-VTON
```

- 우리 저장소 위치: `D:\GitHub\fit-reasoning-vton`
- 외부 IDM-VTON 위치: `D:\GitHub\IDM-VTON`
- 외부 IDM-VTON 코드, checkpoint, dataset, generated image는 본 저장소에 커밋하지 않는다.

## 외부 IDM-VTON 정보

- 사용 모델: IDM-VTON
- 역할: main virtual try-on baseline
- 외부 저장소 경로: `D:\GitHub\IDM-VTON`
- 외부 IDM-VTON commit hash: `0d5f3ec2d737487a9bb24e4100936ad254780383`

위 commit hash는 이후 inference 실행 로그와 결과 분석 로그에도 함께 기록한다.

## GPU / Python / PyTorch / CUDA 환경

다음 명령어로 GPU와 PyTorch CUDA 상태를 확인했다.

```powershell
python .\scripts\check_gpu.py
```

확인 결과:

```text
Python version: 3.10.20 (CPython)
PyTorch version: 2.0.1
CUDA availability: True
CUDA device name: NVIDIA GeForce RTX 4080
CUDA device count: 1
```

따라서 현재 PyTorch에서 RTX 4080 GPU를 사용할 수 있는 상태로 확인했다.

## conda 환경

- Miniconda 설치 위치: `D:\miniconda3`
- conda version: `conda 26.3.2`
- conda 환경 저장 위치: `D:\conda-envs`
- conda 패키지 캐시 위치: `D:\conda-pkgs`
- IDM-VTON용 conda 환경 경로: `D:\conda-envs\idm`
- 프롬프트 예시: `(D:\conda-envs\idm) PS D:\GitHub\fit-reasoning-vton>`

C 드라이브 용량 부담을 줄이기 위해 conda 환경과 패키지 캐시를 D 드라이브에 두도록 구성했다.

## 설치 또는 확인된 주요 패키지

다음 패키지를 설치 또는 import 확인했다.

- `accelerate==0.25.0`
- `torchmetrics==1.2.1`
- `tqdm==4.66.1`
- `transformers==4.36.2`
- `diffusers==0.25.0`
- `einops==0.7.0`
- `scipy==1.11.1`
- `opencv-python`
- `gradio==4.24.0`
- `fvcore`
- `cloudpickle`
- `omegaconf`
- `pycocotools`
- `basicsr`
- `av`
- `onnxruntime==1.16.2`
- `huggingface_hub==0.20.2`
- `numpy==1.26.4`

기본 import 확인 명령어:

```powershell
python -c "import torch, diffusers, transformers, accelerate, gradio, cv2; print('basic imports ok')"
```

결과:

```text
basic imports ok
```

pip 의존성 확인:

```powershell
python -m pip check
```

결과:

```text
No broken requirements found.
```

## 외부 IDM-VTON 구조 검증 결과

다음 명령어로 외부 IDM-VTON 저장소의 기본 구조를 확인했다.

```powershell
python .\scripts\verify_external_idm_vton.py --idm-vton-root ..\IDM-VTON
```

결과:

```text
확인 대상 IDM-VTON 경로: ..\IDM-VTON
경로 확인: 성공 - IDM-VTON 디렉터리가 존재합니다.
README 확인: 성공 - README.md
inference 후보 확인: 성공 - inference.py
환경 파일 후보 확인: 성공 - environment.yaml
검증 결과: 성공 - 외부 IDM-VTON 저장소의 기본 구조가 확인되었습니다.
```

## 해결한 트러블슈팅

### 1. conda 미설치 및 D 드라이브 환경 구성

처음에는 `conda` 명령어를 사용할 수 없었으나, Miniconda를 `D:\miniconda3`에 설치하고 PowerShell에서 정상 인식되도록 설정했다.

C 드라이브 용량 부담을 줄이기 위해 conda 환경과 패키지 캐시를 D 드라이브로 설정했다.

- Miniconda: `D:\miniconda3`
- conda envs: `D:\conda-envs`
- conda pkgs: `D:\conda-pkgs`
- IDM env: `D:\conda-envs\idm`

### 2. huggingface_hub cached_download 오류

처음에는 `huggingface_hub==0.36.2` 때문에 다음 오류가 발생했다.

```text
ImportError: cannot import name 'cached_download' from 'huggingface_hub'
```

원인은 `diffusers==0.25.0`에서 `cached_download`를 필요로 하지만, 최신 `huggingface_hub`에서는 해당 함수가 제거되었기 때문이다.

해결 방법:

```powershell
pip install huggingface_hub==0.20.2
```

확인 결과:

```text
huggingface_hub 0.20.2
cached_download ok
```

### 3. PyTorch CUDA 확인

RTX 4080 환경에서 PyTorch CUDA 사용 가능 여부를 확인했다.

```text
CUDA availability: True
CUDA device name: NVIDIA GeForce RTX 4080
CUDA device count: 1
```

## 아직 하지 않은 작업

아래 작업은 아직 수행하지 않았다.

- IDM-VTON inference 실행
- checkpoint 다운로드
- sample person / garment 이미지 준비
- generated image 생성
- 결과 이미지 저장
- README에 실제 결과 추가
- PR 생성

따라서 현재 문서에는 inference 성공, 결과 이미지 생성 성공, 성능 수치, 성공 사례를 기록하지 않는다.

## 다음 실행 계획

1. IDM-VTON 공식 README 기준으로 필요한 checkpoint 파일을 준비한다.
2. checkpoint 폴더 구조와 실제 파일 존재 여부를 확인한다.
3. sample person / garment 이미지를 준비한다.
4. Gradio demo 실행 전 import와 경로를 다시 확인한다.
5. local Gradio demo를 실행한다.
6. demo가 정상 실행되면 별도 smoke test 로그에 실행 명령어, 입력 이미지 경로, 출력 경로, 관찰 결과를 기록한다.

## checkpoint 준비 체크리스트

IDM-VTON 공식 README 기준 local Gradio demo 실행을 위해 checkpoint가 필요하다.

Gradio demo checkpoint 구조는 다음과 같이 준비되어야 한다.

```text
D:\GitHub\IDM-VTON\ckpt
├── densepose
│   └── model_final_162be9.pkl
├── humanparsing
│   ├── parsing_atr.onnx
│   └── parsing_lip.onnx
└── openpose
    └── ckpts
        └── body_pose_model.pth
```

현재 `ckpt` 폴더와 하위 폴더는 존재하지만, 실제 필요한 checkpoint 파일이 들어 있는지는 아직 확인하지 않았다. 따라서 checkpoint 파일 준비 상태는 **확인 필요**로 둔다.

- `D:\GitHub\IDM-VTON\ckpt\densepose\model_final_162be9.pkl`: 확인 필요
- `D:\GitHub\IDM-VTON\ckpt\humanparsing\parsing_atr.onnx`: 확인 필요
- `D:\GitHub\IDM-VTON\ckpt\humanparsing\parsing_lip.onnx`: 확인 필요
- `D:\GitHub\IDM-VTON\ckpt\openpose\ckpts\body_pose_model.pth`: 확인 필요

## Gradio demo 실행 전 체크리스트

- `D:\conda-envs\idm` 환경 활성화 확인
- `D:\GitHub\IDM-VTON` 외부 저장소 위치 확인
- 외부 IDM-VTON commit hash 기록 확인: `0d5f3ec2d737487a9bb24e4100936ad254780383`
- checkpoint 파일 존재 여부 확인
- sample person 이미지 준비
- sample garment 이미지 준비
- 실행 결과 저장 위치 결정
- generated image를 본 저장소에 커밋하지 않는 원칙 재확인

## checkpoint / Gradio demo 계획

Gradio demo 실행 명령어 후보:

```powershell
cd D:\GitHub\IDM-VTON
python .\gradio_demo\app.py
```

위 명령어는 아직 실행하지 않았다. 현재 상태는 **실행 예정**이다.
