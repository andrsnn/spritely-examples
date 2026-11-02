#!/bin/bash
# Train a LoRA on Qwen Image Edit 2511 from a pairs folder made by make_grow_pairs.py or the Blender script.
#   bash train.sh <pairs folder> <name> [steps, default 600]
# Saves a version every 200 steps in /workspace/output/<name>/, plus test pictures from sample_prompts.txt.
# On a 24 GB card (RTX 4090), keep part of the model in normal memory instead:
#   TRAIN_EXTRA="--blocks_to_swap 30 --gradient_checkpointing_cpu_offload" bash train.sh ...
set -e
P=$(realpath "$1"); NAME=$2; STEPS=${3:-600}
W=${WORKSPACE:-/workspace}; M=$W/models/split_files
DIT=$M/diffusion_models/qwen_image_edit_2511_bf16.safetensors; VAE=$M/vae/qwen_image_vae.safetensors; TE=$M/text_encoders/qwen_2.5_vl_7b.safetensors
cd $W/musubi-tuner
echo "== 1/3 turning the pictures into the form the trainer reads"
python src/musubi_tuner/qwen_image_cache_latents.py --dataset_config $P/dataset.toml --vae $VAE --model_version edit-2511
echo "== 2/3 turning the captions into the form the trainer reads"
python src/musubi_tuner/qwen_image_cache_text_encoder_outputs.py --dataset_config $P/dataset.toml --text_encoder $TE --batch_size 1 --model_version edit-2511
echo "== 3/3 training $NAME for $STEPS steps"
accelerate launch --num_cpu_threads_per_process 1 --mixed_precision bf16 src/musubi_tuner/qwen_image_train_network.py \
  --dit $DIT --vae $VAE --text_encoder $TE --model_version edit-2511 --dataset_config $P/dataset.toml \
  --sdpa --mixed_precision bf16 --fp8_base --fp8_scaled --gradient_checkpointing \
  --timestep_sampling shift --weighting_scheme none --discrete_flow_shift 2.2 \
  --optimizer_type adamw8bit --learning_rate 1e-4 --network_module networks.lora_qwen_image --network_dim 16 --network_alpha 16 \
  --max_train_steps $STEPS --save_every_n_steps 200 --seed 42 \
  --sample_prompts $P/sample_prompts.txt --sample_every_n_steps 200 --sample_at_first \
  --max_data_loader_n_workers 2 --persistent_data_loader_workers \
  --output_dir $W/output/$NAME --output_name $NAME $TRAIN_EXTRA
echo "done: $(ls $W/output/$NAME/*.safetensors)"
