"""Generate the Heron Reach foliage textures (all original, procedural numpy/Pillow).

Run:  python3 scripts/maps/art/make_heron_foliage_textures.py
Writes WebP files to public/materials/heron/foliage/. Deterministic: every generator
uses its own fixed seed. Nothing is downloaded or traced; leaf outlines, veins, bark
plates and lenticels are drawn from analytic shapes and filtered noise.
"""
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heron_foliage_atlas import (CLUSTER_LAYOUT, GRASS_COLUMNS, GRASS_TUFTS, HEDGE_LAYOUT,  # noqa: E402
                                 LITTER_CELLS, SIZE, WEED_LAYOUT)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "public", "materials", "heron", "foliage")
SS = 2  # supersampling factor for atlases


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------

def fft_noise(shape, rng, beta=2.0, fmin=0.0, fmax=None, aniso=(1.0, 1.0)):
    """Periodic coloured noise (tiles seamlessly). Frequencies in cycles per image."""
    h, w = shape
    white = rng.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None] * h * aniso[1]
    fx = np.fft.rfftfreq(w)[None, :] * w * aniso[0]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1.0
    filt = 1.0 / f ** beta
    if fmin > 0:
        filt *= 1.0 / (1.0 + (fmin / f) ** 8)
    if fmax is not None:
        filt *= np.exp(-(f / fmax) ** 2)
    filt[0, 0] = 0.0
    n = np.fft.irfft2(np.fft.rfft2(white) * filt, s=(h, w))
    n -= n.mean()
    n /= (n.std() + 1e-9)
    return n


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    t = np.asarray(t)
    if t.ndim and t.shape[-1:] != (3,):
        t = t[..., None]
    return a * (1 - t) + b * t


def worley(size, cells, rng, warp=None, aniso=(1.0, 1.0), jitter=0.9):
    """Periodic Worley noise. Returns F1, F2 (in cell units) and nearest cell id."""
    g = cells
    jx = rng.uniform(0.5 - jitter / 2, 0.5 + jitter / 2, (g, g))
    jy = rng.uniform(0.5 - jitter / 2, 0.5 + jitter / 2, (g, g))
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float64)
    u = (xs + 0.5) / size
    v = (ys + 0.5) / size
    if warp is not None:
        u = u + warp[0]
        v = v + warp[1]
    px = u * g
    py = v * g
    ci = np.floor(px).astype(int)
    cj = np.floor(py).astype(int)
    f1 = np.full(px.shape, 1e9)
    f2 = np.full(px.shape, 1e9)
    ids = np.zeros(px.shape, dtype=int)
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            ni = ci + di
            nj = cj + dj
            wi = np.mod(ni, g)
            wj = np.mod(nj, g)
            qx = ni + jx[wj, wi]
            qy = nj + jy[wj, wi]
            d = np.sqrt(((px - qx) * aniso[0]) ** 2 + ((py - qy) * aniso[1]) ** 2)
            cid = wj * g + wi
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            ids = np.where(closer, cid, ids)
            f1 = np.where(closer, d, f1)
    return f1, f2, ids


def height_to_normal(h, strength, wrap):
    if wrap:
        dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
        dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5
    else:
        dy, dx = np.gradient(h)
    # OpenGL convention: green = +Y = up in the image. Rows grow downwards, so dh/dy_up = -dh/drow.
    nx = -dx * strength
    ny = dy * strength
    nz = np.ones_like(h)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / l, ny / l, nz / l], -1)
    return (n * 0.5 + 0.5)


def box_blur(a, r, wrap=True):
    """Separable box blur via cumulative sums (radius r pixels)."""
    if r < 1:
        return a.copy()
    out = a
    for axis in (0, 1):
        if wrap:
            pad = np.concatenate([np.take(out, range(-r - 1, 0), axis=axis), out,
                                  np.take(out, range(0, r), axis=axis)], axis=axis)
        else:
            pad = np.pad(out, [(r + 1, r) if ax == axis else (0, 0) for ax in range(out.ndim)], mode="edge")
        c = np.cumsum(pad, axis=axis)
        n = out.shape[axis]
        hi = np.take(c, range(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, range(0, n), axis=axis)
        out = (hi - lo) / (2 * r + 1)
    return out


def pull_push_fill(rgb, a):
    """Fill colour under transparent pixels with nearby leaf colour, so mipmaps do not fringe."""
    h, w = a.shape
    levels = []
    c = rgb * a[..., None]
    al = a.copy()
    while min(c.shape[0], c.shape[1]) > 1:
        levels.append((c, al))
        hh, ww = c.shape[0] // 2, c.shape[1] // 2
        c = c[:hh * 2, :ww * 2].reshape(hh, 2, ww, 2, 3).sum((1, 3))
        al = al[:hh * 2, :ww * 2].reshape(hh, 2, ww, 2).sum((1, 3))
    # push down
    fill = c / np.maximum(al[..., None], 1e-6)
    for c_l, a_l in reversed(levels):
        up = np.repeat(np.repeat(fill, 2, 0), 2, 1)[:c_l.shape[0], :c_l.shape[1]]
        mine = c_l / np.maximum(a_l[..., None], 1e-6)
        t = np.clip(a_l, 0, 1)[..., None]
        fill = mine * t + up * (1 - t)
    out = rgb * a[..., None] + fill * (1 - a[..., None])
    return out


def to_u8(x):
    return np.clip(np.round(x * 255.0), 0, 255).astype(np.uint8)


def save_webp(arr, name, quality=90, lossless=False):
    path = os.path.join(OUT, name)
    mode = "RGBA" if arr.shape[-1] == 4 else "RGB"
    img = Image.fromarray(to_u8(arr), mode)
    if lossless:
        img.save(path, "WEBP", lossless=True, quality=100, method=6)
    else:
        img.save(path, "WEBP", quality=quality, alpha_quality=100, method=6)
    print("wrote", os.path.relpath(path, REPO), os.path.getsize(path) // 1024, "KiB")


def downsample(x, f):
    if f == 1:
        return x
    h, w = x.shape[:2]
    sh = (h // f, f, w // f, f) + x.shape[2:]
    return x.reshape(sh).mean((1, 3))


def seg_dist(px, py, ax, ay, bx, by):
    abx, aby = bx - ax, by - ay
    l2 = abx * abx + aby * aby + 1e-12
    t = np.clip(((px - ax) * abx + (py - ay) * aby) / l2, 0, 1)
    dx = px - (ax + t * abx)
    dy = py - (ay + t * aby)
    return np.sqrt(dx * dx + dy * dy), t


def C(*rgb):
    return np.array(rgb, dtype=np.float64)


# --------------------------------------------------------------------------------------
# Atlas canvas: leaves and stems composited painter-style at SS resolution
# --------------------------------------------------------------------------------------

class Canvas:
    def __init__(self, size=SIZE, ss=SS, seed=0):
        n = size * ss
        self.n = n
        self.ss = ss
        self.rgb = np.zeros((n, n, 3))
        self.a = np.zeros((n, n))
        self.h = np.zeros((n, n))
        rng = np.random.default_rng(seed + 991)
        self.blotch = fft_noise((n, n), rng, beta=2.2, fmin=6)
        self.fine = fft_noise((n, n), rng, beta=1.2, fmin=40)
        self.layer = 0.0
        self.clip = (0, n, 0, n)

    def set_clip(self, rect=None):
        if rect is None:
            self.clip = (0, self.n, 0, self.n)
        else:
            x, y, w, h = rect
            m = 2 * self.ss  # keep a small transparent gutter inside each cell
            self.clip = (x * self.ss + m, (x + w) * self.ss - m, y * self.ss + m, (y + h) * self.ss - m)

    def bbox(self, cx, cy, r):
        cx0, cx1, cy0, cy1 = self.clip
        x0 = int(max(cx0, math.floor(cx - r)))
        x1 = int(min(cx1, math.ceil(cx + r)))
        y0 = int(max(cy0, math.floor(cy - r)))
        y1 = int(min(cy1, math.ceil(cy + r)))
        return x0, x1, y0, y1

    def composite(self, sl, mask, col, height):
        ys, xs = sl
        m = mask
        self.rgb[ys, xs] = self.rgb[ys, xs] * (1 - m[..., None]) + col * m[..., None]
        self.h[ys, xs] = self.h[ys, xs] * (1 - m) + height * m
        self.a[ys, xs] = np.maximum(self.a[ys, xs], m)

    # ---- stems -------------------------------------------------------------------------
    def stem(self, pts, r0, r1, col, dark=0.25):
        """Tapered polyline stem; pts in SS pixels; radii in SS pixels."""
        pts = np.asarray(pts, dtype=np.float64)
        rmax = max(r0, r1) + 2
        cx0, cx1, cy0, cy1 = self.clip
        x0 = max(cx0, int(pts[:, 0].min() - rmax))
        x1 = min(cx1, int(pts[:, 0].max() + rmax) + 1)
        y0 = max(cy0, int(pts[:, 1].min() - rmax))
        y1 = min(cy1, int(pts[:, 1].max() + rmax) + 1)
        if x1 <= x0 or y1 <= y0:
            return
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64) + 0.5
        best = np.full(xs.shape, 1e9)
        rad = np.zeros(xs.shape)
        nseg = len(pts) - 1
        lens = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        cum = np.concatenate([[0], np.cumsum(lens)])
        total = cum[-1] + 1e-9
        for i in range(nseg):
            d, t = seg_dist(xs, ys, pts[i, 0], pts[i, 1], pts[i + 1, 0], pts[i + 1, 1])
            s = (cum[i] + t * lens[i]) / total
            r = r0 + (r1 - r0) * s
            q = d / np.maximum(r, 0.3)
            better = q < best
            best = np.where(better, q, best)
            rad = np.where(better, r, rad)
        m = np.clip((1.0 - best) * np.maximum(rad, 0.5) + 0.5, 0, 1)
        prof = np.sqrt(np.clip(1 - best ** 2, 0, 1))
        shade = (1 - dark) + dark * prof
        colv = col[None, None, :] * shade[..., None]
        colv = colv * (1 + 0.08 * self.fine[y0:y1, x0:x1, None])
        hgt = self.layer + prof * rad * 0.08
        self.composite((slice(y0, y1), slice(x0, x1)), m, colv, hgt)
        self.layer += 0.02

    # ---- leaves ------------------------------------------------------------------------
    def leaf(self, kind, ox, oy, ang, L, base, alt, rng, edge=0.5, vein_light=0.12, gloss=False,
             holes=0, wet=0.0, curl=0.0, petiole=0.25, pet_col=None):
        """Draw one leaf. (ox, oy) is where the blade meets the petiole, ang the axis angle
        (0 = pointing up the image), L the blade length in SS pixels."""
        if petiole > 0:
            dx, dy = -math.sin(ang), math.cos(ang)
            pc = pet_col if pet_col is not None else base * 0.75
            self.stem([(ox, oy), (ox + dx * L * petiole, oy + dy * L * petiole)], L * 0.022, L * 0.03, pc)
        R = L * 1.25
        x0, x1, y0, y1 = self.bbox(ox, oy, R)
        if x1 <= x0 or y1 <= y0:
            return
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float64) + 0.5
        dx = xs - ox
        dy = ys - oy
        dirx, diry = math.sin(ang), -math.cos(ang)
        perx, pery = math.cos(ang), math.sin(ang)
        ly = (dx * dirx + dy * diry) / L
        lx = (dx * perx + dy * pery) / L
        shape = SHAPES[kind]
        sd, margin, veins = shape(lx, ly, rng)
        # sd: signed distance proxy in leaf units (positive inside)
        m = np.clip(sd * L + 0.5, 0, 1)
        if holes:
            for _ in range(holes):
                hx = rng.uniform(-0.25, 0.25)
                hy = rng.uniform(0.2, 0.8)
                hr = rng.uniform(0.02, 0.06)
                dh = np.sqrt((lx - hx) ** 2 + (ly - hy) ** 2) - hr
                m = m * np.clip(dh * L + 0.5, 0, 1)
        if m.max() <= 0:
            return
        bl = self.blotch[y0:y1, x0:x1]
        fn = self.fine[y0:y1, x0:x1]
        col = mix(base, alt, smoothstep(-0.4, 1.4, bl))
        edge_t = (1 - smoothstep(0.0, 0.16, margin)) * edge
        col = mix(col, alt * 0.55, edge_t)
        col = mix(col, np.minimum(col * 1.25 + 0.06, 1.0), veins * vein_light / 0.12 * 0.5)
        if wet > 0:
            spot = smoothstep(0.6, 1.6, self.blotch[y0:y1, x0:x1] * -1 + fn * 0.3)
            col = col * (1 - wet * 0.35 * spot[..., None])
        col = col * (1 + 0.05 * fn[..., None])
        dome = np.clip(margin, 0, 0.3) / 0.3
        hgt = self.layer + 0.6 * np.sqrt(dome) - 0.35 * veins + 0.04 * fn
        if curl:
            hgt = hgt + curl * (lx * 2) ** 2
        if gloss:
            hgt = hgt + 0.2 * np.sqrt(dome)
        self.composite((slice(y0, y1), slice(x0, x1)), m, col, hgt)
        self.layer += 0.05

    def finish(self):
        a = downsample(self.a, self.ss)
        rgb = downsample(self.rgb * self.a[..., None], self.ss) / np.maximum(a[..., None], 1e-6)
        h = downsample(self.h, self.ss)
        rgb = pull_push_fill(np.clip(rgb, 0, 1), a)
        return rgb, a, h


# --------------------------------------------------------------------------------------
# Leaf shapes in leaf units: ly from blade base (0) to tip (1), lx across.
# Each returns (signed distance, margin depth 0..1, vein intensity).
# --------------------------------------------------------------------------------------

def _veins(lx, ly, segs):
    v = np.zeros_like(lx)
    for (ax, ay, bx, by, w0, w1) in segs:
        d, t = seg_dist(lx, ly, ax, ay, bx, by)
        w = w0 + (w1 - w0) * t
        v = np.maximum(v, np.clip(1 - d / w, 0, 1))
    return v


def plane_shape(lx, ly, rng):
    # Palmate London plane leaf: three to five pointed lobes radiating from the petiole junction.
    five = rng.random() < 0.7
    j = lambda s: rng.uniform(-s, s)
    lobes = [(0.0 + j(0.06), 1.0, 0.78)]
    side_a = 0.95 + j(0.08)
    lobes += [(side_a, 0.88 + j(0.06), 0.72), (-side_a + j(0.05), 0.88 + j(0.06), 0.72)]
    if five:
        b = 1.95 + j(0.1)
        lobes += [(b, 0.5 + j(0.06), 0.62), (-b, 0.5 + j(0.06), 0.62)]
    else:
        lobes += [(1.95, 0.4, 0.7), (-1.95, 0.4, 0.7)]
    rho = np.sqrt(lx * lx + ly * ly)
    th = np.arctan2(lx, ly)
    at = np.abs(th)
    body = 0.5 * (1 - 0.72 * smoothstep(2.0, 3.14, at))
    k = 5.0
    acc = body ** k
    for (t0, a, w) in lobes:
        dth = np.angle(np.exp(1j * (th - t0)))
        lob = a * np.clip(1 - np.abs(dth) / w, 0, 1) ** 1.1
        acc = acc + lob ** k
    r = acc ** (1 / k)
    ph = rng.uniform(0, 1)
    tooth = np.mod(th * 10.0 / math.pi + ph, 1.0) ** 2.5
    r = r * (1 + 0.07 * tooth * (1 - smoothstep(2.2, 2.8, at)) * smoothstep(0.35, 0.7, r))
    sd = r - rho
    margin = np.clip(sd / np.maximum(r, 1e-3), 0, 1)
    segs = []
    for (t0, a, w) in lobes:
        tipx, tipy = math.sin(t0) * a * 0.93, math.cos(t0) * a * 0.93
        segs.append((0, 0, tipx, tipy, 0.022, 0.005))
        for f in (0.3, 0.5, 0.7):
            px, py = tipx * f, tipy * f
            for s in (-1, 1):
                ang = t0 + s * 0.8
                ln = 0.32 * a * (1 - f) + 0.08
                segs.append((px, py, px + math.sin(ang) * ln, py + math.cos(ang) * ln, 0.009, 0.003))
    veins = _veins(lx, ly, segs) * (sd > 0)
    return sd, margin, veins


def ovate_factory(W, p, q, taper, serr=0.0, serr_n=12, pairs=6, parallel=False, tip_pow=1.0,
                  lobed=0.0, lobes_n=5):
    def shape(lx, ly, rng):
        t = np.clip(ly, 0, 1)
        hw = W * np.sin(math.pi * t ** p) ** q * (1 - taper * t)
        hw = hw * np.where(t > 0.75, (1 - (t - 0.75) / 0.25) ** (tip_pow - 1) if tip_pow != 1 else 1.0, 1.0)
        if serr:
            ph = rng.uniform(0, 1)
            hw = hw * (1 + serr * np.mod(t * serr_n + ph, 1.0) ** 2 + 0.4 * serr * np.mod(t * serr_n * 2 + ph, 1.0) ** 2)
        if lobed:
            ph = rng.uniform(0, 0.3)
            ph_t = np.mod(t * lobes_n + ph, 1.0)
            # lobe tips point back towards the base: quick rise, long falling upper edge
            saw = np.where(ph_t < 0.18, ph_t / 0.18, 1 - (ph_t - 0.18) / 0.82)
            hw = hw * (1 - lobed + lobed * saw ** 1.8) * (0.6 + 0.4 * t)
        inside_y = np.minimum(ly, 1 - ly)
        sd = np.minimum(hw - np.abs(lx), inside_y * 0.5)
        sd = np.where((ly < 0) | (ly > 1), np.minimum(sd, -np.abs(np.minimum(ly, 1 - ly))), sd)
        margin = np.clip((hw - np.abs(lx)) / (W + 1e-6), 0, 1) * (sd > 0)
        segs = [(0, 0, 0, 0.97, 0.018, 0.004)]
        if parallel:
            for s in (-1, 1):
                for k in (0.5, 0.85):
                    prev = (0.0, 0.0)
                    for i in range(1, 9):
                        tt = i / 8
                        w = W * math.sin(math.pi * tt ** p) ** q * (1 - taper * tt) * k * 0.85
                        cur = (s * w, tt * 0.97)
                        segs.append((prev[0], prev[1], cur[0], cur[1], 0.008, 0.003))
                        prev = cur
        else:
            for i in range(pairs):
                t0 = 0.1 + i * (0.8 / pairs)
                t1 = min(t0 + 0.17, 0.98)
                w = W * math.sin(math.pi * t1 ** p) ** q * (1 - taper * t1) * 0.92
                for s in (-1, 1):
                    segs.append((0, t0, s * w, t1, 0.008, 0.0025))
        veins = _veins(lx, ly, segs) * (sd > 0)
        return sd, margin, veins
    return shape


SHAPES = {
    "plane": plane_shape,
    "birch": ovate_factory(W=0.36, p=0.55, q=0.9, taper=0.08, serr=0.08, serr_n=13, pairs=7, tip_pow=1.7),
    "privet": ovate_factory(W=0.25, p=0.95, q=0.7, taper=0.12, pairs=5),
    "laurel": ovate_factory(W=0.3, p=0.85, q=0.75, taper=0.1, pairs=7, serr=0.02, serr_n=20),
    "dandelion": ovate_factory(W=0.115, p=1.3, q=0.6, taper=-0.2, lobed=0.55, lobes_n=5, pairs=0),
    "plantain": ovate_factory(W=0.3, p=0.8, q=0.9, taper=0.1, parallel=True),
    "blade": ovate_factory(W=0.06, p=0.5, q=0.4, taper=0.6, pairs=0),
}


# --------------------------------------------------------------------------------------
# Colour palettes (sRGB 0..1). Muted and mid-valued so they survive translucency and fog.
# --------------------------------------------------------------------------------------

PLANE_PAL = [C(0.50, 0.53, 0.22), C(0.62, 0.56, 0.24), C(0.72, 0.58, 0.26), C(0.66, 0.49, 0.26),
             C(0.55, 0.38, 0.18), C(0.44, 0.30, 0.15)]
BIRCH_PAL = [C(0.62, 0.62, 0.26), C(0.78, 0.68, 0.25), C(0.80, 0.60, 0.20), C(0.70, 0.52, 0.20),
             C(0.55, 0.40, 0.18)]
PRIVET_PAL = [C(0.12, 0.19, 0.08), C(0.15, 0.24, 0.09), C(0.19, 0.28, 0.11), C(0.27, 0.35, 0.13),
              C(0.36, 0.36, 0.14)]
SHRUB_PAL = [C(0.14, 0.21, 0.10), C(0.18, 0.26, 0.11), C(0.23, 0.30, 0.13), C(0.30, 0.27, 0.14),
             C(0.33, 0.22, 0.14)]
LITTER_PAL = [C(0.40, 0.28, 0.13), C(0.48, 0.33, 0.14), C(0.34, 0.23, 0.11), C(0.55, 0.40, 0.17),
              C(0.42, 0.33, 0.16)]
BIRCH_LITTER_PAL = [C(0.58, 0.44, 0.18), C(0.48, 0.35, 0.15), C(0.40, 0.28, 0.13)]
TWIG = C(0.30, 0.26, 0.22)
TWIG_BIRCH = C(0.26, 0.19, 0.15)
TWIG_GREEN = C(0.24, 0.24, 0.14)


def pick(pal, rng, bias=None):
    i = rng.integers(len(pal)) if bias is None else int(np.clip(rng.normal(bias, 1.0), 0, len(pal) - 1))
    j = int(np.clip(i + rng.choice([-1, 1]), 0, len(pal) - 1))
    t = rng.uniform(0, 0.6)
    return pal[i] * (1 - t) + pal[j] * t, pal[min(len(pal) - 1, i + 1)]


def bezier(p0, p1, p2, n=12):
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def cell_px(rect):
    x, y, w, h = rect
    return x * SS, y * SS, w * SS, h * SS


# --------------------------------------------------------------------------------------
# Leaf atlases
# --------------------------------------------------------------------------------------

def cluster_twig(cv, rect, pivot, rng, kind, pal, n_leaves, leaf_len, twig_col, spread=0.9,
                 hang=False, opposite=False, bias=None, edge=0.5, vein_light=0.12, gloss=False,
                 petiole=0.25, top_y=0.3):
    cv.set_clip(rect)
    x, y, w, h = cell_px(rect)
    sx, sy = x + pivot[0] * w, y + pivot[1] * h
    top = (x + w * (0.5 + rng.uniform(-0.08, 0.08)), y + h * top_y * rng.uniform(0.9, 1.1))
    mid = (x + w * (0.5 + rng.uniform(-0.15, 0.15)), y + h * 0.6)
    pts = bezier((sx, sy), mid, top, 16)
    cv.stem(pts, w * 0.012, w * 0.005, twig_col, dark=0.35)
    nodes = []
    for i in range(n_leaves):
        f = 0.25 + 0.75 * (i + rng.uniform(-0.2, 0.2)) / max(1, n_leaves - 1) if n_leaves > 1 else 0.9
        f = float(np.clip(f, 0.15, 1.0))
        k = int(f * (len(pts) - 1))
        nodes.append((pts[k], f, i))
    for (p, f, i) in nodes:
        sides = [-1, 1] if opposite else [(-1) ** i]
        for side in sides:
            if f > 0.97 and not opposite:
                ang = rng.uniform(-0.2, 0.2)
            else:
                ang = side * spread * rng.uniform(0.6, 1.15) * (1.15 - 0.4 * f)
            if hang:
                ang = side * rng.uniform(1.6, 2.6)
            L = leaf_len * w * rng.uniform(0.8, 1.15) * (1.0 - 0.25 * f if opposite else 1.0)
            pet = L * petiole
            ox = p[0] + math.sin(ang) * pet
            oy = p[1] - math.cos(ang) * pet
            base, alt = pick(pal, rng, bias)
            cv.leaf(kind, ox, oy, ang, L, base, alt, rng, edge=edge, vein_light=vein_light, gloss=gloss,
                    petiole=petiole, pet_col=twig_col)
    cv.set_clip()


def single_leaf(cv, rect, pivot, rng, kind, pal, rel_len, twig_col, bias=None, edge=0.5, petiole=0.25,
                gloss=False, vein_light=0.12):
    cv.set_clip(rect)
    x, y, w, h = cell_px(rect)
    sx, sy = x + pivot[0] * w, y + pivot[1] * h
    L = h * rel_len
    pet = L * petiole
    ang = rng.uniform(-0.1, 0.1)
    ox = sx + math.sin(ang) * pet
    oy = sy - math.cos(ang) * pet
    base, alt = pick(pal, rng, bias)
    cv.leaf(kind, ox, oy, ang, L, base, alt, rng, edge=edge, petiole=petiole, pet_col=twig_col, gloss=gloss,
            vein_light=vein_light)
    cv.set_clip()


def write_atlas(name, cv, nstrength, extra_note=""):
    rgb, a, h = cv.finish()
    save_webp(np.concatenate([rgb, a[..., None]], -1), f"{name}-color.webp", quality=92)
    nrm = height_to_normal(h * 6.0, nstrength, wrap=False)
    flat = np.array([0.5, 0.5, 1.0])
    nrm = nrm * a[..., None] + flat * (1 - a[..., None])
    save_webp(nrm, f"{name}-normal.webp", quality=92)


def make_plane_atlas():
    rng = np.random.default_rng(4101)
    cv = Canvas(seed=4101)
    L = CLUSTER_LAYOUT
    # clusters: twiglet with 3 to 5 leaves
    for i, (nl, ll, b) in enumerate([(5, 0.23, 2.5), (4, 0.25, 1.2), (4, 0.25, 4.0)]):
        c = L["cluster"][i]
        cluster_twig(cv, c["rect"], c["pivot"], rng, "plane", PLANE_PAL, nl, ll, TWIG, bias=b, spread=1.35,
                     petiole=0.5, top_y=0.5)
    for i, c in enumerate(L["single"]):
        single_leaf(cv, c["rect"], c["pivot"], rng, "plane", PLANE_PAL, 0.4, TWIG, bias=[0.5, 2, 3, 4.5][i],
                    petiole=0.5)
    write_atlas("plane-leaf-atlas", cv, 1.6)


def make_birch_atlas():
    rng = np.random.default_rng(4202)
    cv = Canvas(seed=4202)
    L = CLUSTER_LAYOUT
    for i, c in enumerate(L["cluster"]):
        cluster_twig(cv, c["rect"], c["pivot"], rng, "birch", BIRCH_PAL, [9, 8, 7][i], 0.2, TWIG_BIRCH,
                     spread=1.0, bias=[1.0, 2.0, 3.0][i], edge=0.35, vein_light=0.08, petiole=0.3)
    for i, c in enumerate(L["single"]):
        cv.set_clip(c["rect"])
        x, y, w, h = cell_px(c["rect"])
        # small pairs of birch leaves on a short spur
        sx, sy = x + w * 0.5, y + h * 0.97
        cv.stem([(sx, sy), (sx, y + h * 0.55)], w * 0.012, w * 0.007, TWIG_BIRCH)
        for s in (-1, 1):
            ang = s * rng.uniform(0.4, 0.8)
            Ll = h * 0.42
            base, alt = pick(BIRCH_PAL, rng, [0.5, 1.5, 2.5, 3.5][i])
            cv.leaf("birch", sx + math.sin(ang) * Ll * 0.25, y + h * 0.6 - math.cos(ang) * Ll * 0.25, ang, Ll,
                    base, alt, rng, edge=0.3, vein_light=0.08, petiole=0.3, pet_col=TWIG_BIRCH)
    write_atlas("birch-leaf-atlas", cv, 1.4)


def make_shrub_atlas():
    rng = np.random.default_rng(4303)
    cv = Canvas(seed=4303)
    L = CLUSTER_LAYOUT
    for i, c in enumerate(L["cluster"]):
        cluster_twig(cv, c["rect"], c["pivot"], rng, "laurel", SHRUB_PAL, [7, 6, 6][i], 0.24, TWIG_GREEN,
                     spread=1.1, bias=[1.0, 1.5, 2.8][i], edge=0.25, vein_light=0.05, gloss=True, petiole=0.12)
    for i, c in enumerate(L["single"]):
        single_leaf(cv, c["rect"], c["pivot"], rng, "laurel", SHRUB_PAL, 0.62, TWIG_GREEN,
                    bias=[0.5, 1.5, 3.0, 4.0][i], edge=0.25, petiole=0.12, gloss=True, vein_light=0.05)
    write_atlas("shrub-leaf-atlas", cv, 1.8)


def make_hedge_atlas():
    rng = np.random.default_rng(4404)
    cv = Canvas(seed=4404)
    L = HEDGE_LAYOUT
    # opaque inner-foliage tile for the hidden core: dark base then many overlapping leaves
    cv.set_clip(L["core"]["rect"])
    x, y, w, h = cell_px(L["core"]["rect"])
    cv.rgb[y:y + h, x:x + w] = C(0.07, 0.09, 0.045)
    cv.a[y:y + h, x:x + w] = 1.0
    for k in range(900):
        depth = k / 900
        cx = x + rng.uniform(-0.05, 1.05) * w
        cy = y + rng.uniform(-0.05, 1.05) * h
        base, alt = pick(PRIVET_PAL, rng, 1.0)
        shade = 0.35 + 0.65 * depth
        cv.leaf("privet", cx, cy, rng.uniform(-math.pi, math.pi), w * rng.uniform(0.07, 0.1), base * shade,
                alt * shade, rng, edge=0.15, vein_light=0.04, gloss=True, petiole=0.0)
    cv.a[y:y + h, x:x + w] = 1.0
    for i, c in enumerate(L["cluster"]):
        cluster_twig(cv, c["rect"], c["pivot"], rng, "privet", PRIVET_PAL, [8, 7][i], 0.15, TWIG_GREEN,
                     spread=1.0, opposite=True, bias=[1.2, 2.0][i], edge=0.15, vein_light=0.05, gloss=True,
                     petiole=0.08)
    for i, c in enumerate(L["single"]):
        cv.set_clip(c["rect"])
        x, y, w, h = cell_px(c["rect"])
        sx, sy = x + w * 0.5, y + h * 0.97
        cv.stem([(sx, sy), (sx, y + h * 0.25)], w * 0.012, w * 0.006, TWIG_GREEN)
        for j, f in enumerate((0.7, 0.45)):
            for s in (-1, 1):
                ang = s * rng.uniform(0.5, 0.9)
                Ll = h * 0.36 * (1 - 0.2 * j)
                base, alt = pick(PRIVET_PAL, rng, [0.5, 1.5, 2.5, 3.5][i])
                cv.leaf("privet", sx, y + h * f, ang, Ll, base, alt, rng, edge=0.15, vein_light=0.05, gloss=True,
                        petiole=0.05, pet_col=TWIG_GREEN)
        base, alt = pick(PRIVET_PAL, rng, 3.0)
        cv.leaf("privet", sx, y + h * 0.27, 0.0, h * 0.24, base, alt, rng, edge=0.1, gloss=True, petiole=0.05)
    write_atlas("hedge-leaf-atlas", cv, 1.8)


def make_litter_atlas():
    rng = np.random.default_rng(4505)
    cv = Canvas(seed=4505)
    for c in LITTER_CELLS:
        cv.set_clip(c["rect"])
        x, y, w, h = cell_px(c["rect"])
        if c["kind"] == "plane":
            base, alt = pick(LITTER_PAL, rng)
            L = h * rng.uniform(0.36, 0.42)
            cv.leaf("plane", x + w * 0.5, y + h * 0.6, rng.uniform(-0.15, 0.15), L, base, alt * 0.8, rng,
                    edge=0.8, vein_light=0.1, holes=int(rng.integers(0, 3)), wet=1.0, curl=0.3, petiole=0.3,
                    pet_col=base * 0.6)
        else:
            for k in range(int(rng.integers(1, 3))):
                base, alt = pick(BIRCH_LITTER_PAL, rng)
                L = h * rng.uniform(0.38, 0.5)
                ang = rng.uniform(-0.6, 0.6) + (k * 2.6)
                ox = x + w * (0.5 - 0.35 * math.sin(ang) * 0.6)
                oy = y + h * (0.5 + 0.35 * math.cos(ang) * 0.6)
                cv.leaf("birch", ox, oy, ang, L, base, alt * 0.75, rng, edge=0.8, vein_light=0.06,
                        holes=int(rng.integers(0, 2)), wet=1.0, curl=0.2, petiole=0.25, pet_col=base * 0.6)
    rgb, a, h = cv.finish()
    rgb = rgb * 0.96  # wet darkening
    save_webp(np.concatenate([rgb, a[..., None]], -1), "leaf-litter-color.webp", quality=92)
    nrm = height_to_normal(h * 6.0, 1.5, wrap=False)
    nrm = nrm * a[..., None] + np.array([0.5, 0.5, 1.0]) * (1 - a[..., None])
    save_webp(nrm, "leaf-litter-normal.webp", quality=92)


# --------------------------------------------------------------------------------------
# Grass and weeds
# --------------------------------------------------------------------------------------

GRASS_GREENS = [C(0.20, 0.27, 0.11), C(0.24, 0.31, 0.12), C(0.28, 0.34, 0.14), C(0.18, 0.24, 0.10),
                C(0.26, 0.29, 0.12), C(0.34, 0.35, 0.16)]
GRASS_DRY = [C(0.55, 0.48, 0.30), C(0.48, 0.41, 0.26), C(0.62, 0.55, 0.36), C(0.42, 0.36, 0.22)]


def make_grass_atlas():
    rng = np.random.default_rng(4606)
    cv = Canvas(seed=4606)
    n = cv.n
    # blade columns
    for i, c in enumerate(GRASS_COLUMNS):
        x, y, w, h = cell_px(c["rect"])
        ys, xs = np.mgrid[y:y + h, x:x + w].astype(np.float64) + 0.5
        u = (xs - x) / w  # 0..1 across
        t = 1 - (ys - y) / h  # 0 at base (bottom) .. 1 at tip (top)
        margin = 3.0 * SS / w
        half = 0.5 - margin
        tip_start = 0.9
        hw = np.where(t < tip_start, half, half * np.clip((1 - t) / (1 - tip_start), 0, 1) ** 0.8)
        sd = (hw - np.abs(u - 0.5)) * w
        m = np.clip(sd + 0.5, 0, 1)
        green = GRASS_GREENS[i % len(GRASS_GREENS)] * rng.uniform(0.9, 1.1)
        dry = GRASS_DRY[i % len(GRASS_DRY)]
        if i in (5, 10):  # fully yellowed blades
            green = mix(green, dry, 0.65)
        dry_len = rng.uniform(0.08, 0.4)
        ragged = 0.03 * cv.fine[y:y + h, x:x + w]
        dry_t = smoothstep(1 - dry_len - 0.05, 1 - dry_len + 0.05, t + ragged)
        base_t = 1 - smoothstep(0.0, 0.15, t)
        col = mix(green, green * 0.7 + C(0.08, 0.07, 0.03), base_t * 0.7)
        col = mix(col, dry, dry_t)
        # brown transition band where the tip dies back
        band = np.exp(-((t - (1 - dry_len)) / 0.025) ** 2)
        col = mix(col, C(0.32, 0.22, 0.12), band * 0.6)
        stri = 0.06 * np.sin((u - 0.5) * math.pi * 9 + i) * (1 - dry_t * 0.5)
        rib = np.exp(-((u - 0.5) / 0.05) ** 2)
        col = col * (1 + stri[..., None] + 0.12 * rib[..., None] + 0.04 * cv.fine[y:y + h, x:x + w, None])
        hgt = 0.5 - np.abs(u - 0.5) * 1.6 + 0.2 * rib
        cv.composite((slice(y, y + h), slice(x, x + w)), m, col, hgt)
    # tuft cards: side view blades from bottom centre
    for k, c in enumerate(GRASS_TUFTS):
        cv.set_clip(c["rect"])
        x, y, w, h = cell_px(c["rect"])
        bx, by = x + w * 0.5, y + h * 0.995
        for b in range(46):
            lean = rng.normal(0, 0.45)
            length = h * rng.uniform(0.45, 0.95)
            ex = bx + math.sin(lean) * length * 0.8 + rng.normal(0, w * 0.05)
            ey = by - math.cos(lean) * length * rng.uniform(0.7, 1.0)
            cx = bx + (ex - bx) * 0.3 + rng.normal(0, w * 0.03)
            cy = by - length * 0.55
            pts = bezier((bx + rng.normal(0, w * 0.04), by), (cx, cy), (ex, ey), 14)
            green = GRASS_GREENS[int(rng.integers(len(GRASS_GREENS)))] * rng.uniform(0.85, 1.15)
            dry = GRASS_DRY[int(rng.integers(len(GRASS_DRY)))]
            split = int(len(pts) * rng.uniform(0.55, 0.9))
            r0 = w * rng.uniform(0.012, 0.02)
            rmid = r0 * (1 - split / len(pts) * 0.6)
            cv.stem(pts[:split + 1], r0, rmid, green, dark=0.3)
            cv.stem(pts[split:], rmid, 0.6, dry, dark=0.3)
    rgb, a, h = cv.finish()
    save_webp(np.concatenate([rgb, a[..., None]], -1), "grass-blades-color.webp", quality=92)
    nrm = height_to_normal(h * 4.0, 1.2, wrap=False)
    nrm = nrm * a[..., None] + np.array([0.5, 0.5, 1.0]) * (1 - a[..., None])
    save_webp(nrm, "grass-blades-normal.webp", quality=92)


WEED_GREENS = [C(0.18, 0.27, 0.10), C(0.22, 0.31, 0.12), C(0.16, 0.23, 0.09), C(0.28, 0.32, 0.13)]


def make_weed_atlas():
    rng = np.random.default_rng(4707)
    cv = Canvas(seed=4707)
    W = WEED_LAYOUT
    for c in W["dandelion"]:
        cv.set_clip(c["rect"])
        x, y, w, h = cell_px(c["rect"])
        base, alt = pick(WEED_GREENS, rng)
        cv.leaf("dandelion", x + w * 0.5, y + h * 0.99, 0.0, h * 0.95, base, base * 0.8 + C(0.05, 0.02, 0.0), rng,
                edge=0.5, vein_light=0.2, petiole=0.0)
    for c in W["plantain"]:
        cv.set_clip(c["rect"])
        x, y, w, h = cell_px(c["rect"])
        base, alt = pick(WEED_GREENS, rng)
        cv.stem([(x + w * 0.5, y + h * 0.99), (x + w * 0.5, y + h * 0.62)], w * 0.05, w * 0.035, base * 1.15)
        cv.leaf("plantain", x + w * 0.5, y + h * 0.64, 0.0, h * 0.6, base, base * 0.75 + C(0.06, 0.04, 0.0), rng,
                edge=0.35, vein_light=0.18, petiole=0.0)
    # crack weed: short grassy tuft with seed panicles
    cv.set_clip(W["crack"]["rect"])
    x, y, w, h = cell_px(W["crack"]["rect"])
    bx, by = x + w * 0.5, y + h * 0.995
    for b in range(40):
        lean = rng.normal(0, 0.55)
        length = h * rng.uniform(0.25, 0.6)
        ex = bx + math.sin(lean) * length
        ey = by - math.cos(lean) * length
        pts = bezier((bx + rng.normal(0, w * 0.03), by), (bx + (ex - bx) * 0.3, by - length * 0.6), (ex, ey), 12)
        g = GRASS_GREENS[int(rng.integers(len(GRASS_GREENS)))] * 1.2
        cv.stem(pts, w * 0.012, 0.6, g, dark=0.3)
    for b in range(7):
        lean = rng.normal(0, 0.35)
        length = h * rng.uniform(0.6, 0.9)
        ex = bx + math.sin(lean) * length
        ey = by - math.cos(lean) * length
        pts = bezier((bx, by), (bx + (ex - bx) * 0.2, by - length * 0.5), (ex, ey), 14)
        cv.stem(pts, w * 0.006, w * 0.003, C(0.42, 0.40, 0.24), dark=0.3)
        for s in range(9):
            k = int(len(pts) * (0.55 + 0.45 * s / 8)) - 1
            px, py = pts[k]
            ang = rng.uniform(-1.2, 1.2)
            ln = w * rng.uniform(0.03, 0.06)
            cv.stem([(px, py), (px + math.sin(ang) * ln, py - math.cos(ang) * ln)], w * 0.002, w * 0.001,
                    C(0.45, 0.42, 0.25))
            cv.leaf("blade", px + math.sin(ang) * ln, py - math.cos(ang) * ln, ang, w * 0.035,
                    C(0.55, 0.5, 0.3), C(0.4, 0.35, 0.2), rng, edge=0.2, petiole=0.0)
    # herb sprig: branching stems, small lobed leaves and a few muted yellow flower heads
    cv.set_clip(W["herb"]["rect"])
    x, y, w, h = cell_px(W["herb"]["rect"])
    bx, by = x + w * 0.5, y + h * 0.995
    tips = []
    for b in range(5):
        lean = (b - 2) * 0.3 + rng.normal(0, 0.1)
        length = h * rng.uniform(0.55, 0.8)
        ex = bx + math.sin(lean) * length * 0.7
        ey = by - math.cos(lean) * length
        pts = bezier((bx, by), (bx + (ex - bx) * 0.2, by - length * 0.5), (ex, ey), 14)
        cv.stem(pts, w * 0.012, w * 0.006, C(0.30, 0.30, 0.15), dark=0.3)
        tips.append((ex, ey))
        for s in range(5):
            k = int(len(pts) * (0.15 + 0.17 * s))
            px, py = pts[k]
            side = (-1) ** (s + b)
            ang = side * rng.uniform(0.7, 1.3) + lean
            base, alt = pick(WEED_GREENS, rng)
            cv.leaf("plane", px, py, ang, w * rng.uniform(0.08, 0.12) * (1.2 - s * 0.12), base, alt, rng,
                    edge=0.2, vein_light=0.1, petiole=0.3, pet_col=C(0.3, 0.3, 0.15))
    for (ex, ey) in tips[:4]:
        ys, xs = np.mgrid[int(ey - 30):int(ey + 30), int(ex - 30):int(ex + 30)].astype(np.float64) + 0.5
        d = np.sqrt((xs - ex) ** 2 + ((ys - ey) * 1.3) ** 2)
        m = np.clip(w * 0.022 - d + 0.5, 0, 1)
        col = mix(C(0.78, 0.64, 0.22), C(0.55, 0.42, 0.15), smoothstep(0, w * 0.022, d))
        cv.composite((slice(int(ey - 30), int(ey + 30)), slice(int(ex - 30), int(ex + 30))), m,
                     col, cv.layer + 0.3)
    rgb, a, h = cv.finish()
    save_webp(np.concatenate([rgb, a[..., None]], -1), "weeds-color.webp", quality=92)
    nrm = height_to_normal(h * 6.0, 1.4, wrap=False)
    nrm = nrm * a[..., None] + np.array([0.5, 0.5, 1.0]) * (1 - a[..., None])
    save_webp(nrm, "weeds-normal.webp", quality=92)


# --------------------------------------------------------------------------------------
# Bark (tileable 1024 x 1024, U around the trunk, V up the trunk, 1 tile = 1 m)
# --------------------------------------------------------------------------------------

def make_plane_bark():
    rng = np.random.default_rng(4808)
    n = SIZE
    warp = (fft_noise((n, n), rng, beta=2.3, fmin=1) * 0.06, fft_noise((n, n), rng, beta=2.3, fmin=1) * 0.06)
    f1, f2, ids = worley(n, 7, rng, warp=warp, aniso=(1.0, 0.8))
    warp2 = (warp[0] * 0.6 + fft_noise((n, n), rng, beta=2.0, fmin=4) * 0.012,
             warp[1] * 0.6 + fft_noise((n, n), rng, beta=2.0, fmin=4) * 0.012)
    g1, g2, gids = worley(n, 17, rng, warp=warp2, aniso=(1.0, 0.85))
    age_big = rng.choice([0, 1, 2, 3], size=49, p=[0.22, 0.3, 0.3, 0.18])
    age_small = rng.choice([0, 1, 2, 3], size=17 * 17, p=[0.25, 0.3, 0.3, 0.15])
    # combine: within a big plate, small flakes may have peeled to a younger layer
    big = age_big[ids].astype(np.float64)
    small = age_small[gids].astype(np.float64)
    peel = (rng.random(17 * 17) < 0.45)[gids]
    age = np.where(peel, np.minimum(big, small), big)
    pal = [C(0.70, 0.66, 0.52), C(0.55, 0.53, 0.41), C(0.47, 0.46, 0.40), C(0.40, 0.37, 0.32)]
    col = np.zeros((n, n, 3))
    for k in range(4):
        col += (age == k)[..., None] * pal[k]
    mott = fft_noise((n, n), rng, beta=1.6, fmin=10)
    grain = fft_noise((n, n), rng, beta=1.0, fmin=60)
    col = col * (1 + 0.07 * mott[..., None] + 0.04 * grain[..., None])
    # flake edges: thin dark rims and a lighter lip on the older side
    e_big = 1 - smoothstep(0.0, 0.05, f2 - f1)
    e_small = (1 - smoothstep(0.0, 0.06, g2 - g1)) * peel
    edge = np.maximum(e_big, e_small * 0.7)
    col = col * (1 - 0.12 * edge[..., None])
    # soften plate boundaries so the colour change reads as flaking, not drawn outlines
    col = np.stack([box_blur(col[..., k], 2) for k in range(3)], -1)
    col = col * (1 + 0.06 * grain[..., None])
    # vertical grime streaks from rain run-off
    streak = fft_noise((n, n), rng, beta=1.8, fmin=2, aniso=(1.0, 0.12))
    col = col * (1 - 0.12 * smoothstep(0.2, 2.0, streak)[..., None])
    col = mix(col, C(0.33, 0.35, 0.28), 0.12 * smoothstep(0.5, 2.0, mott))  # algae tint
    hgt = box_blur(age * 0.25, 2) + 0.05 * mott + 0.03 * grain - 0.08 * edge
    save_webp(np.clip(col, 0, 1), "plane-bark-color.webp", quality=90)
    save_webp(height_to_normal(hgt * 30, 1.0, wrap=True), "plane-bark-normal.webp", quality=92)
    cav = box_blur(hgt, 6) - hgt
    ao = np.clip(1 - cav * 2.2, 0.45, 1)
    rough = np.clip(0.78 + 0.05 * age - 0.04 * (age == 0) + 0.03 * grain, 0, 1)
    save_webp(np.stack([ao, rough, np.zeros_like(ao)], -1), "plane-bark-orm.webp", quality=92)


def make_birch_bark():
    rng = np.random.default_rng(4909)
    n = SIZE
    mott = fft_noise((n, n), rng, beta=1.8, fmin=4)
    grain = fft_noise((n, n), rng, beta=1.0, fmin=80)
    band = fft_noise((n, n), rng, beta=2.0, fmin=3, aniso=(0.08, 1.0))  # horizontal banding
    col = np.ones((n, n, 3)) * C(0.84, 0.82, 0.77)
    col = mix(col, C(0.72, 0.71, 0.68), smoothstep(-0.5, 1.8, mott))
    col = mix(col, C(0.82, 0.72, 0.62), 0.5 * smoothstep(1.0, 2.2, band))  # peeled pinkish patches
    col = col * (1 + 0.035 * grain[..., None])
    hgt = 0.05 * mott + 0.02 * grain + 0.08 * smoothstep(1.0, 2.2, band)
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float64)
    # lenticels: dark horizontal dashes, wrapped so the tile is seamless
    dark = np.zeros((n, n))
    for _ in range(300):
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        hl = rng.uniform(8, 42) * (1.6 if rng.random() < 0.15 else 1.0)
        ht = rng.uniform(1.2, 3.5)
        x0, x1 = int(cx - hl - 3), int(cx + hl + 4)
        y0, y1 = int(cy - ht - 3), int(cy + ht + 4)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        dx = np.maximum(np.abs(xx - cx) - hl, 0)
        dy = np.abs(yy - cy) * (1 + 0.3 * np.abs(xx - cx) / hl)
        d = np.sqrt(dx * dx + dy * dy)
        m = np.clip(ht - d + 0.5, 0, 1) * rng.uniform(0.45, 1.0)
        dark[np.mod(yy.astype(int), n), np.mod(xx.astype(int), n)] = np.maximum(
            dark[np.mod(yy.astype(int), n), np.mod(xx.astype(int), n)], m)
    # black fissured patches and branch-scar chevrons
    patches = fft_noise((n, n), rng, beta=2.2, fmin=2)
    crack = fft_noise((n, n), rng, beta=1.3, fmin=20, aniso=(0.25, 1.0))
    ragged = fft_noise((n, n), rng, beta=1.2, fmin=30)
    pmask = smoothstep(1.55, 1.75, patches + 0.25 * ragged)
    fiss = pmask * smoothstep(0.2, 1.2, crack)
    for _ in range(0):
        cx, cy = rng.uniform(0, n), rng.uniform(0, n)
        wdt = rng.uniform(40, 90)
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float64)
        dx = np.mod(xx - cx + n / 2, n) - n / 2
        dy = np.mod(yy - cy + n / 2, n) - n / 2
        chev = np.clip(1 - np.abs(dy + np.abs(dx) * 0.55) / 7.0, 0, 1) * (np.abs(dx) < wdt) * (dy < 0)
        pmask = np.maximum(pmask, chev)
    col = mix(col, C(0.30, 0.26, 0.23), dark * 0.85)
    col = mix(col, C(0.20, 0.19, 0.17) * (1 + 0.25 * ragged[..., None]), pmask * 0.85)
    col = mix(col, C(0.08, 0.075, 0.07), fiss * 0.5)
    hgt = hgt - 0.25 * dark - 0.2 * pmask - 0.3 * fiss
    save_webp(np.clip(col, 0, 1), "birch-bark-color.webp", quality=90)
    save_webp(height_to_normal(hgt * 25, 1.0, wrap=True), "birch-bark-normal.webp", quality=92)
    cav = box_blur(hgt, 5) - hgt
    ao = np.clip(1 - cav * 2.5, 0.45, 1)
    rough = np.clip(0.62 + 0.25 * pmask + 0.1 * dark + 0.03 * grain, 0, 1)
    save_webp(np.stack([ao, rough, np.zeros_like(ao)], -1), "birch-bark-orm.webp", quality=92)


def main():
    os.makedirs(OUT, exist_ok=True)
    which = sys.argv[1:] or ["plane", "birch", "shrub", "hedge", "litter", "grass", "weed", "planebark", "birchbark"]
    jobs = {"plane": make_plane_atlas, "birch": make_birch_atlas, "shrub": make_shrub_atlas,
            "hedge": make_hedge_atlas, "litter": make_litter_atlas, "grass": make_grass_atlas,
            "weed": make_weed_atlas, "planebark": make_plane_bark, "birchbark": make_birch_bark}
    for w in which:
        jobs[w]()


if __name__ == "__main__":
    main()
