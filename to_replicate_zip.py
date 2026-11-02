"""Pack a pairs folder (from make_grow_pairs.py or the Blender script) into the zip Replicate's FLUX Kontext trainer reads:
0001_start.png (what you give the model), 0001_end.png (what you want back) and 0001.txt (the caption).

    python to_replicate_zip.py <pairs folder> [--max 20] [--out pairs.zip]

Replicate suggests 10 to 20 pairs; --max picks that many spread evenly through the folder. Pictures are shrunk to --size
(768 by default): in my test the trainer ran out of graphics memory on 1024 px pairs."""


def png_bytes(path, size):
    im = Image.open(path).convert('RGB')
    if max(im.size) > size: im.thumbnail((size, size), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'PNG'); return b.getvalue()
import argparse, io, json, zipfile
from pathlib import Path
from PIL import Image


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('pairs')
    ap.add_argument('--max', type=int, default=20)
    ap.add_argument('--out')
    ap.add_argument('--size', type=int, default=768)
    a = ap.parse_args(argv)
    pairs = Path(a.pairs)
    rows = [json.loads(l) for l in (pairs / 'train.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    if a.max and len(rows) > a.max:
        rows = [rows[round(k * (len(rows) - 1) / (a.max - 1))] for k in range(a.max)] if a.max > 1 else rows[:1]
    out = Path(a.out or pairs / 'replicate-pairs.zip')
    with zipfile.ZipFile(out, 'w') as z:
        for k, r in enumerate(rows, 1):
            control = r.get('control_path') or r.get('control_path_0')
            z.writestr(f'{k:04d}_start.png', png_bytes(control, a.size))
            z.writestr(f'{k:04d}_end.png', png_bytes(r['image_path'], a.size))
            z.writestr(f'{k:04d}.txt', r['caption'])
    print(f'{len(rows)} pairs -> {out}')
    return out


if __name__ == '__main__':
    main()
