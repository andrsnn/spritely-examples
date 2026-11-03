# sprite-cutout

Spritely's edge slicer (`analyzeSpritesUnified` + `sliceSprites` from the Spritely app), ported from TypeScript to Python.
Use it to cut sprites out of a sheet: background from the edges in, everything the edge can't reach is a sprite,
4-connected components, outliers dropped, one pixel mask per sprite, in reading order.

```
python edge_slicer.py sheet.png out_dir                                   # transparent or white background (as in Spritely)
python edge_slicer.py sheet.png out_dir --bg 255,0,255 --bg-tol 110 --clear-pockets --despill   # art drawn on magenta
```

`--clear-pockets` and `--despill` are for sheets drawn on a key colour instead of transparency. They clear key-coloured
gaps the edge flood can't reach, and take the magenta tint out of outline pixels (the purple fringe). Keep `--bg-tol` tight
(about 40) when the background is close to skin or cloth colours, such as tan.

Needs Python 3 with numpy, scipy and Pillow. Tests: `python -m pytest` in this folder.
