# StableVITON 외부 설정

## 목적

PC1에서 StableVITON 외부 저장소와 `vton` conda environment를 준비하고, 우리 저장소에서 외부 StableVITON 경로를 참조할 수 있는 기본 구조를 정리한다.

이번 문서는 setup 준비 문서이다. StableVITON inference 성공, 결과 이미지 생성, 성능 수치, benchmark를 기록하지 않는다.

## StableVITON 역할

StableVITON은 MVP main VTON backbone이다.

PC1에서 StableVITON inference server와 FastAPI API server를 실행하고, 이후 `/api/tryon` 요청이 들어오면 StableVITON inference를 통해 result image를 생성하는 방향으로 간다.

핵심 기여는 StableVITON 자체 구현이 아니라 CV 기반 fit analyzer, confidence scoring, fit reasoning이다.

## 외부 clone 원칙

StableVITON source code, checkpoint, dataset, generated image는 본 저장소에 커밋하지 않는다.

StableVITON은 우리 repo 내부가 아니라 같은 상위 폴더에 외부 저장소로 clone한다.

## 권장 폴더 구조

Windows PC1 기준 권장 구조는 다음과 같다.

```text
D:\GitHub
├── fit-reasoning-vton
└── StableVITON
```

## clone 명령어

```powershell
cd D:\GitHub
git clone https://github.com/rlawjdghek/StableVITON.git
```

## commit hash 기록 방법

외부 StableVITON repository commit hash는 setup log와 이후 smoke test log에 반드시 기록한다.

```powershell
cd D:\GitHub\StableVITON
git rev-parse HEAD
```

## conda environment 원칙

- PC1에서는 StableVITON 실행용 conda environment를 `vton` 이름으로 준비한다.
- Python, PyTorch, CUDA 버전은 StableVITON 공식 README와 PC1 CUDA 상태를 기준으로 맞춘다.
- 환경 생성과 패키지 설치 결과는 `docs/experiments/stableviton_pc1_setup_log_template.md`를 복사해 실제 setup log에 기록한다.

예시:

```powershell
conda create -n vton python=3.10
conda activate vton
```

위 명령은 예시이며, 실제 Python/PyTorch 버전은 StableVITON 설치 과정에서 확인한 뒤 기록한다.

## checkpoint / dataset / generated image 관리 원칙

- checkpoint는 본 저장소에 커밋하지 않는다.
- dataset은 본 저장소에 커밋하지 않는다.
- generated image는 본 저장소에 커밋하지 않는다.
- Hugging Face cache는 본 저장소에 커밋하지 않는다.
- output image는 repository 밖 또는 ignored output 경로에 저장한다.

## PC1에서 확인할 기본 명령어

우리 repo에서 GPU 상태를 확인한다.

```powershell
cd D:\GitHub\fit-reasoning-vton
python .\scripts\check_gpu.py
```

우리 repo에서 외부 StableVITON 구조를 검증한다.

```powershell
cd D:\GitHub\fit-reasoning-vton
python .\scripts\verify_external_stableviton.py --stableviton-root ..\StableVITON
```

성공 시 외부 StableVITON 경로, README, 실행 파일 후보, 환경 파일 후보가 확인된다.

## 다음 단계

1. PC1에 StableVITON 외부 저장소를 clone한다.
2. 외부 StableVITON commit hash를 기록한다.
3. `vton` conda environment를 준비한다.
4. PyTorch CUDA와 RTX 4080 인식 여부를 확인한다.
5. StableVITON 필수 패키지 설치 상태를 기록한다.
6. 외부 StableVITON 구조 검증 helper를 실행한다.
7. 다음 이슈에서 StableVITON CLI smoke test를 진행한다.
