# src

향후 Fit-aware Reasoning Layer 코드를 둘 위치이다.

현재 단계에서는 feature extraction, training, inference pipeline을 구현하지 않는다.

예상 모듈:

- input quality evaluation
- fit confidence scoring
- fit reasoning sentence generation
- failure reason analysis
- overlay visualization
- web integration helpers

구현 시 IDM-VTON 또는 CatVTON 원본 코드를 이 디렉터리에 복사하지 않는다. 외부 VTON 모델은 외부 경로로 참조하고, 이 저장소는 웹 시스템과 분석 레이어의 책임만 가진다.
