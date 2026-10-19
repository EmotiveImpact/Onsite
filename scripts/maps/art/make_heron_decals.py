"""Procedural decals, lit-window interiors and the distant tower facade for Heron Reach.

Run after make_heron_textures.py (the tower facade reuses hr_concrete_cast-color.webp):
    python3 scripts/maps/art/make_heron_decals.py
Writes public/materials/heron/{decals,windows,backdrop}/ and merges records into
assets/blender/heron-reach/materials-manifest.json. Everything is drawn here with numpy
and Pillow; there is no source photograph or download behind any of these maps.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from heron_tex_common import (OUT, REPO, SCRATCH, blur_reflect, blur_wrap, height_to_normal,
                              lin_to_srgb, norm01, periodic_noise, resize, save_png, save_webp,
                              seam_ratio, seam_ratio_phase, sha256, smoothstep, srgb_to_lin, write_json)

MANIFEST = REPO / "assets/blender/heron-reach/materials-manifest.json"
DEC = OUT / "decals"
WIN = OUT / "windows"
BACK = OUT / "backdrop"
records = []


def rec(path, kind, size_m, how, extra=None, seam=None):
    p = Path(path)
    im = Image.open(p)
    r = {"path": str(p.relative_to(REPO)), "kind": kind, "pixels": list(im.size), "mode": im.mode,
         "bytes": p.stat().st_size, "sha256": sha256(p), "physicalSizeMetres": size_m,
         "source": "procedural (original, this script)", "processing": how}
    if seam is not None:
        r["seamRatio"] = seam
    if extra:
        r.update(extra)
    records.append(r)


def rgba(col_srgb, alpha):
    """col_srgb: (h,w,3) or (3,), alpha: (h,w)."""
    h, w = alpha.shape
    c = np.broadcast_to(np.asarray(col_srgb, np.float32), (h, w, 3)) if np.ndim(col_srgb) == 1 else col_srgb
    return np.concatenate([c, alpha[..., None]], axis=2)


def edge_fade(h, w, margin):
    y = np.minimum(np.arange(h) + 0.5, h - np.arange(h) - 0.5)[:, None]
    x = np.minimum(np.arange(w) + 0.5, w - np.arange(w) - 0.5)[None, :]
    return (smoothstep(0, margin, y) * smoothstep(0, margin, x)).astype(np.float32)


# ============================================================ decals
def rain_streaks():
    H, W = 1024, 512  # 1.0 m tall x 0.5 m wide, tiles horizontally under long sills
    rng = np.random.default_rng(7)
    x = np.arange(W)
    inten = np.zeros(W)
    length = np.zeros(W)
    # 1D periodic noise for streak strength and length
    for s, a in ((40, 1.0), (14, 0.6), (5, 0.35)):
        n = rng.standard_normal(W)
        n = np.real(np.fft.ifft(np.fft.fft(n) * np.exp(-2 * (np.pi * np.fft.fftfreq(W) * s) ** 2)))
        n -= n.mean()
        inten += a * n / (n.std() + 1e-9)
    inten = smoothstep(-0.9, 1.3, inten)
    ln = rng.standard_normal(W)
    ln = np.real(np.fft.ifft(np.fft.fft(ln) * np.exp(-2 * (np.pi * np.fft.fftfreq(W) * 9) ** 2)))
    length = 0.25 + 0.6 * norm01(ln[None, :])[0]
    y = (np.arange(H) + 0.5)[:, None] / H
    fall = np.exp(-y / (length[None, :] * 0.55)) * smoothstep(1.0, 0.75, y / (length[None, :] * 1.25 + 0.05))
    head = smoothstep(0.0, 0.02, y)  # starts just under the sill drip line
    fine = periodic_noise(H, W, 6, 9, octaves=3, aniso=12.0)
    alpha = inten[None, :] * fall * head * (0.65 + 0.5 * fine)
    alpha = blur_wrap(alpha.astype(np.float32), 0.8, 2.5)
    # darker drip tips
    tip = np.exp(-((y - length[None, :] * 0.8) / 0.03) ** 2) * inten[None, :] * 0.25
    alpha = np.clip(alpha * 0.85 + tip * (fine > 0.55), 0, 0.85)
    alpha *= smoothstep(1.0, 0.92, y)  # clean bottom edge
    col = np.stack([0.20 + 0.03 * fine, 0.19 + 0.03 * fine, 0.17 + 0.02 * fine], -1)
    p = save_webp(rgba(col, alpha.astype(np.float32)), DEC / "rain-streaks.webp", 90)
    rec(p, "decal", [0.5, 1.0], ["1D periodic noise for streak strength and length across the sill",
                                 "exponential fall-off downward, vertical anisotropic fine noise, darker drip tips",
                                 "alpha only carries the stain; colour is dark grey-brown"],
        {"tiles": "horizontally", "alphaMode": "BLEND"}, seam=round(seam_ratio(alpha)[0], 3))


def grime():
    N = 1024
    n1 = periodic_noise(N, N, 260, 13, octaves=6, persistence=0.6)
    n2 = periodic_noise(N, N, 40, 17, octaves=4)
    a = smoothstep(0.45, 0.8, n1 * 0.75 + n2 * 0.25)
    rad = np.hypot(*(np.mgrid[0:N, 0:N] - N / 2 + 0.5)) / (N / 2)
    a = a * smoothstep(1.0, 0.55, rad + 0.25 * (n2 - 0.5))
    a = np.clip(a * 0.8, 0, 0.8).astype(np.float32)
    col = np.stack([0.17 + 0.06 * n2, 0.15 + 0.05 * n2, 0.12 + 0.03 * n2], -1)
    p = save_webp(rgba(col, a), DEC / "grime.webp", 90)
    rec(p, "decal", [1.5, 1.5], ["fractal periodic noise thresholded into soft blotches", "noisy radial fade so it sits anywhere"],
        {"alphaMode": "BLEND"})


def moss_edge():
    H, W = 1024, 1024  # 1 m wide, tiles horizontally; base of wall / kerb
    n1 = periodic_noise(H, W, 120, 23, octaves=5)
    n2 = periodic_noise(H, W, 18, 29, octaves=4)
    n3 = periodic_noise(H, W, 6, 31, octaves=2)
    y = (np.arange(H) + 0.5)[:, None] / H  # 0 top, 1 bottom
    up = 1.0 - y
    reach = 0.22 + 0.30 * n1  # how far up the moss climbs
    dense = smoothstep(reach * 0.2, reach * 0.9, up)  # solid at the very bottom, broken higher up
    moss = smoothstep(reach + 0.08, reach - 0.08, up) * smoothstep(0.2 + 0.25 * dense, 0.45 + 0.2 * dense, n2 * 0.7 + n3 * 0.3)
    algae = smoothstep(reach * 1.6 + 0.1, reach * 0.6, up) * 0.35 * (0.6 + 0.4 * n2)
    a = np.clip(np.maximum(moss, algae), 0, 1).astype(np.float32)
    moss_c = np.array([0.24, 0.27, 0.12])
    algae_c = np.array([0.13, 0.16, 0.10])
    m = (moss / (moss + algae + 1e-4))[..., None]
    col = moss_c * m + algae_c * (1 - m)
    col = col * (0.75 + 0.5 * n3[..., None])
    p = save_webp(rgba(col.astype(np.float32), a), DEC / "moss-edge.webp", 90)
    rec(p, "decal", [1.0, 1.0], ["moss clumps from thresholded periodic noise climbing a noisy height from the bottom edge",
                                 "dark green-black algae wash above the moss"],
        {"tiles": "horizontally", "alphaMode": "BLEND"}, seam=round(seam_ratio(a)[0], 3))


def puddle():
    N = 1024
    yy, xx = (np.mgrid[0:N, 0:N] + 0.5) / N - 0.5
    n1 = periodic_noise(N, N, 300, 41, octaves=5)
    n2 = periodic_noise(N, N, 60, 43, octaves=3)
    r = np.hypot(xx * 1.15, yy * 1.4) * 2
    f = r + 0.55 * (n1 - 0.5) + 0.12 * (n2 - 0.5)
    mask = smoothstep(0.78, 0.62, f) * edge_fade(N, N, 60)
    mask = np.clip(mask, 0, 1).astype(np.float32)
    save_webp(mask, DEC / "puddle-mask.webp", 92)
    # water surface: flat; faint wind ripples inside, slight meniscus slope at the rim
    rip = periodic_noise(N, N, 10, 47, octaves=2)
    h = (blur_reflect(mask, 6.0) * 0.4 + rip * 0.04 * mask).astype(np.float32)
    nrm = height_to_normal(h, 0.6, 1.0)
    save_webp(nrm, DEC / "puddle-normal.webp", 92)
    col = np.stack([np.full_like(mask, 0.05), np.full_like(mask, 0.055), np.full_like(mask, 0.06)], -1)
    save_webp(rgba(col, mask * 0.75), DEC / "puddle-color.webp", 90)
    for nm, how in (("puddle-mask.webp", ["noisy ellipse, soft rim, faded to zero at the border; R=G=B mask"]),
                    ("puddle-normal.webp", ["OpenGL normal from rim slope plus faint ripple noise inside the mask"]),
                    ("puddle-color.webp", ["near-black wet tint with alpha = 0.75 x mask (for a blended decal)"])):
        rec(DEC / nm, "decal", [2.0, 2.0], how, {"alphaMode": "BLEND"} if nm.endswith("color.webp") else None)


def worn_paint(H, W, seed):
    n1 = periodic_noise(H, W, 90, seed, octaves=5)
    n2 = periodic_noise(H, W, 8, seed + 1, octaves=3)
    n3 = periodic_noise(H, W, 30, seed + 2, octaves=3, aniso=0.5)
    wear = smoothstep(0.30, 0.55, n1 * 0.55 + n2 * 0.3 + n3 * 0.15)
    return wear.astype(np.float32), n2


def lines(kind):
    H, W = 1024, 512  # 1.0 m long (tiles along V) x 0.5 m wide
    x = (np.arange(W) + 0.5) / W * 500.0  # mm
    if kind == "yellow":
        stripes = [(100, 200), (300, 400)]  # double yellow, 100 mm lines, 100 mm gap
        col = np.array([0.76, 0.60, 0.20])
        seed = 51
    else:
        stripes = [(210, 290)]  # 80 mm court line
        col = np.array([0.80, 0.80, 0.76])
        seed = 61
    prof = np.zeros(W)
    for a, b in stripes:
        prof = np.maximum(prof, smoothstep(a - 1.5, a + 1.5, x) * smoothstep(b + 1.5, b - 1.5, x))
    wear, n2 = worn_paint(H, W, seed)
    # edges wobble a little (hand/road-marking machine)
    alpha = prof[None, :] * wear
    alpha = np.clip(alpha * (0.85 + 0.15 * n2), 0, 1).astype(np.float32)
    c = col[None, None, :] * (0.82 + 0.25 * n2[..., None]) * np.ones((H, W, 1))
    c = c * 0.9 + 0.1 * np.array([0.3, 0.3, 0.3])  # dirt
    p = save_webp(rgba(c.astype(np.float32), alpha), DEC / ("line-%s.webp" % kind), 90)
    rec(p, "decal", [0.5, 1.0], ["%s line profile (%s mm)" % (kind, ", ".join("%d-%d" % s for s in stripes)),
                                 "wear mask from periodic noise (paint loss, speckled aggregate showing through)"],
        {"tiles": "vertically", "alphaMode": "BLEND"}, seam=round(seam_ratio(alpha)[1], 3))


def drain():
    N = 1024  # 0.5 m square gully grate with frame
    px = 500.0 / N
    y, x = (np.mgrid[0:N, 0:N] + 0.5) * px  # mm
    frame_out, frame_in = 8, 50
    inside = (x > frame_in) & (x < 500 - frame_in) & (y > frame_in) & (y < 500 - frame_in)
    frame = (x > frame_out) & (x < 500 - frame_out) & (y > frame_out) & (y < 500 - frame_out) & ~inside
    # 9 slots across, bars between, a cross rib at mid height
    slot_w, pitch = 26.0, (400.0 - 2 * 10) / 9
    xs = (x - frame_in - 10) % pitch
    slot = inside & (xs > (pitch - slot_w) / 2) & (xs < (pitch + slot_w) / 2) & (np.abs(y - 250) > 12) \
        & (y > frame_in + 18) & (y < 500 - frame_in - 18)
    metal = (frame | inside) & ~slot
    h = np.zeros((N, N), np.float32)
    h[frame] = 1.0
    h[inside & ~slot] = 0.85
    h[slot] = -2.0
    h = blur_reflect(h, 1.6)
    # cast surface: anti-skid chequer bumps on the frame
    cheq = ((np.floor(x / 12) + np.floor(y / 12)) % 2 == 0) & frame
    h = h + 0.08 * blur_reflect(cheq.astype(np.float32), 1.2)
    n1 = periodic_noise(N, N, 80, 71, octaves=5)
    n2 = periodic_noise(N, N, 6, 73, octaves=3)
    rust = smoothstep(0.55, 0.8, n1 * 0.7 + n2 * 0.3) * (h < 0.95)
    iron = np.array([0.25, 0.245, 0.235])  # sRGB
    rustc = np.array([0.40, 0.24, 0.13])
    col = iron * (0.8 + 0.4 * n2[..., None])
    col = col * (1 - rust[..., None]) + rustc * rust[..., None]
    col[slot] = [0.015, 0.014, 0.013]
    wear = smoothstep(0.92, 1.0, h) * smoothstep(0.4, 0.7, n2)  # polished tops
    col = col + wear[..., None] * 0.08
    outer = (x > 4) & (x < 496) & (y > 4) & (y < 496)
    alpha = blur_reflect(outer.astype(np.float32), 1.0)
    p = save_webp(rgba(np.clip(col, 0, 1).astype(np.float32), alpha), DEC / "drain-grate-color.webp", 90)
    nrm = height_to_normal(h * 6.0, px, 1.0)
    save_webp(nrm, DEC / "drain-grate-normal.webp", 92)
    ao = np.clip(1 - 1.2 * np.clip(blur_reflect(h, 10) - h, 0, None), 0.15, 1)
    ao[slot] = 0.08
    rough = np.clip(0.55 + 0.25 * rust - 0.15 * wear + 0.05 * (n2 - 0.5), 0.3, 0.9)
    met = np.clip(metal * (0.85 - 0.85 * rust), 0, 1)
    save_webp(np.stack([ao, rough, met], -1).astype(np.float32), DEC / "drain-grate-orm.webp", 92)
    how = ["0.5 m cast-iron gully grate: 50 mm frame with chequer anti-skid pattern, 9 slots, mid rib",
           "rust and polished-top wear from periodic noise; slots near-black"]
    rec(DEC / "drain-grate-color.webp", "decal", [0.5, 0.5], how + ["colour sRGB, alpha 1 inside the frame"], {"alphaMode": "MASK"})
    rec(DEC / "drain-grate-normal.webp", "decal", [0.5, 0.5], ["OpenGL normal from the analytic grate height (6 mm relief, slots recessed)"])
    rec(DEC / "drain-grate-orm.webp", "decal", [0.5, 0.5], ["R AO (cavity, slots 0.08), G roughness, B metalness 0.85 on iron, 0 on rust"])


def _catmull(pts, n=24):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = map(np.asarray, (P[i - 1], P[i], P[i + 1], P[i + 2]))
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(np.asarray(P[-2]))
    return np.array(out)


def graffiti():
    """2x2 atlas of abstract marker/spray tags. Random looping strokes only: no letters,
    words, crew names or brands."""
    S = 512
    atlas = np.zeros((1024, 1024, 4), np.float32)
    palettes = [((0.05, 0.05, 0.06), None), ((0.62, 0.63, 0.66), (0.06, 0.06, 0.07)),
                ((0.45, 0.12, 0.10), (0.05, 0.05, 0.05)), ((0.12, 0.20, 0.38), (0.75, 0.76, 0.78))]
    for cell in range(4):
        rng = np.random.default_rng(900 + cell)
        SS = S * 2
        mask_fill = Image.new("L", (SS, SS), 0)
        df = ImageDraw.Draw(mask_fill)
        strokes = []
        n_str = int(rng.integers(3, 6))
        x = SS * 0.14
        for k in range(n_str):
            # each stroke: a loopy, jagged path drifting rightwards (letter-like rhythm, no letters)
            pts = []
            cx = x
            for j in range(int(rng.integers(4, 7))):
                cx += rng.uniform(-0.04, 0.10) * SS  # backward steps make curls, not letters
                cy = SS * (0.5 + rng.uniform(-0.22, 0.22) + 0.06 * math.sin(j * 1.7 + k))
                pts.append((cx, cy))
            x = cx - rng.uniform(0.0, 0.06) * SS
            path = _catmull(pts, 18)
            strokes.append(path)
            w = int(rng.integers(30, 50))
            df.line([tuple(p) for p in path], fill=255, width=w, joint="curve")
            for p in (path[0], path[-1]):
                df.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=255)
            if x > SS * 0.8:
                break
        # underline swoosh and a few drips under low points
        sw = _catmull([(SS * 0.12, SS * 0.78), (SS * 0.4, SS * 0.84), (SS * 0.7, SS * 0.8), (SS * 0.9, SS * 0.7)], 30)
        df.line([tuple(p) for p in sw], fill=255, width=22, joint="curve")
        for _ in range(int(rng.integers(3, 7))):
            path = strokes[int(rng.integers(len(strokes)))]
            p = path[int(rng.integers(len(path)))]
            L = rng.uniform(20, 90)
            df.line([(p[0], p[1]), (p[0], p[1] + L)], fill=255, width=7)
            df.ellipse([p[0] - 4, p[1] + L - 4, p[0] + 4, p[1] + L + 4], fill=255)
        fill = np.asarray(mask_fill.resize((S, S), Image.LANCZOS)).astype(np.float32) / 255
        fill_c, line_c = palettes[cell]
        if line_c is not None:
            outline = np.asarray(mask_fill.filter(ImageFilter.MaxFilter(17)).resize((S, S), Image.LANCZOS)).astype(np.float32) / 255
            a = np.maximum(outline, fill)
            c = np.asarray(line_c)[None, None] * (1 - fill[..., None]) + np.asarray(fill_c)[None, None] * fill[..., None]
        else:
            a = fill
            c = np.broadcast_to(np.asarray(fill_c), (S, S, 3)).copy()
        n = periodic_noise(S, S, 5, 950 + cell, octaves=2)
        a = np.clip(a * (0.78 + 0.3 * n), 0, 0.95)  # porous wall takes paint unevenly
        a = blur_reflect(a.astype(np.float32), 0.6) * edge_fade(S, S, 8)
        y0, x0 = (cell // 2) * S, (cell % 2) * S
        atlas[y0:y0 + S, x0:x0 + S, :3] = c
        atlas[y0:y0 + S, x0:x0 + S, 3] = a
    p = save_webp(atlas, DEC / "graffiti-atlas.webp", 90)
    rec(p, "decal atlas 2x2", [1.2, 1.2], ["four abstract tags: Catmull-Rom loops of random points, marker widths, outlines, drips",
                                            "no letters, words, crew names or brands; porous-wall alpha noise"],
        {"cells": "2x2, each 512 px, about 1.2 m wide", "alphaMode": "BLEND"})


def leaf_stains():
    N = 1024  # 2 m tileable scatter of tannin stains
    SS = 2
    R = N * SS
    acc = np.zeros((R, R), np.float32)
    rng = np.random.default_rng(81)
    im = Image.new("L", (R, R), 0)
    d = ImageDraw.Draw(im)
    for _ in range(70):
        cx, cy = rng.uniform(0, R, 2)
        L = rng.uniform(60, 150) * SS  # 6-15 cm leaves (plane, birch)
        Wd = L * rng.uniform(0.45, 0.9)
        ang = rng.uniform(0, 2 * np.pi)
        lobes = int(rng.integers(0, 3)) * 2 + 1
        t = np.linspace(0, 2 * np.pi, 80)
        r = 0.5 * (1 + 0.15 * np.cos(lobes * t)) * np.abs(np.sin(t / 2)) ** 0.3
        px_ = np.cos(t) * L * 0.5
        py_ = np.sin(t) * Wd * 0.5 * r * 2
        val = int(rng.uniform(90, 255))
        for ox in (-R, 0, R):
            for oy in (-R, 0, R):
                xs = cx + ox + px_ * np.cos(ang) - py_ * np.sin(ang)
                ys = cy + oy + px_ * np.sin(ang) + py_ * np.cos(ang)
                if xs.max() < 0 or xs.min() > R or ys.max() < 0 or ys.min() > R:
                    continue
                d.polygon(list(zip(xs, ys)), fill=val)
                # stem
                sx, sy = cx + ox - np.cos(ang) * L * 0.5, cy + oy - np.sin(ang) * L * 0.5
                d.line([(sx, sy), (sx - np.cos(ang) * L * 0.2, sy - np.sin(ang) * L * 0.2)], fill=val, width=3 * SS)
    acc = np.asarray(im).astype(np.float32) / 255
    acc = blur_wrap(acc, 3.0 * SS)
    acc = resize(acc[..., None], N, N, periodic=True)[..., 0]
    n = periodic_noise(N, N, 10, 83, octaves=3)
    # tannin rings: darker rim
    rim = np.clip(acc - blur_wrap(acc, 6), 0, None) * 3
    a = np.clip(acc * 0.55 * (0.7 + 0.5 * n) + rim * 0.4, 0, 0.75).astype(np.float32)
    col = np.stack([0.16 + 0.05 * n, 0.11 + 0.03 * n, 0.06 + 0.02 * n], -1)
    p = save_webp(rgba(col, a), DEC / "leaf-stains.webp", 90)
    rec(p, "decal", [2.0, 2.0], ["70 lobed leaf silhouettes with stems, random size 6-15 cm, wrap-placed (tileable)",
                                 "soft blur, tannin rim darkening, alpha noise"],
        {"tiles": "both", "alphaMode": "BLEND"}, seam=round(seam_ratio(a)[2], 3))


# ============================================================ window interiors
K2700 = np.array([1.0, 0.66, 0.36])  # 2700 K approximate linear tint (normalised to R)
K3000 = np.array([1.0, 0.72, 0.45])
K4000 = np.array([1.0, 0.86, 0.70])
TVBLUE = np.array([0.45, 0.62, 1.0])


def room_base(h, w, rng, wall, light_pos, light_col, light_amt, dark=False):
    """One-point-perspective room box lit by a ceiling or lamp source. Returns colour
    (albedo-ish, linear) and emitted radiance (linear)."""
    y, x = (np.mgrid[0:h, 0:w] + 0.5)
    u, v = x / w, y / h
    # back wall occupies the centre; side walls / floor / ceiling as perspective bands
    bw0, bw1 = 0.18 + rng.uniform(-0.04, 0.04), 0.82 + rng.uniform(-0.04, 0.04)
    bh0, bh1 = 0.16, 0.72 + rng.uniform(-0.03, 0.03)
    albedo = np.empty((h, w, 3), np.float32)
    albedo[:] = wall
    floor = v > bh1 + (np.abs(u - 0.5) - (bw1 - bw0) / 2).clip(0) * (1 - bh1) / 0.3
    ceil = v < bh0 - (np.abs(u - 0.5) - (bw1 - bw0) / 2).clip(0) * bh0 / 0.3
    side = ((u < bw0) | (u > bw1)) & ~floor & ~ceil
    floorc = np.array(rng.choice([[0.18, 0.12, 0.08], [0.25, 0.22, 0.2], [0.12, 0.1, 0.1]]))
    albedo[floor] = floorc
    albedo[ceil] = np.array([0.75, 0.73, 0.7])
    albedo[side] = np.asarray(wall) * 0.8
    lx, ly = light_pos
    dist = np.hypot((u - lx) * w / h, v - ly)
    illum = light_amt * (0.15 + 1.0 / (1.0 + (dist / 0.25) ** 2))
    shade = np.ones((h, w), np.float32)
    shade[side] = 0.75
    shade[floor] = 0.6
    shade[ceil] = 0.9
    # furniture silhouettes (sofa back, shelf, frame, plant, lampshade)
    items = []
    if rng.random() < 0.8:
        sx0 = rng.uniform(0.05, 0.4)
        items.append(((bh1 - 0.12, bh1 + 0.06, sx0, sx0 + rng.uniform(0.35, 0.55)), np.array(rng.choice([[0.2, 0.17, 0.14], [0.1, 0.12, 0.15], [0.25, 0.1, 0.08]]))))
    if rng.random() < 0.6:
        fx = rng.uniform(0.3, 0.6)
        items.append(((0.3, 0.42, fx, fx + 0.14), np.array([0.35, 0.3, 0.25])))
    if rng.random() < 0.5:
        shx = rng.choice([0.06, 0.78])
        items.append(((0.25, bh1 + 0.05, shx, shx + 0.16), np.array([0.28, 0.2, 0.13])))
    for (y0, y1, x0, x1), c in items:
        sel = (v > y0) & (v < y1) & (u > x0) & (u < x1)
        albedo[sel] = c
        shade[sel] *= 0.7
    rad = albedo * shade[..., None] * illum[..., None] * np.asarray(light_col)[None, None]
    if dark:
        rad *= 0.02
    return albedo, rad.astype(np.float32), (u, v)


def paint_cell(kind, rng):
    h, w = 600, 480  # 1.5 m x 1.2 m at 400 px/m
    walls = [[0.72, 0.66, 0.52], [0.62, 0.66, 0.58], [0.6, 0.62, 0.66], [0.75, 0.7, 0.62], [0.55, 0.45, 0.38]]
    wall = np.array(walls[int(rng.integers(len(walls)))])
    warm = K2700 if rng.random() < 0.75 else K3000
    if kind == "curtains":
        col = np.array(rng.choice([[0.55, 0.25, 0.15], [0.6, 0.5, 0.3], [0.35, 0.3, 0.45], [0.5, 0.45, 0.4], [0.3, 0.4, 0.3]]))
        y, x = (np.mgrid[0:h, 0:w] + 0.5)
        folds = 0.5 + 0.5 * np.sin(x / w * 2 * np.pi * rng.uniform(5, 8) + 0.6 * np.sin(x / 37.0))
        folds = folds ** 1.5
        gap_c = rng.uniform(0.4, 0.6)
        gap = np.abs(x / w - gap_c) < rng.uniform(0.0, 0.025)
        trans = 0.35 + 0.65 * folds  # light through thin fabric
        glow = np.exp(-((y / h - 0.35) ** 2) / 0.2)  # brighter where the room light is
        alb = col[None, None] * (0.6 + 0.4 * folds[..., None])
        rad = col[None, None] * warm[None, None] * (trans * glow * 1.4)[..., None]
        rad[gap] = warm * 1.6
        top = y / h < 0.04
        alb[top] = [0.3, 0.3, 0.3]
        rad[top] *= 0.2
        return alb, rad
    if kind == "nets":
        alb, rad, (u, v) = room_base(h, w, rng, wall, (rng.uniform(0.3, 0.7), 0.1), warm, 1.0)
        y, x = (np.mgrid[0:h, 0:w] + 0.5)
        mesh = (0.5 + 0.5 * np.sin(x * 1.3) * np.sin(y * 1.3)) * 0.3 + 0.7
        motif = 0.5 + 0.5 * np.sin(x / 9.0) * np.cos(y / 11.0)
        net = 0.55 + 0.2 * motif * mesh
        cafe = rng.random() < 0.4
        cover = np.ones((h, w)) if not cafe else (v > 0.45).astype(float)
        folds = 0.85 + 0.15 * np.sin(x / w * 2 * np.pi * 11)
        n_alb = np.array([0.85, 0.84, 0.8])
        a = (net * folds * cover)[..., None]
        alb = alb * (1 - a) + n_alb * a
        rad = rad * (1 - a * 0.6) + (0.55 * net * folds)[..., None] * warm[None, None] * a * np.clip(rad.mean() * 4, 0.3, 1.5)
        return alb, rad
    if kind == "blinds":
        cool = rng.random() < 0.3
        lc = K4000 if cool else warm
        alb, rad, (u, v) = room_base(h, w, rng, wall, (0.5, 0.05), lc, 1.0)
        y = (np.arange(h) + 0.5)[:, None]
        per = 14.0
        ph = (y % per) / per
        tilt = rng.uniform(0.55, 0.85)
        slat = ph < tilt
        sc = np.array(rng.choice([[0.8, 0.8, 0.78], [0.7, 0.62, 0.5], [0.5, 0.5, 0.5]]))
        lit = 0.5 + 0.5 * np.cos(ph / tilt * np.pi)  # slat curvature
        s_alb = np.broadcast_to(sc, (h, w, 3))
        s_rad = sc[None, None] * lc[None, None] * (0.25 + 0.35 * lit)[..., None] * np.ones((1, w, 1))
        m = np.broadcast_to(slat, (h, w))[..., None]
        alb = np.where(m, s_alb, alb)
        rad = np.where(m, s_rad, rad * 0.9)
        return alb, rad
    if kind == "lamp":
        lx = rng.choice([0.2, 0.8])
        alb, rad, (u, v) = room_base(h, w, rng, wall, (lx, 0.55), warm, 0.9)
        shade_c = np.array([0.95, 0.85, 0.65])
        sel = (np.abs(u - lx) < 0.07 + (v - 0.48) * 0.25) & (v > 0.48) & (v < 0.58)
        alb[sel] = shade_c
        rad[sel] = warm * 2.2
        stand = (np.abs(u - lx) < 0.008) & (v > 0.58) & (v < 0.85)
        alb[stand] = [0.1, 0.1, 0.1]
        rad[stand] *= 0.3
        rad *= 0.8
        return alb, rad
    if kind == "dark":
        alb, rad, _ = room_base(h, w, rng, wall * 0.6, (0.5, 0.2), np.array([0.6, 0.7, 1.0]), 0.3, dark=True)
        return alb * 0.4, rad
    if kind == "tv":
        alb, rad, (u, v) = room_base(h, w, rng, wall, (rng.uniform(0.3, 0.7), 0.78), TVBLUE, 0.55)
        flick = 0.85 + 0.15 * np.sin(u * 7 + v * 3)
        rad = rad * flick[..., None]
        rad += alb * 0.02 * warm  # faint warm spill from another room
        return alb, rad
    if kind == "kitchen":
        alb, rad, (u, v) = room_base(h, w, rng, np.array([0.8, 0.8, 0.78]), (0.5, 0.06), K4000, 1.3)
        strip = (v > 0.04) & (v < 0.07) & (u > 0.15) & (u < 0.85)
        alb[strip] = [1, 1, 1]
        rad[strip] = K4000 * 4.0
        cab = (v > 0.14) & (v < 0.36) & ((u < 0.42) | (u > 0.5))
        cabc = np.array(rng.choice([[0.75, 0.73, 0.68], [0.35, 0.4, 0.45], [0.55, 0.42, 0.3]]))
        alb[cab] = cabc
        rad[cab] = cabc * K4000 * 0.45
        tiles = (v > 0.36) & (v < 0.55)
        y, x = (np.mgrid[0:h, 0:w] + 0.5)
        grout = ((x % 24) < 1.5) | ((y % 24) < 1.5)
        alb[tiles & grout] *= 0.8
        rad[tiles] *= 1.2
        worktop = (v > 0.55) & (v < 0.6)
        alb[worktop] = [0.2, 0.2, 0.2]
        return alb, rad
    raise ValueError(kind)


def windows():
    plan = (["curtains"] * 6 + ["nets"] * 6 + ["blinds"] * 5 + ["lamp"] * 4 + ["dark"] * 5 + ["tv"] * 3 + ["kitchen"] * 3)
    rng = np.random.default_rng(2700)
    order = list(rng.permutation(plan))
    C, R, cs = 8, 4, 256
    col = np.zeros((R * cs, C * cs, 3), np.float32)
    emit = np.zeros((R * cs, C * cs, 3), np.float32)
    cells = []
    for i, kind in enumerate(order):
        alb, rad = paint_cell(kind, rng)
        # soft optical blur: the view is seen through glazing from outside
        alb = blur_reflect(alb.astype(np.float32), 1.2)
        rad = blur_reflect(rad.astype(np.float32), 1.5)
        a = resize(alb, cs, cs)
        e = resize(rad, cs, cs)
        r, c = divmod(i, C)
        col[r * cs:(r + 1) * cs, c * cs:(c + 1) * cs] = np.clip(a, 0, 1)
        emit[r * cs:(r + 1) * cs, c * cs:(c + 1) * cs] = np.clip(e, 0, None)
        cells.append({"cell": i, "row": r, "col": c, "kind": kind})
    # emit is stored as display-referred colour: normalise so the brightest lamp ~ 1.0
    scale = 1.0 / np.percentile(emit, 99.7)
    emit_s = lin_to_srgb(np.clip(emit * scale, 0, 1))
    col_s = lin_to_srgb(col * 0.5)  # unlit appearance (dim)
    p1 = save_webp(col_s, WIN / "interiors-color.webp", 90)
    p2 = save_webp(emit_s, WIN / "interiors-emit.webp", 90)
    how = ["32 procedural dusk room views (8 x 4 cells, 256 px each; painted at 480 x 600 px for a 1.2 x 1.5 m pane, then squeezed)",
           "kinds: drawn curtains with warm glow, net curtains (full and cafe), venetian blinds (warm and cool), lamp glow, dark unlit room, TV-blue glow, kitchen strip light",
           "warm 2700 K dominant; kitchens 4000 K, some blinds cool, TVs blue"]
    rec(p1, "window atlas", [1.2, 1.5], how + ["colour = dim unlit albedo (sRGB)"], {"cells": cells, "grid": [8, 4]})
    rec(p2, "window atlas", [1.2, 1.5], how + ["emit = emitted radiance, normalised so the brightest 0.3% clip at 1, sRGB encoded"], {"grid": [8, 4]})
    return col, emit * scale, cells


# ============================================================ tower facade
def tower(win_col, win_emit, cells):
    N = 1024  # 12 m x 12 m, 85.3 px per metre; 4 storeys x 4 bays
    ppm = N / 12.0
    conc = np.asarray(Image.open(OUT / "hr_concrete_cast-color.webp").convert("RGB")).astype(np.float32) / 255
    conc_l = srgb_to_lin(conc)
    c3 = resize(conc_l, 256, 256, periodic=True)  # 2 m tile drawn at 3 m
    base = np.tile(c3, (4, 4, 1))
    y, x = (np.mgrid[0:N, 0:N] + 0.5) / ppm  # metres
    sy, bx = y % 3.0, x % 3.0  # within storey / bay
    storey = (y // 3.0).astype(int)
    bay = (x // 3.0).astype(int)
    col = base * 1.0
    emit = np.zeros_like(col)
    # floor slab band (0.30 m) and precast panel joints
    slab = sy > 2.7
    col[slab] *= 0.78
    joint = (np.abs(bx - 0.02) < 0.025) | (np.abs(sy - 2.7) < 0.02) | (np.abs(sy - 0.0) < 0.02)
    col[joint] *= 0.55
    # window opening: 1.9 m x 1.35 m, sill at 0.95 m above floor (floor at sy = 0 at the top? use sy from top)
    # storey coordinate: top of storey at sy=0 (slab sits at the bottom of each band)
    wx0, wx1 = 0.55, 2.45
    wy0, wy1 = 0.45, 1.80
    win = (bx > wx0) & (bx < wx1) & (sy > wy0) & (sy < wy1)
    frame = win & ((bx < wx0 + 0.06) | (bx > wx1 - 0.06) | (sy < wy0 + 0.06) | (sy > wy1 - 0.06) | (np.abs(bx - 1.5) < 0.03))
    spandrel = (bx > wx0) & (bx < wx1) & (sy > wy1) & (sy < 2.7)
    col[spandrel] = col[spandrel] * 0.9 + np.array([0.08, 0.08, 0.075]) * 0.1
    sill = (bx > wx0 - 0.05) & (bx < wx1 + 0.05) & (sy > wy1) & (sy < wy1 + 0.06)
    col[sill] *= 1.15
    # rain staining under sills and from slab edges
    n = periodic_noise(N, N, 6, 501, octaves=3, aniso=10)
    stain = np.zeros((N, N), np.float32)
    below = (sy - wy1).clip(0)
    stain += ((bx > wx0) & (bx < wx1)) * np.exp(-below / 0.6) * (sy > wy1) * (0.5 + 0.6 * n)
    stain += np.exp(-(sy % 3.0 - 0.0).clip(0) / 0.8) * 0.25 * n
    col *= (1 - 0.35 * np.clip(stain, 0, 1))[..., None]
    # glazing: dark sky-reflecting glass, or an interior from the atlas
    rng = np.random.default_rng(1960)
    lit_kinds = {"curtains", "nets", "blinds", "lamp", "tv", "kitchen"}
    lit_cells = [c for c in cells if c["kind"] in lit_kinds]
    dark_cells = [c for c in cells if c["kind"] == "dark"]
    assign = {}
    for s in range(4):
        for b in range(4):
            assign[(s, b)] = lit_cells[int(rng.integers(len(lit_cells)))] if rng.random() < 0.38 else dark_cells[int(rng.integers(len(dark_cells)))]
    glass_sky = np.array([0.035, 0.045, 0.07])
    ww = int(round((wx1 - wx0) * ppm))
    wh = int(round((wy1 - wy0) * ppm))
    for (s, b), cdef in assign.items():
        r, c = cdef["row"], cdef["col"]
        ia = win_col[r * 256:(r + 1) * 256, c * 256:(c + 1) * 256]
        ie = win_emit[r * 256:(r + 1) * 256, c * 256:(c + 1) * 256]
        ia = resize(ia, wh, ww)
        ie = resize(ie, wh, ww)
        y0 = int(round((s * 3.0 + wy0) * ppm))
        x0 = int(round((b * 3.0 + wx0) * ppm))
        sl = (slice(y0, y0 + wh), slice(x0, x0 + ww))
        m = win[sl] & ~frame[sl]
        refl = glass_sky * (1.0 + 0.5 * (1 - np.linspace(0, 1, wh))[:, None])[..., None]
        col[sl][m] = (ia * 0.25 + refl * 0.75)[m]
        emit[sl][m] = ie[m] * (0.9 if cdef["kind"] != "dark" else 0.0)
    col[frame] = np.array([0.55, 0.55, 0.53])  # white uPVC replacement frames, weathered
    col = np.clip(col, 0, 1)
    col_s = lin_to_srgb(col)
    emit_s = lin_to_srgb(np.clip(emit, 0, 1))
    p1 = save_webp(col_s, BACK / "tower-facade-color.webp", 90)
    p2 = save_webp(emit_s, BACK / "tower-facade-emit.webp", 90)
    lit = sum(1 for v in assign.values() if v["kind"] != "dark")
    how = ["12 m x 12 m patch: 4 storeys of 3 m x 4 bays of 3 m; precast panels with joints, 0.3 m floor slab bands",
           "1.9 x 1.35 m windows with white uPVC frames and mullion, spandrels, sills, rain staining under sills",
           "panel concrete = hr_concrete_cast colour (periodic resample, 2 m drawn at 3 m)",
           "glazing: dark sky reflection blended with interiors from the window atlas; %d of 16 windows lit" % lit]
    sr = seam_ratio_phase(col_s, 4, 4)
    rec(p1, "backdrop", [12.0, 12.0], how, {"tiles": "both", "seamRatioMethod": "phase-matched (4 bays x 4 storeys)"}, seam=round(sr[2], 3))
    rec(p2, "backdrop", [12.0, 12.0], how[-1:] + ["emit = lit window radiance, sRGB encoded"], {"tiles": "both"})
    return col_s, emit_s


def main():
    for d in (DEC, WIN, BACK):
        d.mkdir(parents=True, exist_ok=True)
    rain_streaks()
    grime()
    moss_edge()
    puddle()
    lines("yellow")
    lines("white")
    drain()
    graffiti()
    leaf_stains()
    wc, we, cells = windows()
    tower(wc, we, cells)
    data = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    data["decalAndAtlasTextures"] = records
    write_json(MANIFEST, data)
    for r in records:
        print("%-55s %8d B %s" % (r["path"], r["bytes"], r.get("seamRatio", "")))


if __name__ == "__main__":
    main()
