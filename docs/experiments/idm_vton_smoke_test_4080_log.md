# IDM-VTON Smoke Test 4080 환경 및 Gradio 실행 로그

## 실험 개요

- 프로젝트명: Fit-Confidence Virtual Try-On (체형·핏 신뢰도 평가를 제공하는 가상 착장 웹 시스템)
- 실험 목적: RTX 4080 GPU 컴퓨터에서 IDM-VTON smoke test를 실행하기 위한 환경 세팅, 실행 과정, 트러블슈팅, 최종 Gradio demo 실행 결과를 기록한다.
- 현재 상태: IDM-VTON local Gradio demo smoke test 성공
- 기록일: 2026-05-20

본 프로젝트의 핵심 기여는 VTON 모델 자체 구현이 아니라, 기존 VTON 결과를 컴퓨터비전 특징 기반으로 분석하는 Fit-aware Reasoning Layer이다. 이번 로그에는 RTX 4080 환경에서 IDM-VTON local Gradio demo를 실행하기 위한 준비 과정과 smoke test 결과를 기록한다. 결과 이미지는 본 저장소에 커밋하지 않는다.

## 작업 브랜치

- 현재 작업 브랜치: `experiment/#1/idm-vton-smoke-test`
- 브랜치 목적: RTX 4080 GPU 컴퓨터에서 IDM-VTON smoke test를 준비하고, 환경 세팅 및 실행 과정을 문서화한다.

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

### 4. Checkpoint placeholder 문제와 해결

처음에는 `D:\GitHub\IDM-VTON\ckpt` 아래에 필요한 파일명이 존재했지만, 실제 checkpoint가 아니라 매우 작은 placeholder 파일이었다.

확인 명령어:

```powershell
Get-ChildItem .\ckpt\humanparsing -Recurse | Select-Object FullName, Length
Get-ChildItem .\ckpt\densepose -Recurse | Select-Object FullName, Length
Get-ChildItem .\ckpt\openpose -Recurse | Select-Object FullName, Length
```

초기 확인 결과:

```text
D:\GitHub\IDM-VTON\ckpt\humanparsing\parsing_atr.onnx          25
D:\GitHub\IDM-VTON\ckpt\humanparsing\parsing_lip.onnx          25
D:\GitHub\IDM-VTON\ckpt\densepose\model_final_162be9.pkl       31
D:\GitHub\IDM-VTON\ckpt\openpose\ckpts\body_pose_model.pth     28
```

이 상태에서 Gradio demo 실행 중 다음 오류가 발생했다.

```text
onnxruntime.capi.onnxruntime_pybind11_state.InvalidProtobuf:
[ONNXRuntimeError] : 7 : INVALID_PROTOBUF :
Load model from D:\GitHub\IDM-VTON\ckpt/humanparsing/parsing_atr.onnx failed:
Protobuf parsing failed.
```

원인은 checkpoint 경로에 파일은 있었지만 실제 모델 파일이 아니라 매우 작은 placeholder 파일이었고, ONNXRuntime이 `parsing_atr.onnx`를 정상적인 ONNX protobuf 모델로 읽지 못했기 때문이다.

해결 방법:

1. 기존 작은 checkpoint 파일을 삭제했다.
2. Hugging Face Space `yisol/IDM-VTON`에서 실제 checkpoint 파일을 재다운로드했다.

삭제 명령어:

```powershell
Remove-Item .\ckpt\humanparsing\parsing_atr.onnx
Remove-Item .\ckpt\humanparsing\parsing_lip.onnx
Remove-Item .\ckpt\densepose\model_final_162be9.pkl
Remove-Item .\ckpt\openpose\ckpts\body_pose_model.pth
```

재다운로드 스크립트:

```powershell
@'
from huggingface_hub import hf_hub_download

repo_id = "yisol/IDM-VTON"
repo_type = "space"
local_dir = r"D:\GitHub\IDM-VTON"

files = [
    "ckpt/humanparsing/parsing_atr.onnx",
    "ckpt/humanparsing/parsing_lip.onnx",
    "ckpt/densepose/model_final_162be9.pkl",
    "ckpt/openpose/ckpts/body_pose_model.pth",
]

for file in files:
    print(f"Downloading {file} ...")
    path = hf_hub_download(
        repo_id=repo_id,
        repo_type=repo_type,
        filename=file,
        local_dir=local_dir,
        local_dir_use_symlinks=False,
        force_download=True,
    )
    print(f"Saved to: {path}")

print("All checkpoint files downloaded.")
'@ | python
```

재다운로드 후 파일 크기:

```text
D:\GitHub\IDM-VTON\ckpt\humanparsing\parsing_atr.onnx      266859305
D:\GitHub\IDM-VTON\ckpt\humanparsing\parsing_lip.onnx      266863411
D:\GitHub\IDM-VTON\ckpt\densepose\model_final_162be9.pkl   255757821
D:\GitHub\IDM-VTON\ckpt\openpose\ckpts\body_pose_model.pth 209267595
```

위 checkpoint 파일은 외부 IDM-VTON 저장소 경로에 준비한 것이며, 본 저장소에 커밋하지 않는다.

### 5. Gradio / FastAPI / Starlette / Jinja2 호환 문제와 해결

checkpoint 문제 해결 후 Gradio demo를 다시 실행했지만, 웹 접속 과정에서 다음 오류가 발생했다.

```text
TypeError: unhashable type: 'dict'
```

당시 Gradio 관련 버전:

```text
gradio 4.24.0
fastapi 0.136.1
starlette 1.0.0
jinja2 3.1.6
pydantic 2.13.4
```

해결을 위해 다음 패키지 버전을 고정했다.

```powershell
python -m pip install "fastapi==0.110.0" "starlette==0.36.3" "jinja2==3.1.3"
python -m pip check
```

확인 결과:

```text
No broken requirements found.
```

### 6. Pydantic 호환 문제와 해결

그 다음 실행에서는 Gradio 서버는 열렸지만 API info 생성 과정에서 다음 오류가 발생했다.

```text
TypeError: argument of type 'bool' is not iterable
```

당시 Gradio 관련 버전:

```text
gradio 4.24.0
gradio_client 0.14.0
fastapi 0.110.0
starlette 0.36.3
jinja2 3.1.3
pydantic 2.13.4
```

해결을 위해 `pydantic`을 포함한 Gradio 관련 패키지 버전을 아래와 같이 고정했다.

```powershell
python -m pip install "gradio==4.24.0" "gradio_client==0.14.0" "pydantic==2.7.4" "fastapi==0.110.0" "starlette==0.36.3" "jinja2==3.1.3"
python -m pip check
```

확인 결과:

```text
No broken requirements found.
```

## Hugging Face cache 경로 설정

PowerShell에서 다음 환경 변수를 설정했다.

```powershell
$env:HF_HOME="D:\hf-cache"
$env:HF_HUB_CACHE="D:\hf-cache\hub"
New-Item -ItemType Directory -Force -Path $env:HF_HOME | Out-Null
New-Item -ItemType Directory -Force -Path $env:HF_HUB_CACHE | Out-Null
```

확인 결과:

```text
D:\hf-cache
D:\hf-cache\hub
```

목적:

- 모델 다운로드 cache를 D 드라이브에 저장한다.
- C 드라이브 용량 부담을 줄인다.

첫 Gradio demo 실행 시 Hugging Face에서 모델 파일들이 다운로드되었다.

다운로드된 주요 파일 예시:

```text
diffusion_pytorch_model.bin: 12.0G
model.safetensors: 492M
model.safetensors: 2.78G
model.safetensors: 2.53G
diffusion_pytorch_model.safetensors: 335M
diffusion_pytorch_model.safetensors: 10.3G
```

Windows symlink 관련 경고가 발생했지만, cache는 degraded mode로 동작하며 다운로드 자체는 진행되었다.

경고 요지:

```text
huggingface_hub cache-system uses symlinks by default ...
your machine does not support them ...
Caching files will still work but in a degraded version
```

이 경고는 blocking error가 아니라 warning으로 기록한다.

## 최종 고정된 Gradio 관련 버전

최종 Gradio 관련 버전은 다음과 같다.

```text
gradio 4.24.0
gradio_client 0.14.0
fastapi 0.110.0
starlette 0.36.3
jinja2 3.1.3
pydantic 2.7.4
```

## 최종 Gradio demo 실행 결과

최종 실행 명령어:

```powershell
$env:HF_HOME="D:\hf-cache"
$env:HF_HUB_CACHE="D:\hf-cache\hub"

cd D:\GitHub\IDM-VTON
python .\gradio_demo\app.py
```

성공 로그:

```text
Loading pipeline components...: 100%
Running on local URL:  http://127.0.0.1:7860
```

이후 Gradio UI에서 기본 example person image와 garment image를 사용해 Try-on을 실행했다. Gradio UI에서 output image가 생성되는 것을 시각적으로 확인했다.

생성 과정 로그:

```text
100%|████████████████████████████████████████████████████████████████████████| 30/30 [02:07<00:00,  4.25s/it]
```

한 번 더 실행했을 때:

```text
100%|████████████████████████████████████████████████████████████████████████| 30/30 [01:47<00:00,  3.57s/it]
```

위 시간은 공식 benchmark가 아니다. 단순히 local Gradio smoke test 실행 중 관찰된 실행 시간으로만 기록한다.

## Smoke test 결과 요약

- Status: Success
- Demo type: IDM-VTON local Gradio demo
- Machine: School RTX 4080 GPU workstation
- URL: `http://127.0.0.1:7860`
- Input: built-in example person image and garment image
- Output: try-on image generated and visually confirmed in Gradio UI
- Inference steps: 30
- Runtime observed: about 2 minutes for the first run, about 1 minute 47 seconds for a later run
- Note: This is not a formal benchmark. It only verifies that the local Gradio demo runs and generates an output image.

결과 이미지는 본 저장소에 커밋하지 않는다. README에도 결과 이미지나 benchmark처럼 보이는 성능 수치를 추가하지 않는다.

## 현재 남은 작업

아래 작업은 아직 남아 있다.

- 직접 촬영 이미지 또는 직접 고른 sample person / garment 이미지로 추가 테스트
- 생성 결과를 repository 밖 또는 ignored output 경로에 저장
- smoke test 결과를 기반으로 PR 생성
- 이후 Fit Confidence / Fit-aware Reasoning Layer 구현으로 넘어가기

외부 IDM-VTON 코드, checkpoint 파일, Hugging Face cache 파일, dataset 파일, generated image, UI screenshot은 본 저장소에 커밋하지 않는다.

## 다음 실행 계획

1. 직접 촬영 이미지 또는 직접 고른 sample person / garment 이미지를 준비한다.
2. 생성 결과 저장 위치를 repository 밖 또는 ignored output 경로로 정한다.
3. 추가 sample 기반 smoke test를 수행한다.
4. smoke test 결과를 기반으로 PR을 생성한다.
5. 이후 Fit Confidence / Fit-aware Reasoning Layer 구현으로 넘어간다.

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

초기 준비 단계에서는 `ckpt` 폴더와 하위 폴더가 존재했지만, 실제 필요한 checkpoint 파일이 들어 있는지는 확인이 필요했다. 이후 Gradio 실행 단계에서 작은 placeholder 파일 문제를 확인했고, Hugging Face Space `yisol/IDM-VTON`에서 실제 checkpoint 파일을 재다운로드했다.

- `D:\GitHub\IDM-VTON\ckpt\densepose\model_final_162be9.pkl`: 재다운로드 완료, 외부 경로 보관
- `D:\GitHub\IDM-VTON\ckpt\humanparsing\parsing_atr.onnx`: 재다운로드 완료, 외부 경로 보관
- `D:\GitHub\IDM-VTON\ckpt\humanparsing\parsing_lip.onnx`: 재다운로드 완료, 외부 경로 보관
- `D:\GitHub\IDM-VTON\ckpt\openpose\ckpts\body_pose_model.pth`: 재다운로드 완료, 외부 경로 보관

## Gradio demo 실행 전 체크리스트

- `D:\conda-envs\idm` 환경 활성화 확인
- `D:\GitHub\IDM-VTON` 외부 저장소 위치 확인
- 외부 IDM-VTON commit hash 기록 확인: `0d5f3ec2d737487a9bb24e4100936ad254780383`
- checkpoint 파일 존재 여부 확인
- built-in example person image 사용
- built-in example garment image 사용
- 실행 결과 저장 위치 결정
- generated image를 본 저장소에 커밋하지 않는 원칙 재확인

## checkpoint / Gradio demo 계획

Gradio demo 실행 명령어:

```powershell
$env:HF_HOME="D:\hf-cache"
$env:HF_HUB_CACHE="D:\hf-cache\hub"

cd D:\GitHub\IDM-VTON
python .\gradio_demo\app.py
```

위 명령어로 local Gradio demo 실행에 성공했다.
