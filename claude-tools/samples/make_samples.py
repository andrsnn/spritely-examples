"""Draws the sample sheets used in the README (simple pixel art, free to use): a 6-frame walk of a plain body,
an outfit (hat, coat, boots) that fits it, and an outfit with one frame drawn too tall, to show the tool stopping.

    python samples/make_samples.py
"""
from pathlib import Path
from PIL import Image, ImageDraw

W = H = 64
N = 6
HERE = Path(__file__).parent
SKIN, SUIT, HAIR = (235, 190, 150, 255), (70, 74, 86, 255), (90, 60, 40, 255)
HAT, COAT, TRIM, BOOT = (60, 50, 40, 255), (40, 70, 130, 255), (230, 190, 80, 255), (90, 60, 35, 255)


def bob(n):
    return [0, -1, -2, 0, -1, -2][n]


def legs(d, x, y, n, col, w=5):
    step = [-3, -1, 2, 3, 1, -2][n]
    d.rectangle((x - 6 + step, y, x - 6 + step + w, y + 14), fill=col)
    d.rectangle((x + 2 - step, y, x + 2 - step + w, y + 14), fill=col)


def body(n):
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    x, y = 32, 14 + bob(n)
    d.rectangle((x - 6, y, x + 5, y + 11), fill=SKIN)          # head
    d.rectangle((x - 6, y, x + 5, y + 2), fill=HAIR)
    d.rectangle((x - 8, y + 12, x + 7, y + 31), fill=SUIT)     # body
    legs(d, x, y + 32, n, SUIT)
    return im


def outfit(n, too_tall=False):
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    x, y = 32, 14 + bob(n)
    top = y - (8 if too_tall else 2)
    d.rectangle((x - 9, top, x + 8, y + 1), fill=HAT)          # hat
    d.rectangle((x - 9, y + 12, x + 8, y + 33), fill=COAT)     # coat
    d.line((x - 1, y + 12, x - 1, y + 33), fill=TRIM)
    step = [-3, -1, 2, 3, 1, -2][n]
    d.rectangle((x - 6 + step, y + 41, x - 6 + step + 5, y + 46), fill=BOOT)   # boots
    d.rectangle((x + 2 - step, y + 41, x + 2 - step + 5, y + 46), fill=BOOT)
    return im


def sheet(make):
    s = Image.new('RGBA', (W * N, H))
    for n in range(N):
        s.alpha_composite(make(n), (n * W, 0))
    return s


if __name__ == '__main__':
    sheet(body).save(HERE / 'hero.png')
    sheet(outfit).save(HERE / 'coat.png')
    sheet(lambda n: outfit(n, too_tall=(n == 2))).save(HERE / 'coat-bad.png')
    print('saved hero.png, coat.png, coat-bad.png')
