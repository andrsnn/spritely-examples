# Train your own image model

Scripts from my video "How to Train Your Own AI Image Model". They train a small add-on (a LoRA) for Qwen Image Edit 2511 on your own graphics card or a rented one, from training pairs you make yourself.

A training pair is a picture you give the model, the picture you want back, and one sentence that says what to do. There are two ways to make pairs here:

- **Grow:** cut pairs from pictures you already have. The script keeps one edge of each picture and paints the rest magenta. The model learns to paint the magenta part so it matches the edge.
- **Blender:** render pairs from free 3D characters. Blender draws the same character in the same pose from the front and from 7 other sides. The model learns to turn a character you give it.

## What you need

- A RunPod account. I used an A40 (48 GB) on Community Cloud at about 35 cents an hour, with 150 GB of disk. Pick the PyTorch template.
- For grow: a folder of your own pictures, each at least 1024 pixels on its short side. About 50 to 100 pictures is enough to start.
- For Blender: nothing. The script downloads 9 free CC0 characters by Kay Lousberg.

## Steps

If you'd rather not type the commands, give Claude Code the prompt in [PROMPT.md](PROMPT.md) and it runs these steps for you.

Open a terminal on the pod, then:

```bash
cd /workspace
git clone https://github.com/andrsnn/spritely-examples
cd spritely-examples/train-your-own-image-model
bash setup.sh blender        # the trainer, the model files (about 58 GB) and Blender
```

**Grow pairs.** Upload your pictures to `/workspace/my-pictures` (drag them into the pod's Jupyter file browser), then:

```bash
python make_grow_pairs.py --images /workspace/my-pictures --out /workspace/grow_pairs
bash train.sh /workspace/grow_pairs grow
```

**Blender pairs.**

```bash
bash blender/get_characters.sh
/workspace/blender/blender -b -P blender/render_turn_pairs.py -- --models "characters/*.glb" --out /workspace/turn_pairs --holdout Rogue_Hooded
bash train.sh /workspace/turn_pairs turn
```

`train.sh` saves a version of the model every 200 steps in `/workspace/output/<name>/`, with test pictures in its `sample` folder. Look at those pictures and pick the version you like best. The last one isn't always the best.

**Try it.**

```bash
bash test.sh /workspace/output/grow/grow.safetensors my-test.png "Continue the picture into the magenta area. Keep the same style, lighting and scale, and fill the magenta area with matching art." out.png
bash test.sh none my-test.png "...same sentence..." out-without.png    # the same job without your LoRA, to compare
```

Download the `.safetensors` file to use your LoRA anywhere that runs Qwen Image Edit 2511, then delete the pod so it stops charging.

## Tips from my own models

- Balance your pairs. If every pair has something in common that you didn't mean to teach, the model learns it anyway.
- Write the caption the same way you'll ask for a picture later.
- Save versions while training, and compare their pictures before you choose one.

## Credits

- Trainer: [musubi-tuner](https://github.com/kohya-ss/musubi-tuner) by kohya-ss.
- Model: Qwen Image Edit 2511 (Apache 2.0), files from [Comfy-Org](https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI).
- Characters: [KayKit](https://kaylousberg.itch.io/kaykit-adventurers) by Kay Lousberg. I bought them, and you should too. The script downloads the free (CC0) versions. Thanks, Kay!

MIT licence for the scripts in this repo.
