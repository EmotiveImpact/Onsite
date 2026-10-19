"""Cycles CPU preview renders of the Heron Reach foliage kit.

Run:  python3 scripts/maps/art/render_heron_foliage.py [shot ...] [--out DIR] [--samples N] [--blend PATH]
Shots: plane_a plane_b birch_a birch_b under_plane lineup lod ground hedge
Default output: /mnt/project-files/heron-reach/progress/kit/foliage-<shot>.png

The kit's asset collections are instanced into a separate PREVIEW scene with a blue-hour
gradient sky, damp dark paving and a warm 2700 K street lamp from one side.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BLEND = os.path.join(REPO, "assets", "blender", "heron-reach", "foliage-kit.blend")
OUT = "/mnt/project-files/heron-reach/progress/kit"


def args():
    a = sys.argv[1:]
    shots, out, samples, blend, suffix = [], OUT, 96, BLEND, ""
    i = 0
    while i < len(a):
        if a[i] == "--out":
            out = a[i + 1]; i += 2
        elif a[i] == "--samples":
            samples = int(a[i + 1]); i += 2
        elif a[i] == "--blend":
            blend = a[i + 1]; i += 2
        elif a[i] == "--suffix":
            suffix = a[i + 1]; i += 2
        else:
            shots.append(a[i]); i += 1
    return shots, out, samples, blend, suffix


def world(scene, strength=1.5):
    w = bpy.data.worlds.new("BlueHour")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.010, 0.012, 0.02, 1)
    cr.elements[1].position = 0.5
    cr.elements[1].color = (0.16, 0.15, 0.24, 1)   # horizon glow, muted violet
    e = cr.elements.new(0.56)
    e.color = (0.07, 0.09, 0.20, 1)
    e = cr.elements.new(0.75)
    e.color = (0.03, 0.05, 0.13, 1)
    e = cr.elements.new(1.0)
    e.color = (0.015, 0.025, 0.07, 1)              # deep blue zenith
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def ground(scene, size=60):
    me = bpy.data.meshes.new("ground")
    s = size / 2
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("ground", me)
    scene.collection.objects.link(o)
    m = bpy.data.materials.new("preview_wet_paving")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.05, 0.05, 0.052, 1)
    b.inputs["Roughness"].default_value = 0.45
    # broken wet sheen so the lamp pools rather than mirrors
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.9
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.4
    mr.inputs["From Max"].default_value = 0.65
    mr.inputs["To Min"].default_value = 0.22
    mr.inputs["To Max"].default_value = 0.7
    nt.links.new(nz.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    me.materials.append(m)
    return o


def soil_patch(scene, sx, sy, loc=(0, 0, 0.001)):
    me = bpy.data.meshes.new("soil")
    me.from_pydata([(-sx, -sy, 0), (sx, -sy, 0), (sx, sy, 0), (-sx, sy, 0)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("soil", me)
    o.location = loc
    scene.collection.objects.link(o)
    m = bpy.data.materials.new("preview_soil")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.035, 0.04, 0.02, 1)
    b.inputs["Roughness"].default_value = 0.8
    me.materials.append(m)


def lamp(scene, loc, power=900, radius=0.12):
    ld = bpy.data.lights.new("lamp", "POINT")
    ld.energy = power
    ld.shadow_soft_size = radius
    ld.color = (1.0, 0.62, 0.32)  # about 2700 K
    o = bpy.data.objects.new("lamp", ld)
    o.location = loc
    scene.collection.objects.link(o)
    return o


def cool_fill(scene, rot=(math.radians(60), 0, math.radians(200)), strength=0.45):
    ld = bpy.data.lights.new("skyfill", "SUN")
    ld.energy = strength
    ld.angle = math.radians(40)
    ld.color = (0.55, 0.65, 1.0)
    o = bpy.data.objects.new("skyfill", ld)
    o.rotation_euler = rot
    scene.collection.objects.link(o)


def camera(scene, loc, target, lens=35):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    o = bpy.data.objects.new("cam", cd)
    o.location = loc
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(o)
    scene.camera = o


def inst(scene, cname, loc=(0, 0, 0), rot=0.0, scale=1.0):
    c = bpy.data.collections[cname]
    e = bpy.data.objects.new("inst_" + cname, None)
    e.instance_type = "COLLECTION"
    e.instance_collection = c
    e.location = loc
    e.rotation_euler = (0, 0, rot)
    e.scale = (scale, scale, scale)
    scene.collection.objects.link(e)
    return e


def new_scene(samples):
    sc = bpy.data.scenes.new("PREVIEW")
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.transparent_max_bounces = 64
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.render.resolution_x = 960
    sc.render.resolution_y = 640
    sc.render.resolution_percentage = 100
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 4
    sc.render.image_settings.file_format = "PNG"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = 0.0
    return sc


def shot(name, samples):
    sc = new_scene(samples)
    world(sc)
    ground(sc)
    if name in ("plane_a", "plane_b", "birch_a", "birch_b"):
        cname = {"plane_a": "TREE_PLANE_A", "plane_b": "TREE_PLANE_B", "birch_a": "TREE_BIRCH_A",
                 "birch_b": "TREE_BIRCH_B"}[name]
        inst(sc, cname)
        soil_patch(sc, 1.2, 1.2)
        inst(sc, "GRASS_PATCH_1M", (0.6, -0.6, 0))
        inst(sc, "GRASS_PATCH_1M", (-0.5, -0.4, 0), math.pi / 2)
        inst(sc, "LEAF_LITTER_B", (1.6, -1.2, 0))
        lamp(sc, (-4.2, -3.0, 5.2), power=1400)
        cool_fill(sc)
        camera(sc, (1.0, -12.5, 1.65), (0.0, 0.0, 3.75), lens=33)
    elif name == "under_plane":
        inst(sc, "TREE_PLANE_A")
        soil_patch(sc, 1.2, 1.2)
        inst(sc, "GRASS_PATCH_1M", (0.6, -0.6, 0))
        lamp(sc, (-4.2, -3.0, 5.2), power=1400)
        cool_fill(sc)
        camera(sc, (1.5, -4.2, 1.65), (-0.2, 0.6, 4.6), lens=22)
    elif name == "lineup":
        for k, (c, x) in enumerate((("TREE_PLANE_A", -10.5), ("TREE_PLANE_B", -3.6), ("TREE_BIRCH_A", 2.6),
                                   ("TREE_BIRCH_B", 7.8))):
            inst(sc, c, (x, 0, 0))
        lamp(sc, (-1.0, -4.0, 5.2), power=2200)
        cool_fill(sc)
        camera(sc, (-1.2, -24, 1.7), (-1.2, 0, 3.9), lens=30)
    elif name == "lod":
        for c, x in (("TREE_PLANE_A", -9.0), ("TREE_PLANE_A_LOD1", -3.2), ("TREE_BIRCH_A", 2.8),
                     ("TREE_BIRCH_A_LOD1", 7.6)):
            inst(sc, c, (x, 0, 0))
        lamp(sc, (-1.0, -4.0, 5.2), power=2200)
        cool_fill(sc)
        camera(sc, (-0.7, -22, 1.7), (-0.7, 0, 3.9), lens=30)
    elif name == "ground":
        soil_patch(sc, 1.0, 0.9, (-0.6, 0.3, 0.001))
        for gx in (-1, 0):
            for gy in (0, 1):
                inst(sc, "GRASS_PATCH_1M", (gx - 0.1, gy - 0.2, 0), (gx + gy) * math.pi / 2)
        inst(sc, "GRASS_EDGE_1M", (-0.6, -0.8, 0))
        inst(sc, "GRASS_EDGE_1M", (0.4, -0.8, 0), math.pi)
        inst(sc, "LEAF_LITTER_A", (0.95, -0.55, 0), 0)
        inst(sc, "LEAF_LITTER_C", (0.9, 0.5, 0), 1.0)
        inst(sc, "WEED_TUFT_A", (0.55, -1.15, 0))
        inst(sc, "WEED_TUFT_B", (1.25, -1.1, 0), 0.6)
        inst(sc, "WEED_TUFT_C", (1.5, 0.05, 0), 2.0)
        inst(sc, "WEED_TUFT_B", (0.2, -1.35, 0), 2.0)
        lamp(sc, (1.6, -1.9, 2.4), power=420)
        cool_fill(sc, strength=0.45)
        camera(sc, (0.35, -2.55, 1.15), (0.35, -0.15, 0.0), lens=32)
    elif name == "hedge":
        inst(sc, "HEDGE_END", (-1.5, 0.6, 0), math.pi)
        inst(sc, "HEDGE_1M", (-0.5, 0.6, 0))
        inst(sc, "HEDGE_1M", (0.5, 0.6, 0))
        inst(sc, "HEDGE_END", (1.5, 0.6, 0))
        soil_patch(sc, 2.3, 0.5, (0, -0.35, 0.001))
        inst(sc, "SHRUB_A", (-1.2, -0.35, 0))
        inst(sc, "SHRUB_B", (0.1, -0.4, 0), 1.0)
        inst(sc, "SHRUB_C", (1.25, -0.3, 0), 2.0)
        inst(sc, "GRASS_EDGE_1M", (-0.6, -0.95, 0))
        inst(sc, "GRASS_EDGE_1M", (0.6, -0.95, 0), math.pi)
        lamp(sc, (2.6, -2.4, 2.8), power=650)
        cool_fill(sc, strength=0.5)
        camera(sc, (-1.3, -3.6, 1.45), (0.2, 0.2, 0.42), lens=30)
    return sc


def main():
    shots, out, samples, blend, suffix = args()
    shots = shots or ["plane_a", "plane_b", "birch_a", "birch_b", "under_plane", "lineup", "lod", "ground", "hedge"]
    os.makedirs(out, exist_ok=True)
    for s in shots:
        bpy.ops.wm.open_mainfile(filepath=blend)
        sc = shot(s, samples)
        sc.render.filepath = os.path.join(out, "foliage-%s%s.png" % (s.replace("_", "-"), suffix))
        bpy.ops.render.render(write_still=True, scene=sc.name)
        print("rendered", sc.render.filepath)


if __name__ == "__main__":
    main()
