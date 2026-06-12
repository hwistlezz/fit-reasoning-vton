"""Run StableVITON baseline and saved-LoRA inference on the same pairs.

This helper imports the external StableVITON checkout without modifying it.
Generated images and summaries should be written under ignored output paths.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from importlib import import_module
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from omegaconf import OmegaConf
from PIL import Image, ImageOps
from torch.utils.data import DataLoader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stableviton-root", default=r"D:\GitHub\StableVITON")
    parser.add_argument(
        "--data-root",
        default=r"D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_tiny10",
    )
    parser.add_argument(
        "--output-root",
        default=r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_saved_lora_inference_comparison",
    )
    parser.add_argument("--config-path", default=None)
    parser.add_argument("--model-load-path", default=None)
    parser.add_argument(
        "--lora-adapter-path",
        default=r"D:\GitHub\fit-reasoning-vton\backend\training\outputs\stableviton_lora_10k_adapter_save\lora_adapter.pt",
    )
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--denoise-steps", type=int, default=50)
    parser.add_argument("--img-height", type=int, default=512)
    parser.add_argument("--img-width", type=int, default=384)
    parser.add_argument("--eta", type=float, default=0.0)
    parser.add_argument("--rank", type=int, default=4)
    parser.add_argument("--alpha", type=float, default=4.0)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--max-lora-modules", type=int, default=8)
    parser.add_argument("--strict-checkpoint-load", action="store_true")
    parser.add_argument("--repaint", action="store_true")
    parser.add_argument("--unpair", action="store_true")
    parser.add_argument("--prepare-inference-data", dest="prepare_inference_data", action="store_true", default=True)
    parser.add_argument("--no-prepare-inference-data", dest="prepare_inference_data", action="store_false")
    parser.add_argument("--skip-baseline", action="store_true")
    parser.add_argument("--skip-lora", action="store_true")
    return parser.parse_args()


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def setup_paths(stableviton_root: Path) -> None:
    repo_root = repo_root_from_script()
    for path in (str(repo_root), str(stableviton_root)):
        if path not in sys.path:
            sys.path.insert(0, path)
    os.chdir(stableviton_root)


def read_pair_file(path: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        person_name, cloth_name = stripped.split()
        pairs.append((person_name, cloth_name))
    return pairs


def resize_copy_image(src: Path, dst: Path, width: int, height: int, is_mask: bool) -> None:
    if not src.exists():
        raise FileNotFoundError(f"required inference artifact not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    mode = "L" if is_mask else "RGB"
    resample = Image.Resampling.NEAREST if is_mask else Image.Resampling.BILINEAR
    with Image.open(src) as image:
        image = ImageOps.exif_transpose(image)
        image = image.convert(mode).resize((width, height), resample)
        image.save(dst)


def prepare_inference_layout(source_root: Path, prepared_root: Path, width: int, height: int) -> Path:
    pairs = read_pair_file(source_root / "test_pairs.txt")
    if not pairs:
        raise ValueError(f"test_pairs.txt has no pairs: {source_root / 'test_pairs.txt'}")

    prepared_root.mkdir(parents=True, exist_ok=True)
    (prepared_root / "train_pairs.txt").write_text("", encoding="utf-8")
    (prepared_root / "test_pairs.txt").write_text(
        "".join(f"{person_name} {cloth_name}\n" for person_name, cloth_name in pairs),
        encoding="utf-8",
    )

    for person_name, cloth_name in pairs:
        artifacts = [
            ("image", person_name, False),
            ("cloth", cloth_name, False),
            ("agnostic-v3.2", person_name, False),
            ("agnostic-mask", person_name.replace(".jpg", "_mask.png"), True),
            ("cloth-mask", cloth_name, True),
            ("image-densepose", person_name, False),
        ]
        for dirname, filename, is_mask in artifacts:
            resize_copy_image(
                source_root / "test" / dirname / filename,
                prepared_root / "test" / dirname / filename,
                width=width,
                height=height,
                is_mask=is_mask,
            )
    return prepared_root


def tensor2img_local(tensor: torch.Tensor) -> np.ndarray:
    from utils import tensor2img  # noqa: WPS433

    return tensor2img(tensor)


def load_model(
    *,
    config_path: Path,
    model_load_path: Path,
    img_height: int,
    img_width: int,
    lora_adapter_path: Path | None,
    rank: int,
    alpha: float,
    dropout: float,
    max_lora_modules: int,
    strict_checkpoint_load: bool,
) -> tuple[Any, dict[str, Any]]:
    from cldm.model import create_model  # noqa: WPS433
    from backend.training.scripts.run_stableviton_lora_tiny_smoke import (  # noqa: WPS433
        insert_lora_modules,
        load_lora_adapter,
    )

    config = OmegaConf.load(config_path)
    config.model.params.img_H = img_height
    config.model.params.img_W = img_width
    params = config.model.params

    model = create_model(config_path=None, config=config)
    checkpoint = torch.load(model_load_path, map_location="cpu")
    checkpoint = checkpoint["state_dict"] if "state_dict" in checkpoint.keys() else checkpoint
    checkpoint_load_info = model.load_state_dict(checkpoint, strict=strict_checkpoint_load)

    lora_info: dict[str, Any] = {
        "lora_adapter_path": str(lora_adapter_path) if lora_adapter_path else None,
        "lora_adapter_loaded": False,
        "lora_adapter_loaded_key_count": 0,
        "load_missing_keys": [],
        "load_unexpected_keys": [],
        "load_shape_mismatch_keys": [],
        "inserted_lora_module_count": 0,
        "inserted_lora_module_names": [],
        "checkpoint_strict_load": strict_checkpoint_load,
        "checkpoint_missing_keys": list(getattr(checkpoint_load_info, "missing_keys", [])),
        "checkpoint_unexpected_keys": list(getattr(checkpoint_load_info, "unexpected_keys", [])),
    }
    if lora_adapter_path is not None:
        inserted_names = insert_lora_modules(
            model,
            rank=rank,
            alpha=alpha,
            dropout=dropout,
            max_modules=max_lora_modules,
        )
        load_success, loaded_count, missing_keys, unexpected_keys, shape_mismatch_keys = load_lora_adapter(
            model,
            lora_adapter_path,
        )
        lora_info.update(
            {
                "lora_adapter_loaded": load_success,
                "lora_adapter_loaded_key_count": loaded_count,
                "load_missing_keys": missing_keys,
                "load_unexpected_keys": unexpected_keys,
                "load_shape_mismatch_keys": shape_mismatch_keys,
                "inserted_lora_module_count": len(inserted_names),
                "inserted_lora_module_names": inserted_names,
                "lora_adapter_file_size_mb": round(lora_adapter_path.stat().st_size / 1024**2, 4),
            }
        )

    model = model.cuda()
    model.eval()
    return model, {"config": config, "params": params, "lora": lora_info}


@torch.no_grad()
def run_inference(
    *,
    run_name: str,
    stableviton_root: Path,
    config_path: Path,
    model_load_path: Path,
    data_root: Path,
    save_dir: Path,
    lora_adapter_path: Path | None,
    args: argparse.Namespace,
) -> dict[str, Any]:
    del stableviton_root
    from cldm.plms_hacked import PLMSSampler  # noqa: WPS433

    started = time.perf_counter()
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    model, model_info = load_model(
        config_path=config_path,
        model_load_path=model_load_path,
        img_height=args.img_height,
        img_width=args.img_width,
        lora_adapter_path=lora_adapter_path,
        rank=args.rank,
        alpha=args.alpha,
        dropout=args.dropout,
        max_lora_modules=args.max_lora_modules,
        strict_checkpoint_load=args.strict_checkpoint_load,
    )
    config = model_info["config"]
    params = model_info["params"]
    sampler = PLMSSampler(model)

    dataset = getattr(import_module("dataset"), config.dataset_name)(
        data_root_dir=str(data_root),
        img_H=args.img_height,
        img_W=args.img_width,
        is_paired=not args.unpair,
        is_test=True,
        is_sorted=True,
    )
    dataloader = DataLoader(
        dataset,
        num_workers=0,
        shuffle=False,
        batch_size=args.batch_size,
        pin_memory=True,
    )

    shape = (4, args.img_height // 8, args.img_width // 8)
    pair_dir = save_dir / ("unpair" if args.unpair else "pair")
    pair_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[str] = []
    pair_ids: list[str] = []

    for batch_idx, batch in enumerate(dataloader):
        print(f"{run_name}: {batch_idx}/{len(dataloader)}")
        z, c = model.get_input(batch, params.first_stage_key)
        bs = z.shape[0]
        c_crossattn = c["c_crossattn"][0][:bs]
        if c_crossattn.ndim == 4:
            c_crossattn = model.get_learned_conditioning(c_crossattn)
            c["c_crossattn"] = [c_crossattn]
        uc_cross = model.get_unconditional_conditioning(bs)
        uc_full = {"c_concat": c["c_concat"], "c_crossattn": [uc_cross]}
        uc_full["first_stage_cond"] = c["first_stage_cond"]
        for key, value in batch.items():
            if isinstance(value, torch.Tensor):
                batch[key] = value.cuda()
        sampler.model.batch = batch

        ts = torch.full((1,), 999, device=z.device, dtype=torch.long)
        start_code = model.q_sample(z, ts)
        samples, _, _ = sampler.sample(
            args.denoise_steps,
            bs,
            shape,
            c,
            x_T=start_code,
            verbose=False,
            eta=args.eta,
            unconditional_conditioning=uc_full,
        )

        x_samples = model.decode_first_stage(samples)
        for sample_idx, (x_sample, img_fn, cloth_fn) in enumerate(
            zip(x_samples, batch["img_fn"], batch["cloth_fn"]),
        ):
            x_sample_img = tensor2img_local(x_sample)
            if args.repaint:
                repaint_agn_img = np.uint8((batch["image"][sample_idx].cpu().numpy() + 1) / 2 * 255)
                repaint_agn_mask_img = batch["agn_mask"][sample_idx].cpu().numpy()
                x_sample_img = repaint_agn_img * repaint_agn_mask_img + x_sample_img * (1 - repaint_agn_mask_img)
                x_sample_img = np.uint8(x_sample_img)

            output_path = pair_dir / f"{img_fn.split('.')[0]}_{cloth_fn.split('.')[0]}.jpg"
            cv2.imwrite(str(output_path), x_sample_img[:, :, ::-1])
            output_paths.append(str(output_path))
            pair_ids.append(img_fn.split(".")[0])

    elapsed = time.perf_counter() - started
    peak_vram_mb = None
    if torch.cuda.is_available():
        peak_vram_mb = round(torch.cuda.max_memory_allocated() / 1024**2, 2)
    return {
        "run_name": run_name,
        "status": "success",
        "dataset_len": len(dataset),
        "batch_size": args.batch_size,
        "denoise_steps": args.denoise_steps,
        "pair_ids": pair_ids,
        "output_paths": output_paths,
        "output_count": len(output_paths),
        "elapsed_sec": round(elapsed, 4),
        "peak_vram_mb": peak_vram_mb,
        **model_info["lora"],
    }


def main() -> int:
    args = parse_args()
    stableviton_root = Path(args.stableviton_root)
    data_root = Path(args.data_root)
    output_root = Path(args.output_root)
    config_path = Path(args.config_path) if args.config_path else stableviton_root / "configs" / "VITONHD.yaml"
    model_load_path = Path(args.model_load_path) if args.model_load_path else stableviton_root / "ckpts" / "VITONHD_PBE_pose.ckpt"
    lora_adapter_path = Path(args.lora_adapter_path)
    summary_path = output_root / "saved_lora_inference_comparison_summary.json"
    output_root.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "task": "saved_lora_inference_comparison",
        "stableviton_root": str(stableviton_root),
        "data_root": str(data_root),
        "effective_data_root": None,
        "prepare_inference_data": args.prepare_inference_data,
        "output_root": str(output_root),
        "config_path": str(config_path),
        "model_load_path": str(model_load_path),
        "lora_adapter_path": str(lora_adapter_path),
        "baseline": None,
        "lora": None,
        "error": None,
    }
    try:
        for required in (stableviton_root, data_root, config_path, model_load_path):
            if not required.exists():
                raise FileNotFoundError(f"required path not found: {required}")
        if not args.skip_lora and not lora_adapter_path.exists():
            raise FileNotFoundError(f"LoRA adapter not found: {lora_adapter_path}")
        if args.prepare_inference_data:
            data_root = prepare_inference_layout(
                data_root,
                output_root / "prepared_inference_data",
                width=args.img_width,
                height=args.img_height,
            )
        summary["effective_data_root"] = str(data_root)
        setup_paths(stableviton_root)

        if not args.skip_baseline:
            summary["baseline"] = run_inference(
                run_name="baseline",
                stableviton_root=stableviton_root,
                config_path=config_path,
                model_load_path=model_load_path,
                data_root=data_root,
                save_dir=output_root / "baseline",
                lora_adapter_path=None,
                args=args,
            )

        if not args.skip_lora:
            summary["lora"] = run_inference(
                run_name="lora",
                stableviton_root=stableviton_root,
                config_path=config_path,
                model_load_path=model_load_path,
                data_root=data_root,
                save_dir=output_root / "lora",
                lora_adapter_path=lora_adapter_path,
                args=args,
            )

        summary["status"] = "success"
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:
        summary["status"] = "failed"
        summary["error"] = f"{type(exc).__name__}: {exc}"
        summary["traceback"] = traceback.format_exc()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 1
    finally:
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
