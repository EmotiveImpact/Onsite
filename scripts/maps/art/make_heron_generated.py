"""Turn the ChatGPT images made for Heron Reach into runtime textures.

    python3 scripts/maps/art/make_heron_generated.py docs/maps/heron-reach-32/art/generated

The source PNGs live in docs/maps/heron-reach-32/art/generated/ (merged from the
claude/chatgpt-images branch; see TEXTURES.md for provenance). This
script only crops, resizes, packs and keys them; it never draws new content.

Writes, under public/materials/heron/:
- backdrop/tower-elevation-{a,b}-{color,emit}.webp: one tower front each, cropped to the building,
  with an emission map keyed from the warm lit windows.
- backdrop/skyline-panorama.webp: the wrap-around city horizon, its top quarter faded to clear so the
  graded sky dome shows above it.
- windows/interiors-photo-{color,emit}.webp: the 8 x 4 window atlas (256 px cells) with the twelve
  interiors, their mirror images and four close-ups in the lit cells; cells 4, 12, 20 and 28 stay dark curtains from
  the procedural atlas, as the Blender build expects.
- decals/graffiti-photo-atlas.webp: six pieces in a 2 x 3 atlas (1024 x 512 cells), alpha keyed from
  the black background.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'public' / 'materials' / 'heron'
DARK = {4, 12, 20, 28}


def arr(im):
    return np.asarray(im.convert('RGB')).astype(np.float32) / 255


def u8(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8))


def warm_emit(a, gain=1.4):
    """Keep the warm, bright pixels (lit rooms and lamps) as emission."""
    lum = a @ np.array([.2126, .7152, .0722], np.float32)
    warm = np.clip((a[..., 0] - a[..., 2] - .12) * 4, 0, 1) * np.clip((lum - .25) * 3, 0, 1)
    return a * warm[..., None] * gain


def tower(src, name):
    im = Image.open(src).convert('RGB')
    a = arr(im)
    lum = a.mean(2)
    cols = np.where((lum > .06).mean(0) > .5)[0]
    rows = np.where((lum > .06).mean(1) > .3)[0]
    box = (int(cols.min()) + 2, int(rows.min()) + 1, int(cols.max()) - 1, int(rows.max()))
    body = im.crop(box)
    h = round(512 * body.height / body.width)
    body = body.resize((512, h), Image.LANCZOS)
    body.save(OUT / 'backdrop' / f'{name}-color.webp', quality=88)
    u8(warm_emit(arr(body))).save(OUT / 'backdrop' / f'{name}-emit.webp', quality=88)
    print(name, 'crop', box, '->', body.size)


def panorama(src):
    im = Image.open(src).convert('RGB')
    a = arr(im)
    h = a.shape[0]
    y = np.arange(h, dtype=np.float32)[:, None] / h
    alpha = np.clip(y / .25, 0, 1) ** 1.5  # clear at the top edge, solid from a quarter down
    rgba = np.dstack([a, np.broadcast_to(alpha, a.shape[:2])])
    Image.fromarray((rgba * 255 + .5).astype(np.uint8), 'RGBA').save(OUT / 'backdrop' / 'skyline-panorama.webp', quality=88)
    print('panorama', im.size)


def windows(folder):
    old_c = Image.open(OUT / 'windows' / 'interiors-color.webp').convert('RGB')
    old_e = Image.open(OUT / 'windows' / 'interiors-emit.webp').convert('RGB')
    srcs = [Image.open(p).convert('RGB').resize((256, 256), Image.LANCZOS) for p in sorted(folder.glob('interior-*.png'))]
    zoom = [s.crop((40, 40, 216, 216)).resize((256, 256), Image.LANCZOS) for s in srcs[::3]]  # four close-ups fill the last cells
    cells = srcs + [ImageOps.mirror(s) for s in srcs] + zoom
    col, emi = Image.new('RGB', (2048, 1024)), Image.new('RGB', (2048, 1024))
    k = 0
    for i in range(32):
        x, y = (i % 8) * 256, (i // 8) * 256
        if i in DARK or k >= len(cells):
            col.paste(old_c.crop((x, y, x + 256, y + 256)), (x, y))
            emi.paste(old_e.crop((x, y, x + 256, y + 256)), (x, y))
            continue
        c = cells[k]
        k += 1
        col.paste(c, (x, y))
        a = arr(c)
        lum = a @ np.array([.2126, .7152, .0722], np.float32)
        emi.paste(u8(a * np.clip((lum[..., None] - .05) * 2.6, 0, 1) * 1.3), (x, y))
    col.save(OUT / 'windows' / 'interiors-photo-color.webp', quality=88)
    emi.save(OUT / 'windows' / 'interiors-photo-emit.webp', quality=88)
    print('windows', len(srcs), 'interiors,', k, 'lit cells')


def graffiti(folder):
    atlas = Image.new('RGBA', (2048, 1536), (0, 0, 0, 0))
    for i, p in enumerate(sorted(folder.glob('graffiti-*.png'))[:6]):
        a = arr(Image.open(p).resize((1024, 512), Image.LANCZOS))
        alpha = np.clip((a.max(2) - .06) * 2.2, 0, 1)
        rgb = np.where(alpha[..., None] > 0, a / np.maximum(alpha[..., None], 1e-3), 0)
        tile = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), alpha]) * 255 + .5).astype(np.uint8), 'RGBA')
        atlas.paste(tile, ((i % 2) * 1024, (i // 2) * 512))
    atlas.save(OUT / 'decals' / 'graffiti-photo-atlas.webp', quality=90)
    print('graffiti atlas', atlas.size)


if __name__ == '__main__':
    src = Path(sys.argv[1])
    tower(src / 'backdrop' / 'tower-elevation-a.png', 'tower-elevation-a')
    tower(src / 'backdrop' / 'tower-elevation-b.png', 'tower-elevation-b')
    panorama(src / 'backdrop' / 'skyline-panorama.png')
    windows(src / 'windows')
    graffiti(src / 'decals')
