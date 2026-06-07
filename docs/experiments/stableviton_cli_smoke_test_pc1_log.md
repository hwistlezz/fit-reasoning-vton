# StableVITON CLI Smoke Test PC1 Log

## 1. Experiment Overview

- Issue: #11
- Branch: `experiment/#11/pc1-stableviton-cli-smoke-test`
- Goal: PC1에서 StableVITON CLI inference smoke test
- Machine: PC1
- Status: In progress

이번 로그는 PC1에서 StableVITON을 CLI 또는 최소 실행 방식으로 smoke test하기 위한 기록 문서이다. 아직 실제 StableVITON inference 성공, result image 생성, runtime, VRAM 사용량은 기록하지 않는다.

## 2. Repository Layout

Windows 기준 권장 구조:

```text
D:\GitHub
├── fit-reasoning-vton
└── StableVITON
```

StableVITON source code, checkpoint, dataset, generated image는 본 저장소에 커밋하지 않는다.

## 3. External StableVITON

- Path: `D:\GitHub\StableVITON`
- Repository URL: `https://github.com/rlawjdghek/StableVITON.git`
- Commit hash: TBD

Commit hash 기록 명령어:

```powershell
cd D:\GitHub\StableVITON
git rev-parse HEAD
```

## 4. Environment

- Conda env: `vton`
- Python version: TBD
- PyTorch version: TBD
- CUDA availability: TBD
- CUDA device name: TBD

환경 확인 명령어:

```powershell
python --version
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

우리 repo에서 GPU 확인:

```powershell
cd D:\GitHub\fit-reasoning-vton
python .\scripts\check_gpu.py
```

## 5. External Repository Verification

우리 repo에서 실행할 명령어:

```powershell
cd D:\GitHub\fit-reasoning-vton
python .\scripts\verify_external_stableviton.py --stableviton-root ..\StableVITON
```

결과 기록:

```text
TBD
```

## 6. Checkpoint Preparation

StableVITON checkpoint는 외부 경로 또는 ignored path에서 관리하며, 본 저장소에 커밋하지 않는다.

- checkpoint source: TBD
- checkpoint local path: TBD
- required files: TBD
- status: TBD

## 7. Sample Input Preparation

sample image와 generated output은 repository에 커밋하지 않는다.

- person image path: TBD
- cloth image path: TBD
- source: TBD
- status: TBD

## 8. CLI Inference Command

아직 정확한 명령어는 확정하지 않았다. StableVITON 공식 README 확인 후 작성한다.

```powershell
# TBD: StableVITON 공식 README 확인 후 작성
```

명령어 후보를 기록할 경우, 아직 실행하지 않았다면 반드시 candidate로 표시한다.

## 9. Execution Result

- Status: Not yet executed
- Output path: TBD
- Runtime: TBD
- VRAM: TBD
- Result: TBD

Runtime과 VRAM은 공식 benchmark가 아니라 PC1 smoke test 중 관찰한 값으로만 기록한다.

## 10. Troubleshooting

No issue recorded yet.

향후 문제 발생 시 아래 형식으로 기록한다.

### Problem

TBD

### Error log

```text
TBD
```

### Cause

TBD

### Solution

TBD

### Result

TBD

## 11. Current Status

Completed:

- [ ] StableVITON external clone
- [ ] StableVITON commit hash recorded
- [ ] `vton` conda environment prepared
- [ ] PyTorch CUDA checked
- [ ] external StableVITON structure verified
- [ ] checkpoint prepared
- [ ] sample person / garment images prepared
- [ ] CLI inference command confirmed
- [ ] first smoke test executed

Not completed yet:

- [ ] result image generated
- [ ] runtime / VRAM recorded
- [ ] troubleshooting documented
- [ ] PR created

## 12. Next Action

1. Clone external StableVITON repository
2. Prepare `vton` conda environment
3. Verify PyTorch CUDA
4. Verify external StableVITON structure
5. Prepare checkpoint
6. Prepare sample person / garment image
7. Run CLI smoke test
8. Record success or failure

## Notes

- StableVITON 외부 repository 코드를 본 저장소에 복사하지 않는다.
- checkpoint 파일을 추가하지 않는다.
- dataset 파일을 추가하지 않는다.
- generated image를 추가하지 않는다.
- Hugging Face cache를 추가하지 않는다.
- sample image를 추가하지 않는다.
- fake result를 작성하지 않는다.
- StableVITON inference가 성공한 것처럼 쓰지 않는다.
- benchmark 수치를 작성하지 않는다.
- FastAPI backend 또는 frontend 구현을 시작하지 않는다.
