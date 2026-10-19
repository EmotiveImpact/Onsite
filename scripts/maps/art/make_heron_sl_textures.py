"""Turn the South London thread's seam-fixed ChatGPT textures into Heron Reach runtime sets.

    python3 scripts/maps/art/make_heron_sl_textures.py /mnt/project-files/south-london/assets/textures-generated

The sources are the research thread's healed copies of images made with ChatGPT (originals on
branch claude/chatgpt-images, commit dd803c9; see TEXTURES.md). This script resizes them and derives
normal and ORM maps from their luminance; it never draws new content.

Writes, under public/materials/heron/:
- hr_tile_underpass, hr_concrete_aggregate, hr_glass_blocks, hr_wired_glass, hr_stair_tread:
  <name>-{color,normal,orm}.webp, picked up by the Blender build and the runtime library by name.
- props/hr_void_sheet-color.webp: the perforated steel void sheet, mapped per asset at runtime.
- decals/sl-tags.webp, decals/sl-buffed.webp, decals/sl-gum.webp: wall tags and throw-ups, buffed
  patches, and chewing gum on paving (a soft round falloff so a patch never shows a square edge).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from heron_tex_common import OUT, cavity_ao, detail_height, height_to_normal, norm01, save_webp  # noqa: E402


def load(path, size):
    im = Image.open(path)
    im = im.convert('RGBA' if im.mode == 'RGBA' else 'RGB').resize(size, Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255


def lin(a):
    return np.where(a <= .04045, a / 12.92, ((a + .055) / 1.055) ** 2.4).astype(np.float32)


def tiling(src, name, size, cover_m, depth_mm, rough, rough_var=.08, metal=0.0):
    """Colour as given; height from band-passed luminance; normal, cavity AO and roughness from it."""
    c = load(src, size)[..., :3]
    h = detail_height(lin(c), 1.0, 14.0)
    texel = cover_m * 1000 / size[0]
    nrm = height_to_normal(h * depth_mm / 3, texel)
    h01 = norm01(h)
    ao = cavity_ao(h01, sigma=5.0, floor=.55)
    r = np.clip(rough + rough_var * (.5 - h01) * 2, .04, 1).astype(np.float32)
    orm = np.stack([ao, r, np.full_like(r, metal)], -1)
    save_webp(c, OUT / f'{name}-color.webp', 90)
    save_webp(nrm, OUT / f'{name}-normal.webp', 92)
    hh, ww = orm.shape[:2]
    save_webp(orm.reshape(hh // 2, 2, ww // 2, 2, -1).mean((1, 3)), OUT / f'{name}-orm.webp', 92)
    print(name, size, f'{cover_m} m')


def decal(src, out, size, falloff=False):
    a = load(src, size)
    if falloff:
        h, w = a.shape[:2]
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.hypot((x + .5) / w - .5, (y + .5) / h - .5) * 2
        a[..., 3] *= np.clip((1 - r) / .35, 0, 1) ** 1.5
    save_webp(a, OUT / 'decals' / out, 90)
    print(out, size)


if __name__ == '__main__':
    src = Path(sys.argv[1])
    T, D = src / 'textures', src / 'decals'
    tiling(T / 'hr_tex_underpass_tiles.png', 'hr_tile_underpass', (1024, 1024), 2.0, 2.5, .38, .25)
    tiling(T / 'hr_tex_exposed_aggregate_concrete.png', 'hr_concrete_aggregate', (1024, 1024), 2.0, 4.0, .86)
    tiling(T / 'hr_tex_glass_blocks.png', 'hr_glass_blocks', (512, 512), 1.0, 6.0, .12, .1)
    tiling(T / 'hr_tex_wired_glass.png', 'hr_wired_glass', (512, 512), .5, .6, .15, .04)
    tiling(T / 'hr_tex_stair_tread_painted.png', 'hr_stair_tread', (1024, 512), 1.0, 1.5, .62)
    save_webp(load(T / 'hr_tex_void_sheet.png', (512, 1024)), OUT / 'props' / 'hr_void_sheet-color.webp', 90)
    decal(D / 'hr_decal_tags_set.png', 'sl-tags.webp', (1024, 1024))
    decal(D / 'hr_decal_buffed_graffiti.png', 'sl-buffed.webp', (1024, 512))
    decal(D / 'hr_decal_gum_spots.png', 'sl-gum.webp', (1024, 1024), falloff=True)
