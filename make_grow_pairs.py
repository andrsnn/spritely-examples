"""Make training pairs for a "grow the picture" model from a folder of your own pictures.

Each pair is one square cut from a picture:
  target   the cut as it is (what the model must learn to paint)
  control  the same cut with everything but one edge band painted magenta (what the model is given)
The model learns to fill the magenta part so it matches the edge it was given.

    python make_grow_pairs.py --images my_pictures --out grow_pairs [--size 1024] [--per-image 6] [--holdout 2]

Writes <out>/target/*.png, <out>/control/*.png, <out>/train.jsonl, <out>/dataset.toml and <out>/sample_prompts.txt
(test jobs made from --holdout pictures that never go into training)."""
import argparse, json, random
from pathlib import Path
from PIL import Image

MAGENTA = (255, 0, 255)
CAPTION = ("Continue the picture into the magenta area. Keep the same style, lighting and scale, "
           "and fill the magenta area with matching art.")
EXTS = {'.png', '.jpg', '.jpeg', '.webp'}


def blank_all_but_edge(img, side, keep):
    """Returns a copy of img with everything except a band `keep` pixels deep on `side` painted magenta."""
    w, h = img.size
    out = Image.new('RGB', (w, h), MAGENTA)
    box = {'left': (0, 0, keep, h), 'right': (w - keep, 0, w, h), 'top': (0, 0, w, keep), 'bottom': (0, h - keep, w, h)}[side]
    out.paste(img.crop(box), box[:2])
    return out


def random_cut(img, size, rng):
    """A random size x size square from img, after shrinking img by a random amount so the art shows at more than one scale."""
    w, h = img.size
    smallest = size / min(w, h)
    scale = rng.uniform(max(smallest, 0.5), 1.0) if smallest < 1 else smallest
    img = img.resize((max(size, round(w * scale)), max(size, round(h * scale))), Image.LANCZOS)
    x, y = rng.randint(0, img.width - size), rng.randint(0, img.height - size)
    return img.crop((x, y, x + size, y + size))


def make_pair(img, size, rng):
    cut = random_cut(img, size, rng)
    side = rng.choice(['left', 'right', 'top', 'bottom'])
    keep = round(size * rng.uniform(0.3, 0.5))
    return cut, blank_all_but_edge(cut, side, keep), side


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--images', required=True, help='folder of your pictures (each at least --size pixels on its short side)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--size', type=int, default=1024)
    ap.add_argument('--per-image', type=int, default=6, help='how many pairs to cut from each picture')
    ap.add_argument('--holdout', type=int, default=2, help='pictures kept out of training and used for test jobs')
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)
    files = sorted(p for p in Path(a.images).rglob('*') if p.suffix.lower() in EXTS)
    files = [p for p in files if min(Image.open(p).size) >= a.size]
    if len(files) <= a.holdout: raise SystemExit(f'need more than {a.holdout} pictures at least {a.size} px on the short side, found {len(files)}')
    rng.shuffle(files)
    held, train = files[:a.holdout], files[a.holdout:]
    out = Path(a.out).resolve()
    for d in ('target', 'control', 'test'): (out / d).mkdir(parents=True, exist_ok=True)
    rows = []
    for p in train:
        img = Image.open(p).convert('RGB')
        for k in range(a.per_image):
            name = f'{len(rows):05d}.png'
            target, control, _ = make_pair(img, a.size, rng)
            target.save(out / 'target' / name); control.save(out / 'control' / name)
            rows.append({'image_path': str(out / 'target' / name), 'control_path': str(out / 'control' / name), 'caption': CAPTION})
    with open(out / 'train.jsonl', 'w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r) + '\n')
    prompts = []
    for k, p in enumerate(held):
        target, control, _ = make_pair(Image.open(p).convert('RGB'), a.size, rng)
        target.save(out / 'test' / f'{k}-answer.png'); control.save(out / 'test' / f'{k}-input.png')
        prompts.append(f'{CAPTION} --ci {out / "test" / f"{k}-input.png"} --w {a.size} --h {a.size} --s 20 --d {k + 1}')
    (out / 'sample_prompts.txt').write_text('\n'.join(prompts) + '\n', encoding='utf-8')
    write_toml(out, a.size)
    print(f'{len(rows)} pairs from {len(train)} pictures, {len(held)} kept out for testing -> {out}')
    return rows


def write_toml(out, size):
    (out / 'dataset.toml').write_text(
        f'[general]\nresolution = [{size}, {size}]\nbatch_size = 1\nenable_bucket = false\n\n'
        f'[[datasets]]\nimage_jsonl_file = "{(out / "train.jsonl").as_posix()}"\ncache_directory = "{(out / "cache").as_posix()}"\n'
        f'control_resolution = [{size}, {size}]\n', encoding='utf-8')


if __name__ == '__main__':
    main()
