# claude-tools: turn a fix into a tool Claude uses every time

This is the example from my video "AI game dev | Claude: stop making the same mistakes". It's a small project you can copy:
a working tool, the skill file that tells Claude Code when to use it, and a rules file.

```
claude-tools/
  tools/fit_gear.py                 the tool: puts an outfit on every frame of a sprite sheet
  .claude/skills/fit-gear/SKILL.md  tells Claude Code what the tool is for and how to run it
  CLAUDE.md                         rules Claude reads at the start of every session
  tests/test_fit_gear.py            tests, so a fix to the tool stays fixed
  samples/                          a plain walking body, an outfit, and an outfit with one bad frame
```

## Try it

You need Python 3 and Pillow (`pip install pillow`).

```
python tools/fit_gear.py samples/hero.png samples/coat.png out.png
```

That saves `out.png`, the hero wearing the coat in all 6 frames, and `out-check.png`, each frame before and after.

Now try the outfit with a bad frame:

```
python tools/fit_gear.py samples/hero.png samples/coat-bad.png out.png
```

It prints `Stopped: frame 3: outfit is 17% taller than the body` and saves nothing.

## Use it with Claude Code

1. Copy this folder into your project, or copy `tools/`, `.claude/` and `CLAUDE.md` into it.
2. Open Claude Code in your project. It reads `CLAUDE.md` and sees the `fit-gear` skill at the start of the session.
3. Ask for the job in plain words, like "put the coat on my hero". Claude uses the skill and runs the tool.
4. Or call it yourself: type `/fit-gear samples/hero.png samples/coat.png out.png`.

## Make your own

1. Pick the mistake your AI keeps making. Save a bad picture and a good picture.
2. Fix one example with Claude, and check it yourself.
3. Ask Claude to turn the steps that worked into a script in `tools/`, with a check that stops when the mistake comes back.
4. Have the script save a before-and-after picture, and look at that picture.
5. Ask Claude to write a skill for it in `.claude/skills/<name>/SKILL.md`, and put rules for every job in `CLAUDE.md`.

When the tool gets something new wrong, ask Claude to fix the tool and add a test, not just fix that one picture.

The sample art is drawn by `samples/make_samples.py` and is free to use.
