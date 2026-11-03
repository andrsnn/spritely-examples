"""fit_gear: put an outfit on every frame of a character sprite sheet, and stop if a frame doesn't fit.

    python tools/fit_gear.py <hero sheet> <outfit sheet> <out sheet> [--frame 64x64]

Both sheets use the same grid of frames, on a transparent background. The outfit sheet holds only the outfit
(hat, coat, boots...) drawn in the same place as the body in each frame. The tool:
  1. checks every frame: the outfit must be about as tall as the body (within 5%) and sit over it;
  2. stops on the first frame that fails, and says which frame and why;
  3. otherwise draws the outfit over the body in every frame and saves the dressed sheet;
  4. saves <out>-check.png next to it: each frame before (top row) and after (bottom row), to look at.
"""
import argparse
import sys
from PIL import Image

HEIGHT_TOLERANCE = 0.05   # the outfit may be 5% taller or shorter than the body
CENTER_TOLERANCE = 0.25   # the outfit's middle may sit at most a quarter of the body's width off the body's middle


class FitError(Exception):
    pass


def frames(sheet, w, h):
    """The frames of a sheet, left to right, top to bottom."""
    return [sheet.crop((x, y, x + w, y + h)) for y in range(0, sheet.height - h + 1, h) for x in range(0, sheet.width - w + 1, w)]


def check_frame(n, body, outfit):
    """Raise FitError if the outfit in frame n doesn't fit the body."""
    b, o = body.getbbox(), outfit.getbbox()
    if b is None:
        raise FitError(f'frame {n}: no body drawn')
    if o is None:
        return  # nothing to put on in this frame
    bh, oh = b[3] - b[1], o[3] - o[1]
    if abs(oh / bh - 1) > HEIGHT_TOLERANCE:
        raise FitError(f'frame {n}: outfit is {round(100 * (oh / bh - 1))}% {"taller" if oh > bh else "shorter"} than the body')
    off = abs((o[0] + o[2]) / 2 - (b[0] + b[2]) / 2)
    if off > CENTER_TOLERANCE * (b[2] - b[0]):
        raise FitError(f'frame {n}: outfit sits {round(off)} px off the body')


def fit_gear(hero, outfit, frame_size):
    """The hero sheet with the outfit drawn on every frame. Raises FitError on the first frame that doesn't fit."""
    w, h = frame_size
    hero, outfit = hero.convert('RGBA'), outfit.convert('RGBA')
    if hero.size != outfit.size:
        raise FitError(f'the sheets are different sizes: hero {hero.size}, outfit {outfit.size}')
    for n, (b, o) in enumerate(zip(frames(hero, w, h), frames(outfit, w, h)), 1):
        check_frame(n, b, o)
    dressed = hero.copy()
    dressed.alpha_composite(outfit)
    return dressed


def check_sheet(hero, dressed, frame_size, scale=4):
    """Before (top row) and after (bottom row) for every frame, scaled up so pixel art is easy to see."""
    w, h = frame_size
    before, after = frames(hero.convert('RGBA'), w, h), frames(dressed, w, h)
    sheet = Image.new('RGBA', (w * len(before), h * 2), (40, 42, 54, 255))
    for n, (b, a) in enumerate(zip(before, after)):
        sheet.alpha_composite(b, (n * w, 0)); sheet.alpha_composite(a, (n * w, h))
    return sheet.resize((sheet.width * scale, sheet.height * scale), Image.NEAREST)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Put an outfit on every frame of a sprite sheet.')
    ap.add_argument('hero'); ap.add_argument('outfit'); ap.add_argument('out')
    ap.add_argument('--frame', default='64x64', help='frame size, e.g. 64x64')
    a = ap.parse_args(argv)
    size = tuple(int(v) for v in a.frame.lower().split('x'))
    hero, outfit = Image.open(a.hero), Image.open(a.outfit)
    try:
        dressed = fit_gear(hero, outfit, size)
    except FitError as e:
        sys.exit(f'Stopped: {e}')
    dressed.save(a.out)
    check = a.out.rsplit('.', 1)[0] + '-check.png'
    check_sheet(hero, dressed, size).save(check)
    print(f'saved {a.out} and {check}')


if __name__ == '__main__':
    main()
