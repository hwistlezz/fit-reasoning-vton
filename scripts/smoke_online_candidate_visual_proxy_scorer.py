from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.fit_aware_evaluator import score_candidate  # noqa: E402
from backend.app.services.online_candidate_visual_proxy_scorer import (  # noqa: E402
    warning_penalty,
    score_online_candidate_visual_proxy,
)

DEFAULT_MANIFEST = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\chunk_001_fit_analysis_attachment_smoke_30\pc3_chunk_001_sanity_candidate_manifest_with_fit_analysis.jsonl"
)
DEFAULT_FALLBACK_MANIFEST = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\chunk_001_blur_fill_package_sanity_inference_30\pc3_chunk_001_sanity_candidate_manifest.jsonl"
)
DEFAULT_ARTIFACT_ROOT = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\datasets\aihub_39k_artifact_chunks\chunk_001_blur_fill_package_sanity"
)
DEFAULT_OUTPUT_ROOT = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\chunk_001_online_proxy_visual_scoring_smoke_30"
)
DEFAULT_OFFLINE_RERANKING = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\chunk_001_candidate_visual_scoring_smoke_30\fit_aware_visual_reranking_smoke.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test production-safe online candidate visual proxy scoring.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fallback-manifest", type=Path, default=DEFAULT_FALLBACK_MANIFEST)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--offline-reranking", type=Path, default=DEFAULT_OFFLINE_RERANKING)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)

    manifest_path = args.manifest if args.manifest.is_file() else args.fallback_manifest
    rows = load_jsonl(manifest_path)
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("input manifest has no rows")

    output_manifest = args.output_root / "pc3_chunk_001_sanity_candidate_manifest_with_online_visual_score.jsonl"
    summary_path = args.output_root / "online_candidate_visual_proxy_summary.json"
    reranking_path = args.output_root / "fit_aware_online_proxy_reranking_smoke.json"
    reranking_summary_path = args.output_root / "fit_aware_online_proxy_reranking_smoke_summary.json"
    report_path = args.output_root / "online_candidate_visual_proxy_report.md"

    enriched_rows: list[dict[str, Any]] = []
    image_paths_valid = 0
    source_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    candidate_specific_count = 0
    production_safe_count = 0
    score_values: list[float] = []
    generator_components: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for row in rows:
        candidate = dict(row)
        image_path = Path(str(candidate.get("image_path") or ""))
        if image_path.is_file():
            image_paths_valid += 1
        online_fields = score_online_candidate_visual_proxy(candidate, artifact_root=args.artifact_root)
        candidate.update(online_fields)
        enriched_rows.append(candidate)

        source_counts[str(candidate.get("online_visual_score_source") or "unavailable")] += 1
        mode_counts[str(candidate.get("online_visual_score_mode") or "unavailable")] += 1
        if candidate.get("candidate_specific_online_score"):
            candidate_specific_count += 1
        if candidate.get("production_safe") is True:
            production_safe_count += 1
        score = candidate.get("online_visual_score")
        if isinstance(score, int | float):
            score_values.append(float(score))
            generator = str(candidate.get("generator") or "unknown")
            generator_components[generator]["online_visual_score"].append(float(score))
            components = candidate.get("online_visual_components") or {}
            for key in (
                "image_readability",
                "dimension_exposure_sanity",
                "artifact_score",
                "cloth_mask_alignment_proxy",
                "agnostic_boundary_consistency",
                "body_preservation_proxy",
                "pose_visibility_sanity",
                "garment_boundary_proxy",
            ):
                value = components.get(key)
                if isinstance(value, int | float):
                    generator_components[generator][key].append(float(value))

    write_jsonl(output_manifest, enriched_rows)

    pair_groups = group_by_pair(enriched_rows)
    reranking_results, reranking_summary = rerank_with_online_proxy(pair_groups)
    reranking_path.write_text(json.dumps(reranking_results, ensure_ascii=False, indent=2), encoding="utf-8")
    reranking_summary_path.write_text(json.dumps(reranking_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    offline_comparison = compare_with_offline(args.offline_reranking, reranking_results)
    generator_average = {
        generator: {key: round(sum(values) / len(values), 6) for key, values in metrics.items() if values}
        for generator, metrics in generator_components.items()
    }
    score_range = {
        "min": round(min(score_values), 6) if score_values else None,
        "max": round(max(score_values), 6) if score_values else None,
    }
    summary = {
        "task": "online_candidate_visual_proxy_scoring_smoke",
        "created_at": utc_now(),
        "input_manifest": str(manifest_path),
        "fallback_manifest_used": manifest_path == args.fallback_manifest,
        "input_candidate_count": len(rows),
        "image_paths_valid": image_paths_valid,
        "artifact_root": str(args.artifact_root),
        "output_manifest": str(output_manifest),
        "online_score_source_distribution": dict(source_counts),
        "online_score_mode_distribution": dict(mode_counts),
        "candidate_specific_online_score_count": candidate_specific_count,
        "production_safe_count": production_safe_count,
        "score_range": score_range,
        "generator_average": generator_average,
        "reranking_summary": reranking_summary,
        "offline_scorer_comparison": offline_comparison,
        "gt_worn_reference_used_for_online_score": False,
        "additional_inference_run": False,
        "lora_run": False,
        "rank8_module16_run": False,
        "full_10000_inference_run": False,
        "images_copied": False,
        "files_deleted": False,
        "backend_endpoint_changed": False,
        "frontend_changed": False,
        "schema_changed": False,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(summary), encoding="utf-8")

    print(json.dumps({"summary": str(summary_path), "report": str(report_path), **summary}, ensure_ascii=False, indent=2))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"line {line_number} is not an object")
        rows.append(payload)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def group_by_pair(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("pair_id") or "")].append(row)
    return dict(groups)


def rerank_with_online_proxy(pair_groups: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    selected_distribution: Counter[str] = Counter()
    online_resolved_count = 0
    deterministic_tie_count = 0
    unavailable_count = 0
    low_confidence_count = 0

    for pair_id, candidates in sorted(pair_groups.items()):
        scored = []
        for candidate in candidates:
            fit_scored = score_candidate(candidate, pair_id=pair_id)
            online_score = candidate.get("online_visual_score")
            online_warnings = candidate.get("online_visual_warnings") or []
            penalty = warning_penalty([str(warning) for warning in online_warnings])
            if not isinstance(online_score, int | float):
                combined_score = float(fit_scored.get("fit_score") or 0.0) - 5.0
                unavailable_count += 1
            else:
                combined_score = (0.75 * float(fit_scored.get("fit_score") or 0.0)) + (0.25 * float(online_score)) - penalty
            fit_scored.update(
                {
                    "online_visual_score": online_score,
                    "online_visual_score_source": candidate.get("online_visual_score_source"),
                    "online_visual_score_mode": candidate.get("online_visual_score_mode"),
                    "online_visual_warnings": online_warnings,
                    "candidate_specific_online_score": candidate.get("candidate_specific_online_score"),
                    "production_safe": candidate.get("production_safe"),
                    "online_warning_penalty": penalty,
                    "combined_score": round(max(0.0, min(100.0, combined_score)), 4),
                }
            )
            if "candidate_image_missing" in online_warnings or "candidate_image_load_failed" in online_warnings:
                fit_scored["eligible"] = False
                reasons = list(fit_scored.get("ineligibility_reasons") or [])
                reasons.append("online_candidate_image_unavailable")
                fit_scored["ineligibility_reasons"] = reasons
            scored.append(fit_scored)

        deterministic = sorted(scored, key=fit_only_sort_key)
        online_ranked = sorted(scored, key=online_sort_key)
        selected = online_ranked[0] if online_ranked else None
        if selected:
            selected_distribution[str(selected.get("generator") or "unknown")] += 1
            if float(selected.get("confidence_score") or 0.0) < 45.0:
                low_confidence_count += 1

        top_base_group = [candidate for candidate in scored if fit_base_tie_key(candidate) == fit_base_tie_key(deterministic[0])]
        online_scores = [candidate.get("online_visual_score") for candidate in top_base_group if candidate.get("candidate_specific_online_score")]
        unique_online_scores = {round(float(score), 6) for score in online_scores if isinstance(score, int | float)}
        if len(top_base_group) > 1 and len(unique_online_scores) > 1:
            online_resolved_count += 1
        elif len(top_base_group) > 1:
            deterministic_tie_count += 1

        results.append(
            {
                "pair_id": pair_id,
                "selected_candidate_id": selected.get("candidate_id") if selected else None,
                "selected_generator": selected.get("generator") if selected else None,
                "selected_combined_score": selected.get("combined_score") if selected else None,
                "selected_online_visual_score": selected.get("online_visual_score") if selected else None,
                "fit_only_candidate_id": deterministic[0].get("candidate_id") if deterministic else None,
                "online_visual_tie_breaker_used": len(top_base_group) > 1 and len(unique_online_scores) > 1,
                "ranked_candidates": public_candidates(online_ranked),
            }
        )

    summary = {
        "schema_version": "fit_aware_online_proxy_reranking_smoke.v1",
        "created_at": utc_now(),
        "pair_count": len(pair_groups),
        "candidate_count": sum(len(candidates) for candidates in pair_groups.values()),
        "selected_generator_distribution": dict(selected_distribution),
        "online_visual_tie_breaker_resolved_count": online_resolved_count,
        "unchanged_deterministic_tie_breaker_count": deterministic_tie_count,
        "online_score_unavailable_count": unavailable_count,
        "low_confidence_count": low_confidence_count,
        "combined_score_used": True,
        "combined_score_rule": "0.75 * fit_score + 0.25 * online_visual_score - warning_penalty",
    }
    return results, summary


def fit_base_tie_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    return (
        0 if candidate.get("eligible") else 1,
        -float(candidate.get("fit_score") or 0.0),
        -float(candidate.get("confidence_score") or 0.0),
        len(candidate.get("warnings") or []),
        int(candidate.get("missing_core_ratio_count") or 0),
    )


def fit_only_sort_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    return (*fit_base_tie_key(candidate), str(candidate.get("candidate_id") or ""))


def online_sort_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    online_score = candidate.get("online_visual_score")
    online_available = bool(candidate.get("candidate_specific_online_score")) and isinstance(online_score, int | float)
    online_value = float(online_score) if online_available else -1.0
    return (
        0 if candidate.get("eligible") else 1,
        -float(candidate.get("combined_score") or 0.0),
        -float(candidate.get("fit_score") or 0.0),
        0 if online_available else 1,
        -online_value,
        -float(candidate.get("confidence_score") or 0.0),
        len((candidate.get("warnings") or []) + (candidate.get("online_visual_warnings") or [])),
        int(candidate.get("missing_core_ratio_count") or 0),
        str(candidate.get("candidate_id") or ""),
    )


def public_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = (
        "candidate_id",
        "generator",
        "fit_score",
        "confidence_score",
        "online_visual_score",
        "combined_score",
        "online_warning_penalty",
        "candidate_specific_online_score",
        "production_safe",
        "eligible",
        "online_visual_warnings",
    )
    return [{key: candidate.get(key) for key in keys} for candidate in candidates]


def compare_with_offline(path: Path, online_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not path.is_file():
        return {"available": False, "agreement_count": None, "disagreement_count": None, "note": "offline scorer result unavailable"}
    try:
        offline_payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"available": False, "agreement_count": None, "disagreement_count": None, "note": "offline scorer result unreadable"}
    if not isinstance(offline_payload, list):
        return {"available": False, "agreement_count": None, "disagreement_count": None, "note": "offline scorer result format unsupported"}
    offline_by_pair = {
        str(row.get("pair_id")): row.get("selected_generator")
        for row in offline_payload
        if isinstance(row, dict)
    }
    agreement = 0
    disagreement = 0
    missing = 0
    for row in online_results:
        pair_id = str(row.get("pair_id"))
        offline_generator = offline_by_pair.get(pair_id)
        if offline_generator is None:
            missing += 1
        elif offline_generator == row.get("selected_generator"):
            agreement += 1
        else:
            disagreement += 1
    return {
        "available": True,
        "offline_result_path": str(path),
        "agreement_count": agreement,
        "disagreement_count": disagreement,
        "missing_pair_count": missing,
        "note": "offline scorer uses worn/target reference; comparison is report-only and not part of online score",
    }


def build_report(summary: dict[str, Any]) -> str:
    reranking = summary["reranking_summary"]
    offline = summary["offline_scorer_comparison"]
    lines = [
        "# PC3 online candidate visual proxy scorer smoke",
        "",
        "## 목적",
        "GT/worn reference 없이 production-safe artifact만 사용해 candidate-specific online visual score를 계산했다.",
        "",
        "## 입력",
        f"- input_manifest: `{summary['input_manifest']}`",
        f"- input_candidate_count: {summary['input_candidate_count']}",
        f"- image_paths_valid: {summary['image_paths_valid']}",
        f"- artifact_root: `{summary['artifact_root']}`",
        "",
        "## Online Score",
        f"- source_distribution: `{summary['online_score_source_distribution']}`",
        f"- mode_distribution: `{summary['online_score_mode_distribution']}`",
        f"- candidate_specific_online_score_count: {summary['candidate_specific_online_score_count']}",
        f"- production_safe_count: {summary['production_safe_count']}",
        f"- score_range: `{summary['score_range']}`",
        "",
        "## Reranking Smoke",
        f"- selected_generator_distribution: `{reranking['selected_generator_distribution']}`",
        f"- online_visual_tie_breaker_resolved_count: {reranking['online_visual_tie_breaker_resolved_count']}",
        f"- unchanged_deterministic_tie_breaker_count: {reranking['unchanged_deterministic_tie_breaker_count']}",
        f"- combined_score_rule: `{reranking['combined_score_rule']}`",
        "",
        "## Offline Scorer 비교",
        f"- available: {offline.get('available')}",
        f"- agreement_count: {offline.get('agreement_count')}",
        f"- disagreement_count: {offline.get('disagreement_count')}",
        f"- note: {offline.get('note')}",
        "",
        "## 안전 확인",
        "- online score 계산에 worn/fit/target reference를 사용하지 않았다.",
        "- 추가 StableVITON inference, LoRA 실행, rank8-module16 실행, full 10,000 inference는 수행하지 않았다.",
        "- 이미지 복사/삭제, backend endpoint 변경, frontend 변경, schema 변경은 수행하지 않았다.",
        "",
        "## 한계",
        "- rule-based proxy이므로 실제 사람 눈의 착장 품질 판단을 대체하지 않는다.",
        "- mask/change/body preservation heuristic은 segmentation 품질과 preprocessing artifact에 민감하다.",
        "- production 적용 전 human review와 larger sample calibration이 필요하다.",
    ]
    return "\n".join(lines) + "\n"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
