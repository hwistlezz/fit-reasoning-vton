# 프로젝트 개요

## 프로젝트명

**Fit-aware Virtual Try-On Web Prototype**

기존 프로젝트명 **Fit-Confidence Virtual Try-On**의 문제의식을 유지하되, MVP 방향은 StableVITON 기반 제품형 웹 프로토타입으로 수정한다.

## 한 줄 설명

StableVITON으로 생성한 VTON 결과를 CV 기반 fit analyzer로 분석하고, confidence score와 자연어 fit explanation을 웹에서 제공하는 제품형 프로토타입.

## 프로젝트 목표

이 프로젝트는 사람 전신 이미지와 의류 이미지를 입력받아 StableVITON 기반 가상 착장 결과를 생성하고, 그 결과가 얼마나 신뢰 가능한지 컴퓨터비전 특징 기반으로 평가하는 웹 시스템을 목표로 한다.

논문 수준의 신규 모델 개발이 아니라, RTX 4080 16GB GPU 환경에서 1개월 안에 실제 동작하는 AI 웹 프로토타입을 만드는 것이 목표이다.

## 문제 정의

기존 가상 착장 모델은 이미지를 생성하지만, 생성 결과가 신뢰 가능한지 또는 어떤 부분이 어색한지 설명하지 못하는 경우가 많다. 사용자는 결과 이미지가 성공적인지, 입력 이미지 품질이 낮아서 실패했는지, pose 또는 parsing이 불안정한지 판단하기 어렵다.

본 프로젝트는 생성 이미지와 함께 입력 품질 점수, 착장 결과 confidence score, 간단한 fit explanation, 실패 원인을 제공하는 방향을 다룬다.

## MVP 핵심 기능

- 사용자 전신 이미지 업로드
- 의류 이미지 업로드
- 키 / 몸무게 / 평소 사이즈 입력
- StableVITON 기반 Virtual Try-On 생성
- DWPose / SCHP 기반 CV preprocessing
- CV 기반 fit 분석
- confidence score 제공
- 자연어 fit explanation 제공
- 웹 기반 인터랙티브 결과 UI 제공

## 핵심 파이프라인

```text
User Input
-> Input Quality Check
-> Pose Estimation, DWPose
-> Human Parsing, SCHP
-> StableVITON Inference
-> Fit Analyzer
-> Confidence Scoring
-> Fit Reasoning
-> Web UI Visualization
```

## Fit-Aware Reasoning Layer

초기 후보 분석 요소는 다음과 같다.

- `pose_quality`: 사람 이미지의 자세 안정성
- `parsing_quality`: SCHP 기반 사람/의류 영역 분리 안정성
- `silhouette_consistency`: 착장 전후 실루엣 변화의 자연스러움
- `garment_preservation`: 의류 색상, 패턴, 형태 보존 정도
- `input_quality`: 전신 포함 여부, 가림, 잘림, 해상도 문제
- `distortion_risk`: 착장 결과 왜곡 가능성
- `length_tendency`: 기장감 경향
- `roominess_tendency`: 품 여유 경향
- `sleeve_length_tendency`: 소매 길이 경향
- `shoulder_line_tendency`: 어깨선 경향

현재 문서 단계에서는 feature extraction 알고리즘을 구현하지 않는다. 실제 계산 방식은 StableVITON smoke test, DWPose, SCHP 결과를 확인한 뒤 결정한다.

## 모델 사용 방향

### StableVITON

StableVITON은 MVP main VTON backbone이다.

PC1에서 StableVITON inference server와 FastAPI API server를 실행하고, `/api/tryon` 요청을 받아 result image를 생성하는 방향으로 설계한다.

현재 단계에서는 계획 수정만 진행하며, StableVITON inference가 성공한 것처럼 기록하지 않는다.

### IDM-VTON

IDM-VTON은 MVP에 통합하지 않는다.

PR #8에서 생성한 IDM-VTON local Gradio demo smoke test 기록은 삭제하지 않고 유지한다. IDM-VTON은 PC3에서 comparison baseline으로 활용한다.

PC3에서는 StableVITON 대비 설치 난이도, VRAM 사용량, inference time, 결과 품질, API 통합 난이도를 비교한다. IDM-VTON 작업이 오래 막히면 MVP 보호를 위해 중단하고 PC3를 LoRA 실험용으로 전환한다.

### CatVTON

CatVTON은 MVP 범위에서는 제외하며, 후속 optional baseline으로만 검토한다.

### LoRA

LoRA는 MVP 필수 기능이 아니라 PC3에서 진행하는 후순위 feasibility 실험이다. 가능하다면 oversized LoRA 1개만 feasibility 수준으로 검토한다.

## 시스템 구성

- 노트북 1: Frontend 개발, Next.js UI, localhost 개발, PC1 API 연결 테스트
- 노트북 2: Backend 개발, Git / Issue / PR 관리, PC1 / PC2 / PC3 SSH 접속 및 실행 관리
- PC1: StableVITON main inference server, FastAPI API server, 실제 VTON 결과 생성
- PC2: DWPose, SCHP, input quality check, fit feature extraction
- PC3: IDM-VTON comparison, oversized LoRA feasibility

자세한 역할은 [PC / 노트북 역할](pc_roles.md)을 따른다.

## 명확한 비목표

- 실제 신체 치수 예측
- 정확한 의류 사이즈 추천
- VTON 모델을 처음부터 학습
- StableVITON 외부 저장소를 본 저장소에 복사
- checkpoint, dataset, generated image 커밋
- CatVTON을 MVP active baseline으로 통합
- LoRA를 MVP 필수 기능으로 포함
- 검증되지 않은 성능 수치 제시
- fake result 작성

## 산출물

- StableVITON 중심 MVP 계획 문서
- PC / 노트북 역할 문서
- FastAPI API contract 문서
- backend 구조 계획
- StableVITON external setup 및 smoke test 로그
- 입력 품질 평가 및 fit confidence score 설계
- fit reasoning 문장 생성 계획
- 성공/실패 사례 정리 계획

결과 이미지, checkpoint, dataset, generated image는 본 저장소에 포함하지 않는다.
