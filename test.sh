#!/bin/bash
# Try a trained LoRA (or none) on one picture.
#   bash test.sh <lora.safetensors or none> <input.png> "<caption>" <output.png>
set -e
W=${WORKSPACE:-/workspace}; M=$W/models/split_files
LORA=()
[ "$1" != none ] && LORA=(--lora_weight "$(realpath "$1")" --lora_multiplier 1.0)
IN=$(realpath "$2"); OUT=$(realpath -m "$4")
cd $W/musubi-tuner
python src/musubi_tuner/qwen_image_generate_image.py \
  --dit $M/diffusion_models/qwen_image_edit_2511_bf16.safetensors --vae $M/vae/qwen_image_vae.safetensors \
  --text_encoder $M/text_encoders/qwen_2.5_vl_7b.safetensors --model_version edit-2511 --fp8_scaled \
  --control_image_path "$IN" --resize_control_to_official_size --prompt "$3" \
  --image_size 1024 1024 --infer_steps 25 --guidance_scale 4.0 --seed 7 "${LORA[@]}" --save_path "$(dirname "$OUT")"
NEW=$(ls -t "$(dirname "$OUT")"/*.png | head -1); [ "$NEW" != "$OUT" ] && mv "$NEW" "$OUT"
echo "saved $OUT"
