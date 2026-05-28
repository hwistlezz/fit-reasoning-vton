# StableVITON preprocessing artifact pipeline design

## 1. Purpose

Issue #50 defines the preprocessing artifact pipeline required for upload-based StableVITON inference.

After the #14 service wrapper, the backend can call StableVITON CLI inference from FastAPI and return a generated `result.png` when a prepared smoke dataset already exists. That is not the same as real upload-based inference. StableVITON does not run from only a raw person image and raw cloth image. It expects a job data root that already contains DensePose, agnostic person representations, agnostic masks, cloth masks, and a pair list.

The purpose of this document is to define the artifact generation flow before implementing it. The implementation should use this document as the boundary between the input adapter, preprocessing, StableVITON inference, and failure handling.

## 2. StableVITON required input structure

StableVITON inference expects a data root shaped like this:

```text
DATA/{job_data_root}/
  test_pairs.txt
  test/
    image/
    image-densepose/
    agnostic-v3.2/
    agnostic-mask/
    cloth/
    cloth-mask/
```

| Path | Role |
| --- | --- |
| `test/image/` | Original person image used as the target body input. |
| `test/cloth/` | Original clothing image used as the garment input. |
| `test/cloth-mask/` | Binary or near-binary mask for the garment region. StableVITON uses it to isolate the clothing shape. |
| `test/image-densepose/` | DensePose result for the person image. This provides body surface correspondence information. |
| `test/agnostic-v3.2/` | Person representation with the original clothing region removed or neutralized. StableVITON uses it as the clothing-agnostic body context. |
| `test/agnostic-mask/` | Mask for the agnostic region. It identifies where the original clothing/body area should be treated as replaceable context. |
| `test_pairs.txt` | Pair list that maps a person image filename to a cloth image filename. For one uploaded job, it should contain one line. |

Example single-job pair list:

```text
person.png cloth.png
```

## 3. Current #14 state

The #14 wrapper state, represented by PR #47, is:

- FastAPI can call a StableVITON wrapper.
- Prepared smoke data can produce `result.png`.
- `/api/result/{job_id}` can return `result_image_url`.
- `stdout` and `stderr` logs can be saved under the job output directory.

The remaining gap is upload adaptation. The uploaded person and cloth images are stored by the backend, but they are not yet transformed into a StableVITON-ready input root. There is no automatic generation path yet for:

- `image-densepose`
- `agnostic-v3.2`
- `agnostic-mask`
- `cloth-mask`
- job-scoped `test_pairs.txt`

## 4. Relationship with #48 input adapter

Issue #48 should create the minimum job-scoped StableVITON input adapter. Its scope should be limited to deterministic file placement and validation:

- Create a job-specific StableVITON input root.
- Copy the uploaded person image into `test/image/`.
- Copy the uploaded cloth image into `test/cloth/`.
- Generate `test_pairs.txt`.
- Detect missing required artifacts and return clear errors.

Issue #50 defines the preprocessing artifact pipeline around that adapter:

- Define where DensePose, agnostic images, agnostic masks, and cloth masks are produced.
- Define which stage owns each artifact.
- Define how failures should be reported.
- Provide a staged implementation plan for later preprocessing work.

The intended split is:

```text
#48 input adapter
  raw upload files -> job-scoped StableVITON input root skeleton

#50 preprocessing pipeline design
  required artifact generation stages and failure handling

future preprocessing implementation
  actual DensePose / agnostic / mask generation code
```

## 5. Preprocessing stage design

| Step | Input | Output | Failure case |
| --- | --- | --- | --- |
| 1. Upload 저장 | `person_image`, `cloth_image` from `/api/tryon` | Raw uploaded files under `backend/outputs/{job_id}/` | Missing or empty upload should fail before preprocessing. |
| 2. Job-scoped StableVITON input root 생성 | `job_id`, stored upload paths | `DATA/{job_data_root}/test/...` directory skeleton, preferably outside tracked Git paths or inside ignored runtime paths | Directory creation failure or unsafe path resolution should fail the job. |
| 3. `test_pairs.txt` 생성 | Normalized person filename, normalized cloth filename | One-line `test_pairs.txt` such as `person.png cloth.png` | Invalid filename mapping or missing copied files should fail adapter validation. |
| 4. `cloth-mask` 준비 | Uploaded cloth image | `test/cloth-mask/{cloth_filename}` | Cloth segmentation or mask extraction failure should produce `PREPROCESS_CLOTH_MASK_FAILED`. |
| 5. DensePose 생성 | Uploaded person image | `test/image-densepose/{person_filename}` | DensePose model/runtime failure should produce `PREPROCESS_DENSEPOSE_FAILED`. |
| 6. `agnostic-v3.2` 생성 | Person image, parse/pose signals, clothing region estimate | `test/agnostic-v3.2/{person_filename}` | Incomplete parse or agnostic generation failure should produce `PREPROCESS_AGNOSTIC_IMAGE_FAILED`. |
| 7. `agnostic-mask` 생성 | Person image, parse/pose signals, clothing region estimate | `test/agnostic-mask/{person_filename}` | Missing or invalid mask should produce `PREPROCESS_AGNOSTIC_MASK_FAILED`. |
| 8. Preflight check | Job data root | Verified StableVITON input structure | Any missing required artifact should produce `PREPROCESS_REQUIRED_ARTIFACT_MISSING`. |
| 9. StableVITON inference 실행 | Verified job data root, StableVITON config/checkpoint | Raw StableVITON generated image under ignored runtime output | StableVITON wrapper should keep using existing `STABLEVITON_*` error codes. |
| 10. `result.png` 복사 및 `result.json` 업데이트 | StableVITON raw result image | `backend/outputs/{job_id}/result.png`, updated `result.json` | Missing generated result should remain `STABLEVITON_RESULT_NOT_FOUND`. |

Implementation note: the first upload-based MVP can intentionally stop after Step 3 and fail with explicit missing-artifact errors. That is better than silently falling back to prepared smoke data because it makes the boundary between upload storage and preprocessing visible.

## 6. Failure case design

| Error code | When it should occur |
| --- | --- |
| `PREPROCESS_PERSON_IMAGE_MISSING` | The job has no stored person image, the file is empty, or the adapter cannot copy it into `test/image/`. |
| `PREPROCESS_CLOTH_IMAGE_MISSING` | The job has no stored cloth image, the file is empty, or the adapter cannot copy it into `test/cloth/`. |
| `PREPROCESS_CLOTH_MASK_FAILED` | Cloth mask generation fails, produces no file, or produces an invalid empty mask. |
| `PREPROCESS_DENSEPOSE_FAILED` | DensePose execution fails, times out, or produces no usable `image-densepose` artifact. |
| `PREPROCESS_AGNOSTIC_IMAGE_FAILED` | Agnostic person image generation fails or produces no usable `agnostic-v3.2` artifact. |
| `PREPROCESS_AGNOSTIC_MASK_FAILED` | Agnostic mask generation fails or produces no usable `agnostic-mask` artifact. |
| `PREPROCESS_REQUIRED_ARTIFACT_MISSING` | Final preflight detects that one or more required StableVITON input files or folders are missing. |
| `STABLEVITON_INPUT_ADAPTER_FAILED` | The adapter cannot create the job input root, cannot write `test_pairs.txt`, or cannot map filenames consistently. |

Failure payloads should follow the existing backend pattern:

```json
{
  "job_id": "job_20260528_120000_ab12cd34",
  "status": "failed",
  "error": {
    "code": "PREPROCESS_REQUIRED_ARTIFACT_MISSING",
    "message": "StableVITON preprocessing artifact is missing: test/image-densepose/person.png"
  }
}
```

## 7. Git safety rule

The following files and folders must never be committed:

```text
*.ckpt
DATA/**
samples_smoke/**
backend/outputs/**
backend/logs/**
stableviton_raw/**
*.jpg
*.jpeg
*.png
*.webp
```

Allowed tracked files:

- Documentation under `docs/**`.
- Source scripts under `scripts/**`.
- Backend source under `backend/app/**`.
- Example templates that do not contain real dataset rows, images, generated outputs, checkpoints, or private local assets.

Preprocessing implementation PRs should always check `git status --ignored --short` before commit if they execute local image generation.

## 8. Work separation plan

Related issues:

- #48 Uploaded image 기반 StableVITON input adapter 구현
- #50 StableVITON preprocessing artifacts 생성 pipeline 설계
- #51 PC3 StableVITON batch evaluation 및 failure case 수집

Recommended implementation order:

1. #48 input adapter
2. Cloth-mask preparation
3. DensePose generation
4. `agnostic-v3.2` / `agnostic-mask` generation
5. Full upload-based inference smoke test
6. PC3 batch evaluation

This order keeps the system testable at each boundary. The adapter can be validated before model-dependent preprocessing is available, and each preprocessing artifact can then be added with a specific failure mode and preflight check.
