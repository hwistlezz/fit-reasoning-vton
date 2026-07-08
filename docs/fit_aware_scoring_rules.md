# Fit-Aware Scoring Rules

## Purpose

This document defines the first rule-based scorer for post-generation
fit-aware reranking. The scorer consumes candidate objects that embed
`fit_analysis.v2` and returns a deterministic `fit_score` in the range `0..100`.

The rules are conservative. They prefer complete, high-confidence fit analysis
over aggressive interpretation of missing measurements. `sleeve_length_ratio`
is treated as a proxy, not as a calibrated sleeve-end measurement.

## Inputs

For each candidate, read:

- `fit_analysis.fit_label`
- `fit_analysis.confidence.score`
- `fit_analysis.confidence.level`
- `fit_analysis.confidence.warnings`
- `fit_analysis.measurements.shoulder_ratio`
- `fit_analysis.measurements.torso_width_ratio`
- `fit_analysis.measurements.garment_length_ratio`
- `fit_analysis.measurements.sleeve_length_ratio`
- `fit_analysis.hotspots`
- candidate `warnings`

Core ratios:

- `shoulder_ratio`
- `torso_width_ratio`
- `garment_length_ratio`

Proxy ratio:

- `sleeve_length_ratio`

## Score Formula Draft

Start from the calibrated confidence score:

```text
fit_score = clamp(confidence.score, 0, 100)
```

Then apply additive adjustments and clamp again to `0..100`.

### Fit Label Adjustment

| fit_label | adjustment | rationale |
| --- | ---: | --- |
| `regular` | `+12` | Preferred everyday fit. |
| `slightly_oversized` | `+6` | Acceptable fit, especially for outer/top garments. |
| `oversized` | `-12` | Usually less ideal unless user preference says otherwise. |
| `fitted_or_slim_direction` | `-8` | Can be acceptable but has tightness risk. |
| `unknown_low_confidence` | `-30` | Do not select unless all candidates are weak. |
| `unknown` or missing | `-20` | Analysis did not produce a reliable label. |

Future user preference may change label weights, but the default product
behavior should avoid choosing low-confidence candidates when a complete
regular or slightly oversized candidate exists.

### Core Ratio Coverage Adjustment

Count missing core ratios:

```text
missing_core_ratio_count = count_missing(
  shoulder_ratio,
  torso_width_ratio,
  garment_length_ratio
)
```

Apply:

| missing_core_ratio_count | adjustment |
| ---: | ---: |
| `0` | `+8` |
| `1` | `-6` |
| `2` | `-16` |
| `3` | `-25` |

If `confidence.warnings` contains `missing_core_ratio_count=N`, use that `N`
when it is present and consistent with the measurements. If the warning is
missing, compute from measurements.

### Warning Adjustment

| warning | adjustment |
| --- | ---: |
| `cloth_type_unknown` | `-12` |
| `missing_core_ratio_count=N` | already handled by core coverage |
| sleeve proxy warning | `0` score penalty, user-facing warning only |
| future generation artifact warning, mild | `-5` |
| future generation artifact warning, severe | `-20` |

The current fit analyzer already penalizes `cloth_type=unknown` in confidence.
The reranker applies a second small selection penalty because unknown garment
type makes cross-candidate comparison less stable.

### Ratio Severity Adjustment

Only evaluate a ratio if it is present. Missing ratios are handled by core
coverage rules and should not create hotspots or severity statements.

Draft default ideal bands:

| ratio | ideal band | acceptable band | penalty outside acceptable |
| --- | --- | --- | ---: |
| `shoulder_ratio` | `0.92..1.12` | `0.85..1.22` | up to `-12` |
| `torso_width_ratio` | `0.92..1.15` | `0.85..1.25` | up to `-12` |
| `garment_length_ratio` | `0.85..1.20` | `0.75..1.35` | up to `-10` |
| `sleeve_length_ratio` | no calibrated band | no calibrated band | `0` |

For each core ratio:

```text
if value inside ideal band:
  adjustment += 3
elif value inside acceptable band:
  adjustment += 0
else:
  adjustment -= severity_penalty(value)
```

`severity_penalty` should grow with distance from the acceptable band and cap at
the table maximum.

Do not use `sleeve_length_ratio` to strongly promote or demote candidates until
sleeve-end detection is calibrated. It can be displayed as a proxy with a
warning.

### Hotspot Severity Adjustment

For each selected candidate:

- Use `fit_analysis.hotspots` as display annotations.
- Do not create a score penalty just because a hotspot exists.
- If a hotspot value confirms a severe out-of-band core ratio, the ratio
  severity rule already applies.
- Ignore hotspots whose measurement is missing. The current loader suppresses
  those, and the evaluator should preserve that behavior.

## Reranking Logic

1. Validate all candidates.
2. Mark candidates without `fit_analysis.v2` as scorable but weak:
   - `fit_score = 0`
   - warning: `fit_analysis_missing`
3. Mark candidates without `image_path` and `image_url` as ineligible.
4. Compute `fit_score` for every eligible candidate.
5. Sort by:
   - higher `fit_score`
   - higher `confidence.score`
   - fewer confidence warnings
   - fewer missing core ratios
   - stable `candidate_id` ascending for deterministic ties
6. Select rank 1.
7. If selected candidate has `fit_score < 45` or label
   `unknown_low_confidence`, return it as best available but include a low
   confidence selected reason.

## Selected Reason Drafts

Regular or good confidence:

```text
Selected because it has the highest calibrated fit_score, complete core
measurements, and a reliable fit label.
```

Missing measurements:

```text
Selected as the best available candidate, but some core fit measurements were
not available. The explanation should be shown with a confidence warning.
```

Unknown low confidence:

```text
Selected as the best available candidate only because all candidates had low
fit confidence. The UI should make the low confidence state visible.
```

## Korean Explanation Template

Use one paragraph for the final user-facing explanation.

Template:

```text
{fit_label_sentence} 신뢰도는 {confidence_level_ko}입니다. {measurement_sentence} {sleeve_sentence} 이 후보는 {selection_reason_ko}
```

Fit label sentences:

| fit_label | Korean sentence |
| --- | --- |
| `regular` | `전체 핏은 보통 핏으로 판단됩니다.` |
| `slightly_oversized` | `전체 핏은 약간 여유 있는 핏으로 판단됩니다.` |
| `oversized` | `전체 핏은 넉넉한 오버핏 경향으로 판단됩니다.` |
| `fitted_or_slim_direction` | `전체 핏은 몸에 비교적 맞는 슬림한 방향으로 판단됩니다.` |
| `unknown_low_confidence` | `현재 결과는 핏 판단 신뢰도가 낮습니다.` |
| missing or unknown | `현재 결과는 핏 판단을 보류해야 합니다.` |

Confidence level Korean:

| confidence.level | Korean |
| --- | --- |
| `high` | `높음` |
| `medium` | `중간` |
| `low` | `낮음` |
| `unknown` | `알 수 없음` |

Measurement sentence rules:

- Mention only available ratios.
- Hide missing ratios in normal/high confidence cases.
- In low confidence cases, say `일부 핵심 비율은 판단 보류 상태입니다.`
- For shoulder: `어깨 비율은 {value}로 확인되었습니다.`
- For torso: `몸통 폭 비율은 {value}로 확인되었습니다.`
- For garment length: `기장 비율은 {value}로 확인되었습니다.`
- For sleeve: `소매 비율은 {value}로 확인되었지만, 현재 값은 손목 정렬 기반 proxy입니다.`

Selection reason Korean:

- Good candidate: `핵심 비율과 신뢰도가 가장 안정적이어서 선택되었습니다.`
- Some missing ratios: `사용 가능한 측정값 기준으로 가장 안정적인 후보라 선택되었습니다.`
- Low confidence: `다만 모든 후보의 신뢰도가 낮아 결과 해석에 주의가 필요합니다.`

Example:

```text
전체 핏은 보통 핏으로 판단됩니다. 신뢰도는 높음입니다. 어깨 비율은 1.05로 확인되었고, 몸통 폭 비율은 1.08로 확인되었습니다. 소매 비율은 1.00으로 확인되었지만, 현재 값은 손목 정렬 기반 proxy입니다. 이 후보는 핵심 비율과 신뢰도가 가장 안정적이어서 선택되었습니다.
```

## Calibration Notes

- `cloth_type_unknown` should make a candidate less likely to win unless the
  other candidates are worse.
- `unknown_low_confidence` should not outrank regular or slightly oversized
  candidates with comparable confidence.
- Missing core ratios should reduce ranking confidence but should not produce
  fake hotspots.
- Sleeve proxy should be visible in explanations and warnings, but it should
  not dominate selection.

## Future Inputs

Generation artifact warnings are intentionally future fields. Examples:

- `generation_artifact_mild`
- `generation_artifact_severe`
- `cloth_texture_distortion`
- `skin_bleed`
- `body_shape_distortion`

These should be added at the candidate layer first. Only move them into
`fit_analysis` if the fit analyzer directly computes them.

## Production Online Visual Proxy

Offline visual scoring may use worn/target references and PSNR/SSIM for
evaluation. Production scoring must not depend on those references. Production
candidate reranking should use a separate online visual proxy score attached at
the candidate layer.

Online visual fields:

- `online_visual_score`
- `online_visual_score_source`
- `online_visual_score_mode`
- `online_visual_components`
- `online_visual_warnings`
- `candidate_specific_online_score`
- `production_safe`

Recommended combination:

```text
if online_visual_score is unavailable:
  combined_score = fit_score - 5
else:
  combined_score = 0.75 * fit_score + 0.25 * online_visual_score - warning_penalty
```

Use online visual scoring as a tie-breaker and visual quality guardrail:

1. eligible success candidate
2. higher `combined_score`
3. higher `fit_score`
4. higher `online_visual_score`
5. higher confidence score
6. fewer warnings
7. fewer missing core ratios
8. stable `candidate_id`

Warning penalties should be conservative and based on measured artifacts, not
generator name. Example penalties:

- `generation_artifact_mild`: `-3`
- `generation_artifact_severe`: `-12`
- `agnostic_change_leakage`: `-6`
- `body_region_distortion_proxy`: `-8`
- missing candidate image: ineligible

Detailed design:

```text
docs/online_candidate_visual_proxy_scorer.md
```
