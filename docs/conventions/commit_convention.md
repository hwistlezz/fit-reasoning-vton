# 🧾 Commit Convention

## 🧩 커밋 메시지 형식

커밋 메시지는 다음 형식을 사용한다.

```text
type(#issue-number/scope or domain): message
```

## 📝 예시

```text
feat(#7/analysis): fit confidence score skeleton 구현
docs(#9/readme): 텀프로젝트 proposal 설명 보완
chore(#10/github): issue 및 PR 템플릿 추가
experiment(#11/idm-vton): smoke test 로그 템플릿 추가
fix(#12/scripts): IDM-VTON 외부 경로 검증 오류 수정
```

## 📚 type 목록

| type | 의미 |
| --- | --- |
| `feat` | 새로운 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `chore` | 설정, 템플릿, 빌드, 폴더 구조 등 |
| `refactor` | 기능 변화 없는 코드 구조 개선 |
| `experiment` | 실험 코드, 실험 로그, baseline 비교 |
| `test` | 테스트 코드 또는 검증 코드 |
| `style` | 포맷팅, 오타, 개행 등 |

## 🗂️ scope 예시

- `readme`
- `docs`
- `github`
- `scripts`
- `config`
- `idm-vton`
- `catvton`
- `analysis`
- `preprocessing`
- `app`

## ✅ 규칙

- 간결한 작업 완료형을 사용한다.
- 예: `템플릿 추가`, `문서 보완`, `검증 스크립트 추가`

## 👍 좋은 예시

```text
docs(#3/readme): 프로젝트 범위 설명 보완
chore(#4/github): PR 템플릿 추가
feat(#5/analysis): fit reasoning skeleton 추가
```

## 👎 나쁜 예시

```text
update
fix
feat: 여러 작업
docs: 결과 추가
```
