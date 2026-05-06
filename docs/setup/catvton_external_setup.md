# CatVTON 외부 저장소 설정

## 목적

이 문서는 CatVTON을 본 저장소에 복사하지 않고 외부 저장소로 관리하기 위한 Phase 1 설정 절차를 정리한다. 현재 단계의 목표는 CatVTON 실행 환경을 준비하고, Gradio smoke test로 첫 실행 가능 여부를 확인하며, 이후 실험 재현성을 위해 필요한 정보를 기록하는 것이다.

## CatVTON을 외부 저장소로 관리하는 이유

CatVTON은 별도의 연구 코드와 실행 환경을 가진 pretrained virtual try-on baseline이다. 본 저장소는 CatVTON 자체를 수정하거나 복제하는 저장소가 아니라, CatVTON 결과를 기반으로 fit-aware 분석과 설명 레이어를 준비하는 저장소이다.

외부 저장소로 분리하면 다음 장점이 있다.

- 원본 CatVTON 코드와 본 프로젝트 분석 코드를 명확히 분리할 수 있다.
- CatVTON upstream 변경 이력을 별도 commit hash로 기록할 수 있다.
- 대용량 checkpoint, generated image, log가 본 저장소에 섞이는 것을 방지할 수 있다.
- 향후 baseline, fine-tuning, 분석 실험의 재현성을 더 명확히 관리할 수 있다.

## 라이선스 주의

외부 clone 구조는 CatVTON 원본 코드를 본 저장소에 재배포하지 않기 위한 구조이다. CatVTON을 사용할 때는 원저작자와 공식 저장소의 라이선스를 표시하고, 사용 범위가 라이선스 조건에 맞는지 확인해야 한다.

CatVTON 공식 저장소 기준 라이선스는 Creative Commons BY-NC-SA 4.0으로 안내되어 있다. 상업적 사용은 별도 확인이 필요하며, 수정한 CatVTON 코드를 공개하는 경우에도 원 라이선스 조건을 확인해야 한다.

## 권장 작업 공간 구조

```text
workspace/
  fit-reasoning-vton/
  CatVTON/
  datasets/
    VITON-HD/
    DressCode/
```

`fit-reasoning-vton/`은 본 저장소이고, `CatVTON/`은 공식 CatVTON 저장소를 별도로 clone한 위치이다. `datasets/`는 원본 데이터셋을 두는 로컬 경로이며 GitHub에 커밋하지 않는다.

## CatVTON Clone

작업 공간의 상위 디렉터리에서 다음 명령을 실행한다.

```bash
git clone https://github.com/Zheng-Chong/CatVTON.git
```

CatVTON 코드를 `fit-reasoning-vton/` 내부로 복사하지 않는다.

## CatVTON Commit Hash 기록

CatVTON 디렉터리에서 다음 명령으로 현재 commit hash를 기록한다.

```bash
cd CatVTON
git rev-parse HEAD
```

이 값은 smoke test log, baseline inference log, fine-tuning 실험 계획에 함께 기록한다.

## Conda 환경 설정

CatVTON README 기준 환경을 별도로 구성한다.

```bash
cd CatVTON
conda create -n catvton python==3.9.0
conda activate catvton
pip install -r requirements.txt
```

본 저장소에는 CatVTON 의존성을 추가하지 않는다. CatVTON 실행에 필요한 Python 패키지는 `catvton` conda 환경에 설치한다.

## GPU 확인

CatVTON 환경 활성화 후 GPU와 PyTorch 상태를 확인한다.

```bash
python -c "import torch; print('torch:', torch.__version__); print('cuda:', torch.cuda.is_available()); print('count:', torch.cuda.device_count()); print('device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

본 저장소의 경량 점검 스크립트도 사용할 수 있다.

```bash
cd fit-reasoning-vton
python scripts/check_gpu.py
```

## 외부 CatVTON 경로 검증

본 저장소에서 CatVTON 외부 clone 위치가 예상 구조를 갖는지 확인한다.

```bash
python scripts/verify_external_catvton.py --catvton-root ../CatVTON
```

이 스크립트는 CatVTON을 import하지 않고, 필수 파일 존재 여부만 확인한다.

## Gradio Smoke Test

CatVTON 디렉터리에서 다음 명령으로 Gradio demo 실행 여부를 확인한다.

```bash
CUDA_VISIBLE_DEVICES=0 python app.py \
  --output_dir="resource/demo/output" \
  --mixed_precision="bf16" \
  --allow_tf32
```

확인할 항목은 다음과 같다.

- `app.py`가 오류 없이 시작되는지
- checkpoint 다운로드 또는 로딩이 성공하는지
- Gradio URL이 출력되는지
- 첫 try-on 결과 이미지가 생성되는지
- 생성 결과가 CatVTON 외부 저장소 또는 별도 output 경로에 저장되는지

## 수동 저장할 스크린샷과 로그

다음 자료는 실험 기록용으로 수동 저장한다. 단, 대용량 파일이나 생성 이미지는 본 저장소에 커밋하지 않는다.

- Gradio 실행 화면 스크린샷
- 첫 try-on 결과 확인용 스크린샷
- 실행 command
- CatVTON commit hash
- GPU 이름과 개수
- PyTorch 버전
- CUDA 사용 가능 여부
- checkpoint 다운로드 성공 여부
- 오류 발생 시 terminal log 일부

로그 내용은 [CatVTON smoke test 로그 템플릿](../experiments/catvton_smoke_test_log_template.md)에 요약해서 기록한다.

## 커밋하지 않을 항목

다음 항목은 본 저장소에 커밋하지 않는다.

- CatVTON 원본 소스 코드
- VITON-HD, DressCode 등 원본 데이터셋
- checkpoint 및 model weight
- generated try-on image
- Gradio output
- inference output
- experiment log 원본 파일
- 대용량 압축 파일
- 로컬 환경 파일

## 문제 해결 메모

향후 실제 smoke test 중 발생한 문제를 아래에 정리한다.

### CUDA 또는 PyTorch 문제

- 향후 작성

### Checkpoint 다운로드 문제

- 향후 작성

### Gradio 실행 문제

- 향후 작성

### 첫 try-on 결과 생성 실패

- 향후 작성
