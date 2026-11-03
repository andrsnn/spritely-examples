import subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools')); sys.path.insert(0, str(ROOT / 'samples'))
import fit_gear as fg
import make_samples as ms


def test_good_outfit_goes_on_every_frame():
    hero, coat = ms.sheet(ms.body), ms.sheet(ms.outfit)
    dressed = fg.fit_gear(hero, coat, (64, 64))
    assert dressed.size == hero.size
    assert dressed.getpixel((32, 30)) == ms.COAT  # the coat is over the body in frame 1


def test_too_tall_frame_stops_and_names_the_frame():
    hero, bad = ms.sheet(ms.body), ms.sheet(lambda n: ms.outfit(n, too_tall=(n == 2)))
    try:
        fg.fit_gear(hero, bad, (64, 64))
    except fg.FitError as e:
        assert 'frame 3' in str(e) and 'taller' in str(e)
    else:
        raise AssertionError('should have stopped')


def test_command_line_saves_the_check_sheet(tmp_path):
    ms.sheet(ms.body).save(tmp_path / 'hero.png'); ms.sheet(ms.outfit).save(tmp_path / 'coat.png')
    r = subprocess.run([sys.executable, str(ROOT / 'tools' / 'fit_gear.py'), 'hero.png', 'coat.png', 'out.png'], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / 'out-check.png').exists()
