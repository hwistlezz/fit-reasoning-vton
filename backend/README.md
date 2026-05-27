# Backend

## 목적

Fit-aware Virtual Try-On Web Prototype의 FastAPI backend skeleton이다.

현재 범위는 API 서버 뼈대, health check, CORS 설정, runtime directory 준비까지이다. StableVITON inference와 upload/job API는 아직 구현하지 않는다.

## 실행 환경

- Python 3.10
- Conda env: `D:\conda-envs\vton`
- FastAPI
- Uvicorn

## 설치

```powershell
cd D:\GitHub\fit-reasoning-vton
conda activate D:\conda-envs\vton
python -m pip install -r backend/requirements.txt
```

## 실행

```powershell
cd D:\GitHub\fit-reasoning-vton
conda activate D:\conda-envs\vton
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Health Check

```powershell
curl http://localhost:8000/api/health
```

예상 응답:

```json
{
  "status": "ok",
  "service": "fit-aware-vton-backend",
  "version": "0.1.0"
}
```

## 현재 범위

- FastAPI app entrypoint
- `/api/health`
- CORS 설정
- config 관리
- path 관리
- `backend/outputs` directory 생성
- `backend/logs` directory 생성

## 제외 범위

- StableVITON inference 구현
- checkpoint 추가
- dataset 추가
- generated image 추가
- `/api/tryon`
- `/api/job/{job_id}`
- `/api/result/{job_id}`
- frontend 구현
