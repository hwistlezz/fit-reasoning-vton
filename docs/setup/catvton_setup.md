# CatVTON 설정 계획

## 원칙

CatVTON은 pretrained baseline으로 사용한다. CatVTON 원본 코드는 이 저장소에 직접 복사하지 않는다.

권장 방식은 다음 중 하나이다.

- 이 저장소와 같은 상위 작업 공간에 CatVTON을 별도 clone
- 외부 경로에 있는 CatVTON을 설정 파일 또는 실행 인자로 참조
- 필요한 경우 git submodule 사용 여부를 별도 검토

현재 스캐폴드 단계에서는 CatVTON 코드를 포함하지 않는다.

## 역할 분리

이 저장소의 책임:

- 프로젝트 문서화
- 데이터 구조 정의
- 실험 계획 관리
- 생성 결과 분석 코드
- fit-aware feature 및 label 분석
- 설명 및 UI로 확장될 코드

CatVTON 외부 저장소의 책임:

- virtual try-on 모델 정의
- pretrained inference 실행
- 모델 checkpoint 로딩
- 원본 모델에 필요한 전처리 및 후처리

## 실행 흐름 초안

1. CatVTON 실행 환경을 별도 구성한다.
2. VITON-HD 입력 데이터를 CatVTON 형식에 맞게 준비한다.
3. pretrained checkpoint로 baseline inference를 수행한다.
4. 생성 결과를 본 저장소의 로컬 `outputs/` 하위 구조에 맞춰 저장한다.
5. 본 저장소의 분석 코드가 생성 결과와 paired target 정보를 읽어 평가한다.

## 체크포인트 관리

CatVTON checkpoint와 model weight는 GitHub에 커밋하지 않는다. 로컬 디스크, 연구실 서버, 클라우드 스토리지 등 별도 저장소에서 관리한다.

## 향후 작성 항목

- 사용한 CatVTON commit hash
- 사용한 checkpoint 이름 및 출처
- PyTorch/CUDA 버전
- inference command
- 입력 데이터 매핑 규칙
- 생성 결과 저장 규칙
