"""sprite-cutout: Spritely's unified edge slicer (analyzeSpritesUnified + sliceSprites), ported from TypeScript to Python.
It is an edge-slicing algorithm, not chroma or colour keying.

The algorithm (same steps and defaults as the TypeScript):
  1. Background mask: a pixel is background if alpha <= 10, or it is near-white (every channel >= 245).
     Added option: `bg=(r, g, b), bg_tol=...` also counts pixels within that colour distance of a known plain background
     (for sheets drawn on magenta or tan instead of white or transparency).
  2. Flood fill from all four image edges through background pixels (4-connectivity). Only background that is
     connected to the edge is background; enclosed areas stay part of the sprite.
  3. Everything else is foreground. Label it with 4-connectivity.
  4. Drop outliers: boxes under 10 px, components under 10% of the median area of the "large" components (over 5% of
     the biggest), and components shorter than 35% of the median large height.
  5. Each surviving component becomes a sprite: its box and its pixel mask (only that component's own pixels), so
     neighbouring sprites and specks never leak in. Sprites are ordered in reading rows, left to right.

    python edge_slicer.py sheet.png out_dir [--bg 255,0,255 --bg-tol 60]      -> out_dir/sprite_00.png ...
    from edge_slicer import slice_sprites; sprites = slice_sprites(pil_image, bg=(255, 0, 255))   # list of RGBA images
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

DEFAULTS = dict(alpha_threshold=10, min_sprite_size=10, white_threshold=245, treat_white_as_background=True)
FOUR = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]])


def background_mask(rgba, alpha_threshold=10, white_threshold=245, treat_white_as_background=True, bg=None, bg_tol=60):
    """True where a pixel counts as background before the flood fill (step 1)."""
    a = rgba[..., 3]; rgb = rgba[..., :3].astype(int)
    m = a <= alpha_threshold
    if treat_white_as_background:
        m |= (rgb >= white_threshold).all(-1)
    if bg is not None:
        m |= np.sqrt(((rgb - np.array(bg)) ** 2).sum(-1)) < bg_tol
    return m


def flood_fill_background(bgmask):
    """Background reachable from the image border through background pixels, 4-connectivity (step 2)."""
    lab, _ = ndimage.label(bgmask, structure=FOUR)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    return np.isin(lab, border[border > 0])


def filter_outlier_labels(counts, boxes, min_sprite_size=10, expected_count=None):
    """Same rules as filterOutlierLabels in sprite-slicer.ts (step 4)."""
    entries = [(l, c) for l, c in counts.items()
               if boxes[l][2] - boxes[l][0] + 1 >= min_sprite_size and boxes[l][3] - boxes[l][1] + 1 >= min_sprite_size]
    entries.sort(key=lambda e: -e[1])
    if not entries: return set()
    if len(entries) == 1: return {entries[0][0]}
    if expected_count and len(entries) == expected_count: return {l for l, _ in entries}
    max_area = entries[0][1]
    large = [(l, c) for l, c in entries if c > max_area * 0.05]
    median_area = sorted(c for _, c in large)[len(large) // 2]
    heights = sorted(boxes[l][3] - boxes[l][1] + 1 for l, _ in large)
    median_h = heights[len(heights) // 2]
    return {l for l, c in entries if c >= median_area * 0.10 and boxes[l][3] - boxes[l][1] + 1 >= median_h * 0.35}


def analyze(img, expected_count=None, bg=None, bg_tol=60, **opts):
    """Boxes and per-sprite masks: [{'box': (x0, y0, x1, y1), 'mask': bool array over the box}] in reading order."""
    o = {**DEFAULTS, **opts}
    rgba = np.asarray(img.convert('RGBA'))
    bgm = flood_fill_background(background_mask(rgba, o['alpha_threshold'], o['white_threshold'], o['treat_white_as_background'], bg, bg_tol))
    fg = ~bgm
    labels, n = ndimage.label(fg, structure=FOUR)
    counts, boxes = {}, {}
    for k, sl in enumerate(ndimage.find_objects(labels), start=1):
        if sl is None: continue
        counts[k] = int((labels[sl] == k).sum())
        boxes[k] = (sl[1].start, sl[0].start, sl[1].stop - 1, sl[0].stop - 1)
    keep = filter_outlier_labels(counts, boxes, o['min_sprite_size'], expected_count)
    sprites = [{'label': k, 'box': boxes[k], 'mask': labels[boxes[k][1]:boxes[k][3] + 1, boxes[k][0]:boxes[k][2] + 1] == k} for k in keep]
    # reading rows: a sprite joins a row it overlaps by 20% of the shorter height, or whose centre is within slack
    if sprites:
        hs = sorted(s['box'][3] - s['box'][1] + 1 for s in sprites); slack = max(20, hs[len(hs) // 2] * 0.45)
        rows = []
        for s in sorted(sprites, key=lambda s: ((s['box'][1] + s['box'][3]) / 2, s['box'][0])):
            cy = (s['box'][1] + s['box'][3]) / 2; best = None
            for r in rows:
                ov = any(min(s['box'][3], m['box'][3]) - max(s['box'][1], m['box'][1]) >= 0.2 * min(s['box'][3] - s['box'][1], m['box'][3] - m['box'][1]) for m in r['m'])
                d = abs(cy - r['cy'])
                if (ov or d <= slack) and (best is None or d < best[0]): best = (d, r)
            if best: best[1]['m'].append(s); best[1]['cy'] = sum((m['box'][1] + m['box'][3]) / 2 for m in best[1]['m']) / len(best[1]['m'])
            else: rows.append({'m': [s], 'cy': cy})
        sprites = [s for r in sorted(rows, key=lambda r: r['cy']) for s in sorted(r['m'], key=lambda s: s['box'][0])]
    return sprites


def despill(crop, band=3, tint=18):
    """Take the magenta tint out of opaque pixels within `band` px of transparency (outline pixels of art drawn on magenta)."""
    keep = crop[..., 3] > 0
    grown = np.pad(~keep, band, constant_values=True)  # outside the crop counts as transparent
    for _ in range(band):
        grown = grown | np.roll(grown, 1, 0) | np.roll(grown, -1, 0) | np.roll(grown, 1, 1) | np.roll(grown, -1, 1)
    grown = grown[band:-band, band:-band]
    r, g, b = (crop[..., k].astype(int) for k in range(3))
    spill = grown & keep & (r > g + tint) & (b > g + tint)
    crop[..., 0] = np.where(spill, np.minimum(r, g + 6), r); crop[..., 2] = np.where(spill, np.minimum(b, g + 6), b)
    return crop


def slice_sprites(img, expected_count=None, bg=None, bg_tol=60, clear_pockets=False, despill_edges=False, **opts):
    """RGBA images of each sprite: its box, with pixels outside its own component made transparent (step 5).
    Extras for art drawn on a plain key colour (magenta) rather than transparency (not in sprite-slicer.ts, which gets
    transparent or white input): `clear_pockets` also clears background-coloured pixels the edge flood could not reach
    (gaps between an arm and the body); `despill_edges` takes the key tint out of outline pixels."""
    rgba = np.asarray(img.convert('RGBA'))
    out = []
    for s in analyze(img, expected_count, bg, bg_tol, **opts):
        x0, y0, x1, y1 = s['box']
        crop = rgba[y0:y1 + 1, x0:x1 + 1].copy()
        alpha = np.where(s['mask'], crop[..., 3], 0)
        if clear_pockets and bg is not None:
            near = np.sqrt(((crop[..., :3].astype(int) - np.array(bg)) ** 2).sum(-1)) < bg_tol
            alpha = np.where(near, 0, alpha)
        crop[..., 3] = alpha
        if despill_edges: crop = despill(crop)
        out.append(Image.fromarray(crop, 'RGBA'))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('out_dir')
    ap.add_argument('--bg', help='r,g,b of a plain background other than white/transparent')
    ap.add_argument('--bg-tol', type=float, default=60)
    ap.add_argument('--expected', type=int)
    ap.add_argument('--clear-pockets', action='store_true'); ap.add_argument('--despill', action='store_true')
    a = ap.parse_args(argv)
    bg = tuple(int(v) for v in a.bg.split(',')) if a.bg else None
    d = Path(a.out_dir); d.mkdir(parents=True, exist_ok=True)
    sprites = slice_sprites(Image.open(a.src), a.expected, bg, a.bg_tol, a.clear_pockets, a.despill)
    for k, s in enumerate(sprites): s.save(d / f'sprite_{k:02d}.png')
    print(len(sprites), 'sprites ->', d)


if __name__ == '__main__':
    main()
