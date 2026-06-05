from __future__ import annotations

import argparse
import json
import math
import os
import platform
import random
import sys
import time
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


DEFAULT_DATA_ROOT = Path("backend/datasets/lora_pilot_aihub_1k")
DEFAULT_OUTPUT_ROOT = Path("backend/training/outputs/lora_1k_training_smoke")
DEFAULT_IMAGE_SIZE = (512, 384)
TEN_K_SAMPLE_COUNT = 9995


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a small pre-LoRA training smoke test on the AIHub LoRA dataset."
    )
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--image-size", type=int, nargs=2, default=DEFAULT_IMAGE_SIZE, metavar=("HEIGHT", "WIDTH"))
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--save-every", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", choices=("cuda", "cpu", "auto"), default="cuda")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    validation_error = _validate_args(args)
    if validation_error:
        print(validation_error, file=sys.stderr)
        return 1

    try:
        torch, DataLoader, AihubLoraTorchDataset = _import_runtime()
    except ImportError as exc:
        print(f"torch import failed: {exc}", file=sys.stderr)
        return 1

    _seed_everything(torch, args.seed)

    height, width = args.image_size
    dataset = AihubLoraTorchDataset(args.data_root, image_height=height, image_width=width)
    cuda_available = bool(torch.cuda.is_available())
    device = _resolve_device(torch, args.device, cuda_available)
    device_name = torch.cuda.get_device_name(0) if cuda_available else None
    use_cuda = device.type == "cuda"

    if use_cuda:
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=use_cuda,
    )

    model = TinyTryOnSmokeModel(torch).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    criterion = torch.nn.L1Loss()

    output_root = args.output_root
    checkpoint_dir = output_root / "checkpoints"
    sample_dir = output_root / "samples"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "task": "pre_lora_training_smoke",
        "note": "This is not StableVITON LoRA fine-tuning.",
        "data_root": _display_path(args.data_root),
        "output_root": _display_path(output_root),
        "manifest_count": len(dataset),
        "steps_requested": args.steps,
        "steps_completed": 0,
        "batch_size": args.batch_size,
        "image_size": [height, width],
        "lr": args.lr,
        "num_workers": args.num_workers,
        "save_every": args.save_every,
        "seed": args.seed,
        "cuda_available": cuda_available,
        "device": str(device),
        "device_name": device_name,
        "environment": _environment_summary(torch),
        "first_loss": None,
        "final_loss": None,
        "loss_nan": False,
        "loss_history": [],
        "elapsed_sec": 0.0,
        "avg_step_time_sec": 0.0,
        "peak_vram_mb": 0.0,
        "checkpoints": [],
        "samples": [],
        "train_summary_json": _display_path(output_root / "train_summary.json"),
        "estimates": {},
        "error": None,
    }

    model.train()
    data_iter = iter(loader)
    start_time = time.perf_counter()
    last_batch: dict[str, Any] | None = None
    last_prediction = None

    try:
        for step in range(1, args.steps + 1):
            try:
                batch = next(data_iter)
            except StopIteration:
                data_iter = iter(loader)
                batch = next(data_iter)

            person = batch["person"].to(device, non_blocking=use_cuda)
            cloth = batch["cloth"].to(device, non_blocking=use_cuda)
            target = batch["target"].to(device, non_blocking=use_cuda)
            model_input = torch.cat([person, cloth], dim=1)

            optimizer.zero_grad(set_to_none=True)
            prediction = model(model_input)
            loss = criterion(prediction, target)

            if torch.isnan(loss).item():
                summary["loss_nan"] = True
                summary["error"] = f"loss became NaN at step {step}"
                break

            loss.backward()
            optimizer.step()

            if use_cuda:
                torch.cuda.synchronize(device)

            loss_value = float(loss.detach().cpu())
            if summary["first_loss"] is None:
                summary["first_loss"] = loss_value
            summary["final_loss"] = loss_value
            summary["loss_history"].append({"step": step, "loss": loss_value})
            summary["steps_completed"] = step
            last_batch = batch
            last_prediction = prediction.detach().cpu()

            if _should_save(step, args.steps, args.save_every):
                checkpoint_path = _save_checkpoint(
                    torch=torch,
                    checkpoint_dir=checkpoint_dir,
                    model=model,
                    optimizer=optimizer,
                    args=args,
                    step=step,
                    loss_value=loss_value,
                )
                summary["checkpoints"].append(_display_path(checkpoint_path))

                if last_batch is not None and last_prediction is not None:
                    sample_path = sample_dir / f"sample_step_{step:04d}.jpg"
                    _save_sample_grid(
                        path=sample_path,
                        person=last_batch["person"][0],
                        cloth=last_batch["cloth"][0],
                        prediction=last_prediction[0],
                        target=last_batch["target"][0],
                        label=f"step {step} loss {loss_value:.4f}",
                    )
                    summary["samples"].append(_display_path(sample_path))
    except Exception as exc:
        summary["error"] = str(exc)
        print(f"training smoke failed: {exc}", file=sys.stderr)

    elapsed = time.perf_counter() - start_time
    summary["elapsed_sec"] = round(elapsed, 4)
    if summary["steps_completed"]:
        summary["avg_step_time_sec"] = round(elapsed / summary["steps_completed"], 6)
    if use_cuda:
        summary["peak_vram_mb"] = round(torch.cuda.max_memory_allocated(device) / (1024 * 1024), 2)
    summary["estimates"] = _build_estimates(summary["avg_step_time_sec"], args.batch_size)

    _write_summary(output_root / "train_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["error"] is None and not summary["loss_nan"] else 1


def _validate_args(args: argparse.Namespace) -> str | None:
    if args.steps <= 0:
        return "--steps must be positive."
    if args.batch_size <= 0:
        return "--batch-size must be positive."
    if args.image_size[0] <= 0 or args.image_size[1] <= 0:
        return "--image-size values must be positive."
    if args.lr <= 0:
        return "--lr must be positive."
    if args.num_workers < 0:
        return "--num-workers must be non-negative."
    if args.save_every < 0:
        return "--save-every must be non-negative."
    if not args.data_root.is_dir():
        return f"data-root not found: {args.data_root}"
    if not (args.data_root / "manifest.jsonl").is_file():
        return f"manifest.jsonl not found: {args.data_root / 'manifest.jsonl'}"
    return None


def _import_runtime() -> tuple[Any, Any, Any]:
    import torch
    from torch.utils.data import DataLoader

    from backend.training.datasets.aihub_lora_torch_dataset import AihubLoraTorchDataset

    return torch, DataLoader, AihubLoraTorchDataset


def _seed_everything(torch: Any, seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _resolve_device(torch: Any, requested_device: str, cuda_available: bool) -> Any:
    if requested_device == "cpu":
        return torch.device("cpu")
    if requested_device == "auto":
        return torch.device("cuda" if cuda_available else "cpu")
    if requested_device == "cuda" and cuda_available:
        return torch.device("cuda")
    return torch.device("cpu")


def TinyTryOnSmokeModel(torch: Any) -> Any:
    nn = torch.nn
    return nn.Sequential(
        nn.Conv2d(6, 16, kernel_size=3, padding=1),
        nn.ReLU(inplace=True),
        nn.Conv2d(16, 16, kernel_size=3, padding=1),
        nn.ReLU(inplace=True),
        nn.Conv2d(16, 8, kernel_size=3, padding=1),
        nn.ReLU(inplace=True),
        nn.Conv2d(8, 3, kernel_size=1),
        nn.Sigmoid(),
    )


def _should_save(step: int, total_steps: int, save_every: int) -> bool:
    if step == total_steps:
        return True
    return save_every > 0 and step % save_every == 0


def _save_checkpoint(
    *,
    torch: Any,
    checkpoint_dir: Path,
    model: Any,
    optimizer: Any,
    args: argparse.Namespace,
    step: int,
    loss_value: float,
) -> Path:
    checkpoint_path = checkpoint_dir / f"checkpoint_step_{step:04d}.pt"
    torch.save(
        {
            "step": step,
            "loss": loss_value,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "args": {
                "data_root": str(args.data_root),
                "steps": args.steps,
                "batch_size": args.batch_size,
                "image_size": list(args.image_size),
                "lr": args.lr,
                "seed": args.seed,
            },
        },
        checkpoint_path,
    )
    return checkpoint_path


def _save_sample_grid(
    *,
    path: Path,
    person: Any,
    cloth: Any,
    prediction: Any,
    target: Any,
    label: str,
) -> None:
    tiles = [
        ("person", _tensor_to_image(person)),
        ("cloth", _tensor_to_image(cloth)),
        ("prediction", _tensor_to_image(prediction)),
        ("target", _tensor_to_image(target)),
    ]
    tile_width, tile_height = tiles[0][1].size
    label_height = 24
    canvas = Image.new("RGB", (tile_width * len(tiles), tile_height + label_height * 2), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((6, 4), label, fill=(0, 0, 0))

    for index, (name, image) in enumerate(tiles):
        x = index * tile_width
        canvas.paste(image, (x, label_height))
        draw.text((x + 6, tile_height + label_height + 4), name, fill=(0, 0, 0))

    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, quality=92)


def _tensor_to_image(tensor: Any) -> Image.Image:
    tensor = tensor.detach().cpu().clamp(0.0, 1.0)
    tensor = (tensor * 255.0).byte().permute(1, 2, 0).contiguous()
    return Image.fromarray(tensor.numpy(), mode="RGB")


def _build_estimates(avg_step_time_sec: float, batch_size: int) -> dict[str, Any]:
    steps_per_epoch = math.ceil(TEN_K_SAMPLE_COUNT / batch_size)
    epoch_seconds = steps_per_epoch * avg_step_time_sec
    thousand_step_seconds = 1000 * avg_step_time_sec
    return {
        "assumed_10k_sample_count": TEN_K_SAMPLE_COUNT,
        "batch_size": batch_size,
        "steps_per_10k_epoch": steps_per_epoch,
        "estimated_10k_epoch_time_sec": round(epoch_seconds, 2),
        "estimated_10k_epoch_time_min": round(epoch_seconds / 60, 2),
        "estimated_1000_step_time_sec": round(thousand_step_seconds, 2),
        "estimated_1000_step_time_min": round(thousand_step_seconds / 60, 2),
    }


def _environment_summary(torch: Any) -> dict[str, Any]:
    return {
        "os": platform.platform(),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "d_drive_free_gb": _drive_free_gb("D:\\"),
    }


def _drive_free_gb(path: str) -> float | None:
    if os.name != "nt":
        return None
    try:
        import shutil

        return round(shutil.disk_usage(path).free / (1024**3), 2)
    except OSError:
        return None


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
