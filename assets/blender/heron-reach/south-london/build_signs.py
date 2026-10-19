"""Build hr_prop_signs_kit.glb from the sign atlas. Usage: python3 build_signs.py TEX_DIR OUT_DIR"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import bpy
import hrlib as H

TEX = Path(sys.argv[1]); OUT = Path(sys.argv[2])
layout = json.loads((TEX / "hr_sign_atlas_layout.json").read_text())
H.reset()
m_sign = H.mat("mat_sign_atlas", rough=0.45, image=TEX / "hr_sign_atlas_color.jpg")
m_post = H.mat("mat_galvanised_steel", (0.55, 0.56, 0.56), rough=0.55, metal=0.9)
m_num = H.mat("mat_decal_level_numerals", rough=0.8, image=TEX / "hr_decal_level_numerals.png", alpha="image")
GREY_UV = (0.995, 0.005)  # unused grey corner of the atlas
T = 0.004

def plate(sid, info):
    w, h = info["size_m"]; u0, v0, u1, v1 = info["uv"]
    ob = H.box(f"hr_prop_sign_{sid}", (w, T, h), (0, -T / 2, h / 2), m_sign)
    me = ob.data
    uvl = me.uv_layers.new(name="UVMap").data
    for p in me.polygons:
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if p.normal.y < -0.9:  # front face
                uvl[li].uv = (u0 + (co.x / w + 0.5) * (u1 - u0), v0 + (co.z / h + 0.5) * (v1 - v0))
            else:
                uvl[li].uv = GREY_UV
    return ob, w, h

made = []
for sid, info in layout["signs"].items():
    ob, w, h = plate(sid, info)
    mount = info["mount"]
    if mount == "post1":
        top = 2.25
        ob.location.z = top - h
        post = H.cyl("post", 0.038, 2.4, (0, 0.04, 1.2), m_post, 12)
        cl = [H.box("clamp", (0.1, 0.05, 0.03), (0, 0.025, z), m_post) for z in (top - 0.05, top - h + 0.05)]
        ob = H.join([ob, post, *cl], f"hr_prop_sign_{sid}_post")
    elif mount == "post2":
        ob.location.z = 0.85
        posts = [H.cyl("post", 0.045, 1.85, (x, 0.05, 0.925), m_post, 12) for x in (-w / 2 + 0.15, w / 2 - 0.15)]
        rails = [H.box("rail", (w - 0.1, 0.04, 0.04), (0, 0.02, z), m_post) for z in (0.95, 0.85 + h - 0.1)]
        ob = H.join([ob, *posts, *rails], f"hr_prop_sign_{sid}_posts")
    else:
        ob = H.join([ob], ob.name)
    made.append(ob)

# painted level numerals (decals, 0.8 m, sit 2 mm off the wall)
labels = ["G", "1", "2", "3", "4", "B1", "G1", "R"]
for i, lb in enumerate(labels):
    s = 0.8
    ob = H.mesh_obj(f"hr_decal_level_{lb.lower()}", [(-s / 2, -0.002, 0), (s / 2, -0.002, 0), (s / 2, -0.002, s), (-s / 2, -0.002, s)], [(0, 1, 2, 3)], m_num)
    cu, cv = i % 4, i // 4
    uv = ob.data.uv_layers.new(name="UVMap").data
    for li, (a, b) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv[li].uv = ((cu + a) / 4, 1 - (cv + 1 - b) / 2)
    made.append(ob)

print("tris", H.stats(), "objects", len(made))
H.export(OUT / "hr_prop_signs_kit.glb", made, blend=OUT / "source" / "hr_prop_signs_kit.blend")
