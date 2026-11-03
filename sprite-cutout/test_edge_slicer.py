"""python -m pytest sprite-cutout   (Pillow, numpy, scipy)"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_slicer as es

MAG = (255, 0, 255)


def sheet():
    """Two 'characters' on magenta. The left one has an enclosed magenta pocket and a purple-tinted outline."""
    im = Image.new('RGB', (200, 120), MAG); d = ImageDraw.Draw(im)
    d.rectangle((20, 20, 70, 100), fill=(40, 60, 140))           # body
    d.rectangle((35, 45, 55, 70), fill=MAG)                         # enclosed pocket (gap between arm and body)
    d.rectangle((19, 19, 71, 101), outline=(90, 20, 90))            # dark outline blended with magenta
    d.rectangle((120, 30, 170, 100), fill=(60, 120, 40))
    d.point((100, 60), fill=(10, 10, 10))                           # a speck: filtered as an outlier
    return im


def test_white_background_like_spritely():
    im = Image.new('RGB', (100, 60), (255, 255, 255)); d = ImageDraw.Draw(im)
    d.rectangle((10, 10, 40, 50), fill=(200, 30, 30)); d.rectangle((60, 10, 90, 50), fill=(30, 30, 200))
    sprites = es.analyze(im)
    assert [s['box'] for s in sprites] == [(10, 10, 40, 50), (60, 10, 90, 50)]  # reading order, left to right


def test_slices_two_sprites_and_drops_specks():
    assert len(es.slice_sprites(sheet(), bg=MAG, bg_tol=110)) == 2


def test_enclosed_pocket_kept_by_default_cleared_on_request():
    left = es.slice_sprites(sheet(), bg=MAG, bg_tol=110)[0]
    assert np.asarray(left)[30, 20, 3] == 255  # the faithful slicer keeps what the edge flood can't reach
    left = es.slice_sprites(sheet(), bg=MAG, bg_tol=110, clear_pockets=True)[0]
    assert np.asarray(left)[30, 20, 3] == 0


def test_despill_neutralises_purple_outline():
    left = np.asarray(es.slice_sprites(sheet(), bg=MAG, bg_tol=110, despill_edges=True)[0]).astype(int)
    r, g, b = left[0, 10, :3]  # a pixel of the outline
    assert r - g < 10 and b - g < 10
