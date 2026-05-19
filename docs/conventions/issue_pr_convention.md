# 🔗 Issue / PR Convention

## 🧩 Issue 규칙

- 모든 작업은 가능한 issue를 먼저 생성한다.
- issue 제목은 `[Type] 작업 내용` 형식을 사용한다.
- 기능, 버그, 실험, 문서 작업은 가능한 전용 issue template을 사용한다.
- issue 본문에는 작업 목적, 범위, 체크리스트를 작성한다.

## 📝 Issue 제목 예시

```text
[Feat] Fit confidence score skeleton 구현
[Docs] README 협업 규칙 추가
[Experiment] IDM-VTON smoke test 실행
[Bug] 외부 경로 검증 스크립트 오류 수정
```

## 📌 PR 규칙

- PR base branch는 기본적으로 `dev`이다.
- PR 제목은 커밋 메시지와 유사하게 작성한다.
- PR 본문에는 관련 issue를 `close #이슈번호` 형태로 연결한다.
- PR에는 변경 내용, 검증 방법, 리뷰어 확인 사항을 작성한다.
- 모델 코드, checkpoint, dataset, generated image가 포함되지 않았는지 반드시 확인한다.
- 아직 실행하지 않은 결과 이미지나 성능 수치를 실제 결과처럼 작성하지 않는다.

## 📝 PR 제목 예시

```text
feat(#7/analysis): fit confidence score skeleton 구현
docs(#9/readme): 협업 규칙 문서 추가
```

## 🔀 Merge 규칙

- 둘이서 작업하므로 최소 1명 이상 확인 후 merge하는 것을 권장한다.
- 문서만 바꾸는 작은 PR은 self-check 후 merge할 수 있다.
- 기능, 실험, 스크립트 PR은 가능하면 상대방 확인 후 merge한다.
- merge 방식은 Squash merge를 권장한다.
- squash commit 메시지는 [Commit Convention](commit_convention.md)을 따른다.

## ✅ PR 생성 전 self-check

- `dev`를 base branch로 설정했는지 확인한다.
- 관련 issue가 연결되어 있는지 확인한다.
- 변경 파일 목록에 외부 모델 코드가 없는지 확인한다.
- checkpoint, dataset, generated image, 대용량 로그가 없는지 확인한다.
- README 또는 docs 링크가 깨지지 않았는지 확인한다.
