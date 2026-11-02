#!/bin/bash
# Run once on a fresh RunPod pod (PyTorch template, 48 GB card such as an A40 or RTX A6000, 150 GB disk):
#   bash setup.sh            trainer + the three model files (about 58 GB)
#   bash setup.sh blender    also installs Blender, for the Blender pairs
set -e
W=${WORKSPACE:-/workspace}
cd $W
if [ ! -d musubi-tuner ]; then
  git clone https://github.com/kohya-ss/musubi-tuner
  git -C musubi-tuner checkout f8a1b03794a49239a3539015075f5123d6c07d66   # the version this tutorial was tested with
fi
pip install -q -e musubi-tuner "huggingface_hub[hf_transfer]" pillow pytest
export HF_HUB_ENABLE_HF_TRANSFER=1
python - <<'PY'
import os
from huggingface_hub import hf_hub_download
m = os.environ.get('WORKSPACE', '/workspace') + '/models'
for repo, f in [('Comfy-Org/Qwen-Image-Edit_ComfyUI', 'split_files/diffusion_models/qwen_image_edit_2511_bf16.safetensors'),
                ('Comfy-Org/Qwen-Image_ComfyUI', 'split_files/vae/qwen_image_vae.safetensors'),
                ('Comfy-Org/Qwen-Image_ComfyUI', 'split_files/text_encoders/qwen_2.5_vl_7b.safetensors')]:
    p = hf_hub_download(repo, f, local_dir=m)
    print('got', p, round(os.path.getsize(p) / 1e9, 1), 'GB')
PY
if [ "$1" = blender ] && [ ! -d $W/blender ]; then
  apt-get update -qq && apt-get install -y -qq libxrender1 libxi6 libxkbcommon0 libsm6 libgl1 libegl1 libxxf86vm1 libxfixes3 >/dev/null
  curl -sL https://download.blender.org/release/Blender4.2/blender-4.2.9-linux-x64.tar.xz | tar xJ -C $W
  mv $W/blender-4.2.9-linux-x64 $W/blender
  $W/blender/blender --version | head -1
fi
echo "setup done"
