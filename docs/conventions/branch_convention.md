# 🌿 Branch Convention

## 🏷️ 브랜치 네이밍 규칙

브랜치 이름은 다음 형식을 사용한다.

```text
type/#issue-number/short-description
```

## 📝 예시

```text
feat/#7/fit-confidence-score
fix/#8/idm-vton-path-check
docs/#9/update-readme-proposal
chore/#10/add-pr-template
experiment/#11/idm-vton-smoke-test
```

## 📚 type 목록

| type | 의미 |
| --- | --- |
| `feat` | 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `chore` | 설정, 템플릿, 구조 정리 |
| `refactor` | 기능 변화 없는 코드 구조 개선 |
| `experiment` | 실험, smoke test, baseline 비교 |
| `test` | 테스트 코드 또는 검증 스크립트 |

## ⚠️ 주의 사항

- 브랜치명은 영어 소문자와 하이픈을 사용한다.
- 공백을 사용하지 않는다.
- 너무 긴 설명은 피한다.
- issue 번호를 반드시 포함한다.
- 외부 모델 이름은 필요한 경우만 포함한다.
- 브랜치 하나에는 하나의 작업 목적만 담는다.
