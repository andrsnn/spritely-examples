# Let Claude Code run the steps

If you'd rather not type the commands yourself, install Claude Code in the pod's terminal (or on your own computer, if it
has the graphics card), start it, sign in, and paste the prompt below.

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude
```

## The prompt

```
Help me train my own LoRA for Qwen Image Edit 2511 with the scripts in
github.com/andrsnn/spritely-examples, in the train-your-own-image-model folder.
Read its README first and follow it.

1. Clone the repo into /workspace and run setup.sh. Add "blender" only if I want character pairs.
2. Make training pairs from my pictures in /workspace/my-pictures with make_grow_pairs.py.
3. Tell me where the pairs are so I can open some of them, and wait for my OK before training.
4. Train with train.sh, and tell me where the saved versions and test pictures are.
5. Run test.sh on my test picture with my chosen version, then again with none,
   and tell me where both results are so I can compare them.
6. Tell me which .safetensors file to download, and remind me to delete the pod when I'm done.

Stop and ask me if a step fails. Show me the real error instead of guessing.
```

Claude runs the same commands as the README, so you can still check each step yourself.
