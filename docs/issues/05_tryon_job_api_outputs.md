# [Feat] Try-On job API 및 outputs 구조 구현

## 목적

프론트엔드와 연결할 Try-On job API와 outputs 구조를 구현한다.

## API 계획

### POST /api/tryon

form-data:

```text
person_image: File
cloth_image: File
height: float
weight: float
usual_size: string
```

response:

```json
{
  "job_id": "job_001",
  "status": "pending"
}
```

### GET /api/job/{job_id}

```json
{
  "job_id": "job_001",
  "status": "pending | running | done | failed",
  "progress": 45,
  "message": "Running StableVITON inference"
}
```

### GET /api/result/{job_id}

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

위 JSON은 API contract example이며 실제 결과가 아니다. StableVITON 연결 전에는 mock result 또는 placeholder 상태로 둔다.

## 체크리스트

- [ ] `job_id` 생성 규칙 구현
- [ ] upload image 저장 구조 구현
- [ ] `backend/outputs/{job_id}` 구조 구현
- [ ] job status 저장 방식 구현
- [ ] `/api/tryon` 구현
- [ ] `/api/job/{job_id}` 구현
- [ ] `/api/result/{job_id}` 구현
- [ ] mock pipeline으로 응답 확인
- [ ] generated outputs git 제외 확인

## 완료 기준

- [ ] 프론트엔드가 API contract 기준으로 연동을 시작할 수 있다.
- [ ] 실제 StableVITON inference 연결 전에도 mock job 흐름이 동작한다.

## 주의사항

- API example을 실제 inference 결과처럼 표현하지 않는다.
- generated image는 git에 커밋하지 않는다.
