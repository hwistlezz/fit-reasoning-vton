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

from backend.app.services.candidate_visual_scorer import (  # noqa: E402
    PER_CANDIDATE_METRIC_SOURCE,
    score_candidate_visual,
    score_from_reference_metrics,
)
from backend.app.services.fit_aware_evaluator import score_candidate  # noqa: E402

DEFAULT_MANIFEST = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\chunk_001_fit_analysis_attachment_smoke_30\pc3_chunk_001_sanity_candidate_manifest_with_fit_analysis.jsonl"
)
DEFAULT_METRICS = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\chunk_001_blur_fill_package_sanity_inference_30\metrics.json"
)
DEFAULT_ARTIFACT_ROOT = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\datasets\aihub_39k_artifact_chunks\chunk_001_blur_fill_package_sanity"
)
DEFAULT_OUTPUT_ROOT = Path(
    r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\chunk_001_candidate_visual_scoring_smoke_30"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test candidate-specific visual scoring and reranking.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--metrics-json", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(args.manifest)
    if args.limit is not None:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("input manifest has no rows")

    metrics_payload = load_json(args.metrics_json)
    per_candidate_metrics = extract_per_candidate_metrics(metrics_payload)
    metrics_structure = classify_metrics(metrics_payload, per_candidate_metrics)

    output_manifest = args.output_root / "pc3_chunk_001_sanity_candidate_manifest_with_fit_and_visual_score.jsonl"
    summary_path = args.output_root / "candidate_visual_scoring_summary.json"
    reranking_path = args.output_root / "fit_aware_visual_reranking_smoke.json"
    reranking_summary_path = args.output_root / "fit_aware_visual_reranking_smoke_summary.json"
    report_path = args.output_root / "candidate_visual_scoring_report.md"

    enriched_rows: list[dict[str, Any]] = []
    source_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    candidate_specific_count = 0
    image_paths_valid = 0
    reference_status = Counter()
    generator_components: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for row in rows:
        candidate = dict(row)
        image_path = Path(str(candidate.get("image_path") or ""))
        if image_path.is_file():
            image_paths_valid += 1
        reference_path = resolve_reference_path(candidate, args.artifact_root)
        if reference_path is None:
            reference_status["unavailable"] += 1
        elif reference_path.is_file():
            reference_status["available"] += 1
        else:
            reference_status["missing"] += 1

        metric_key = metric_lookup_key(candidate)
        metric_payload = per_candidate_metrics.get(metric_key)
        if metric_payload is not None:
            visual = score_from_reference_metrics(
                psnr=metric_payload.get("psnr"),
                ssim=metric_payload.get("ssim"),
            )
            visual_score_components = dict(visual.get("components") or {})
            visual_score_components["metric_lookup_key"] = list(metric_key)
            visual_fields = {
                "visual_score": visual.get("visual_score"),
                "visual_score_source": PER_CANDIDATE_METRIC_SOURCE,
                "visual_score_mode": "offline_eval",
                "visual_warnings": visual.get("visual_warnings") or [],
                "candidate_specific_visual_score": bool(visual.get("candidate_specific_visual_score")),
                "visual_score_components": visual_score_components,
            }
        else:
            visual_fields = score_candidate_visual(candidate, reference_image_path=reference_path)

        candidate.update(visual_fields)
        enriched_rows.append(candidate)
        source = str(candidate.get("visual_score_source") or "unavailable")
        mode = str(candidate.get("visual_score_mode") or "unavailable")
        source_counts[source] += 1
        mode_counts[mode] += 1
        if candidate.get("candidate_specific_visual_score"):
            candidate_specific_count += 1
        components = candidate.get("visual_score_components") or {}
        generator = str(candidate.get("generator") or "unknown")
        for key in ("psnr", "ssim", "visual_score"):
            value = candidate.get(key) if key == "visual_score" else components.get(key)
            if isinstance(value, int | float):
                generator_components[generator][key].append(float(value))

    write_jsonl(output_manifest, enriched_rows)

    pair_groups = group_by_pair(enriched_rows)
    reranking_results, reranking_summary = rerank_with_visual_tie_breaker(pair_groups)
    reranking_path.write_text(json.dumps(reranking_results, ensure_ascii=False, indent=2), encoding="utf-8")
    reranking_summary_path.write_text(json.dumps(reranking_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    generator_average = {
        generator: {key: round(sum(values) / len(values), 6) for key, values in metrics.items() if values}
        for generator, metrics in generator_components.items()
    }
    reference_matching = summarize_reference_matching(reference_status, len(enriched_rows))
    summary = {
        "task": "candidate_specific_visual_scoring_smoke",
        "created_at": utc_now(),
        "input_manifest": str(args.manifest),
        "input_candidate_count": len(rows),
        "output_manifest": str(output_manifest),
        "metrics_json": str(args.metrics_json),
        "metrics_structure": metrics_structure,
        "per_candidate_metric_count": len(per_candidate_metrics),
        "artifact_root": str(args.artifact_root),
        "image_paths_valid": image_paths_valid,
        "reference_matching": reference_matching,
        "visual_score_source_distribution": dict(source_counts),
        "visual_score_mode_distribution": dict(mode_counts),
        "candidate_specific_visual_score_count": candidate_specific_count,
        "generator_average": generator_average,
        "reranking_summary": reranking_summary,
        "additional_inference_run": False,
        "rank8_module16_run": False,
        "full_10000_inference_run": False,
        "images_copied": False,
        "files_deleted": False,
        "schema_changed": False,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(summary, reranking_summary), encoding="utf-8")

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


def load_json(path: Path) -> Any:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def resolve_reference_path(candidate: dict[str, Any], fallback_root: Path) -> Path | None:
    pair_id = str(candidate.get("pair_id") or "")
    if not pair_id:
        return None
    artifact_root = Path(str(candidate.get("artifact_root") or fallback_root))
    candidates = [
        artifact_root / "worn" / f"{pair_id}.jpg",
        artifact_root / "fit" / f"{pair_id}.jpg",
        fallback_root / "worn" / f"{pair_id}.jpg",
        fallback_root / "fit" / f"{pair_id}.jpg",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


def extract_per_candidate_metrics(payload: Any) -> dict[tuple[str, str, str], dict[str, Any]]:
    metrics: dict[tuple[str, str, str], dict[str, Any]] = {}

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            pair_id = value.get("pair_id")
            generator = value.get("generator") or value.get("method")
            candidate_id = value.get("candidate_id") or value.get("output_id") or ""
            has_metric = any(key in value for key in ("psnr", "ssim", "lpips"))
            if pair_id and generator and has_metric:
                metrics[(str(pair_id), str(generator), str(candidate_id))] = dict(value)
                metrics[(str(pair_id), str(generator), "")] = dict(value)
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return metrics


def classify_metrics(payload: Any, per_candidate_metrics: dict[tuple[str, str, str], dict[str, Any]]) -> str:
    if per_candidate_metrics:
        return "per_candidate_available"
    if isinstance(payload, dict) and ("method_summary" in payload or "summary" in payload):
        return "generator_level_only"
    if payload is None:
        return "unavailable"
    return "generator_level_only"


def metric_lookup_key(candidate: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(candidate.get("pair_id") or ""),
        str(candidate.get("generator") or ""),
        str(candidate.get("candidate_id") or ""),
    )


def group_by_pair(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("pair_id") or "")].append(row)
    return dict(groups)


def rerank_with_visual_tie_breaker(pair_groups: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    selected_distribution: Counter[str] = Counter()
    visual_resolved_count = 0
    deterministic_tie_count = 0
    low_confidence_count = 0

    for pair_id, candidates in sorted(pair_groups.items()):
        scored = [score_candidate(candidate, pair_id=pair_id) for candidate in candidates]
        for candidate in scored:
            original = next((row for row in candidates if row.get("candidate_id") == candidate.get("candidate_id")), {})
            candidate["visual_score"] = original.get("visual_score")
            candidate["visual_score_source"] = original.get("visual_score_source")
            candidate["visual_score_mode"] = original.get("visual_score_mode")
            candidate["candidate_specific_visual_score"] = original.get("candidate_specific_visual_score")
            candidate["visual_warnings"] = original.get("visual_warnings") or []

        deterministic = sorted(scored, key=deterministic_sort_key)
        visual_ranked = sorted(scored, key=visual_sort_key)
        selected = visual_ranked[0] if visual_ranked else None
        selected_generator = selected.get("generator") if selected else None
        if selected_generator:
            selected_distribution[str(selected_generator)] += 1
        if selected and float(selected.get("confidence_score") or 0.0) < 45.0:
            low_confidence_count += 1

        top_base_group = [candidate for candidate in scored if base_tie_key(candidate) == base_tie_key(deterministic[0])]
        visual_scores = [candidate.get("visual_score") for candidate in top_base_group if candidate.get("candidate_specific_visual_score")]
        unique_visual_scores = {round(float(score), 6) for score in visual_scores if isinstance(score, int | float)}
        if len(top_base_group) > 1 and len(unique_visual_scores) > 1:
            visual_resolved_count += 1
        elif len(top_base_group) > 1:
            deterministic_tie_count += 1

        results.append(
            {
                "pair_id": pair_id,
                "selected_candidate_id": selected.get("candidate_id") if selected else None,
                "selected_generator": selected_generator,
                "selected_visual_score": selected.get("visual_score") if selected else None,
                "deterministic_candidate_id": deterministic[0].get("candidate_id") if deterministic else None,
                "visual_tie_breaker_used": len(top_base_group) > 1 and len(unique_visual_scores) > 1,
                "ranked_candidates": public_candidates(visual_ranked),
            }
        )

    summary = {
        "schema_version": "fit_aware_visual_reranking_smoke.v1",
        "created_at": utc_now(),
        "pair_count": len(pair_groups),
        "candidate_count": sum(len(candidates) for candidates in pair_groups.values()),
        "selected_generator_distribution": dict(selected_distribution),
        "visual_tie_breaker_resolved_count": visual_resolved_count,
        "unchanged_deterministic_tie_breaker_count": deterministic_tie_count,
        "low_confidence_count": low_confidence_count,
    }
    return results, summary


def base_tie_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    return (
        0 if candidate.get("eligible") else 1,
        -float(candidate.get("fit_score") or 0.0),
        -float(candidate.get("confidence_score") or 0.0),
        len(candidate.get("warnings") or []),
        int(candidate.get("missing_core_ratio_count") or 0),
    )


def deterministic_sort_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    return (*base_tie_key(candidate), str(candidate.get("candidate_id") or ""))


def visual_sort_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    visual_score = candidate.get("visual_score")
    visual_available = bool(candidate.get("candidate_specific_visual_score")) and isinstance(visual_score, int | float)
    visual_value = float(visual_score) if visual_available else -1.0
    return (*base_tie_key(candidate), 0 if visual_available else 1, -visual_value, str(candidate.get("candidate_id") or ""))


def public_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = (
        "candidate_id",
        "generator",
        "fit_score",
        "confidence_score",
        "visual_score",
        "visual_score_source",
        "visual_score_mode",
        "candidate_specific_visual_score",
        "eligible",
        "warnings",
    )
    return [{key: candidate.get(key) for key in keys} for candidate in candidates]


def summarize_reference_matching(status: Counter[str], total: int) -> str:
    if status.get("available") == total:
        return "available"
    if status.get("available"):
        return "partial"
    return "unavailable"


def build_report(summary: dict[str, Any], reranking_summary: dict[str, Any]) -> str:
    averages = summary.get("generator_average") or {}
    lines = [
        "# PC3 candidate-specific visual scorer smoke",
        "",
        "## 목적",
        "pair-level fit_analysis로는 같은 pair의 baseline/rank8 후보 차이가 반영되지 않아, generated candidate image 기반 visual_score를 보조 tie-breaker로 계산했다.",
        "",
        "## 입력",
        f"- input_manifest: `{summary['input_manifest']}`",
        f"- candidate_count: {summary['input_candidate_count']}",
        f"- metrics_structure: {summary['metrics_structure']}",
        f"- reference_matching: {summary['reference_matching']}",
        "",
        "## Visual Score",
        f"- source_distribution: `{summary['visual_score_source_distribution']}`",
        f"- mode_distribution: `{summary['visual_score_mode_distribution']}`",
        f"- candidate_specific_visual_score_count: {summary['candidate_specific_visual_score_count']}",
        "",
        "## Reranking Smoke",
        f"- selected_generator_distribution: `{reranking_summary['selected_generator_distribution']}`",
        f"- visual_tie_breaker_resolved_count: {reranking_summary['visual_tie_breaker_resolved_count']}",
        f"- unchanged_deterministic_tie_breaker_count: {reranking_summary['unchanged_deterministic_tie_breaker_count']}",
        f"- low_confidence_count: {reranking_summary['low_confidence_count']}",
        "",
        "## PSNR/SSIM 보조 비교",
    ]
    for generator, values in sorted(averages.items()):
        lines.append(f"- {generator}: `{values}`")
    lines.extend(
        [
            "",
            "## 한계",
            "- 이번 visual_score는 worn/target reference를 사용하는 offline_eval 지표다.",
            "- production 환경에서는 target/worn ground truth가 없으므로 그대로 사용할 수 없다.",
            "- 실제 제품용 candidate-specific scorer는 segmentation, pose alignment, garment boundary, artifact leakage 기반 online proxy로 고도화해야 한다.",
            "- 추가 StableVITON inference, LoRA 실행, rank8-module16 실행, full 10,000 inference는 수행하지 않았다.",
        ]
    )
    return "\n".join(lines) + "\n"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
