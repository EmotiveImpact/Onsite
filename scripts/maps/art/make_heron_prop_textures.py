"""Procedural textures for the Heron Reach props kit.

Run: python3 scripts/maps/art/make_heron_prop_textures.py

Everything is drawn from code with numpy and Pillow: no photographs, no downloads.
Fonts are the system Inter and DejaVu families (both under open font licences),
used only to rasterise invented lettering. All brand names are invented.
Output: public/materials/heron/props/<name>-color.webp (+ -normal.webp where noted).
Deterministic: every random source is seeded.
"""

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heron_props_atlas as A  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, A.PROPS_DIR)

F_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
F_XBOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
F_DISP = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_REG = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
F_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
F_SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"

_font_cache = {}


def font(path, size):
    key = (path, int(size))
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, max(6, int(size)))
    return _font_cache[key]


# ---------------------------------------------------------------------------
# noise and helpers
# ---------------------------------------------------------------------------


def pnoise(h, w, beta=2.0, seed=0, lo=0.0):
    """Periodic (tileable) 1/f^beta noise in 0..1."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1.0
    amp = 1.0 / np.power(f, beta / 2.0)
    amp[0, 0] = 0.0
    if lo > 0:
        amp *= f > lo
    n = np.real(np.fft.ifft2(np.fft.fft2(white) * amp))
    n -= n.min()
    n /= max(1e-9, n.max())
    return n


def box_px(rect, W, H):
    u0, v0, u1, v1 = rect
    return (int(round(u0 * W)), int(round((1 - v1) * H)), int(round(u1 * W)), int(round((1 - v0) * H)))


def to_img(arr):
    return Image.fromarray(np.clip(arr * 255.0 + 0.5, 0, 255).astype(np.uint8))


def rgb(c):
    return tuple(int(round(x * 255)) for x in c)


def mute(c, amount=0.18):
    g = sum(c) / 3
    return tuple(x + (g - x) * amount for x in c)


def text_img(text, path, size, fill, condense=1.0, stroke=0):
    f = font(path, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    w, h = r - l + 4, b - t + 4
    im = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((2 - l, 2 - t), text, font=f, fill=fill, stroke_width=stroke, stroke_fill=fill)
    if condense != 1.0:
        im = im.resize((max(1, int(w * condense)), h), Image.LANCZOS)
    return im


def paste_text(canvas, box, text, path, fill, condense=0.85, align="center", max_size=None, rotate=0):
    x0, y0, x1, y1 = box
    bw, bh = max(1, x1 - x0), max(1, y1 - y0)
    size = max_size or bh
    im = text_img(text, path, size * 1.3, fill, condense)
    if rotate:
        im = im.rotate(rotate, expand=True)
    s = min(bw / im.width, bh / im.height)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    if align == "center":
        px = x0 + (bw - im.width) // 2
    elif align == "left":
        px = x0
    else:
        px = x1 - im.width
    py = y0 + (bh - im.height) // 2
    canvas.alpha_composite(im, (int(px), int(py)))


def grime(canvas, seed, strength=0.25, scale_beta=2.6, spots=0.0):
    """Multiply a tileable grime field into an RGBA canvas."""
    arr = np.asarray(canvas).astype(np.float32) / 255.0
    h, w = arr.shape[:2]
    n = pnoise(h, w, scale_beta, seed)
    m = 1.0 - strength * np.clip((n - 0.35) * 1.8, 0, 1)
    if spots > 0:
        s = pnoise(h, w, 0.6, seed + 99)
        m *= 1.0 - spots * (s > 0.82)
    arr[..., :3] *= m[..., None]
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGBA")


def save(img, name, kind="color", lossless=False):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"{name}-{kind}.webp")
    if img.mode == "RGBA" and kind == "color" and not lossless:
        img = img.convert("RGB")
    if lossless:
        img.save(path, "WEBP", lossless=True, quality=100, method=6)
    else:
        img.save(path, "WEBP", quality=90, method=6)
    print("wrote", os.path.relpath(path, ROOT), img.size)


def normal_from_height(h, strength=4.0):
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5
    nx = -dx * strength
    ny = dy * strength  # OpenGL: +Y up, image rows run down
    nz = np.ones_like(h)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / ln, ny / ln, nz / ln], axis=-1)
    return to_img(n * 0.5 + 0.5)


# ---------------------------------------------------------------------------
# wire meshes (RGBA, alpha clip at 0.5)
# ---------------------------------------------------------------------------


def line_cov(coord, pitch, width):
    """Anti-aliased coverage of lines of `width` px every `pitch` px."""
    d = np.abs(((coord / pitch) + 0.5) % 1.0 - 0.5) * pitch
    return np.clip(width / 2.0 - d + 0.5, 0.0, 1.0)


def wire_mesh(name, size, cells, wire_px, base, seed, knot=0.0, wobble=0.0):
    pitch = size / cells
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) + 0.5
    if wobble > 0:
        wx = (pnoise(size, size, 3.0, seed + 3) - 0.5) * wobble
        wy = (pnoise(size, size, 3.0, seed + 4) - 0.5) * wobble
    else:
        wx = wy = 0.0
    a = np.maximum(line_cov(xx + wx, pitch, wire_px), line_cov(yy + wy, pitch, wire_px))
    if knot > 0:
        dx = np.abs(((xx + wx) / pitch + 0.5) % 1.0 - 0.5) * pitch
        dy = np.abs(((yy + wy) / pitch + 0.5) % 1.0 - 0.5) * pitch
        a = np.maximum(a, np.clip(knot - np.sqrt(dx * dx + dy * dy) + 0.5, 0, 1))
    n = pnoise(size, size, 2.2, seed)
    col = np.ones((size, size, 3), np.float32) * np.array(base, np.float32)
    col *= (0.75 + 0.5 * n)[..., None]
    rust = pnoise(size, size, 1.2, seed + 7)
    rust_m = (rust > 0.80).astype(np.float32) * 0.6
    col = col * (1 - rust_m[..., None]) + np.array([0.20, 0.11, 0.06]) * rust_m[..., None]
    # cylindrical shading across each wire
    out = np.concatenate([np.clip(col, 0, 1), a[..., None]], axis=-1)
    img = to_img(out)
    save(img, name, lossless=True)


# ---------------------------------------------------------------------------
# packaging
# ---------------------------------------------------------------------------

PALETTE = [
    (0.78, 0.20, 0.16), (0.90, 0.62, 0.12), (0.18, 0.40, 0.66), (0.20, 0.52, 0.30),
    (0.86, 0.80, 0.62), (0.52, 0.18, 0.42), (0.95, 0.92, 0.86), (0.12, 0.12, 0.14),
    (0.84, 0.42, 0.16), (0.30, 0.62, 0.70), (0.62, 0.70, 0.22), (0.70, 0.12, 0.20),
    (0.92, 0.80, 0.30), (0.36, 0.24, 0.16), (0.16, 0.26, 0.44), (0.88, 0.56, 0.56),
]

TALL_NAMES = ["MORNING OATS", "GOLD FLAKES", "HONEY RINGS", "BRAN CRUNCH", "CORN PUFFS",
              "REACH VALUE", "CHOCO HOOPS", "WHEAT BITES", "SUNNY RICE", "TEA BAGS",
              "FRUIT MUESLI", "PORRIDGE", "LONG LIFE MILK", "ORANGE JUICE", "APPLE JUICE",
              "HOT CHOCOLATE"]
WIDE_NAMES = ["DIGESTIVES", "CUSTARD CREAMS", "GINGER NUTS", "ROOIBOS", "CRACKERS",
              "WAFERS", "SHORTBREAD", "RICH TEA"]
BAG_NAMES = ["KRUNCHO", "PLANTAIN CHIPS", "SALT & VINEGAR", "CHEESE PUFFS", "PRAWN SNACKS",
             "TORTILLA", "POPCORN", "SPICY RINGS"]
CAN_NAMES = ["KORA COLA", "LEMON FIZZ", "GINGER KICK", "MANGO DROP", "VOLTEDGE",
             "PINE SODA", "TROPIQ", "CREAM SODA"]
BOTTLE_NAMES = ["STILL WATER", "KORA COLA", "ORANGE", "LEMONADE", "TONIC", "PALE ALE",
                "SUNFIZZ", "APPLE"]
TIN_NAMES = ["BAKED BEANS", "TOMATOES", "SWEETCORN", "ACKEE", "CHICKPEAS", "SOUP",
             "PEACHES", "JOLLOF BASE"]
SACK_NAMES = ["BASMATI RICE", "LONG GRAIN", "CHAPATI FLOUR", "SEMOLINA"]


def design_box(im, box, seed, name, style):
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    c1 = mute(PALETTE[seed % len(PALETTE)])
    c2 = mute(PALETTE[(seed * 7 + 3) % len(PALETTE)])
    light = sum(c1) / 3 > 0.6
    ink = (0.10, 0.09, 0.09) if light else (0.97, 0.95, 0.90)
    d.rectangle(box, fill=rgb(c1))
    if style == "tall":
        d.rectangle((x0, y0, x1, y0 + int(h * 0.20)), fill=rgb(c2))
        cx, cy, r = x0 + w * 0.5, y0 + h * 0.70, w * 0.30
        d.ellipse((cx - r, cy - r * 0.8, cx + r, cy + r * 0.8), fill=rgb(mute((0.95, 0.90, 0.80))))
        d.ellipse((cx - r * 0.7, cy - r * 0.5, cx + r * 0.7, cy + r * 0.35), fill=rgb(mute(PALETTE[(seed + 5) % 16])))
        paste_text(im, (x0 + 4, y0 + int(h * 0.24), x1 - 4, y0 + int(h * 0.40)), name.split()[0], F_XBOLD, rgb(ink) + (255,), 0.8)
        if len(name.split()) > 1:
            paste_text(im, (x0 + 6, y0 + int(h * 0.40), x1 - 6, y0 + int(h * 0.48)), " ".join(name.split()[1:]), F_BOLD, rgb(ink) + (255,), 0.85)
        paste_text(im, (x0 + 4, y0 + 3, x1 - 4, y0 + int(h * 0.17)), "HERON" if seed % 3 == 0 else "REACH", F_BOLD, rgb((0.97, 0.95, 0.9)) + (255,), 0.8)
        d.rectangle((x0, y1 - int(h * 0.08), x1, y1), fill=rgb(c2))
    elif style == "wide":
        d.rectangle((x0, y0 + int(h * 0.62), x1, y1), fill=rgb(c2))
        d.ellipse((x1 - w * 0.35, y0 + h * 0.15, x1 - w * 0.05, y0 + h * 0.85), fill=rgb(mute((0.80, 0.62, 0.38))))
        paste_text(im, (x0 + 6, y0 + int(h * 0.12), x0 + int(w * 0.64), y0 + int(h * 0.55)), name, F_XBOLD, rgb(ink) + (255,), 0.8)
    elif style == "bag":
        d.rectangle(box, fill=rgb(c1))
        for k in range(0, w, 6):
            d.line((x0 + k, y0, x0 + k + 3, y0 + 8), fill=rgb(mute(c2)), width=2)
            d.line((x0 + k, y1, x0 + k + 3, y1 - 8), fill=rgb(mute(c2)), width=2)
        cx, cy = x0 + w / 2, y0 + h * 0.62
        d.ellipse((cx - w * 0.36, cy - h * 0.2, cx + w * 0.36, cy + h * 0.2), fill=rgb(mute((0.90, 0.72, 0.36))))
        paste_text(im, (x0 + 6, y0 + int(h * 0.12), x1 - 6, y0 + int(h * 0.34)), name, F_XBOLD, rgb(ink) + (255,), 0.8)
        d.rectangle((x0, y0 + int(h * 0.36), x1, y0 + int(h * 0.40)), fill=rgb(c2))
    elif style == "sack":
        d.rectangle(box, fill=rgb(mute((0.92, 0.89, 0.80))))
        d.rectangle((x0, y0 + int(h * 0.30), x1, y0 + int(h * 0.56)), fill=rgb(c1))
        paste_text(im, (x0 + 6, y0 + int(h * 0.33), x1 - 6, y0 + int(h * 0.53)), name, F_XBOLD, rgb((0.97, 0.95, 0.9)) + (255,), 0.8)
        paste_text(im, (x0 + int(w * 0.3), y0 + int(h * 0.62), x1 - int(w * 0.3), y0 + int(h * 0.78)), "5kg", F_XBOLD, rgb(c1) + (255,), 0.9)
        for k in range(6):
            yy = y0 + int(h * (0.08 + k * 0.03))
            d.line((x0 + 8, yy, x1 - 8, yy), fill=rgb(mute(c2)), width=1)
    # small print lines and weight block
    for k in range(3):
        yy = y1 - int(h * (0.12 + 0.04 * k))
        if style in ("tall", "wide"):
            d.line((x0 + 6, yy, x0 + int(w * (0.3 + 0.1 * rng.random())), yy), fill=rgb(ink), width=1)


def design_wrap(im, box, seed, name, kind):
    """Cylinder wraps: u runs around, v runs bottom to top (image rows reversed)."""
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    c1 = mute(PALETTE[(seed * 3 + 1) % len(PALETTE)])
    c2 = mute(PALETTE[(seed * 5 + 2) % len(PALETTE)])
    ink = (0.97, 0.95, 0.90) if sum(c1) / 3 < 0.6 else (0.1, 0.1, 0.1)

    def band(f0, f1, col):
        d.rectangle((x0, y0 + int(h * (1 - f1)), x1, y0 + int(h * (1 - f0))), fill=rgb(col))

    if kind == "can":
        band(0.0, 1.0, c1)
        band(0.0, 0.06, (0.62, 0.63, 0.64))
        band(0.94, 1.0, (0.70, 0.71, 0.72))
        band(0.18, 0.26, c2)
        for half in (0, 1):
            paste_text(im, (x0 + half * w // 2 + 6, y0 + int(h * 0.32), x0 + (half + 1) * w // 2 - 6, y0 + int(h * 0.70)), name, F_XBOLD, rgb(ink) + (255,), 0.75)
    elif kind == "bottle":
        body = [(0.20, 0.12, 0.08), (0.55, 0.66, 0.72), (0.86, 0.50, 0.14), (0.84, 0.86, 0.80),
                (0.70, 0.78, 0.74), (0.42, 0.26, 0.10), (0.80, 0.70, 0.24), (0.62, 0.70, 0.30)][seed % 8]
        band(0.0, 1.0, mute(body))
        band(0.22, 0.52, c1)
        band(0.22, 0.25, c2)
        band(0.49, 0.52, c2)
        band(0.90, 1.0, mute(PALETTE[(seed + 11) % 16]))
        for half in (0, 1):
            paste_text(im, (x0 + half * w // 2 + 4, y0 + int(h * 0.52), x0 + (half + 1) * w // 2 - 4, y0 + int(h * 0.74)), name, F_XBOLD, rgb(ink) + (255,), 0.75)
    elif kind == "tin":
        band(0.0, 1.0, c1)
        band(0.0, 0.07, (0.64, 0.64, 0.62))
        band(0.93, 1.0, (0.66, 0.66, 0.64))
        band(0.60, 0.70, c2)
        for half in (0, 1):
            cx = x0 + half * w // 2 + w // 4
            d.ellipse((cx - w * 0.1, y0 + h * 0.48, cx + w * 0.1, y0 + h * 0.74), fill=rgb(mute((0.85, 0.35, 0.18))))
            paste_text(im, (x0 + half * w // 2 + 4, y0 + int(h * 0.12), x0 + (half + 1) * w // 2 - 4, y0 + int(h * 0.36)), name, F_XBOLD, rgb(ink) + (255,), 0.75)
    elif kind == "jug":
        body = [(0.86, 0.86, 0.84), (0.30, 0.50, 0.70)][seed % 2]
        band(0.0, 1.0, mute(body))
        band(0.25, 0.62, c1)
        band(0.88, 1.0, c2)
        paste_text(im, (x0 + 8, y0 + int(h * 0.42), x1 - 8, y0 + int(h * 0.70)), ["FRESH WASH", "BIO LIQUID"][seed % 2], F_XBOLD, rgb((0.97, 0.95, 0.9)) + (255,), 0.75)


def make_products():
    W = H = 2048
    im = Image.new("RGBA", (W, H), (40, 38, 36, 255))
    for cat, (row, count, _) in A.PRODUCT_ROWS.items():
        for i in range(count):
            rect = A.product_rect(cat, i)
            box = box_px(rect, W, H)
            seed = row * 31 + i * 7 + 3
            if cat in ("tall", "wide", "bag", "sack"):
                names = {"tall": TALL_NAMES, "wide": WIDE_NAMES, "bag": BAG_NAMES, "sack": SACK_NAMES}[cat]
                design_box(im, box, seed, names[i % len(names)], cat)
            elif cat in ("can", "bottle", "tin", "jug"):
                names = {"can": CAN_NAMES, "bottle": BOTTLE_NAMES, "tin": TIN_NAMES, "jug": ["", ""]}[cat]
                design_wrap(im, box, seed, names[i % len(names)], cat)
            elif cat == "scratch":
                d = ImageDraw.Draw(im)
                x0, y0, x1, y1 = box
                d.rectangle(box, fill=rgb((0.12, 0.12, 0.13)))
                cw, ch = (x1 - x0) // 3, (y1 - y0) // 2
                for k in range(6):
                    cx0 = x0 + (k % 3) * cw + 4
                    cy0 = y0 + (k // 3) * ch + 4
                    col = mute(PALETTE[(k * 5 + i * 3 + 2) % 16], 0.1)
                    d.rectangle((cx0, cy0, cx0 + cw - 8, cy0 + ch - 8), fill=rgb(col))
                    d.rectangle((cx0 + 6, cy0 + ch // 2, cx0 + cw - 14, cy0 + ch - 16), fill=rgb((0.72, 0.72, 0.70)))
                    paste_text(im, (cx0 + 4, cy0 + 6, cx0 + cw - 12, cy0 + ch // 2 - 4), ["£1", "£2", "£5", "WIN", "LUCKY", "£3"][(k + i) % 6], F_XBOLD, (250, 245, 235, 255), 0.8)
    im = grime(im, 11, 0.10, 2.4)
    save(im, "products")


# ---------------------------------------------------------------------------
# shop and office details
# ---------------------------------------------------------------------------


def make_shop():
    W = H = 1024
    im = Image.new("RGBA", (W, H), (60, 58, 56, 255))
    d = ImageDraw.Draw(im)
    # price ticket channel
    x0, y0, x1, y1 = box_px(A.SHOP["price_strip"], W, H)
    d.rectangle((x0, y0, x1, y1), fill=rgb((0.16, 0.16, 0.17)))
    prices = ["£1.29", "£0.89", "2 FOR £3", "£2.49", "£1.10", "£3.99", "£0.65", "£1.75"]
    step = (x1 - x0) / 8
    for k in range(8):
        tx = int(x0 + k * step + 10)
        yellow = k % 3 == 2
        d.rectangle((tx, y0 + 6, tx + int(step * 0.55), y1 - 6), fill=rgb((0.92, 0.80, 0.25) if yellow else (0.93, 0.92, 0.88)))
        paste_text(im, (tx + 4, y0 + 10, tx + int(step * 0.55) - 4, y1 - 10), prices[k], F_XBOLD, (30, 30, 30, 255), 0.85)
    # COLD DRINKS header (used as an emissive texture too)
    box = box_px(A.SHOP["cold_drinks"], W, H)
    d.rectangle(box, fill=rgb((0.08, 0.10, 0.14)))
    paste_text(im, (box[0] + 30, box[1] + 18, box[2] - 30, box[3] - 18), "COLD DRINKS", F_DISP, (235, 238, 240, 255), 0.82)
    # till screen
    box = box_px(A.SHOP["till_screen"], W, H)
    d.rectangle(box, fill=rgb((0.10, 0.18, 0.26)))
    bx0, by0, bx1, by1 = box
    for k in range(6):
        yy = by0 + 12 + k * 16
        d.rectangle((bx0 + 10, yy, bx0 + 10 + (40 + (k * 37) % 80), yy + 8), fill=rgb((0.70, 0.80, 0.86)))
        d.rectangle((bx1 - 50, yy, bx1 - 12, yy + 8), fill=rgb((0.70, 0.80, 0.86)))
    d.rectangle((bx0 + 10, by1 - 26, bx1 - 10, by1 - 10), fill=rgb((0.30, 0.62, 0.40)))
    # card reader
    box = box_px(A.SHOP["card_reader"], W, H)
    d.rectangle(box, fill=rgb((0.10, 0.10, 0.11)))
    bx0, by0, bx1, by1 = box
    d.rectangle((bx0 + 8, by0 + 8, bx1 - 8, by0 + 40), fill=rgb((0.32, 0.44, 0.40)))
    for r_ in range(4):
        for c_ in range(3):
            px = bx0 + 12 + c_ * ((bx1 - bx0 - 24) // 3)
            py = by0 + 50 + r_ * 16
            d.rectangle((px, py, px + 18, py + 10), fill=rgb((0.30, 0.30, 0.32)))
    # counter front panel
    box = box_px(A.SHOP["counter_front"], W, H)
    d.rectangle(box, fill=rgb((0.20, 0.21, 0.23)))
    bx0, by0, bx1, by1 = box
    d.rectangle((bx0, by0, bx1, by0 + 24), fill=rgb((0.75, 0.55, 0.22)))
    paste_text(im, (bx0 + 40, by0 + 50, bx0 + 470, by1 - 60), "THE CORNER", F_DISP, (225, 222, 214, 255), 0.82)
    paste_text(im, (bx0 + 520, by0 + 60, bx1 - 40, by0 + 120), "BILL PAY  ·  TOP UP  ·  PARCELS", F_BOLD, (200, 196, 186, 255), 0.85)
    paste_text(im, (bx0 + 520, by0 + 140, bx1 - 40, by0 + 200), "SCRATCHCARDS SOLD HERE", F_BOLD, (226, 196, 120, 255), 0.85)
    paste_text(im, (bx0 + 520, by0 + 216, bx1 - 140, by0 + 250), "NO SALE OF TOBACCO OR ALCOHOL TO UNDER 18s", F_REG, (170, 166, 160, 255), 0.9)
    # monitor
    box = box_px(A.SHOP["monitor"], W, H)
    d.rectangle(box, fill=rgb((0.82, 0.86, 0.90)))
    bx0, by0, bx1, by1 = box
    d.rectangle((bx0, by0, bx1, by0 + 14), fill=rgb((0.22, 0.36, 0.52)))
    for r_ in range(9):
        for c_ in range(5):
            px = bx0 + 8 + c_ * ((bx1 - bx0 - 16) // 5)
            py = by0 + 22 + r_ * 14
            d.rectangle((px, py, px + (bx1 - bx0) // 6, py + 9), outline=rgb((0.6, 0.66, 0.72)), fill=rgb((0.94, 0.95, 0.96)))
    # keyboard
    box = box_px(A.SHOP["keyboard"], W, H)
    d.rectangle(box, fill=rgb((0.12, 0.12, 0.13)))
    bx0, by0, bx1, by1 = box
    kw = (bx1 - bx0 - 12) / 15
    for r_ in range(5):
        for c_ in range(15):
            px = bx0 + 6 + c_ * kw
            py = by0 + 8 + r_ * ((by1 - by0 - 16) / 5)
            d.rectangle((px + 1, py + 1, px + kw - 2, py + (by1 - by0 - 16) / 5 - 3), fill=rgb((0.22, 0.22, 0.24)))
    # papers
    box = box_px(A.SHOP["papers"], W, H)
    d.rectangle(box, fill=rgb((0.90, 0.89, 0.85)))
    bx0, by0, bx1, by1 = box
    for k in range(12):
        yy = by0 + 16 + k * 11
        d.line((bx0 + 14, yy, bx1 - 14 - (k * 23) % 60, yy), fill=rgb((0.45, 0.45, 0.48)), width=2)
    # fridge back panel: white ribbed liner
    box = box_px(A.SHOP["fridge_back"], W, H)
    d.rectangle(box, fill=rgb((0.88, 0.89, 0.90)))
    bx0, by0, bx1, by1 = box
    for k in range(bx0, bx1, 16):
        d.line((k, by0, k, by1), fill=rgb((0.74, 0.76, 0.78)), width=3)
    # phone
    box = box_px(A.SHOP["phone"], W, H)
    d.rectangle(box, fill=rgb((0.14, 0.14, 0.15)))
    bx0, by0, bx1, by1 = box
    d.rectangle((bx0 + 8, by0 + 8, bx1 - 8, by0 + 34), fill=rgb((0.40, 0.48, 0.42)))
    for r_ in range(4):
        for c_ in range(3):
            d.rectangle((bx0 + 14 + c_ * 36, by0 + 46 + r_ * 18, bx0 + 40 + c_ * 36, by0 + 58 + r_ * 18), fill=rgb((0.32, 0.32, 0.34)))
    # cash drawer
    box = box_px(A.SHOP["cash_drawer"], W, H)
    d.rectangle(box, fill=rgb((0.13, 0.13, 0.14)))
    bx0, by0, bx1, by1 = box
    d.ellipse(((bx0 + bx1) // 2 - 8, by0 + 30, (bx0 + bx1) // 2 + 8, by0 + 46), fill=rgb((0.55, 0.55, 0.56)))
    d.line((bx0 + 10, by1 - 20, bx1 - 10, by1 - 20), fill=rgb((0.06, 0.06, 0.06)), width=3)
    im = grime(im, 21, 0.10, 2.4)
    save(im, "shop")


# ---------------------------------------------------------------------------
# launderette
# ---------------------------------------------------------------------------


def brushed(h, w, seed, base=0.62, amp=0.10):
    rng = np.random.default_rng(seed)
    rows = rng.standard_normal((h, 1)) * 0.5
    line = np.repeat(rows, w, axis=1)
    fine = rng.standard_normal((h, w)) * 0.3
    n = (line + fine)
    n = np.asarray(Image.fromarray(((n - n.min()) / (n.max() - n.min()) * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(1))) / 255.0
    return base + (n - 0.5) * amp


def make_laundry():
    W = H = 1024
    base = brushed(H, W, 5, 0.60, 0.12)
    arr = np.stack([base * 0.98, base, base * 1.02, np.ones_like(base)], -1)
    im = to_img(np.clip(arr, 0, 1))
    im = im.convert("RGBA")
    d = ImageDraw.Draw(im)
    for key, label, price in (("washer_panel", "WASH 8kg", "£4.00"), ("dryer_panel", "DRY 10 MIN", "£1.00")):
        bx0, by0, bx1, by1 = box_px(A.LAUNDRY[key], W, H)
        d.rectangle((bx0 + 2, by0 + 2, bx1 - 2, by1 - 2), outline=rgb((0.30, 0.30, 0.31)), width=3)
        # display
        d.rectangle((bx0 + 30, by0 + 40, bx0 + 190, by0 + 110), fill=rgb((0.05, 0.06, 0.05)))
        paste_text(im, (bx0 + 40, by0 + 50, bx0 + 180, by0 + 100), "00:28" if "WASH" in label else "10:00", F_MONO, (232, 150, 60, 255), 1.0)
        # buttons
        cols = [(0.70, 0.30, 0.22), (0.30, 0.48, 0.62), (0.40, 0.56, 0.36), (0.80, 0.66, 0.30)]
        for k, c in enumerate(cols):
            cx = bx0 + 230 + k * 58
            d.ellipse((cx, by0 + 52, cx + 40, by0 + 92), fill=rgb((0.18, 0.18, 0.19)))
            d.ellipse((cx + 6, by0 + 58, cx + 34, by0 + 86), fill=rgb(mute(c)))
        paste_text(im, (bx0 + 230, by0 + 104, bx0 + 460, by0 + 128), "HOT   WARM   COOL   START", F_REG, (40, 40, 42, 255), 0.9)
        # coin slot and label
        d.rectangle((bx0 + 30, by0 + 150, bx0 + 190, by0 + 230), fill=rgb((0.22, 0.22, 0.23)))
        d.rectangle((bx0 + 100, by0 + 165, bx0 + 116, by0 + 215), fill=rgb((0.02, 0.02, 0.02)))
        paste_text(im, (bx0 + 220, by0 + 150, bx0 + 470, by0 + 195), label, F_XBOLD, (36, 36, 38, 255), 0.85)
        paste_text(im, (bx0 + 220, by0 + 200, bx0 + 400, by0 + 240), price, F_XBOLD, (150, 40, 30, 255), 0.85)
    for i, rect in enumerate(A.LAUNDRY["number"]):
        bx0, by0, bx1, by1 = box_px(rect, W, H)
        d.rectangle((bx0 + 6, by0 + 6, bx1 - 6, by1 - 6), fill=rgb((0.92, 0.91, 0.86)))
        paste_text(im, (bx0 + 16, by0 + 14, bx1 - 16, by1 - 14), f"{i + 1:02d}", F_XBOLD, (20, 20, 22, 255), 0.9)
    bx0, by0, bx1, by1 = box_px(A.LAUNDRY["notice"], W, H)
    d.rectangle((bx0, by0, bx1, by1), fill=rgb((0.93, 0.90, 0.80)))
    paste_text(im, (bx0 + 14, by0 + 20, bx1 - 14, by0 + 90), "PLEASE DO NOT", F_XBOLD, (130, 30, 25, 255), 0.85)
    paste_text(im, (bx0 + 14, by0 + 100, bx1 - 14, by0 + 170), "OVERLOAD MACHINES", F_XBOLD, (130, 30, 25, 255), 0.85)
    paste_text(im, (bx0 + 14, by0 + 200, bx1 - 14, by0 + 250), "Attendant 8am to 8pm", F_REG, (40, 40, 40, 255), 0.9)
    im = grime(im, 31, 0.16, 2.2)
    save(im, "laundry")


# ---------------------------------------------------------------------------
# notice board
# ---------------------------------------------------------------------------


def make_notices():
    W = H = 1024
    cork = pnoise(H, W, 0.5, 41) * 0.2 + pnoise(H, W, 2.5, 42) * 0.15
    arr = np.stack([0.50 + cork, 0.36 + cork * 0.8, 0.22 + cork * 0.6], -1)
    im = to_img(np.clip(arr, 0, 1)).convert("RGBA")
    d = ImageDraw.Draw(im)
    bx0, by0, bx1, by1 = box_px(A.NOTICES["board"], W, H)
    posters = [
        ((0.03, 0.04, 0.36, 0.48), (0.95, 0.94, 0.90), ["HERON REACH", "TENANTS' &", "RESIDENTS'", "MEETING", "Thursday 7pm", "Community Room"]),
        ((0.40, 0.03, 0.66, 0.40), (0.98, 0.86, 0.36), ["BULKY", "WASTE", "Book with the", "Estate Office"]),
        ((0.70, 0.06, 0.97, 0.44), (0.86, 0.90, 0.94), ["YOUTH CLUB", "Football", "Tuesdays 6pm", "The Cage"]),
        ((0.05, 0.54, 0.30, 0.94), (0.94, 0.93, 0.91), ["LOST CAT", "", "", "Ginger, answers", "to Biscuit"]),
        ((0.34, 0.46, 0.62, 0.92), (0.78, 0.88, 0.80), ["HOUSING", "SURGERY", "Every Monday", "10am to 1pm", "Block C office"]),
        ((0.66, 0.50, 0.95, 0.80), (0.95, 0.95, 0.95), ["CCTV IN", "OPERATION", "on this estate"]),
        ((0.68, 0.83, 0.94, 0.98), (0.92, 0.70, 0.62), ["Repairs line", "open 24 hours"]),
    ]
    bw, bh = bx1 - bx0, by1 - by0
    for (fx0, fy0, fx1, fy1), col, lines in posters:
        px0, py0 = bx0 + int(fx0 * bw), by0 + int(fy0 * bh)
        px1, py1 = bx0 + int(fx1 * bw), by0 + int(fy1 * bh)
        d.rectangle((px0 + 4, py0 + 5, px1 + 4, py1 + 5), fill=(30, 22, 14, 255))
        d.rectangle((px0, py0, px1, py1), fill=rgb(col))
        lh = (py1 - py0 - 20) / max(4, len(lines))
        for k, line in enumerate(lines):
            if not line:
                continue
            big = k < 2
            paste_text(im, (px0 + 10, int(py0 + 10 + k * lh), px1 - 10, int(py0 + 10 + (k + 0.85) * lh)), line,
                       F_XBOLD if big else F_REG, (28, 28, 30, 255), 0.85, max_size=int(lh * (1.0 if big else 0.7)))
        if lines[0] == "LOST CAT":
            d.ellipse((px0 + 40, int(py0 + 1.4 * lh), px1 - 40, int(py0 + 3.0 * lh)), fill=rgb((0.80, 0.52, 0.26)))
        # pins
        d.ellipse(((px0 + px1) // 2 - 7, py0 + 3, (px0 + px1) // 2 + 7, py0 + 17), fill=rgb((0.70, 0.18, 0.15)))
    hx0, hy0, hx1, hy1 = box_px(A.NOTICES["header"], W, H)
    d.rectangle((hx0, hy0, hx1, hy1), fill=rgb((0.10, 0.16, 0.24)))
    paste_text(im, (hx0 + 30, hy0 + 18, hx1 - 30, hy1 - 18), "HERON REACH ESTATE  ·  NOTICES", F_DISP, (230, 228, 220, 255), 0.85)
    im = grime(im, 43, 0.20, 2.0)
    save(im, "notices")


# ---------------------------------------------------------------------------
# vehicles
# ---------------------------------------------------------------------------


def make_vehicle():
    W = H = 1024
    im = Image.new("RGBA", (W, H), (24, 24, 25, 255))
    d = ImageDraw.Draw(im)
    for key, col, txt in (("plate_front", (0.92, 0.92, 0.90), "HR18 0NS"), ("plate_rear", (0.92, 0.78, 0.18), "HR18 0NS")):
        bx0, by0, bx1, by1 = box_px(A.VEHICLE[key], W, H)
        d.rectangle((bx0 + 2, by0 + 2, bx1 - 2, by1 - 2), fill=rgb(col), outline=(20, 20, 20, 255), width=3)
        paste_text(im, (bx0 + 26, by0 + 14, bx1 - 26, by1 - 14), txt, F_MONO, (16, 16, 16, 255), 0.8)
    # headlight: dark chrome housing, projector, LED strip
    bx0, by0, bx1, by1 = box_px(A.VEHICLE["headlight"], W, H)
    g = np.linspace(0.18, 0.55, by1 - by0)[:, None] * np.ones((1, bx1 - bx0))
    im.paste(to_img(np.stack([g, g, g * 1.05], -1).clip(0, 1)), (bx0, by0))
    d.ellipse((bx0 + 40, by0 + 60, bx0 + 170, by0 + 190), fill=rgb((0.70, 0.72, 0.74)))
    d.ellipse((bx0 + 70, by0 + 90, bx0 + 140, by0 + 160), fill=rgb((0.12, 0.13, 0.15)))
    d.ellipse((bx0 + 230, by0 + 70, bx0 + 340, by0 + 180), fill=rgb((0.60, 0.62, 0.64)))
    d.line((bx0 + 30, by0 + 34, bx1 - 30, by0 + 26), fill=rgb((0.95, 0.96, 0.96)), width=10)
    # taillight
    bx0, by0, bx1, by1 = box_px(A.VEHICLE["taillight"], W, H)
    d.rectangle((bx0, by0, bx1, by1), fill=rgb((0.42, 0.04, 0.05)))
    for k in range(8):
        d.line((bx0 + 20, by0 + 30 + k * 26, bx1 - 20, by0 + 30 + k * 26), fill=rgb((0.62, 0.08, 0.08)), width=8)
    d.rectangle((bx0 + 20, by1 - 70, bx0 + 150, by1 - 20), fill=rgb((0.80, 0.80, 0.80)))
    d.rectangle((bx1 - 120, by1 - 70, bx1 - 20, by1 - 20), fill=rgb((0.80, 0.42, 0.10)))
    # van lamp stack
    bx0, by0, bx1, by1 = box_px(A.VEHICLE["van_lamp"], W, H)
    hh = (by1 - by0) // 3
    d.rectangle((bx0, by0, bx1, by0 + hh), fill=rgb((0.62, 0.06, 0.06)))
    d.rectangle((bx0, by0 + hh, bx1, by0 + 2 * hh), fill=rgb((0.80, 0.42, 0.10)))
    d.rectangle((bx0, by0 + 2 * hh, bx1, by1), fill=rgb((0.78, 0.78, 0.78)))
    # grille: hex honeycomb
    bx0, by0, bx1, by1 = box_px(A.VEHICLE["grille"], W, H)
    # drawn on its own tile and pasted, so the cells stop at the rect edge
    gt = Image.new(im.mode, (bx1 - bx0, by1 - by0), rgb((0.03, 0.03, 0.03)) + ((255,) if im.mode == "RGBA" else ()))
    gd = ImageDraw.Draw(gt)
    r = 12
    for j in range(-1, (by1 - by0) // r + 2):
        for i in range(-1, (bx1 - bx0) // (2 * r) + 2):
            cx = i * 2 * r + (r if j % 2 else 0)
            cy = j * r * 1.7
            pts = [(cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a)) for a in np.linspace(0, TAU, 7)[:-1] + math.pi / 6]
            gd.polygon(pts, outline=rgb((0.20, 0.20, 0.21)), width=3)
    im.paste(gt, (bx0, by0))
    d.rectangle((bx1, by0, bx1 + 2, by1), fill=(24, 24, 25, 255))
    # alloy wheel face: 10 split spokes on dark recess
    bx0, by0, bx1, by1 = box_px(A.VEHICLE["alloy"], W, H)
    cx, cy, R_ = (bx0 + bx1) / 2, (by0 + by1) / 2, (bx1 - bx0) / 2 - 2
    d.ellipse((cx - R_, cy - R_, cx + R_, cy + R_), fill=rgb((0.22, 0.22, 0.23)))
    d.ellipse((cx - R_ * 0.93, cy - R_ * 0.93, cx + R_ * 0.93, cy + R_ * 0.93), fill=rgb((0.03, 0.03, 0.035)))
    d.ellipse((cx - R_ * 0.55, cy - R_ * 0.55, cx + R_ * 0.55, cy + R_ * 0.55), fill=rgb((0.10, 0.10, 0.11)))
    for k in range(10):
        a = TAU * k / 10
        for off in (-0.07, 0.07):
            a0 = a + off
            p = [(cx + R_ * 0.22 * math.cos(a0 - 0.12), cy + R_ * 0.22 * math.sin(a0 - 0.12)),
                 (cx + R_ * 0.92 * math.cos(a0 - 0.035), cy + R_ * 0.92 * math.sin(a0 - 0.035)),
                 (cx + R_ * 0.92 * math.cos(a0 + 0.035), cy + R_ * 0.92 * math.sin(a0 + 0.035)),
                 (cx + R_ * 0.22 * math.cos(a0 + 0.12), cy + R_ * 0.22 * math.sin(a0 + 0.12))]
            d.polygon(p, fill=rgb((0.30, 0.30, 0.31)))
    d.ellipse((cx - R_ * 0.25, cy - R_ * 0.25, cx + R_ * 0.25, cy + R_ * 0.25), fill=rgb((0.26, 0.26, 0.27)))
    for k in range(5):
        a = TAU * k / 5
        d.ellipse((cx + R_ * 0.15 * math.cos(a) - 7, cy + R_ * 0.15 * math.sin(a) - 7, cx + R_ * 0.15 * math.cos(a) + 7, cy + R_ * 0.15 * math.sin(a) + 7), fill=rgb((0.55, 0.55, 0.56)))
    d.ellipse((cx - R_ * 0.08, cy - R_ * 0.08, cx + R_ * 0.08, cy + R_ * 0.08), fill=rgb((0.12, 0.12, 0.13)))
    # steel wheel face
    bx0, by0, bx1, by1 = box_px(A.VEHICLE["steel_wheel"], W, H)
    cx, cy, R_ = (bx0 + bx1) / 2, (by0 + by1) / 2, (bx1 - bx0) / 2 - 2
    d.ellipse((cx - R_, cy - R_, cx + R_, cy + R_), fill=rgb((0.10, 0.10, 0.10)))
    d.ellipse((cx - R_ * 0.8, cy - R_ * 0.8, cx + R_ * 0.8, cy + R_ * 0.8), fill=rgb((0.16, 0.16, 0.16)))
    for k in range(8):
        a = TAU * k / 8
        hx, hy = cx + R_ * 0.62 * math.cos(a), cy + R_ * 0.62 * math.sin(a)
        d.ellipse((hx - 12, hy - 8, hx + 12, hy + 8), fill=rgb((0.02, 0.02, 0.02)))
    d.ellipse((cx - R_ * 0.3, cy - R_ * 0.3, cx + R_ * 0.3, cy + R_ * 0.3), fill=rgb((0.20, 0.20, 0.20)))
    im = grime(im, 51, 0.14, 2.4)
    save(im, "vehicle")


TAU = math.tau

# ---------------------------------------------------------------------------
# litter and mattress
# ---------------------------------------------------------------------------


def make_litter():
    W = H = 1024
    im = Image.new("RGBA", (W, H), (120, 100, 80, 255))
    d = ImageDraw.Draw(im)
    box = box_px(A.LITTER["crisp"], W, H)
    design_box(im, box, 5, "KRUNCHO", "bag")
    paste_text(im, (box[0] + 60, box[1] + 330, box[2] - 60, box[1] + 400), "SALT & VINEGAR", F_BOLD, (245, 240, 230, 255), 0.85)
    for key, name, seed in (("can", "KORA COLA", 1), ("can2", "VOLTEDGE", 4)):
        box = box_px(A.LITTER[key], W, H)
        design_wrap(im, box, seed, name, "can")
    for key, seed in (("cardboard", 61), ("cardboard2", 62)):
        bx0, by0, bx1, by1 = box_px(A.LITTER[key], W, H)
        n = pnoise(by1 - by0, bx1 - bx0, 2.2, seed)
        base = np.array([0.60, 0.46, 0.30]) * (0.85 + 0.3 * n[..., None])
        fib = pnoise(by1 - by0, bx1 - bx0, 0.4, seed + 1)[..., None] * 0.08
        im.paste(to_img(np.clip(base - fib, 0, 1)), (bx0, by0))
        d = ImageDraw.Draw(im)
        d.rectangle((bx0, by0 + (by1 - by0) // 2 - 22, bx1, by0 + (by1 - by0) // 2 + 22), fill=rgb((0.68, 0.58, 0.40)))
        if seed == 61:
            paste_text(im, (bx0 + 40, by0 + 40, bx1 - 160, by0 + 110), "THIS WAY UP", F_XBOLD, (40, 30, 24, 255), 0.85)
            for k in range(2):
                ax = bx1 - 120 + k * 50
                d.polygon([(ax, by0 + 110), (ax + 18, by0 + 70), (ax + 36, by0 + 110)], fill=(40, 30, 24, 255))
                d.rectangle((ax + 12, by0 + 108, ax + 24, by0 + 140), fill=(40, 30, 24, 255))
            paste_text(im, (bx0 + 40, by1 - 120, bx0 + 300, by1 - 60), "FRAGILE", F_XBOLD, (130, 40, 30, 255), 0.85)
        else:
            paste_text(im, (bx0 + 40, by0 + 50, bx1 - 40, by0 + 140), "24 x 330ml", F_XBOLD, (40, 30, 24, 255), 0.85)
            paste_text(im, (bx0 + 40, by1 - 140, bx1 - 40, by1 - 70), "KORA COLA  ·  KEEP DRY", F_BOLD, (70, 40, 30, 255), 0.85)
        # water stain rings
        for k in range(3):
            cx = bx0 + 80 + k * 140
            cy = by1 - 60 - (k * 53) % 120
            d.ellipse((cx - 50, cy - 40, cx + 50, cy + 40), outline=rgb((0.40, 0.30, 0.20)), width=4)
    im = grime(im, 63, 0.25, 2.0)
    save(im, "litter")

    # mattress: quilted ticking with stains, 1024 x 512 covering the top face
    W, H = 1024, 512
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    q = 56.0
    a = np.abs(((xx + yy) / q) % 1.0 - 0.5)
    b = np.abs(((xx - yy) / q) % 1.0 - 0.5)
    quilt = np.minimum(a, b)
    stitch = np.clip(1.0 - quilt * 30.0, 0, 1)
    puff = np.sqrt(np.clip(quilt * 2, 0, 1))
    stripe = (np.sin(xx / 6.0) * 0.5 + 0.5) * 0.04
    base = np.stack([0.86 - stripe, 0.84 - stripe, 0.78 - stripe * 0.5], -1)
    base *= (0.86 + 0.14 * puff)[..., None]
    base *= (1 - 0.25 * stitch)[..., None]
    st = pnoise(H, W, 2.8, 71)
    stain = np.clip((st - 0.62) * 4.0, 0, 1)
    base = base * (1 - stain[..., None] * 0.5) + np.array([0.55, 0.42, 0.22]) * stain[..., None] * 0.5
    edge = np.minimum(np.minimum(xx, W - xx), np.minimum(yy, H - yy))
    dirt = np.clip(1 - edge / 70.0, 0, 1) * 0.35
    base *= (1 - dirt)[..., None]
    g2 = pnoise(H, W, 1.8, 72)
    base *= (0.9 + 0.1 * g2)[..., None]
    save(to_img(np.clip(base, 0, 1)), "mattress")


# ---------------------------------------------------------------------------
# intercom, cctv, manhole, vents, pegboard, fabric
# ---------------------------------------------------------------------------


def make_intercom():
    W = H = 512
    metal = brushed(H, W, 81, 0.30, 0.10)
    col = np.stack([metal, metal * 0.98, metal * 0.95], -1)
    height = np.zeros((H, W), np.float32)
    px0, py0, px1, py1 = box_px(A.INTERCOM["plate"], W, H)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # bevelled edge of the plate
    edge = np.minimum(np.minimum(xx - px0, px1 - 1 - xx), np.minimum(yy - py0, py1 - 1 - yy))
    inplate = (xx < px1)
    height += np.where(inplate, np.clip(edge / 6.0, 0, 1), 0) * 0.6
    # speaker grille dots in a rounded pattern
    cx, cy = (px0 + px1) / 2, py0 + (py1 - py0) * 0.20
    for j in range(-4, 5):
        for i in range(-5, 6):
            hx, hy = cx + i * 13, cy + j * 11
            if ((i / 5.6) ** 2 + (j / 4.6) ** 2) <= 1.0:
                m = (xx - hx) ** 2 + (yy - hy) ** 2 < 16
                col[m] = 0.03
                height[m] -= 0.8
    # LED slot
    m = (np.abs(xx - cx) < 16) & (np.abs(yy - (py0 + (py1 - py0) * 0.33)) < 4)
    col[m] = (0.05, 0.05, 0.06)
    height[m] -= 0.4
    # screws
    for sx in (px0 + 16, px1 - 16):
        for sy in (py0 + 16, py1 - 16):
            m = (xx - sx) ** 2 + (yy - sy) ** 2 < 49
            col[m] = 0.12
            height[m] += 0.3
    # call button ring area
    by = py0 + (py1 - py0) * 0.86
    m = ((xx - cx) ** 2 + (yy - by) ** 2 < 34 ** 2) & ((xx - cx) ** 2 + (yy - by) ** 2 > 26 ** 2)
    col[m] = (0.06, 0.06, 0.06)
    # wear
    n = pnoise(H, W, 2.4, 82)
    col *= (0.8 + 0.35 * n)[..., None]
    img = to_img(np.clip(col, 0, 1)).convert("RGBA")
    d = ImageDraw.Draw(img)
    paste_text(img, (px0 + 30, int(py0 + (py1 - py0) * 0.40), px1 - 30, int(py0 + (py1 - py0) * 0.43)), "PRESS FLAT NUMBER THEN CALL", F_REG, (190, 190, 186, 255), 0.9)
    # key legends
    labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    for rect, lab in zip(A.INTERCOM["keys"], labels):
        bx0, by0, bx1, by1 = box_px(rect, W, H)
        d.rectangle((bx0, by0, bx1, by1), fill=rgb((0.09, 0.09, 0.10)))
        d.rectangle((bx0 + 3, by0 + 3, bx1 - 3, by1 - 3), outline=rgb((0.16, 0.16, 0.17)), width=2)
        paste_text(img, (bx0 + 22, by0 + 14, bx1 - 22, by1 - 14), lab, F_BOLD, (200, 200, 196, 255), 1.0)
    bx0, by0, bx1, by1 = box_px(A.INTERCOM["label"], W, H)
    d.rectangle((bx0 + 4, by0 + 4, bx1 - 4, by1 - 4), fill=rgb((0.86, 0.85, 0.80)))
    paste_text(img, (bx0 + 14, by0 + 12, bx1 - 14, by0 + 46), "HERON HOUSE", F_XBOLD, (30, 30, 30, 255), 0.85)
    paste_text(img, (bx0 + 14, by0 + 52, bx1 - 14, by1 - 12), "FLATS 1 TO 48", F_BOLD, (30, 30, 30, 255), 0.85)
    save(img, "intercom")
    save(normal_from_height(np.asarray(Image.fromarray((np.clip(height + 1, 0, 2) * 120).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32) / 120.0, 3.0), "intercom", "normal")


def make_cctv():
    W = H = 512
    n = pnoise(H, W, 2.2, 91)
    base = np.stack([0.66 + 0.0 * n, 0.62 + 0.0 * n, 0.54 + 0.0 * n], -1) * (0.85 + 0.25 * n[..., None])
    streak_src = pnoise(H, W, 1.0, 92)
    streak = np.asarray(Image.fromarray((streak_src * 255).astype(np.uint8)).resize((W // 16, H), Image.BILINEAR).resize((W, H), Image.BILINEAR)) / 255.0
    rust = np.clip((streak - 0.6) * 3, 0, 1) * np.clip((pnoise(H, W, 2.0, 93) - 0.4) * 3, 0, 1)
    base = base * (1 - rust[..., None] * 0.6) + np.array([0.36, 0.22, 0.12]) * rust[..., None] * 0.6
    chips = pnoise(H, W, 0.8, 94) > 0.86
    base[chips] = base[chips] * 0.45
    save(to_img(np.clip(base, 0, 1)), "cctv")


def make_manhole():
    W = H = 512
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx = cy = W / 2
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (W / 2)
    ang = np.arctan2(yy - cy, xx - cx)
    h = np.zeros((H, W), np.float32)
    # square frame band
    edge = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
    frame = edge < 26
    h[frame] = 0.6
    # round cover inside the frame with a raised chequer of small studs
    inside = r < 0.86
    stud = ((np.abs(((xx / 18.0) % 1) - 0.5) < 0.22) & (np.abs(((yy / 18.0) % 1) - 0.5) < 0.22))
    h[inside & stud] = 0.5
    ring = (np.abs(r - 0.86) < 0.025) | (np.abs(r - 0.40) < 0.02)
    h[ring] = 0.8
    gap = np.abs(r - 0.885) < 0.012
    h[gap] = -0.6
    centre = r < 0.36
    h[centre] = 0.15
    # raised lettering
    img = Image.new("L", (W, H), 0)
    dd = ImageDraw.Draw(img)
    f = font(F_XBOLD, 60)
    dd.text((cx, cy - 4), "HR  FW", font=f, fill=255, anchor="mm")
    letters = np.asarray(img).astype(np.float32) / 255.0
    h = np.where(centre, 0.15 + letters * 0.5, h)
    h_blur = np.asarray(Image.fromarray(((h + 1) * 100).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 100.0 - 1
    n = pnoise(H, W, 2.2, 101)
    base = 0.11 + 0.08 * n + np.clip(h_blur, 0, 1) * 0.10  # worn high points polish lighter
    rust = np.clip((pnoise(H, W, 1.6, 102) - 0.55) * 3, 0, 1) * (h_blur < 0.2)
    col = np.stack([base + rust * 0.12, base + rust * 0.05, base], -1)
    col[gap] = 0.03
    save(to_img(np.clip(col, 0, 1)), "manhole")
    save(normal_from_height(h_blur, 5.0), "manhole", "normal")


def make_vents():
    W = H = 512
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x0, y0, x1, y1 = box_px(A.VENTS["airbrick"], W, H)
    n = pnoise(H, W, 2.0, 111)
    col = np.stack([0.50 + 0.1 * n, 0.30 + 0.06 * n, 0.22 + 0.04 * n], -1)
    h = np.zeros((H, W), np.float32)
    inside = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    # grid of square holes: 9 x 4
    cols_, rows_ = 9, 4
    cw = (x1 - x0 - 40) / cols_
    rh = (y1 - y0 - 40) / rows_
    for j in range(rows_):
        for i in range(cols_):
            hx0 = x0 + 20 + i * cw + cw * 0.18
            hy0 = y0 + 20 + j * rh + rh * 0.18
            m = (xx >= hx0) & (xx < hx0 + cw * 0.64) & (yy >= hy0) & (yy < hy0 + rh * 0.64)
            col[m] = (0.04, 0.03, 0.03)
            h[m] = -1.0
    edge = np.minimum(np.minimum(xx - x0, x1 - 1 - xx), np.minimum(yy - y0, y1 - 1 - yy))
    h += np.where(inside, np.clip(edge / 8.0, 0, 1) * 0.3, 0)
    g = pnoise(H, W, 2.6, 112)
    col *= (0.75 + 0.3 * g)[..., None]
    save(to_img(np.clip(col, 0, 1)), "vents")
    hb = np.asarray(Image.fromarray(((h + 1) * 100).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 100.0 - 1
    save(normal_from_height(hb, 4.0), "vents", "normal")


def make_pegboard():
    W = H = 512
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    n = pnoise(H, W, 2.0, 121)
    col = np.stack([0.52 + 0.08 * n, 0.40 + 0.06 * n, 0.27 + 0.05 * n], -1)
    pitch = W / 20.0
    d = np.sqrt((((xx / pitch) % 1) - 0.5) ** 2 + (((yy / pitch) % 1) - 0.5) ** 2) * pitch
    hole = d < 3.2
    col[hole] = (0.05, 0.04, 0.03)
    g = pnoise(H, W, 2.8, 122)
    col *= (0.8 + 0.25 * g)[..., None]
    save(to_img(np.clip(col, 0, 1)), "pegboard")


def make_fabric():
    W = H = 512
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    weave = (np.sin(xx * math.pi / 2.0) * np.sin(yy * math.pi / 2.0)) * 0.5 + 0.5
    n = pnoise(H, W, 2.4, 131)
    wear = np.clip((pnoise(H, W, 3.0, 132) - 0.6) * 2.5, 0, 1)
    base = np.array([0.20, 0.22, 0.28])
    col = base * (0.85 + 0.15 * weave[..., None]) * (0.85 + 0.3 * n[..., None])
    col = col * (1 - wear[..., None] * 0.4) + np.array([0.34, 0.34, 0.36]) * wear[..., None] * 0.4
    save(to_img(np.clip(col, 0, 1)), "fabric")


def make_estate_sign():
    """Council-style estate sign: white enamel face, navy header, worn edges."""
    W, H = 512, 384
    im = Image.new("RGBA", (W, H), rgb((0.86, 0.86, 0.83)) + (255,))
    d = ImageDraw.Draw(im)
    navy = rgb((0.07, 0.12, 0.25))
    d.rectangle((0, 0, W, 112), fill=navy)
    paste_text(im, (24, 14, W - 24, 62), "HERON REACH ESTATE", F_XBOLD, rgb((0.95, 0.94, 0.90)) + (255,), 0.86)
    paste_text(im, (40, 70, W - 40, 100), "HERON HOUSE  \u00b7  THE CAGE  \u00b7  ESTATE OFFICE", F_BOLD, rgb((0.80, 0.82, 0.86)) + (255,), 0.9)
    ink = rgb((0.10, 0.10, 0.11)) + (255,)
    paste_text(im, (30, 140, W - 30, 210), "NO BALL GAMES", F_XBOLD, ink, 0.84)
    paste_text(im, (30, 226, W - 30, 276), "NO CYCLING ON FOOTPATHS", F_BOLD, ink, 0.86)
    paste_text(im, (30, 300, W - 30, 336), "By order of the Estate Office", F_BOLD, rgb((0.30, 0.30, 0.32)) + (255,), 0.9)
    d.rectangle((6, 6, W - 7, H - 7), outline=rgb((0.07, 0.12, 0.25)), width=4)
    # fixing holes, rust weeps and a dent of grime toward the bottom
    for (x, y) in ((22, 128), (W - 22, 128), (22, H - 22), (W - 22, H - 22)):
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=rgb((0.35, 0.36, 0.38)))
    im = grime(im, 141, 0.35, 2.2, 0.15)
    arr = np.asarray(im).astype(np.float32) / 255.0
    n = pnoise(H, W, 1.2, 142)
    yy = np.mgrid[0:H, 0:W][0] / H
    weep = np.clip((n - 0.55) * 3.0, 0, 1) * np.clip(yy * 1.4 - 0.2, 0, 1) * 0.35
    arr[..., 0] *= 1 - weep * 0.4
    arr[..., 1] *= 1 - weep * 0.6
    arr[..., 2] *= 1 - weep * 0.8
    save(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGBA"), "estate_sign")


def main():
    wire_mesh("cage_mesh", 1024, 20, 5.0, (0.07, 0.07, 0.075), 1)
    wire_mesh("wire_grid", 1024, 20, 4.0, (0.62, 0.63, 0.64), 2)
    wire_mesh("goal_net", 1024, 10, 6.0, (0.80, 0.80, 0.77), 3, knot=5.0, wobble=10.0)
    make_products()
    make_shop()
    make_laundry()
    make_notices()
    make_vehicle()
    make_litter()
    make_intercom()
    make_cctv()
    make_manhole()
    make_vents()
    make_pegboard()
    make_fabric()
    make_estate_sign()


if __name__ == "__main__":
    main()
