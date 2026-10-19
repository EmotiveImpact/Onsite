"""Shop, launderette, workshop, youth club and estate office fixtures."""

import math

import bmesh
from mathutils import Vector

from heron_props_lib import (
    Asset, R, S, T, box, box_mm, bolt_head, cyl, cyl_between, deform, dome_head, fillet_path, lathe,
    loft, prism, quad, rect_profile, rrect, soft_box, sphere, sweep, text_mesh, torus, tube, fbm,
)
from heron_props_street import box_collider, cyl_collider
import heron_props_atlas as A

BLK = "hr_steel_black"
GALV = "hr_steel_galv"
PBLK = "hr_plastic_black"
PROD = "hr_prop_products"
SHOP = "hr_prop_shop"
SHOP_LIT = "hr_prop_shop_lit"
PAINT = "hr_prop_shelf_paint"
STEEL = "hr_prop_stainless"
GLASS = "hr_glass"
CLEAR = "hr_prop_glass_clear"
VOID = "hr_prop_dark_void"
TIMBER = "hr_timber"
LAM = "hr_prop_laminate"
GREY = "hr_prop_formica_grey"
FONT_SIGN = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_SMALL = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def remap(rect, u, v):
    u0, v0, u1, v1 = rect
    return (u0 + (u1 - u0) * u, v0 + (v1 - v0) * v)


# ---------------------------------------------------------------------------
# product primitives with atlas UVs
# ---------------------------------------------------------------------------


def product_box(w, d, h, rect):
    """Box standing on z=0, front (-Y) carries the design, sides and top take edge strips."""
    bm = box(w, d, h, 0.0, 1, (0, 0, h / 2))
    uvl = bm.loops.layers.uv.active
    bm.normal_update()
    su = 0.08
    for f in bm.faces:
        n = f.normal
        for l in f.loops:
            x, y, z = l.vert.co
            fu, fz, fy = (x + w / 2) / w, z / h, (y + d / 2) / d
            if abs(n.y) > 0.5:
                uv = remap(rect, fu if n.y < 0 else 1 - fu, fz)
            elif abs(n.x) > 0.5:
                uv = remap(rect, su * fy, fz)
            else:
                uv = remap(rect, fu, 1 - su + su * fy)
            l[uvl].uv = uv
    return bm


def wrap_z(bm, rect, h):
    """Replace a lathe's v with z/h and remap 0..1 into rect."""
    uvl = bm.loops.layers.uv.active
    for f in bm.faces:
        for l in f.loops:
            u = l[uvl].uv.x
            if abs(l.vert.co.x) < 1e-6 and abs(l.vert.co.y) < 1e-6:
                u = 0.5
            l[uvl].uv = remap(rect, u, max(0.0, min(1.0, l.vert.co.z / h)))
    return bm


def can(r=0.033, h=0.115, rect=None, n=10):
    bm = lathe([(0.0, 0.0), (r * 0.8, 0.0), (r, 0.008), (r, h - 0.010), (r * 0.82, h - 0.002), (0.0, h)], n, False, False, uv="unit")
    return wrap_z(bm, rect, h)


def bottle(r=0.035, h=0.30, rect=None, n=8):
    rn, rc = r * 0.36, r * 0.42
    prof = [(0.0, 0.0), (r * 0.85, 0.0), (r, 0.012 * h / 0.3), (r, 0.58 * h), (r * 0.92, 0.66 * h), (rn * 1.2, 0.80 * h),
            (rn, 0.88 * h), (rc, 0.90 * h), (rc, 0.99 * h), (0.0, h)]
    bm = lathe(prof, n, False, False, uv="unit")
    return wrap_z(bm, rect, h)


def can_lo(r=0.033, h=0.115, rect=None, n=8):
    bm = lathe([(0.0, 0.0), (r, 0.0), (r, h), (0.0, h)], n, False, False, uv="unit")
    return wrap_z(bm, rect, h)


def bottle_lo(r=0.032, h=0.23, rect=None, n=8):
    rn, rc = r * 0.36, r * 0.42
    prof = [(0.0, 0.0), (r, 0.02 * h), (r, 0.60 * h), (rn * 1.1, 0.82 * h), (rc, 0.90 * h), (rc, h), (0.0, h)]
    bm = lathe(prof, n, False, False, uv="unit")
    return wrap_z(bm, rect, h)


def tin(r=0.038, h=0.11, rect=None, n=10):
    bm = lathe([(0.0, 0.0), (r * 0.94, 0.0), (r, 0.006), (r, h - 0.006), (r * 0.94, h), (0.0, h)], n, False, False, uv="unit")
    return wrap_z(bm, rect, h)


def jug(rect, h=0.28):
    bm = lathe([(0.0, 0.0), (0.060, 0.0), (0.068, 0.01), (0.068, 0.20), (0.055, 0.24), (0.025, 0.255), (0.022, 0.27), (0.0, h)], 8, False, False, uv="unit", phase=math.pi / 8)
    bmesh.ops.scale(bm, vec=(1.0, 0.72, 1.0), verts=bm.verts)
    return wrap_z(bm, rect, h)


# ---------------------------------------------------------------------------


def shelf_unit():
    a = Asset("SHOP_SHELF_UNIT", "shop", 51)
    rng = a.rng
    W = 1.20
    # structure
    for x in (-0.585, 0.585):
        a.add(box(0.03, 0.04, 2.0, 0.003, 1, (x, 0.225, 1.0)), PAINT)
    a.add(box(1.14, 0.012, 1.80, 0.002, 1, (0, 0.238, 1.05)), PAINT)
    a.add(box(1.20, 0.012, 0.13, 0.002, 1, (0, -0.244, 0.065)), PAINT)
    a.add(box(1.20, 0.49, 0.025, 0.003, 1, (0, 0.0, 0.1425)), PAINT)
    a.add(box(1.20, 0.07, 0.07, 0.004, 1, (0, 0.21, 2.035)), PAINT)
    shelves = [0.52, 0.88, 1.24, 1.58]
    for z in shelves:
        a.add(box(1.17, 0.40, 0.022, 0.003, 1, (0, 0.03, z - 0.011)), PAINT)
        a.add(box(1.17, 0.008, 0.038, 0.001, 1, (0, -0.174, z - 0.006)), PAINT)
        a.add(quad((-0.58, -0.1785, z - 0.022), (0.58, -0.1785, z - 0.022), (0.58, -0.1785, z + 0.010), (-0.58, -0.1785, z + 0.010)),
              SHOP, uv="rect", uv_rect=A.SHOP["price_strip"])
        for x in (-0.57, 0.57):
            a.add(prism([(0.0, 0.0), (0.36, 0.04), (0.0, 0.04)], 0.012, 0.0, 1), PAINT, T(x, 0.23, z - 0.062) @ R("Z", -90))
    # products
    xmin, xmax = -0.565, 0.565
    zones = [
        (0.155, "deck"), (shelves[0], "tins"), (shelves[1], "bottles"), (shelves[2], "tall"), (shelves[3], "top"),
    ]
    for z, kind in zones:
        x = xmin
        while x < xmax - 0.05:
            block = rng.randint(2, 4)
            if kind == "deck":
                if rng.random() < 0.55:
                    w, d, h = 0.27, 0.15, 0.36
                    idx = rng.randrange(4)
                    sk = soft_box(w, d, h, 0.03, 3, (0, 0, h / 2))
                    deform(sk, lambda p, s=rng.random(): Vector((p.x * (1 + 0.06 * math.cos(p.z * 9 + s * 6)), p.y * (1.0 + 0.4 * math.sin(math.pi * min(1, max(0, p.z / h)))), p.z * (0.96 + 0.04 * s))))
                    if x + w > xmax:
                        break
                    a.add(sk, PROD, T(x + w / 2, -0.12 + rng.uniform(0, 0.03), z) @ R("Z", rng.uniform(-4, 4)), uv="fit", fit_axis="Y", uv_rect=A.product_rect("sack", idx))
                    x += w + 0.01
                else:
                    idx = rng.randrange(2)
                    for k in range(block):
                        if x + 0.15 > xmax:
                            break
                        a.add(jug(A.product_cell("jug", idx)), PROD, T(x + 0.07, -0.15 + rng.uniform(0, 0.02), z) @ R("Z", rng.uniform(-8, 8)), uv="keep")
                        x += 0.145
            elif kind == "tins":
                idx = rng.randrange(8)
                r, h = 0.038, 0.11
                for k in range(block):
                    if x + 2 * r > xmax:
                        break
                    if rng.random() < 0.12:
                        x += 2 * r + 0.006
                        continue
                    cx = x + r
                    yb = -0.13 + rng.uniform(0, 0.01) + (0.08 if rng.random() < 0.15 else 0.0)
                    for lev in range(2 if rng.random() < 0.85 else 1):
                        a.add(tin(r, h, A.product_cell("tin", idx)), PROD, T(cx + rng.uniform(-0.002, 0.002), yb, z + lev * h) @ R("Z", rng.uniform(0, 360)), uv="keep")
                    x += 2 * r + 0.006
            elif kind == "bottles":
                idx = rng.randrange(8)
                r, h = 0.042, 0.31
                for k in range(block):
                    if x + 2 * r > xmax:
                        break
                    if rng.random() < 0.15:
                        x += 2 * r + 0.008
                        continue
                    a.add(bottle(r, h, A.product_cell("bottle", idx)), PROD, T(x + r, -0.125 + rng.uniform(0, 0.03), z) @ R("Z", rng.uniform(0, 360)), uv="keep")
                    x += 2 * r + 0.008
            elif kind == "tall":
                idx = rng.randrange(16)
                w = rng.choice((0.19, 0.20, 0.16))
                h = w / 0.70
                for k in range(min(block, 3)):
                    if x + w > xmax:
                        break
                    pull = 0.0 if rng.random() > 0.2 else rng.uniform(0.04, 0.12)
                    a.add(product_box(w, 0.28 - pull, h, A.product_rect("tall", idx)), PROD,
                          T(x + w / 2, -0.155 + pull + (0.28 - pull) / 2 - 0.005, z) @ R("Z", rng.uniform(-2.5, 2.5)), uv="keep")
                    x += w + 0.006
            else:  # top shelf: wide boxes and bags
                if rng.random() < 0.5:
                    idx = rng.randrange(8)
                    w, h = 0.22, 0.22 / 1.6
                    for k in range(block):
                        if x + w > xmax:
                            break
                        for lev in range(2 if rng.random() < 0.6 else 1):
                            a.add(product_box(w, 0.06, h, A.product_rect("wide", idx)), PROD,
                                  T(x + w / 2, -0.12, z + lev * h) @ R("Z", rng.uniform(-2, 2)), uv="keep")
                        x += w + 0.008
                else:
                    idx = rng.randrange(8)
                    w, h = 0.16, 0.20
                    for k in range(block):
                        if x + w > xmax:
                            break
                        bag = soft_box(w, 0.055, h, 0.022, 2, (0, 0, h / 2))
                        deform(bag, lambda p, s=rng.random(): Vector((p.x * (1 - 0.15 * (abs(p.z - h / 2) / (h / 2)) ** 3), p.y * (1 - 0.8 * (abs(p.z - h / 2) / (h / 2)) ** 4), p.z)))
                        a.add(bag, PROD, T(x + w / 2, -0.13 + rng.uniform(0, 0.03), z) @ R("X", rng.uniform(-8, 2)) @ R("Z", rng.uniform(-6, 6)),
                              uv="fit", fit_axis="Y", uv_rect=A.product_rect("bag", idx))
                        x += w + 0.008
            x += rng.uniform(0.005, 0.02)
    a.meta.update(needsCollision=True, collider=box_collider((1.20, 0.50, 2.07), (0, 0, 1.035)),
                  notes="1.2 m perimeter shelving bay (gondola wall bay), 0.5 m deep, five levels of procedurally placed packs, tins, bottles and sacks. Back faces +Y: stand it against the wall.")
    return a


def fridge():
    a = Asset("SHOP_FRIDGE", "shop", 52)
    rng = a.rng
    W, D, H = 1.30, 0.72, 2.05
    y0, y1 = -D / 2, D / 2
    t = 0.04
    # carcass: sides, top, bottom, back (outside)
    a.add(box_mm(-W / 2, -W / 2 + t, y0, y1, 0.0, H - 0.20, 0.006), BLK)
    a.add(box_mm(W / 2 - t, W / 2, y0, y1, 0.0, H - 0.20, 0.006), BLK)
    a.add(box_mm(-W / 2, W / 2, y1 - t, y1, 0.0, H - 0.20, 0.006), BLK)
    a.add(box_mm(-W / 2, W / 2, y0, y1, 0.0, 0.16, 0.006), BLK)
    # canopy with lit header
    a.add(box_mm(-W / 2, W / 2, y0 - 0.04, y1, H - 0.20, H, 0.008), BLK)
    a.add(quad((-0.60, y0 - 0.0405, H - 0.18), (0.60, y0 - 0.0405, H - 0.18), (0.60, y0 - 0.0405, H - 0.02), (-0.60, y0 - 0.0405, H - 0.02)),
          SHOP_LIT, uv="rect", uv_rect=A.SHOP["cold_drinks"])
    # interior liner (faces inward) and mullion
    zi0, zi1 = 0.16, H - 0.20
    xi0, xi1 = -W / 2 + t, W / 2 - t
    yi0, yi1 = y0 + 0.06, y1 - t
    a.add(quad((xi0, yi1, zi0), (xi0, yi1, zi1), (xi1, yi1, zi1), (xi1, yi1, zi0), uvs=((0, 0), (0, 1), (1, 1), (1, 0))), "hr_prop_fridge_liner", uv="rect", uv_rect=A.SHOP["fridge_back"])
    for (x, s) in ((xi0, 1), (xi1, -1)):
        pts = [(x, yi0, zi0), (x, yi1, zi0), (x, yi1, zi1), (x, yi0, zi1)]
        if s < 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        a.add(quad(*pts), "hr_prop_fridge_liner", uv="rect", uv_rect=A.SHOP["fridge_back"])
    a.add(quad((xi0, yi0, zi1), (xi0, yi1, zi1), (xi1, yi1, zi1), (xi1, yi0, zi1)), "hr_prop_fridge_liner", uv="rect", uv_rect=A.SHOP["fridge_back"], flip=True)
    a.add(box_mm(-0.02, 0.02, y0, y0 + 0.08, zi0, zi1, 0.003), BLK)
    # LED strips
    for x in (xi0 + 0.012, xi1 - 0.012, -0.024, 0.024):
        a.add(box_mm(x - 0.006, x + 0.006, yi0 + 0.01, yi0 + 0.03, zi0 + 0.05, zi1 - 0.05), "hr_prop_fridge_light")
    a.add(box_mm(xi0, xi1, yi0 + 0.05, yi0 + 0.09, zi1 - 0.03, zi1 - 0.01), "hr_prop_fridge_light")
    # bottom kick grille
    a.add(box_mm(-W / 2 + 0.05, W / 2 - 0.05, y0 - 0.002, y0 + 0.01, 0.02, 0.13), VOID)
    for k in range(9):
        z = 0.03 + k * 0.011
        a.add(box_mm(-W / 2 + 0.05, W / 2 - 0.05, y0 - 0.006, y0 - 0.001, z, z + 0.005), BLK)
    # shelves and stock
    levels = [0.18, 0.52, 0.86, 1.18, 1.50]
    for li, z in enumerate(levels):
        if li > 0:
            for (bx0, bx1) in ((xi0, -0.02), (0.02, xi1)):
                a.add(box_mm(bx0, bx1, yi0 + 0.03, yi1 - 0.02, z - 0.012, z), GALV)
                a.add(quad((bx0 + 0.01, yi0 + 0.0285, z - 0.012), (bx1 - 0.01, yi0 + 0.0285, z - 0.012), (bx1 - 0.01, yi0 + 0.0285, z + 0.012), (bx0 + 0.01, yi0 + 0.0285, z + 0.012)),
                      SHOP, uv="rect", uv_rect=A.SHOP["price_strip"])
        for (bx0, bx1) in ((xi0 + 0.02, -0.03), (0.03, xi1 - 0.02)):
            kind = "bottle" if li in (0, 2) else "can"
            x = bx0
            idx = rng.randrange(8)
            run = 0
            while True:
                if kind == "can":
                    r, h = 0.033, 0.115
                    if x + 2 * r > bx1:
                        break
                    for row in range(2):
                        if rng.random() < 0.1:
                            continue
                        a.add(can_lo(r, h, A.product_rect("can", idx), 8), PROD, T(x + r, yi0 + 0.08 + row * 0.08, z) @ R("Z", rng.uniform(-30, 30)), uv="keep")
                    x += 2 * r + 0.004
                else:
                    r, h = 0.032, 0.23
                    if x + 2 * r > bx1:
                        break
                    if rng.random() > 0.08:
                        a.add(bottle_lo(r, h, A.product_cell("bottle", idx), 8), PROD, T(x + r, yi0 + 0.08 + rng.uniform(0, 0.02), z) @ R("Z", rng.uniform(0, 360)), uv="keep")
                    x += 2 * r + 0.006
                run += 1
                if run % rng.randint(3, 5) == 0:
                    idx = rng.randrange(8)
    # doors: frames, glass, handles (closed)
    for (dx0, dx1) in ((-W / 2 + 0.01, -0.005), (0.005, W / 2 - 0.01)):
        fy0, fy1 = y0 - 0.035, y0
        for (a0, a1, b0, b1) in ((dx0, dx1, 0.165, 0.215), (dx0, dx1, H - 0.255, H - 0.205), (dx0, dx0 + 0.04, 0.165, H - 0.205), (dx1 - 0.04, dx1, 0.165, H - 0.205)):
            a.add(box_mm(a0, a1, fy0, fy1, b0, b1, 0.004), BLK)
        a.add(quad((dx0 + 0.04, fy0 + 0.017, 0.215), (dx1 - 0.04, fy0 + 0.017, 0.215), (dx1 - 0.04, fy0 + 0.017, H - 0.255), (dx0 + 0.04, fy0 + 0.017, H - 0.255)), CLEAR, uv="keep")
        hx = dx1 - 0.06 if dx0 < 0 else dx0 + 0.06
        a.add(cyl_between((hx, fy0 - 0.045, 0.75), (hx, fy0 - 0.045, 1.45), 0.012, 10), STEEL)
        for z in (0.78, 1.42):
            a.add(cyl_between((hx, fy0, z), (hx, fy0 - 0.045, z), 0.009, 8), STEEL)
    a.meta.update(needsCollision=True, collider=box_collider((1.30, 0.80, 2.05), (0, -0.04, 1.025)), lightAnchor=[0.0, -0.10, 1.2],
                  notes="Two-door glass drinks fridge with lit interior strips and a lit COLD DRINKS header. Glass is alpha blended (hr_prop_glass_clear).")
    return a


def counter():
    a = Asset("SHOP_COUNTER", "shop", 53)
    rng = a.rng
    L, D, H = 1.80, 0.60, 0.98
    a.add(box_mm(-L / 2, L / 2, -D / 2 + 0.02, D / 2 - 0.30, 0.0, H - 0.04, 0.006), GREY)
    a.add(box_mm(-L / 2 + 0.02, L / 2 - 0.02, -D / 2 + 0.02, -D / 2 + 0.04, 0.0, 0.10, 0.003), PBLK)
    # printed fascia on the upper front
    a.add(quad((-L / 2 + 0.01, -D / 2 + 0.019, 0.46), (L / 2 - 0.01, -D / 2 + 0.019, 0.46), (L / 2 - 0.01, -D / 2 + 0.019, H - 0.06), (-L / 2 + 0.01, -D / 2 + 0.019, H - 0.06)),
          SHOP, uv="rect", uv_rect=A.SHOP["counter_front"])
    # staff side: open shelves under the top
    for x in (-L / 2 + 0.01, L / 2 - 0.01):
        a.add(box_mm(x - 0.01, x + 0.01, -0.0, D / 2 - 0.02, 0.0, H - 0.04, 0.002), GREY)
    a.add(box_mm(-L / 2, L / 2, 0.0, D / 2 - 0.02, 0.0, 0.03, 0.002), GREY)
    a.add(box_mm(-L / 2 + 0.02, L / 2 - 0.02, 0.0, D / 2 - 0.04, 0.45, 0.47, 0.002), GREY)
    for k in range(5):
        x = -0.75 + k * 0.30 + rng.uniform(-0.04, 0.04)
        idx = rng.randrange(8)
        a.add(product_box(0.26, 0.20, 0.16, A.product_rect("wide", idx)), PROD, T(x, 0.14, 0.03 if k % 2 else 0.47) @ R("Z", 180 + rng.uniform(-5, 5)), uv="keep")
    # worktop
    a.add(box(L + 0.06, D + 0.04, 0.04, 0.008, 2, (0, 0, H - 0.02)), LAM)
    # till: base, cash drawer, screen on a stand, card reader
    tx = 0.30
    a.add(box(0.36, 0.40, 0.10, 0.006, 1, (tx, 0.05, H + 0.05)), PBLK)
    a.add(quad((tx - 0.17, 0.25 + 0.001, H + 0.01), (tx + 0.17, 0.25 + 0.001, H + 0.01), (tx + 0.17, 0.25 + 0.001, H + 0.09), (tx - 0.17, 0.25 + 0.001, H + 0.09), uvs=((1, 0), (0, 0), (0, 1), (1, 1))),
          SHOP, uv="rect", uv_rect=A.SHOP["cash_drawer"])
    a.add(cyl(0.025, 0.18, 10, 0.0), PBLK, T(tx, 0.08, H + 0.10))
    scr = T(tx, 0.08, H + 0.30) @ R("X", -15)
    a.add(box(0.32, 0.03, 0.22, 0.006, 1), PBLK, scr)
    a.add(quad((0.15, 0.0155, -0.10), (-0.15, 0.0155, -0.10), (-0.15, 0.0155, 0.10), (0.15, 0.0155, 0.10)), SHOP_LIT, scr, uv="rect", uv_rect=A.SHOP["till_screen"])
    # customer display facing the front
    a.add(box(0.14, 0.02, 0.06, 0.004, 1, (tx, -0.08, H + 0.36)), PBLK)
    a.add(quad((tx - 0.065, -0.0905, H + 0.335), (tx + 0.065, -0.0905, H + 0.335), (tx + 0.065, -0.0905, H + 0.385), (tx - 0.065, -0.0905, H + 0.385)), SHOP_LIT, uv="rect", uv_rect=A.SHOP["till_screen"])
    cr = T(-0.05, -0.12, H + 0.04) @ R("X", -25)
    a.add(box(0.08, 0.16, 0.035, 0.008, 1), PBLK, cr)
    a.add(quad((-0.035, -0.07, 0.0181), (0.035, -0.07, 0.0181), (0.035, 0.07, 0.0181), (-0.035, 0.07, 0.0181)), SHOP, cr, uv="rect", uv_rect=A.SHOP["card_reader"])
    # scratchcard dispenser: two clear tiers at the left end facing the customer
    sx = -0.62
    for k, z in enumerate((H + 0.02, H + 0.22)):
        a.add(box(0.36, 0.14, 0.19, 0.004, 1, (sx, -0.16, z + 0.095)), CLEAR)
        a.add(quad((sx - 0.17, -0.2305, z + 0.01), (sx + 0.17, -0.2305, z + 0.01), (sx + 0.17, -0.2305, z + 0.18), (sx - 0.17, -0.2305, z + 0.18)),
              PROD, uv="rect", uv_rect=A.product_rect("scratch", k))
    a.add(box(0.38, 0.16, 0.012, 0.002, 1, (sx, -0.16, H + 0.42)), PBLK)
    # sweets tray and a stack of free papers
    for k in range(4):
        idx = rng.randrange(8)
        a.add(product_box(0.08, 0.14, 0.05, A.product_rect("wide", idx)), PROD, T(-0.28 + k * 0.09, -0.20, H) @ R("Z", rng.uniform(-3, 3)), uv="keep")
    a.add(box(0.28, 0.38, 0.03, 0.004, 1, (0.72, -0.08, H + 0.015)), "hr_prop_plastic_white")
    a.meta.update(needsCollision=True, collider=box_collider((1.86, 0.64, 1.0), (0, 0, 0.5)),
                  notes="Shop counter: customer side faces -Y with a printed fascia, till and card reader on top, two-tier scratchcard stand at the left end, open shelves on the staff side.")
    return a


def shop_sign():
    a = Asset("SHOP_SIGN_CORNER", "shop", 54)
    W, H, D = 6.0, 0.80, 0.10
    a.add(box_mm(-W / 2, W / 2, -D, 0.0, 0.0, H, 0.008), "hr_prop_fascia")
    for z0, z1 in ((-0.02, 0.025), (H - 0.025, H + 0.02)):
        a.add(box_mm(-W / 2 - 0.02, W / 2 + 0.02, -D - 0.025, 0.0, z0, z1, 0.004), BLK)
    for sx in (-1, 1):
        a.add(box_mm(sx * W / 2 - 0.02, sx * W / 2 + 0.02, -D - 0.025, 0.0, -0.02, H + 0.02, 0.004), BLK)
    big = text_mesh("THE CORNER", FONT_SIGN, 0.50, extrude=0.012, align="CENTER", condense=0.86, spacing=1.08)
    bmesh.ops.translate(big, vec=(0, -D - 0.013, 0.33), verts=big.verts)
    a.add(big, "hr_prop_sign_letters", uv="box", sharp=30)
    small = text_mesh("FOOD & WINE", FONT_SMALL, 0.15, extrude=0.008, align="CENTER", condense=0.9, spacing=1.25)
    bmesh.ops.translate(small, vec=(0, -D - 0.009, 0.10), verts=small.verts)
    a.add(small, "hr_prop_sign_letters", uv="box", sharp=30)
    # fixing screws along the trims
    for k in range(9):
        x = -W / 2 + 0.2 + k * (W - 0.4) / 8
        for z in (0.0, H):
            a.add(dome_head(0.006, 0.003), GALV, T(x, -D - 0.026, z) @ R("X", 90))
    a.meta.update(needsCollision=False, collider=None, mount="wall", lightAnchor=[0.0, -0.4, 0.4],
                  notes="6.0 x 0.8 m dark green painted fascia with emissive 3D letters reading THE CORNER and FOOD & WINE. Origin on the wall face at the bottom centre of the fascia.")
    return a


def _porthole(a, m, r_out=0.24, r_glass=0.17):
    prof = [(r_out, 0.0), (r_out + 0.006, 0.02), (r_out - 0.005, 0.055), (r_out - 0.03, 0.068),
            (r_glass + 0.012, 0.064), (r_glass, 0.05)]
    a.add(lathe(prof, 28, False, False), STEEL, m @ R("X", 90))
    a.add(cyl(r_glass + 0.002, 0.004, 28, 0.034), GLASS, m @ R("X", 90))
    a.add(lathe([(r_glass, 0.034), (r_glass * 0.96, -0.12)], 24, False, False), STEEL, m @ R("X", 90), flip=True)
    a.add(cyl(r_glass * 0.96, 0.004, 24, -0.124), VOID, m @ R("X", 90))


def washing_machine():
    a = Asset("WASHING_MACHINE", "shop", 55)
    W, D, H = 0.70, 0.78, 1.10
    a.add(box(W, D, H - 0.06, 0.012, 2, (0, 0, 0.06 + (H - 0.06) / 2)), STEEL)
    a.add(box(W - 0.04, D - 0.06, 0.06, 0.004, 1, (0, 0.02, 0.03)), PBLK)
    yf = -D / 2
    # control panel, slightly proud, inclined
    pm = T(0, yf - 0.006, 0.97) @ R("X", 8)
    a.add(box(W - 0.04, 0.03, 0.24, 0.006, 1), STEEL, pm)
    a.add(quad((-0.31, -0.0155, -0.11), (0.31, -0.0155, -0.11), (0.31, -0.0155, 0.11), (-0.31, -0.0155, 0.11)), "hr_prop_laundry", pm, uv="rect", uv_rect=A.LAUNDRY["washer_panel"])
    # porthole door with hinge and handle
    dm = T(0, yf, 0.52)
    _porthole(a, dm)
    a.add(box(0.05, 0.05, 0.16, 0.008, 1, (-0.25, yf - 0.03, 0.52)), STEEL)
    a.add(box(0.035, 0.05, 0.12, 0.008, 1, (0.245, yf - 0.035, 0.52)), PBLK)
    # number sticker and detergent tray
    a.add(quad((0.20, yf - 0.0005, 0.81), (0.30, yf - 0.0005, 0.81), (0.30, yf - 0.0005, 0.85), (0.20, yf - 0.0005, 0.85)), "hr_prop_laundry", uv="rect", uv_rect=A.LAUNDRY["number"][2])
    a.add(box(0.18, 0.04, 0.05, 0.006, 1, (-0.20, yf - 0.01, 0.80)), STEEL)
    a.add(box(0.14, 0.006, 0.012, 0.0, 1, (-0.20, yf - 0.031, 0.81)), VOID)
    for x in (-0.30, 0.30):
        a.add(dome_head(0.006, 0.003), STEEL, T(x, yf - 0.001, 0.12) @ R("X", 90))
    a.meta.update(needsCollision=True, collider=box_collider((0.70, 0.86, 1.10), (0, -0.04, 0.55)),
                  notes="Commercial front-loading washer, stainless, porthole door, coin control panel. Front faces -Y.")
    return a


def tumble_dryer():
    a = Asset("TUMBLE_DRYER", "shop", 56)
    W, D, H = 0.80, 0.90, 1.95
    a.add(box(W, D, H - 0.05, 0.012, 2, (0, 0, 0.05 + (H - 0.05) / 2)), STEEL)
    a.add(box(W - 0.04, D - 0.06, 0.05, 0.004, 1, (0, 0.02, 0.025)), PBLK)
    yf = -D / 2
    # top control strip
    a.add(box(W - 0.04, 0.02, 0.30, 0.006, 1, (0, yf - 0.006, 1.76)), STEEL)
    a.add(quad((-0.37, yf - 0.0165, 1.62), (0.37, yf - 0.0165, 1.62), (0.37, yf - 0.0165, 1.90), (-0.37, yf - 0.0165, 1.90)), "hr_prop_laundry", uv="rect", uv_rect=A.LAUNDRY["dryer_panel"])
    for k, zc in enumerate((0.48, 1.20)):
        a.add(box(0.66, 0.012, 0.62, 0.006, 1, (0, yf - 0.004, zc)), STEEL)
        _porthole(a, T(0, yf - 0.010, zc), 0.27, 0.20)
        a.add(box(0.04, 0.05, 0.14, 0.008, 1, (0.29, yf - 0.04, zc)), PBLK)
        a.add(box(0.60, 0.01, 0.06, 0.003, 1, (0, yf - 0.006, zc - 0.36)), STEEL)
        a.add(box(0.18, 0.012, 0.01, 0.0, 1, (0, yf - 0.012, zc - 0.36)), VOID)
        a.add(quad((-0.32, yf - 0.0105, zc + 0.25), (-0.22, yf - 0.0105, zc + 0.25), (-0.22, yf - 0.0105, zc + 0.29), (-0.32, yf - 0.0105, zc + 0.29)), "hr_prop_laundry", uv="rect", uv_rect=A.LAUNDRY["number"][5 + k])
    a.meta.update(needsCollision=True, collider=box_collider((0.80, 0.98, 1.95), (0, -0.04, 0.975)),
                  notes="Stacked double tumble dryer, two porthole doors, top coin panel. Front faces -Y.")
    return a


def laundry_cage():
    a = Asset("LAUNDRY_CAGE", "shop", 57)
    L, Wd = 0.80, 0.55
    z0, z1 = 0.22, 0.95
    xs, ys = L / 2, Wd / 2
    wire = "hr_prop_wire_grid"
    for (p0, p1, p2, p3) in (((-xs, -ys, z0), (xs, -ys, z0), (xs, -ys, z1), (-xs, -ys, z0 + (z1 - z0))),
                             ((xs, ys, z0), (-xs, ys, z0), (-xs, ys, z1), (xs, ys, z1)),
                             ((xs, -ys, z0), (xs, ys, z0), (xs, ys, z1), (xs, -ys, z1)),
                             ((-xs, ys, z0), (-xs, -ys, z0), (-xs, -ys, z1), (-xs, ys, z1)),
                             ((-xs, -ys, z0), (-xs, ys, z0), (xs, ys, z0), (xs, -ys, z0))):
        P = [Vector(p) for p in (p0, p1, p2, p3)]
        lu, lv = (P[1] - P[0]).length, (P[3] - P[0]).length
        a.add(quad(p0, p1, p2, p3, uvs=((0, 0), (lu, 0), (lu, lv), (0, lv))), wire, uv="keep")
    rim = [(-xs, -ys, z1), (xs, -ys, z1), (xs, ys, z1), (-xs, ys, z1)]
    a.add(tube(rim, 0.011, 8, closed=True), GALV)
    a.add(tube([(-xs, -ys, z0), (xs, -ys, z0), (xs, ys, z0), (-xs, ys, z0)], 0.011, 8, closed=True), GALV)
    for (x, y) in ((-xs, -ys), (xs, -ys), (xs, ys), (-xs, ys)):
        a.add(cyl_between((x, y, 0.12), (x, y, z1), 0.012, 8), GALV)
        a.add(box(0.06, 0.06, 0.012, 0.002, 1, (x * 0.92, y * 0.88, 0.115)), GALV)
        a.add(box(0.012, 0.035, 0.05, 0.002, 1, (x * 0.92 - 0.02, y * 0.88, 0.085)), GALV)
        a.add(box(0.012, 0.035, 0.05, 0.002, 1, (x * 0.92 + 0.02, y * 0.88, 0.085)), GALV)
        a.add(cyl(0.045, 0.026, 14, -0.013), PBLK, T(x * 0.92, y * 0.88, 0.05) @ R("Y", 90))
    # hanging rail on two uprights at the back
    for x in (-xs, xs):
        a.add(cyl_between((x, ys, z1), (x, ys, 1.75), 0.012, 8), GALV)
    a.add(cyl_between((-xs, ys, 1.75), (xs, ys, 1.75), 0.012, 8), GALV)
    # a heap of washing
    heap = soft_box(0.62, 0.40, 0.30, 0.12, 4, (0, 0, 0))
    deform(heap, lambda p: p + Vector((0, 0, 0.06 * fbm(p.x * 6, p.y * 6, 0.3, 571) + 0.05 * fbm(p.x * 13, p.y * 11, 0.7, 572))))
    a.add(heap, "hr_prop_fabric", T(0, 0, z0 + 0.14), uv_scale=2.0)
    a.meta.update(needsCollision=True, collider=box_collider((0.84, 0.60, 1.76), (0, 0, 0.88)),
                  notes="Wheeled launderette cage trolley with wire mesh basket (alpha clipped), hanging rail and a heap of washing.")
    return a


def work_bench():
    a = Asset("WORK_BENCH", "shop", 58)
    rng = a.rng
    L, D, H = 1.80, 0.70, 0.90
    for (x, y) in ((-0.86, -0.31), (0.86, -0.31), (-0.86, 0.31), (0.86, 0.31)):
        a.add(box(0.045, 0.045, H - 0.04, 0.004, 1, (x, y, (H - 0.04) / 2)), BLK)
        a.add(box(0.07, 0.07, 0.008, 0.002, 1, (x, y, 0.004)), BLK)
    for y in (-0.31, 0.31):
        a.add(box(1.68, 0.04, 0.05, 0.004, 1, (0, y, H - 0.065)), BLK)
        a.add(box(1.68, 0.04, 0.04, 0.004, 1, (0, y, 0.18)), BLK)
    a.add(box(1.72, 0.60, 0.018, 0.003, 1, (0, 0, 0.21)), "hr_prop_formica_grey")
    a.add(box(L, D, 0.045, 0.006, 2, (0, 0, H - 0.0225)), TIMBER)
    # pegboard back with frame
    a.add(box(1.80, 0.018, 0.95, 0.004, 1, (0, 0.34, H + 0.475)), "hr_prop_pegboard", uv_scale=2.0)
    for x in (-0.89, 0.89):
        a.add(box(0.04, 0.04, 0.95, 0.004, 1, (x, 0.34, H + 0.475)), BLK)
    a.add(box(1.82, 0.05, 0.04, 0.004, 1, (0, 0.34, H + 0.96)), BLK)
    # tools on the pegboard
    yb = 0.325
    for k in range(7):
        x = -0.70 + k * 0.07
        ln = 0.14 + k * 0.025
        spanner = prism([(-0.008, 0.0), (0.008, 0.0), (0.008, ln - 0.02), (0.018, ln), (0.006, ln + 0.012), (0.0, ln - 0.004), (-0.006, ln + 0.012), (-0.018, ln)], 0.006, 0.0, 1)
        a.add(spanner, "hr_steel_galv", T(x, yb - 0.006, H + 0.62 - ln * 0.5) @ S(1, 1, 1))
    for k in range(4):
        x = 0.0 + k * 0.06
        a.add(cyl(0.012, 0.11, 8, 0.0), "hr_prop_tool_red" if k % 2 else "hr_plastic_black", T(x, yb - 0.02, H + 0.55))
        a.add(cyl(0.003, 0.12, 6, -0.12), "hr_steel_galv", T(x, yb - 0.02, H + 0.55))
    a.add(box(0.03, 0.025, 0.30, 0.004, 1, (0.40, yb - 0.02, H + 0.52)), TIMBER)
    a.add(box(0.11, 0.03, 0.035, 0.006, 1, (0.40, yb - 0.02, H + 0.68)), "hr_steel_aged")
    for k in range(3):
        a.add(torus(0.17 - k * 0.01, 0.011, 20, 5), "hr_prop_tyre", T(0.68, yb - 0.02 - k * 0.02, H + 0.62) @ R("X", 90))
    # vice at the right end, toolbox, a wheel and a pump on the bench
    vx = 0.72
    a.add(box(0.14, 0.18, 0.05, 0.006, 1, (vx, -0.22, H + 0.025)), "hr_prop_tool_red")
    a.add(box(0.13, 0.05, 0.10, 0.006, 1, (vx, -0.29, H + 0.10)), "hr_prop_tool_red")
    a.add(box(0.13, 0.05, 0.10, 0.006, 1, (vx, -0.20, H + 0.10)), "hr_prop_tool_red")
    a.add(cyl_between((vx, -0.42, H + 0.08), (vx, -0.12, H + 0.08), 0.008, 6), "hr_steel_galv")
    a.add(cyl_between((vx - 0.06, -0.42, H + 0.08), (vx + 0.06, -0.42, H + 0.08), 0.006, 6), "hr_steel_galv")
    a.add(box(0.42, 0.20, 0.18, 0.01, 2, (-0.55, 0.05, H + 0.09)), "hr_prop_tool_red")
    a.add(cyl_between((-0.70, 0.05, H + 0.22), (-0.40, 0.05, H + 0.22), 0.008, 6), BLK)
    for x in (-0.70, -0.40):
        a.add(cyl_between((x, 0.05, H + 0.18), (x, 0.05, H + 0.22), 0.008, 6), BLK)
    a.add(torus(0.30, 0.016, 32, 6), "hr_prop_tyre", T(0.05, -0.02, H + 0.017))
    a.add(torus(0.28, 0.008, 32, 4), "hr_steel_galv", T(0.05, -0.02, H + 0.017))
    a.add(cyl(0.02, 0.42, 10, 0.0), "hr_plastic_black", T(-0.86, -0.42, 0.0))
    a.add(box(0.12, 0.05, 0.015, 0.003, 1, (-0.86, -0.42, 0.007)), "hr_plastic_black")
    a.meta.update(needsCollision=True, collider=box_collider((1.82, 0.72, 1.86), (0, 0, 0.93)),
                  notes="Cycle workshop bench, steel frame, timber top, pegboard back with tools, vice, toolbox, inner tubes and a wheel.")
    return a


def youth_sofa():
    a = Asset("YOUTH_SOFA", "shop", 59)
    rng = a.rng
    F = "hr_prop_fabric"
    W, D = 2.0, 0.88
    a.add(soft_box(W, D - 0.10, 0.24, 0.04, 3, (0, 0.03, 0.20)), F, uv_scale=2.0)
    a.add(soft_box(W - 0.06, 0.20, 0.50, 0.06, 4, (0, D / 2 - 0.12, 0.55)), F, uv_scale=2.0)
    for sx in (-1, 1):
        arm = soft_box(0.20, D - 0.04, 0.34, 0.07, 4, (sx * (W / 2 - 0.10), 0.0, 0.46))
        a.add(arm, F, uv_scale=2.0)
    for k in range(3):
        cx = -0.53 + k * 0.53
        cu = soft_box(0.52, 0.60, 0.14, 0.06, 4, (0, 0, 0))
        sag = rng.uniform(0.02, 0.04)
        deform(cu, lambda p, s=sag, k=k: Vector((p.x, p.y, p.z - s * math.cos(p.x * 2.9) * math.cos(p.y * 2.4) * (1 if p.z > 0 else 0.3) + 0.006 * fbm(p.x * 9, p.y * 9, k, 590))))
        a.add(cu, F, T(cx + rng.uniform(-0.01, 0.01), -0.08 + rng.uniform(-0.02, 0.03), 0.39) @ R("Z", rng.uniform(-2, 2)), uv_scale=2.0)
        bc = soft_box(0.52, 0.18, 0.42, 0.07, 4, (0, 0, 0))
        deform(bc, lambda p, k=k: p + Vector((0, 0.02 * math.cos(p.x * 3) * (1 if p.y < 0 else 0) + 0.005 * fbm(p.x * 9, p.z * 9, k + 3, 591), 0)))
        a.add(bc, F, T(cx, 0.20, 0.66) @ R("X", 12 + rng.uniform(-4, 4)) @ R("Y", rng.uniform(-3, 3)), uv_scale=2.0)
    for (x, y) in ((-0.92, -0.33), (0.92, -0.33), (-0.92, 0.38), (0.92, 0.38)):
        a.add(cyl(0.025, 0.08, 10, 0.0), "hr_plastic_black", T(x, y, 0.0))
    a.meta.update(needsCollision=True, collider=box_collider((2.0, 0.88, 0.85), (0, 0, 0.425)),
                  notes="Worn three-seat fabric sofa for the youth club, sagging cushions.")
    return a


def table_folding():
    a = Asset("TABLE_FOLDING", "shop", 60)
    L, Wd, H = 1.83, 0.76, 0.74
    a.add(soft_box(L, Wd, 0.045, 0.015, 3, (0, 0, H - 0.0225)), "hr_prop_plastic_white")
    for y in (-0.33, 0.33):
        a.add(box(1.70, 0.025, 0.03, 0.003, 1, (0, y, H - 0.06)), GALV)
    for sx in (-1, 1):
        x = sx * 0.72
        a.add(tube(fillet_path([(x, -0.32, 0.0), (x, -0.32, H - 0.05), (x, 0.32, H - 0.05), (x, 0.32, 0.0)], 0.04, 3), 0.0125, 8, up=(1, 0, 0)), GALV)
        a.add(cyl_between((x, -0.32, 0.12), (x, 0.32, 0.12), 0.009, 6), GALV)
        a.add(cyl_between((x, 0.0, 0.12), (sx * 0.30, 0.0, H - 0.05), 0.008, 6), GALV)
        for y in (-0.32, 0.32):
            a.add(cyl(0.016, 0.02, 8, 0.0), "hr_plastic_black", T(x, y, 0.0))
    a.meta.update(needsCollision=True, collider=box_collider((1.83, 0.76, 0.74), (0, 0, 0.37)),
                  notes="1.83 m blow-moulded folding table on steel leg frames.")
    return a


def chair_stacking():
    a = Asset("CHAIR_STACKING", "shop", 61)
    P = "hr_prop_plastic_blue"
    seat = soft_box(0.44, 0.42, 0.022, 0.009, 3, (0, 0, 0))
    deform(seat, lambda p: Vector((p.x, p.y, p.z - 0.018 * (1 - (2 * p.x / 0.44) ** 2) * 0.6 + 0.012 * (p.y / 0.21) ** 2 * (p.y < 0))))
    a.add(seat, P, T(0, -0.02, 0.45))
    back = soft_box(0.42, 0.018, 0.30, 0.008, 3, (0, 0, 0))
    deform(back, lambda p: Vector((p.x, p.y + 0.03 * (2 * p.x / 0.42) ** 2, p.z)))
    a.add(back, P, T(0, 0.21, 0.70) @ R("X", 10))
    for sx in (-1, 1):
        x = sx * 0.205
        a.add(tube([(x * 1.06, -0.22, 0.0), (x, -0.17, 0.44), (x, 0.17, 0.44), (x * 1.06, 0.24, 0.0)], 0.0095, 8, up=(1, 0, 0)), GALV)
        a.add(cyl_between((x, 0.17, 0.44), (x, 0.235, 0.80), 0.0095, 8), GALV)
        for y in (-0.22, 0.24):
            a.add(cyl(0.012, 0.015, 8, 0.0), "hr_plastic_black", T(x * 1.06, y, 0.0))
    a.meta.update(needsCollision=True, collider=box_collider((0.48, 0.50, 0.86), (0, 0, 0.43)),
                  notes="Polypropylene stacking chair on a steel frame.")
    return a


def pool_table():
    a = Asset("POOL_TABLE", "shop", 62)
    rng = a.rng
    L, Wd, H = 2.05, 1.15, 0.80
    felt = "hr_prop_felt"
    # cabinet and legs
    a.add(box(L - 0.10, Wd - 0.10, 0.30, 0.02, 2, (0, 0, 0.56)), TIMBER)
    for (x, y) in ((-0.88, -0.45), (0.88, -0.45), (-0.88, 0.45), (0.88, 0.45)):
        a.add(loft([rrect(0.14, 0.14, 0.02, 2, 0.0), rrect(0.11, 0.11, 0.02, 2, 0.06), rrect(0.13, 0.13, 0.02, 2, 0.42)], True, True), TIMBER, T(x, y, 0))
    # bed and cushions
    pl, pw = 1.80, 0.90
    a.add(box(pl + 0.04, pw + 0.04, 0.04, 0.0, 1, (0, 0, 0.74)), felt)
    gap = 0.075
    # long cushions (two per side, split by the middle pocket) and short cushions
    for sy in (-1, 1):
        for (x0, x1) in ((-pl / 2 + gap, -0.06), (0.06, pl / 2 - gap)):
            prof = [(x0, 0.0), (x1, 0.0), (x1 - 0.025, 0.04), (x0 + 0.025, 0.04)]
            a.add(prism(prof, 0.05, 0.004, 1), felt, T(0, sy * (pw / 2 + 0.005), 0.76))
    for sx in (-1, 1):
        a.add(box(0.05, pw - 2 * gap, 0.04, 0.006, 1, (sx * (pl / 2 + 0.005), 0, 0.78)), felt)
    # top rails
    for sy in (-1, 1):
        a.add(box(L, 0.11, 0.05, 0.012, 2, (0, sy * (Wd / 2 - 0.055), 0.785)), TIMBER)
    for sx in (-1, 1):
        a.add(box(0.11, Wd - 0.22, 0.05, 0.012, 2, (sx * (L / 2 - 0.055), 0, 0.785)), TIMBER)
    # pockets: corners and middles
    for (x, y) in ((-pl / 2, -pw / 2), (pl / 2, -pw / 2), (-pl / 2, pw / 2), (pl / 2, pw / 2), (0, -pw / 2 - 0.015), (0, pw / 2 + 0.015)):
        a.add(cyl(0.058, 0.012, 16, 0.0), PBLK, T(x, y, 0.80))
        a.add(cyl(0.046, 0.02, 16, 0.0), VOID, T(x, y, 0.795))
    # coin slide and ball return
    a.add(box(0.22, 0.03, 0.10, 0.006, 1, (0, -Wd / 2 + 0.035, 0.56)), "hr_prop_stainless")
    a.add(box(0.12, 0.012, 0.012, 0.0, 1, (0, -Wd / 2 + 0.019, 0.58)), VOID)
    a.add(box(0.30, 0.04, 0.08, 0.004, 1, (0.6, -Wd / 2 + 0.03, 0.47)), VOID)
    # a few balls and a cue
    rb = 0.026
    balls = [("hr_prop_ball_white", -0.45, 0.05), ("hr_prop_pool_red", 0.40, -0.10), ("hr_prop_pool_red", 0.55, 0.12),
             ("hr_prop_pool_yellow", 0.25, 0.20), ("hr_prop_pool_yellow", 0.62, -0.25), ("hr_prop_ball_black", 0.48, 0.0)]
    for mat, x, y in balls:
        a.add(sphere(rb, 12, 8), mat, T(x, y, 0.76 + rb))
    a.add(cyl_between((-0.75, 0.30, 0.775), (0.62, 0.36, 0.778), 0.007, 8), TIMBER)
    a.meta.update(needsCollision=True, collider=box_collider((2.05, 1.15, 0.82), (0, 0, 0.41)),
                  notes="Seven-foot pub pool table, coin operated, with a few balls and a cue on the cloth.")
    return a


def office_desk():
    a = Asset("ESTATE_OFFICE_DESK", "shop", 63)
    rng = a.rng
    L, D, H = 1.60, 0.80, 0.74
    a.add(box(L, D, 0.025, 0.004, 1, (0, 0, H - 0.0125)), LAM)
    a.add(box(0.025, D - 0.04, H - 0.025, 0.003, 1, (-L / 2 + 0.03, 0, (H - 0.025) / 2)), GREY)
    a.add(box(L - 0.10, 0.018, 0.40, 0.003, 1, (0, D / 2 - 0.06, H - 0.24)), GREY)
    # pedestal with three drawers on the right
    px = L / 2 - 0.23
    a.add(box(0.44, D - 0.06, H - 0.03, 0.004, 1, (px, 0, (H - 0.03) / 2)), GREY)
    for k, (z0, z1) in enumerate(((0.03, 0.30), (0.31, 0.50), (0.51, 0.69))):
        a.add(box(0.42, 0.012, z1 - z0 - 0.008, 0.003, 1, (px, -D / 2 + 0.024, (z0 + z1) / 2)), GREY)
        a.add(box(0.12, 0.02, 0.012, 0.004, 1, (px, -D / 2 + 0.012, z1 - 0.04)), "hr_prop_stainless")
    # monitor
    mz = H
    a.add(box(0.22, 0.17, 0.012, 0.004, 1, (0, 0.16, mz + 0.006)), PBLK)
    a.add(box(0.05, 0.03, 0.22, 0.004, 1, (0, 0.18, mz + 0.12)), PBLK)
    sm = T(0, 0.155, mz + 0.34) @ R("X", -4)
    a.add(box(0.56, 0.025, 0.34, 0.006, 1), PBLK, sm)
    a.add(quad((-0.265, -0.0130, -0.155), (0.265, -0.0130, -0.155), (0.265, -0.0130, 0.165), (-0.265, -0.0130, 0.165)), SHOP_LIT, sm, uv="rect", uv_rect=A.SHOP["monitor"])
    # keyboard, mouse, phone, trays, mug, folders
    a.add(box(0.44, 0.15, 0.02, 0.004, 1, (0, -0.15, mz + 0.01)), PBLK)
    a.add(quad((-0.215, -0.22, mz + 0.0205), (0.215, -0.22, mz + 0.0205), (0.215, -0.08, mz + 0.0205), (-0.215, -0.08, mz + 0.0205)), SHOP, uv="rect", uv_rect=A.SHOP["keyboard"])
    a.add(soft_box(0.06, 0.10, 0.03, 0.012, 2, (0.32, -0.15, mz + 0.015)), PBLK)
    pm = T(-0.55, -0.05, mz) @ R("Z", 15)
    a.add(box(0.20, 0.22, 0.05, 0.01, 1, (0, 0, 0.025)), PBLK, pm)
    a.add(quad((-0.08, -0.10, 0.0505), (0.08, -0.10, 0.0505), (0.08, 0.06, 0.0505), (-0.08, 0.06, 0.0505)), SHOP, pm, uv="rect", uv_rect=A.SHOP["phone"])
    a.add(soft_box(0.20, 0.05, 0.05, 0.02, 2, (0, 0.07, 0.07)), PBLK, pm)
    for k in range(2):
        z = mz + k * 0.07
        a.add(box(0.26, 0.34, 0.006, 0.0, 1, (-0.58, 0.20, z + 0.003)), PBLK)
        for side in (-1, 1):
            a.add(box(0.006, 0.34, 0.06, 0.0, 1, (-0.58 + side * 0.127, 0.20, z + 0.03)), PBLK)
        a.add(box(0.21, 0.297, 0.02, 0.0, 1, (-0.58, 0.20, z + 0.016)), SHOP, uv="fit", fit_axis="Z", uv_rect=A.SHOP["papers"])
    a.add(lathe([(0.0, 0.0), (0.038, 0.0), (0.042, 0.095), (0.039, 0.095), (0.035, 0.008), (0.0, 0.008)], 14, False, False), "hr_prop_plastic_white", T(0.45, 0.10, mz))
    a.add(torus(0.025, 0.006, 10, 4), "hr_prop_plastic_white", T(0.495, 0.10, mz + 0.05) @ R("X", 90))
    for k in range(4):
        a.add(box(0.05, 0.25, 0.31, 0.004, 1, (0.70 - k * 0.055, 0.30, mz + 0.155)), ["hr_prop_plastic_blue", "hr_prop_tool_red", "hr_prop_formica_grey", "hr_prop_plastic_blue"][k])
    a.meta.update(needsCollision=True, collider=box_collider((1.60, 0.80, 0.74), (0, 0, 0.37)),
                  notes="Estate office panel-end desk with drawer pedestal, monitor, keyboard, phone, paper trays, mug and folders.")
    return a


BUILDERS = [shelf_unit, fridge, counter, shop_sign, washing_machine, tumble_dryer, laundry_cage, work_bench,
            youth_sofa, table_folding, chair_stacking, pool_table, office_desk]
