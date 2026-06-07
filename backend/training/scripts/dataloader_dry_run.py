from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


DEFAULT_DATA_ROOT = Path("backend/datasets/lora_pilot_aihub_10k_full")
DEFAULT_SUMMARY_JSON = Path("backend/training/outputs/lora_dataloader_dry_run/summary.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run the AIHub LoRA PyTorch DataLoader.")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--limit", type=int, default=512)
    parser.add_argument("--batch-sizes", type=int, nargs="+", default=[1, 2])
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--image-height", type=int, default=512)
    parser.add_argument("--image-width", type=int, default=384)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--device", choices=("cuda", "cpu", "auto"), default="cuda")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not _validate_inputs(args):
        return 1

    try:
        torch, DataLoader, Subset, AihubLoraTorchDataset = _import_torch_runtime()
    except ImportError as exc:
        print(f"torch import failed: {exc}", file=sys.stderr)
        return 1

    dataset = AihubLoraTorchDataset(
        args.data_root,
        image_height=args.image_height,
        image_width=args.image_width,
    )
    checked_count = min(len(dataset), args.limit)
    subset = Subset(dataset, range(checked_count))

    cuda_available = bool(torch.cuda.is_available())
    device = _resolve_device(torch, args.device, cuda_available)
    device_name = torch.cuda.get_device_name(0) if cuda_available else None

    summary: dict[str, Any] = {
        "data_root": _display_path(args.data_root),
        "manifest_count": len(dataset),
        "limit": args.limit,
        "checked_count": checked_count,
        "image_height": args.image_height,
        "image_width": args.image_width,
        "num_workers": args.num_workers,
        "requested_device": args.device,
        "device": str(device),
        "cuda_available": cuda_available,
        "device_name": device_name,
        "batch_results": [],
        "errors": 0,
    }

    for batch_size in args.batch_sizes:
        if batch_size <= 0:
            print(f"batch size must be positive: {batch_size}", file=sys.stderr)
            summary["errors"] += 1
            continue

        result = _run_batch_size(
            torch=torch,
            DataLoader=DataLoader,
            subset=subset,
            batch_size=batch_size,
            num_workers=args.num_workers,
            device=device,
        )
        summary["batch_results"].append(result)
        if result.get("error"):
            summary["errors"] += 1

    _write_summary(args.summary_json, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["errors"] == 0 else 1


def _validate_inputs(args: argparse.Namespace) -> bool:
    if args.limit < 0:
        print("--limit must be non-negative.", file=sys.stderr)
        return False
    if args.num_workers < 0:
        print("--num-workers must be non-negative.", file=sys.stderr)
        return False
    if args.image_height <= 0 or args.image_width <= 0:
        print("--image-height and --image-width must be positive.", file=sys.stderr)
        return False
    if not args.data_root.is_dir():
        print(f"data-root not found: {args.data_root}", file=sys.stderr)
        return False
    if not (args.data_root / "manifest.jsonl").is_file():
        print(f"manifest.jsonl not found: {args.data_root / 'manifest.jsonl'}", file=sys.stderr)
        return False
    return True


def _import_torch_runtime() -> tuple[Any, Any, Any, Any]:
    import torch
    from torch.utils.data import DataLoader, Subset

    from backend.training.datasets.aihub_lora_torch_dataset import AihubLoraTorchDataset

    return torch, DataLoader, Subset, AihubLoraTorchDataset


def _resolve_device(torch: Any, requested_device: str, cuda_available: bool) -> Any:
    if requested_device == "cpu":
        return torch.device("cpu")
    if requested_device == "auto":
        return torch.device("cuda" if cuda_available else "cpu")
    if requested_device == "cuda" and cuda_available:
        return torch.device("cuda")
    return torch.device("cpu")


def _run_batch_size(
    *,
    torch: Any,
    DataLoader: Any,
    subset: Any,
    batch_size: int,
    num_workers: int,
    device: Any,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "batch_size": batch_size,
        "num_batches": 0,
        "checked_samples": 0,
        "first_batch": None,
        "cuda_available": bool(torch.cuda.is_available()),
        "device": str(device),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "peak_vram_mb": 0.0,
        "elapsed_seconds": 0.0,
        "avg_batch_seconds": 0.0,
    }

    use_cuda = device.type == "cuda"
    if use_cuda:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)

    loader = DataLoader(
        subset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=use_cuda,
    )

    start = time.perf_counter()
    try:
        for batch in loader:
            person = batch["person"]
            cloth = batch["cloth"]
            target = batch["target"]

            if result["first_batch"] is None:
                result["first_batch"] = {
                    "person_shape": list(person.shape),
                    "cloth_shape": list(cloth.shape),
                    "target_shape": list(target.shape),
                    "pair_id": _metadata_preview(batch.get("pair_id")),
                    "fit_label": _metadata_preview(batch.get("fit_label")),
                    "confidence": _confidence_preview(batch.get("confidence")),
                    "prompt": _metadata_preview(batch.get("prompt")),
                }

            if use_cuda:
                person = person.to(device, non_blocking=True)
                cloth = cloth.to(device, non_blocking=True)
                target = target.to(device, non_blocking=True)
                torch.cuda.synchronize(device)

            result["num_batches"] += 1
            result["checked_samples"] += int(person.shape[0])
    except Exception as exc:
        result["error"] = str(exc)
        print(f"DataLoader dry-run failed for batch_size={batch_size}: {exc}", file=sys.stderr)

    elapsed = time.perf_counter() - start
    result["elapsed_seconds"] = round(elapsed, 4)
    if result["num_batches"]:
        result["avg_batch_seconds"] = round(elapsed / result["num_batches"], 6)
    if use_cuda:
        result["peak_vram_mb"] = round(torch.cuda.max_memory_allocated(device) / (1024 * 1024), 2)

    return result


def _metadata_preview(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def _confidence_preview(value: Any) -> Any:
    if hasattr(value, "detach"):
        return float(value.detach().cpu()[0])
    if isinstance(value, (list, tuple)):
        return value[0] if value else None
    return value


def _write_summary(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
