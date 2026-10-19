"""Street and estate furniture for the Heron Reach props kit."""

import math

import bmesh
from mathutils import Vector

from heron_props_lib import (
    Asset, R, S, T, look_matrix, box, box_mm, bolt_head, circle_profile, cyl, cyl_between, dome_head,
    fillet_path, lathe, loft, prism, quad, rect_profile, round_profile, rrect, soft_box,
    sphere, sweep, torus, tube, fbm,
)
import heron_props_atlas as A

BLK = "hr_steel_black"
GALV = "hr_steel_galv"
AGED = "hr_steel_aged"
CONC = "hr_concrete_cast"
CONC_R = "hr_concrete_rough"
TIMBER = "hr_timber"
PBLK = "hr_plastic_black"
PGRN = "hr_plastic_green"
YEL = "hr_paint_yellow"
LAMP = "hr_lamp_emit"
GLASS = "hr_glass"
SIGN = "hr_signage"
RUBBER = "hr_prop_tyre"
UPVC = "hr_upvc_white"
VOID = "hr_prop_dark_void"


def box_collider(size, center):
    return {"type": "box", "size": [round(s, 3) for s in size], "center": [round(c, 3) for c in center]}


def cyl_collider(radius, height, center_z=None):
    return {"type": "cylinder", "radius": round(radius, 3), "height": round(height, 3),
            "center": [0.0, 0.0, round(height / 2 if center_z is None else center_z, 3)]}


def bolts_ring(a, mat, positions, z, r=0.009, h=0.007, n=6):
    for (x, y) in positions:
        a.add(bolt_head(r, h, n), mat, T(x, y, z))


# ---------------------------------------------------------------------------


def lamp_column():
    a = Asset("LAMP_COLUMN", "street", 11)
    a.add(box(0.34, 0.34, 0.025, 0.005, 1, (0, 0, 0.0125)), BLK)
    for (x, y) in ((0.13, 0.13), (-0.13, 0.13), (0.13, -0.13), (-0.13, -0.13)):
        a.add(cyl(0.022, 0.004, 12, 0.0), BLK, T(x, y, 0.025))
        a.add(bolt_head(0.014, 0.012), BLK, T(x, y, 0.029))
        a.add(cyl(0.007, 0.02, 6, 0.0), BLK, T(x, y, 0.035))
    # base shroud with door
    prof = [(0.112, 0.025), (0.112, 0.055), (0.104, 0.065), (0.104, 1.08), (0.100, 1.10),
            (0.082, 1.13), (0.074, 1.17), (0.074, 1.22)]
    a.add(lathe(prof, 24, True, True), BLK, uv="box")
    a.add(box(0.075, 0.012, 0.52, 0.003, 1, (0, -0.102, 0.58)), BLK)
    for z in (0.36, 0.80):
        a.add(dome_head(0.006, 0.004), BLK, T(0, -0.108, z) @ R("X", 90))
    # collars and shaft
    a.add(lathe([(0.082, 1.20), (0.086, 1.215), (0.086, 1.25), (0.075, 1.27)], 24, True, True), BLK)
    a.add(lathe([(0.066, 1.25), (0.060, 2.60), (0.055, 3.90), (0.050, 4.32)], 16, False, False), BLK)
    a.add(lathe([(0.070, 2.56), (0.073, 2.58), (0.073, 2.63), (0.068, 2.65)], 16, True, True), BLK)
    a.add(lathe([(0.058, 4.26), (0.064, 4.28), (0.064, 4.34), (0.050, 4.37), (0.040, 4.40),
                 (0.040, 4.44), (0.062, 4.47), (0.105, 4.50), (0.105, 4.53)], 16, True, True), BLK)
    # lantern: tapered square frame wider at the top
    zb, zt = 4.53, 4.84
    hb, ht = 0.13, 0.20
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.add(cyl_between((sx * hb, sy * hb, zb), (sx * ht, sy * ht, zt), 0.011, 6), BLK)
    a.add(sweep([(hb, hb, zb), (-hb, hb, zb), (-hb, -hb, zb), (hb, -hb, zb)], rect_profile(0.03, 0.02), closed=True), BLK)
    a.add(sweep([(ht, ht, zt), (-ht, ht, zt), (-ht, -ht, zt), (ht, -ht, zt)], rect_profile(0.03, 0.025), closed=True), BLK)
    # four lenses, inset slightly from the posts, and a base lens
    ins = 0.012
    for k in range(4):
        rot = R("Z", 90 * k)
        p0 = Vector((-hb + ins, -hb + 0.004, zb + 0.012))
        p1 = Vector((hb - ins, -hb + 0.004, zb + 0.012))
        p2 = Vector((ht - ins, -ht + 0.004, zt - 0.012))
        p3 = Vector((-ht + ins, -ht + 0.004, zt - 0.012))
        a.add(quad(p0, p1, p2, p3), LAMP, rot, uv="keep")
        a.add(quad(p0, p3, p2, p1), LAMP, rot, uv="keep")  # inner face so the lens reads from inside too
    a.add(quad((-hb, hb, zb + 0.002), (hb, hb, zb + 0.002), (hb, -hb, zb + 0.002), (-hb, -hb, zb + 0.002)), LAMP, uv="keep")
    # inner lamp holder
    a.add(cyl(0.025, 0.12, 10, zb), GALV)
    # canopy roof with overhang, then pyramid and finial
    a.add(box(0.50, 0.50, 0.014, 0.004, 1, (0, 0, zt + 0.012)), BLK)
    roof = loft([rrect(0.48, 0.48, 0.01, 1, zt + 0.019), rrect(0.16, 0.16, 0.01, 1, 4.94)], True, True)
    a.add(roof, BLK)
    a.add(lathe([(0.045, 4.94), (0.045, 4.955), (0.032, 4.965), (0.026, 4.975), (0.034, 4.985), (0.024, 4.997), (0.0, 5.0)], 12, True, False), BLK)
    a.meta.update(needsCollision=True, collider=cyl_collider(0.12, 5.0), lightAnchor=[0.0, 0.0, 4.68],
                  notes="5 m estate column, lantern head with four emissive lenses and a base lens.")
    return a


def wall_lamp():
    a = Asset("WALL_LAMP", "street", 12)
    # wall plate and arm (wall face is y = 0, lamp projects to -y)
    a.add(box(0.13, 0.012, 0.17, 0.003, 1, (0, -0.006, 0)), BLK)
    for (x, z) in ((-0.045, 0.06), (0.045, 0.06), (-0.045, -0.06), (0.045, -0.06)):
        a.add(dome_head(0.006, 0.003), BLK, T(x, -0.012, z) @ R("X", 90))
    a.add(box(0.05, 0.035, 0.05, 0.004, 1, (0, -0.0295, 0)), BLK)
    # body: back box
    yb0, yb1 = -0.047, -0.075
    a.add(box_mm(-0.115, 0.115, yb1, yb0, -0.175, 0.175, 0.004), BLK)
    # glass block
    a.add(box_mm(-0.098, 0.098, -0.150, yb1 + 0.002, -0.155, 0.155, 0.002), LAMP)
    # frame: top and bottom caps, corner posts
    a.add(box_mm(-0.115, 0.115, -0.160, yb1, 0.150, 0.175, 0.004), BLK)
    a.add(box_mm(-0.115, 0.115, -0.160, yb1, -0.175, -0.150, 0.004), BLK)
    for x in (-0.106, 0.106):
        a.add(box_mm(x - 0.009, x + 0.009, -0.160, -0.142, -0.152, 0.152, 0.002), BLK)
        a.add(box_mm(x - 0.009, x + 0.009, yb1 - 0.018, yb1, -0.152, 0.152, 0.002), BLK)
    # front frame rails just inside the posts
    for z in (0.143, -0.143):
        a.add(box_mm(-0.098, 0.098, -0.160, -0.148, z - 0.008, z + 0.008, 0.002), BLK)
    # guard bars wrapping round the front and sides
    for z in (-0.055, 0.055):
        path = fillet_path([(0.116, yb1, z), (0.116, -0.170, z), (-0.116, -0.170, z), (-0.116, yb1, z)], 0.015, 3)
        a.add(tube(path, 0.0055, 8), BLK)
    for (x, z) in ((-0.106, 0.163), (0.106, 0.163), (-0.106, -0.163), (0.106, -0.163)):
        a.add(dome_head(0.005, 0.003), BLK, T(x, -0.160, z) @ R("X", 90))
    a.meta.update(needsCollision=False, collider=None, mount="wall", lightAnchor=[0.0, -0.11, 0.0],
                  notes="Caged bulkhead. Origin on the wall face at the fixing plate centre; projects 0.17 m.")
    return a


def bollard():
    a = Asset("BOLLARD", "street", 13)
    a.add(lathe([(0.150, 0.0), (0.150, 0.016), (0.140, 0.022), (0.106, 0.024)], 24, True, False), BLK)
    for k in range(6):
        ang = math.tau * k / 6 + 0.2
        a.add(bolt_head(0.011, 0.010), BLK, T(0.128 * math.cos(ang), 0.128 * math.sin(ang), 0.022))
    a.add(lathe([(0.102, 0.020), (0.100, 0.03), (0.100, 0.845), (0.097, 0.852), (0.097, 0.858),
                 (0.101, 0.864), (0.101, 0.88), (0.096, 0.93), (0.080, 0.968), (0.055, 0.990),
                 (0.025, 0.999), (0.0, 1.0)], 28, False, False), BLK)
    a.add(lathe([(0.1012, 0.72), (0.1018, 0.722), (0.1018, 0.798), (0.1012, 0.80)], 28, False, False), YEL, uv="box")
    # seam line
    a.add(box(0.004, 0.003, 0.80, 0.0, 1, (0, -0.1005, 0.43)), BLK)
    a.meta.update(needsCollision=True, collider=cyl_collider(0.10, 1.0), notes="1.0 m black steel bollard, yellow reflective band.")
    return a


def litter_bin():
    a = Asset("LITTER_BIN", "street", 14)
    n = 36
    R0 = 0.255
    z_ap0, z_ap1 = 0.64, 0.80
    prof = [(R0 - 0.01, 0.0), (R0, 0.012), (R0, 0.13), (R0 + 0.012, 0.135), (R0 + 0.012, 0.16), (R0, 0.165),
            (R0, 0.575), (R0 + 0.012, 0.58), (R0 + 0.012, 0.605), (R0, 0.61), (R0, z_ap0), (R0, z_ap1),
            (R0, 0.855), (R0 + 0.012, 0.86), (R0 + 0.015, 0.875), (R0 + 0.012, 0.892), (R0 - 0.01, 0.90),
            (0.22, 0.945), (0.15, 0.978), (0.07, 0.995), (0.0, 1.0)]
    body = lathe(prof, n, True, False, phase=0.0)
    # aperture faces: angle centred on -90 (front) and +90 (back), 70 degrees wide
    kill = []
    for f in body.faces:
        c = f.calc_center_median()
        if z_ap0 + 0.005 < c.z < z_ap1 - 0.005:
            ang = math.degrees(math.atan2(c.y, c.x))
            if abs(ang + 90) < 34 or abs(ang - 90) < 34:
                kill.append(f)
    bmesh.ops.delete(body, geom=kill, context="FACES_ONLY")
    edges = [e for e in body.edges if len(e.link_faces) == 1]
    res = bmesh.ops.extrude_edge_only(body, edges=edges)
    for v in [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]:
        d = Vector((v.co.x, v.co.y, 0)).normalized()
        v.co -= d * 0.03
    bmesh.ops.recalc_face_normals(body, faces=body.faces)
    a.add(body, BLK)
    # liner (dark) visible through the apertures, faces pointing inward
    liner = lathe([(0.222, 0.30), (0.222, 0.86)], n, False, False)
    a.add(liner, PBLK, flip=True)
    a.add(cyl(0.222, 0.01, n, 0.40), VOID)
    for x in (-0.12, 0.12):
        a.add(dome_head(0.008, 0.005), BLK, T(x, -math.sqrt(R0 * R0 - x * x) - 0.001, 0.07) @ R("X", 90))
    a.meta.update(needsCollision=True, collider=cyl_collider(0.27, 1.0), notes="Cylindrical steel litter bin with domed lid and two apertures.")
    return a


def _wheel(a, radius, width, center, axis="X", tyre=RUBBER, hub=PBLK, spokes=6):
    rot = R("Y", 90) if axis == "X" else R("X", 90)
    tyre_prof = [(radius * 0.62, -width / 2), (radius * 0.92, -width / 2), (radius, -width * 0.32),
                 (radius, width * 0.32), (radius * 0.92, width / 2), (radius * 0.62, width / 2)]
    a.add(lathe(tyre_prof, 20, False, False), tyre, T(*center) @ rot)
    a.add(lathe([(radius * 0.63, -width * 0.42), (radius * 0.63, width * 0.42)], 20, False, False), hub, T(*center) @ rot, flip=True)
    a.add(cyl(radius * 0.22, width * 0.9, 12, -width * 0.45), hub, T(*center) @ rot)
    for k in range(spokes):
        ang = 360.0 * k / spokes
        a.add(box(radius * 0.42, width * 0.12, radius * 0.06, 0.0, 1, (radius * 0.42, 0, 0)), hub,
              T(*center) @ rot @ R("Z", ang))


def wheelie_bin(name="WHEELIE_BIN_240", body_mat=PBLK, lid_mat=PBLK):
    a = Asset(name, "street", 15)
    rings = []
    for (z, w, d) in ((0.04, 0.48, 0.56), (0.08, 0.50, 0.59), (0.92, 0.575, 0.705), (0.94, 0.578, 0.71)):
        rings.append(rrect(w, d, 0.05, 3, z, 0, 0.0))
    a.add(loft(rings, True, True), body_mat)
    # top rim lip
    a.add(loft([rrect(0.60, 0.735, 0.05, 3, 0.94), rrect(0.615, 0.75, 0.05, 3, 0.955), rrect(0.615, 0.75, 0.05, 3, 0.985), rrect(0.59, 0.73, 0.05, 3, 0.99)], True, True), body_mat)
    # lid with raised panel and front handles
    a.add(soft_box(0.625, 0.76, 0.035, 0.012, 2, (0, 0.0, 1.005)), lid_mat)
    a.add(soft_box(0.50, 0.58, 0.03, 0.012, 2, (0, 0.03, 1.03)), lid_mat)
    for x in (-0.24, 0.24):
        a.add(sweep([(x, -0.36, 1.02), (x, -0.36, 1.065), (x, -0.30, 1.065), (x, -0.30, 1.02)], rect_profile(0.025, 0.012), up=(1, 0, 0)), lid_mat)
    # hinge barrel and handle bar at the back
    a.add(cyl_between((-0.27, 0.392, 0.985), (0.27, 0.392, 0.985), 0.018, 10), lid_mat)
    a.add(cyl_between((-0.25, 0.425, 0.93), (0.25, 0.425, 0.93), 0.016, 10), body_mat)
    for x in (-0.23, 0.23):
        a.add(box(0.03, 0.07, 0.05, 0.006, 1, (x, 0.39, 0.93)), body_mat)
    # front ribs under the rim
    for x in (-0.20, -0.07, 0.07, 0.20):
        a.add(box(0.012, 0.02, 0.10, 0.003, 1, (x, -0.355, 0.88)), body_mat)
    # back recess channel and axle housing, front feet
    a.add(box(0.30, 0.02, 0.70, 0.005, 1, (0, 0.322, 0.50)), body_mat)
    a.add(box(0.52, 0.12, 0.12, 0.02, 2, (0, 0.27, 0.10)), body_mat)
    for x in (-0.18, 0.18):
        a.add(box(0.07, 0.07, 0.05, 0.01, 1, (x, -0.22, 0.025)), body_mat)
    a.add(cyl_between((-0.31, 0.30, 0.10), (0.31, 0.30, 0.10), 0.010, 8), GALV)
    for x in (-0.288, 0.288):
        _wheel(a, 0.10, 0.045, (x, 0.30, 0.10), "X")
    a.meta.update(needsCollision=True, collider=box_collider((0.62, 0.76, 1.07), (0, 0.0, 0.535)),
                  notes="240 litre two-wheel bin, lid hinged at the back (+Y), wheels at the back.")
    return a


def euro_bin():
    a = Asset("EURO_BIN_1100", "street", 16)
    z0, z1 = 0.26, 1.24
    rings = [rrect(1.10, 0.86, 0.10, 3, z0), rrect(1.13, 0.90, 0.10, 3, z0 + 0.04), rrect(1.24, 0.98, 0.10, 3, z1)]
    a.add(loft(rings, True, True), GALV)
    # rolled rim
    rim = [Vector(p) for p in rrect(1.27, 1.01, 0.11, 4, z1 + 0.005)]
    a.add(tube(rim, 0.02, 8, closed=True), GALV)
    # vertical stiffening ribs on the front and sides
    for x in (-0.38, 0.0, 0.38):
        a.add(box(0.05, 0.02, 0.85, 0.006, 1, (x, -0.462, 0.78)), GALV, None)
    # lid: flat galvanised with front lip and handle
    a.add(box(1.30, 1.04, 0.03, 0.008, 1, (0, 0.0, z1 + 0.04)), GALV)
    a.add(box(1.30, 0.03, 0.07, 0.006, 1, (0, -0.52, z1 + 0.02)), GALV)
    a.add(tube([(-0.25, -0.53, z1 + 0.02), (-0.25, -0.58, z1 + 0.02), (0.25, -0.58, z1 + 0.02), (0.25, -0.53, z1 + 0.02)], 0.012, 8), GALV)
    for x in (-0.5, 0.5):
        a.add(cyl_between((x - 0.06, 0.52, z1 + 0.03), (x + 0.06, 0.52, z1 + 0.03), 0.02, 10), GALV)
    # comb bar on the front and trunnions on the sides
    a.add(box(1.0, 0.07, 0.08, 0.01, 1, (0, -0.505, 1.08)), GALV)
    for x in (-0.64, 0.64):
        a.add(cyl_between((x * 0.94, 0, 1.0), (x * 1.06, 0, 1.0), 0.04, 12), GALV)
        a.add(cyl_between((x * 1.06, 0, 1.0), (x * 1.08, 0, 1.0), 0.06, 12), GALV)
    # side push handles
    for sx in (-1, 1):
        x0, x1 = sx * 0.60, sx * 0.70
        a.add(tube(fillet_path([(x0, -0.3, 1.05), (x1, -0.3, 1.05), (x1, 0.3, 1.05), (x0, 0.3, 1.05)], 0.05), 0.016, 8), GALV)
    # chassis and castors
    a.add(box(1.04, 0.80, 0.05, 0.008, 1, (0, 0, 0.235)), GALV)
    for (x, y) in ((-0.44, -0.32), (0.44, -0.32), (-0.44, 0.32), (0.44, 0.32)):
        a.add(box(0.10, 0.10, 0.012, 0.002, 1, (x, y, 0.205)), GALV)
        a.add(cyl(0.025, 0.02, 10, 0.18), GALV, T(x, y, 0))
        a.add(box(0.012, 0.07, 0.10, 0.002, 1, (x - 0.032, y + 0.02, 0.14)), GALV)
        a.add(box(0.012, 0.07, 0.10, 0.002, 1, (x + 0.032, y + 0.02, 0.14)), GALV)
        _wheel(a, 0.10, 0.05, (x, y + 0.03, 0.10), "X", RUBBER, PBLK, 0)
    a.add(cyl(0.03, 0.03, 10, 0.21), PBLK, T(0.40, -0.40, 0))
    a.meta.update(needsCollision=True, collider=box_collider((1.42, 1.10, 1.30), (0, -0.02, 0.65)),
                  notes="Galvanised 1100 litre communal bin on four castors, flat lid, comb bar on the front.")
    return a


def bench():
    a = Asset("BENCH", "street", 17)
    L = 1.80
    prof = rect_profile(0.05, 0.016, 0.003)
    for x in (-0.80, 0.0, 0.80):
        up = (1, 0, 0)
        if x != 0.0:
            # front leg and armrest bending back to the back post
            path = fillet_path([(x, -0.26, 0.0), (x, -0.26, 0.66), (x, 0.17, 0.66)], 0.07, 4)
            a.add(sweep(path, prof, up=up), BLK)
        # back post, reclined
        path = fillet_path([(x, 0.20, 0.0), (x, 0.20, 0.40), (x, 0.31, 0.88)], 0.05, 3)
        a.add(sweep(path, prof, up=up), BLK)
        # seat rail
        a.add(sweep([(x, -0.30, 0.405), (x, 0.24, 0.405)], prof, up=up), BLK)
        # foot plates
        for y in ((-0.26, 0.20) if x != 0.0 else (0.20,)):
            a.add(box(0.10, 0.12, 0.010, 0.002, 1, (x, y, 0.005)), BLK)
            for (bx, by) in ((-0.035, -0.04), (0.035, -0.04), (-0.035, 0.04), (0.035, 0.04)):
                a.add(bolt_head(0.007, 0.006), BLK, T(x + bx, y + by, 0.010))
        if x == 0.0:
            a.add(sweep([(x, -0.25, 0.42), (x, -0.25, 0.39), (x, 0.0, 0.25), (x, 0.20, 0.25)], prof, up=up), BLK)
    # seat slats
    for y in (-0.255, -0.14, -0.025, 0.09):
        a.add(box(L, 0.10, 0.040, 0.009, 2, (0, y, 0.435)), TIMBER)
        for x in (-0.80, 0.0, 0.80):
            a.add(dome_head(0.008, 0.004), BLK, T(x, y, 0.455))
    # back slats on the reclined plane
    ang = math.degrees(math.atan2(0.11, 0.48))
    for k, z in enumerate((0.53, 0.65, 0.77)):
        y = 0.20 + (z - 0.40) * (0.11 / 0.48) - 0.033
        a.add(box(L, 0.035, 0.10, 0.009, 2), TIMBER, T(0, y, z) @ R("X", -ang))
        for x in (-0.80, 0.0, 0.80):
            a.add(dome_head(0.008, 0.004), BLK, T(x, y - 0.018, z) @ R("X", -ang) @ R("X", 90))
    a.meta.update(needsCollision=True, collider=box_collider((1.82, 0.62, 0.88), (0, -0.02, 0.44)),
                  notes="Estate bench: black flat-bar end frames, four seat slats and three back slats in timber.")
    return a


def cycle_hoop():
    a = Asset("CYCLE_HOOP", "street", 18)
    path = fillet_path([(-0.35, 0, -0.06), (-0.35, 0, 0.76), (0.35, 0, 0.76), (0.35, 0, -0.06)], 0.16, 7)
    a.add(tube(path, 0.024, 12, up=(0, 1, 0)), BLK)
    for x in (-0.35, 0.35):
        a.add(lathe([(0.045, -0.01), (0.045, 0.004), (0.026, 0.012)], 14, False, True), BLK, T(x, 0, 0))
    a.meta.update(needsCollision=True, collider=box_collider((0.75, 0.06, 0.80), (0, 0, 0.40)),
                  notes="Sheffield stand, 48 mm tube, set into the ground.")
    return a


def bike():
    """Parked bicycle. Built nose toward +X then turned so the nose faces -Y."""
    a = Asset("BIKE", "street", 19)
    turn = R("Z", -90)
    PAINT = "hr_prop_bike_paint"
    rw = 0.335
    RA = Vector((-0.51, 0, rw))
    FA = Vector((0.51, 0, rw))
    BB = Vector((-0.08, 0, 0.27))
    ST = Vector((-0.22, 0, 0.80))
    HT = Vector((0.35, 0, 0.79))
    HB = Vector((0.39, 0, 0.64))

    def tb(p0, p1, r, mat=PAINT, n=8):
        a.add(cyl_between(p0, p1, r, n), mat, turn)

    # wheels: tyre, rim, hub, spokes
    for C in (RA, FA):
        a.add(torus(rw - 0.018, 0.018, 32, 6), RUBBER, turn @ T(*C) @ R("X", 90))
        a.add(torus(rw - 0.040, 0.010, 32, 4), GALV, turn @ T(*C) @ R("X", 90))
        a.add(cyl(0.022, 0.10, 10, -0.05), GALV, turn @ T(*C) @ R("X", 90))
        for k in range(16):
            ang = math.tau * k / 16
            side = 0.03 if k % 2 else -0.03
            p0 = C + Vector((0.020 * math.cos(ang), side, 0.020 * math.sin(ang)))
            p1 = C + Vector(((rw - 0.045) * math.cos(ang + 0.1), 0, (rw - 0.045) * math.sin(ang + 0.1)))
            a.add(cyl_between(p0, p1, 0.0012, 3, caps=False), GALV, turn)
    # frame
    tb(BB, ST, 0.015)
    tb(ST + Vector((0.01, 0, -0.03)), HT + Vector((-0.01, 0, -0.03)), 0.016)
    tb(BB, HB, 0.019)
    tb(HB + Vector((-0.004, 0, -0.03)), HT + Vector((0.0, 0, 0.03)), 0.020)
    for s in (-1, 1):
        tb(BB, RA + Vector((0, s * 0.06, 0)), 0.009)
        tb(ST + Vector((0, 0, -0.02)), RA + Vector((0, s * 0.06, 0)), 0.008)
        # fork blades with a slight rake
        fork = [HB + Vector((0, s * 0.045, -0.02)), HB + Vector((0.06, s * 0.05, -0.18)), FA + Vector((0, s * 0.05, 0))]
        a.add(tube(fork, 0.011, 8, up=(0, 1, 0)), PAINT, turn)
    tb(HB + Vector((0, 0, -0.02)), HB + Vector((0, 0, -0.05)), 0.024)
    # seatpost and saddle
    tb(ST, ST + Vector((-0.03, 0, 0.14)), 0.0135, GALV)
    sad = loft([[Vector((x, y, 0.955)) for (x, y) in pts] for pts in (
        [(-0.10, -0.075), (0.02, -0.06), (0.15, -0.02), (0.15, 0.02), (0.02, 0.06), (-0.10, 0.075), (-0.13, 0.0)],)] +
        [[Vector((x, y, 0.985)) for (x, y) in [(-0.10, -0.07), (0.02, -0.055), (0.15, -0.018), (0.15, 0.018), (0.02, 0.055), (-0.10, 0.07), (-0.125, 0.0)]]],
        True, True)
    a.add(sad, PBLK, turn @ T(-0.25, 0, 0))
    # stem, bars and grips
    top = HT + Vector((-0.01, 0, 0.12))
    tb(HT, top, 0.013, GALV)
    tb(top, top + Vector((0.07, 0, 0.0)), 0.013, GALV)
    bar = top + Vector((0.07, 0, 0))
    a.add(tube([bar + Vector((-0.04, -0.29, 0.01)), bar + Vector((0, -0.18, 0)), bar + Vector((0, 0.18, 0)), bar + Vector((-0.04, 0.29, 0.01))], 0.011, 8, up=(1, 0, 0)), GALV, turn)
    for s in (-1, 1):
        a.add(cyl_between(bar + Vector((-0.02, s * 0.20, 0.005)), bar + Vector((-0.045, s * 0.30, 0.01)), 0.016, 8), PBLK, turn)
        a.add(cyl_between(bar + Vector((0.01, s * 0.19, 0.0)), bar + Vector((0.07, s * 0.25, -0.03)), 0.005, 4), BLK, turn)
    # drivetrain on the right (-Y in the build frame)
    a.add(cyl(0.10, 0.004, 24, -0.002), BLK, turn @ T(*(BB + Vector((0, -0.065, 0)))) @ R("X", 90))
    a.add(cyl(0.04, 0.004, 14, -0.002), BLK, turn @ T(*(RA + Vector((0, -0.065, 0)))) @ R("X", 90))
    chain = []
    for k in range(10):
        ang = math.pi / 2 - math.pi * k / 9
        chain.append(BB + Vector((0.10 * math.cos(ang), -0.065, 0.10 * math.sin(ang))))
    for k in range(10):
        ang = -math.pi / 2 - math.pi * k / 9
        chain.append(RA + Vector((0.04 * math.cos(ang), -0.065, 0.04 * math.sin(ang))))
    a.add(tube(chain, 0.003, 4, closed=True, up=(0, 1, 0)), BLK, turn)
    for s, ang in ((-1, 35), (1, 215)):
        end = BB + Vector((0.165 * math.cos(math.radians(ang)), s * 0.08, 0.165 * math.sin(math.radians(ang))))
        a.add(cyl_between(BB + Vector((0, s * 0.07, 0)), end, 0.009, 6), GALV, turn)
        a.add(box(0.09, 0.07, 0.022, 0.004, 1, tuple(end + Vector((0, s * 0.045, 0)))), PBLK, turn)
    a.meta.update(needsCollision=False, collider=box_collider((0.6, 1.72, 1.0), (0, 0, 0.5)),
                  notes="Parked bicycle, nose toward -Y. Stand it beside CYCLE_HOOP. Collision optional (thin).")
    return a


def cctv():
    a = Asset("CCTV", "street", 20)
    P = "hr_prop_cctv"
    a.add(box(0.12, 0.012, 0.18, 0.004, 1, (0, -0.006, 0)), P, uv_scale=4.0)
    for (x, z) in ((-0.042, 0.068), (0.042, 0.068), (-0.042, -0.068), (0.042, -0.068)):
        a.add(bolt_head(0.008, 0.006), BLK, T(x, -0.012, z) @ R("X", 90))
    arm = prism([(-0.035, -0.04), (0.035, -0.04), (0.025, 0.02), (-0.025, 0.02)], 0.30, 0.004, 1, y0=-0.30)
    a.add(arm, P, T(0, -0.012, -0.02), uv_scale=4.0)
    a.add(cyl(0.028, 0.06, 14, -0.03), P, T(0, -0.30, 0.0), uv_scale=4.0)
    a.add(cyl(0.012, 0.075, 10, -0.0375), BLK, T(0, -0.30, 0.04) @ R("Y", 90))
    a.add(box(0.05, 0.05, 0.045, 0.006, 1, (0, -0.30, 0.05)), P, uv_scale=4.0)
    # housing, pitched down 14 degrees, pointing out from the wall
    hous = T(0, -0.30, 0.13) @ R("X", 14)
    a.add(box(0.13, 0.40, 0.12, 0.012, 2, (0, -0.10, 0)), P, hous, uv_scale=4.0)
    # sun hood: top sheet and two side skirts, overhanging the front
    a.add(box(0.16, 0.46, 0.008, 0.003, 1, (0, -0.13, 0.068)), P, hous, uv_scale=4.0)
    for x in (-0.077, 0.077):
        a.add(box(0.006, 0.46, 0.05, 0.002, 1, (x, -0.13, 0.045)), P, hous, uv_scale=4.0)
    # front bezel, glass and lens
    a.add(box(0.110, 0.012, 0.100, 0.006, 1, (0, -0.305, -0.002)), PBLK, hous)
    a.add(box(0.096, 0.004, 0.086, 0.0, 1, (0, -0.312, -0.002)), GLASS, hous)
    a.add(cyl(0.028, 0.02, 16, 0.0), PBLK, hous @ T(0, -0.300, -0.002) @ R("X", 90))
    a.add(cyl(0.016, 0.004, 16, 0.0), GLASS, hous @ T(0, -0.309, -0.002) @ R("X", 90))
    for (x, z) in ((-0.045, 0.040), (0.045, 0.040), (-0.045, -0.044), (0.045, -0.044)):
        a.add(dome_head(0.004, 0.002), BLK, hous @ T(x, -0.311, z) @ R("X", 90))
    a.add(box(0.10, 0.008, 0.09, 0.004, 1, (0, 0.104, 0)), P, hous, uv_scale=4.0)
    a.add(cyl_between((0, 0.10, -0.03), (0, 0.02, -0.12), 0.007, 6), PBLK, T(0, -0.30, 0.13))
    a.meta.update(needsCollision=False, collider=None, mount="wall",
                  notes="Wall-mounted camera with sun hood. Origin on the wall face at the plate centre.")
    return a


def intercom():
    a = Asset("INTERCOM", "street", 21)
    P = "hr_prop_intercom"
    a.add(box(0.20, 0.050, 0.38, 0.006, 1, (0, -0.025, 0)), BLK)
    a.add(box(0.18, 0.006, 0.36, 0.003, 1, (0, -0.053, 0)), P, uv="rect", uv_rect=A.INTERCOM["metal"])
    # front face of the plate mapped to the faceplate art
    a.add(quad((-0.087, -0.0565, -0.177), (0.087, -0.0565, -0.177), (0.087, -0.0565, 0.177), (-0.087, -0.0565, 0.177)),
          P, uv="rect", uv_rect=A.INTERCOM["plate"])
    keys = A.INTERCOM["keys"]
    for r in range(4):
        for c in range(3):
            x = -0.040 + c * 0.040
            z = 0.002 - r * 0.031
            a.add(box(0.030, 0.007, 0.025, 0.002, 1, (x, -0.060, z)), P, uv="rect", uv_rect=A.INTERCOM["metal"])
            a.add(quad((x - 0.0135, -0.0637, z - 0.011), (x + 0.0135, -0.0637, z - 0.011), (x + 0.0135, -0.0637, z + 0.011), (x - 0.0135, -0.0637, z + 0.011)),
                  P, uv="rect", uv_rect=keys[r * 3 + c])
    a.add(lathe([(0.021, 0.0), (0.021, 0.004), (0.016, 0.007), (0.014, 0.007)], 20, False, False), "hr_prop_stainless", T(0, -0.0565, -0.130) @ R("X", 90))
    a.add(lathe([(0.0145, 0.0), (0.0145, 0.004), (0.010, 0.0065), (0.0, 0.007)], 20, False, False), "hr_prop_stainless", T(0, -0.0565, -0.130) @ R("X", 90))
    a.add(lathe([(0.0165, 0.004), (0.0165, 0.0055)], 20, False, False), "hr_lamp_emit", T(0, -0.0565, -0.130) @ R("X", 90))
    # name label above
    a.add(box(0.12, 0.006, 0.045, 0.002, 1, (0, -0.003, 0.225)), "hr_prop_stainless")
    a.add(quad((-0.056, -0.0062, 0.205), (0.056, -0.0062, 0.205), (0.056, -0.0062, 0.245), (-0.056, -0.0062, 0.245)),
          P, uv="rect", uv_rect=A.INTERCOM["label"])
    a.meta.update(needsCollision=False, collider=None, mount="wall",
                  notes="Surface entry panel with keypad and call button. Origin on the wall face at the panel centre; mount the centre at about 1.35 m.")
    return a


def utility_cabinet():
    a = Asset("UTILITY_CABINET", "street", 22)
    a.add(box(1.12, 0.46, 0.20, 0.02, 2, (0, 0, 0.10)), CONC_R)
    a.add(box(1.00, 0.38, 1.06, 0.008, 1, (0, 0, 0.73)), PGRN)
    a.add(box(1.05, 0.43, 0.045, 0.010, 2, (0, 0, 1.283)), PGRN)
    # doors slightly proud with a gap between
    for sx in (-1, 1):
        cx = sx * 0.2425
        a.add(box(0.475, 0.012, 0.98, 0.004, 1, (cx, -0.196, 0.73)), PGRN)
        for zc in (0.37, 1.07):
            for k in range(3):
                z = zc + (k - 1) * 0.032
                a.add(box(0.15, 0.006, 0.012, 0.0, 1, (cx, -0.2005, z)), VOID)
                a.add(box(0.16, 0.012, 0.010, 0.003, 1, (cx, -0.206, z + 0.011)), PGRN)
        hx = sx * 0.488
        for z in (0.36, 1.10):
            a.add(cyl(0.010, 0.09, 10, -0.045), PGRN, T(hx, -0.205, z))
    a.add(box(0.045, 0.014, 0.11, 0.006, 1, (0.035, -0.208, 0.80)), PBLK)
    a.add(cyl(0.008, 0.006, 10, 0.0), "hr_prop_stainless", T(0.035, -0.215, 0.79) @ R("X", 90))
    for k in range(3):
        for sx in (-1, 1):
            a.add(box(0.15, 0.006, 0.012, 0.0, 1, (sx * 0.24, 0.1925, 1.05 + (k - 1) * 0.032)), VOID)
    a.meta.update(needsCollision=True, collider=box_collider((1.12, 0.46, 1.31), (0, 0, 0.655)),
                  notes="Green street services cabinet on a concrete plinth, two doors with louvres.")
    return a


def planter_edge():
    a = Asset("PLANTER_EDGE", "street", 23)
    poly = [(-0.075, 0.0), (0.075, 0.0), (0.075, 0.43), (0.06, 0.45), (-0.06, 0.45), (-0.075, 0.43)]
    seg = prism(poly, 0.998, 0.004, 1)
    a.add(seg, CONC, R("Z", 90))
    a.meta.update(needsCollision=True, collider=box_collider((1.0, 0.15, 0.45), (0, 0, 0.225)),
                  notes="Precast concrete planter kerb, 1 m segment, 150 mm thick, 450 mm high, chamfered top. Tiles along X.")
    return a


def kerb():
    a = Asset("KERB_1M", "street", 24)
    poly = [(-0.0625, -0.10), (0.0625, -0.10), (0.0625, 0.125), (-0.0125, 0.125), (-0.0625, 0.075)]
    a.add(prism(poly, 0.998, 0.004, 1), CONC, R("Z", 90))
    a.meta.update(needsCollision=False, collider=None,
                  notes="Half-battered kerb, 125 mm upstand. Road face is -Y; top is at pavement level 0.125. Buried 0.10 below road level. Tiles along X. Collision belongs to the ground mesh.")
    return a


def drain_gully():
    a = Asset("DRAIN_GULLY", "street", 25)
    W, D = 0.50, 0.40
    t = 0.035
    for (x0, x1, y0, y1) in ((-W / 2, W / 2, -D / 2, -D / 2 + t), (-W / 2, W / 2, D / 2 - t, D / 2),
                             (-W / 2, -W / 2 + t, -D / 2, D / 2), (W / 2 - t, W / 2, -D / 2, D / 2)):
        a.add(box_mm(x0, x1, y0, y1, -0.04, 0.004, 0.003), AGED)
    nb = 10
    span = W - 2 * t
    for k in range(nb + 1):
        x = -span / 2 + span * k / nb
        a.add(box_mm(x - 0.009, x + 0.009, -D / 2 + t, D / 2 - t, -0.035, 0.002, 0.002), AGED)
    a.add(box_mm(-0.20, 0.20, -0.01, 0.01, -0.035, 0.0015, 0.002), AGED)
    pit = box_mm(-W / 2 + t, W / 2 - t, -D / 2 + t, D / 2 - t, -0.30, -0.02)
    a.add(pit, VOID, flip=True)
    a.meta.update(needsCollision=False, collider=None, notes="Kerbside gully grating, flush with the road. Long side along X.")
    return a


def manhole():
    a = Asset("MANHOLE", "street", 26)
    a.add(box(0.74, 0.74, 0.03, 0.006, 1, (0, 0, -0.012)), "hr_prop_manhole", uv="fit", fit_axis="Z", uv_rect=A.MANHOLE["cover"])
    a.meta.update(needsCollision=False, collider=None, notes="Cast iron cover in a square frame, 0.74 m, sits 3 mm proud of the paving.")
    return a


def sign_post():
    a = Asset("SIGN_POST", "street", 27)
    a.add(lathe([(0.05, -0.05), (0.05, 0.01), (0.04, 0.02)], 14, False, True), CONC)
    a.add(cyl(0.038, 2.90, 14, -0.05), GALV)
    a.add(lathe([(0.040, 2.85), (0.040, 2.88), (0.025, 2.90), (0.0, 2.905)], 14, False, False), PBLK)
    # galvanised blade with folded edges and a printed estate sign face
    a.add(box(0.60, 0.004, 0.45, 0.002, 1, (0, -0.065, 2.43)), GALV)
    a.add(quad((-0.297, -0.069, 2.207), (0.297, -0.069, 2.207), (0.297, -0.069, 2.653), (-0.297, -0.069, 2.653)), "hr_prop_estate_sign", uv="rect", uv_rect=(0.0, 0.0, 1.0, 1.0))
    a.add(box(0.60, 0.018, 0.45, 0.003, 1, (0, -0.055, 2.43)), GALV)
    for z in (2.30, 2.56):
        a.add(box(0.12, 0.03, 0.03, 0.004, 1, (0, -0.04, z)), GALV)
        a.add(torus(0.042, 0.006, 16, 4), GALV, T(0, 0, z))
    a.meta.update(needsCollision=True, collider=cyl_collider(0.05, 2.9), notes="Galvanised 76 mm post with a 600 x 450 estate sign (NO BALL GAMES) facing -Y.")
    return a


def notice_board():
    a = Asset("NOTICE_BOARD", "street", 28)
    for x in (-0.66, 0.66):
        a.add(box(0.07, 0.07, 2.16, 0.006, 1, (x, 0, 1.03)), BLK)
        a.add(box(0.075, 0.075, 0.01, 0.002, 1, (x, 0, 2.115)), BLK)
    a.add(box(1.30, 0.08, 0.96, 0.008, 1, (0, -0.07, 1.42)), BLK)
    a.add(quad((-0.61, -0.111, 0.97), (0.61, -0.111, 0.97), (0.61, -0.111, 1.87), (-0.61, -0.111, 1.87)), "hr_prop_notices", uv="rect", uv_rect=A.NOTICES["board"])
    # frame lip around the board
    for (x0, x1, z0, z1) in ((-0.65, 0.65, 0.94, 0.97), (-0.65, 0.65, 1.87, 1.90), (-0.65, -0.61, 0.97, 1.87), (0.61, 0.65, 0.97, 1.87)):
        a.add(box_mm(x0, x1, -0.135, -0.105, z0, z1, 0.003), BLK)
    a.add(quad((-0.61, -0.127, 0.97), (0.61, -0.127, 0.97), (0.61, -0.127, 1.87), (-0.61, -0.127, 1.87)), "hr_prop_glass_clear", uv="keep")
    a.add(box(1.36, 0.03, 0.17, 0.004, 1, (0, -0.10, 1.995)), BLK)
    a.add(quad((-0.64, -0.1155, 1.925), (0.64, -0.1155, 1.925), (0.64, -0.1155, 2.065), (-0.64, -0.1155, 2.065)), "hr_prop_notices", uv="rect", uv_rect=A.NOTICES["header"])
    a.add(box(1.44, 0.20, 0.02, 0.005, 1, (0, -0.07, 2.09)), BLK)
    a.meta.update(needsCollision=True, collider=box_collider((1.44, 0.20, 2.1), (0, -0.05, 1.05)),
                  notes="Freestanding estate notice board on two posts, posters behind a clear cover.")
    return a


def satellite_dish():
    a = Asset("SATELLITE_DISH", "street", 29)
    a.add(box(0.10, 0.012, 0.16, 0.003, 1, (0, -0.006, 0)), GALV)
    for z in (-0.06, 0.06):
        a.add(bolt_head(0.007, 0.006), GALV, T(0, -0.012, z) @ R("X", 90))
    a.add(cyl_between((0, -0.012, 0), (0, -0.26, 0.0), 0.02, 10), GALV)
    a.add(box(0.06, 0.05, 0.08, 0.006, 1, (0, -0.27, 0.0)), GALV)
    dish_m = T(0, -0.33, 0.04) @ R("X", 98) @ S(1.0, 1.12, 1.0)
    prof = [(0.0, 0.0)]
    for k in range(1, 8):
        r = 0.30 * k / 7
        prof.append((r, (r * r) / 0.80))
    front = lathe(prof, 24, False, False)
    a.add(front, "hr_prop_dish_paint", dish_m)
    back = lathe([(p[0], p[1] - 0.004) for p in prof], 24, False, False)
    a.add(back, "hr_prop_dish_paint", dish_m, flip=True)
    a.add(lathe([(0.296, 0.108), (0.300, 0.1125), (0.296, 0.116)], 24, False, False), "hr_prop_dish_paint", dish_m)
    # LNB arm from the lower rim out to the focus
    a.add(cyl_between((0, -0.37, -0.28), (0, -0.55, -0.06), 0.010, 8), "hr_prop_dish_paint")
    a.add(box(0.05, 0.07, 0.05, 0.008, 1, (0, -0.56, -0.03)), PBLK)
    a.add(cyl(0.022, 0.03, 12, 0.0), PBLK, T(0, -0.53, -0.025) @ R("X", 98))
    a.meta.update(needsCollision=False, collider=None, mount="wall", notes="Offset dish on a wall bracket. Origin on the wall face at the bracket centre.")
    return a


def airbrick():
    a = Asset("AIRBRICK", "street", 30)
    a.add(box(0.215, 0.02, 0.14, 0.003, 1, (0, 0.005, 0)), "hr_prop_vents", uv="fit", fit_axis="Y", uv_rect=A.VENTS["airbrick"])
    a.meta.update(needsCollision=False, collider=None, mount="wall", notes="Clay airbrick, 215 x 140, 5 mm proud. Origin on the wall face at its centre.")
    return a


def vent_grille():
    a = Asset("VENT_GRILLE", "street", 31)
    for (x0, x1, z0, z1) in ((-0.125, 0.125, 0.105, 0.125), (-0.125, 0.125, -0.125, -0.105), (-0.125, -0.105, -0.105, 0.105), (0.105, 0.125, -0.105, 0.105)):
        a.add(box_mm(x0, x1, -0.014, 0.0, z0, z1, 0.003), UPVC)
    for k in range(7):
        z = -0.09 + k * 0.03
        a.add(box(0.21, 0.004, 0.026, 0.0012, 1), UPVC, T(0, -0.008, z) @ R("X", 45))
    a.add(box_mm(-0.105, 0.105, 0.0, 0.004, -0.105, 0.105), VOID)
    a.meta.update(needsCollision=False, collider=None, mount="wall", notes="250 mm louvred plastic wall vent. Origin on the wall face.")
    return a


def downpipe():
    a = Asset("DOWNPIPE_3M", "street", 32)
    y = -0.065
    r = 0.034
    path = fillet_path([(0, y, 3.0), (0, y, 0.20), (0, y - 0.11, 0.06)], 0.09, 5)
    a.add(tube(path, r, 12, up=(1, 0, 0)), PBLK)
    a.add(lathe([(r + 0.004, -0.012), (r + 0.004, 0.0), (r + 0.001, 0.004)], 12, False, False), PBLK, T(0, y - 0.11, 0.06) @ look_matrix((0, -0.11, -0.14)))
    for z in (1.50, 2.94):
        a.add(cyl(r + 0.004, 0.07, 12, z - 0.035), PBLK, T(0, y, 0))
    for z in (0.95, 2.45):
        a.add(cyl(r + 0.006, 0.025, 12, z - 0.0125), PBLK, T(0, y, 0))
        a.add(box(0.06, y * -1 - r + 0.002, 0.025, 0.003, 1, (0, (y + r) / 2 - 0.001, z)), PBLK)
        a.add(box(0.11, 0.008, 0.035, 0.003, 1, (0, -0.004, z)), PBLK)
        for x in (-0.04, 0.04):
            a.add(dome_head(0.005, 0.003), GALV, T(x, -0.008, z) @ R("X", 90))
    a.meta.update(needsCollision=False, collider=None, mount="wall",
                  notes="68 mm black PVC downpipe, 3 m, two brackets and a kicked shoe. Origin at ground on the wall face, pipe centre 65 mm off the wall.")
    return a


def roof_vent():
    a = Asset("ROOF_VENT", "street", 33)
    W, D, H0, H1 = 1.20, 0.70, 0.12, 0.62
    for x in (-0.48, 0.48):
        a.add(box(0.16, 0.62, H0, 0.01, 1, (x, 0, H0 / 2)), GALV)
    a.add(box(W, D, H1 - H0, 0.008, 1, (0, 0, (H0 + H1) / 2)), GALV)
    # angle frame on the vertical edges and rails
    for sx in (-1, 1):
        for sy in (-1, 1):
            a.add(box(0.035, 0.035, H1 - H0, 0.003, 1, (sx * (W / 2 - 0.012), sy * (D / 2 - 0.012), (H0 + H1) / 2)), GALV, S(1.0))
    for z in (H0 + 0.02, H1 - 0.015):
        a.add(box(W + 0.01, 0.012, 0.035, 0.003, 1, (0, -D / 2 - 0.004, z)), GALV)
        a.add(box(W + 0.01, 0.012, 0.035, 0.003, 1, (0, D / 2 + 0.004, z)), GALV)
    a.add(box(W + 0.02, D + 0.02, 0.012, 0.004, 1, (0, 0, H1 + 0.004)), GALV)
    a.add(box(0.012, D, 0.006, 0.0, 1, (0, 0, H1 + 0.012)), GALV)
    # front louvre bank, recessed
    a.add(box_mm(-0.47, 0.47, -D / 2 + 0.002, -D / 2 + 0.03, H0 + 0.07, H1 - 0.08), VOID)
    for k in range(7):
        z = H0 + 0.10 + k * 0.045
        a.add(box(0.92, 0.006, 0.05, 0.002, 1), GALV, T(0, -D / 2 - 0.006, z) @ R("X", -40))
    for (x0, x1, z0, z1) in ((-0.50, 0.50, H0 + 0.05, H0 + 0.075), (-0.50, 0.50, H1 - 0.08, H1 - 0.055), (-0.50, -0.47, H0 + 0.05, H1 - 0.055), (0.47, 0.50, H0 + 0.05, H1 - 0.055)):
        a.add(box_mm(x0, x1, -D / 2 - 0.016, -D / 2 + 0.004, z0, z1, 0.002), GALV)
    # side louvres
    for sx in (-1, 1):
        for k in range(5):
            a.add(box(0.006, 0.12, 0.04, 0.0015, 1), GALV, T(sx * (W / 2 + 0.004), 0.22, H0 + 0.12 + k * 0.06) @ R("Y", sx * 40))
    # rivets along the front rails
    for z in (H0 + 0.02, H1 - 0.015):
        for k in range(9):
            x = -0.56 + k * 0.14
            a.add(dome_head(0.004, 0.003, 6), GALV, T(x, -D / 2 - 0.010, z) @ R("X", 90))
    a.meta.update(needsCollision=True, collider=box_collider((1.22, 0.72, 0.64), (0, 0, 0.32)), notes="Galvanised louvred roof vent housing on two feet.")
    return a


def roof_tank():
    a = Asset("ROOF_TANK", "street", 34)
    a.add(box(1.60, 1.60, 0.20, 0.02, 2, (0, 0, 0.10)), CONC_R)
    Rt = 0.66
    prof = [(Rt - 0.03, 0.20), (Rt, 0.23)]
    z = 0.26
    while z < 1.30:
        prof += [(Rt, z), (Rt + 0.012, z + 0.012), (Rt + 0.012, z + 0.028), (Rt, z + 0.04)]
        z += 0.12
    prof += [(Rt, 1.36), (Rt - 0.03, 1.40), (Rt - 0.12, 1.43), (0.30, 1.445), (0.30, 1.46), (0.26, 1.47)]
    a.add(lathe(prof, 32, True, False), PBLK)
    a.add(lathe([(0.28, 1.465), (0.28, 1.50), (0.25, 1.51), (0.0, 1.515)], 24, False, False), PBLK)
    for k in range(4):
        ang = 45 + 90 * k
        m = R("Z", ang)
        a.add(box(0.012, 0.25, 0.012, 0.002, 1, (0, 0.20, 1.522)), PBLK, m)
        tri = prism([(0.0, 0.0), (0.16, 0.0), (0.0, 0.22)], 0.012, 0.002, 1)
        a.add(tri, AGED, m @ T(0, Rt - 0.01, 0.20) @ R("Z", 90))
        a.add(box(0.12, 0.10, 0.008, 0.002, 1, (0.0, Rt + 0.06, 0.204)), AGED, m)
        for dx in (-0.035, 0.035):
            a.add(bolt_head(0.008, 0.007), AGED, m @ T(dx, Rt + 0.09, 0.208))
    # outlet pipe and elbow on the front
    a.add(cyl(0.05, 0.02, 14, 0.0), BLK, T(0.18, -Rt + 0.005, 0.38) @ R("X", 90))
    a.add(tube(fillet_path([(0.18, -Rt - 0.01, 0.38), (0.18, -Rt - 0.17, 0.38), (0.18, -Rt - 0.17, 0.22)], 0.06, 4), 0.032, 12, up=(1, 0, 0)), BLK)
    a.add(cyl(0.042, 0.04, 12, 0.0), "hr_prop_copper", T(0.18, -Rt - 0.17, 0.205))
    a.meta.update(needsCollision=True, collider=cyl_collider(0.70, 1.52), notes="Black ribbed water tank on a concrete plinth with steel brackets and outlet elbow.")
    return a


def ac_unit():
    a = Asset("AC_UNIT", "street", 35)
    C = "hr_prop_ac_casing"
    y0, y1 = -0.06, -0.33
    yc = (y0 + y1) / 2
    for x in (-0.28, 0.28):
        a.add(sweep([(x, 0.0, 0.0), (x, y1 - 0.02, 0.0)], rect_profile(0.04, 0.004), up=(1, 0, 0)), GALV)
        a.add(sweep([(x, 0.0, 0.0), (x, 0.0, 0.25)], rect_profile(0.04, 0.004), up=(1, 0, 0)), GALV)
        a.add(cyl_between((x, -0.004, 0.22), (x, y1 + 0.02, 0.005), 0.008, 6), GALV)
    a.add(box(0.80, 0.27, 0.56, 0.012, 2, (0, yc, 0.30)), C)
    # fan grille: recess, rings and spokes
    fy = y1 - 0.002
    a.add(cyl(0.20, 0.004, 28, 0.0), VOID, T(-0.10, fy + 0.003, 0.30) @ R("X", 90))
    for r in (0.07, 0.12, 0.17, 0.205):
        a.add(torus(r, 0.003, 28, 4), BLK, T(-0.10, fy - 0.002, 0.30) @ R("X", 90))
    for k in range(4):
        a.add(box(0.41, 0.004, 0.008, 0.0, 1), BLK, T(-0.10, fy - 0.002, 0.30) @ R("Y", 45 + 90 * k))
    a.add(cyl(0.045, 0.02, 14, 0.0), BLK, T(-0.10, fy + 0.012, 0.30) @ R("X", 90))
    # side louvres on the right
    for k in range(8):
        a.add(box(0.12, 0.006, 0.006, 0.0, 1, (0.26, y1 - 0.002, 0.12 + k * 0.045)), VOID)
    # pipes into the wall
    for z, r in ((0.10, 0.012), (0.15, 0.016)):
        a.add(tube(fillet_path([(0.42, yc, z), (0.46, yc, z), (0.46, -0.02, z + 0.02), (0.46, 0.01, z + 0.02)], 0.04), r, 8), "hr_prop_copper" if r < 0.014 else PBLK)
    a.meta.update(needsCollision=False, collider=None, mount="wall",
                  notes="Small condenser on wall brackets. Origin on the wall face at the bracket foot.")
    return a


def railing():
    a = Asset("RAILING_1M", "street", 36)
    H = 1.20
    # post at x = -0.5 (left end), bars, rails
    a.add(box(0.06, 0.06, H, 0.004, 1, (-0.5, 0, H / 2)), BLK)
    a.add(box(0.064, 0.064, 0.008, 0.002, 1, (-0.5, 0, H + 0.004)), BLK)
    a.add(box(0.14, 0.14, 0.010, 0.002, 1, (-0.5, 0, 0.005)), BLK)
    for (bx, by) in ((-0.05, -0.05), (0.05, -0.05), (-0.05, 0.05), (0.05, 0.05)):
        a.add(bolt_head(0.008, 0.007), BLK, T(-0.5 + bx, by, 0.010))
    a.add(box(1.0 - 0.06, 0.04, 0.04, 0.004, 1, (0.0, 0, H - 0.04)), BLK)
    a.add(box(1.0 - 0.06, 0.04, 0.03, 0.003, 1, (0.0, 0, 0.11)), BLK)
    nb = 8
    for k in range(nb):
        x = -0.5 + 0.03 + (k + 0.5) * (0.94 / nb)
        a.add(box(0.016, 0.016, H - 0.17, 0.0015, 1, (x, 0, 0.125 + (H - 0.17) / 2)), BLK)
    a.meta.update(needsCollision=True, collider=box_collider((1.0, 0.06, H), (0, 0, H / 2)),
                  notes="1.2 m black steel estate railing module, 1 m pitch, post on the -X end. Tiles along +X; finish a run with RAILING_POST at the far end.")
    return a


def railing_post():
    a = Asset("RAILING_POST", "street", 37)
    H = 1.20
    a.add(box(0.06, 0.06, H, 0.004, 1, (0, 0, H / 2)), BLK)
    a.add(box(0.064, 0.064, 0.008, 0.002, 1, (0, 0, H + 0.004)), BLK)
    a.add(box(0.14, 0.14, 0.010, 0.002, 1, (0, 0, 0.005)), BLK)
    for (bx, by) in ((-0.05, -0.05), (0.05, -0.05), (-0.05, 0.05), (0.05, 0.05)):
        a.add(bolt_head(0.008, 0.007), BLK, T(bx, by, 0.010))
    a.meta.update(needsCollision=True, collider=box_collider((0.06, 0.06, H), (0, 0, H / 2)), notes="End post for a RAILING_1M run.")
    return a


BUILDERS = [lamp_column, wall_lamp, bollard, litter_bin, wheelie_bin,
            lambda: wheelie_bin("WHEELIE_BIN_240_GREEN", PGRN, PGRN), euro_bin, bench, cycle_hoop, bike,
            cctv, intercom, utility_cabinet, planter_edge, railing, railing_post, kerb, drain_gully, manhole,
            sign_post, notice_board, satellite_dish, airbrick, vent_grille, downpipe, roof_vent, roof_tank, ac_unit]
