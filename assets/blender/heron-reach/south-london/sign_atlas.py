"""Build the Heron Reach estate sign atlas (colour + layout JSON).

Run: python3 sign_atlas.py OUT_DIR
Writes hr_sign_atlas_color.jpg, hr_sign_atlas_layout.json and hr_decal_numerals.png.
All names and wording are fictional. Fonts: Inter (SIL OFL) and DejaVu Sans (free licence),
rasterised into the texture only.
"""
import json, math, random, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
OUT.mkdir(parents=True, exist_ok=True)
ATLAS = 2048
PX_PER_MM = 0.62
PAD = 8
random.seed(7)
np.random.seed(7)

INTER = "/usr/share/fonts/opentype/inter/"
def font(weight, px):
    return ImageFont.truetype(INTER + f"Inter-{weight}.otf", int(px))

NAVY = (24, 38, 66)
WHITE = (236, 236, 230)
RED = (190, 30, 36)
YELLOW = (240, 196, 24)
GREEN = (0, 132, 80)
BLUE = (22, 74, 150)
BLACK = (22, 22, 22)

# --- pictograms -----------------------------------------------------------------
def heron(d, x, y, s, col):
    """Simple standing heron mark in a box of size s at x, y."""
    w = max(2, int(s * 0.035))
    pts = [(0.62, 0.95), (0.6, 0.62)]
    d.line([(x + px * s, y + py * s) for px, py in pts], fill=col, width=w)
    d.line([(x + 0.52 * s, y + 0.95 * s), (x + 0.56 * s, y + 0.62 * s)], fill=col, width=w)
    d.polygon([(x + 0.4 * s, y + 0.44 * s), (x + 0.58 * s, y + 0.4 * s), (x + 0.92 * s, y + 0.58 * s),
               (x + 0.66 * s, y + 0.64 * s), (x + 0.5 * s, y + 0.6 * s)], fill=col)
    neck = [(0.45, 0.48), (0.36, 0.36), (0.42, 0.22), (0.36, 0.12)]
    d.line([(x + px * s, y + py * s) for px, py in neck], fill=col, width=w, joint="curve")
    d.ellipse([x + 0.31 * s, y + 0.07 * s, x + 0.41 * s, y + 0.15 * s], fill=col)
    d.polygon([(x + 0.33 * s, y + 0.1 * s), (x + 0.12 * s, y + 0.14 * s), (x + 0.33 * s, y + 0.13 * s)], fill=col)

def ball(d, cx, cy, r, col):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=max(2, r // 7))
    d.polygon([(cx, cy - r * 0.35), (cx + r * 0.33, cy - r * 0.1), (cx + r * 0.2, cy + r * 0.3),
               (cx - r * 0.2, cy + r * 0.3), (cx - r * 0.33, cy - r * 0.1)], fill=col)

def prohibit(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=RED, width=max(3, r // 6))
    k = r * 0.7
    d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=RED, width=max(3, r // 6))

def dog(d, x, y, s, col):
    d.ellipse([x + 0.2 * s, y + 0.35 * s, x + 0.75 * s, y + 0.6 * s], fill=col)
    d.ellipse([x + 0.65 * s, y + 0.2 * s, x + 0.9 * s, y + 0.42 * s], fill=col)
    d.polygon([(x + 0.85 * s, y + 0.3 * s), (x + 0.98 * s, y + 0.36 * s), (x + 0.85 * s, y + 0.4 * s)], fill=col)
    for lx in (0.25, 0.35, 0.6, 0.7):
        d.rectangle([x + lx * s, y + 0.5 * s, x + (lx + 0.06) * s, y + 0.85 * s], fill=col)
    d.line([(x + 0.22 * s, y + 0.42 * s), (x + 0.08 * s, y + 0.28 * s)], fill=col, width=max(2, int(s * 0.05)))

def camera(d, x, y, s, col):
    d.polygon([(x + 0.1 * s, y + 0.35 * s), (x + 0.7 * s, y + 0.2 * s), (x + 0.78 * s, y + 0.45 * s),
               (x + 0.18 * s, y + 0.6 * s)], fill=col)
    d.rectangle([x + 0.62 * s, y + 0.45 * s, x + 0.7 * s, y + 0.85 * s], fill=col)
    d.rectangle([x + 0.5 * s, y + 0.82 * s, x + 0.9 * s, y + 0.9 * s], fill=col)

def bolt(d, x, y, s, col):
    d.polygon([(x + 0.55 * s, y + 0.05 * s), (x + 0.25 * s, y + 0.55 * s), (x + 0.48 * s, y + 0.55 * s),
               (x + 0.38 * s, y + 0.95 * s), (x + 0.75 * s, y + 0.4 * s), (x + 0.52 * s, y + 0.4 * s)], fill=col)

def runner(d, x, y, s, col):
    w = max(3, int(s * 0.11))
    d.ellipse([x + 0.5 * s, y, x + 0.68 * s, y + 0.18 * s], fill=col)
    d.line([(x + 0.55 * s, y + 0.25 * s), (x + 0.42 * s, y + 0.6 * s)], fill=col, width=w)
    d.line([(x + 0.42 * s, y + 0.6 * s), (x + 0.62 * s, y + 0.78 * s), (x + 0.6 * s, y + 0.98 * s)], fill=col, width=w)
    d.line([(x + 0.42 * s, y + 0.6 * s), (x + 0.22 * s, y + 0.8 * s), (x + 0.05 * s, y + 0.78 * s)], fill=col, width=w)
    d.line([(x + 0.55 * s, y + 0.28 * s), (x + 0.78 * s, y + 0.45 * s), (x + 0.9 * s, y + 0.35 * s)], fill=col, width=w)
    d.line([(x + 0.53 * s, y + 0.3 * s), (x + 0.32 * s, y + 0.35 * s), (x + 0.22 * s, y + 0.5 * s)], fill=col, width=w)

def bike(d, cx, cy, r, col):
    w = max(2, r // 9)
    d.ellipse([cx - r, cy, cx - r * 0.1, cy + r * 0.9], outline=col, width=w)
    d.ellipse([cx + r * 0.1, cy, cx + r, cy + r * 0.9], outline=col, width=w)
    d.line([(cx - r * 0.55, cy + r * 0.45), (cx - r * 0.1, cy - r * 0.1), (cx + r * 0.4, cy - r * 0.1),
            (cx + r * 0.55, cy + r * 0.45), (cx, cy + r * 0.45), (cx - r * 0.55, cy + r * 0.45)], fill=col, width=w)
    d.line([(cx, cy + r * 0.45), (cx - r * 0.1, cy - r * 0.1)], fill=col, width=w)

def arrow(d, x, y, s, col, direction="right"):
    w = max(3, int(s * 0.16))
    if direction == "right":
        d.line([(x, y + s / 2), (x + s * 0.8, y + s / 2)], fill=col, width=w)
        d.polygon([(x + s, y + s / 2), (x + s * 0.6, y + s * 0.15), (x + s * 0.6, y + s * 0.85)], fill=col)
    else:
        d.line([(x + s / 2, y + s), (x + s / 2, y + s * 0.2)], fill=col, width=w)
        d.polygon([(x + s / 2, y), (x + s * 0.15, y + s * 0.4), (x + s * 0.85, y + s * 0.4)], fill=col)

def text_c(d, cx, y, s, f, col):
    w = d.textlength(s, font=f)
    d.text((cx - w / 2, y), s, font=f, fill=col)

def fit(d, s, weight, max_w, start_px):
    px = start_px
    while px > 6 and d.textlength(s, font=font(weight, px)) > max_w:
        px -= 1
    return font(weight, px)

# --- sign designs (each draws into an RGB image of its own pixel size) -----------
def border(d, w, h, col, t):
    d.rectangle([0, 0, w - 1, h - 1], outline=col, width=t)

def sign_estate_board(img):
    d = ImageDraw.Draw(img); w, h = img.size
    d.rectangle([0, 0, w, h * 0.3], fill=NAVY)
    heron(d, w * 0.03, h * 0.02, h * 0.26, WHITE)
    d.text((w * 0.2, h * 0.06), "HERON REACH ESTATE", font=fit(d, "HERON REACH ESTATE", "Bold", w * 0.76, h * 0.16), fill=WHITE)
    f = font("SemiBold", h * 0.075)
    rows = ["Rowan House  1 – 48", "Ash House  1 – 48", "Birch House  1 – 48", "Cedar House  1 – 48"]
    for i, r in enumerate(rows):
        d.text((w * 0.05, h * (0.36 + i * 0.1)), r, font=f, fill=NAVY)
        arrow(d, w * 0.5, h * (0.37 + i * 0.1), h * 0.07, NAVY, "right" if i % 2 else "up")
    d.line([(w * 0.6, h * 0.36), (w * 0.6, h * 0.76)], fill=NAVY, width=3)
    fs = font("Medium", h * 0.055)
    for i, r in enumerate(["Garden Court", "The Cage", "Washhouse Square", "Estate office: Unit 3"]):
        d.text((w * 0.63, h * (0.37 + i * 0.1)), r, font=fs, fill=NAVY)
    d.rectangle([0, h * 0.84, w, h], fill=NAVY)
    d.text((w * 0.05, h * 0.87), "Repairs  0800 000 0000   Out of hours  0800 000 0001", font=font("Medium", h * 0.06), fill=WHITE)
    border(d, w, h, NAVY, 4)

def sign_block(name, flats, direction):
    def draw(img):
        d = ImageDraw.Draw(img); w, h = img.size
        d.rectangle([0, 0, h * 0.95, h], fill=NAVY)
        heron(d, h * 0.08, h * 0.08, h * 0.8, WHITE)
        d.text((h * 1.1, h * 0.08), name, font=fit(d, name, "Bold", w - h * 1.6, h * 0.42), fill=NAVY)
        d.text((h * 1.1, h * 0.58), flats, font=fit(d, flats, "SemiBold", w - h * 1.95, h * 0.28), fill=NAVY)
        arrow(d, w - h * 0.62, h * 0.55, h * 0.36, NAVY, direction)
        border(d, w, h, NAVY, 3)
    return draw

def sign_text(lines, fg, bg, pict=None, weights=None, border_col=None):
    def draw(img):
        d = ImageDraw.Draw(img); w, h = img.size
        d.rectangle([0, 0, w, h], fill=bg)
        top = 0.06 * h
        if pict and lines == [""]:
            ph = h * 0.86
            pict(d, w / 2 - ph / 2, h * 0.07, ph)
            border(d, w, h, border_col or fg, max(3, int(min(w, h) * 0.03)))
            return
        if pict:
            ph = h * 0.42
            pict(d, w / 2 - ph / 2, top, ph)
            top += ph + h * 0.04
        avail = h - top - h * 0.06
        lh = avail / len(lines)
        for i, ln in enumerate(lines):
            wt = (weights or ["Bold"] * len(lines))[i]
            f = fit(d, ln, wt, w * 0.88, lh * 0.8)
            text_c(d, w / 2, top + i * lh + (lh - f.size) * 0.35, ln, f, fg)
        border(d, w, h, border_col or fg, max(3, int(min(w, h) * 0.03)))
    return draw

def p_noball(d, x, y, s):
    ball(d, x + s / 2, y + s / 2, int(s * 0.3), BLACK); prohibit(d, x + s / 2, y + s / 2, int(s * 0.47))
def p_nodog(d, x, y, s):
    dog(d, x + s * 0.15, y + s * 0.1, s * 0.7, BLACK); prohibit(d, x + s / 2, y + s / 2, int(s * 0.47))
def p_dog(d, x, y, s):
    dog(d, x + s * 0.1, y + s * 0.05, s * 0.8, BLACK)
def p_camera(d, x, y, s):
    camera(d, x + s * 0.1, y + s * 0.05, s * 0.85, BLACK)
def p_nobike(d, x, y, s):
    d.ellipse([x + s * 0.03, y + s * 0.03, x + s * 0.97, y + s * 0.97], outline=RED, width=max(4, int(s * 0.1)))
    bike(d, x + s / 2, y + s * 0.3, int(s * 0.3), BLACK)
def p_flytip(d, x, y, s):
    d.rectangle([x + s * 0.2, y + s * 0.45, x + s * 0.55, y + s * 0.8], fill=BLACK)
    d.ellipse([x + s * 0.5, y + s * 0.5, x + s * 0.8, y + s * 0.82], fill=BLACK)
    prohibit(d, x + s / 2, y + s / 2, int(s * 0.47))

def sign_danger(img):
    d = ImageDraw.Draw(img); w, h = img.size
    d.rectangle([0, 0, w, h], fill=WHITE)
    tri = [(w / 2, h * 0.05), (w * 0.92, h * 0.55), (w * 0.08, h * 0.55)]
    d.polygon(tri, fill=YELLOW, outline=BLACK, width=6)
    bolt(d, w * 0.36, h * 0.18, h * 0.33, BLACK)
    d.text((w * 0.08, h * 0.6), "DANGER OF DEATH", font=fit(d, "DANGER OF DEATH", "Black", w * 0.84, h * 0.13), fill=BLACK)
    d.text((w * 0.08, h * 0.78), "Keep out", font=fit(d, "Keep out", "Bold", w * 0.84, h * 0.13), fill=BLACK)
    border(d, w, h, BLACK, 4)

def sign_fire_exit(img):
    d = ImageDraw.Draw(img); w, h = img.size
    d.rectangle([0, 0, w, h], fill=GREEN)
    runner(d, w * 0.05, h * 0.12, h * 0.76, WHITE)
    d.rectangle([w * 0.3, h * 0.15, w * 0.42, h * 0.85], outline=WHITE, width=4)
    arrow(d, w * 0.5, h * 0.25, h * 0.5, WHITE)
    d.text((w * 0.68, h * 0.25), "EXIT", font=fit(d, "EXIT", "Bold", w * 0.29, h * 0.42), fill=WHITE)

def sign_fire_door(img):
    d = ImageDraw.Draw(img); w, h = img.size
    d.rectangle([0, 0, w, h], fill=WHITE)
    d.ellipse([w * 0.06, h * 0.06, w * 0.94, h * 0.94], fill=BLUE)
    for i, ln in enumerate(["FIRE DOOR", "KEEP SHUT"]):
        f = fit(d, ln, "Bold", w * 0.62, h * 0.14)
        text_c(d, w / 2, h * (0.32 + i * 0.2), ln, f, WHITE)

def sign_level(label):
    def draw(img):
        d = ImageDraw.Draw(img); w, h = img.size
        d.rectangle([0, 0, w, h], fill=WHITE)
        f = fit(d, label, "Black", w * 0.8, h * 0.8)
        text_c(d, w / 2, h * 0.02, label, f, NAVY)
        border(d, w, h, NAVY, 4)
    return draw

def sign_handwritten(lines):
    def draw(img):
        d = ImageDraw.Draw(img); w, h = img.size
        d.rectangle([0, 0, w, h], fill=(225, 220, 205))
        px = int(h / (len(lines) + 1))
        widest = max(lines, key=len)
        while px > 8 and d.textlength(widest, font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", px)) > w * 0.86:
            px -= 1
        f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", px)
        for i, ln in enumerate(lines):
            d.text((w * 0.06 + random.randint(-4, 4), h * 0.1 + i * h / (len(lines) + 0.6)), ln, font=f, fill=(25, 25, 30))
    return draw

def notice_board(img):
    d = ImageDraw.Draw(img); w, h = img.size
    d.rectangle([0, 0, w, h], fill=(150, 120, 80))
    papers = [("RESIDENTS' ASSOCIATION", "Meeting Thursday 7pm\nCommunity room"), ("LIFT OUT OF SERVICE", "Rowan House lift B\nEngineer booked"),
              ("BULKY WASTE", "Collection: first Monday\nof the month"), ("MISSING CAT", "Answers to Biscuit\nPlease call"),
              ("BIN STORE", "Do not leave bags\noutside the store"), ("FIRE SAFETY", "Keep landings clear")]
    for i, (t, b) in enumerate(papers):
        cx, cy = i % 3, i // 3
        x0 = w * (0.04 + cx * 0.32) + random.randint(-6, 6); y0 = h * (0.05 + cy * 0.48) + random.randint(-6, 6)
        pw, ph = w * 0.28, h * 0.42
        col = (240, 238, 228) if i != 1 else (250, 232, 120)
        d.rectangle([x0, y0, x0 + pw, y0 + ph], fill=col)
        d.text((x0 + pw * 0.06, y0 + ph * 0.08), t, font=fit(d, t, "Bold", pw * 0.88, ph * 0.13), fill=BLACK)
        d.multiline_text((x0 + pw * 0.06, y0 + ph * 0.35), b, font=font("Regular", ph * 0.09), fill=(40, 40, 40), spacing=4)
        d.ellipse([x0 + pw / 2 - 4, y0 + 2, x0 + pw / 2 + 4, y0 + 10], fill=RED)

def door_number(n):
    def draw(img):
        d = ImageDraw.Draw(img); w, h = img.size
        d.rectangle([0, 0, w, h], fill=(190, 160, 70))
        text_c(d, w / 2, h * 0.08, str(n), fit(d, str(n), "Bold", w * 0.8, h * 0.8), BLACK)
    return draw

# id, size mm (w, h), draw fn, kind, note
SIGNS = [
    ("estate_board", (1800, 900), sign_estate_board, "post2", "Estate name board at each vehicle and footpath entrance"),
    ("block_rowan", (900, 300), sign_block("ROWAN HOUSE", "Flats 1 – 48", "up"), "wall", "Beside Rowan House entrances"),
    ("block_alder", (900, 300), sign_block("ALDER HOUSE", "Flats 13 – 23", "right"), "wall", "Alder House; deliberately missing 1 to 12, a real estate quirk"),
    ("block_ash", (900, 300), sign_block("ASH HOUSE", "Flats 1 – 48", "right"), "wall", "Ash House entrances (NE block)"),
    ("block_cedar", (900, 300), sign_block("CEDAR HOUSE", "Flats 1 – 48", "up"), "wall", "Cedar House entrances (SE block)"),
    ("block_birch", (900, 300), sign_block("BIRCH HOUSE", "Flats 1 – 36", "right"), "wall", "Birch House entrance"),
    ("block_maple", (900, 300), sign_block("MAPLE COURT", "Flats 1 – 120", "up"), "wall", "Point block lobby"),
    ("no_ball_games", (450, 300), sign_text(["NO BALL GAMES"], RED, WHITE), "wall", "Classic; walls facing grass and windows"),
    ("no_ball_games_please", (450, 300), sign_text(["Please do not play", "ball games here"], BLACK, WHITE, p_noball, ["SemiBold", "SemiBold"], RED), "wall", "Newer softer wording"),
    ("no_dogs_please", (450, 300), sign_text(["Please be a good neighbour,", "do not walk dogs here"], BLACK, WHITE, p_nodog, ["SemiBold", "SemiBold"], RED), "post1", "Grass and play areas"),
    ("dog_fouling", (300, 400), sign_text(["DOG FOULING", "IS AN OFFENCE", "Maximum penalty £1,000"], BLACK, WHITE, p_dog, ["Black", "Bold", "Medium"], RED), "post1", "Lamp posts and grass edges"),
    ("no_fly_tipping", (600, 400), sign_text(["NO FLY TIPPING", "Offenders will be prosecuted"], RED, WHITE, p_flytip, ["Black", "SemiBold"]), "wall", "Bin stores, garage forecourts, dark corners"),
    ("private_parking", (600, 450), sign_text(["PRIVATE PROPERTY", "Residents parking only", "Unauthorised vehicles", "will be clamped"], WHITE, BLUE, None, ["Black", "SemiBold", "Medium", "Medium"], WHITE), "post1", "Car park and garage entrances"),
    ("cctv", (300, 400), sign_text(["CCTV", "IN OPERATION", "Images recorded for", "community safety"], BLACK, YELLOW, p_camera, ["Black", "Bold", "Medium", "Medium"]), "wall", "Lobbies, shops, car park"),
    ("anti_climb", (300, 100), sign_text(["WARNING", "ANTI-CLIMB PAINT"], BLACK, YELLOW, None, ["Black", "Bold"]), "wall", "Tops of low walls, garage roofs, downpipes"),
    ("danger_of_death", (200, 250), sign_danger, "wall", "Substation doors and palisade fence"),
    ("no_cycling", (300, 300), sign_text([""], BLACK, WHITE, p_nobike), "post1", "Footpaths and walkways"),
    ("fire_exit", (300, 150), sign_fire_exit, "wall", "Over stair doors"),
    ("fire_door", (150, 150), sign_fire_door, "wall", "On every stair and lobby fire door"),
    ("dry_riser", (250, 150), sign_text(["DRY RISER", "INLET"], WHITE, RED, None, ["Black", "Black"]), "wall", "Block wall at ground level near entrance"),
    ("bins_tuesday", (300, 200), sign_text(["BINS COLLECTED", "TUESDAY", "Bags inside the store please"], NAVY, WHITE, None, ["Bold", "Black", "Medium"]), "wall", "Bin store gate"),
    ("garage_to_let", (400, 250), sign_handwritten(["GARAGE", "TO LET", "07700 900000"]), "wall", "Lock-up garage doors (handwritten board)"),
    ("no_parking_garage", (500, 200), sign_handwritten(["NO PARKING", "IN FRONT OF GARAGE"]), "wall", "Garage doors (handwritten)"),
    ("max_headroom", (900, 300), sign_text(["MAX HEADROOM 2.1 m"], BLACK, YELLOW, None, ["Black"]), "beam", "Height barrier at the car park entrance"),
    ("close_the_door", (210, 297), sign_text(["Please close", "the door", "behind you", "Thank you"], BLACK, WHITE, None, ["Bold", "Bold", "Bold", "Medium"], (200, 200, 200)), "wall", "Laminated A4 taped inside lobby doors"),
    ("level_g", (200, 200), sign_level("G"), "wall", "Small level plate by lift and stair doors"),
    ("level_1", (200, 200), sign_level("1"), "wall", "Small level plate"),
    ("level_2", (200, 200), sign_level("2"), "wall", "Small level plate"),
    ("level_3", (200, 200), sign_level("3"), "wall", "Small level plate"),
    ("notice_board_paper", (900, 600), notice_board, "insert", "Paper layer behind glass of the main build's notice board"),
    ("door_number_12", (90, 120), door_number(12), "wall", "Brass flat number, example"),
    ("door_number_27", (90, 120), door_number(27), "wall", "Brass flat number, example"),
]

# --- weathering -----------------------------------------------------------------
def blur_noise(w, h, scale):
    small = np.random.rand(max(2, h // scale), max(2, w // scale)).astype(np.float32)
    return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), dtype=np.float32) / 255

def weather(img, strength, tag=False):
    w, h = img.size
    a = np.asarray(img, dtype=np.float32) / 255
    fade = blur_noise(w, h, 60) * 0.1 * strength
    a = a * (1 - fade[..., None]) + fade[..., None] * np.array([0.82, 0.8, 0.74])
    grime = np.clip(blur_noise(w, h, 40) * 0.6 + blur_noise(w, h, 6) * 0.4 - 0.55, 0, 1) * 0.45 * strength
    streak = np.zeros((h, w), np.float32)
    for _ in range(int(6 * strength) + 1):
        x = random.randint(0, w - 1); width = random.randint(2, max(3, w // 30)); ln = random.uniform(0.2, 0.9)
        col = np.linspace(1, 0, int(h * ln)) * random.uniform(0.06, 0.2)
        streak[: len(col), max(0, x - width): x + width] += col[:, None]
    edge = np.ones((h, w), np.float32)
    m = max(4, min(w, h) // 25)
    edge[m:-m, m:-m] = 0
    edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(m)), np.float32) / 255
    dirt = np.clip(grime + streak * strength + edge * 0.4 * strength, 0, 0.8)
    a = a * (1 - dirt[..., None]) + dirt[..., None] * np.array([0.22, 0.2, 0.16])
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    d = ImageDraw.Draw(out)
    for _ in range(int(10 * strength)):
        x0, y0 = random.randint(0, w), random.randint(0, h)
        d.line([(x0, y0), (x0 + random.randint(-w // 4, w // 4), y0 + random.randint(-h // 10, h // 10))], fill=(200, 200, 195), width=1)
    if tag:
        col = random.choice([(15, 15, 15), (170, 170, 175), (120, 20, 120)])
        x, y = random.uniform(0.55, 0.7) * w, random.uniform(0.7, 0.85) * h
        pts = []
        for i in range(random.randint(7, 11)):
            x += random.uniform(0.012, 0.03) * w; y += random.uniform(-0.07, 0.07) * h
            pts.append((x, min(max(y, 0.55 * h), 0.95 * h)))
        d.line(pts, fill=col, width=max(2, h // 70), joint="curve")
        d.line([(pts[0][0], pts[-1][1] + h * 0.06), (pts[-1][0], pts[-1][1] + h * 0.04)], fill=col, width=max(2, h // 60))
    return out

# --- pack -----------------------------------------------------------------------
atlas = Image.new("RGB", (ATLAS, ATLAS), (128, 128, 128))
layout = {"atlas": "hr_sign_atlas_color.jpg", "size": ATLAS, "px_per_mm": PX_PER_MM, "signs": {}}
order = sorted(SIGNS, key=lambda s: -s[1][1])
x = y = PAD; shelf = 0
for sid, (wmm, hmm), fn, kind, note in order:
    pw, ph = int(wmm * PX_PER_MM), int(hmm * PX_PER_MM)
    if max(pw, ph) < 90:
        pw, ph = int(pw * 2), int(ph * 2)
    if x + pw + PAD > ATLAS:
        x = PAD; y += shelf + PAD; shelf = 0
    assert y + ph + PAD <= ATLAS, f"atlas full at {sid}"
    im = Image.new("RGB", (pw * 2, ph * 2), WHITE)
    fn(im)
    im = im.resize((pw, ph), Image.LANCZOS)
    tagged = sid in ("no_ball_games", "estate_board", "block_alder", "cctv", "no_fly_tipping")
    im = weather(im, 1.0 if kind != "insert" else 0.4, tag=tagged)
    atlas.paste(im, (x, y))
    layout["signs"][sid] = {"size_m": [wmm / 1000, hmm / 1000], "mount": kind, "note": note,
                            "uv": [x / ATLAS, 1 - (y + ph) / ATLAS, (x + pw) / ATLAS, 1 - y / ATLAS]}
    x += pw + PAD; shelf = max(shelf, ph)
atlas.save(OUT / "hr_sign_atlas_color.jpg", quality=90)
(OUT / "hr_sign_atlas_layout.json").write_text(json.dumps(layout, indent=2))
print("atlas used height", y + shelf, "of", ATLAS)

# --- painted level numerals (decal, alpha) ------------------------------------------
labels = ["G", "1", "2", "3", "4", "B1", "G1", "R"]
cell = 512
dec = Image.new("RGBA", (cell * 4, cell * 2), (0, 0, 0, 0))
for i, lb in enumerate(labels):
    im = Image.new("L", (cell, cell), 0)
    d = ImageDraw.Draw(im)
    f = fit(d, lb, "Black", cell * 0.86, cell * 0.92)
    text_c(d, cell / 2, cell * 0.0, lb, f, 255)
    # stencil bridges
    for bx in range(cell // 6, cell, cell // 3):
        d.rectangle([bx - 3, 0, bx + 3, cell], fill=0) if lb in ("B1", "G1") else None
    n = blur_noise(cell, cell, 6)
    a = np.asarray(im, np.float32) / 255 * np.clip(0.8 + (blur_noise(cell, cell, 40) - 0.5) * 0.5 + (n - 0.5) * 0.25, 0, 1)
    rgba = np.zeros((cell, cell, 4), np.uint8)
    rgba[..., :3] = (30, 30, 34); rgba[..., 3] = (a * 235).astype(np.uint8)
    dec.paste(Image.fromarray(rgba, "RGBA"), ((i % 4) * cell, (i // 4) * cell))
dec.save(OUT / "hr_decal_level_numerals.png", optimize=True)
print("done")
