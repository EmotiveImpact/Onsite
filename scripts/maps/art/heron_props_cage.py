"""The Cage: ball-court fence panels, posts, gate, goal and ball."""

import math

import bmesh
from mathutils import Vector

from heron_props_lib import (
    Asset, R, T, box, box_mm, bolt_head, cyl, cyl_between, dome_head, fillet_path, grid_plane,
    lathe, quad, rect_profile, sweep, tube, fbm, _new,
)
from heron_props_street import box_collider, cyl_collider

BLK = "hr_prop_cage_green"
MESH = "hr_prop_cage_mesh"
NET = "hr_prop_goal_net"
PAINT = "hr_prop_goal_paint"

POST = 0.08          # post section
PANEL_W = 2.5        # post centre to post centre
PANEL_H = 2.6


def _mesh_plane(a, x0, x1, z0, z1, y=0.0, mat=MESH, uv_scale=1.0):
    """Double-sided alpha-clipped mesh as one quad; UVs in metres from x0, z0."""
    w, h = x1 - x0, z1 - z0
    a.add(quad((x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1),
               uvs=((x0 * uv_scale, z0 * uv_scale), (x1 * uv_scale, z0 * uv_scale),
                    (x1 * uv_scale, z1 * uv_scale), (x0 * uv_scale, z1 * uv_scale))), mat, uv="keep")


def cage_post():
    a = Asset("CAGE_POST", "cage", 41)
    H = 2.72
    a.add(box(POST, POST, H, 0.005, 1, (0, 0, H / 2)), BLK)
    a.add(box(POST + 0.008, POST + 0.008, 0.012, 0.003, 1, (0, 0, H + 0.006)), BLK)
    a.add(box(0.20, 0.20, 0.012, 0.003, 1, (0, 0, 0.006)), BLK)
    for (bx, by) in ((-0.07, -0.07), (0.07, -0.07), (-0.07, 0.07), (0.07, 0.07)):
        a.add(bolt_head(0.010, 0.009), BLK, T(bx, by, 0.012))
    # welded gussets
    for k in range(4):
        a.add(box(0.006, 0.05, 0.06, 0.001, 1, (0, POST / 2 + 0.025, 0.04)), BLK, R("Z", 90 * k))
    a.meta.update(needsCollision=True, collider=box_collider((POST, POST, H), (0, 0, H / 2)),
                  notes="80 mm SHS court post, 2.72 m, on a bolted base plate. Posts sit every 2.5 m between CAGE_PANEL_2_5M modules.")
    return a


def cage_panel():
    a = Asset("CAGE_PANEL_2_5M", "cage", 42)
    xi = PANEL_W / 2 - POST / 2 - 0.012       # frame outer edge, clear of the post
    rail = 0.04
    # perimeter frame and two intermediate rails (40 x 40 SHS)
    for z in (0.04, 1.00, 1.90, PANEL_H - 0.02):
        a.add(box(2 * xi, rail, rail, 0.003, 1, (0, 0, z)), BLK)
    for x in (-xi + rail / 2, xi - rail / 2):
        a.add(box(rail, rail, PANEL_H - 0.04, 0.003, 1, (x, 0, (PANEL_H) / 2 + 0.0)), BLK)
    # mesh infill, double-sided single sheet on the frame centreline
    _mesh_plane(a, -xi + rail, xi - rail, 0.06, PANEL_H - 0.04)
    # clamp brackets to the posts on both ends
    for sx in (-1, 1):
        for z in (0.40, 1.45, 2.30):
            a.add(box(0.05, 0.05, 0.06, 0.004, 1, (sx * (xi + 0.004), 0, z)), BLK)
            a.add(bolt_head(0.008, 0.008), BLK, T(sx * (xi + 0.004), -0.025, z) @ R("X", 90))
    a.meta.update(needsCollision=True, collider=box_collider((PANEL_W, 0.06, PANEL_H), (0, 0, PANEL_H / 2)),
                  notes="2.5 m wide, 2.6 m high chain-link panel (fine diagonal wire texture on a double-sided sheet) in a green 40 mm box frame. Existing footprint and gates retained.")
    return a


def _leaf(a, hinge, direction, width, height, z0=0.08):
    """One gate leaf as a frame of 50 mm box with mesh, hinged at `hinge`."""
    d = Vector(direction).normalized()
    n = Vector((-d.y, d.x, 0))
    def P(u, z, off=0.0):
        p = Vector(hinge) + d * u + n * off
        return (p.x, p.y, z)
    ang = math.degrees(math.atan2(d.y, d.x))
    m = T(*Vector(hinge)) @ R("Z", ang)
    r = 0.05
    a.add(box(r, r, height, 0.003, 1, (0.03, 0, z0 + height / 2)), BLK, m)
    a.add(box(r, r, height, 0.003, 1, (width - 0.03, 0, z0 + height / 2)), BLK, m)
    for z in (z0 + r / 2, z0 + 1.05, z0 + height - r / 2):
        a.add(box(width - 0.06, r * 0.8, r * 0.8, 0.003, 1, (width / 2, 0, z)), BLK, m)
    # diagonal brace in the lower bay
    a.add(cyl_between((0.06, 0, z0 + 0.06), (width - 0.06, 0, z0 + 1.02), 0.012, 6), BLK, m)
    # mesh
    xa, xb = 0.055, width - 0.055
    za, zb = z0 + 0.05, z0 + height - 0.05
    a.add(quad((xa, 0, za), (xb, 0, za), (xb, 0, zb), (xa, 0, zb),
               uvs=((xa, za), (xb, za), (xb, zb), (xa, zb))), MESH, m, uv="keep")
    # hinges
    for z in (z0 + 0.25, z0 + height - 0.25):
        a.add(cyl(0.022, 0.12, 12, z - 0.06), BLK, m @ T(-0.012, 0, 0))
        a.add(box(0.06, 0.012, 0.08, 0.002, 1, (0.02, 0, z)), BLK, m)
    # drop bolt on the free end
    a.add(cyl(0.010, 0.55, 8, z0 - 0.06), "hr_steel_galv", m @ T(width - 0.06, -0.04, 0))
    a.add(box(0.04, 0.03, 0.05, 0.004, 1, (width - 0.06, -0.035, z0 + 0.36)), BLK, m)
    return m


def cage_gate():
    a = Asset("CAGE_GATE_4M", "cage", 43)
    P = 0.10
    xc = 2.0 + P / 2
    H = 2.90
    for sx in (-1, 1):
        a.add(box(P, P, H, 0.005, 1, (sx * xc, 0, H / 2)), BLK)
        a.add(box(P + 0.01, P + 0.01, 0.012, 0.003, 1, (sx * xc, 0, H + 0.006)), BLK)
        a.add(box(0.24, 0.24, 0.014, 0.003, 1, (sx * xc, 0, 0.007)), BLK)
        for (bx, by) in ((-0.09, -0.09), (0.09, -0.09), (-0.09, 0.09), (0.09, 0.09)):
            a.add(bolt_head(0.011, 0.010), BLK, T(sx * xc + bx, by, 0.014))
    # header across the top of the opening
    a.add(box(2 * xc + P, P, 0.10, 0.005, 1, (0, 0, H - 0.05)), BLK)
    # leaves swung outward (to -Y) by 100 degrees
    wl = 1.97
    hl = 2.30
    open_deg = 100.0
    for sx in (-1, 1):
        hinge = (sx * (2.0 - 0.02), -0.02, 0)
        # left leaf (sx=-1) closes toward +x, opens toward -y: rotate +x by -100 degrees
        # right leaf (sx=+1) closes toward -x, opens toward -y: rotate -x by +100 degrees
        d = Vector((math.cos(math.radians(-open_deg)), math.sin(math.radians(-open_deg)), 0)) if sx < 0 else \
            Vector((-math.cos(math.radians(-open_deg)), math.sin(math.radians(-open_deg)), 0))
        _leaf(a, hinge, d, wl, hl)
        # ground stop where the open leaf rests
        tip = Vector(hinge) + d * (wl - 0.10)
        a.add(box(0.08, 0.08, 0.08, 0.008, 1, (tip.x + sx * 0.06, tip.y, 0.04)), "hr_concrete_cast")
    # keeper plate on the ground at the centre of the opening
    a.add(box(0.12, 0.12, 0.012, 0.003, 1, (0, -0.04, 0.003)), "hr_steel_galv")
    a.add(cyl(0.014, 0.004, 10, 0.009), "hr_prop_dark_void", T(0, -0.04, 0))
    a.meta.update(needsCollision=True,
                  collider=[box_collider((P, P, H), (-xc, 0, H / 2)), box_collider((P, P, H), (xc, 0, H / 2)),
                            box_collider((0.06, 2.0, 2.4), (-2.27, -1.0, 1.2)), box_collider((0.06, 2.0, 2.4), (2.27, -1.0, 1.2))],
                  notes="4.0 m clear opening between 100 mm posts with a header beam; two 1.97 m leaves swung 100 degrees outward to -Y. The opening itself is walkable; collide posts and the open leaves only.")
    return a


def goal():
    a = Asset("GOAL_FIVE_A_SIDE", "cage", 44)
    W = 3.66            # inside width between posts
    Hh = 1.22           # underside of crossbar
    r = 0.038
    xo = W / 2 + r
    yf = -0.50          # mouth on the -Y side
    yb = 0.50
    zt = Hh + r
    # front frame with rounded top corners
    a.add(tube(fillet_path([(-xo, yf, 0.0), (-xo, yf, zt), (xo, yf, zt), (xo, yf, 0.0)], 0.07, 4), r, 12, up=(0, 1, 0)), PAINT)
    # ground frame: sides and back
    rg = 0.024
    a.add(tube(fillet_path([(-xo, yf + 0.03, rg), (-xo, yb, rg), (xo, yb, rg), (xo, yf + 0.03, rg)], 0.08, 3), rg, 8), PAINT)
    # top return and back stanchions
    yt = yf + 0.16
    for sx in (-1, 1):
        a.add(tube(fillet_path([(sx * xo, yf + 0.02, zt - 0.02), (sx * xo, yt, zt - 0.02), (sx * xo, yb, rg + 0.02)], 0.06, 3), 0.022, 8, up=(1, 0, 0)), PAINT)
    a.add(cyl_between((-xo, yt, zt - 0.02), (xo, yt, zt - 0.02), 0.020, 8), PAINT)
    # net: back slope, top strip, two sides; slightly slack
    def net_quad(p0, p1, p2, p3, nu=8, nv=4, sag=0.04, normal=(0, 1, 0)):
        bm = _new()
        uvl = bm.loops.layers.uv.active
        P = [Vector(p) for p in (p0, p1, p2, p3)]
        nrm = Vector(normal).normalized()
        grid = []
        for j in range(nv + 1):
            row = []
            for i in range(nu + 1):
                u, v = i / nu, j / nv
                p = (P[0] * (1 - u) + P[1] * u) * (1 - v) + (P[3] * (1 - u) + P[2] * u) * v
                s = math.sin(math.pi * u) * math.sin(math.pi * v)
                p = p + nrm * sag * s
                row.append(bm.verts.new(p))
            grid.append(row)
        L_u = (P[1] - P[0]).length
        L_v = (P[3] - P[0]).length
        for j in range(nv):
            for i in range(nu):
                f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
                for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                    loop[uvl].uv = (L_u * ii / nu, L_v * jj / nv)
        a.add(bm, NET, uv="keep")
    xi = xo - 0.01
    net_quad((-xi, yb - 0.01, 0.03), (xi, yb - 0.01, 0.03), (xi, yt + 0.01, zt - 0.03), (-xi, yt + 0.01, zt - 0.03), 10, 5, 0.05, (0, 1, 0.3))
    net_quad((-xi, yt, zt - 0.03), (xi, yt, zt - 0.03), (xi, yf + 0.02, zt - 0.03), (-xi, yf + 0.02, zt - 0.03), 10, 1, 0.0)
    for sx in (-1, 1):
        pts = [(sx * xi, yf + 0.02, 0.03), (sx * xi, yb - 0.01, 0.03), (sx * xi, yt, zt - 0.03), (sx * xi, yf + 0.02, zt - 0.03)]
        if sx > 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        net_quad(*pts, 4, 4, 0.03, (sx, 0, 0))
    # net clips along the crossbar
    for k in range(12):
        x = -xo + 0.15 + k * (2 * xo - 0.3) / 11
        a.add(cyl(r + 0.004, 0.012, 8, -0.006), "hr_plastic_black", T(x, yf, zt) @ R("Y", 90))
    a.meta.update(needsCollision=True, collider=box_collider((2 * xo + 2 * r, 1.04, zt + r), (0, 0, (zt + r) / 2)),
                  notes="3.66 x 1.22 m five-a-side goal, mouth faces -Y, white painted steel with a slack alpha-clipped net.")
    return a


def ball():
    a = Asset("BALL", "cage", 45)
    phi = (1 + 5 ** 0.5) / 2
    ico = []
    for (x, y) in ((-1, phi), (1, phi), (-1, -phi), (1, -phi)):
        ico += [Vector((0, x, y)), Vector((x, y, 0)), Vector((y, 0, x))]
    ico = [v.normalized() for v in ico]
    # icosahedron faces by nearest-neighbour search
    elen = min((ico[i] - ico[j]).length for i in range(12) for j in range(i + 1, 12))
    faces = []
    for i in range(12):
        for j in range(i + 1, 12):
            for k in range(j + 1, 12):
                if all(abs((ico[p] - ico[q]).length - elen) < 1e-4 for p, q in ((i, j), (j, k), (i, k))):
                    faces.append((i, j, k))
    Rr = 0.11

    def panel(poly, mat):
        bm = _new()
        c = sum(poly, Vector()) / len(poly)
        rings = [[(c + (p - c) * f).normalized() * (Rr * (0.985 if f == 1.0 else 1.0)) for p in poly] for f in (1.0, 0.88, 0.5)]
        vr = [[bm.verts.new(p) for p in ring] for ring in rings]
        cv = bm.verts.new(c.normalized() * Rr)
        n = len(poly)
        for t in range(2):
            for k in range(n):
                k1 = (k + 1) % n
                bm.faces.new((vr[t][k], vr[t][k1], vr[t + 1][k1], vr[t + 1][k]))
        for k in range(n):
            bm.faces.new((vr[2][k], vr[2][(k + 1) % n], cv))
        bm.normal_update()
        for f in bm.faces:
            if f.normal.dot(f.calc_center_median()) < 0:
                f.normal_flip()
        a.add(bm, mat, sharp=60.0)

    # pentagons around each original vertex
    def third(i, j):
        return ico[i] + (ico[j] - ico[i]) / 3.0
    for i in range(12):
        nbrs = [j for j in range(12) if j != i and abs((ico[i] - ico[j]).length - elen) < 1e-4]
        pts = [third(i, j) for j in nbrs]
        c = ico[i]
        ref = (pts[0] - c).normalized()
        side = c.cross(ref)
        pts.sort(key=lambda p: math.atan2((p - c).dot(side), (p - c).dot(ref)))
        panel(pts, "hr_prop_ball_black")
    for (i, j, k) in faces:
        hexa = [third(i, j), third(j, i), third(j, k), third(k, j), third(k, i), third(i, k)]
        panel(hexa, "hr_prop_ball_white")
    # sit on the ground, scuffed: shift up by radius
    import bmesh as _b
    _b.ops.translate(a.bm, vec=(0, 0, Rr), verts=a.bm.verts)
    a.meta.update(needsCollision=False, collider=cyl_collider(Rr, 2 * Rr),
                  notes="Size 5 ball, 0.22 m, 32 panels with stitched seams. Dynamic prop if wanted; static it can be ignored by collision.")
    return a


def floodlight():
    """Render replacement on the four existing lamp-column footprints; no new collider."""
    a = Asset('CAGE_FLOODLIGHT', 'cage', 47)
    a.add(cyl(.085, 6.25, 12), BLK)
    a.add(box(.28, .28, .025, .008, 1, (0, 0, .0125)), BLK)
    a.add(box(1.1, .08, .08, .008, 1, (0, 0, 6.22)), BLK)
    for x in [-.34, .34]:
        a.add(box(.48, .18, .32, .02, 2, (x, 0, 6.36)), BLK)
        a.add(box(.42, .012, .25, .01, 1, (x, -.097, 6.36)), 'hr_prop_court_lens')
        for u in [-.12, 0, .12]:
            a.add(box(.015, .012, .24, 0, 1, (x+u, -.107, 6.36)), 'hr_steel_galv')
    a.meta.update(needsCollision=False, notes='6.5 m paired court floodlight head; replaces render mesh at existing LAMP_COLUMN positions. Existing collision remains authoritative.')
    return a


def markings():
    """Original worn pitch paint. Goals retain their as-built offsets from the four gates."""
    a = Asset('CAGE_MARKINGS', 'cage', 48)
    def line(x0, y0, x1, y1, width=.075):
        dx, dy = x1-x0, y1-y0
        length = math.hypot(dx, dy)
        nx, ny = -dy/length*width/2, dx/length*width/2
        a.add(quad((x0+nx,y0+ny,.014),(x0-nx,y0-ny,.014),(x1-nx,y1-ny,.014),(x1+nx,y1+ny,.014)), 'hr_prop_court_paint', uv='keep')
    for x in [-14,14]: line(x,-9,x,9)
    for y in [-9,9]: line(-14,y,14,y)
    line(0,-9,0,9)
    for i in range(64):
        p=i*math.tau/64; q=(i+1)*math.tau/64
        line(2.5*math.cos(p),2.5*math.sin(p),2.5*math.cos(q),2.5*math.sin(q))
    # Blender Y is opposite map Z; goals are deliberately offset to preserve central gates.
    for x,y,side in [(-14,5.5,1),(14,-5.5,-1)]:
        line(x,y-2.7,x+side*4,y-2.7);line(x+side*4,y-2.7,x+side*4,y+2.7);line(x+side*4,y+2.7,x,y+2.7)
    a.meta.update(needsCollision=False, notes='30 x 20 m court, 75 mm paint lines, 5 m centre circle. Render-only; five-a-side goal offsets match the as-built fence gate clearance.')
    return a


BUILDERS = [cage_post, cage_panel, cage_gate, goal, ball]
