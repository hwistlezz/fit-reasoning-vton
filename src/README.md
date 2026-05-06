# src

향후 fit-aware 분석 코드를 둘 위치이다.

현재 단계에서는 feature extraction, training, inference pipeline을 구현하지 않는다.

예상 모듈:

- feature extraction
- pseudo label generation
- gold set evaluation
- reliability analysis
- overlay visualization
- natural language explanation

구현 시 CatVTON 원본 코드를 이 디렉터리에 복사하지 않는다. CatVTON은 외부 경로로 참조하고, 이 저장소는 분석 레이어의 책임만 가진다.
