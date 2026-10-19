"""Security fittings, car park kit and small estate extras.
Usage: python3 build_misc.py OUT_DIR. Floor items: origin base centre. Wall items: origin back centre, front -Y.
"""
import math, random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image
import bpy
import hrlib as H

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
random.seed(3)
# hazard stripe texture: 45 degree yellow/black, 125 mm bands at 1 UV = 1 m (texture covers 1 m)
n = 512
yy, xx = np.mgrid[0:n, 0:n]
band = ((xx + yy) // (n // 8)) % 2
img = np.where(band[..., None] == 0, np.array([228, 178, 20]), np.array([22, 22, 22])).astype(np.float32)
dirt = np.asarray(Image.fromarray((np.random.rand(n // 16, n // 16) * 255).astype(np.uint8)).resize((n, n), Image.BICUBIC), np.float32) / 255
img *= (0.75 + 0.25 * dirt)[..., None]
Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(OUT / "hr_hazard_stripes.png")

H.reset()
blk = H.mat("mat_steel_black_painted", (0.03, 0.03, 0.03), 0.6, 0.3)
white_steel = H.mat("mat_painted_metal_white", (0.82, 0.82, 0.8), 0.5)
galv = H.mat("mat_galvanised_steel", (0.55, 0.56, 0.56), 0.55, 0.9)
void = H.mat("mat_void_sheet", (0.42, 0.43, 0.43), 0.5, 0.7)
haz = H.mat("mat_hazard_stripes", rough=0.6, image=OUT / "hr_hazard_stripes.png")
rubber = H.mat("mat_rubber_black", (0.025, 0.025, 0.025), 0.85)
yellow = H.mat("mat_plastic_yellow", (0.75, 0.55, 0.02), 0.5)
conc = H.mat("mat_concrete_cast", (0.45, 0.45, 0.43), 0.9)
fabric = H.mat("mat_sofa_fabric", (0.16, 0.12, 0.1), 0.95)
wood = H.mat("mat_pallet_timber", (0.45, 0.34, 0.22), 0.85)
plastic_grey = H.mat("mat_plastic_grey", (0.2, 0.2, 0.21), 0.5)
screen = H.mat("mat_crt_screen", (0.02, 0.025, 0.03), 0.15)
chrome = H.mat("mat_canister_silver", (0.8, 0.8, 0.82), 0.25, 1.0)
cloth = [H.mat(f"mat_washing_{i}", c, 0.95) for i, c in enumerate([(0.6, 0.6, 0.6), (0.1, 0.12, 0.25), (0.5, 0.1, 0.1), (0.75, 0.72, 0.6)])]
made = []

def keep(ob):
    H.world_uv(ob, skip_materials=("mat_hazard_stripes",)); made.append(ob); return ob

# --- security ---------------------------------------------------------------
def grille(name, w, h, m):
    q = [H.box("frame", (w, 0.03, 0.03), (0, -0.04, z), m) for z in (0.015, h - 0.015, h / 2)]
    q += [H.box("side", (0.03, 0.03, h), (x, -0.04, h / 2), m) for x in (-w / 2 + 0.015, w / 2 - 0.015)]
    x = -w / 2 + 0.11
    while x < w / 2 - 0.05:
        q.append(H.cyl("bar", 0.008, h - 0.03, (x, -0.04, h / 2), m, 6)); x += 0.11
    q += [H.box("lug", (0.05, 0.04, 0.04), (sx * (w / 2 - 0.015), -0.02, z), m) for sx in (-1, 1) for z in (0.1, h - 0.1)]
    return keep(H.join(q, name))

grille("hr_prop_window_grille_1200", 1.2, 1.2, white_steel)  # origin: bottom centre of window reveal face
grille("hr_prop_window_grille_1200_black", 1.2, 1.2, blk)
grille("hr_prop_door_security_gate", 0.95, 2.05, blk)
lock = H.box("lockbox", (0.12, 0.06, 0.18), (0.38, -0.08, 1.0), blk)
made[-1] = H.join([made[-1], lock], "hr_prop_door_security_gate")
H.world_uv(made[-1])

def void_sheet(name, w, h):
    q = [H.box("sheet", (w + 0.1, 0.004, h + 0.1), (0, -0.01, h / 2), void)]
    q += [H.box("bolt", (0.02, 0.015, 0.02), (x, -0.018, z), galv) for x in (-w / 2 - 0.02, w / 2 + 0.02) for z in (0.05, h / 2, h - 0.05)]
    q.append(H.box("seam", (w + 0.1, 0.006, 0.015), (0, -0.013, h * 0.5), void))
    return keep(H.join(q, name))

void_sheet("hr_prop_void_sheet_window_1200", 1.2, 1.2)
void_sheet("hr_prop_void_sheet_door", 0.95, 2.05)

# anti-pigeon spikes strip 1 m (sits on a ledge)
sp = [H.box("base", (1.0, 0.04, 0.005), (0, 0, 0.0025), plastic_grey)]
for i in range(20):
    x = -0.475 + i * 0.05
    for a in (-0.4, 0, 0.4):
        sp.append(H.cyl("spike", 0.0015, 0.11, (x + math.sin(a) * 0.02, 0, 0.055), galv, 4, (a, 0, 0)))
keep(H.join(sp, "hr_prop_pigeon_spikes_1m"))

# --- car park kit -------------------------------------------------------------
cw = 0.45
wrap = H.box("wrap", (cw + 0.01, cw + 0.01, 1.0), (0, 0, 0.5), haz)
H.world_uv(wrap)
made.append(H.join([wrap], "hr_prop_column_hazard_wrap_450"))  # slips over a 450 mm column
stop = [H.box("stop", (1.8, 0.15, 0.1), (0, 0, 0.05), rubber)]
for i in range(4):
    stop.append(H.box("band", (0.18, 0.152, 0.102), (-0.6 + i * 0.4, 0, 0.051), yellow))
keep(H.join(stop, "hr_prop_wheel_stop"))
hb = [H.box("post", (0.12, 0.12, 2.4), (x, 0, 1.2), haz) for x in (-1.6, 1.6)]
hb.append(H.box("bar", (3.32, 0.1, 0.15), (0, 0, 2.18), haz))
for o in hb:
    H.world_uv(o)
made.append(H.join(hb, "hr_prop_height_barrier_3m2"))
# parking bay number stencil block is in the sign kit; speed hump
hump = H.mesh_obj("hump", [(-1.5, -0.45, 0), (1.5, -0.45, 0), (1.5, 0, 0.065), (-1.5, 0, 0.065), (-1.5, 0.45, 0), (1.5, 0.45, 0)],
                  [(0, 1, 2, 3), (3, 2, 5, 4)], rubber)
keep(H.join([hump], "hr_prop_speed_hump_rubber_3m"))

# --- extras -------------------------------------------------------------------
gb = [H.mesh_obj("bin", [(-0.45, -0.3, 0), (0.45, -0.3, 0), (0.42, -0.27, 0.6), (-0.42, -0.27, 0.6),
                          (-0.45, 0.3, 0), (0.45, 0.3, 0), (0.42, 0.27, 0.6), (-0.42, 0.27, 0.6)],
                  [(0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)], yellow)]
gb.append(H.box("lid", (0.92, 0.6, 0.06), (0, 0.0, 0.66), yellow))
gb.append(H.box("lid_rise", (0.92, 0.12, 0.12), (0, 0.25, 0.7), yellow))
keep(H.join(gb, "hr_prop_grit_bin"))

# drying area: two T posts with lines (one per piece; post spacing 6 m)
dp = []
for x in (-3, 3):
    dp += [H.cyl("post", 0.04, 2.1, (x, 0, 1.05), galv, 10), H.box("arm", (0.06, 1.2, 0.05), (x, 0, 2.05), galv)]
for y in (-0.5, -0.17, 0.17, 0.5):
    dp.append(H.tube("line", [(-3, y, 2.0), (0, y, 1.85), (3, y, 2.0)], 0.003, white_steel, 4))
keep(H.join(dp, "hr_prop_drying_posts_6m"))

# clothes airer with washing (balcony clutter)
ca = []
for sx in (-1, 1):
    ca.append(H.tube("leg", [(sx * 0.4, -0.3, 0), (sx * 0.4, 0.0, 0.95), (sx * 0.4, 0.3, 0)], 0.008, white_steel, 6))
for i in range(6):
    y = -0.25 + i * 0.1
    z = 0.95 - abs(y) * 2.9 * 0.3
    ca.append(H.cyl("rail", 0.004, 0.8, (0, y, z + 0.02), white_steel, 4, (0, math.radians(90), 0)))
for i in range(5):
    m = cloth[i % 4]
    x = -0.3 + i * 0.15
    ca.append(H.box("cloth", (0.12, 0.02, 0.35 + 0.1 * (i % 2)), (x, -0.05 + 0.1 * (i % 2), 0.85 - (0.35 + 0.1 * (i % 2)) / 2), m))
keep(H.join(ca, "hr_prop_clothes_airer"))

# dumped two-seat sofa, cushions askew
so = [H.box("base", (1.6, 0.85, 0.42), (0, 0, 0.21), fabric), H.box("back", (1.6, 0.22, 0.45), (0, 0.32, 0.64), fabric),
      H.box("armL", (0.2, 0.85, 0.25), (-0.7, 0, 0.54), fabric), H.box("armR", (0.2, 0.85, 0.25), (0.7, 0, 0.54), fabric),
      H.box("cush1", (0.6, 0.65, 0.14), (-0.3, -0.06, 0.49), fabric, (0.05, 0.08, 0.1)),
      H.box("cush2", (0.6, 0.65, 0.14), (0.42, -0.25, 0.3), fabric, (0.6, 0.0, -0.3))]
keep(H.join(so, "hr_prop_dumped_sofa"))

tv = [H.box("body", (0.6, 0.45, 0.48), (0, 0.05, 0.24), plastic_grey), H.box("rear", (0.4, 0.25, 0.35), (0, 0.35, 0.2), plastic_grey),
      H.box("screen", (0.5, 0.01, 0.38), (0, -0.175, 0.25), screen)]
keep(H.join(tv, "hr_prop_crt_tv_dumped"))

pal = []
for x in (-0.5, 0, 0.5):
    pal.append(H.box("block", (0.1, 1.0, 0.08), (x, 0, 0.04), wood))
for y in np.linspace(-0.45, 0.45, 7):
    pal.append(H.box("deck", (1.2, 0.1, 0.022), (0, float(y), 0.091), wood))
for y in (-0.45, 0, 0.45):
    pal.append(H.box("bottom", (1.2, 0.1, 0.022), (0, y, -0.011 + 0.011), wood))
keep(H.join(pal, "hr_prop_pallet"))

# nitrous oxide canisters, a scatter of 9 on 0.6 m (very common estate litter)
nos = []
for i in range(9):
    a = random.uniform(0, math.tau)
    nos.append(H.cyl("can", 0.009, 0.066, (random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), 0.009), chrome, 8, (math.radians(90), 0, a)))
keep(H.join(nos, "hr_prop_litter_nos_canisters"))

for o in made:
    H.smooth_by_angle(o)
print("tris", H.stats(), "objects", len(made))
H.export(OUT / "hr_prop_security_carpark_extras_kit.glb", made, blend=OUT / "source" / "hr_prop_security_carpark_extras_kit.blend")
