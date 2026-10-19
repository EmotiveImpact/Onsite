"""Build the 22 Heron Reach tiling PBR sets from the repo's own source-30 colour images.

Run:  python3 scripts/maps/art/make_heron_textures.py [name ...]
Writes public/materials/heron/<name>-{color,normal,orm}.webp and a texture record in
assets/blender/heron-reach/materials-manifest.json (merged with what is already there).

Methods (all original processing, numpy + Pillow only):
  stochastic  delight -> resample -> two closed min-cut wrap passes (tileable)
  bricks      detect courses/head joints in the source, re-lay every source brick on a
              regular running-bond grid with an integer course and brick count
  slabs       same with a square slab grid
  strips      detect board/slat/plank joints, re-stack joint-to-joint strips, each strip
              made periodic along its length with min-cut quilting
  herringbone analytic 45-degree herringbone layout, paver colours and speckle sampled
              from the source pavers
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np

from heron_tex_common import (OUT, REPO, SCRATCH, blur_reflect, blur_wrap, cavity_ao, delight,
                              detail_height, flatten_wrap, grade, height_to_normal, lin_to_srgb,
                              load_source, lum, norm01, periodic_noise, quilt_concat, resize,
                              save_png, save_webp, seam_ratio, seam_ratio_phase, sha256, smoothstep, srgb_to_lin,
                              wrap_1d, wrap_tile, write_json, zscore)

N = 1024
MANIFEST = REPO / "assets/blender/heron-reach/materials-manifest.json"
PH = "public/materials/pbr/provenance.json"


# ============================================================ joint detection
def _skew(p):
    p = p - p.mean()
    return float((p ** 3).mean() / (p.std() ** 3 + 1e-9))


def oriented_profile(score, axis, rows=None):
    s = score if rows is None else score[rows]
    p = s.mean(axis=axis)
    p = np.convolve(p, np.ones(3) / 3, mode="same")
    return p


def find_joints(p, period, refine=0.3, fit_period=False):
    """Comb-fit a period to a 1D joint profile, then refine every tooth locally."""
    n = len(p)
    best, phase = -1e9, 0
    periods = np.arange(period - 1.5, period + 1.5, 0.02) if fit_period else [period]
    for per in periods:
        for ph in np.arange(0, per, 0.5):
            idx = np.round(np.arange(ph, n - 1, per)).astype(int)
            v = p[idx].mean()
            if v > best:
                best, phase, period = v, ph, per
    out = []
    r = int(period * refine)
    for c in np.arange(phase, n, period):
        c = int(round(c))
        lo, hi = max(0, c - r), min(n, c + r + 1)
        if hi - lo < 3:
            continue
        out.append(lo + int(np.argmax(p[lo:hi])))
    # drop near-duplicates
    clean = []
    for x in out:
        if not clean or x - clean[-1] > 0.6 * period:
            clean.append(x)
    return clean


def mortar_score(srgb, mode="pale"):
    L = srgb.mean(2)
    mx, mn = srgb.max(2), srgb.min(2)
    S = (mx - mn) / (mx + 1e-3)
    if mode == "pale":  # pale, grey mortar
        s = zscore(L) - zscore(S)
    elif mode == "dark":  # dark joints
        s = -zscore(L)
    elif mode == "edge_y":  # horizontal ridges/grooves
        g = np.abs(np.diff(L, axis=0, append=L[-1:]))
        s = zscore(blur_reflect(g, 1.5)) - 0.5 * zscore(L)
    elif mode == "grey":  # greyer than painted faces
        s = zscore(S) - zscore(L)
    else:
        raise ValueError(mode)
    return s.astype(np.float32)


# ============================================================ cell composition
def place(acc, wsum, cell, y0, x0, m):
    """Accumulate a cell (with margin m on all sides) at core origin (y0, x0), wrapping."""
    h, w = cell.shape[:2]
    H, W = acc.shape[:2]

    def ramp(n):
        i = np.arange(n) + 0.5
        return np.clip(np.minimum(i, n - i) / (2 * m), 0, 1)

    wt = ramp(h)[:, None] * ramp(w)[None, :]
    rows = (np.arange(h) + y0 - m) % H
    cols = (np.arange(w) + x0 - m) % W
    ix = np.ix_(rows, cols)
    acc[ix] += cell * wt[..., None]
    wsum[ix] += wt


def extract(img, y0, y1, x0, x1, ch, cw, m):
    """Crop joint-centre to joint-centre rectangle plus a proportional margin, resample
    to (ch+2m, cw+2m)."""
    sy = (y1 - y0) / ch
    sx = (x1 - x0) / cw
    my, mx = m * sy, m * sx
    Y0, Y1 = int(np.floor(y0 - my)), int(np.ceil(y1 + my))
    X0, X1 = int(np.floor(x0 - mx)), int(np.ceil(x1 + mx))
    if Y0 < 0 or X0 < 0 or Y1 > img.shape[0] or X1 > img.shape[1]:
        return None
    crop = img[Y0:Y1, X0:X1]
    return resize(crop, ch + 2 * m, cw + 2 * m)


def brick_cells(img, score, course_p, brick_p, ch, cw, m):
    prow = oriented_profile(score, 1)
    if _skew(prow) < 0:
        score = -score
        prow = -prow
    rows = find_joints(prow, course_p)
    cells = []
    for a, b in zip(rows[:-1], rows[1:]):
        if not (0.75 * course_p < b - a < 1.3 * course_p):
            continue
        band = slice(int(a + 0.3 * (b - a)), int(b - 0.3 * (b - a)) + 1)
        pc = oriented_profile(score, 0, band)
        cols = find_joints(pc, brick_p, refine=0.25)
        for c0, c1 in zip(cols[:-1], cols[1:]):
            if not (0.7 * brick_p < c1 - c0 < 1.35 * brick_p):
                continue
            cell = extract(img, a, b, c0, c1, ch, cw, m)
            if cell is not None:
                cells.append(cell)
    return cells, rows, score


def compose_bond(cells, n_rows, n_cols, ch, cw, m, rng, offset=0.5, rot180=True, rot90=False):
    C = cells[0].shape[2]
    H, W = n_rows * ch, n_cols * cw
    acc = np.zeros((H, W, C), np.float32)
    wsum = np.zeros((H, W), np.float32)
    order = []
    for r in range(n_rows):
        off = int(round((r % 2) * offset * cw))
        for c in range(n_cols):
            if not order:
                order = list(rng.permutation(len(cells)))
            cell = cells[order.pop()]
            if rot90:
                k = int(rng.integers(4))
                cell = np.rot90(cell, k)
            elif rot180 and rng.random() < 0.5:
                cell = cell[::-1, ::-1]
            if rng.random() < 0.5:
                cell = cell[:, ::-1]
            place(acc, wsum, cell, r * ch, c * cw + off, m)
    out = acc / np.maximum(wsum, 1e-6)[..., None]
    return out


def bond_distance(H, W, ch, cw, offset=0.5):
    """Distance (canvas px) to the nearest joint line of a running bond."""
    y = np.arange(H)[:, None] + 0.5
    x = np.arange(W)[None, :] + 0.5
    dy = np.abs(((y + ch / 2) % ch) - ch / 2)
    r = (np.floor(y / ch)).astype(int)
    off = np.round((r % 2) * offset * cw)
    dx = np.abs(((x - off + cw / 2) % cw) - cw / 2)
    return np.minimum(dy, dx).astype(np.float32)


# ============================================================ strips
def strip_cells(img, score, period, sh, m, refine=0.3, fit_period=False):
    """Joint-to-joint horizontal strips resampled to height sh+2m (length scaled)."""
    prow = oriented_profile(score, 1)
    if _skew(prow) < 0:
        prow = -prow
    rows = find_joints(prow, period, refine, fit_period)
    strips = []
    for a, b in zip(rows[:-1], rows[1:]):
        if not (0.7 * period < b - a < 1.35 * period):
            continue
        s = (b - a) / sh
        Y0, Y1 = int(np.floor(a - m * s)), int(np.ceil(b + m * s))
        if Y0 < 0 or Y1 > img.shape[0]:
            continue
        crop = img[Y0:Y1]
        L = int(round(img.shape[1] / s))
        strips.append(resize(crop, sh + 2 * m, L))
    return strips, rows


def compose_strips(strips, n, sh, W, m, rng, O=96):
    C = strips[0].shape[2]
    H = n * sh
    acc = np.zeros((H, W, C), np.float32)
    wsum = np.zeros((H, W), np.float32)
    order = []
    for r in range(n):
        if not order:
            order = list(rng.permutation(len(strips)))
        cur = strips[order.pop()]
        if rng.random() < 0.5:
            cur = cur[:, ::-1]
        x0 = int(rng.integers(0, max(1, cur.shape[1] - 64)))
        cur = np.roll(cur, -x0, axis=1)
        while cur.shape[1] < W + O:
            j = int(rng.integers(len(strips)))
            nxt = strips[j]
            if rng.random() < 0.5:
                nxt = nxt[:, ::-1]
            cur = quilt_concat(cur, nxt, O)
        per = wrap_1d(cur, W, O)
        place(acc, wsum, per, r * sh, int(rng.integers(W)) + m, m)
    # placement used a column margin of m too; only the row ramp matters for strips
    return acc / np.maximum(wsum, 1e-6)[..., None]


# ============================================================ herringbone
def herringbone(Npx, n_x, ss=2):
    """45-degree herringbone, 2:1 pavers. Returns paver id (int), orientation, and
    edge distance in units of paver width, all periodic on an Npx tile that holds
    n_x lattice steps across and n_x/2 down."""
    R = Npx * ss
    Wpx = R / (n_x * np.sqrt(2))  # paver width in px
    y, x = np.mgrid[0:R, 0:R].astype(np.float64) + 0.5
    x /= Wpx
    y /= Wpx
    u = (x - y) / np.sqrt(2)
    v = (x + y) / np.sqrt(2)
    n_y = n_x // 2
    pid = np.full(u.shape, -1, np.int64)
    ori = np.zeros(u.shape, np.int8)
    dist = np.zeros(u.shape)
    n0 = np.floor((v - u) / 4.0)
    for dn in (-2, -1, 0, 1, 2):
        n = n0 + dn
        up, vp = u + 2 * n, v - 2 * n
        # horizontal-in-(u,v) paver H_k: u in [k,k+2], v in [k,k+1]
        k = np.floor(vp)
        inside = (up >= k) & (up < k + 2) & (pid < 0)
        d = np.minimum(np.minimum(up - k, k + 2 - up), np.minimum(vp - k, k + 1 - vp))
        key = ((np.mod(n, n_y) * n_x + np.mod(k, n_x)) * 2).astype(np.int64)
        pid[inside] = key[inside]
        ori[inside] = 0
        dist[inside] = d[inside]
        # vertical paver V_k: u in [k,k+1], v in [k+1,k+3]
        k = np.floor(up)
        inside = (vp >= k + 1) & (vp < k + 3) & (pid < 0)
        d = np.minimum(np.minimum(up - k, k + 1 - up), np.minimum(vp - k - 1, k + 3 - vp))
        key = ((np.mod(n, n_y) * n_x + np.mod(k, n_x)) * 2 + 1).astype(np.int64)
        pid[inside] = key[inside]
        ori[inside] = 1
        dist[inside] = d[inside]
    # a handful of pixels land exactly on a float boundary: take a neighbour's paver
    for _ in range(3):
        hole = pid < 0
        if not hole.any():
            break
        for arr in (pid, ori, dist):
            arr[hole] = np.roll(arr, 1, axis=1)[hole]
    assert (pid >= 0).all(), "herringbone partition has holes"
    return pid, ori, dist.astype(np.float32), Wpx / ss


# ============================================================ material specs
# grade: sat, mean_y (linear luminance), tint (linear rgb), tint_amt, contrast
SPECS = {
    "hr_brick_stock": dict(src=1, kind="bricks", mode="pale", grade=(0.85, 0.15, (0.32, 0.28, 0.22), 0.06, 1.0),
                           depth=7.0, detail=1.0, rough=(0.84, 0.08), ao=1.0, soot=0.10),
    "hr_brick_red": dict(src=2, kind="bricks", mode="pale", grade=(0.72, 0.085, (0.30, 0.25, 0.22), 0.10, 1.0),
                         depth=7.0, detail=1.0, rough=(0.84, 0.08), ao=1.0, soot=0.06),
    "hr_brick_painted": dict(src=3, kind="bricks", mode="grey", grade=(0.65, 0.42, (0.36, 0.34, 0.30), 0.12, 1.0),
                             depth=6.0, detail=0.8, rough=(0.76, 0.08), ao=0.9, soot=0.05),
    "hr_concrete_cast": dict(src=4, kind="stochastic", grade=(0.6, 0.20, (0.33, 0.33, 0.32), 0.15, 1.0),
                             depth=1.6, hp=(0.8, 10), rough=(0.86, 0.07)),
    "hr_concrete_board": dict(src=5, kind="strips", mode="edge_y", grade=(0.6, 0.17, (0.33, 0.32, 0.30), 0.15, 1.0),
                              depth=3.5, hp=(0.8, 12), rough=(0.86, 0.07), boards=10),
    "hr_concrete_rough": dict(src=6, kind="stochastic", grade=(0.62, 0.17, (0.32, 0.31, 0.29), 0.18, 1.0),
                              depth=4.0, hp=(0.8, 8), rough=(0.9, 0.05), stain=0.18),
    "hr_render": dict(src=7, kind="stochastic", flat=(40, 0.85), grade=(0.6, 0.36, (0.36, 0.34, 0.31), 0.10, 0.9),
                      depth=1.4, hp=(1.0, 14), rough=(0.82, 0.06), stain=0.08),
    "hr_asphalt": dict(src=8, kind="stochastic", grade=(0.45, 0.055, (0.30, 0.30, 0.30), 0.2, 1.0),
                       depth=3.2, hp=(0.7, 8), rough=(0.72, 0.13), ground=True, stain=0.15),
    "hr_court": dict(src=9, kind="stochastic", grade=(0.4, 0.065, (0.24, 0.33, 0.28), 0.5, 0.8),
                     depth=1.4, hp=(0.7, 8), rough=(0.68, 0.10), ground=True, stain=0.10),
    "hr_paving": dict(src=10, kind="slabs", mode="dark", grade=(0.55, 0.19, (0.33, 0.32, 0.30), 0.15, 1.0),
                      depth=6.0, detail=1.0, rough=(0.74, 0.11), ground=True, slabs=4),
    "hr_pavers_red": dict(src=11, kind="herringbone", grade=(0.75, 0.085, (0.30, 0.25, 0.22), 0.10, 1.0),
                          depth=5.0, detail=0.8, rough=(0.74, 0.11), ground=True),
    "hr_roof_felt": dict(src=12, kind="stochastic", grade=(0.4, 0.055, (0.30, 0.30, 0.30), 0.2, 1.0),
                         depth=2.6, hp=(0.7, 6), rough=(0.76, 0.09), ground=True, stain=0.12),
    "hr_steel_black": dict(src=13, kind="stochastic", grade=(0.3, 0.028, (0.30, 0.30, 0.31), 0.4, 1.0),
                           depth=0.35, hp=(1.0, 16), rough=(0.42, 0.08), metal="chips"),
    "hr_steel_galv": dict(src=14, kind="stochastic", grade=(0.25, 0.33, (0.32, 0.33, 0.34), 0.3, 0.75),
                          depth=0.25, hp=(1.0, 16), rough=(0.45, 0.12), metal="full"),
    "hr_steel_aged": dict(src=15, kind="stochastic", flat=(50, 0.6), grade=(0.75, 0.075, (0.30, 0.27, 0.24), 0.08, 1.0),
                          depth=0.9, hp=(0.8, 12), rough=(0.62, 0.1), metal="rust"),
    "hr_shutter": dict(src=16, kind="strips", mode="dark", grade=(0.3, 0.075, (0.30, 0.31, 0.32), 0.25, 0.7),
                       depth=7.0, hp=(1.0, 12), rough=(0.5, 0.08), slats=24, metal="none",
                       refine=0.08, fit_period=True),
    "hr_rubber": dict(src=17, kind="stochastic", grade=(0.35, 0.045, (0.30, 0.30, 0.30), 0.2, 1.0),
                      depth=1.3, hp=(0.7, 6), rough=(0.82, 0.05)),
    "hr_timber": dict(src=26, kind="strips_v", mode="dark", grade=(0.6, 0.10, (0.32, 0.29, 0.25), 0.12, 1.0),
                      depth=4.0, hp=(0.8, 10), rough=(0.74, 0.08), planks=8),
    "hr_soil": dict(src=27, kind="stochastic", grade=(0.7, 0.035, (0.30, 0.26, 0.22), 0.1, 1.0),
                    depth=5.0, hp=(0.8, 10), rough=(0.74, 0.11), ground=True),
    "hr_grass_ground": dict(src=28, kind="grass", grade=(0.55, 0.075, (0.25, 0.27, 0.18), 0.25, 1.0),
                            depth=3.0, hp=(0.8, 8), rough=(0.76, 0.09), ground=True),
    "hr_gravel": dict(src=29, kind="stochastic", grade=(0.5, 0.17, (0.31, 0.30, 0.29), 0.12, 1.0),
                      depth=6.0, hp=(1.0, 10), rough=(0.74, 0.11), ground=True, delight_sigma=60),
    "hr_plaster": dict(src=30, kind="stochastic", flat=(45, 0.7), grade=(0.55, 0.52, (0.35, 0.34, 0.32), 0.08, 0.9),
                       depth=0.5, hp=(1.0, 16), rough=(0.88, 0.04)),
}
COVERAGE = {k: (1.0 if k in ("hr_steel_black", "hr_steel_galv", "hr_steel_aged", "hr_rubber") else 2.0)
            for k in SPECS}


PHASE = {"hr_brick_stock": (9, 26), "hr_brick_red": (9, 26), "hr_brick_painted": (9, 26),
         "hr_paving": (4, 4), "hr_pavers_red": (14, 7), "hr_concrete_board": (None, 10),
         "hr_shutter": (None, 24), "hr_timber": (8, None)}


def seed_of(name):
    return sum((i + 1) * ord(c) for i, c in enumerate(name)) * 7919


def apply_grade(lin, g):
    sat, my, tint, ta, con = g
    return grade(lin, sat=sat, mean_y=my, tint=tint, tint_amt=ta, contrast=con)


# ============================================================ builders
def build_stochastic(src_lin, spec, O=160):
    sig = spec.get("delight_sigma", 125)
    d = delight(src_lin, sig)
    r = resize(d, N + O, N + O)
    t = wrap_tile(r, N, N, O)
    return t, {"joint": None}, [
        "sRGB to linear",
        "delight: divide luminance by Gaussian blur (sigma %d px at 1254 px), chroma kept" % sig,
        "Lanczos resample 1254 to %d px" % (N + O),
        "two closed minimum-error-cut wrap passes (overlap %d px, 2 px feather)" % O,
    ]


def build_bricks(src, src_lin, spec, rng):
    n_rows, n_cols = 26, 9
    ch, m = 80, 6
    cw = int(round(ch * n_rows / n_cols))
    score = mortar_score(src, spec["mode"])
    prof = score.mean(1)
    # course period by autocorrelation of the row profile
    p = prof - prof.mean()
    ac = np.correlate(p, p, "full")[len(p) - 1:]
    course_p = 40 + int(np.argmax(ac[40:200]))
    pc = score.mean(0) - score.mean(0).mean()
    acc = np.correlate(pc, pc, "full")[len(pc) - 1:]
    half = 60 + int(np.argmax(acc[60:220]))
    brick_p = 2 * half
    d = delight(src_lin, 125)
    stack = np.concatenate([d, norm01(score)[..., None]], axis=2)
    cells, rows, _ = brick_cells(stack, score, course_p, brick_p, ch, cw, m)
    canvas = compose_bond(cells, n_rows, n_cols, ch, cw, m, rng)
    H, W = canvas.shape[:2]
    D = bond_distance(H, W, ch, cw)
    canvas = np.concatenate([canvas, D[..., None]], axis=2)
    out = resize(canvas, N, N, periodic=True)
    scale = N / H
    info = {"joint_dist": out[..., 4] * 1.0, "mscore": out[..., 3], "jscale": scale,
            "course_p": course_p, "brick_p": brick_p, "cells": len(cells), "courses_src": len(rows)}
    steps = [
        "sRGB to linear; delight (sigma 125 px)",
        "mortar score '%s'; course period %d px, brick period %d px by autocorrelation" % (spec["mode"], course_p, brick_p),
        "comb-fit bed joints, per-course head joints; %d source bricks extracted joint-centre to joint-centre" % len(cells),
        "re-laid on a regular running bond: %d courses x %d bricks per 2 m (course %.1f mm, brick pitch %.1f mm), random flips, feathered 6 px mortar overlap" % (
            n_rows, n_cols, 2000 / n_rows, 2000 / n_cols),
        "periodic Lanczos resample to 1024 px",
    ]
    return out[..., :3], info, steps


def build_slabs(src, src_lin, spec, rng):
    n = spec["slabs"]
    score = mortar_score(src, spec["mode"])
    pr = score.mean(1) - score.mean(1).mean()
    ac = np.correlate(pr, pr, "full")[len(pr) - 1:]
    per = 150 + int(np.argmax(ac[150:500]))
    ch = cw = 300
    m = 8
    d = delight(src_lin, 200)
    stack = np.concatenate([d, norm01(score)[..., None]], axis=2)
    cells, rows, _ = brick_cells(stack, score, per, per, ch, cw, m)
    canvas = compose_bond(cells, n, n, ch, cw, m, rng, offset=0.0, rot90=True)
    H, W = canvas.shape[:2]
    D = bond_distance(H, W, ch, cw, offset=0.0)
    canvas = np.concatenate([canvas, D[..., None]], axis=2)
    out = resize(canvas, N, N, periodic=True)
    info = {"joint_dist": out[..., 4], "mscore": out[..., 3], "jscale": N / H, "period": per, "cells": len(cells)}
    steps = [
        "sRGB to linear; delight (sigma 200 px)",
        "dark-joint score; slab period %d px by autocorrelation; %d source slabs extracted" % (per, len(cells)),
        "re-laid on a %d x %d grid per 2 m (%.0f mm slabs) with random 90-degree rotations and flips, 8 px feathered joints" % (n, n, 2000 / n),
        "periodic Lanczos resample to 1024 px",
    ]
    return out[..., :3], info, steps


def build_strips(src, src_lin, spec, rng, vertical=False):
    img_srgb = src
    lin = delight(src_lin, 125)
    if vertical:
        img_srgb = np.transpose(src, (1, 0, 2))
        lin = np.transpose(lin, (1, 0, 2))
    score = mortar_score(img_srgb, spec["mode"])
    pr = score.mean(1) - score.mean(1).mean()
    ac = np.correlate(pr, pr, "full")[len(pr) - 1:]
    lo = 30
    per = lo + int(np.argmax(ac[lo:300]))
    n = spec.get("boards") or spec.get("slats") or spec.get("planks")
    sh = int(round(N * 1.25 / n))  # canvas strip height (canvas 1.25x final)
    m = 4
    stack = np.concatenate([lin, norm01(score)[..., None]], axis=2)
    strips, rows = strip_cells(stack, score, per, sh, m, spec.get("refine", 0.3), spec.get("fit_period", False))
    H = n * sh
    canvas = compose_strips(strips, n, sh, H, m, rng)
    y = np.arange(H)[:, None] + 0.5
    D = np.abs(((y + sh / 2) % sh) - sh / 2) * np.ones((1, H))
    canvas = np.concatenate([canvas, D[..., None].astype(np.float32)], axis=2)
    out = resize(canvas, N, N, periodic=True)
    if vertical:
        out = np.transpose(out, (1, 0, 2))
    info = {"joint_dist": out[..., 4], "mscore": out[..., 3], "jscale": N / H, "period": per,
            "strips": len(strips), "vertical": vertical}
    what = "planks" if vertical else ("slats" if "slats" in spec else "boards")
    steps = [
        "sRGB to linear; delight (sigma 125 px)",
        "joint score '%s'; %s period %d px by autocorrelation; %d joint-to-joint source strips" % (spec["mode"], what, per, len(strips)),
        "each strip made periodic along its length (min-cut quilting of source strips, 96 px overlap)",
        "%d %s stacked per 2 m (%.0f mm pitch), random order and offsets, feathered joints" % (n, what, 2000 / n),
        "periodic Lanczos resample to 1024 px",
    ]
    return out[..., :3], info, steps


def build_herringbone(src, src_lin, spec, rng):
    n_x = 14
    pid, ori, dist, Wpx = herringbone(N, n_x, ss=2)
    d = delight(src_lin, 125)
    L = src.mean(2)
    joint = (L < blur_reflect(L, 6) * 0.82).astype(np.float32)
    interior = blur_reflect(joint, 4) < 0.02
    ys, xs = np.nonzero(interior[20:-20, 20:-20])
    ys += 20
    xs += 20
    # per-paver colours: 9x9 means at random interior points
    k = 600
    sel = rng.integers(0, len(ys), k)
    box = blur_reflect(d, 3.0)
    cols = box[ys[sel], xs[sel]]
    jcol = np.median(d[joint > 0.5], axis=0)
    # speckle detail: source luminance ratio to its local mean, joints neutralised
    Y = lum(d)
    ratio = Y / (blur_reflect(Y, 5) + 1e-4)
    ratio = np.where(blur_reflect(joint, 2) > 0.05, 1.0, ratio)
    O = 160
    sp = wrap_tile(resize(ratio[..., None].repeat(3, 2), N + O, N + O), N, N, O)[..., 0]
    sp2 = resize(np.tile(sp[..., None], (2, 2, 1)), 2 * N, 2 * N, periodic=True)[..., 0]
    ids = np.unique(pid)
    lut = np.zeros((ids.max() + 1, 3), np.float32)
    lut[ids] = cols[rng.integers(0, k, len(ids))]
    base = lut[pid]
    R = pid.shape[0]
    lowf = periodic_noise(R, R, R / 6, 11, octaves=3)
    base *= (0.9 + 0.2 * lowf)[..., None]
    base *= np.clip(sp2, 0.6, 1.5)[..., None] ** 0.9
    jw = 0.045  # joint half width in paver widths (~4.5 mm)
    edge = smoothstep(jw, jw + 0.10, dist)  # 0 at joint
    chip = periodic_noise(R, R, 18, 21, octaves=3)
    edge_w = smoothstep(jw, jw + 0.06 + 0.10 * chip, dist)
    jfill = jcol[None, None, :] * (0.8 + 0.4 * periodic_noise(R, R, 12, 5, octaves=2))[..., None]
    colr = base * (0.82 + 0.18 * edge_w)[..., None]
    colr = colr * edge_w[..., None] + jfill * (1 - edge_w[..., None])
    hgt = np.where(dist > jw, 1.0, 0.0) * (0.85 + 0.15 * smoothstep(jw, jw + 0.15, dist))
    hgt = blur_wrap(hgt.astype(np.float32), 1.0)
    stack = np.concatenate([colr, hgt[..., None], dist[..., None]], axis=2)
    out = resize(stack, N, N, periodic=True)
    info = {"height_base": out[..., 3], "joint_dist_w": out[..., 4], "paver_mm": 2000 / (n_x * np.sqrt(2))}
    steps = [
        "sRGB to linear; delight (sigma 125 px)",
        "analytic 45-degree herringbone, 2:1 pavers, lattice %d x %d per 2 m (paver %.0f x %.0f mm), rendered at 2x and periodic-downsampled" % (
            n_x, n_x // 2, 2 * info["paver_mm"], info["paver_mm"]),
        "per-paver colour drawn from 600 sampled source paver interiors; source speckle (luminance / local mean, joints removed) made tileable by min-cut wrap and multiplied in",
        "joint fill colour = median of source joint pixels; edge wear and chipped arrises from periodic noise",
    ]
    return out[..., :3], info, steps


def build_grass(src_lin, spec, rng):
    t, info, steps = build_stochastic(src_lin, spec)
    # autumn/damp: pull hue toward olive-brown in patches, add soil showing through
    nz = periodic_noise(N, N, 220, 31, octaves=4)
    nz2 = periodic_noise(N, N, 60, 37, octaves=3)
    Y = lum(t)
    olive = np.array([0.30, 0.28, 0.14], np.float32)
    brown = np.array([0.30, 0.22, 0.13], np.float32)
    olive /= olive @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    brown /= brown @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    green_chroma = t / (Y[..., None] + 1e-5)
    mix = smoothstep(0.45, 0.75, nz)[..., None] * 0.6
    chroma = green_chroma * (1 - mix) + olive * mix
    dead = smoothstep(0.62, 0.8, nz2 * 0.6 + nz * 0.4)[..., None] * 0.5
    chroma = chroma * (1 - dead) + brown * dead
    t2 = chroma * Y[..., None]
    soil_src, _ = load_source(27)
    soil, _, _ = build_stochastic(srgb_to_lin(soil_src), SPECS["hr_soil"])
    soil = grade(soil, sat=0.7, mean_y=0.03)
    bare = smoothstep(0.66, 0.82, periodic_noise(N, N, 160, 41, octaves=4) * 0.7 + nz2 * 0.3)
    bare = bare * smoothstep(0.35, 0.15, Y / Y.mean() * 0.5)  # soil shows between blades
    bare = np.clip(bare * 1.6, 0, 1)[..., None]
    t3 = t2 * (1 - bare) + soil * bare * (lum(t2).mean() / max(lum(soil).mean(), 1e-4)) * 0.8
    steps = steps + [
        "autumn grade: chroma pulled toward olive and dead-brown in periodic-noise patches",
        "tileable hr_soil blended into blade gaps in bare patches",
    ]
    info["bare"] = bare[..., 0]
    return t3.astype(np.float32), info, steps


# ============================================================ PBR maps
def make_maps(name, col_lin, info, spec, rng):
    texel_mm = COVERAGE[name] * 1000 / N
    hp = spec.get("hp", (0.8, 10))
    det = detail_height(col_lin, *hp)  # zscore
    kind = spec["kind"]
    joint = None
    if kind in ("bricks", "slabs"):
        D = info["joint_dist"]  # canvas px (values carried through the resample)
        # canvas px half-joint: bricks ~10 mm joint at 80 px per 77 mm course,
        # slabs ~10 mm joint at 300 px per 500 mm slab
        hw = 5.0 if kind == "bricks" else 3.0
        ms = info["mscore"]
        core = smoothstep(hw + 2.0, hw - 2.0, D)
        band = smoothstep(hw + 6.0, hw + 2.0, D)
        colm = smoothstep(0.55, 0.8, ms) * band
        joint = np.clip(np.maximum(core * 0.9, colm), 0, 1)
        joint = blur_wrap(joint, 0.7)
        pillow = smoothstep(hw, hw + 10, D)
        h01 = (1 - joint) * (0.8 + 0.2 * pillow) + 0.06 * det * spec.get("detail", 1.0) * (1 - joint)
        h_mm = h01 * spec["depth"]
    elif kind == "herringbone":
        base = info["height_base"]
        joint = 1 - np.clip(base, 0, 1)
        h01 = base + 0.05 * det * (base > 0.5)
        h_mm = h01 * spec["depth"]
    elif kind in ("strips", "strips_v"):
        D = info["joint_dist"]
        ms = info["mscore"]
        if name == "hr_shutter":
            # lath profile: rounded crown, groove at the interlock
            sh = 1024 * 1.25 / spec["slats"]
            t = np.clip(D / (sh / 2), 0, 1)  # 0 at joint, 1 at lath centre
            prof = np.sqrt(np.clip(1 - (1 - t) ** 2, 0, 1)) * 0.7 + 0.3 * smoothstep(0.0, 0.25, t)
            joint = 1 - smoothstep(0.0, 0.12, t)
            h01 = prof + 0.03 * det
        elif name == "hr_timber":
            joint = smoothstep(5.0, 1.5, D) * 0.9 + 0.1 * smoothstep(0.6, 0.85, ms) * smoothstep(8, 3, D)
            h01 = (1 - joint) + 0.12 * det
        else:  # board-marked concrete: small ridge/step at each board line
            ridge = smoothstep(4.0, 0.0, D)
            joint = ridge * 0.0
            step = smoothstep(-2.0, 2.0, D - 2.0)
            h01 = 0.5 + 0.5 * ridge - 0.15 * (1 - step) + 0.22 * det
        h_mm = h01 * spec["depth"]
    else:
        h01 = 0.5 + 0.18 * det
        h_mm = h01 * spec["depth"]
    h_mm = h_mm.astype(np.float32)
    nrm = height_to_normal(h_mm, texel_mm)
    hn = norm01(h_mm, 0.5, 99.5)
    ao = cavity_ao(hn, sigma=5.0, k=2.0 * spec.get("ao", 1.0), floor=0.5, sigma2=18.0)
    # roughness
    base, var = spec["rough"]
    rn = periodic_noise(N, N, 180, seed_of(name) % 1000, octaves=4)
    Yn = norm01(lum(col_lin))
    rough = base + var * (rn - 0.5) * 1.6 + 0.04 * (0.5 - Yn)
    if joint is not None:
        rough = rough + 0.06 * joint
    metal = np.zeros((N, N), np.float32)
    mkind = spec.get("metal")
    if spec.get("ground"):
        # wet-prone: puddle-ish lower roughness in low-lying, low-frequency regions
        wet = smoothstep(0.55, 0.8, periodic_noise(N, N, 260, seed_of(name) % 997 + 3, octaves=3))
        rough = rough - 0.12 * wet
        rough = np.clip(rough, 0.6, 0.85)
    if mkind == "full":
        dull = periodic_noise(N, N, 90, 71, octaves=4)
        metal[:] = 1.0
        rough = np.clip(rough + 0.12 * (dull - 0.5), 0.3, 0.65)
    elif mkind == "chips":
        chipn = periodic_noise(N, N, 14, 73, octaves=3) * 0.6 + periodic_noise(N, N, 120, 79, octaves=2) * 0.4
        chips = smoothstep(0.78, 0.82, chipn)
        metal = chips.astype(np.float32)
        info["chips"] = chips
        rough = np.clip(rough * (1 - chips) + 0.55 * chips, 0.3, 0.6)
    elif mkind == "rust":
        r, g, b = col_lin[..., 0], col_lin[..., 1], col_lin[..., 2]
        redness = (r - b) / (lum(col_lin) + 1e-3)
        rust = smoothstep(0.12, 0.55, blur_wrap(redness.astype(np.float32), 1.5))
        # unrusted areas are dull, dirty mill-scale steel: partly metallic only
        metal = np.clip(0.75 * (1 - rust), 0, 1).astype(np.float32)
        rough = np.clip(0.42 + 0.45 * rust + 0.08 * (rn - 0.5), 0.35, 0.92)
        info["rust_cover"] = float(rust.mean())
    elif name == "hr_shutter":
        rough = np.clip(rough, 0.38, 0.65)
    else:
        rough = np.clip(rough, 0.05, 0.95)
    orm = np.stack([ao, rough.astype(np.float32), metal], -1)
    return nrm, orm, hn


def post_colour(name, lin, spec, info, rng):
    """Weathering after grading: soot on stock brick, broad stains, chips on black steel."""
    if spec.get("soot"):
        s = periodic_noise(N, N, 260, 101, octaves=4)
        lin = lin * (1 - spec["soot"] * smoothstep(0.4, 0.85, s))[..., None]
    if spec.get("stain"):
        s = periodic_noise(N, N, 200, 103 + spec["src"], octaves=5)
        dirt = np.array([0.6, 0.55, 0.45], np.float32)
        a = spec["stain"] * smoothstep(0.45, 0.9, s)[..., None]
        lin = lin * (1 - a) + lin * dirt * a
    return lin.astype(np.float32)


def build(name, rng):
    spec = SPECS[name]
    src, path = load_source(spec["src"])
    src_lin = srgb_to_lin(src)
    t0 = time.time()
    kind = spec["kind"]
    if kind == "stochastic":
        col, info, steps = build_stochastic(src_lin, spec)
    elif kind == "bricks":
        col, info, steps = build_bricks(src, src_lin, spec, rng)
    elif kind == "slabs":
        col, info, steps = build_slabs(src, src_lin, spec, rng)
    elif kind == "strips":
        col, info, steps = build_strips(src, src_lin, spec, rng)
    elif kind == "strips_v":
        col, info, steps = build_strips(src, src_lin, spec, rng, vertical=True)
    elif kind == "herringbone":
        col, info, steps = build_herringbone(src, src_lin, spec, rng)
    elif kind == "grass":
        col, info, steps = build_grass(src_lin, spec, rng)
    col = np.clip(col, 0, None)
    # residual low-frequency flattening on the periodic tile (keeps re-laid cells honest)
    if kind in ("bricks", "slabs", "strips", "strips_v", "herringbone"):
        col = flatten_wrap(col, 160, 0.7)
        steps.append("periodic low-frequency flatten (sigma 160 px, 70%)")
    else:
        col = flatten_wrap(col, 200, 1.0)
        steps.append("periodic low-frequency flatten (sigma 200 px)")
    if spec.get("flat"):
        fs, fa = spec["flat"]
        col = flatten_wrap(col, fs, fa)
        steps.append("mid-frequency blotch reduction against visible repeats (sigma %d px, %d%%)" % (fs, fa * 100))
    if name == "hr_shutter":
        # the source bakes groove shading; compress it so the normal map carries the form
        Y = lum(col)
        prof = Y.mean(1, keepdims=True)
        col = col * ((prof.mean() / prof) ** 0.6)[..., None]
        steps.append("baked groove shading compressed 60% (row-profile division)")
    col = apply_grade(col, spec["grade"])
    sat, my, tint, ta, con = spec["grade"]
    steps.append("linear grade: saturation x%.2f, %.0f%% tint toward grime grey-brown, mean luminance %.3f" % (sat, ta * 100, my))
    col = post_colour(name, col, spec, info, rng)
    if spec.get("soot"):
        steps.append("soot darkening from periodic noise (%.0f%%)" % (spec["soot"] * 100))
    if spec.get("stain"):
        steps.append("broad dirt staining from periodic noise (%.0f%%)" % (spec["stain"] * 100))
    nrm, orm, hn = make_maps(name, col, info, spec, rng)
    if spec.get("metal") == "chips":
        chips = info["chips"][..., None]
        bare = np.array([0.30, 0.29, 0.28], np.float32)
        col = col * (1 - chips) + bare * chips
        steps.append("paint chips (periodic noise, ~%.1f%%) as bare steel, metalness 1" % (100 * float(info["chips"].mean())))
    if spec["kind"] in ("bricks", "slabs"):
        # mortar a touch darker in cavities so colour and AO agree
        pass
    srgb = lin_to_srgb(col)
    base = OUT / name
    save_webp(srgb, str(base) + "-color.webp", 90)
    save_webp(nrm, str(base) + "-normal.webp", 92)
    # ORM is low-frequency: half resolution saves a quarter of each set's texture memory.
    h, w = orm.shape[:2]
    save_webp(orm.reshape(h // 2, 2, w // 2, 2, -1).mean((1, 3)), str(base) + "-orm.webp", 92)
    ph = PHASE.get(name, (None, None))
    sr_out = seam_ratio_phase(srgb, *ph)
    sr_src = seam_ratio(src)
    sr_n = seam_ratio_phase(nrm, *ph)
    sr_o = seam_ratio_phase(orm, *ph)
    sr_plain = seam_ratio(srgb)
    # previews
    tile = np.tile(srgb, (4, 4, 1))
    save_png(resize(tile, 1024, 1024), SCRATCH / ("tile4_%s.png" % name))
    rec = {
        "name": name,
        "coverageMetres": COVERAGE[name],
        "source": {"path": str(path.relative_to(REPO)), "sha256": sha256(path), "pixels": [src.shape[1], src.shape[0]]},
        "method": kind,
        "processing": steps,
        "derived": {
            "height": "from processed colour: band-passed log luminance (sigma %s px)" % (list(spec.get("hp", (0.8, 10))),)
                      + ("; joint/mortar mask from the regular layout and the carried mortar score" if kind in ("bricks", "slabs", "strips", "strips_v", "herringbone") else ""),
            "heightDepthMillimetres": spec["depth"],
            "normal": "OpenGL (+Y), central differences of the height in millimetres over a %.2f mm texel" % (COVERAGE[name] * 1000 / N),
            "orm": "R cavity AO from height (two blur radii), G roughness base %.2f +/- %.2f with periodic noise%s, B metalness %s" % (
                spec["rough"][0], spec["rough"][1], ", clamped 0.60-0.85 with wet patches" if spec.get("ground") else "",
                {"full": "1 (bare galvanised)", "chips": "1 at paint chips only", "rust": "0.75 on dull bare steel, 0 on rust", "none": "0"}.get(spec.get("metal"), "0")),
        },
        "seamRatio": {"color": round(sr_out[2], 3), "colorXY": [round(sr_out[0], 3), round(sr_out[1], 3)],
                      "normal": round(sr_n[2], 3), "orm": round(sr_o[2], 3), "sourceColor": round(sr_src[2], 3),
                      "colorPlain": round(sr_plain[2], 3),
                      "method": ("phase-matched: wrap edge vs interior line pairs at the same joint phase (%s x, %s y periods per tile)" % ph)
                      if ph != (None, None) else "wrap-edge mean abs difference / mean adjacent-pixel difference"},
        "reusedPolyHaven": None,
        "files": {},
        "seconds": round(time.time() - t0, 1),
    }
    for suf in ("color", "normal", "orm"):
        p = OUT / ("%s-%s.webp" % (name, suf))
        rec["files"][suf] = {"path": str(p.relative_to(REPO)), "bytes": p.stat().st_size, "sha256": sha256(p),
                             "pixels": [N, N], "colorSpace": "sRGB" if suf == "color" else "Non-Color",
                             "webpQuality": 90 if suf == "color" else 92}
    extra = {k: v for k, v in info.items() if isinstance(v, (int, float, str, bool))}
    if extra:
        rec["analysis"] = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in extra.items()}
    return rec


def merge_manifest(records):
    data = {}
    if MANIFEST.exists():
        data = json.loads(MANIFEST.read_text())
    tex = {r["name"]: r for r in data.get("tilingTextures", [])}
    for r in records:
        tex[r["name"]] = r
    data["tilingTextures"] = [tex[k] for k in SPECS if k in tex]
    write_json(MANIFEST, data)


def main(names):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []
    for name in names:
        rng = np.random.default_rng(seed_of(name))
        r = build(name, rng)
        print("%-18s seam color %.3f (src %.3f) normal %.3f orm %.3f  %.1fs" % (
            name, r["seamRatio"]["color"], r["seamRatio"]["sourceColor"], r["seamRatio"]["normal"], r["seamRatio"]["orm"], r["seconds"]), flush=True)
        recs.append(r)
    merge_manifest(recs)


if __name__ == "__main__":
    main(sys.argv[1:] or list(SPECS))
