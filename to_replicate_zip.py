"""Pack a pairs folder (from make_grow_pairs.py or the Blender script) into the zip Replicate's FLUX Kontext trainer reads:
0001_start.png (what you give the model), 0001_end.png (what you want back) and 0001.txt (the caption).

    python to_replicate_zip.py <pairs folder> [--max 20] [--out pairs.zip]

Replicate suggests 10 to 20 pairs; --max picks that many spread evenly through the folder."""
import argparse, json, zipfile
from pathlib import Path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('pairs')
    ap.add_argument('--max', type=int, default=20)
    ap.add_argument('--out')
    a = ap.parse_args(argv)
    pairs = Path(a.pairs)
    rows = [json.loads(l) for l in (pairs / 'train.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    if a.max and len(rows) > a.max:
        rows = [rows[round(k * (len(rows) - 1) / (a.max - 1))] for k in range(a.max)] if a.max > 1 else rows[:1]
    out = Path(a.out or pairs / 'replicate-pairs.zip')
    with zipfile.ZipFile(out, 'w') as z:
        for k, r in enumerate(rows, 1):
            control = r.get('control_path') or r.get('control_path_0')
            z.write(control, f'{k:04d}_start{Path(control).suffix}')
            z.write(r['image_path'], f'{k:04d}_end{Path(r["image_path"]).suffix}')
            z.writestr(f'{k:04d}.txt', r['caption'])
    print(f'{len(rows)} pairs -> {out}')
    return out


if __name__ == '__main__':
    main()
