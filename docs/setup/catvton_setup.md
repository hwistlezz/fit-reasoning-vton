# CatVTON 설정 계획

## 역할

CatVTON은 이번 프로젝트에서 optional comparison baseline이다. 메인 실행 대상은 StableVITON이며, CatVTON은 시간이 허용될 때 비교 실험 또는 smoke test에 사용한다.

CatVTON 원본 코드는 이 저장소에 직접 복사하지 않는다.

## 외부 참조 원칙

권장 방식은 다음 중 하나이다.

- 이 저장소와 같은 상위 작업 공간에 CatVTON을 별도 clone
- 외부 경로에 있는 CatVTON을 설정 파일 또는 실행 인자로 참조
- 필요한 경우 별도 문서에서 commit hash를 기록

현재 단계에서는 CatVTON 코드를 포함하지 않는다.

## 역할 분리

이 저장소의 책임:

- proposal 문서화
- 웹 데모 코드
- 입력 품질 평가
- 착장 결과 신뢰도 평가
- Fit-aware Reasoning Layer
- optional comparison 결과 기록

CatVTON 외부 저장소의 책임:

- virtual try-on 모델 정의
- pretrained inference 실행
- checkpoint 로딩
- 원본 모델에 필요한 전처리 및 후처리

## 실행 흐름 초안

1. CatVTON 실행 환경을 별도 구성한다.
2. 외부 CatVTON 경로와 commit hash를 기록한다.
3. smoke test가 필요한 경우 공식 실행 절차를 따른다.
4. 생성 결과는 본 저장소에 커밋하지 않는다.
5. 비교 결과는 실제 실행 후에만 기록한다.

## 체크포인트 관리

CatVTON checkpoint와 model weight는 GitHub에 커밋하지 않는다. 로컬 디스크, 연구실 서버, 클라우드 스토리지 등 별도 저장소에서 관리한다.

## 향후 작성 항목

- 사용한 CatVTON commit hash
- 사용한 checkpoint 이름 및 출처
- smoke test command
- 비교 실험 여부
