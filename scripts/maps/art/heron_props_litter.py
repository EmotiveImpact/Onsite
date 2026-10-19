"""Litter and clutter: render-only dressing plus the cone and trolley."""

import math

import bmesh
from mathutils import Vector

from heron_props_lib import (
    Asset, R, S, T, box, cyl, cyl_between, deform, fbm, fillet_path, lathe, quad, rect_profile, rrect,
    soft_box, sweep, tube, vnoise, _new,
)
from heron_props_street import box_collider, cyl_collider, _wheel
import heron_props_atlas as A

BAG = "hr_prop_bin_bag"
LIT = "hr_prop_litter"


def _bag_mesh(seed, h=0.62, r=0.27):
    """A tied refuse sack: lathe body, settled, creased and gathered at the neck."""
    prof = [(0.0, 0.0), (r * 0.55, 0.0), (r * 0.88, 0.02), (r * 1.0, 0.08), (r * 1.04, 0.20), (r * 1.0, 0.34),
            (r * 0.86, 0.46), (r * 0.55, h * 0.84), (r * 0.22, h * 0.92), (r * 0.10, h * 0.95), (r * 0.12, h * 0.98),
            (r * 0.05, h), (0.0, h * 1.005)]
    bm = lathe(prof, 18, False, False)
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.05], cuts=1)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])

    def f(p):
        ang = math.atan2(p.y, p.x)
        zf = max(0.0, min(1.0, p.z / h))
        rad = math.hypot(p.x, p.y)
        n1 = fbm(math.cos(ang) * 1.6 + seed, math.sin(ang) * 1.6, zf * 2.5, seed, 3)
        n2 = vnoise(math.cos(ang) * 4 + seed, math.sin(ang) * 4, zf * 6, seed + 9)
        gather = 0.012 * math.sin(ang * 9 + zf * 3) * max(0.0, zf - 0.55) * 2.2
        k = 1.0 + 0.16 * n1 + 0.05 * n2
        rad2 = rad * k + gather
        x, y = rad2 * math.cos(ang), rad2 * math.sin(ang) * 0.86
        z = p.z * (0.92 + 0.06 * n1)
        # settle: bottom spreads flat, top leans
        if z < 0.06:
            z = max(0.0, z * 0.7)
        x += 0.05 * zf * zf
        return Vector((x, y, z))
    deform(bm, f)
    return bm


def bin_bag():
    a = Asset("BIN_BAG", "litter", 71)
    a.add(_bag_mesh(3), BAG, sharp=70)
    a.add(lathe([(0.0, 0.0), (0.04, 0.01), (0.03, 0.05), (0.0, 0.06)], 6, False, False), BAG, T(-0.005, 0.0, 0.60) @ R("Y", 40), sharp=70)
    a.add(lathe([(0.0, 0.0), (0.035, 0.01), (0.025, 0.045), (0.0, 0.055)], 6, False, False), BAG, T(0.02, 0.0, 0.60) @ R("Y", -45), sharp=70)
    a.meta.update(needsCollision=False, collider=None, notes="Tied black refuse sack, about 0.62 m. Render only.")
    return a


def bin_bag_b():
    a = Asset("BIN_BAG_B", "litter", 72)
    bm = _bag_mesh(11, 0.55, 0.25)
    # lying on its side
    bmesh.ops.transform(bm, matrix=R("Y", 78), verts=bm.verts)
    zmin = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z -= zmin
        if v.co.z < 0.05:
            v.co.z *= 0.6
    xc = sum(v.co.x for v in bm.verts) / len(bm.verts)
    for v in bm.verts:
        v.co.x -= xc
    a.add(bm, BAG, sharp=70)
    a.meta.update(needsCollision=False, collider=None, notes="Refuse sack lying on its side. Render only.")
    return a


def bin_bag_c():
    a = Asset("BIN_BAG_C", "litter", 73)
    a.add(_bag_mesh(21, 0.60, 0.26), BAG, T(-0.22, 0.05, 0.0) @ R("Z", 20), sharp=70)
    a.add(_bag_mesh(22, 0.56, 0.25), BAG, T(0.24, -0.02, 0.0) @ R("Z", -50), sharp=70)
    top = _bag_mesh(23, 0.52, 0.23)
    bmesh.ops.transform(top, matrix=R("Y", 70), verts=top.verts)
    a.add(top, BAG, T(0.0, 0.10, 0.36) @ R("Z", 15), sharp=70)
    a.meta.update(needsCollision=False, collider=None, notes="Pile of three refuse sacks. Render only (give the pile a low box if it should block).")
    return a


def crushed_can():
    a = Asset("CRUSHED_CAN", "litter", 74)
    r, h = 0.033, 0.115
    bm = lathe([(0.0, 0.0), (r * 0.8, 0.0)] + [(r, 0.008 + (h - 0.018) * k / 8) for k in range(9)] + [(r * 0.82, h - 0.002), (0.0, h)], 14, False, False, uv="unit")
    uvl = bm.loops.layers.uv.active
    rect = A.LITTER["can"]
    for f in bm.faces:
        for l in f.loops:
            u = l[uvl].uv.x
            l[uvl].uv = (rect[0] + (rect[2] - rect[0]) * u, rect[1] + (rect[3] - rect[1]) * max(0, min(1, l.vert.co.z / h)))

    def f(p):
        zf = p.z / h
        ang = math.atan2(p.y, p.x)
        fold = 0.006 * math.sin(zf * math.pi * 5 + ang * 2)
        rad = math.hypot(p.x, p.y)
        rad2 = rad * (1 + 0.25 * fbm(math.cos(ang) * 2, math.sin(ang) * 2, zf * 3, 741)) + fold * (rad > 0.01)
        z = p.z * 0.55 + 0.01 * vnoise(ang * 2, zf * 4, 0, 742)
        return Vector((rad2 * math.cos(ang), rad2 * math.sin(ang) * 0.55, z))
    deform(bm, f)
    bmesh.ops.transform(bm, matrix=T(0, 0, 0.022) @ R("X", 90) @ T(0, 0, -0.032), verts=bm.verts)
    a.add(bm, LIT, uv="keep", sharp=55)
    a.meta.update(needsCollision=False, collider=None, notes="Stepped-on drinks can lying on its side. Render only.")
    return a


def crisp_packet():
    a = Asset("CRISP_PACKET", "litter", 75)
    w, h = 0.17, 0.23
    bm = soft_box(w, 0.04, h, 0.015, 4, (0, 0, 0))

    def f(p):
        zf = abs(p.z) / (h / 2)
        y = p.y * max(0.05, 1 - zf ** 3)
        if zf > 0.88:
            y = p.y * 0.04
        y += 0.010 * fbm(p.x * 30, p.z * 30, 0, 751)
        return Vector((p.x * (1 - 0.06 * zf), y, p.z + 0.004 * vnoise(p.x * 40, p.y * 40, 0, 752)))
    deform(bm, f)
    a.add(bm, LIT, T(0, 0, 0.012) @ R("X", -90) @ R("Y", 0), uv="fit", fit_axis="Y", uv_rect=A.LITTER["crisp"], sharp=60)
    a.meta.update(needsCollision=False, collider=None, notes="Crumpled crisp packet lying flat. Render only.")
    return a


def cardboard_flat():
    a = Asset("CARDBOARD_FLAT", "litter", 76)
    L, W, t = 0.92, 0.62, 0.006
    bm = box(L, W, t, 0.0, 1, (0, 0, t / 2))
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6], cuts=5, use_grid_fill=True)

    def f(p):
        lift = 0.0
        if p.x > 0.2:
            lift = (p.x - 0.2) * 0.12
        lift += max(0.0, -p.y - 0.2) * 0.10 * (p.x < -0.2)
        lift += 0.006 * fbm(p.x * 4, p.y * 4, 0, 761)
        return Vector((p.x, p.y, p.z + lift))
    deform(bm, f)
    a.add(bm, LIT, uv="fit", fit_axis="Z", uv_rect=A.LITTER["cardboard"], sharp=50)
    a.meta.update(needsCollision=False, collider=None, notes="Flattened cardboard box, slightly curled and water stained. Render only.")
    return a


def traffic_cone():
    a = Asset("TRAFFIC_CONE", "litter", 77)
    a.add(box(0.38, 0.38, 0.035, 0.012, 2, (0, 0, 0.0175)), "hr_prop_tyre")
    a.add(lathe([(0.17, 0.035), (0.16, 0.05)], 20, False, False), "hr_prop_tyre")
    prof = [(0.155, 0.045), (0.150, 0.06)]
    zs = [0.06, 0.34, 0.345, 0.48, 0.485, 0.55, 0.555, 0.63, 0.635, 0.70]
    rr = lambda z: 0.150 - (0.150 - 0.030) * (z - 0.06) / (0.72 - 0.06)
    prof += [(rr(z), z) for z in zs[1:]]
    prof += [(0.028, 0.718), (0.018, 0.73), (0.0, 0.732)]
    a.add(lathe(prof, 20, False, False), "hr_prop_cone")
    for (z0, z1) in ((0.345, 0.48), (0.555, 0.63)):
        a.add(lathe([(rr(z0) + 0.0018, z0), (rr(z1) + 0.0018, z1)], 20, False, False), "hr_prop_reflective")
    a.meta.update(needsCollision=False, collider=cyl_collider(0.16, 0.73), notes="750 mm road cone with two reflective sleeves. Render only by default.")
    return a


def shopping_trolley():
    a = Asset("SHOPPING_TROLLEY", "litter", 78)
    wire = "hr_prop_wire_grid"
    G = "hr_steel_galv"
    # basket corners: front is -Y and narrower/lower
    top = [(-0.27, -0.46, 0.98), (0.27, -0.46, 0.98), (0.28, 0.42, 1.00), (-0.28, 0.42, 1.00)]
    bot = [(-0.22, -0.30, 0.55), (0.22, -0.30, 0.55), (0.25, 0.40, 0.62), (-0.25, 0.40, 0.62)]
    faces = [(bot[0], bot[1], top[1], top[0]), (bot[1], bot[2], top[2], top[1]), (bot[2], bot[3], top[3], top[2]),
             (bot[3], bot[0], top[0], top[3]), (bot[3], bot[2], bot[1], bot[0])]
    for q in faces:
        P = [Vector(p) for p in q]
        lu, lv = (P[1] - P[0]).length, (P[3] - P[0]).length
        a.add(quad(*q, uvs=((0, 0), (lu * 2, 0), (lu * 2, lv * 2), (0, lv * 2))), wire, uv="keep")
    a.add(tube(top, 0.008, 6, closed=True), G)
    a.add(tube(bot, 0.006, 6, closed=True), G)
    for k in range(4):
        a.add(cyl_between(bot[k], top[k], 0.007, 6), G)
    # child seat flap at the back
    a.add(quad((-0.26, 0.40, 0.80), (0.26, 0.40, 0.80), (0.26, 0.38, 0.99), (-0.26, 0.38, 0.99), uvs=((0, 0), (1.04, 0), (1.04, 0.38), (0, 0.38))), wire, uv="keep")
    a.add(cyl_between((-0.26, 0.40, 0.80), (0.26, 0.40, 0.80), 0.006, 6), G)
    # chassis
    for sx in (-1, 1):
        a.add(tube([(sx * 0.20, -0.42, 0.14), (sx * 0.24, 0.38, 0.14), (sx * 0.28, 0.48, 1.04)], 0.012, 8), G)
        a.add(cyl_between((sx * 0.22, -0.28, 0.14), (sx * 0.22, -0.30, 0.55), 0.010, 6), G)
        a.add(cyl_between((sx * 0.25, 0.30, 0.14), (sx * 0.25, 0.40, 0.62), 0.010, 6), G)
    a.add(cyl_between((-0.20, -0.42, 0.14), (0.20, -0.42, 0.14), 0.012, 8), G)
    # lower tray
    a.add(quad((-0.20, -0.36, 0.17), (0.20, -0.36, 0.17), (0.23, 0.32, 0.17), (-0.23, 0.32, 0.17), uvs=((0, 0), (0.8, 0), (0.92, 1.36), (0, 1.36))), wire, uv="keep")
    # handle
    a.add(cyl_between((-0.30, 0.49, 1.05), (0.30, 0.49, 1.05), 0.018, 10), "hr_prop_trolley_plastic")
    for sx in (-1, 1):
        a.add(cyl_between((sx * 0.28, 0.48, 1.04), (sx * 0.30, 0.49, 1.05), 0.014, 8), "hr_prop_trolley_plastic")
    # castors
    for (x, y) in ((-0.20, -0.40), (0.20, -0.40), (-0.24, 0.34), (0.24, 0.34)):
        a.add(box(0.035, 0.05, 0.05, 0.004, 1, (x, y, 0.105)), G)
        _wheel(a, 0.062, 0.03, (x, y + 0.02, 0.062), "X", "hr_prop_tyre", "hr_plastic_black", 0)
    a.meta.update(needsCollision=True, collider=box_collider((0.62, 1.0, 1.06), (0, 0.0, 0.53)),
                  notes="Abandoned shopping trolley, wire basket alpha clipped (25 mm grid). Generic, no branding.")
    return a


def mattress():
    a = Asset("MATTRESS_DUMPED", "litter", 79)
    L, W, Ht = 1.90, 0.90, 0.20
    bm = soft_box(L, W, Ht, 0.05, 6, (0, 0, 0))
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.x - e.verts[1].co.x) > 0.1], cuts=2, use_grid_fill=True)

    def f(p):
        x = p.x
        z = p.z + Ht / 2
        # far end flopped up against a wall or bin
        t = max(0.0, (x - 0.35) / (L / 2 - 0.35))
        bend = math.radians(62) * t * t
        if t > 0:
            r0 = 0.45
            ang = bend
            x2 = 0.35 + (x - 0.35) * math.cos(ang) - (z - 0.0) * math.sin(ang) * 0.6
            z2 = z * math.cos(ang) + (x - 0.35) * math.sin(ang) * 0.9
            x, z = x2, z2
        z += 0.03 * fbm(p.x * 2.5, p.y * 2.5, 0, 791) + 0.015 * math.sin(p.y * 4.0) * (abs(p.x) < 0.3)
        y = p.y * (1 + 0.02 * vnoise(p.x * 3, p.z * 3, 0, 792))
        return Vector((x, y, max(0.0, z)))
    deform(bm, f)
    a.add(bm, "hr_prop_mattress", R("Z", 8), uv="fit", fit_axis="Z", uv_rect=(0, 0, 1, 1), sharp=60)
    a.meta.update(needsCollision=False, collider=box_collider((1.9, 0.95, 0.6), (0, 0, 0.3)),
                  notes="Dumped single mattress, stained, one end flopped up. Render only by default; the collider is offered if it should block.")
    return a


BUILDERS = [bin_bag, bin_bag_b, bin_bag_c, crushed_can, crisp_packet, cardboard_flat, traffic_cone, shopping_trolley, mattress]
