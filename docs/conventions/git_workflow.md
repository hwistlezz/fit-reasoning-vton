# 🌿 Git Workflow

## 🎯 목적

이 문서는 `Fit-Confidence Virtual Try-On` 프로젝트에서 둘이서 협업하기 위한 Git 작업 흐름을 정리한다.

## 🧭 브랜치 구조

```text
main
└── dev
    ├── feat/#issue-number/short-description
    ├── fix/#issue-number/short-description
    ├── docs/#issue-number/short-description
    ├── chore/#issue-number/short-description
    └── experiment/#issue-number/short-description
```

## 🧱 브랜치 역할

### 🔒 main

- 제출 가능한 안정 버전이다.
- 직접 커밋하지 않는다.
- `dev`에서 검증된 내용만 병합한다.
- 발표, 제출, 배포 기준으로 사용할 수 있는 상태를 유지한다.

### 🔧 dev

- 통합 개발 브랜치이다.
- 기능 브랜치의 PR target이다.
- 둘이서 작업한 내용을 합치는 기준 브랜치이다.
- 작업 시작 전 최신 상태로 유지한다.

### 🌱 작업 브랜치

- issue 단위로 생성한다.
- 작업 완료 후 `dev`로 PR을 생성한다.
- PR merge 후 삭제한다.
- 브랜치 이름은 [Branch Convention](branch_convention.md)을 따른다.

## 🔁 기본 작업 흐름

1. Issue를 생성한다.
2. `dev`를 최신화한다.
3. issue 번호 기반 작업 브랜치를 생성한다.
4. 작업하고 커밋한다.
5. 원격 브랜치에 push한다.
6. `dev`를 base로 PR을 생성한다.
7. 리뷰 후 Squash merge 또는 merge한다.
8. 작업 브랜치를 삭제한다.

## 🚀 초기 브랜치 생성 예시

```bash
git checkout main
git pull origin main
git checkout -b dev
git push -u origin dev
```

## ✨ 기능 브랜치 생성 예시

```bash
git checkout dev
git pull origin dev
git checkout -b feat/#7/product-like-toggle
```

## ✅ PR 생성 전 확인

- 외부 모델 코드가 포함되지 않았는지 확인한다.
- checkpoint, dataset, generated image, 대용량 로그가 포함되지 않았는지 확인한다.
- fake result 또는 실행하지 않은 성능 수치가 문서에 들어가지 않았는지 확인한다.
- README 또는 docs 링크가 깨지지 않았는지 확인한다.
