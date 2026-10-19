"""Covered-space lights and surface services. Usage: python3 build_lights_services.py OUT_DIR
Ceiling items: origin at the mounting face centre (top). Wall items: origin at back centre, front faces -Y (glTF +Z).
Run-type items (conduit, tray, pipes) run along +X from the origin.
"""
import math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import bpy
import hrlib as H

OUT = Path(sys.argv[1])
H.reset()
white = H.mat("mat_painted_metal_white", (0.82, 0.82, 0.8), 0.5)
grey_pvc = H.mat("mat_pvc_grey", (0.55, 0.56, 0.56), 0.6)
white_pvc = H.mat("mat_pvc_white", (0.85, 0.85, 0.83), 0.55)
galv = H.mat("mat_galvanised_steel", (0.55, 0.56, 0.56), 0.55, 0.9)
black = H.mat("mat_steel_black_painted", (0.03, 0.03, 0.03), 0.6, 0.3)
red = H.mat("mat_painted_metal_red", (0.55, 0.04, 0.03), 0.5)
cable = H.mat("mat_cable_black", (0.02, 0.02, 0.02), 0.5)
glow_cool = H.mat("mat_emissive_fluorescent", (0.9, 0.95, 1.0), 0.4, emissive=(0.92, 0.97, 1.0), strength=6)
glow_warm = H.mat("mat_emissive_warm", (1.0, 0.8, 0.55), 0.4, emissive=(1.0, 0.72, 0.4), strength=6)
dead = H.mat("mat_diffuser_off", (0.75, 0.75, 0.72), 0.3)
glass = H.mat("mat_glass_wired", (0.6, 0.65, 0.65), 0.1, 0.0)
made = []

def batten(name, length, twin=False, broken=False):
    parts = [H.box("body", (length, 0.07 if not twin else 0.14, 0.05), (0, 0, -0.025), white)]
    ys = [0] if not twin else [-0.035, 0.035]
    for y in ys:
        t = H.cyl("tube", 0.017, length - 0.06, (0, y, -0.065), dead if broken else glow_cool, 10, (0, math.radians(90), 0))
        parts.append(t)
    if not broken:
        parts.append(H.box("diffuser", (length - 0.02, (0.08 if not twin else 0.15), 0.004), (0, 0, -0.085), glow_cool))
    for x in (-length / 2 + 0.01, length / 2 - 0.01):
        parts.append(H.box("endcap", (0.02, 0.08 if not twin else 0.15, 0.06), (x, 0, -0.06), white))
    ob = H.join(parts, name); made.append(ob)

batten("hr_prop_light_batten_1500", 1.5)
batten("hr_prop_light_batten_1500_twin", 1.5, twin=True)
batten("hr_prop_light_batten_1500_dead", 1.5, broken=True)

# round bulkhead, wall mounted, with eyelid shade
def bulkhead(name, mat_glow):
    base = H.cyl("base", 0.15, 0.06, (0, -0.03, 0), black, 20, (math.radians(90), 0, 0))
    lens = H.cyl("lens", 0.12, 0.03, (0, -0.075, 0), mat_glow, 20, (math.radians(90), 0, 0))
    lid = H.box("eyelid", (0.28, 0.06, 0.02), (0, -0.09, 0.13), black)
    bars = [H.box("bar", (0.25, 0.012, 0.012), (0, -0.095, z), black) for z in (-0.05, 0.0, 0.05)]
    ob = H.join([base, lens, lid, *bars], name); made.append(ob)

bulkhead("hr_prop_light_bulkhead", glow_warm)
bulkhead("hr_prop_light_bulkhead_cool", glow_cool)

# caged wall lantern for the underpass (mockup 04)
back = H.box("back", (0.22, 0.04, 0.32), (0, -0.02, 0), black)
glob = H.cyl("globe", 0.075, 0.2, (0, -0.12, -0.01), glow_warm, 16)
cap = H.box("cap", (0.2, 0.18, 0.03), (0, -0.11, 0.105), black)
base = H.box("foot", (0.18, 0.16, 0.03), (0, -0.11, -0.125), black)
cage = []
for i in range(8):
    a = i / 8 * math.tau
    cage.append(H.box("cbar", (0.01, 0.01, 0.22), (math.cos(a) * 0.088, -0.12 + math.sin(a) * 0.088, -0.01), black))
made.append(H.join([back, glob, cap, base, *cage], "hr_prop_light_wall_caged"))

# --- services ------------------------------------------------------------------
def conduit(name, length, mat, r=0.0125):
    parts = [H.cyl("pipe", r, length, (length / 2, -0.03, 0), mat, 8, (0, math.radians(90), 0))]
    n = int(length / 0.5)
    for i in range(n + 1):
        x = min(length - 0.02, max(0.02, i * 0.5))
        parts.append(H.box("saddle", (0.02, 0.03, r * 2 + 0.008), (x, -0.017, 0), mat))
    ob = H.join(parts, name); made.append(ob)

conduit("hr_prop_conduit_2m_grey", 2.0, grey_pvc)
conduit("hr_prop_conduit_2m_white", 2.0, white_pvc)
# vertical conduit with junction box and 90 degree turn into the wall
parts = [H.cyl("pipe", 0.0125, 2.4, (0, -0.03, 1.2), white_pvc, 8), H.box("jbox", (0.1, 0.06, 0.1), (0, -0.03, 2.45), white_pvc)]
parts += [H.box("saddle", (0.03, 0.03, 0.02), (0, -0.017, z), white_pvc) for z in (0.2, 0.7, 1.2, 1.7, 2.2)]
made.append(H.join(parts, "hr_prop_conduit_riser_2m4"))

# cable tray 3 m with cables, ceiling hung on drop rods (origin at ceiling)
tray = [H.box("floor", (3.0, 0.3, 0.004), (1.5, 0, -0.4), galv),
        H.box("lip", (3.0, 0.004, 0.06), (1.5, -0.15, -0.37), galv), H.box("lip", (3.0, 0.004, 0.06), (1.5, 0.15, -0.37), galv)]
for x in (0.3, 1.5, 2.7):
    tray += [H.cyl("rod", 0.005, 0.4, (x, -0.17, -0.2), galv, 6), H.cyl("rod", 0.005, 0.4, (x, 0.17, -0.2), galv, 6),
             H.box("strut", (0.04, 0.38, 0.04), (x, 0, -0.42), galv)]
for i, y in enumerate((-0.1, -0.05, 0.0, 0.06, 0.11)):
    tray.append(H.cyl("cable", 0.012 + 0.004 * (i % 2), 3.0, (1.5, y, -0.385), cable, 8, (0, math.radians(90), 0)))
made.append(H.join(tray, "hr_prop_cable_tray_3m"))

# ceiling pipe pair (drainage + water) 3 m, with hangers
pp = [H.cyl("pipe", 0.055, 3.0, (1.5, 0, -0.25), black, 14, (0, math.radians(90), 0)),
      H.cyl("pipe", 0.03, 3.0, (1.5, 0.18, -0.2), grey_pvc, 10, (0, math.radians(90), 0))]
for x in (0.4, 1.5, 2.6):
    pp += [H.cyl("hanger", 0.005, 0.2, (x, 0, -0.1), galv, 6), H.cyl("hanger", 0.005, 0.17, (x, 0.18, -0.085), galv, 6)]
made.append(H.join(pp, "hr_prop_ceiling_pipes_3m"))

# dry riser inlet cabinet (ground floor wall) and landing valve (each floor)
cab = [H.box("box", (0.6, 0.3, 0.5), (0, -0.15, 0.25), red), H.box("glass", (0.5, 0.01, 0.38), (0, -0.305, 0.27), glass),
       H.box("frame", (0.6, 0.02, 0.05), (0, -0.31, 0.03), red)]
cab += [H.cyl("inlet", 0.045, 0.12, (x, -0.2, 0.25), galv, 12, (math.radians(90), 0, 0)) for x in (-0.12, 0.12)]
made.append(H.join(cab, "hr_prop_dry_riser_inlet"))
lv = [H.cyl("riser", 0.05, 2.7, (0, -0.08, 1.35), red, 12), H.cyl("outlet", 0.04, 0.18, (0, -0.17, 0.9), galv, 12, (math.radians(90), 0, 0)),
      H.cyl("wheel", 0.07, 0.02, (0, -0.27, 0.9), red, 14, (math.radians(90), 0, 0))]
lv += [H.box("clip", (0.12, 0.08, 0.03), (0, -0.04, z), galv) for z in (0.3, 2.3)]
made.append(H.join(lv, "hr_prop_dry_riser_landing"))

# coax drop: black cable down a facade from a dish, with clips (3 storeys)
pts = [(0, -0.01, 8.5), (0.05, -0.01, 6.0), (0.0, -0.01, 3.2), (0.08, -0.01, 0.8), (0.4, -0.01, 0.5)]
coax = [H.tube("coax", pts, 0.004, cable, 6)]
coax += [H.box("clip", (0.015, 0.012, 0.015), (p[0], -0.006, p[2]), white_pvc) for p in pts[:-1]]
made.append(H.join(coax, "hr_prop_coax_drop_3storey"))

for o in made:
    H.smooth_by_angle(o)
print("tris", H.stats(), "objects", len(made))
H.export(OUT / "hr_prop_lights_services_kit.glb", made, blend=OUT / "source" / "hr_prop_lights_services_kit.blend")
