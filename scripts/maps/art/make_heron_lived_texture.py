"""Original, reproducible corner-shop labels and packaging for Heron Reach.

No downloaded artwork: Pillow vector shapes, local Apache-2.0 Open Sans fonts,
and seeded numpy surface variation. Run with system Python; Blender is not needed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "public/materials/heron/lived"
SOURCE_OUT = ROOT / "assets/textures/heron/lived"
FONT_ROOT = Path("/usr/share/fonts/truetype/open-sans")
SIZE = 1024
SCALE = 3
SEED = 291019
CREAM = (219, 213, 185)
PAPER = (204, 195, 163)
GREEN = (62, 81, 67)
INK = (52, 62, 53)
RUST = (129, 81, 62)
OCHRE = (167, 139, 82)
PALE = (182, 190, 167)

# Pixel rectangles are [left, top, width, height], excluding extruded gutters.
RECTS = {
    "open_hours": (8, 8, 240, 240),
    "services": (264, 8, 368, 160),
    "fresh_daily": (648, 8, 368, 160),
    "keep_clear": (264, 184, 368, 128),
    "daily_essentials": (8, 264, 240, 304),
    "value_prices": (648, 184, 368, 128),
    "groceries": (264, 328, 368, 64),
    "household": (648, 328, 368, 64),
    "price_strip": (264, 408, 752, 48),
    "dark_panel": (264, 472, 368, 176),
    "deliveries": (648, 472, 368, 176),
    "cash_card": (8, 584, 240, 64),
    "package_oats": (16, 680, 192, 336),
    "package_tea": (216, 680, 192, 336),
    "package_rice": (416, 680, 192, 336),
    "package_biscuits": (616, 680, 192, 336),
    "package_flakes": (816, 680, 192, 336),
}


def font(size: float, weight: str = "Bold") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_ROOT / f"OpenSans-{weight}.ttf"), round(size * SCALE))


def new_tile(name: str, colour: tuple) -> tuple:
    _, _, w, h = RECTS[name]
    im = Image.new("RGB", (w * SCALE, h * SCALE), colour)
    return im, ImageDraw.Draw(im), w, h


def rect(draw, box, fill=None, outline=None, width=1):
    draw.rectangle(tuple(round(x * SCALE) for x in box), fill=fill, outline=outline,
                   width=max(1, round(width * SCALE)))


def line(draw, points, fill, width=1):
    draw.line([(round(x * SCALE), round(y * SCALE)) for x, y in points], fill=fill,
              width=max(1, round(width * SCALE)))


def ellipse(draw, box, fill=None, outline=None, width=1):
    draw.ellipse(tuple(round(x * SCALE) for x in box), fill=fill, outline=outline,
                 width=max(1, round(width * SCALE)))


def text(draw, words, y, w, size, colour, weight="Bold", x=None, max_width=None):
    """Centred text with a fit guard; y specifies the visible glyph top."""
    max_width = max_width or w - 24
    face = font(size, weight)
    while draw.textbbox((0, 0), words, font=face)[2] > max_width * SCALE:
        size -= 0.5
        face = font(size, weight)
    bounds = draw.textbbox((0, 0), words, font=face)
    px = (w * SCALE - bounds[2]) / 2 if x is None else x * SCALE
    draw.text((px, y * SCALE - bounds[1]), words, font=face, fill=colour)


def frame(draw, w, h, colour, inset=7):
    rect(draw, (inset, inset, w - inset - 1, h - inset - 1), outline=colour)


def fixings(draw, w, h):
    for x in (7, w - 8):
        for y in (7, h - 8):
            ellipse(draw, (x - 1.7, y - 1.7, x + 1.7, y + 1.7), (123, 129, 111))
            line(draw, ((x - 1, y), (x + 1, y)), INK, 0.5)


def weather(im, index, strength=1.0, metal=False):
    """Quiet broad dirt and edge scuffs preserve legibility at mip levels."""
    im = im.resize((im.width // SCALE, im.height // SCALE), Image.Resampling.LANCZOS)
    rng = np.random.default_rng(SEED + index)
    w, h = im.size
    fine = rng.normal(0, 0.8 * strength, (h, w, 1))
    broad = Image.fromarray(rng.integers(80, 176, (max(2, h // 48), max(2, w // 48)), dtype=np.uint8))
    broad = np.asarray(broad.resize((w, h), Image.Resampling.BICUBIC), dtype=float)
    broad = (broad - 128)[:, :, None] * 0.075 * strength
    yy, xx = np.mgrid[:h, :w]
    edge = np.minimum.reduce([xx, yy, w - 1 - xx, h - 1 - yy])
    edge_dark = np.exp(-edge / 5.5)[:, :, None] * 10 * strength
    arr = np.asarray(im, dtype=float) + fine + broad - edge_dark
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(im)
    for _ in range(65 if metal else 24):
        x = int(rng.integers(2, w - 2))
        y = int(rng.integers(2, h - 2))
        if not metal and min(x, y, w - x, h - y) > 9:
            continue
        old = im.getpixel((x, y))
        c = tuple(min(255, int(v + (9 if metal else 12) * strength)) for v in old)
        draw.line((x, y, min(w - 2, x + int(rng.integers(2, 13))), y), fill=c)
    return im


def wheat(draw, cx, cy, colour, height=70):
    line(draw, ((cx, cy + height / 2), (cx, cy - height / 2)), colour, 2)
    for i in range(5):
        y = cy + height / 3 - i * height / 7
        for side in (-1, 1):
            x = cx + side * (9 + i * 0.6)
            ellipse(draw, (min(x, cx), y - 9, max(x, cx) + 1, y + 2), colour)


def leaf(draw, cx, cy, colour):
    ellipse(draw, (cx - 27, cy - 8, cx - 3, cy + 7), colour)
    ellipse(draw, (cx + 3, cy - 22, cx + 27, cy - 7), colour)
    ellipse(draw, (cx - 20, cy - 37, cx - 1, cy - 21), colour)
    line(draw, ((cx - 2, cy + 27), (cx + 2, cy - 36)), colour, 2)


def pack(name, brand, lines, colour, icon, weight):
    im, d, w, h = new_tile(name, CREAM)
    rect(d, (0, 0, w, 54), colour)
    rect(d, (0, h - 56, w, h), colour)
    # Printed crimped ends, shallow side folds and an original oval device.
    for x in range(4, w, 8):
        line(d, ((x, 1), (x, 8)), PALE, 0.65)
        line(d, ((x, h - 8), (x, h - 2)), PALE, 0.65)
    line(d, ((9, 55), (9, h - 57)), PAPER, 1.5)
    line(d, ((w - 10, 55), (w - 10, h - 57)), PAPER, 1.5)
    text(d, brand, 20, w, 17, CREAM)
    text(d, "PANTRY GOODS", 68, w, 10, colour, "Semibold")
    for i, word in enumerate(lines):
        text(d, word, 92 + i * 29, w, 26, colour)
    ellipse(d, (47, 167, 145, 251), outline=colour, width=1.1)
    if icon == "wheat":
        wheat(d, 86, 209, colour, 53)
        wheat(d, 109, 216, colour, 39)
    elif icon == "leaf":
        leaf(d, 95, 211, colour)
    elif icon == "rice":
        for x, y in ((77, 197), (96, 190), (111, 205), (84, 217), (104, 224), (71, 231)):
            ellipse(d, (x, y, x + 5, y + 14), colour)
    elif icon == "biscuit":
        for x, y in ((73, 194), (100, 216)):
            ellipse(d, (x - 16, y - 16, x + 16, y + 16), outline=colour, width=2)
            for dx, dy in ((-6, -6), (6, -6), (-6, 6), (6, 6)):
                ellipse(d, (x + dx - 1, y + dy - 1, x + dx + 1, y + dy + 1), colour)
    text(d, weight, 262, w, 12, colour, "Semibold")
    text(d, "EVERYDAY CUPBOARD", 296, w, 10, CREAM)
    return im


def build():
    tiles = {}
    im, d, w, h = new_tile("open_hours", GREEN)
    frame(d, w, h, PALE, 8)
    text(d, "OPEN", 28, w, 61, CREAM, "ExtraBold")
    line(d, ((34, 111), (w - 34, 111)), PALE, 1.5)
    text(d, "EVERY DAY", 131, w, 25, CREAM)
    text(d, "7am — 11pm", 177, w, 25, CREAM, "Semibold")
    tiles["open_hours"] = im

    im, d, w, h = new_tile("services", CREAM)
    frame(d, w, h, GREEN)
    text(d, "FOOD", 17, w, 41, GREEN, "ExtraBold")
    text(d, "DRINKS  /  TOP UPS", 78, w, 28, GREEN)
    text(d, "YOUR LOCAL CORNER SHOP", 127, w, 11, GREEN, "Semibold")
    tiles["services"] = im

    im, d, w, h = new_tile("fresh_daily", OCHRE)
    frame(d, w, h, INK)
    text(d, "FRESH", 22, w, 49, INK, "ExtraBold")
    text(d, "EVERY DAY", 94, w, 33, INK)
    tiles["fresh_daily"] = im

    im, d, w, h = new_tile("keep_clear", PAPER)
    rect(d, (0, 0, w, 7), RUST)
    rect(d, (0, h - 8, w, h), RUST)
    text(d, "KEEP CLEAR", 22, w, 39, RUST, "ExtraBold")
    text(d, "SERVICE ACCESS", 80, w, 22, INK)
    fixings(d, w, h)
    tiles["keep_clear"] = im

    im, d, w, h = new_tile("daily_essentials", CREAM)
    frame(d, w, h, RUST, 7)
    rect(d, (14, 14, w - 15, 45), RUST)
    text(d, "GOOD VALUE", 23, w, 14, CREAM)
    text(d, "DAILY", 67, w, 42, RUST, "ExtraBold")
    text(d, "ESSENTIALS", 123, w, 31, INK)
    line(d, ((29, 174), (w - 29, 174)), RUST, 1.5)
    text(d, "FROM", 190, w, 15, INK, "Semibold")
    text(d, "£1.29", 220, w, 49, RUST, "ExtraBold")
    tiles["daily_essentials"] = im

    im, d, w, h = new_tile("value_prices", OCHRE)
    text(d, "EVERYDAY VALUE", 14, w, 20, INK)
    text(d, "£1.49  /  £2.25", 56, w, 40, INK, "ExtraBold")
    tiles["value_prices"] = im

    for name in ("groceries", "household"):
        im, d, w, h = new_tile(name, GREEN)
        line(d, ((15, h - 8), (w - 15, h - 8)), OCHRE, 2)
        text(d, name.upper(), 15, w, 32, CREAM)
        tiles[name] = im

    im, d, w, h = new_tile("price_strip", CREAM)
    for i, (label, price) in enumerate((("OATS", "£1.29"), ("TEA", "£1.49"), ("RICE", "£1.85"), ("BISCUITS", "89p"), ("FLAKES", "£2.25"))):
        x = i * w / 5
        if i:
            line(d, ((x, 6), (x, h - 7)), PAPER, 1)
        text(d, label, 7, w / 5, 10, INK, "Semibold", x=x + 9, max_width=w / 5 - 16)
        text(d, price, 23, w / 5, 18, INK, x=x + 9, max_width=w / 5 - 16)
    tiles["price_strip"] = im

    im, d, w, h = new_tile("dark_panel", (54, 61, 59))
    frame(d, w, h, (81, 88, 83), 4)
    for y in range(9, h - 8, 4):
        line(d, ((8, y), (w - 9, y)), (57 + y % 7, 65 + y % 5, 61 + y % 5), 0.5)
    fixings(d, w, h)
    tiles["dark_panel"] = im

    im, d, w, h = new_tile("deliveries", PALE)
    frame(d, w, h, GREEN)
    text(d, "DELIVERIES", 26, w, 39, GREEN)
    text(d, "PLEASE RING BELL", 89, w, 24, GREEN)
    text(d, "KEEP THIS DOOR CLEAR", 140, w, 12, GREEN, "Semibold")
    fixings(d, w, h)
    tiles["deliveries"] = im

    im, d, w, h = new_tile("cash_card", PAPER)
    text(d, "CASH + CARD", 18, w, 25, INK)
    tiles["cash_card"] = im

    for name, brand, words, colour, icon, weight in (
        ("package_oats", "WILLOW MILL", ("ROLLED", "OATS"), GREEN, "wheat", "500 g"),
        ("package_tea", "GROVE LEAF", ("EVERYDAY", "TEA"), RUST, "leaf", "80 TEA BAGS"),
        ("package_rice", "CUPBOARD CO.", ("LONG GRAIN", "RICE"), (101, 112, 112), "rice", "1 kg"),
        ("package_biscuits", "BAKER'S ROW", ("OAT", "BISCUITS"), (142, 113, 64), "biscuit", "300 g"),
        ("package_flakes", "MORNING YARD", ("CORN", "FLAKES"), (126, 113, 76), "wheat", "375 g"),
    ):
        tiles[name] = pack(name, brand, words, colour, icon, weight)

    atlas = Image.new("RGB", (SIZE, SIZE), (69, 76, 66))
    for index, (name, im) in enumerate(tiles.items()):
        x, y, w, h = RECTS[name]
        im = weather(im, index, strength=1.2 if name == "dark_panel" else 1.0, metal=name == "dark_panel")
        # Four-pixel repeated edge gutter prevents immediate filtering bleed.
        padded = np.pad(np.asarray(im), ((4, 4), (4, 4), (0, 0)), mode="edge")
        atlas.paste(Image.fromarray(padded), (x - 4, y - 4))
    return atlas


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    SOURCE_OUT.mkdir(parents=True, exist_ok=True)
    atlas = build()
    png = SOURCE_OUT / "shop-lived-color.png"
    webp = OUT / "shop-lived-color.webp"
    atlas.save(png, optimize=True)
    atlas.save(webp, quality=88, method=6)
    metadata = {
        "version": 1,
        "size": [SIZE, SIZE],
        "colour_space": "sRGB",
        "opaque": True,
        "gutter_pixels": 4,
        "texture": "shop-lived-color.webp",
        "pixel_origin": "top-left",
        "uv_origin": "bottom-left; Blender source UVs, exported through Blender glTF conversion",
        "uv_rect_order": "u_min,v_min,u_max,v_max",
        "cells": {
            name: {
                "rect_px": [x, y, w, h],
                "aspect_ratio": w / h,
                "uv_rect": [x / SIZE, 1 - (y + h) / SIZE, (x + w) / SIZE, 1 - y / SIZE],
            }
            for name, (x, y, w, h) in RECTS.items()
        },
    }
    metadata_path = OUT / "atlas.json"
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    font_names = ("OpenSans-Bold.ttf", "OpenSans-ExtraBold.ttf", "OpenSans-Semibold.ttf")
    provenance = {
        "asset": "Heron Reach original lived-in corner-shop texture atlas",
        "authoring_date": "2026-10-19",
        "origin": "Original procedural artwork authored for ONSITE using Pillow and numpy; no photographs, downloaded artwork, external logo, donor texture or image generation.",
        "design": "Muted green, cream, rust and ochre UK corner-shop notices; five invented pantry package designs. Product names and packaging artwork were devised for the fictional setting.",
        "source": str(Path(__file__).relative_to(ROOT)),
        "source_image": str(png.relative_to(ROOT)),
        "source_sha256": sha(Path(__file__)),
        "rebuild": "python scripts/maps/art/make_heron_lived_texture.py",
        "random_seed": SEED,
        "encoding": {"mode": "RGB", "dimensions": [SIZE, SIZE], "webp_quality": 88, "webp_method": 6, "alpha": False},
        "fonts": [{
            "file": name,
            "source": str(FONT_ROOT / name),
            "sha256": sha(FONT_ROOT / name),
            "family": "Open Sans",
            "copyright": "Digitized data copyright (c) 2010-2011, Google Corporation.",
            "licence": "Apache-2.0",
            "licence_source": "/usr/share/doc/fonts-open-sans/copyright",
            "licence_url": "https://www.apache.org/licenses/LICENSE-2.0",
            "use": "Locally installed font rasterised into original artwork; font binaries are not shipped.",
        } for name in font_names],
        "outputs": [{"file": p.name, "path": str(p.relative_to(ROOT)), "role": "source" if p == png else "runtime", "bytes": p.stat().st_size, "sha256": sha(p)} for p in (png, webp, metadata_path)],
    }
    (OUT / "manifest.json").write_text(json.dumps(provenance, indent=2) + "\n")
    assert webp.stat().st_size < 200_000, "Atlas exceeded WebP budget"
    assert atlas.mode == "RGB" and atlas.size == (1024, 1024)
    print(json.dumps({"webp_bytes": webp.stat().st_size, "png_bytes": png.stat().st_size, "cells": len(RECTS), "output": str(OUT)}))


if __name__ == "__main__":
    main()
