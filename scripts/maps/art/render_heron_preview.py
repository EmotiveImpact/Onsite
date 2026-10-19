"""Cycles preview stills of the authored Heron Reach file (inspection renders, not gameplay).

    python3 scripts/maps/art/render_heron_preview.py OUT_DIR [view ...] [--samples N] [--size WxH]

Views are named camera positions in map coordinates. Lighting is a blue-hour approximation for
judging geometry and materials; the game's own lighting lives in the Three.js view.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from heron_art_mesh import bl  # noqa: E402
from heron_art_materials import ROOT  # noqa: E402

VIEWS = {
    # name: (eye x, y, z), (target x, y, z), lens mm
    'aerial': ((-22, 52, 142), (72, 0, 58), 30),
    'garden-court': ((58, 1.7, 33), (80, 3.5, 18), 22),
    'cage': ((46, 1.7, 52), (74, 1.5, 63), 22),
    'washhouse': ((84, 1.7, 108), (66, 3, 88), 22),
    'west-yard': ((4, 1.7, 52), (30, 4, 62), 22),
    'gallery': ((30, 4.7, 37.6), (60, 4.2, 37.6), 22),
    'undercroft': ((60, -1.3, 60), (80, -1.5, 66), 20),
    'rowan-north': ((30, 1.7, 6), (46, 4.5, 20), 20),
    'block-oblique': ((10, 14, 4), (42, 3, 27), 24),
    'roof': ((14, 10.7, 14), (60, 6, 50), 22),
}


def kelvin_rgb(k):
    t = k / 100
    r = 255 if t <= 66 else 329.7 * (t - 60) ** -0.1332
    g = 99.47 * math.log(t) - 161.1 if t <= 66 else 288.1 * (t - 60) ** -0.0755
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5 * math.log(t - 10) - 305.0)
    return tuple(max(0, min(255, c)) / 255 for c in (r, g, b))


def setup(samples, size):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 4
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = 0.6

    world = bpy.data.worlds.new('blue hour')
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new('ShaderNodeTexSky')
    try:
        sky.sky_type = 'NISHITA'
    except TypeError:
        pass
    if hasattr(sky, 'sun_elevation'):
        sky.sun_elevation = math.radians(-1.5)
        sky.sun_rotation = math.radians(250)
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = 1.6
    tint = nt.nodes.new('ShaderNodeMix')
    tint.data_type = 'RGBA'
    tint.blend_type = 'MULTIPLY'
    tint.inputs['Factor'].default_value = .5
    tint.inputs['B'].default_value = (.35, .5, 1.0, 1)
    out = nt.nodes.new('ShaderNodeOutputWorld')
    nt.links.new(sky.outputs['Color'], tint.inputs['A'])
    nt.links.new(tint.outputs['Result'], bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])

    L = json.load(open(os.path.join(ROOT, 'assets', 'blender', 'heron-reach', 'layout.json')))
    col = bpy.data.collections.new('PREVIEW_LIGHTS')
    scene.collection.children.link(col)
    for li in L['lights']:
        d = bpy.data.lights.new(li['id'], 'POINT')
        d.energy = 900 if li['kind'] == 'street' else 300
        d.color = kelvin_rgb(li.get('kelvin', 2700))
        d.shadow_soft_size = .15
        o = bpy.data.objects.new(li['id'], d)
        o.location = bl(li['x'], li['y'] - .3, li['z'])
        col.objects.link(o)
    return scene


def camera(scene, name, eye, target, lens):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_end = 1000
    o = bpy.data.objects.new(name, cam)
    scene.collection.objects.link(o)
    o.location = bl(*eye)
    o.rotation_euler = (Vector(bl(*target)) - Vector(bl(*eye))).to_track_quat('-Z', 'Y').to_euler()
    return o


def main():
    args = sys.argv[1:]
    samples, size = 48, (960, 540)
    if '--samples' in args:
        i = args.index('--samples')
        samples = int(args[i + 1])
        del args[i:i + 2]
    if '--size' in args:
        i = args.index('--size')
        size = tuple(int(v) for v in args[i + 1].split('x'))
        del args[i:i + 2]
    out_dir = args[0]
    names = args[1:] or ['aerial', 'garden-court', 'cage']
    bpy.ops.wm.open_mainfile(filepath=os.path.join(ROOT, 'assets', 'blender', 'heron-reach', 'heron-reach.blend'))
    scene = setup(samples, size)
    os.makedirs(out_dir, exist_ok=True)
    for n in names:
        eye, target, lens = VIEWS[n]
        scene.camera = camera(scene, n, eye, target, lens)
        scene.render.filepath = os.path.join(out_dir, f'{n}.png')
        bpy.ops.render.render(write_still=True)
        print('rendered', scene.render.filepath)


if __name__ == '__main__':
    main()
