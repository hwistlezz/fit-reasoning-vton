"""Run a tiny StableVITON LoRA compatibility smoke.

This script imports the external StableVITON checkout without modifying it.
Generated logs, summaries, checkpoints, and images must be written under an
ignored output directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path
from types import MethodType
from typing import Any

import torch
from pytorch_lightning.callbacks import Callback
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader


class LoRALinear(nn.Module):
    def __init__(
        self,
        base: nn.Linear,
        rank: int,
        alpha: float,
        dropout: float,
    ) -> None:
        super().__init__()
        self.base = base
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()
        self.lora_down = nn.Linear(base.in_features, rank, bias=False)
        self.lora_up = nn.Linear(rank, base.out_features, bias=False)

        for param in self.base.parameters():
            param.requires_grad = False
        nn.init.kaiming_uniform_(self.lora_down.weight, a=5**0.5)
        nn.init.zeros_(self.lora_up.weight)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.base(x) + self.lora_up(self.lora_down(self.dropout(x))) * self.scaling


class StepMetricsCallback(Callback):
    def __init__(self) -> None:
        self.losses: list[float] = []
        self.steps_seen = 0

    def on_train_batch_end(
        self,
        trainer: Any,
        pl_module: Any,
        outputs: Any,
        batch: Any,
        batch_idx: int,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        del trainer, pl_module, batch, batch_idx, args, kwargs
        self.steps_seen += 1
        loss = None
        if isinstance(outputs, dict):
            loss = outputs.get("loss")
        elif torch.is_tensor(outputs):
            loss = outputs
        if torch.is_tensor(loss):
            self.losses.append(float(loss.detach().cpu()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stableviton-root", default=r"D:\GitHub\StableVITON")
    parser.add_argument(
        "--data-root",
        default=r"D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_tiny10",
    )
    parser.add_argument(
        "--output-root",
        default=r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_tiny10_1step_smoke",
    )
    parser.add_argument("--config-name", default="VITONHD")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--img-height", type=int, default=512)
    parser.add_argument("--img-width", type=int, default=384)
    parser.add_argument("--max-steps", type=int, default=1)
    parser.add_argument("--rank", type=int, default=4)
    parser.add_argument("--alpha", type=float, default=4.0)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--max-lora-modules", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--skip-vae-load", action="store_true", default=True)
    parser.add_argument("--prepare-smoke-data", dest="prepare_smoke_data", action="store_true", default=True)
    parser.add_argument("--no-prepare-smoke-data", dest="prepare_smoke_data", action="store_false")
    parser.add_argument("--enable-input-grad-for-checkpoint", action="store_true", default=True)
    parser.add_argument("--disable-gradient-checkpointing", action="store_true", default=True)
    parser.add_argument("--save-lora-path", default=None)
    parser.add_argument("--load-lora-path", default=None)
    return parser.parse_args()


def count_params(module: nn.Module, trainable_only: bool = False) -> int:
    params = module.parameters()
    if trainable_only:
        params = (param for param in params if param.requires_grad)
    return sum(param.numel() for param in params)


def ensure_smoke_dataset_shape(data_root: Path, width: int, height: int) -> None:
    train_root = data_root / "train"
    gt_dir = train_root / "gt_cloth_warped_mask"
    gt_dir.mkdir(parents=True, exist_ok=True)
    cloth_mask_dir = train_root / "cloth-mask"
    for src in cloth_mask_dir.glob("*"):
        if src.is_file():
            dst = gt_dir / src.name
            if not dst.exists():
                dst.write_bytes(src.read_bytes())

    resize_dirs = [
        "image",
        "agnostic-v3.2",
        "agnostic-mask",
        "cloth",
        "cloth-mask",
        "image-densepose",
        "gt_cloth_warped_mask",
    ]
    for dirname in resize_dirs:
        for path in (train_root / dirname).glob("*"):
            if not path.is_file():
                continue
            is_mask = "mask" in dirname
            mode = "L" if is_mask else "RGB"
            resample = Image.Resampling.NEAREST if is_mask else Image.Resampling.BILINEAR
            with Image.open(path) as image:
                image = image.convert(mode).resize((width, height), resample)
                image.save(path)


def set_child_module(root: nn.Module, module_name: str, new_module: nn.Module) -> None:
    parts = module_name.split(".")
    parent: nn.Module = root
    for part in parts[:-1]:
        parent = getattr(parent, part)
    setattr(parent, parts[-1], new_module)


def lora_candidate_score(name: str) -> tuple[int, str]:
    score = 0
    if "model.diffusion_model" in name:
        score -= 1000
    if "control_model" in name:
        score -= 500
    target_keywords = ["to_q", "to_k", "to_v", "to_out", "proj_in", "proj_out"]
    for index, keyword in enumerate(target_keywords):
        if keyword in name:
            score -= 100 - index
    if "attn" in name:
        score -= 20
    if "transformer" in name:
        score -= 10
    return score, name


def insert_lora_modules(
    model: nn.Module,
    rank: int,
    alpha: float,
    dropout: float,
    max_modules: int,
) -> list[str]:
    candidates: list[str] = []
    for name, module in model.named_modules():
        if not isinstance(module, nn.Linear):
            continue
        lowered = name.lower()
        if any(
            keyword in lowered
            for keyword in [
                "to_q",
                "to_k",
                "to_v",
                "to_out",
                "proj_in",
                "proj_out",
                "attn",
                "transformer",
            ]
        ):
            candidates.append(name)

    if not candidates:
        candidates = [name for name, module in model.named_modules() if isinstance(module, nn.Linear)]

    selected = sorted(candidates, key=lora_candidate_score)[:max_modules]
    module_map = dict(model.named_modules())
    for name in selected:
        base = module_map[name]
        if not isinstance(base, nn.Linear):
            continue
        set_child_module(model, name, LoRALinear(base, rank=rank, alpha=alpha, dropout=dropout))
    return selected


def collect_lora_state_dict(model: nn.Module) -> dict[str, torch.Tensor]:
    return {
        name: param.detach().cpu()
        for name, param in model.named_parameters()
        if ".lora_down." in name or ".lora_up." in name
    }


def load_lora_adapter(
    model: nn.Module,
    adapter_path: Path,
) -> tuple[bool, int, list[str], list[str], list[str]]:
    payload = torch.load(adapter_path, map_location="cpu")
    raw_state_dict = payload.get("state_dict", payload) if isinstance(payload, dict) else payload
    if not isinstance(raw_state_dict, dict):
        raise TypeError(f"LoRA adapter state_dict must be a dict: {adapter_path}")

    lora_params = {
        name: param
        for name, param in model.named_parameters()
        if ".lora_down." in name or ".lora_up." in name
    }
    expected_keys = set(lora_params)
    loaded_keys = set(raw_state_dict)
    missing_keys = sorted(expected_keys - loaded_keys)
    unexpected_keys = sorted(loaded_keys - expected_keys)
    shape_mismatch_keys: list[str] = []
    loaded_count = 0

    with torch.no_grad():
        for key in sorted(expected_keys & loaded_keys):
            value = raw_state_dict[key]
            if not torch.is_tensor(value):
                unexpected_keys.append(key)
                continue
            target = lora_params[key]
            if tuple(target.shape) != tuple(value.shape):
                shape_mismatch_keys.append(key)
                continue
            target.copy_(value.to(device=target.device, dtype=target.dtype))
            loaded_count += 1

    load_success = not missing_keys and not unexpected_keys and not shape_mismatch_keys
    return load_success, loaded_count, missing_keys, sorted(set(unexpected_keys)), shape_mismatch_keys


def main() -> int:
    args = parse_args()
    stableviton_root = Path(args.stableviton_root)
    data_root = Path(args.data_root)
    output_root = Path(args.output_root)
    save_lora_path = Path(args.save_lora_path) if args.save_lora_path else None
    load_lora_path = Path(args.load_lora_path) if args.load_lora_path else None
    logs_root = output_root / "logs"
    output_root.mkdir(parents=True, exist_ok=True)
    logs_root.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "task": "stableviton_lora_tiny10_1step_smoke",
        "stableviton_root": str(stableviton_root),
        "data_root": str(data_root),
        "output_root": str(output_root),
        "max_steps": args.max_steps,
        "rank": args.rank,
        "alpha": args.alpha,
        "dropout": args.dropout,
        "max_lora_modules": args.max_lora_modules,
        "skip_vae_load": args.skip_vae_load,
        "prepare_smoke_data": args.prepare_smoke_data,
        "enable_input_grad_for_checkpoint": args.enable_input_grad_for_checkpoint,
        "disable_gradient_checkpointing": args.disable_gradient_checkpointing,
        "save_lora_path": str(save_lora_path) if save_lora_path else None,
        "load_lora_path": str(load_lora_path) if load_lora_path else None,
        "lora_adapter_saved": False,
        "lora_adapter_loaded": False,
        "lora_state_dict_key_count": 0,
        "lora_adapter_file_size_mb": None,
        "load_missing_keys": [],
        "load_unexpected_keys": [],
        "load_shape_mismatch_keys": [],
    }
    summary_path = output_root / "lora_tiny_smoke_summary.json"

    started = time.perf_counter()
    try:
        if not stableviton_root.exists():
            raise FileNotFoundError(f"StableVITON root not found: {stableviton_root}")
        if not data_root.exists():
            raise FileNotFoundError(f"data root not found: {data_root}")

        if args.prepare_smoke_data:
            ensure_smoke_dataset_shape(data_root, width=args.img_width, height=args.img_height)

        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
        sys.path.insert(0, str(stableviton_root))
        os.chdir(stableviton_root)

        import train  # noqa: WPS433

        sys.argv = [
            "train.py",
            "--config_name",
            args.config_name,
            "--data_root_dir",
            str(data_root),
            "--batch_size",
            str(args.batch_size),
            "--max_epochs",
            "1",
            "--save_root_dir",
            str(output_root),
            "--save_name",
            "lora_tiny10_1step_smoke",
            "--logger_freq",
            "999999",
            "--precision",
            "32",
            "--num_sanity_val_steps",
            "0",
            "--use_validation",
            "--learning_rate",
            str(args.learning_rate),
        ]
        train_args = train.build_args()
        if args.skip_vae_load:
            train_args.vae_load_path = None

        config = train.build_config(train_args)
        if args.disable_gradient_checkpointing:
            config.model.params.unet_config.params.use_checkpoint = False
            config.model.params.control_stage_config.params.use_checkpoint = False
        train.OmegaConf.save(config, train_args.config_save_path)
        train.save_args(train_args, train_args.args_save_path)

        model = train.create_model(train_args.config_path, config=config).cpu()
        load_path = train_args.resume_path if train_args.resume_path is not None else config.resume_path
        if load_path is not None:
            model.load_state_dict(train.load_state_dict(load_path, location="cpu"), strict=not train_args.no_strict_load)
            summary["checkpoint_loaded"] = str(load_path)
        else:
            summary["checkpoint_loaded"] = None

        model.learning_rate = train_args.learning_rate
        model.sd_locked = train_args.sd_locked
        model.only_mid_control = train_args.only_mid_control

        total_params = count_params(model)
        trainable_before = count_params(model, trainable_only=True)
        for param in model.parameters():
            param.requires_grad = False
        trainable_after_freeze = count_params(model, trainable_only=True)

        inserted_names = insert_lora_modules(
            model,
            rank=args.rank,
            alpha=args.alpha,
            dropout=args.dropout,
            max_modules=args.max_lora_modules,
        )
        lora_state_dict = collect_lora_state_dict(model)
        trainable_after_lora = count_params(model, trainable_only=True)

        if load_lora_path is not None:
            if not load_lora_path.exists():
                raise FileNotFoundError(f"LoRA adapter not found: {load_lora_path}")
            load_success, loaded_count, missing_keys, unexpected_keys, shape_mismatch_keys = load_lora_adapter(
                model,
                load_lora_path,
            )
            summary.update(
                {
                    "lora_adapter_loaded": load_success,
                    "lora_adapter_loaded_key_count": loaded_count,
                    "lora_adapter_file_size_mb": round(load_lora_path.stat().st_size / 1024**2, 4),
                    "load_missing_keys": missing_keys,
                    "load_unexpected_keys": unexpected_keys,
                    "load_shape_mismatch_keys": shape_mismatch_keys,
                }
            )

        trainable_param_names = [
            name
            for name, param in model.named_parameters()
            if param.requires_grad
        ]

        summary.update(
            {
                "total_params": total_params,
                "trainable_params_before_lora": trainable_before,
                "trainable_params_after_freeze": trainable_after_freeze,
                "trainable_params_after_lora": trainable_after_lora,
                "trainable_ratio": trainable_after_lora / total_params if total_params else 0,
                "inserted_lora_module_count": len(inserted_names),
                "inserted_lora_module_names": inserted_names,
                "lora_state_dict_key_count": len(lora_state_dict),
                "trainable_param_name_sample": trainable_param_names[:32],
            }
        )

        def configure_lora_optimizers(self: Any) -> torch.optim.Optimizer:
            params = [param for param in self.parameters() if param.requires_grad]
            print(f"LoRA smoke optimizer trainable tensors={len(params)} params={sum(param.numel() for param in params)}")
            return torch.optim.AdamW(params, lr=self.learning_rate)

        model.configure_optimizers = MethodType(configure_lora_optimizers, model)

        if args.enable_input_grad_for_checkpoint:
            original_apply_model = model.apply_model

            def apply_model_with_input_grad(self: Any, x_noisy: torch.Tensor, t: torch.Tensor, cond: Any, *a: Any, **kw: Any) -> Any:
                del self
                if torch.is_tensor(x_noisy) and not x_noisy.requires_grad:
                    x_noisy = x_noisy.detach().requires_grad_(True)
                return original_apply_model(x_noisy, t, cond, *a, **kw)

            model.apply_model = MethodType(apply_model_with_input_grad, model)

        dataset_cls = getattr(train.import_module("dataset"), config.dataset_name)
        train_dataset = dataset_cls(
            data_root_dir=str(data_root),
            img_H=args.img_height,
            img_W=args.img_width,
            transform_size=None,
            transform_color=None,
        )
        summary["train_dataset_len"] = len(train_dataset)
        train_dataloader = DataLoader(
            train_dataset,
            num_workers=0,
            batch_size=args.batch_size,
            shuffle=False,
            pin_memory=True,
        )

        metrics = StepMetricsCallback()
        tb_logger = train.TensorBoardLogger(train_args.tb_save_dir)

        cuda_available = torch.cuda.is_available()
        summary["cuda_available"] = cuda_available
        summary["device_name"] = torch.cuda.get_device_name(0) if cuda_available else None
        if cuda_available:
            torch.cuda.reset_peak_memory_stats()

        trainer = train.pl.Trainer(
            precision=train_args.precision,
            callbacks=[metrics],
            logger=tb_logger,
            devices=train_args.devices,
            accelerator="gpu" if cuda_available else "cpu",
            max_epochs=1,
            max_steps=args.max_steps,
            accumulate_grad_batches=train_args.accum_iter,
            num_sanity_val_steps=0,
            enable_checkpointing=False,
            log_every_n_steps=1,
            limit_train_batches=args.max_steps,
            enable_progress_bar=True,
        )
        trainer.fit(model, train_dataloader)

        elapsed = time.perf_counter() - started
        peak_vram_mb = None
        if cuda_available:
            peak_vram_mb = round(torch.cuda.max_memory_allocated() / 1024**2, 2)
        first_loss = metrics.losses[0] if metrics.losses else None
        final_loss = metrics.losses[-1] if metrics.losses else None
        loss_nan = any(value != value for value in metrics.losses)
        if save_lora_path is not None:
            save_lora_path.parent.mkdir(parents=True, exist_ok=True)
            lora_state_dict = collect_lora_state_dict(model)
            torch.save(
                {
                    "rank": args.rank,
                    "alpha": args.alpha,
                    "dropout": args.dropout,
                    "max_lora_modules": args.max_lora_modules,
                    "inserted_lora_module_names": inserted_names,
                    "state_dict": lora_state_dict,
                },
                save_lora_path,
            )
            summary.update(
                {
                    "lora_adapter_saved": True,
                    "lora_state_dict_key_count": len(lora_state_dict),
                    "lora_adapter_file_size_mb": round(save_lora_path.stat().st_size / 1024**2, 4),
                }
            )
        summary.update(
            {
                "status": "success",
                "steps_completed": trainer.global_step,
                "callback_steps_seen": metrics.steps_seen,
                "first_loss": first_loss,
                "final_loss": final_loss,
                "loss_nan": loss_nan,
                "elapsed_sec": round(elapsed, 4),
                "avg_step_time_sec": round(elapsed / max(trainer.global_step, 1), 4),
                "peak_vram_mb": peak_vram_mb,
                "checkpoint_created": False,
                "sample_created": False,
                "error": None,
            }
        )
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        elapsed = time.perf_counter() - started
        summary.update(
            {
                "status": "failed",
                "elapsed_sec": round(elapsed, 4),
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
            }
        )
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 1
    finally:
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
