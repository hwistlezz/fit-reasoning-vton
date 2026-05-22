# API Contract

이 문서는 FastAPI backend와 Next.js frontend가 맞출 초기 API contract를 정리한다.

아래 JSON은 API contract example이며 실제 inference 결과가 아니다.

## GET /api/health

Response:

```json
{
  "status": "ok"
}
```

## POST /api/tryon

Request form-data:

```text
person_image: File
cloth_image: File
height: float
weight: float
usual_size: string
```

Response:

```json
{
  "job_id": "job_001",
  "status": "pending"
}
```

## GET /api/job/{job_id}

Response:

```json
{
  "job_id": "job_001",
  "status": "pending | running | done | failed",
  "progress": 45,
  "message": "Running StableVITON inference"
}
```

## GET /api/result/{job_id}

Response example:

```json
{
  "job_id": "job_001",
  "status": "done",
  "person_image_url": "/outputs/job_001/person.png",
  "cloth_image_url": "/outputs/job_001/cloth.png",
  "result_image_url": "/outputs/job_001/result.png",
  "confidence": {
    "score": 82,
    "level": "high",
    "warnings": []
  },
  "fit": {
    "label": "oversized",
    "scores": {
      "shoulder_ratio": 1.18,
      "torso_width_ratio": 1.22,
      "sleeve_length_ratio": 1.07,
      "garment_length_ratio": 1.15
    },
    "explanations": [
      "전체적으로 오버핏 실루엣입니다.",
      "어깨선이 신체 어깨보다 바깥쪽에 위치해 루즈한 느낌이 납니다.",
      "상의 기장이 힙 라인에 가깝게 내려옵니다."
    ]
  }
}
```

## 주의사항

- 위 response는 프론트엔드 연동을 위한 contract example이다.
- StableVITON inference가 성공했다는 의미가 아니다.
- confidence score와 fit score 값은 예시이며 실제 성능 수치가 아니다.
- generated image는 repository에 커밋하지 않는다.
- output image는 `backend/outputs/{job_id}` 같은 ignored output 경로에 저장한다.
