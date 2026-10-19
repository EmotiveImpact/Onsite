"""Generic hatchback and panel van for the street outside the site.

The body is a loft of cross-sections defined by smooth profile tables (half
width, sill, shoulder, belt, roof). Glass, pillars and trims are assigned by
section band and station. Lamps, grille and plates are patches that follow the
body surface. Built nose toward +X, then turned so the nose faces -Y.
"""

import math

import bmesh
from mathutils import Vector

from heron_props_lib import (
    Asset, R, S, T, box, cyl, cyl_between, deform, fbm, lathe, look_matrix, quad, rrect, soft_box,
    sweep, torus, tube, _new,
)
from heron_props_street import box_collider
import heron_props_atlas as A

VEH = "hr_prop_vehicle"
GLASS = "hr_glass"
TRIM = "hr_plastic_black"
TYRE = "hr_rubber"


def smooth_interp(x, table):
    xs = [p[0] for p in table]
    if x <= xs[0]:
        return table[0][1]
    if x >= xs[-1]:
        return table[-1][1]
    for i in range(len(table) - 1):
        x0, y0 = table[i]
        x1, y1 = table[i + 1]
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            t = t * t * (3 - 2 * t)
            return y0 + (y1 - y0) * t
    return table[-1][1]


class Body:
    def __init__(self, spec):
        self.s = spec

    def params(self, x):
        s = self.s
        hw = smooth_interp(x, s["hw"])
        zr = smooth_interp(x, s["zr"])
        zw = min(smooth_interp(x, s["zw"]), zr - 0.10)
        zs = min(smooth_interp(x, s["zs"]), zw - 0.08)
        hr = min(smooth_interp(x, s["hr"]), hw - 0.11)
        zb = s["sill"]
        for (ax, ar) in s["axles"]:
            R_ = s["arch"]
            dx = x - ax
            if abs(dx) < R_:
                zb = max(zb, s["wheel_r"] + math.sqrt(R_ * R_ - dx * dx))
        zb = max(zb, smooth_interp(x, s["zb_ends"]))
        return hw, zr, zw, zs, hr, zb

    def half(self, x):
        hw, zr, zw, zs, hr, zb = self.params(x)
        p1z = min(zb + 0.07, zs - 0.03)
        z6 = max(zw + 0.04, zr - 0.10)
        z7 = max(z6 + 0.01, zr - 0.04)
        return [
            (hw - 0.065, zb), (hw - 0.025, p1z), (hw + 0.01, zs), (hw - 0.015, zw - 0.04), (hw - 0.035, zw),
            (hw - 0.075, zw + 0.02), (hr + 0.03, z6), (hr - 0.03, z7), (hr * 0.55, zr - 0.013), (0.0, zr),
        ]

    def loop(self, x):
        h = self.half(x)
        left = [Vector((x, -y, z)) for (y, z) in h[:-1]]
        right = [Vector((x, y, z)) for (y, z) in reversed(h[:-1])]
        return left + [Vector((x, 0.0, h[-1][1]))] + right

    def point(self, x, s_idx, side=1):
        """Point on the right (side=1) or left (-1) half at fractional band index 0..9."""
        h = self.half(x)
        i = max(0, min(8, int(math.floor(s_idx))))
        t = s_idx - i
        y = h[i][0] * (1 - t) + h[i + 1][0] * t
        z = h[i][1] * (1 - t) + h[i + 1][1] * t
        return Vector((x, side * y, z))

    def normal(self, x, s_idx, side=1):
        e = 0.004
        p = self.point(x, s_idx, side)
        dx = self.point(x + e, s_idx, side) - self.point(x - e, s_idx, side)
        ds = self.point(x, min(9, s_idx + 0.05), side) - self.point(x, max(0, s_idx - 0.05), side)
        n = ds.cross(dx) if side > 0 else dx.cross(ds)
        if n.length < 1e-9:
            return Vector((0, side, 0))
        n.normalize()
        return n


def body_mesh(body, stations, band_mat):
    """Loft the stations. band_mat(x, band, side) -> material slot index."""
    bm = _new()
    loops = [body.loop(x) for x in stations]
    vr = [[bm.verts.new(p) for p in lp] for lp in loops]
    n = len(loops[0])
    mid = n // 2
    for i in range(len(stations) - 1):
        xc = 0.5 * (stations[i] + stations[i + 1])
        for k in range(n - 1):
            f = bm.faces.new((vr[i][k], vr[i + 1][k], vr[i + 1][k + 1], vr[i][k + 1]))
            band = k if k < mid else (n - 2 - k)
            side = -1 if k < mid else 1
            f.material_index = band_mat(xc, band, side)
    # end caps
    f = bm.faces.new(list(reversed(vr[0])))
    f.material_index = band_mat(stations[0], -1, 0)
    f = bm.faces.new(vr[-1])
    f.material_index = band_mat(stations[-1], -2, 0)
    bm.normal_update()
    # make normals point outward (centroid test per face)
    c = Vector((0.5 * (stations[0] + stations[-1]), 0, 0.6))
    for f in bm.faces:
        fc = f.calc_center_median()
        d = fc - Vector((fc.x, 0, 0.75))
        if abs(fc.x - stations[0]) < 1e-6 or abs(fc.x - stations[-1]) < 1e-6:
            want = Vector((1 if fc.x > c.x else -1, 0, 0))
        else:
            want = d
        if f.normal.dot(want) < 0:
            f.normal_flip()
    return bm


def patch(body, xa, xb, sa, sb, side, nx=6, ns=4, off=0.004):
    """Grid patch following the body between stations xa..xb and bands sa..sb, 0..1 UVs."""
    bm = _new()
    uvl = bm.loops.layers.uv.active
    grid = []
    for i in range(nx + 1):
        x = xa + (xb - xa) * i / nx
        row = []
        for j in range(ns + 1):
            s = sa + (sb - sa) * j / ns
            p = body.point(x, s, side) + body.normal(x, s, side) * off
            row.append(bm.verts.new(p))
        grid.append(row)
    for i in range(nx):
        for j in range(ns):
            q = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
            if side > 0:
                q = (q[0], q[3], q[2], q[1])
            f = bm.faces.new(q)
            for l in f.loops:
                ii = [r for r in range(nx + 1) for jj in range(ns + 1) if grid[r][jj] is l.vert][0]
                jj = [c for c in range(ns + 1) if grid[ii][c] is l.vert][0]
                u = ii / nx
                v = jj / ns
                l[uvl].uv = (u if side > 0 else 1 - u, v)
    bm.normal_update()
    return bm


def wheel(a, centre, r, width, side, face_rect, turn, spokes_alloy=True):
    """Tyre with sidewall bulge, recessed textured wheel face, dark barrel."""
    cx, cy, cz = centre
    m = turn @ T(cx, cy, cz) @ R("X", -90 if side > 0 else 90)
    w = width / 2
    prof = [(r * 0.66, -w * 0.9), (r * 0.80, -w * 1.0), (r * 0.93, -w * 0.96), (r * 0.99, -w * 0.70),
            (r, -w * 0.3), (r, w * 0.3), (r * 0.99, w * 0.70), (r * 0.93, w * 0.96), (r * 0.80, w * 1.0), (r * 0.66, w * 0.9)]
    a.add(lathe(prof, 28, False, False), TYRE, m)
    # rim lip and textured face (outer side is +local z)
    a.add(lathe([(r * 0.66, w * 0.9), (r * 0.645, w * 0.82), (r * 0.62, w * 0.70)], 28, False, False), "hr_steel_galv" if not spokes_alloy else "hr_steel_black", m)
    face = lathe([(r * 0.62, w * 0.70), (0.0, w * 0.62)], 28, False, False)
    uvl = face.loops.layers.uv.active
    u0, v0, u1, v1 = face_rect
    for f in face.faces:
        for l in f.loops:
            x, y = l.vert.co.x, l.vert.co.y
            l[uvl].uv = (u0 + (u1 - u0) * (0.5 + x / (2 * r * 0.62)), v0 + (v1 - v0) * (0.5 + y / (2 * r * 0.62)))
    a.add(face, VEH, m, uv="keep")
    a.add(lathe([(r * 0.62, w * 0.70), (r * 0.60, -w * 0.8)], 20, False, False), "hr_prop_dark_void", m, flip=True)


def arch_liner(a, ax, R_, y0, y1, wheel_r, turn, side):
    bm = _new()
    n = 14
    rows = []
    for k in range(n + 1):
        ang = math.pi * k / n
        x = ax + R_ * math.cos(ang)
        z = wheel_r + R_ * math.sin(ang)
        rows.append([bm.verts.new((x, side * y0, z)), bm.verts.new((x, side * y1, z))])
    for k in range(n):
        q = (rows[k][0], rows[k][1], rows[k + 1][1], rows[k + 1][0])
        if side < 0:
            q = tuple(reversed(q))
        bm.faces.new(q)
    bm.normal_update()
    for f in bm.faces:
        c = f.calc_center_median()
        if f.normal.dot(Vector((ax, c.y, wheel_r)) - c) < 0:
            f.normal_flip()
    a.add(bm, TRIM, turn)


def interior(a, turn, x_dash, x_front_seat, x_rear, hw, z_floor, rear=True):
    a.add(box(0.40, 2 * hw - 0.20, 0.20, 0.04, 2, (x_dash, 0, z_floor + 0.52)), TRIM, turn)
    for sy in (-1, 1):
        y = sy * 0.36
        a.add(soft_box(0.50, 0.48, 0.12, 0.04, 2, (x_front_seat, y, z_floor + 0.30)), "hr_prop_fabric", turn, uv_scale=2.0)
        a.add(soft_box(0.12, 0.46, 0.62, 0.05, 2, (x_front_seat - 0.30, y, z_floor + 0.66)), "hr_prop_fabric", turn @ T(x_front_seat - 0.30, y, z_floor + 0.40) @ R("Y", -14) @ T(-(x_front_seat - 0.30), -y, -(z_floor + 0.40)), uv_scale=2.0)
    a.add(torus(0.17, 0.016, 20, 5), TRIM, turn @ T(x_dash - 0.30, -0.36, z_floor + 0.66) @ R("Y", -62))
    if rear:
        a.add(soft_box(0.50, 2 * hw - 0.30, 0.12, 0.04, 2, (x_rear, 0, z_floor + 0.32)), "hr_prop_fabric", turn, uv_scale=2.0)
        a.add(soft_box(0.12, 2 * hw - 0.30, 0.56, 0.05, 2, (x_rear - 0.30, 0, z_floor + 0.64)), "hr_prop_fabric", turn, uv_scale=2.0)


# ---------------------------------------------------------------------------

HATCH = {
    "hw": [(-2.0, 0.66), (-1.99, 0.74), (-1.96, 0.80), (-1.88, 0.85), (-1.6, 0.872), (1.2, 0.875), (1.60, 0.862),
           (1.80, 0.835), (1.91, 0.79), (1.965, 0.72), (1.99, 0.64), (2.0, 0.56)],
    "zr": [(-2.0, 0.95), (-1.985, 1.01), (-1.95, 1.08), (-1.88, 1.18), (-1.80, 1.26), (-1.70, 1.32), (-1.50, 1.375),
           (-1.20, 1.415), (-0.60, 1.44), (0.0, 1.435), (0.20, 1.41), (0.45, 1.31), (0.70, 1.16), (0.90, 1.035),
           (1.00, 0.985), (1.12, 0.955), (1.50, 0.895), (1.78, 0.835), (1.92, 0.775), (1.975, 0.71), (2.0, 0.64)],
    "zw": [(-2.0, 1.00), (-1.75, 1.04), (-1.45, 1.035), (-1.0, 0.995), (0.0, 0.96), (0.9, 0.93), (2.0, 0.90)],
    "zs": [(-2.0, 0.84), (-1.4, 0.86), (0.0, 0.83), (1.4, 0.80), (2.0, 0.72)],
    "hr": [(-2.0, 0.58), (-1.9, 0.62), (-1.4, 0.64), (0.3, 0.64), (0.7, 0.68), (1.0, 0.78), (1.8, 0.76), (2.0, 0.52)],
    "zb_ends": [(-2.0, 0.27), (-1.80, 0.24), (-1.70, 0.0), (1.85, 0.0), (1.95, 0.25), (2.0, 0.28)],
    "sill": 0.205,
    "axles": [(-1.35, 0.0), (1.22, 0.0)],
    "arch": 0.355,
    "wheel_r": 0.31,
}


def stations_for(x0, x1, axles, arch, extra=()):
    xs = set()
    k = 0
    x = x0
    # dense near the ends, regular in the middle
    for t in (0.0, 0.004, 0.012, 0.025, 0.045, 0.07, 0.10, 0.14, 0.19):
        xs.add(round(x0 + t, 4))
        xs.add(round(x1 - t, 4))
    n = 34
    for i in range(n + 1):
        xs.add(round(x0 + 0.19 + (x1 - x0 - 0.38) * i / n, 4))
    for (ax, _) in axles:
        for k in range(-7, 8):
            xs.add(round(ax + arch * k / 7.0, 4))
    for e in extra:
        xs.add(round(e, 4))
    return sorted(xs)


def car_hatchback():
    a = Asset("CAR_HATCHBACK", "vehicle", 81)
    turn = R("Z", -90)
    PAINT = "hr_prop_car_paint"
    body = Body(HATCH)
    mats = [PAINT, GLASS, TRIM]
    win_zones = [(-0.08, 0.84), (-1.00, -0.25), (-1.32, -1.13)]

    def band_mat(x, band, side):
        if band < 0:
            return 0
        if band == 0:
            return 2
        if band == 5:  # side glass band
            if any(z0 <= x <= z1 for (z0, z1) in win_zones):
                return 1
            if -0.24 < x < -0.08 or -1.12 < x < -1.0:
                return 2
            return 0
        if band in (6, 7, 8):
            if 0.20 <= x <= 0.97:
                return 1 if band >= 7 else 0
            if -1.93 <= x <= -1.66:
                return 1 if band >= 7 else 0
        return 0

    st = stations_for(-2.0, 2.0, HATCH["axles"], HATCH["arch"], tuple(0.20 + 0.04 * k for k in range(20)) + tuple(-1.93 + 0.03 * k for k in range(10)) + (-0.08, 0.84, -1.00, -0.25, -1.13, -1.32, -0.24, -1.12))
    bm = body_mesh(body, st, band_mat)
    a.add(bm, mats, turn, sharp=48)
    # underbody pieces avoiding the wheels
    yb = 0.60
    for (x0, x1, hy) in ((-1.86, -1.72, 0.80), (-1.72, -0.98, yb), (-0.98, 0.86, 0.80), (0.86, 1.58, yb), (1.58, 1.88, 0.80)):
        a.add(box(x1 - x0, 2 * hy, 0.02, 0.0, 1, ((x0 + x1) / 2, 0, 0.215)), TRIM, turn)
    for (ax, _) in HATCH["axles"]:
        for side in (-1, 1):
            arch_liner(a, ax, HATCH["arch"] - 0.005, 0.50, 0.86, HATCH["wheel_r"], turn, side)
            wheel(a, (ax, side * 0.745, HATCH["wheel_r"]), HATCH["wheel_r"], 0.205, side, A.VEHICLE["alloy"], turn)
    # front: grille, lower intake, plate, headlights
    xf = 2.0
    a.add(box(0.03, 0.80, 0.14, 0.01, 1, (xf - 0.005, 0, 0.53)), VEH, turn, uv="fit", fit_axis="Y", uv_rect=A.VEHICLE["grille"])
    a.add(box(0.03, 1.00, 0.10, 0.01, 1, (xf - 0.012, 0, 0.34)), VEH, turn, uv="fit", fit_axis="Y", uv_rect=A.VEHICLE["grille"])
    a.add(box(0.012, 0.52, 0.111, 0.003, 1, (xf + 0.006, 0, 0.43)), VEH, turn, uv="fit", fit_axis="Y", uv_rect=A.VEHICLE["plate_front"])
    for side in (-1, 1):
        a.add(patch(body, 1.70, 1.988, 2.5, 4.5, side, 6, 3, 0.004), VEH, turn, uv="rect", uv_rect=A.VEHICLE["headlight"])
        a.add(patch(body, -1.995, -1.90, 2.2, 3.9, side, 4, 3, 0.004), VEH, turn, uv="rect", uv_rect=A.VEHICLE["taillight"])
        # fog lamp recesses
        a.add(box(0.02, 0.16, 0.06, 0.008, 1, (xf - 0.02, side * 0.62, 0.33)), TRIM, turn)
    # rear: plate, reflectors, wiper, bumper insert
    xr = -2.0
    a.add(box(0.012, 0.52, 0.111, 0.003, 1, (xr - 0.006, 0, 0.62)), VEH, turn, uv="fit", fit_axis="Y", uv_rect=A.VEHICLE["plate_rear"])
    a.add(box(0.03, 1.10, 0.10, 0.01, 1, (xr + 0.012, 0, 0.33)), TRIM, turn)
    for side in (-1, 1):
        a.add(box(0.012, 0.10, 0.025, 0.004, 1, (xr + 0.004, side * 0.55, 0.36)), "hr_prop_lens_red", turn)
    a.add(box(0.30, 0.012, 0.01, 0.002, 1, (-1.86, 0.12, 1.10)), TRIM, turn @ T(-1.86, 0.12, 1.10) @ R("Y", 50) @ T(1.86, -0.12, -1.10))
    # door shut lines, handles, mirrors
    for side in (-1, 1):
        for x in (0.88, -0.10, -0.99):
            a.add(patch(body, x - 0.003, x + 0.003, 0.9, 4.6, side, 1, 4, 0.0015), TRIM, turn, uv="keep")
        a.add(patch(body, -0.99, 0.88, 0.95, 1.05, side, 8, 1, 0.0015), TRIM, turn, uv="keep")
        for x in (0.30, -0.62):
            p = body.point(x, 3.3, side)
            nrm = body.normal(x, 3.3, side)
            a.add(soft_box(0.13, 0.03, 0.028, 0.008, 2, (0, 0, 0)), PAINT, turn @ T(*(p + nrm * 0.008)) @ look_matrix(nrm) @ R("X", 90))
        mp = body.point(0.78, 5.0, side) + Vector((0, side * 0.10, 0.02))
        a.add(soft_box(0.10, 0.20, 0.12, 0.035, 2, tuple(mp)), PAINT, turn)
        a.add(box(0.06, 0.08, 0.04, 0.01, 1, tuple(mp + Vector((-0.02, -side * 0.10, -0.03)))), TRIM, turn)
        a.add(box(0.004, 0.17, 0.09, 0.0, 1, tuple(mp + Vector((-0.051, 0, 0)))), GLASS, turn)
    # roof spoiler lip, fin and exhaust
    zsp = body.params(-1.70)[1] + 0.012
    a.add(soft_box(0.13, 1.16, 0.03, 0.012, 2, (0, 0, 0)), PAINT, turn @ T(-1.72, 0, zsp) @ R("Y", 12))
    a.add(soft_box(0.16, 0.06, 0.06, 0.025, 2, (-1.30, 0, 1.49)), PAINT, turn)
    a.add(cyl_between((-1.90, -0.45, 0.25), (-2.02, -0.45, 0.25), 0.03, 10), "hr_steel_galv", turn)
    interior(a, turn, 0.62, 0.05, -0.80, 0.80, 0.25)
    a.meta.update(needsCollision=True,
                  collider=[box_collider((1.75, 4.0, 0.75), (0, 0, 0.55)), box_collider((1.40, 2.3, 0.55), (0, 0.4, 1.20))],
                  notes="Generic five-door hatchback, about 4.0 x 1.75 x 1.48 m, black paint, alloy wheels, nose faces -Y. Two-box collider (body and cabin).")
    return a


VAN = {
    "hw": [(-2.475, 0.90), (-2.465, 0.94), (-2.44, 0.96), (1.6, 0.96), (2.05, 0.95), (2.30, 0.91), (2.42, 0.84), (2.465, 0.74), (2.475, 0.66)],
    "zr": [(-2.475, 1.90), (-2.45, 1.93), (-2.40, 1.95), (0.80, 1.95), (1.05, 1.90), (1.45, 1.55), (1.85, 1.16), (2.00, 1.09),
           (2.25, 1.02), (2.40, 0.93), (2.46, 0.84), (2.475, 0.76)],
    "zw": [(-2.475, 1.86), (0.70, 1.86), (0.78, 1.15), (2.475, 1.08)],
    "zs": [(-2.475, 0.80), (0.0, 0.80), (2.475, 0.72)],
    "hr": [(-2.475, 0.80), (-2.40, 0.84), (0.9, 0.84), (1.3, 0.80), (1.9, 0.80), (2.475, 0.60)],
    "zb_ends": [(-2.475, 0.30), (-2.30, 0.27), (-2.20, 0.0), (2.30, 0.0), (2.40, 0.28), (2.475, 0.30)],
    "sill": 0.27,
    "axles": [(-1.55, 0.0), (1.58, 0.0)],
    "arch": 0.375,
    "wheel_r": 0.33,
}


def van_delivery():
    a = Asset("VAN_DELIVERY", "vehicle", 82)
    turn = R("Z", -90)
    PAINT = "hr_prop_van_paint"
    body = Body(VAN)
    mats = [PAINT, GLASS, TRIM]

    def band_mat(x, band, side):
        if band < 0:
            return 0
        if band == 0:
            return 2
        if band == 5 and 0.86 <= x <= 1.80:
            return 1
        if band in (6, 7, 8) and 1.12 <= x <= 1.86:
            return 1 if band >= 7 or (band == 6 and 1.2 < x < 1.8) else 0
        return 0

    st = stations_for(-2.475, 2.475, VAN["axles"], VAN["arch"], (0.70, 0.78, 0.86, 1.80, 1.12, 1.86))
    a.add(body_mesh(body, st, band_mat), mats, turn, sharp=48)
    for (x0, x1, hy) in ((-2.30, -1.95, 0.88), (-1.95, -1.15, 0.62), (-1.15, 1.18, 0.88), (1.18, 1.98, 0.62), (1.98, 2.38, 0.88)):
        a.add(box(x1 - x0, 2 * hy, 0.02, 0.0, 1, ((x0 + x1) / 2, 0, 0.255)), TRIM, turn)
    for (ax, _) in VAN["axles"]:
        for side in (-1, 1):
            arch_liner(a, ax, VAN["arch"] - 0.005, 0.56, 0.95, VAN["wheel_r"], turn, side)
            wheel(a, (ax, side * 0.82, VAN["wheel_r"]), VAN["wheel_r"], 0.215, side, A.VEHICLE["steel_wheel"], turn, False)
    xf, xr = 2.475, -2.475
    a.add(box(0.03, 1.00, 0.20, 0.01, 1, (xf - 0.008, 0, 0.70)), VEH, turn, uv="fit", fit_axis="Y", uv_rect=A.VEHICLE["grille"])
    a.add(box(0.05, 1.70, 0.22, 0.02, 2, (xf - 0.012, 0, 0.40)), TRIM, turn)
    a.add(box(0.012, 0.52, 0.111, 0.003, 1, (xf + 0.016, 0, 0.42)), VEH, turn, uv="fit", fit_axis="Y", uv_rect=A.VEHICLE["plate_front"])
    for side in (-1, 1):
        a.add(patch(body, 2.30, 2.468, 2.4, 3.8, side, 5, 3, 0.004), VEH, turn, uv="rect", uv_rect=A.VEHICLE["headlight"])
        # tall rear lamp stacks on the corners
        a.add(box(0.03, 0.10, 0.48, 0.008, 1, (xr + 0.002, side * 0.88, 1.02)), VEH, turn, uv="fit", fit_axis="Y", uv_rect=A.VEHICLE["van_lamp"])
    a.add(box(0.06, 1.90, 0.20, 0.02, 2, (xr + 0.01, 0, 0.40)), TRIM, turn)
    a.add(box(0.012, 0.52, 0.111, 0.003, 1, (xr - 0.025, 0, 0.62)), VEH, turn, uv="fit", fit_axis="Y", uv_rect=A.VEHICLE["plate_rear"])
    # rear barn door split, handle, step and high brake light
    a.add(box(0.006, 0.008, 1.48, 0.0, 1, (xr - 0.002, 0, 1.18)), TRIM, turn)
    a.add(box(0.03, 0.14, 0.05, 0.01, 1, (xr - 0.01, -0.10, 1.05)), TRIM, turn)
    a.add(box(0.02, 0.30, 0.05, 0.005, 1, (xr - 0.005, 0, 1.92)), "hr_prop_lens_red", turn)
    # sliding door and cab door shut lines, handles, mirrors, roof rails
    for side in (-1, 1):
        for x in (0.70, -0.62, 1.82):
            a.add(patch(body, x - 0.003, x + 0.003, 0.9, 5.3 if x < 0.75 else 4.6, side, 1, 4, 0.0015), TRIM, turn, uv="keep")
        a.add(patch(body, -0.62, 0.70, 5.22, 5.30, side, 6, 1, 0.0015), TRIM, turn, uv="keep")
        a.add(patch(body, -2.30, 1.20, 1.05, 1.45, side, 12, 1, 0.004), TRIM, turn, uv="keep")
        for x in (0.55, 1.05):
            p = body.point(x, 3.4, side)
            nrm = body.normal(x, 3.4, side)
            a.add(soft_box(0.15, 0.035, 0.03, 0.01, 2, (0, 0, 0)), TRIM, turn @ T(*(p + nrm * 0.01)) @ look_matrix(nrm) @ R("X", 90))
        mp = body.point(1.70, 5.0, side) + Vector((0, side * 0.13, 0.05))
        a.add(soft_box(0.10, 0.22, 0.26, 0.04, 2, tuple(mp)), TRIM, turn)
        a.add(box(0.004, 0.18, 0.21, 0.0, 1, tuple(mp + Vector((-0.051, 0, 0)))), GLASS, turn)
        a.add(cyl_between((-2.2, side * 0.70, 1.97), (0.7, side * 0.70, 1.97), 0.015, 8), TRIM, turn)
    a.add(cyl_between((1.0, 0.55, 1.95), (0.70, 0.55, 2.30), 0.006, 6), TRIM, turn)
    interior(a, turn, 1.62, 0.95, 0.0, 0.88, 0.32, rear=False)
    a.add(box(0.04, 1.82, 1.30, 0.004, 1, (0.62, 0, 1.0)), TRIM, turn)
    a.meta.update(needsCollision=True, collider=[box_collider((1.92, 4.95, 1.95), (0, 0, 0.975))],
                  notes="Generic short-wheelbase panel van, about 4.95 x 1.92 x 1.95 m, dark grey, steel wheels, sliding side door and rear barn doors, nose faces -Y.")
    return a


BUILDERS = [car_hatchback, van_delivery]
