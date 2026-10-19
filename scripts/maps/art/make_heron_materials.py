"""Build assets/blender/heron-reach/materials.blend from the Heron Reach texture kit,
test glTF export, and render the Cycles preview boards.

Run after make_heron_textures.py and make_heron_decals.py:
    python3 scripts/maps/art/make_heron_materials.py [--no-render]

Material graph (tiling sets): UV Map -> Mapping (Point, scale = 1/coverage) -> colour
(sRGB), normal (Non-Color -> Normal Map) and ORM (Non-Color -> Separate Color:
R -> glTF Material Output.Occlusion, G -> Roughness, B -> Metallic). Images are packed.
"""
from __future__ import annotations

import json
import os
import struct
import sys
import time
from pathlib import Path

import bpy

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
TEX = REPO / "public/materials/heron"
BLEND = REPO / "assets/blender/heron-reach/materials.blend"
MANIFEST = REPO / "assets/blender/heron-reach/materials-manifest.json"
PREVIEW = Path("/mnt/project-files/heron-reach/progress/kit")
SCRATCH = Path(os.environ.get("HERON_TEX_SCRATCH", "/tmp/heron-tex-scratch"))

TILING = {  # name: coverage metres (from the conventions table)
    "hr_brick_stock": 2, "hr_brick_red": 2, "hr_brick_painted": 2, "hr_concrete_cast": 2,
    "hr_concrete_board": 2, "hr_concrete_rough": 2, "hr_render": 2, "hr_asphalt": 2, "hr_court": 2,
    "hr_paving": 2, "hr_pavers_red": 2, "hr_roof_felt": 2, "hr_steel_black": 1, "hr_steel_galv": 1,
    "hr_steel_aged": 1, "hr_shutter": 2, "hr_rubber": 1, "hr_timber": 2, "hr_soil": 2,
    "hr_grass_ground": 2, "hr_gravel": 2, "hr_plaster": 2,
}
K2700 = (1.0, 0.56, 0.24, 1.0)  # linear RGB, approx. 2700 K blackbody normalised to R
K2700_SRGB_NOTE = "linear (1.0, 0.56, 0.24), approximately a 2700 K blackbody"

# plain shared materials: base colour (linear), roughness, metallic, emission (colour, strength)
PLAIN = {
    "hr_glass": dict(base=(0.012, 0.015, 0.02), rough=0.06, metal=0.0, spec=0.6,
                     note="dark reflective glazing, opaque (no transmission)"),
    "hr_glass_lit": dict(base=(0.03, 0.02, 0.012), rough=0.08, metal=0.0, emit=(K2700, 3.0),
                         note="warm 2700 K emissive glazing, strength 3"),
    "hr_lamp_emit": dict(base=(0.8, 0.7, 0.55), rough=0.3, metal=0.0, emit=(K2700, 12.0),
                         note="lamp lenses, warm 2700 K, strength 12"),
    "hr_upvc_white": dict(base=(0.62, 0.62, 0.6), rough=0.38, metal=0.0, note="weathered white uPVC"),
    "hr_paint_yellow": dict(base=(0.55, 0.36, 0.035), rough=0.5, metal=0.0, note="muted safety yellow"),
    "hr_plastic_black": dict(base=(0.018, 0.018, 0.019), rough=0.48, metal=0.0, note="black plastic"),
    "hr_plastic_green": dict(base=(0.025, 0.06, 0.035), rough=0.5, metal=0.0, note="dark bin green"),
    "hr_door_paint": dict(base=(0.3, 0.3, 0.3), rough=0.42, metal=0.0, vcol=True,
                          note="gloss front-door paint; base colour = active colour attribute (glTF COLOR_0)"),
    "hr_signage": dict(base=(0.7, 0.7, 0.68), rough=0.4, metal=0.0, note="sign face backing"),
}

# decals: (colour file, normal, orm, alpha mode, roughness, metallic, coverage note)
DECALS = {
    "hr_decal_rain_streaks": dict(color="decals/rain-streaks.webp", rough=0.75, alpha="BLEND"),
    "hr_decal_grime": dict(color="decals/grime.webp", rough=0.85, alpha="BLEND"),
    "hr_decal_moss": dict(color="decals/moss-edge.webp", rough=0.9, alpha="BLEND"),
    "hr_decal_puddle": dict(color="decals/puddle-color.webp", normal="decals/puddle-normal.webp", rough=0.04,
                            alpha="BLEND"),
    "hr_decal_line_yellow": dict(color="decals/line-yellow.webp", rough=0.55, alpha="BLEND"),
    "hr_decal_line_white": dict(color="decals/line-white.webp", rough=0.55, alpha="BLEND"),
    "hr_decal_drain": dict(color="decals/drain-grate-color.webp", normal="decals/drain-grate-normal.webp",
                           orm="decals/drain-grate-orm.webp", alpha="MASK"),
    "hr_decal_graffiti": dict(color="decals/graffiti-atlas.webp", rough=0.6, alpha="BLEND"),
    "hr_decal_leaf_stains": dict(color="decals/leaf-stains.webp", rough=0.8, alpha="BLEND"),
}
ATLAS = {
    "hr_window_interior": dict(color="windows/interiors-color.webp", emit="windows/interiors-emit.webp",
                               strength=3.0, coverage=None, base_mul=0.35,
                               note="8 x 4 atlas, one cell per pane (UV the pane to one cell); emission strength 3"),
    "hr_backdrop_tower": dict(color="backdrop/tower-facade-color.webp", emit="backdrop/tower-facade-emit.webp",
                              strength=2.5, coverage=12.0, base_mul=1.0,
                              note="distant tower facade, 12 m tile, lit windows strength 2.5"),
}


# ---------------------------------------------------------------- helpers
_images = {}


def image(rel, non_color):
    if rel in _images:
        return _images[rel]
    img = bpy.data.images.load(str(TEX / rel), check_existing=False)
    img.name = Path(rel).name
    img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    img.alpha_mode = "STRAIGHT"
    img.pack()
    _images[rel] = img
    return img


def gltf_output_group():
    name = "glTF Material Output"
    g = bpy.data.node_groups.get(name)
    if g:
        return g
    g = bpy.data.node_groups.new(name, "ShaderNodeTree")
    s = g.interface.new_socket("Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    s.default_value = 1.0
    s.min_value, s.max_value = 0.0, 1.0
    g.nodes.new("NodeGroupInput")
    return g


def new_material(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (250, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, bsdf


def tex_node(nt, img, loc, vec=None):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    t.location = loc
    t.interpolation = "Linear"
    t.extension = "REPEAT"
    if vec is not None:
        nt.links.new(vec, t.inputs["Vector"])
    return t


def mapping(nt, scale, loc=(-900, 0)):
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.location = (loc[0] - 200, loc[1])
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.vector_type = "POINT"
    mp.location = loc
    mp.inputs["Scale"].default_value = (scale, scale, 1.0)
    nt.links.new(uv.outputs["UV"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def hook_orm(nt, bsdf, orm_tex):
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    sep.location = (-250, -250)
    nt.links.new(orm_tex.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    nt.links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])
    g = nt.nodes.new("ShaderNodeGroup")
    g.node_tree = gltf_output_group()
    g.location = (250, -500)
    g.label = "glTF Material Output"
    nt.links.new(sep.outputs["Red"], g.inputs["Occlusion"])


def hook_normal(nt, bsdf, ntex, strength=1.0):
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.location = (-250, -550)
    nm.inputs["Strength"].default_value = strength
    nt.links.new(ntex.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])


def build_tiling(name, cov):
    m, nt, bsdf = new_material(name)
    vec = mapping(nt, 1.0 / cov)
    c = tex_node(nt, image("%s-color.webp" % name, False), (-500, 250), vec)
    n = tex_node(nt, image("%s-normal.webp" % name, True), (-500, -550), vec)
    o = tex_node(nt, image("%s-orm.webp" % name, True), (-500, -250), vec)
    nt.links.new(c.outputs["Color"], bsdf.inputs["Base Color"])
    hook_orm(nt, bsdf, o)
    hook_normal(nt, bsdf, n)
    m["hr_coverage_m"] = cov
    return m


def build_plain(name, d):
    m, nt, bsdf = new_material(name)
    bsdf.inputs["Base Color"].default_value = (*d["base"], 1.0)
    bsdf.inputs["Roughness"].default_value = d["rough"]
    bsdf.inputs["Metallic"].default_value = d["metal"]
    if "spec" in d:
        bsdf.inputs["Specular IOR Level"].default_value = d["spec"]
    if "emit" in d:
        col, s = d["emit"]
        bsdf.inputs["Emission Color"].default_value = col
        bsdf.inputs["Emission Strength"].default_value = s
    if d.get("vcol"):
        va = nt.nodes.new("ShaderNodeVertexColor")
        va.location = (-300, 100)
        nt.links.new(va.outputs["Color"], bsdf.inputs["Base Color"])
    m.diffuse_color = (*d["base"], 1.0)
    return m


def set_alpha(m, nt, bsdf, alpha_socket, mode):
    if mode == "MASK":
        # Round(alpha) = alpha threshold 0.5; the glTF exporter writes alphaMode MASK
        rn = nt.nodes.new("ShaderNodeMath")
        rn.operation = "ROUND"
        rn.location = (0, -100)
        nt.links.new(alpha_socket, rn.inputs[0])
        nt.links.new(rn.outputs[0], bsdf.inputs["Alpha"])
        m.surface_render_method = "DITHERED"
    else:
        nt.links.new(alpha_socket, bsdf.inputs["Alpha"])
        m.surface_render_method = "BLENDED"
    m.use_transparency_overlap = False


def build_decal(name, d):
    m, nt, bsdf = new_material(name)
    vec = mapping(nt, 1.0)
    c = tex_node(nt, image(d["color"], False), (-500, 250), vec)
    nt.links.new(c.outputs["Color"], bsdf.inputs["Base Color"])
    if d.get("orm"):
        hook_orm(nt, bsdf, tex_node(nt, image(d["orm"], True), (-500, -250), vec))
    else:
        bsdf.inputs["Roughness"].default_value = d.get("rough", 0.7)
        bsdf.inputs["Metallic"].default_value = d.get("metal", 0.0)
    if d.get("normal"):
        hook_normal(nt, bsdf, tex_node(nt, image(d["normal"], True), (-500, -550), vec))
    set_alpha(m, nt, bsdf, c.outputs["Alpha"], d["alpha"])
    return m


def build_atlas(name, d):
    m, nt, bsdf = new_material(name)
    vec = mapping(nt, 1.0 / d["coverage"]) if d["coverage"] else None
    c = tex_node(nt, image(d["color"], False), (-500, 250), vec)
    e = tex_node(nt, image(d["emit"], False), (-500, -100), vec)
    if d["base_mul"] != 1.0:
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        mul.location = (-150, 250)
        nt.links.new(c.outputs["Color"], mul.inputs["A"])
        mul.inputs["B"].default_value = (d["base_mul"],) * 3 + (1.0,)
        nt.links.new(mul.outputs["Result"], bsdf.inputs["Base Color"])
    else:
        nt.links.new(c.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(e.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = d["strength"]
    bsdf.inputs["Roughness"].default_value = 0.12 if name == "hr_window_interior" else 0.8
    return m


def build_all():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = {}
    for name, cov in TILING.items():
        mats[name] = build_tiling(name, cov)
    for name, d in PLAIN.items():
        mats[name] = build_plain(name, d)
    for name, d in DECALS.items():
        mats[name] = build_decal(name, d)
    for name, d in ATLAS.items():
        mats[name] = build_atlas(name, d)
    for m in mats.values():
        m.use_fake_user = True
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=False)
    return mats


# ---------------------------------------------------------------- glTF export test
def read_glb_json(path):
    with open(path, "rb") as f:
        data = f.read()
    magic, ver, length = struct.unpack_from("<4sII", data, 0)
    clen, ctype = struct.unpack_from("<II", data, 12)
    return json.loads(data[20:20 + clen].decode("utf8"))


def gltf_test():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    bpy.ops.mesh.primitive_cube_add(size=2.0)
    cube = bpy.context.active_object
    cube.name = "hr_export_test_cube"
    names = ["hr_brick_stock", "hr_steel_galv", "hr_decal_drain", "hr_glass_lit", "hr_decal_graffiti", "hr_backdrop_tower"]
    for n in names:
        cube.data.materials.append(bpy.data.materials[n])
    for i, p in enumerate(cube.data.polygons):
        p.material_index = i % len(names)
    results = {}
    for fmt in ("WEBP", "AUTO"):
        out = SCRATCH / ("hr_export_test_%s.glb" % fmt.lower())
        t0 = time.time()
        bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", use_selection=True,
                                  export_image_format=fmt, export_materials="EXPORT")
        j = read_glb_json(out)
        mats = []
        for m in j.get("materials", []):
            pbr = m.get("pbrMetallicRoughness", {})
            info = {"name": m["name"], "alphaMode": m.get("alphaMode", "OPAQUE")}
            for slot, ti in (("baseColor", pbr.get("baseColorTexture")), ("metallicRoughness", pbr.get("metallicRoughnessTexture")),
                             ("normal", m.get("normalTexture")), ("occlusion", m.get("occlusionTexture")),
                             ("emissive", m.get("emissiveTexture"))):
                if ti:
                    tt = ti.get("extensions", {}).get("KHR_texture_transform")
                    src = j["textures"][ti["index"]]
                    img_i = src.get("source", src.get("extensions", {}).get("EXT_texture_webp", {}).get("source"))
                    info[slot] = {"texture": ti["index"], "image": img_i, "KHR_texture_transform": tt,
                                  "textureExtensions": list(src.get("extensions", {}).keys())}
            if "emissiveFactor" in m:
                info["emissiveFactor"] = m["emissiveFactor"]
            if m.get("extensions"):
                info["extensions"] = m["extensions"]
            mats.append(info)
        results[fmt] = {
            "file": str(out), "bytes": out.stat().st_size, "seconds": round(time.time() - t0, 2),
            "extensionsUsed": j.get("extensionsUsed", []), "extensionsRequired": j.get("extensionsRequired", []),
            "images": [{"name": im.get("name"), "mimeType": im.get("mimeType")} for im in j.get("images", [])],
            "materials": mats,
        }
    return results


# ---------------------------------------------------------------- previews
def dusk_scene(res=(960, 640), samples=64):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 4
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    w = bpy.data.worlds.new("hr_dusk")
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.05, 0.075, 0.16, 1.0)  # cool blue-hour sky fill
    bg.inputs["Strength"].default_value = 1.6
    sc.world = w
    return sc


def warm_point(loc, power, radius=0.15):
    ld = bpy.data.lights.new("hr_warm", "POINT")
    ld.energy = power
    ld.color = K2700[:3]
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new("hr_warm", ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    return ob


def plane(name, size_x, size_y, loc, rot=(0, 0, 0), mat=None):
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (size_x, size_y, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # world-size UVs: 1 UV unit = 1 m
    uv = ob.data.uv_layers.active.data
    for loop in ob.data.loops:
        v = ob.data.vertices[loop.vertex_index].co
        uv[loop.index].uv = (v.x + size_x / 2, v.y + size_y / 2)
    if mat:
        ob.data.materials.append(mat)
    return ob


def label(text, loc, size=0.12):
    cu = bpy.data.curves.new("lbl_" + text, "FONT")
    cu.body = text
    cu.size = size
    cu.align_x = "CENTER"
    ob = bpy.data.objects.new("lbl_" + text, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (1.5708, 0, 0)
    m = bpy.data.materials.get("hr_label") or bpy.data.materials.new("hr_label")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1)
    b.inputs["Emission Color"].default_value = (0.9, 0.9, 0.9, 1)
    b.inputs["Emission Strength"].default_value = 1.0
    cu.materials.append(m)
    return ob


def camera(loc, rot, ortho=None, lens=35):
    cd = bpy.data.cameras.new("cam")
    if ortho:
        cd.type = "ORTHO"
        cd.ortho_scale = ortho
    else:
        cd.lens = lens
    ob = bpy.data.objects.new("cam", cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.scene.camera = ob
    return ob


def render(path):
    sc = bpy.context.scene
    sc.render.filepath = str(path)
    sc.render.image_settings.file_format = "PNG"
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    return round(time.time() - t0, 1)


def swatches():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    dusk_scene()
    names = list(TILING) + ["hr_glass", "hr_glass_lit", "hr_lamp_emit", "hr_upvc_white", "hr_paint_yellow",
                            "hr_plastic_black", "hr_plastic_green", "hr_door_paint", "hr_signage", "hr_window_interior"]
    cols, gap, s = 8, 1.25, 1.0
    rows = (len(names) + cols - 1) // cols
    for i, n in enumerate(names):
        r, c = divmod(i, cols)
        x = (c - (cols - 1) / 2) * gap
        z = ((rows - 1) / 2 - r) * gap * 1.18
        mat = bpy.data.materials[n]
        if n == "hr_window_interior":
            ob = plane("sw_" + n, s, s, (x, 0, z), (1.5708, 0, 0), mat)
            for li, loop in enumerate(ob.data.loops):  # one atlas cell (row 0, col 2)
                u, v = ob.data.uv_layers.active.data[loop.index].uv
                ob.data.uv_layers.active.data[loop.index].uv = ((2 + u) / 8, (3 + v) / 4)
        else:
            plane("sw_" + n, s, s, (x, 0, z), (1.5708, 0, 0), mat)
        label(n.replace("hr_", ""), (x, -0.01, z - 0.62), 0.1)
    # a sphere row hint for metals: small spheres in front of steel swatches
    for n in ("hr_steel_black", "hr_steel_galv", "hr_steel_aged"):
        sw = bpy.data.objects["sw_" + n]
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(sw.location.x + 0.3, -0.25, sw.location.z - 0.25), segments=48, ring_count=24)
        sp = bpy.context.active_object
        bpy.ops.object.shade_smooth()
        sp.data.materials.append(bpy.data.materials[n])
    backing = plane("backing", 11, 6, (0, 0.02, 0), (1.5708, 0, 0), None)
    bm = bpy.data.materials.new("hr_backing")
    bm.use_nodes = True
    bm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.02, 0.02, 0.022, 1)
    backing.data.materials.append(bm)
    warm_point((-2.5, -2.2, 3.4), 2200, 0.2)
    camera((0, -14, 0), (1.5708, 0, 0), ortho=10.6)
    PREVIEW.mkdir(parents=True, exist_ok=True)
    return render(PREVIEW / "tex-swatches.png")


def tiling():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    dusk_scene()
    names = ["hr_brick_stock", "hr_brick_red", "hr_concrete_board", "hr_render",
             "hr_paving", "hr_pavers_red", "hr_asphalt", "hr_grass_ground"]
    size, gap = 8.0, 0.4
    for i, n in enumerate(names):
        r, c = divmod(i, 4)
        x = (c - 1.5) * (size + gap)
        z = (0.5 - r) * (size + gap * 3)
        plane("tl_" + n, size, size, (x, 0, z), (1.5708, 0, 0), bpy.data.materials[n])
        label(n.replace("hr_", "") + "  (8 m = %d tiles)" % int(size / TILING[n]), (x, -0.01, z - size / 2 - 0.55), 0.4)
    warm_point((0, -9, 4), 9000, 0.3)
    bpy.context.scene.view_settings.exposure = 1.0
    camera((0, -60, 0), (1.5708, 0, 0), ortho=35.0)
    return render(PREVIEW / "tex-tiling.png")


def decal_board():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    dusk_scene()
    M = bpy.data.materials
    plane("wall", 6, 3, (0, 0, 1.5), (1.5708, 0, 0), M["hr_brick_stock"])
    plane("ground", 6, 4, (0, -2, 0), (0, 0, 0), M["hr_paving"])
    plane("road", 6, 3, (0, -5.5, 0), (0, 0, 0), M["hr_asphalt"])
    def dplane(n, w, h, loc, rot, mat, uvrect=None):
        ob = plane(n, w, h, loc, rot, mat)
        uvl = ob.data.uv_layers.active.data
        for loop in ob.data.loops:
            u, v = uvl[loop.index].uv
            u, v = u / w, v / h
            if uvrect:
                u0, v0, u1, v1 = uvrect
                u, v = u0 + u * (u1 - u0), v0 + v * (v1 - v0)
            uvl[loop.index].uv = (u, v)
        return ob
    dplane("d_moss", 6, 0.8, (0, -0.004, 0.4), (1.5708, 0, 0), M["hr_decal_moss"], (0, 0, 6, 1))
    dplane("d_rain", 1.0, 1.0, (-1.6, -0.004, 0.62), (1.5708, 0, 0), M["hr_decal_rain_streaks"], (0, 0, 2, 1))
    dplane("d_graf", 1.6, 1.6, (1.4, -0.006, 1.3), (1.5708, 0, 0), M["hr_decal_graffiti"], (0, 0.5, 0.5, 1.0))
    dplane("d_grime", 1.6, 1.6, (0.0, -0.005, 2.2), (1.5708, 0, 0), M["hr_decal_grime"])
    dplane("d_puddle", 2.0, 2.0, (-1.4, -2.2, 0.004), (0, 0, 0), M["hr_decal_puddle"])
    dplane("d_leaf", 2.0, 2.0, (1.6, -1.8, 0.004), (0, 0, 0), M["hr_decal_leaf_stains"])
    dplane("d_drain", 0.5, 0.5, (0.4, -3.8, 0.004), (0, 0, 0), M["hr_decal_drain"])
    dplane("d_yellow", 0.5, 6.0, (-1.0, -5.0, 0.004), (0, 0, 1.5708), M["hr_decal_line_yellow"], (0, 0, 1, 6))
    sill = plane("window", 1.2, 1.5, (-1.6, -0.003, 1.9), (1.5708, 0, 0), M["hr_window_interior"])
    for loop in sill.data.loops:
        u, v = sill.data.uv_layers.active.data[loop.index].uv
        sill.data.uv_layers.active.data[loop.index].uv = ((1 + u / 1.2) / 8, (2 + v / 1.5) / 4)
    warm_point((0.5, -2.5, 3.2), 1800, 0.2)
    camera((0.6, -10.5, 2.4), (1.38, 0, 0), lens=30)
    return render(PREVIEW / "tex-decals.png")


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    mats = build_all()
    build_s = round(time.time() - t0, 1)
    gl = gltf_test()
    renders = {}
    only = next((a.split("=", 1)[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
    if "--no-render" not in sys.argv:
        for key, fn in (("tex-swatches.png", swatches), ("tex-tiling.png", tiling), ("tex-decals.png", decal_board)):
            if only is None or key.split("-")[1].split(".")[0] in only:
                renders[key] = fn()
    old = json.loads(MANIFEST.read_text()).get("previews", {}) if MANIFEST.exists() else {}
    data = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    matrecs = []
    for name in list(TILING) + list(PLAIN) + list(DECALS) + list(ATLAS):
        r = {"name": name}
        if name in TILING:
            r.update(kind="tiling", coverageMetres=TILING[name], mappingScale=1.0 / TILING[name],
                     maps=["%s-%s.webp" % (name, s) for s in ("color", "normal", "orm")])
        elif name in PLAIN:
            d = PLAIN[name]
            r.update(kind="plain", baseColorLinear=list(d["base"]), roughness=d["rough"], metallic=d["metal"], note=d["note"])
            if "emit" in d:
                r["emission"] = {"colorLinear": list(d["emit"][0][:3]), "strength": d["emit"][1], "note": K2700_SRGB_NOTE}
        elif name in DECALS:
            d = DECALS[name]
            r.update(kind="decal", alphaMode=d["alpha"], maps=[v for k, v in d.items() if k in ("color", "normal", "orm")],
                     uv="0-1 over the decal quad (Mapping scale 1)")
        else:
            d = ATLAS[name]
            r.update(kind="atlas", maps=[d["color"], d["emit"]], emissionStrength=d["strength"], note=d["note"],
                     coverageMetres=d["coverage"])
        matrecs.append(r)
    sizes = {}
    total = 0
    # this kit's files only (foliage/ and props/ belong to the other kits)
    mine = [p for p in sorted(TEX.rglob("*.webp")) if p.parent.name in ("heron", "decals", "windows", "backdrop")]
    for p in mine:
        sizes[str(p.relative_to(REPO))] = p.stat().st_size
        total += p.stat().st_size
    data["materials"] = matrecs
    data["blend"] = {"path": str(BLEND.relative_to(REPO)), "bytes": BLEND.stat().st_size, "imagesPacked": True,
                     "materialCount": len(matrecs), "buildSeconds": build_s,
                     "graph": "UV Map -> Mapping (Point, scale 1/coverage) -> Image Texture; normal via Normal Map node; ORM via Separate Color (R -> glTF Material Output.Occlusion, G -> Roughness, B -> Metallic)"}
    data["gltfExportTest"] = gl
    prev = {k: {"path": str(PREVIEW / k), "renderSeconds": v,
                            "settings": "Cycles CPU, 960 x 640, 64 samples, OpenImageDenoise, AgX; world RGB (0.05, 0.075, 0.16) x 1.6 plus one 2700 K point light"}
                        for k, v in renders.items()}
    data["previews"] = {**old, **prev}
    data["webpTotalBytes"] = total
    data["webpFiles"] = sizes
    data["generator"] = ["scripts/maps/art/heron_tex_common.py", "scripts/maps/art/make_heron_textures.py",
                         "scripts/maps/art/make_heron_decals.py", "scripts/maps/art/make_heron_materials.py"]
    with open(MANIFEST, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(json.dumps({"build_s": build_s, "renders": renders, "webpTotalBytes": total, "blendBytes": BLEND.stat().st_size}, indent=1))
    print(json.dumps(gl, indent=1)[:6000])


if __name__ == "__main__":
    main()
