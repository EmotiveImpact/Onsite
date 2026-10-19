"""Bike hangar, bin store, substation, palisade fence and lock-up garages.
Usage: python3 build_structures.py OUT_DIR. Origins at base centre; fronts face -Y in Blender (+Z in glTF).
"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import bpy
import hrlib as H

OUT = Path(sys.argv[1])
H.reset()
stock = H.mat("mat_brick_london_stock", (0.42, 0.33, 0.22), 0.85)
redb = H.mat("mat_brick_red", (0.33, 0.15, 0.11), 0.85)
conc = H.mat("mat_concrete_cast", (0.45, 0.45, 0.43), 0.9)
felt = H.mat("mat_roof_felt", (0.08, 0.08, 0.08), 0.9)
galv = H.mat("mat_galvanised_steel", (0.55, 0.56, 0.56), 0.55, 0.9)
blk = H.mat("mat_steel_black_painted", (0.03, 0.03, 0.03), 0.6, 0.3)
shell = H.mat("mat_powder_coat_charcoal", (0.035, 0.038, 0.042), 0.55, 0.0)
green = H.mat("mat_painted_steel_green", (0.06, 0.16, 0.09), 0.55, 0.3)
dark = H.mat("mat_interior_dark", (0.02, 0.02, 0.02), 0.95)
doors = {"green": (0.12, 0.22, 0.14), "blue": (0.1, 0.17, 0.3), "white": (0.62, 0.62, 0.58), "rust": (0.3, 0.14, 0.07)}
made = []

def uv_all(ob):
    H.world_uv(ob)
    return ob

# --- bike hangar (Lambeth spec 2550 x 1365 x 2030 mm, six bikes) ---------------------
L, D, Ht = 2.55, 2.03, 1.365
prof = []
for i in range(13):  # front: low lip rising in a quarter ellipse to the crown
    t = i / 12 * math.pi / 2
    prof.append((-D / 2 + 0.25 + (1 - math.cos(t)) * 1.1, 0.32 + math.sin(t) * (Ht - 0.32)))
for i in range(1, 7):  # rear: tighter curve down to the back
    t = i / 6 * math.pi / 2
    prof.append((-D / 2 + 1.35 + math.sin(t) * (D - 1.35 - 0.02), 0.32 + math.cos(t) * (Ht - 0.32)))
prof = [(-D / 2 + 0.25, 0.12)] + prof + [(D / 2 - 0.02, 0.12)]
verts, faces = [], []
n = len(prof)
for x in (-L / 2, L / 2):
    for y, z in prof:
        verts.append((x, y, z))
for i in range(n - 1):
    faces.append((i, i + 1, n + i + 1, n + i))
faces.append(tuple(range(n))[::-1]); faces.append(tuple(range(n, 2 * n)))
hshell = H.mesh_obj("shell", verts, faces, shell)
base = [H.box("rail", (L, 0.08, 0.12), (0, y, 0.06), galv) for y in (-D / 2 + 0.25, D / 2 - 0.06)]
base += [H.box("cross", (0.06, D - 0.3, 0.06), (x, 0.1, 0.03), galv) for x in (-L / 2 + 0.05, 0, L / 2 - 0.05)]
handle = H.box("handle", (0.5, 0.04, 0.03), (0, -D / 2 + 0.22, 0.42), galv)
lockbox = H.box("lock", (0.12, 0.05, 0.1), (0.5, -D / 2 + 0.23, 0.38), galv)
seam = H.box("seam", (L + 0.01, 0.02, 0.02), (0, -0.25, 1.2), blk)
made.append(uv_all(H.join([hshell, *base, handle, lockbox, seam], "hr_prop_bike_hangar")))

# --- bin store: double-skin brick, hit-and-miss side panels, galvanised gates ----------
W, Dp, Wh, T = 3.6, 1.7, 1.5, 0.215
parts = [H.box("slab", (W + 0.3, Dp + 0.4, 0.1), (0, 0.05, 0.05), conc)]
parts.append(H.box("back", (W, T, Wh), (0, Dp / 2 - T / 2, 0.1 + Wh / 2), stock))
bl, bh, gap = 0.215, 0.075, 0.215
for sx in (-1, 1):
    x = sx * (W / 2 - T / 2)
    # solid lower and upper courses, hit-and-miss band between 0.5 and 1.2 m
    parts.append(H.box("side_lo", (T, Dp - T, 0.4), (x, -T / 2, 0.1 + 0.2), stock))
    parts.append(H.box("side_hi", (T, Dp - T, 0.3), (x, -T / 2, 0.1 + Wh - 0.15), stock))
    z = 0.5
    row = 0
    while z + bh <= 0.1 + Wh - 0.3 + 1e-6:
        y = -Dp / 2 + (0 if row % 2 == 0 else bl)
        while y + bl <= Dp / 2 - T + 1e-6:
            parts.append(H.box("brick", (T, bl - 0.01, bh - 0.01), (x, y + bl / 2, z + bh / 2), stock))
            y += bl + gap
        z += bh; row += 1
for sx in (-1, 1):
    parts.append(H.box("pier", (0.35, 0.35, Wh + 0.1), (sx * (W / 2 - 0.165), -Dp / 2 + 0.165, 0.1 + (Wh + 0.1) / 2), stock))
for (sx, sz, px, py) in ((W + 0.06, 0.3, 0, Dp / 2 - T / 2), (0.3, Dp, -W / 2 + T / 2, 0), (0.3, Dp, W / 2 - T / 2, 0)):
    parts.append(H.box("coping", (sx, sz, 0.06), (px, py, 0.1 + Wh + 0.03 + (0.008 if px else 0)), conc))
for sx in (-1, 1):
    parts.append(H.box("pier_cap", (0.4, 0.4, 0.06), (sx * (W / 2 - 0.165), -Dp / 2 + 0.165, 0.1 + Wh + 0.135), conc))
parts.append(H.box("buffer", (W - 2 * T, 0.05, 0.1), (0, Dp / 2 - T - 0.025, 0.45), blk))
store = uv_all(H.join(parts, "hr_prop_bin_store_3bay"))
made.append(store)

def gate_leaf(name, w, h):
    g = [H.box("t", (w, 0.04, 0.04), (w / 2, 0, h - 0.02), galv), H.box("b", (w, 0.04, 0.04), (w / 2, 0, 0.12), galv),
         H.box("m", (w, 0.03, 0.03), (w / 2, 0, h * 0.55), galv),
         H.box("l", (0.04, 0.04, h - 0.1), (0.02, 0, h / 2 + 0.05), galv), H.box("r", (0.04, 0.04, h - 0.1), (w - 0.02, 0, h / 2 + 0.05), galv)]
    x = 0.12
    while x < w - 0.08:
        g.append(H.box("bar", (0.016, 0.016, h - 0.12), (x, 0, h / 2 + 0.06), galv)); x += 0.12
    g.append(H.box("hinge", (0.03, 0.05, 0.08), (0.0, 0, h - 0.3), galv))
    return H.join(g, name)

lw = (W - 0.66) / 2
gl = gate_leaf("hr_prop_bin_store_gate_leaf", lw, 1.45)
made.append(uv_all(gl))  # origin at hinge side, base; place at store front, x = -1.47, y = -0.85, swing about Z

# --- substation and palisade fence ---------------------------------------------------
SW, SD, SH = 4.0, 3.0, 2.7
p = [H.box("walls", (SW, SD, SH), (0, 0, SH / 2), redb), H.box("roof", (SW + 0.3, SD + 0.3, 0.2), (0, 0, SH + 0.1), conc),
     H.box("felt", (SW + 0.2, SD + 0.2, 0.02), (0, 0, SH + 0.21), felt),
     H.box("plinth", (SW + 0.06, SD + 0.06, 0.25), (0, 0, 0.125), conc)]
p.append(H.box("recess", (1.9, 0.06, 2.25), (0, -SD / 2 - 0.0, 1.125 + 0.15), dark))
for sx in (-1, 1):
    leaf = [H.box("door", (0.88, 0.04, 2.15), (sx * 0.46, -SD / 2 - 0.02, 1.075 + 0.17), green)]
    for i in range(14):
        leaf.append(H.box("louvre", (0.7, 0.03, 0.035), (sx * 0.46, -SD / 2 - 0.045, 1.55 + i * 0.05), green))
    leaf.append(H.box("handle", (0.03, 0.05, 0.25), (sx * 0.08, -SD / 2 - 0.06, 1.1), galv))
    p += leaf
for i in range(10):
    p.append(H.box("vent", (0.9, 0.03, 0.04), (SW / 2 + 0.02, 0, 1.8 + i * 0.06), green))
sub = uv_all(H.join(p, "hr_prop_substation"))
made.append(sub)

def palisade(name, w=2.75, h=2.4, m=galv):
    q = [H.box("post", (0.1, 0.1, h + 0.1), (-w / 2, 0, (h + 0.1) / 2), m)]
    q += [H.box("rail", (w, 0.05, 0.05), (0, 0.04, z), m) for z in (0.35, h - 0.35)]
    x = -w / 2 + 0.12
    while x < w / 2 - 0.05:
        pw = 0.068
        prof = [(-pw / 2, 0), (pw / 2, 0), (pw / 2, h - 0.12), (pw / 4, h - 0.05), (pw / 8, h - 0.09), (0, h),
                (-pw / 8, h - 0.09), (-pw / 4, h - 0.05), (-pw / 2, h - 0.12)]
        nv = len(prof)
        vs = [(x + a, -0.015, b) for a, b in prof] + [(x + a, 0.015, b) for a, b in prof]
        fs = [tuple(range(nv)), tuple(range(nv, 2 * nv))[::-1]] + [(i, (i + 1) % nv, nv + (i + 1) % nv, nv + i) for i in range(nv)]
        q.append(H.mesh_obj("pale", vs, fs, m))
        x += 0.145
    return H.join(q, name)

made.append(uv_all(palisade("hr_prop_palisade_panel_2m75")))
made.append(uv_all(palisade("hr_prop_palisade_panel_2m75_green", m=green)))

# --- lock-up garages (module 2.6 m centres, 5.5 m deep) -------------------------------
GW, GD, GH = 2.6, 5.5, 2.3
g = [H.box("floor", (GW, GD, 0.1), (0, GD / 2, 0.05), conc),
     H.box("party", (0.1, GD, GH), (-GW / 2 + 0.05, GD / 2, GH / 2), redb),
     H.box("back", (GW, 0.215, GH - 0.15), (0, GD - 0.1, (GH - 0.15) / 2), redb),
     H.box("lintel", (GW, 0.25, 0.3), (0, 0.12, GH - 0.15), conc),
     H.box("pier", (0.25, 0.25, GH - 0.3), (-GW / 2 + 0.125, 0.12, (GH - 0.3) / 2), redb)]
# roof falls 100 mm to the back
rv = [(-GW / 2, -0.1, GH + 0.02), (GW / 2, -0.1, GH + 0.02), (GW / 2, GD, GH - 0.08), (-GW / 2, GD, GH - 0.08)]
rv += [(x, y, z - 0.12) for x, y, z in rv]
g.append(H.mesh_obj("roof", rv, [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)], felt))
g.append(H.box("interior", (GW - 0.35, 0.02, GH - 0.35), (0.06, GD - 0.22, (GH - 0.35) / 2 + 0.1), dark))
made.append(uv_all(H.join(g, "hr_prop_garage_bay")))
made.append(uv_all(H.join([H.box("end", (0.215, GD, GH), (0, GD / 2, GH / 2), redb), H.box("pier", (0.3, 0.3, GH - 0.3), (0, 0.15, (GH - 0.3) / 2), redb)], "hr_prop_garage_end_wall")))

def garage_door(name, col, opened=False):
    m = H.mat(f"mat_garage_door_{name.split('_')[-1]}", col, 0.5, 0.4)
    dw, dh = 2.1, 1.95
    q = [H.box("panel", (dw, 0.03, dh), (0, 0.27, dh / 2 + 0.1), m)]
    for i in range(int(dw / 0.15)):
        q.append(H.box("rib", (0.03, 0.02, dh - 0.1), (-dw / 2 + 0.1 + i * 0.15, 0.25, dh / 2 + 0.1), m))
    q.append(H.box("handle", (0.14, 0.04, 0.03), (0, 0.24, 1.0), galv))
    q.append(H.box("lock", (0.05, 0.03, 0.05), (0, 0.24, 1.07), galv))
    if opened:  # up-and-over door raised: lies flat just under the roof
        for o in q:
            o.rotation_euler = (math.radians(-90), 0, 0)
            o.location = (o.location.x, 0.3 + (o.location.z - 0.1), 2.08 + (o.location.y - 0.27))
    return uv_all(H.join(q, name))

for k, c in doors.items():
    made.append(garage_door(f"hr_prop_garage_door_{k}", c))
made.append(garage_door("hr_prop_garage_door_open", doors["green"], opened=True))

for o in made:
    H.smooth_by_angle(o)
print("tris", H.stats(), "objects", len(made))
H.export(OUT / "hr_prop_structures_kit.glb", made, blend=OUT / "source" / "hr_prop_structures_kit.blend")
