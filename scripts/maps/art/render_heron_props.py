"""Preview renders for the Heron Reach props kit (Cycles CPU).

    python3 scripts/maps/art/render_heron_props.py inspect OUT.png NAME,NAME,...  [--blend PATH] [--angle DEG]
    python3 scripts/maps/art/render_heron_props.py final OUT_DIR [street,cage,shop,interiors,vehicles]

The final scenes are blue-hour set dressing for review only; nothing here is saved
back into the kit. If the texture kit's materials.blend exists, its shared
materials are linked by name for the previews; otherwise the kit placeholders are
used with a light render-only grime overlay.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
KIT = os.path.join(ROOT, "assets", "blender", "heron-reach", "props-kit.blend")
SHARED_MATS = os.path.join(ROOT, "assets", "blender", "heron-reach", "materials.blend")


def load_kit(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    scene = bpy.context.scene
    # hide the source collections; we place instances instead
    for lc in bpy.context.view_layer.layer_collection.children:
        lc.exclude = False
        lc.hide_viewport = False
    root = bpy.data.collections.get("HERON_PROPS")
    if root and root.name in scene.collection.children:
        scene.collection.children.unlink(root)
    return scene


def instance(name, loc=(0, 0, 0), rot_z=0.0, parent=None):
    col = bpy.data.collections[name]
    e = bpy.data.objects.new(f"inst_{name}", None)
    e.instance_type = "COLLECTION"
    e.instance_collection = col
    e.location = loc
    e.rotation_euler = (0, 0, math.radians(rot_z))
    (parent or bpy.context.scene.collection).objects.link(e)
    return e


def asset_size(name):
    ob = bpy.data.collections[name].objects[0]
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def cycles(scene, w, h, samples):
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    try:
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    scene.cycles.max_bounces = 6
    scene.cycles.transparent_max_bounces = 16
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast" if "AgX - Medium High Contrast" in [i.identifier for i in scene.view_settings.bl_rna.properties["look"].enum_items] else "None"
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4


def world(scene, top=(0.020, 0.030, 0.060), bottom=(0.035, 0.040, 0.055), strength=1.0):
    w = bpy.data.worlds.new("blue_hour")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    mapr = nt.nodes.new("ShaderNodeMapRange")
    mapr.inputs["From Min"].default_value = 0.45
    mapr.inputs["From Max"].default_value = 0.85
    nt.links.new(sep.outputs["Z"], mapr.inputs["Value"])
    nt.links.new(mapr.outputs["Result"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].color = (*bottom, 1)
    ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def ground(scene, size=60, color=(0.05, 0.05, 0.055), rough=0.32, z=0.0, name="ground"):
    me = bpy.data.meshes.new(name)
    s = size / 2
    me.from_pydata([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    m = bpy.data.materials.new(name + "_mat")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    nt = m.node_tree
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.8
    noise.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.42
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[0].color = (rough * 0.55, rough * 0.55, rough * 0.55, 1)
    ramp.color_ramp.elements[1].color = (min(1, rough * 1.9), min(1, rough * 1.9), min(1, rough * 1.9), 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Roughness"])
    # paving joints
    tc = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.0
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Mortar Size"].default_value = 0.006
    brick.inputs["Brick Width"].default_value = 0.6
    brick.inputs["Row Height"].default_value = 0.6
    brick.inputs["Color1"].default_value = (*color, 1)
    brick.inputs["Color2"].default_value = (color[0] * 1.15, color[1] * 1.15, color[2] * 1.12, 1)
    brick.inputs["Mortar"].default_value = (color[0] * 0.5, color[1] * 0.5, color[2] * 0.5, 1)
    nt.links.new(tc.outputs["Object"], brick.inputs["Vector"])
    nt.links.new(brick.outputs["Color"], b.inputs["Base Color"])
    me.materials.append(m)
    return ob


def wall(scene, x0, x1, y, z1, color=(0.16, 0.10, 0.07), name="wall"):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x0, y, 0), (x1, y, 0), (x1, y, z1), (x0, y, z1)], [], [(0, 3, 2, 1)])
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    m = bpy.data.materials.new(name + "_mat")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = 1.0
    brick.inputs["Brick Width"].default_value = 0.225
    brick.inputs["Row Height"].default_value = 0.075
    brick.inputs["Mortar Size"].default_value = 0.008
    brick.inputs["Color1"].default_value = (*color, 1)
    brick.inputs["Color2"].default_value = (color[0] * 1.3, color[1] * 1.2, color[2] * 1.1, 1)
    brick.inputs["Mortar"].default_value = (0.10, 0.095, 0.085, 1)
    nt.links.new(mp.outputs["Vector"], brick.inputs["Vector"])
    nt.links.new(brick.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    me.materials.append(m)
    return ob


def point(scene, loc, energy, color=(1.0, 0.62, 0.32), radius=0.05, name="lamp"):
    ld = bpy.data.lights.new(name, "POINT")
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    scene.collection.objects.link(ob)
    return ob


def area(scene, loc, rot, energy, size=4.0, color=(0.55, 0.65, 0.95), name="fill"):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.color = color
    ld.size = size
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = [math.radians(r) for r in rot]
    scene.collection.objects.link(ob)
    return ob


def camera(scene, loc, target, lens=35):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.clip_start = 0.02
    ob = bpy.data.objects.new("cam", cd)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(ob)
    scene.camera = ob
    return ob


def link_shared_materials(extra=()):
    """Swap kit placeholders for the texture kit's materials, by name, if present.

    Names in extra (ground, wall and court materials for set dressing) are appended too.
    """
    if not os.path.exists(SHARED_MATS):
        return []
    names = [m.name for m in bpy.data.materials if m.name.startswith("hr_") and not m.name.startswith("hr_prop_")]
    names += [n for n in extra if n not in names]
    with bpy.data.libraries.load(SHARED_MATS, link=False) as (src, dst):
        avail = set(src.materials)
        want = [n for n in names if n in avail]
        dst.materials = want
    swapped = []
    for new in dst.materials:
        if new is None:
            continue
        base = new.name.rsplit(".", 1)[0]
        old = bpy.data.materials.get(base)
        if old is None:
            new.name = base
            continue
        if old != new:
            old.user_remap(new)
            swapped.append(base)
    return swapped


def grime_placeholders():
    """Render-only: add subtle colour and roughness breakup to flat placeholders."""
    for m in bpy.data.materials:
        if not m.name.startswith("hr_") or not m.use_nodes:
            continue
        nt = m.node_tree
        b = nt.nodes.get("Principled BSDF")
        if b is None or b.inputs["Base Color"].is_linked:
            continue
        col = list(b.inputs["Base Color"].default_value)
        rough = b.inputs["Roughness"].default_value
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 9.0
        nz.inputs["Detail"].default_value = 8.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[0].color = (col[0] * 0.75, col[1] * 0.75, col[2] * 0.75, 1)
        ramp.color_ramp.elements[1].color = (min(1, col[0] * 1.3 + 0.01), min(1, col[1] * 1.3 + 0.01), min(1, col[2] * 1.25 + 0.01), 1)
        nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
        rr = nt.nodes.new("ShaderNodeMapRange")
        rr.inputs["To Min"].default_value = max(0.0, rough - 0.15)
        rr.inputs["To Max"].default_value = min(1.0, rough + 0.15)
        nt.links.new(nz.outputs["Fac"], rr.inputs["Value"])
        nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])


def inspect(out, names, angle=-35.0, blend=KIT, samples=24, w=960, h=540, light="studio", cam=None, target=None, lens=40, wall_y=None):
    scene = load_kit(blend)
    cycles(scene, w, h, samples)
    world(scene, (0.25, 0.27, 0.30), (0.20, 0.20, 0.21), 1.0)
    ground(scene, 60, (0.18, 0.18, 0.18), 0.6)
    sizes = [asset_size(n) for n in names]
    gap = 0.35
    total = sum((s[1] - s[0]) for s in sizes) + gap * (len(names) - 1)
    x = -total / 2
    hmax = max(s[5] for s in sizes)
    for n, s in zip(names, sizes):
        wdt = s[1] - s[0]
        instance(n, (x - s[0], 0, 0))
        x += wdt + gap
    area(scene, (-3, -6, 7), (50, 0, -25), 1500, 6, (1, 0.97, 0.93), "key")
    area(scene, (6, 3, 4), (60, 0, 120), 400, 6, (0.8, 0.85, 1.0), "rim")
    ymin = min(s[2] for s in sizes)
    fov_h = 2 * math.atan(18.0 / 40.0)
    fov_v = 2 * math.atan(18.0 / 40.0 * h / w)
    dist = max((total / 2) / math.tan(fov_h / 2), (hmax / 2) / math.tan(fov_v / 2)) * 1.12 + abs(ymin)
    a = math.radians(angle)
    el = math.radians(14)
    cam_loc = (math.sin(a) * dist * math.cos(el), -math.cos(a) * dist * math.cos(el), hmax * 0.5 + dist * math.sin(el))
    if cam is not None:
        cam_loc = cam
    camera(scene, cam_loc, target if target is not None else (0, 0, hmax * 0.5), lens)
    if wall_y is not None:
        wall(scene, -20, 20, wall_y, 6)
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[0] == "inspect":
        blend = KIT
        angle = -35.0
        if "--blend" in args:
            blend = args[args.index("--blend") + 1]
        if "--angle" in args:
            angle = float(args[args.index("--angle") + 1])
        def vec(name):
            if name in args:
                return tuple(float(v) for v in args[args.index(name) + 1].split(","))
            return None
        lens = float(args[args.index("--lens") + 1]) if "--lens" in args else 40
        wy = float(args[args.index("--wall") + 1]) if "--wall" in args else None
        inspect(args[1], args[2].split(","), angle, blend, cam=vec("--cam"), target=vec("--target"), lens=lens, wall_y=wy)
    elif args[0] == "final":
        import render_heron_props_final as F  # noqa: E402
        F.run(args[1], set(args[2].split(",")) if len(args) > 2 else None)
