"""python -m pytest tests  (needs only Pillow)"""
import json, random, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import make_grow_pairs as g


def test_edge_band_kept_rest_magenta():
    img = Image.new('RGB', (100, 100), (10, 20, 30))
    out = g.blank_all_but_edge(img, 'left', 40)
    assert out.getpixel((39, 50)) == (10, 20, 30)
    assert out.getpixel((40, 50)) == g.MAGENTA
    out = g.blank_all_but_edge(img, 'bottom', 25)
    assert out.getpixel((50, 75)) == (10, 20, 30) and out.getpixel((50, 74)) == g.MAGENTA


def test_pair_target_matches_control_outside_magenta():
    rng = random.Random(3)
    img = Image.effect_noise((900, 700), 60).convert('RGB')
    target, control, side = g.make_pair(img, 256, rng)
    assert target.size == control.size == (256, 256)
    kept = [(x, y) for x in range(0, 256, 7) for y in range(0, 256, 7) if control.getpixel((x, y)) != g.MAGENTA]
    assert kept and all(control.getpixel(p) == target.getpixel(p) for p in kept)


def test_folder_run(tmp_path):
    src = tmp_path / 'pics'; src.mkdir()
    for k in range(4): Image.effect_noise((800, 800), 50 + k).convert('RGB').save(src / f'{k}.png')
    Image.new('RGB', (100, 100)).save(src / 'too-small.png')
    rows = g.main(['--images', str(src), '--out', str(tmp_path / 'out'), '--size', '256', '--per-image', '3', '--holdout', '1'])
    assert len(rows) == 9
    lines = (tmp_path / 'out' / 'train.jsonl').read_text().splitlines()
    assert len(lines) == 9 and all(Path(json.loads(l)['control_path']).exists() for l in lines)
    assert '--ci' in (tmp_path / 'out' / 'sample_prompts.txt').read_text()
    assert 'control_resolution = [256, 256]' in (tmp_path / 'out' / 'dataset.toml').read_text()


def test_replicate_zip(tmp_path):
    import zipfile
    import to_replicate_zip as rz
    src = tmp_path / 'pics'; src.mkdir()
    for k in range(3): Image.effect_noise((600, 600), 50 + k).convert('RGB').save(src / f'{k}.png')
    g.main(['--images', str(src), '--out', str(tmp_path / 'p'), '--size', '256', '--per-image', '5', '--holdout', '1'])
    zf = zipfile.ZipFile(rz.main([str(tmp_path / 'p'), '--max', '4', '--size', '128'])); names = zf.namelist()
    import io
    assert max(Image.open(io.BytesIO(zf.read('0001_end.png'))).size) == 128
    assert sorted(names)[:3] == ['0001.txt', '0001_end.png', '0001_start.png'] and len(names) == 12
