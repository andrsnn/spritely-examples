---
name: fit-gear
description: Put an outfit on every frame of the hero's sprite sheet. Use whenever gear, clothes or armour go on the hero. Run the tool; never redraw the hero by hand.
---

# fit-gear

Run:

```
python tools/fit_gear.py <hero sheet> <outfit sheet> <out sheet> --frame 64x64
```

- If it prints `Stopped: frame N: ...`, the outfit doesn't fit that frame. Fix the outfit sheet, not the tool's check.
- Open `<out>-check.png` and look at it before saying the job is done. The top row is before and the bottom row is after.
- If the tool gets something new wrong, fix the tool and add a test for that mistake in `tests/`.
