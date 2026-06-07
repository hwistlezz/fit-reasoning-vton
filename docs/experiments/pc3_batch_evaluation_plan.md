# PC3 Batch Evaluation 및 Confidence 실험 계획

## 목적

PC3는 더 이상 LoRA 학습 전용 PC가 아니다. PC3의 핵심 역할은 PC1 StableVITON API가 최소 동작한 뒤 StableVITON 생성 결과를 대량으로 평가하고, failure case와 confidence 관련 실험을 수집하는 것이다.

한 달 MVP에서 PC3는 다음 작업에 집중한다.

- StableVITON batch test
- 대량 inference 결과 평가
- failure case 수집
- low confidence case 수집
- fit analyzer threshold 실험
- confidence scoring 실험
- hotspot annotation 후보 정리
- 시간이 남을 경우에만 대체 VTON 모델 비교 실험

LoRA는 한 달 MVP에서 제외하며, 7개월 고도화 단계에서 fit control 필요성이 명확해졌을 때 선택적으로 검토한다.

IDM-VTON은 시간이 남을 경우에만 진행하는 후순위 대체 VTON 비교 실험이다. IDM-VTON 설치나 실행이 오래 막히면 즉시 중단하고 StableVITON batch evaluation과 fit analyzer 실험을 우선한다.

## 실험 산출물 위치

PC3 실험 결과는 아래 구조를 기준으로 관리한다.

```text
outputs/
  experiments/
    stableviton_batch/
    failure_cases/
    low_confidence_cases/
    fit_threshold_tests/
    confidence_tests/
    idm_test/
```

실제 output, generated image, dataset, checkpoint는 git에 커밋하지 않는다. 공개 저장소에는 실험 계획, schema, example CSV, 로그 템플릿만 포함한다.

## 입력 데이터 방향

PC2에서 AIHub "쉐이프리스 의류 및 포즈 데이터"를 활용해 keypoint, segmentation, fit feature, confidence scoring 기준 설계에 필요한 데이터를 준비한다.

- AIHub 원본 이미지, annotation, JSON 파일은 공개 GitHub에 업로드하지 않는다.
- 원본 데이터를 외부에 공유하지 않는다.
- 공개 저장소에는 schema, example CSV, 문서만 포함한다.
- 데이터 출처를 README 또는 발표자료에 명시한다.
- `datasets/features.csv`와 `datasets/test_cases.csv`는 실제 원본 데이터가 아닌 schema 또는 작은 예시만 공개한다.

## StableVITON Batch Test

PC1 FastAPI가 최소 동작하면 PC3에서 여러 test case를 API로 요청해 결과를 수집한다.

```bash
tmux new -s batch_eval
cd backend
conda activate vton
python scripts/run_test_jobs.py \
  --input datasets/test_cases.csv \
  --output outputs/experiments/stableviton_batch \
  --api http://PC1_IP:8000 \
  2>&1 | tee logs/batch_eval_$(date +%Y%m%d_%H%M).log
```

기록 항목은 다음을 기준으로 한다.

- job_id
- input pair id
- result image path
- job status
- failure reason
- confidence score
- fit label
- warning 여부
- annotation 후보

이 문서에는 실제 inference 성공, 성능 수치, 결과 이미지를 기록하지 않는다.

## Fit Threshold 실험

PC2에서 만든 feature table을 바탕으로 shoulder, torso, sleeve, garment length 관련 threshold를 조정한다.

```bash
tmux new -s fit_threshold
cd backend
conda activate vton
python scripts/evaluate_fit_thresholds.py \
  --features datasets/features.csv \
  --output outputs/experiments/fit_threshold_tests \
  2>&1 | tee logs/fit_threshold_$(date +%Y%m%d_%H%M).log
```

실험 목표는 정확한 신체 치수 예측이 아니라 fit label 분류와 자연어 explanation에 사용할 안정적인 rule 후보를 찾는 것이다.

## Confidence 실험

StableVITON batch 결과와 feature table을 함께 사용해 confidence score 산출 규칙을 실험한다.

```bash
tmux new -s confidence_test
cd backend
conda activate vton
python scripts/evaluate_confidence.py \
  --input outputs/experiments/stableviton_batch \
  --features datasets/features.csv \
  --output outputs/experiments/confidence_tests \
  2>&1 | tee logs/confidence_test_$(date +%Y%m%d_%H%M).log
```

confidence score는 pose quality, parsing stability, silhouette consistency, garment preservation, input image quality, output distortion 여부를 함께 고려한다.

## Failure Case 및 Low Confidence Case 수집

PC3는 batch 결과에서 다음 case를 별도 폴더로 분류한다.

- pose/keypoint가 불안정한 case
- segmentation이 상의 영역을 잘못 잡은 case
- 팔, 소매, 몸통 폭이 왜곡된 case
- 의류 texture나 형태가 크게 훼손된 case
- confidence score가 낮은 case
- fit label과 시각적 결과가 어긋나는 case

분류 결과는 `outputs/experiments/failure_cases/`와 `outputs/experiments/low_confidence_cases/` 아래에 저장하되, 실제 이미지는 git에 커밋하지 않는다.

## IDM-VTON 후순위 비교

IDM-VTON은 시간이 남을 때만 실행한다.

```bash
tmux new -s idm_test
cd ~/projects/idm-vton
conda activate idm
python inference.py \
  --person examples/person.png \
  --cloth examples/cloth.png \
  --output outputs/idm_test \
  2>&1 | tee logs/idm_test_$(date +%Y%m%d_%H%M).log
```

비교 항목은 설치 난이도, VRAM 사용량, inference time, 결과 품질, API 통합 난이도 정도로 제한한다. IDM-VTON 때문에 MVP 일정이 밀리면 비교 실험을 중단한다.

## GPU 로그

장시간 batch test를 수행할 때는 GPU 사용량을 별도 로그로 남긴다.

```bash
tmux new -s gpu_log
nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu,temperature.gpu \
  --format=csv -l 10 > logs/gpu_pc3_$(date +%Y%m%d_%H%M).csv
```

GPU 로그는 개발 환경 관찰 기록이며 공식 benchmark처럼 표현하지 않는다.

## PC1로 결과 동기화

필요한 경우 PC3의 실험 결과 폴더를 PC1로 동기화한다.

```bash
rsync -avh outputs/experiments/ user@PC1_IP:/home/user/projects/vton-fit-aware/backend/outputs/experiments/
```

동기화 대상에는 공개 저장소에 올릴 수 없는 generated image나 원본 데이터가 포함될 수 있으므로 GitHub 커밋 전에 반드시 제외 여부를 확인한다.
