"""Shared image utilities for the Heron Reach texture kit.

numpy + Pillow only. Every operation that has to stay tileable works on periodic
(wrap-around) images: blurs and resampling use FFTs or circular kernels.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
SRC30 = REPO / "assets/textures/source-30"
OUT = REPO / "public/materials/heron"
SCRATCH = Path(os.environ.get("HERON_TEX_SCRATCH", "/tmp/heron-tex-scratch"))


# ---------------------------------------------------------------- colour space
def srgb_to_lin(a):
    a = np.clip(a, 0.0, 1.0)
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4).astype(np.float32)


def lin_to_srgb(a):
    a = np.clip(a, 0.0, 1.0)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055).astype(np.float32)


def lum(lin):
    return (lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722).astype(np.float32)


# ---------------------------------------------------------------- io
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_source(num):
    path = next(SRC30.glob("%02d-*.png" % num))
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255.0
    return a, path


def to_u8(a):
    return (np.clip(a, 0, 1) * 255.0 + 0.5).astype(np.uint8)


def save_webp(a, path, quality, srgb_input=True):
    """a: float array in display space (already sRGB for colour, raw for data)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    u = to_u8(a)
    if u.ndim == 2:
        im = Image.fromarray(u, "L").convert("RGB")
    elif u.shape[2] == 4:
        im = Image.fromarray(u, "RGBA")
    else:
        im = Image.fromarray(u, "RGB")
    im.save(path, "WEBP", quality=quality, method=6)
    return path


def save_png(a, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    u = to_u8(a)
    Image.fromarray(u).save(path)
    return path


# ---------------------------------------------------------------- filters
def _gauss_tf(n, sigma):
    f = np.fft.fftfreq(n)
    return np.exp(-2.0 * (np.pi * f * sigma) ** 2)


def blur_wrap(a, sigma, sy=None):
    """Periodic Gaussian blur by FFT. sigma in pixels (sy optional for anisotropic)."""
    sy = sigma if sy is None else sy
    h, w = a.shape[:2]
    tf = _gauss_tf(h, sy)[:, None] * _gauss_tf(w, sigma)[None, :]
    if a.ndim == 2:
        return np.real(np.fft.ifft2(np.fft.fft2(a) * tf)).astype(np.float32)
    out = np.empty_like(a)
    for c in range(a.shape[2]):
        out[..., c] = np.real(np.fft.ifft2(np.fft.fft2(a[..., c]) * tf))
    return out


def blur_reflect(a, sigma):
    """Gaussian blur for non-periodic images: mirror-pad, blur periodically, crop."""
    h, w = a.shape[:2]
    p = int(min(3 * sigma, h - 1, w - 1))
    pad = ((p, p), (p, p)) + (((0, 0),) if a.ndim == 3 else ())
    b = blur_wrap(np.pad(a, pad, mode="reflect"), sigma)
    return b[p:p + h, p:p + w]


def box_wrap(a, r):
    return blur_wrap(a, r / 1.7)


def periodic_noise(h, w, scale, seed, octaves=4, persistence=0.55, aniso=1.0):
    """Tileable fractal noise in [0,1]. scale = feature size in pixels of the first octave."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    s = float(scale)
    for _ in range(octaves):
        n = rng.standard_normal((h, w)).astype(np.float32)
        n = blur_wrap(n, s / 2.5, s / 2.5 * aniso)
        n /= n.std() + 1e-8
        out += amp * n
        tot += amp
        amp *= persistence
        s /= 2.0
    out /= tot
    out = (out - out.min()) / (out.max() - out.min() + 1e-8)
    return out


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def norm01(a, lo=1, hi=99):
    p0, p1 = np.percentile(a, [lo, hi])
    return np.clip((a - p0) / (p1 - p0 + 1e-8), 0, 1).astype(np.float32)


def zscore(a):
    return ((a - a.mean()) / (a.std() + 1e-8)).astype(np.float32)


# ---------------------------------------------------------------- resampling
def _lanczos(x, a=3):
    x = np.asarray(x, np.float64)
    out = np.sinc(x) * np.sinc(x / a)
    out[np.abs(x) >= a] = 0
    return out


def _resample_matrix(n_in, n_out, periodic, a=3):
    scale = n_in / n_out
    support = a * max(scale, 1.0)
    M = np.zeros((n_out, n_in), np.float64)
    for i in range(n_out):
        c = (i + 0.5) * scale - 0.5
        lo = int(np.floor(c - support)) - 1
        hi = int(np.ceil(c + support)) + 1
        idx = np.arange(lo, hi + 1)
        wts = _lanczos((idx - c) / max(scale, 1.0), a)
        if periodic:
            idx = idx % n_in
        else:
            idx = np.clip(idx, 0, n_in - 1)
        np.add.at(M[i], idx, wts)
        M[i] /= M[i].sum()
    return M.astype(np.float32)


def resize(a, h, w, periodic=False):
    My = _resample_matrix(a.shape[0], h, periodic)
    Mx = _resample_matrix(a.shape[1], w, periodic)
    if a.ndim == 2:
        return My @ a @ Mx.T
    return np.stack([My @ a[..., c] @ Mx.T for c in range(a.shape[2])], axis=2)


# ---------------------------------------------------------------- seams
def seam_ratio(t):
    """Opposite-edge difference divided by the typical adjacent-pixel difference.

    1.0 means the wrap-around edge is statistically indistinguishable from any interior
    column/row step. Returns (horizontal, vertical, combined)."""
    a = t.astype(np.float32)
    if a.ndim == 3:
        a = a[..., :3].mean(2)
    dx = np.abs(np.diff(a, axis=1)).mean()
    dy = np.abs(np.diff(a, axis=0)).mean()
    ex = np.abs(a[:, 0] - a[:, -1]).mean()
    ey = np.abs(a[0, :] - a[-1, :]).mean()
    rx, ry = ex / (dx + 1e-9), ey / (dy + 1e-9)
    return float(rx), float(ry), float(max(rx, ry))


def _closed_min_path(err, margin):
    """Minimum-cost path across columns of err (O rows x N cols), |step|<=1,
    constrained to return to its start row (closed loop for wrap-around)."""
    O, N = err.shape
    e = err.astype(np.float64).copy()
    big = 1e12
    e[:margin, :] = big
    e[O - margin:, :] = big
    starts = np.arange(O)
    C = np.full((O, O), big)
    C[starts, starts] = e[starts, 0]
    back = np.zeros((N, O, O), np.int8)
    for x in range(1, N):
        up = np.concatenate([np.full((O, 1), big), C[:, :-1]], axis=1)
        dn = np.concatenate([C[:, 1:], np.full((O, 1), big)], axis=1)
        stack = np.stack([up, C, dn], 0)
        k = np.argmin(stack, 0)
        C = np.take_along_axis(stack, k[None], 0)[0] + e[:, x][None, :]
        back[x] = (k - 1).astype(np.int8)
    # end must be within one step of the start row
    best, bs, be = big * 10, 0, 0
    for s in range(margin, O - margin):
        for d in (-1, 0, 1):
            j = s + d
            if 0 <= j < O and C[s, j] < best:
                best, bs, be = C[s, j], s, j
    path = np.zeros(N, np.int64)
    j = be
    for x in range(N - 1, -1, -1):
        path[x] = j
        if x > 0:
            j = j + int(back[x, bs, j])
    return path


def _wrap_axis1(a, W, O, feather, margin):
    """a: (H, W+O, C). Returns (H, W, C) periodic along axis 1 using a min-cut seam
    through the O-wide overlap between the tail a[:, W:] and the head a[:, :O]."""
    tail = a[:, W:W + O]
    head = a[:, :O]
    err = ((tail[..., :3] - head[..., :3]) ** 2).sum(-1)  # (H, O)
    err = blur_reflect(err.astype(np.float32), 1.0)
    path = _closed_min_path(err.T, margin)  # path[y] = cut column
    cols = np.arange(O)[None, :]
    m = (cols < path[:, None]).astype(np.float32)  # 1 -> use tail (continuation)
    if feather > 0:
        m = blur_reflect(m, feather)
        m[:, :max(1, margin // 3)] = 1.0
        m[:, O - max(1, margin // 3):] = 0.0
    m = m[..., None]
    out = a[:, :W].copy()
    out[:, :O] = m * tail + (1 - m) * head
    return out


def wrap_tile(a, W, H, O, feather=2.0, margin=None):
    """Make a (H+O, W+O, C) crop tileable to (H, W, C) with two closed min-cut passes."""
    margin = margin or max(6, O // 6)
    assert a.shape[0] >= H + O and a.shape[1] >= W + O
    a = a[:H + O, :W + O]
    b = _wrap_axis1(a, W, O, feather, margin)  # periodic in x, height H+O
    c = _wrap_axis1(np.transpose(b, (1, 0, 2)), H, O, feather, margin)
    return np.transpose(c, (1, 0, 2))


def wrap_1d(a, W, O, feather=2.0, margin=None):
    """Make a strip periodic along axis 1 only."""
    margin = margin or max(6, O // 6)
    return _wrap_axis1(a[:, :W + O], W, O, feather, margin)


def quilt_concat(a, b, O, feather=2.0, margin=None):
    """Join strip b after strip a along axis 1 with an O-wide min-cut overlap."""
    margin = margin or max(4, O // 6)
    joined = np.concatenate([a, b[:, O:]], axis=1)
    La = a.shape[1]
    # reuse the wrap machinery: treat a's tail and b's head as the overlap pair
    tmp = np.concatenate([b[:, :O], a[:, La - O:]], axis=1)  # head=b, tail=a
    blended = _wrap_axis1(tmp, O, O, feather, margin)  # (H, O): tail(a) left of cut
    joined[:, La - O:La] = blended
    return joined


# ---------------------------------------------------------------- delighting / grading
def delight(lin, sigma, strength=1.0):
    """Divide out low-frequency luminance (baked lighting), keep chroma."""
    Y = lum(lin) + 1e-4
    B = blur_reflect(Y, sigma)
    ratio = (B.mean() / B) ** strength
    return (lin * ratio[..., None]).astype(np.float32)


def flatten_wrap(lin, sigma, strength=1.0):
    """Same as delight but for periodic images."""
    Y = lum(lin) + 1e-4
    B = blur_wrap(Y, sigma)
    ratio = (B.mean() / B) ** strength
    return (lin * ratio[..., None]).astype(np.float32)


def grade(lin, sat=1.0, mean_y=None, tint=None, tint_amt=0.0, contrast=1.0, lift=0.0):
    """Linear-light grade: saturation about luminance, mean luminance target,
    tint toward a grime colour, log-contrast about the mean."""
    Y = lum(lin)[..., None] + 1e-5
    chroma = lin / Y
    chroma = 1.0 + (chroma - 1.0) * sat
    if tint is not None and tint_amt:
        t = np.asarray(tint, np.float32)
        t = t / (t @ np.array([0.2126, 0.7152, 0.0722], np.float32))
        chroma = chroma * (1 - tint_amt) + t * tint_amt
    if contrast != 1.0:
        lY = np.log(Y)
        m = lY.mean()
        Y = np.exp(m + (lY - m) * contrast)
    if mean_y is not None:
        Y = Y * (mean_y / Y.mean())
    out = np.clip(chroma * Y + lift, 0, 1)
    return out.astype(np.float32)


# ---------------------------------------------------------------- PBR derivation
def height_to_normal(h_mm, texel_mm, strength=1.0):
    """OpenGL (+Y up) tangent-space normal from a periodic height field in millimetres."""
    dx = (np.roll(h_mm, -1, 1) - np.roll(h_mm, 1, 1)) / (2 * texel_mm)
    dyr = (np.roll(h_mm, -1, 0) - np.roll(h_mm, 1, 0)) / (2 * texel_mm)  # d/drow (down)
    nx = -dx * strength
    ny = dyr * strength  # v points up = -row
    nz = np.ones_like(nx)
    n = np.stack([nx, ny, nz], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (n * 0.5 + 0.5).astype(np.float32)


def cavity_ao(h01, sigma=6.0, k=2.2, floor=0.45, sigma2=None):
    """Ambient occlusion from height cavities (periodic)."""
    c = blur_wrap(h01, sigma) - h01
    if sigma2:
        c = 0.6 * c + 0.4 * (blur_wrap(h01, sigma2) - h01)
    c = np.clip(c, 0, None)
    c = c / (np.percentile(c, 99.5) + 1e-6)
    return np.clip(1.0 - k * 0.3 * c, floor, 1.0).astype(np.float32)


def detail_height(lin, s_hi=0.8, s_lo=12.0):
    """Band-passed log luminance as a periodic height proxy (bright = high)."""
    L = np.log(lum(lin) + 0.01)
    h = blur_wrap(L, s_hi) - blur_wrap(L, s_lo)
    return zscore(h)


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def seam_ratio_phase(t, nx=None, ny=None):
    """Seam ratio for structured tiles: the wrap edge is compared with interior line pairs
    at the same structural phase (e.g. the same bed joint position), so a joint that sits
    on the tile edge is not mistaken for a seam. nx/ny = structural periods per tile."""
    a = t.astype(np.float32)
    if a.ndim == 3:
        a = a[..., :3].mean(2)
    H, W = a.shape
    plain = seam_ratio(t)

    def ax(arr, n, plain_r):
        if not n:
            return plain_r
        L = arr.shape[1]
        edge = np.abs(arr[:, 0] - arr[:, -1]).mean()
        refs = []
        for j in range(1, n):
            p = int(round(j * L / n))
            refs.append(np.abs(arr[:, p] - arr[:, p - 1]).mean())
        return float(edge / (np.mean(refs) + 1e-9))

    rx = ax(a, nx, plain[0])
    ry = ax(a.T, ny, plain[1])
    return rx, ry, max(rx, ry)
