# IDM-VTON 외부 저장소 설정

## 목적

IDM-VTON은 이번 텀프로젝트의 main virtual try-on baseline이다. 본 저장소는 IDM-VTON 자체를 포함하지 않고, 외부 경로에 clone한 IDM-VTON을 실행 대상으로 참조한다.

## 외부 경로 원칙

권장 예시 경로는 다음과 같다.

```text
workspace/
  fit-reasoning-vton/
  IDM-VTON/
```

본 저장소 기준 예시 경로:

```text
../IDM-VTON
```

## 커밋하지 않을 항목

다음 항목은 본 저장소에 복사하거나 커밋하지 않는다.

- IDM-VTON source code
- checkpoint 및 model weight
- dataset
- generated image
- inference log 원본 파일
- 대용량 중간 산출물

## Commit Hash 기록

외부 IDM-VTON 저장소에서 다음 명령으로 commit hash를 기록한다.

```bash
cd ../IDM-VTON
git rev-parse HEAD
```

이 값은 smoke test log와 이후 실험 로그에 함께 기록한다.

## 출력 경로 원칙

모델 실행 결과는 본 저장소의 `outputs/` 아래에 저장할 수 있다.

예시:

```text
outputs/
  idm_vton/
    run_YYYYMMDD_HHMM/
```

단, generated image는 기본적으로 GitHub에 올리지 않는다. `outputs/` 내부 실제 결과물은 `.gitignore` 대상이다.

## 경로 설정 예시

본 저장소의 [configs/paths.example.yaml](../../configs/paths.example.yaml)을 복사해 로컬 환경에 맞게 수정할 수 있다. 실제 로컬 경로가 포함된 설정 파일은 필요 시 별도 ignore 대상으로 관리한다.

## 라이선스 및 사용 조건

IDM-VTON의 코드, checkpoint, demo 자료는 원 저장소의 라이선스와 사용 조건을 확인해야 한다. 상업적 사용, 수정 코드 공개, checkpoint 재배포 가능 여부는 원 저장소 기준으로 별도 확인이 필요하다.

## Smoke Test 목표

Phase 1에서 확인할 항목은 다음과 같다.

- 외부 IDM-VTON 경로가 존재하는지
- README와 실행 관련 파일이 있는지
- 환경 설정 파일 후보가 있는지
- 샘플 person image와 garment image로 inference command를 구성할 수 있는지
- 첫 generated image가 생성되는지

실제 모델 실행, checkpoint 다운로드, dataset 다운로드는 이 문서나 검증 스크립트에서 수행하지 않는다.

## 향후 작성 항목

- 실제 외부 저장소 URL
- 실행 환경 구성 명령
- smoke test command
- 첫 실행 결과 로그
- 실패 사례와 해결 방법

