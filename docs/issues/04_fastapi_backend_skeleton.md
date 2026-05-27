# [Feat] FastAPI backend skeleton 구현

## 목적

PC1에서 StableVITON inference server로 사용할 FastAPI backend skeleton을 만든다.

## 예상 구조

```text
backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── schemas/
│   └── core/
├── outputs/
└── README.md
```

## 체크리스트

- [ ] `backend/` 폴더 생성
- [ ] FastAPI app entrypoint 생성
- [ ] `/api/health` 구현
- [ ] CORS 설정
- [ ] output directory 설정
- [ ] `.gitignore`에 generated outputs 제외 확인
- [ ] backend 실행 방법 문서화
- [ ] uvicorn 실행 확인

## 완료 기준

- [ ] `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000` 명령으로 서버가 실행된다.
- [ ] `GET /api/health`가 정상 응답한다.
- [ ] 아직 StableVITON 실제 inference와 연결하지 않아도 된다.

## 주의사항

- backend skeleton 단계에서는 mock 또는 health check까지만 구현해도 된다.
- generated output 파일이 git에 포함되지 않도록 한다.
