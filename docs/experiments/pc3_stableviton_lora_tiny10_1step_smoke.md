# PC3 StableVITON LoRA tiny10 1-step smoke

## 1. 목적

이번 작업은 StableVITON 전체 모델을 학습하는 것이 아니라, StableVITON 내부 일부 `nn.Linear` module에 lightweight LoRA adapter를 삽입하고 LoRA parameter만 trainable 상태로 1-step 학습이 가능한지 확인하는 smoke test다.

이번 작업은 성능 개선 실험이 아니다. 1 epoch 학습, 10-step, 100-step, 10k 전체 학습은 수행하지 않았다.

## 2. PR #103과의 차이

PR #103에서는 외부 StableVITON repo의 `train.py` compatibility smoke를 수행했다.

확인된 내용:

```text
StableVITON checkpoint load 성공
tiny10 dataset root 인식
train loop 진입
first train step 완료
loss=0.435
loss_nan=false
```

이번 #104 작업은 그 위에 LoRA adapter를 실제로 삽입하고, full model parameter를 freeze한 뒤 LoRA parameter만 optimizer 대상이 되는지 확인했다.

## 3. 경로

우리 repo:

```text
D:\GitHub\fit-reasoning-vton
```

외부 StableVITON repo:

```text
D:\GitHub\StableVITON
```

사용 dataset:

```text
D:\GitHub\fit-reasoning-vton\backend\datasets\stableviton_aihub_10k_layout_tiny10
```

output root:

```text
backend/training/outputs/stableviton_lora_tiny10_1step_smoke
```

output root는 Git에 포함하지 않는다.

## 4. tiny10 dataset 확인

tiny10 dataset은 존재했고 train/test pair file을 읽을 수 있었다.

```text
train_pairs.txt count=9
test_pairs.txt count=1
```

train pair:

```text
EP00000000.jpg EP00000000.jpg
EP00000001.jpg EP00000001.jpg
EP00000002.jpg EP00000002.jpg
EP00000004.jpg EP00000004.jpg
EP00000006.jpg EP00000006.jpg
EP00000009.jpg EP00000009.jpg
EP00000010.jpg EP00000010.jpg
EP00000012.jpg EP00000012.jpg
EP00000013.jpg EP00000013.jpg
```

StableVITON train path에서 필요한 `train/gt_cloth_warped_mask`는 #103 smoke 과정에서 `train/cloth-mask` 기반 smoke-only mask로 준비된 상태였다.

## 5. runner 구현

추가한 script:

```text
backend/training/scripts/run_stableviton_lora_tiny_smoke.py
```

역할:

- 외부 StableVITON repo를 import만 하고 직접 수정하지 않는다.
- `LoRALinear` wrapper로 `nn.Linear`를 감싼다.
- base Linear weight/bias는 freeze한다.
- `lora_down`, `lora_up`만 trainable로 둔다.
- full StableVITON model parameter를 freeze한다.
- LoRA parameter만 optimizer에 전달한다.
- ImageLogger와 checkpoint 저장은 사용하지 않는다.
- `max_steps=1`로 제한한다.
- summary JSON은 ignored output에 저장한다.

이번 runner는 PR #103에서 확인한 smoke-only compatibility 조정도 포함한다.

```text
skip_vae_load=true
prepare_smoke_data=true
enable_input_grad_for_checkpoint=true
disable_gradient_checkpointing=true
```

`VITONHD_VAE_finetuning.ckpt`는 PR #103에서 zip archive 문제를 보였으므로 이번 smoke에서도 추가 VAE load는 생략했다. StableVITON base checkpoint인 `VITONHD_PBE_pose.ckpt`는 정상 로드됐다.

## 6. LoRA 삽입 방식

LoRA 설정:

```text
rank=4
alpha=4.0
dropout=0.0
max_lora_modules=8
```

대상 module 선택 규칙:

- `nn.Linear` module 중 attention/transformer 계열 이름을 우선 탐색
- `model.diffusion_model` 경로를 우선
- `to_q`, `to_k`, `to_v`, `to_out`, `proj_in`, `proj_out`, `attn`, `transformer` 키워드 사용
- 최대 8개 module만 LoRA로 교체

삽입된 LoRA module:

```text
model.diffusion_model.input_blocks.1.1.transformer_blocks.0.attn1.to_q
model.diffusion_model.input_blocks.1.1.transformer_blocks.0.attn2.to_q
model.diffusion_model.input_blocks.2.1.transformer_blocks.0.attn1.to_q
model.diffusion_model.input_blocks.2.1.transformer_blocks.0.attn2.to_q
model.diffusion_model.input_blocks.4.1.transformer_blocks.0.attn1.to_q
model.diffusion_model.input_blocks.4.1.transformer_blocks.0.attn2.to_q
model.diffusion_model.input_blocks.5.1.transformer_blocks.0.attn1.to_q
model.diffusion_model.input_blocks.5.1.transformer_blocks.0.attn2.to_q
```

## 7. parameter 상태

summary path:

```text
backend/training/outputs/stableviton_lora_tiny10_1step_smoke/lora_tiny_smoke_summary.json
```

parameter summary:

```text
total_params=1838680959
trainable_params_before_lora=1451847320
trainable_params_after_freeze=0
trainable_params_after_lora=30720
trainable_ratio=0.000016707629373998428
inserted_lora_module_count=8
```

trainable parameter sample:

```text
model.diffusion_model.input_blocks.1.1.transformer_blocks.0.attn1.to_q.lora_down.weight
model.diffusion_model.input_blocks.1.1.transformer_blocks.0.attn1.to_q.lora_up.weight
model.diffusion_model.input_blocks.1.1.transformer_blocks.0.attn2.to_q.lora_down.weight
model.diffusion_model.input_blocks.1.1.transformer_blocks.0.attn2.to_q.lora_up.weight
...
```

성공 기준:

```text
inserted_lora_module_count > 0
trainable_params_after_lora > 0
trainable_params_after_lora << total_params
trainable module이 lora_down/lora_up 계열
```

위 조건을 만족했다.

## 8. 실행 명령

```powershell
D:\conda-envs\vton\python.exe backend\training\scripts\run_stableviton_lora_tiny_smoke.py
```

stdout log:

```text
backend/training/outputs/stableviton_lora_tiny10_1step_smoke/logs/run_stdout_retry3_no_checkpoint.txt
```

## 9. 1-step 실행 결과

핵심 결과:

```text
status=success
checkpoint_loaded=./ckpts/VITONHD_PBE_pose.ckpt
train_dataset_len=9
cuda_available=true
device_name=NVIDIA GeForce RTX 4080
steps_completed=1
callback_steps_seen=1
first_loss=0.7227942943572998
final_loss=0.7227942943572998
loss_nan=false
elapsed_sec=14.2541
avg_step_time_sec=14.2541
peak_vram_mb=8887.85
checkpoint_created=false
sample_created=false
error=null
```

stdout 근거:

```text
LoRA smoke optimizer trainable tensors=16 params=30720
GPU available: True, used: True
LOCAL_RANK: 0 - CUDA_VISIBLE_DEVICES: [0]
Epoch 0: 100%|##########| 1/1 [00:01<00:00, 1.80s/it, loss=0.723, v_num=2, train_loss_step=0.723, global_step=0.000]
```

PowerShell에서는 stderr warning 때문에 command wrapper가 non-zero처럼 표시됐지만, runner가 저장한 summary JSON의 최종 상태는 `status=success`였다.

## 10. 중간 실패와 조정

첫 시도:

```text
LoRA 삽입과 parameter freeze는 성공
Trainer callback이 Lightning Callback을 상속하지 않아 초기화 실패
```

수정:

```text
StepMetricsCallback이 pytorch_lightning.callbacks.Callback을 상속하도록 수정
```

두 번째 시도:

```text
RuntimeError: element 0 of tensors does not require grad and does not have a grad_fn
```

원인 후보:

```text
StableVITON diffusion/control block의 gradient checkpointing과 frozen base parameter 조합에서 autograd path가 끊김
```

수정:

```text
runner 내부 config copy에서 unet/control use_checkpoint=False
apply_model 진입 시 x_noisy.requires_grad_(True)
```

세 번째 시도:

```text
1-step 성공
loss_nan=false
LoRA parameter만 trainable
```

## 11. checkpoint / sample 생성 여부

이번 smoke는 checkpoint와 sample 생성을 의도적으로 비활성화했다.

```text
checkpoint_created=false
sample_created=false
```

이유:

- 이번 목표는 LoRA adapter 삽입 가능성과 1-step backward/optimizer step 검증이다.
- full checkpoint는 매우 크고 이번 smoke 목적에 필요하지 않다.
- ImageLogger가 DDIM sampling을 실행하면 step time이 크게 늘어나는 문제가 PR #103에서 확인됐다.

## 12. 현재 한계

- 이번 작업은 성능 개선 실험이 아니다.
- 1-step만 수행했으므로 수렴, 품질, generalization을 판단할 수 없다.
- LoRA target은 UNet attention `to_q` 일부 8개 module에 제한했다.
- ControlNet LoRA, `to_k/to_v/to_out`, 더 넓은 attention layer 적용은 아직 검증하지 않았다.
- gradient checkpointing은 smoke runner에서 껐다. 장시간 학습에서는 메모리/속도 tradeoff를 다시 검토해야 한다.
- VAE finetuning checkpoint load는 생략했다. 해당 checkpoint 무결성 문제는 별도 확인이 필요하다.

## 13. Git safety

Git에 포함할 파일:

```text
backend/training/scripts/run_stableviton_lora_tiny_smoke.py
docs/experiments/pc3_stableviton_lora_tiny10_1step_smoke.md
```

Git에 포함하지 않을 파일:

```text
backend/datasets/**
backend/training/outputs/**
backend/outputs/**
backend/logs/**
*.jpg
*.jpeg
*.png
*.webp
*.pt
*.pth
*.ckpt
*.safetensors
*.zip
*.7z
*.part*
```

이번 작업에서 생성된 summary JSON, stdout log, TensorBoard log, tiny10 smoke data normalization 결과는 모두 ignored output/dataset 경로에만 둔다.

## 14. 다음 단계

- LoRA target을 `to_k`, `to_v`, `to_out`까지 확장한 1-step smoke를 비교한다.
- ControlNet attention module LoRA 삽입 가능성을 별도 smoke로 확인한다.
- checkpoint 저장은 LoRA weight만 저장하는 방식으로 구현한다.
- gradient checkpointing을 켠 상태에서 LoRA-only 학습이 가능하도록 checkpoint wrapper 또는 input grad 조건을 정리한다.
- LoRA 10-step smoke는 1-step 결과를 기준으로 별도 작업에서 수행한다.
