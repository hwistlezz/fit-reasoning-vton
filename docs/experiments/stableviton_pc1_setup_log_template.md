# StableVITON PC1 Setup Log

## 1. Experiment Overview

- Issue:
- Date:
- Machine:
- OS:
- GPU:
- Goal:

## 2. Repository Layout

```text
D:\GitHub
├── fit-reasoning-vton
└── StableVITON
```

## 3. Branch

- Working branch:

## 4. External StableVITON

- Path:
- Repository URL:
- Commit hash:

## 5. Conda Environment

- Environment name:
- Python version:
- PyTorch version:
- CUDA availability:
- CUDA device name:

## 6. Verification Commands

```powershell
python .\scripts\check_gpu.py
python .\scripts\verify_external_stableviton.py --stableviton-root ..\StableVITON
```

## 7. Installed Packages

TBD

## 8. Troubleshooting

TBD

## 9. Current Status

Completed:

- [ ] fit-reasoning-vton clone
- [ ] StableVITON external clone
- [ ] conda environment setup
- [ ] PyTorch CUDA check
- [ ] StableVITON repository structure verification

Not completed yet:

- [ ] StableVITON CLI inference
- [ ] checkpoint download
- [ ] sample person / garment image preparation
- [ ] generated image creation
- [ ] FastAPI server connection

## 10. Next Action

- Prepare checkpoint
- Run StableVITON CLI smoke test
- Record success/failure result

## Notes

이 파일은 setup log template이다. 아직 실제 PC1 setup 결과가 없다면 값을 실제처럼 채우지 말고 빈 항목 또는 TBD로 둔다.

StableVITON source code, checkpoint, dataset, generated image, Hugging Face cache는 본 저장소에 커밋하지 않는다.
