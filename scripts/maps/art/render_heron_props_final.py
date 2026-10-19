"""Blue-hour preview scenes for the props kit. Called by render_heron_props.py final OUT_DIR.

Review renders only. The scenes are set dressing around kit instances; nothing is
written back into props-kit.blend.
"""

import math
import os
import sys

import bpy
from mathutils import Vector

import render_heron_props as RP

WARM = (1.0, 0.60, 0.30)      # about 2700 K
SHOP_WARM = (1.0, 0.78, 0.55)  # about 3500 K
COOL = (0.55, 0.66, 1.0)
DRESSING = ("hr_paving", "hr_asphalt", "hr_brick_stock", "hr_court", "hr_plaster", "hr_concrete_rough")


def mat(name):
    return bpy.data.materials.get(name)


def plane(scene, name, x0, x1, y0, y1, z, material, flip=False):
    me = bpy.data.meshes.new(name)
    verts = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    faces = [(0, 3, 2, 1)] if flip else [(0, 1, 2, 3)]
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for li, loop in enumerate(me.loops):
        co = me.vertices[loop.vertex_index].co
        uv.data[li].uv = (co.x, co.y)
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def vwall(scene, name, x0, x1, y, z0, z1, material, facing=-1):
    """Vertical wall in XZ at y, facing -Y (facing=-1) or +Y."""
    me = bpy.data.meshes.new(name)
    verts = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
    faces = [(0, 1, 2, 3)] if facing < 0 else [(0, 3, 2, 1)]
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for li, loop in enumerate(me.loops):
        co = me.vertices[loop.vertex_index].co
        uv.data[li].uv = (co.x, co.z)
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def xwall(scene, name, x, y0, y1, z0, z1, material, facing=1):
    """Vertical wall in YZ at x, facing +X (facing=1) or -X."""
    me = bpy.data.meshes.new(name)
    verts = [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)]
    faces = [(0, 3, 2, 1)] if facing > 0 else [(0, 1, 2, 3)]
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for li, loop in enumerate(me.loops):
        co = me.vertices[loop.vertex_index].co
        uv.data[li].uv = (co.y, co.z)
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def put(name, x, y, z=0.0, rz=0.0):
    return RP.instance(name, (x, y, z), rz)


def setup(samples=96, exposure=0.0):
    scene = RP.load_kit(RP.KIT)
    swapped = RP.link_shared_materials(DRESSING)
    print("shared materials from texture kit:", len(swapped))
    RP.cycles(scene, 960, 640, samples)
    scene.view_settings.exposure = exposure
    RP.world(scene, (0.010, 0.026, 0.110), (0.050, 0.058, 0.085), 1.0)
    return scene


def lamp_light(scene, x, y, z=4.68, energy=260.0):
    # just under the lantern, so the opaque lens geometry does not block it
    RP.point(scene, (x, y, z - 0.45), energy, WARM, 0.12, "column_light")


def scene_street(out):
    scene = setup(96, 0.7)
    paving = mat("hr_paving") or mat("hr_concrete_cast")
    asphalt = mat("hr_asphalt") or paving
    brick = mat("hr_brick_stock") or mat("hr_concrete_cast")
    plane(scene, "pavement", -14, 14, -1.5, 6, 0.125, paving)
    plane(scene, "road", -14, 14, -12, -1.5, 0.0, asphalt)
    vwall(scene, "wall", -14, 14, 2.6, 0.125, 6.0, brick)
    vwall(scene, "wall_back", -14, 14, 2.62, 0.0, 6.0, brick, 1)
    # kerb line along the road edge
    for k in range(-12, 12):
        put("KERB_1M", k + 0.5, -1.5 + 0.0625)
    put("DRAIN_GULLY", -2.3, -1.78, 0.0)
    put("MANHOLE", 3.6, 0.9, 0.128)
    z = 0.125
    # wall-mounted items on the brick wall (wall face at y = 2.6)
    put("WALL_LAMP", -1.2, 2.6, 2.45)
    put("CCTV", 4.6, 2.6, 3.1, 0)
    put("INTERCOM", -0.35, 2.6, 1.45)
    put("AIRBRICK", 1.6, 2.6, 0.35)
    put("AIRBRICK", 2.4, 2.6, 0.35)
    put("VENT_GRILLE", 3.2, 2.6, 2.3)
    put("DOWNPIPE_3M", -2.6, 2.6, z)
    put("SATELLITE_DISH", 5.6, 2.6, 3.4)
    put("AC_UNIT", 2.9, 2.6, 1.0)
    # street furniture line-up on the pavement
    put("LAMP_COLUMN", -3.8, -0.9, z)
    lamp_light(scene, -3.8, -0.9, z + 4.68, 320)
    RP.point(scene, (-1.2, 2.49, 2.45), 22, WARM, 0.06, "wall_light")
    put("BOLLARD", -2.9, -1.1, z)
    put("BOLLARD", -1.8, -1.1, z)
    put("BOLLARD", 1.4, -1.1, z)
    put("LITTER_BIN", -3.0, 0.6, z)
    put("BENCH", -1.0, 1.75, z, 0)
    put("WHEELIE_BIN_240", 0.7, 2.15, z, 180)
    put("WHEELIE_BIN_240_GREEN", 1.4, 2.15, z, 185)
    put("EURO_BIN_1100", 3.0, 1.85, z, 0)
    put("BIN_BAG_C", 4.4, 2.1, z)
    put("BIN_BAG", 0.1, 2.25, z, 30)
    put("CARDBOARD_FLAT", 4.6, 1.2, z, 20)
    put("UTILITY_CABINET", 5.4, 2.15, z, 0)
    put("CYCLE_HOOP", -5.9, 0.7, z, 90)
    put("BIKE", -5.6, 0.7, z, 0)
    put("SIGN_POST", 4.0, -1.0, z)
    put("TRAFFIC_CONE", 2.4, -1.15, z)
    put("CRUSHED_CAN", 0.6, -0.4, z, 40)
    put("CRISP_PACKET", -0.4, 0.2, z, 70)
    for k in range(2):
        put("PLANTER_EDGE", -6.5 + k, 2.2, z)
    for k in range(2):
        put("RAILING_1M", -6.6 + k, -0.9, z)
    put("RAILING_POST", -4.6, -0.9, z)
    put("NOTICE_BOARD", 6.7, 1.9, z, 0)
    RP.area(scene, (2.0, -12.0, 7.0), (60, 0, 0), 320, 14, COOL, "sky_fill")
    RP.camera(scene, (-0.2, -6.2, 1.45), (0.2, 1.0, 1.75), 20)
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


def scene_cage(out):
    scene = setup(96, 0.7)
    court = mat("hr_court") or mat("hr_asphalt")
    paving = mat("hr_paving") or court
    brick = mat("hr_brick_stock")
    plane(scene, "court", -30, 2.5, -1.5, 16, 0.0, court)
    plane(scene, "verge", -30, 2.5, -2, -1.5, 0.0, paving)
    plane(scene, "outside", -30, 14, -12, -2, 0.0, paving)
    plane(scene, "outside2", 2.5, 14, -2, 16, 0.0, paving)
    vwall(scene, "block", -40, 14, 16, 0, 20, brick)
    # corner at (2.5, -1.5): fence along -Y edge running toward -X, and along +X edge running toward +Y
    cx, cy = 2.5, -1.5
    put("CAGE_POST", cx, cy)
    for k in range(4):
        x = cx - 2.5 * (k + 1)
        put("CAGE_PANEL_2_5M", x + 1.25, cy)
        put("CAGE_POST", x, cy)
    # side fence: one panel bay, then the gate (its first post doubles the cage post),
    # then two more bays from the gate's far post
    put("CAGE_PANEL_2_5M", cx, cy + 1.25, 0, 90)
    put("CAGE_POST", cx, cy + 2.5)
    gate_c = cy + 2.5 + 2.05
    put("CAGE_GATE_4M", cx, gate_c, 0, -90)
    y = gate_c + 2.05
    for k in range(2):
        put("CAGE_PANEL_2_5M", cx, y + 1.25, 0, 90)
        y += 2.5
        put("CAGE_POST", cx, y)
    # goal against the near fence, mouth into the court (+Y)
    put("GOAL_FIVE_A_SIDE", -3.2, cy + 0.62, 0, 180)
    put("BALL", -0.6, 3.4, 0)
    put("BENCH", -4.0, -2.8, 0, 180)
    put("LAMP_COLUMN", 4.3, 0.2, 0)
    lamp_light(scene, 4.3, 0.2, 4.68, 340)
    put("LAMP_COLUMN", -7.0, -3.0, 0)
    lamp_light(scene, -7.0, -3.0, 4.68, 260)
    put("LITTER_BIN", 4.6, 1.3, 0)
    put("CRUSHED_CAN", -2.0, 1.0, 0)
    put("CRISP_PACKET", 1.6, 2.2, 0, 120)
    RP.area(scene, (-2.0, -14.0, 9.0), (55, 0, 0), 900, 14, COOL, "sky_fill")
    RP.camera(scene, (5.4, -4.9, 1.6), (-1.0, 2.6, 1.3), 21)
    # court floodlight spill from the block, out of shot
    RP.point(scene, (-2.5, 4.0, 6.5), 1800, WARM, 0.3, "court_flood")
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


def strip_light(scene, x0, x1, y, z, energy=60.0, color=SHOP_WARM):
    ld = bpy.data.lights.new("strip", "AREA")
    ld.shape = "RECTANGLE"
    ld.size = abs(x1 - x0)
    ld.size_y = 0.12
    ld.energy = energy
    ld.color = color
    ob = bpy.data.objects.new("strip", ld)
    ob.location = ((x0 + x1) / 2, y, z)
    scene.collection.objects.link(ob)
    em = bpy.data.materials.get("strip_emit") or bpy.data.materials.new("strip_emit")
    em.use_nodes = True
    b = em.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*color, 1)
    b.inputs["Emission Strength"].default_value = 6.0
    me = bpy.data.meshes.new("strip_mesh")
    me.from_pydata([(x0, y - 0.06, z + 0.01), (x1, y - 0.06, z + 0.01), (x1, y + 0.06, z + 0.01), (x0, y + 0.06, z + 0.01)], [], [(0, 3, 2, 1)])
    me.materials.append(em)
    so = bpy.data.objects.new("strip_geo", me)
    scene.collection.objects.link(so)


def floor_vinyl():
    m = bpy.data.materials.new("render_vinyl")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = 0.30
    br.inputs["Row Height"].default_value = 0.30
    br.offset = 0.0
    br.inputs["Mortar Size"].default_value = 0.002
    br.inputs["Color1"].default_value = (0.20, 0.19, 0.17, 1)
    br.inputs["Color2"].default_value = (0.16, 0.15, 0.135, 1)
    br.inputs["Mortar"].default_value = (0.08, 0.08, 0.07, 1)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    return m


def scene_shop(out):
    scene = setup(96, 0.4)
    plaster = mat("hr_plaster") or mat("hr_concrete_cast")
    vinyl = floor_vinyl()
    # 9 m deep, 18 m wide shop; we frame one corner of it
    plane(scene, "floor", -9, 9, -4.5, 4.5, 0.0, vinyl)
    plane(scene, "ceiling", -9, 9, -4.5, 4.5, 3.0, plaster, flip=True)
    vwall(scene, "back", -9, 9, 4.5, 0, 3.0, plaster)
    xwall(scene, "side", 2.2, -4.5, 4.5, 0, 3.0, plaster, -1)
    xwall(scene, "side_l", -9, -4.5, 4.5, 0, 3.0, plaster, 1)
    # shelving run along the back wall, fridges in the corner, counter by the door
    for k in range(5):
        put("SHOP_SHELF_UNIT", -5.6 + 1.2 * k, 4.5 - 0.25)
    put("SHOP_FRIDGE", 0.7 - 0.0, 4.5 - 0.40)
    put("SHOP_FRIDGE", 1.55, 2.6, 0, -90)
    put("SHOP_SHELF_UNIT", 1.95, 1.0, 0, -90)
    put("SHOP_SHELF_UNIT", 1.95, -0.2, 0, -90)
    put("SHOP_COUNTER", -2.2, -1.6, 0, 180)
    put("CHAIR_STACKING", -3.6, -2.2, 0, 160)
    # island gondola: two bays back to back on each side
    for x in (-5.4, -4.2):
        put("SHOP_SHELF_UNIT", x, 0.75)
        put("SHOP_SHELF_UNIT", x, 1.25, 0, 180)
    for k, x in enumerate((-6.0, -3.0, 0.0)):
        strip_light(scene, x - 0.6, x + 0.6, 2.2, 2.98, 70)
        strip_light(scene, x - 0.6, x + 0.6, -0.8, 2.98, 70)
    RP.camera(scene, (-6.6, -3.6, 1.65), (-0.6, 2.8, 1.05), 22)
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


def scene_interiors(out):
    scene = setup(80, 0.4)
    plaster = mat("hr_plaster") or mat("hr_concrete_cast")
    vinyl = floor_vinyl()
    plane(scene, "floor", -9, 9, -4.5, 4.5, 0.0, vinyl)
    plane(scene, "ceiling", -9, 9, -4.5, 4.5, 3.0, plaster, flip=True)
    vwall(scene, "back", -9, 9, 4.5, 0, 3.0, plaster)
    xwall(scene, "side_r", 4.0, -4.5, 4.5, 0, 3.0, plaster, -1)
    # launderette run on the back wall, workshop and youth club pieces in front
    xs = -4.6
    for k in range(3):
        put("WASHING_MACHINE", xs + 0.75 * k, 4.5 - 0.42)
    put("TUMBLE_DRYER", xs + 2.4, 4.5 - 0.47)
    put("TUMBLE_DRYER", xs + 3.25, 4.5 - 0.47)
    put("LAUNDRY_CAGE", xs + 1.0, 3.2, 0, 10)
    put("WORK_BENCH", 3.6, 2.0, 0, -90)
    put("BIKE", 2.6, 0.4, 0, 70)
    put("YOUTH_SOFA", -2.9, -0.2, 0, 20)
    put("POOL_TABLE", 0.6, -0.2, 0, 8)
    put("TABLE_FOLDING", -4.2, 1.2, 0, 90)
    put("CHAIR_STACKING", -4.9, 1.6, 0, 80)
    put("CHAIR_STACKING", -3.5, 0.9, 0, -100)
    put("ESTATE_OFFICE_DESK", 2.9, -0.6, 0, -90)
    for x in (-4.0, -1.0, 2.0):
        strip_light(scene, x - 0.6, x + 0.6, 2.5, 2.98, 60)
        strip_light(scene, x - 0.6, x + 0.6, -1.0, 2.98, 60)
    RP.camera(scene, (-0.9, -3.3, 1.55), (-0.4, 2.5, 0.95), 21)
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


def scene_vehicles(out):
    scene = setup(96, 0.7)
    asphalt = mat("hr_asphalt")
    paving = mat("hr_paving")
    brick = mat("hr_brick_stock")
    plane(scene, "road", -30, 30, -10, 2.0, 0.0, asphalt)
    plane(scene, "pavement", -30, 30, 2.0, 6.0, 0.125, paving)
    vwall(scene, "shopfront", -30, 30, 5.0, 0.125, 8.0, brick)
    for k in range(-14, 12):
        put("KERB_1M", k + 0.5, 2.0 - 0.0625, 0.0, 180)
    put("CAR_HATCHBACK", -2.2, 1.0, 0, 90)
    put("VAN_DELIVERY", 3.6, 1.05, 0, 90)
    put("SHOP_SIGN_CORNER", 0.0, 5.0, 3.0)
    RP.point(scene, (0.0, 4.4, 3.4), 60, (1.0, 0.85, 0.65), 0.6, "sign_spill")
    put("LAMP_COLUMN", -6.0, 2.6, 0.125)
    lamp_light(scene, -6.0, 2.6, 0.125 + 4.68, 320)
    put("BOLLARD", 0.8, 2.5, 0.125)
    put("BOLLARD", -0.6, 2.5, 0.125)
    put("LITTER_BIN", 6.6, 3.0, 0.125)
    put("DRAIN_GULLY", 0.2, 1.75, 0.0, 180)
    put("CRISP_PACKET", -0.5, -0.6, 0, 30)
    # shop window glow on the pavement
    RP.area(scene, (0.0, 4.6, 1.5), (90, 0, 0), 300, 5.0, SHOP_WARM, "window_glow")
    RP.area(scene, (0.0, -14.0, 8.0), (60, 0, 0), 800, 14, COOL, "sky_fill")
    RP.camera(scene, (8.2, -4.6, 1.5), (-0.4, 1.9, 1.0), 26)
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("rendered", out)


SCENES = {
    "street": scene_street,
    "cage": scene_cage,
    "shop": scene_shop,
    "interiors": scene_interiors,
    "vehicles": scene_vehicles,
}


def run(out_dir, which=None):
    os.makedirs(out_dir, exist_ok=True)
    for name, fn in SCENES.items():
        if which and name not in which:
            continue
        fn(os.path.join(out_dir, f"props-{name}.png"))
