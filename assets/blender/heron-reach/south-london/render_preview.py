"""Render a contact sheet of every top-level node in a GLB. Usage: python3 render_preview.py IN.glb OUT.png [cols] [dusk]"""
import math, sys
import bpy
from mathutils import Vector
src, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 6
dusk = len(sys.argv) > 4 and sys.argv[4] == "dusk"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
import os
SRC30 = os.environ.get("SRC30", "/home/claude/Onsite/assets/textures/source-30/")
PREVIEW_TEX = {"mat_brick_london_stock": "01-london-stock-brick-color.png", "mat_brick_red": "02-red-estate-brick-color.png",
    "mat_concrete_cast": "04-cast-concrete-color.png", "mat_concrete_rough": "06-rough-concrete-color.png",
    "mat_asphalt": "08-asphalt-color.png", "mat_paving_slab": "10-paving-slabs-color.png", "mat_roof_felt": "12-roof-felt-color.png",
    "mat_steel_aged": "15-aged-steel-color.png", "mat_roller_shutter": "16-roller-shutter-color.png", "mat_timber_bench": "26-bench-timber-color.png"}
for m in bpy.data.materials:
    f = PREVIEW_TEX.get(m.name.split(".")[0])
    if f and m.use_nodes and os.path.exists(SRC30 + f) and not any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes):
        t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(SRC30 + f)
        b = [n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"][0]
        m.node_tree.links.new(t.outputs["Color"], b.inputs["Base Color"])
        tc = m.node_tree.nodes.new("ShaderNodeTexCoord"); mp = m.node_tree.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (0.5, 0.5, 0.5)  # source-30 tiles cover 2 x 2 m; UVs are metres
        m.node_tree.links.new(tc.outputs["UV"], mp.inputs["Vector"]); m.node_tree.links.new(mp.outputs["Vector"], t.inputs["Vector"])
objs = [o for o in bpy.context.scene.objects if o.parent is None]
def bounds(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    for ch in o.children_recursive:
        pts += [ch.matrix_world @ Vector(c) for c in ch.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])
ortho = len(sys.argv) > 5 and sys.argv[5] == "front"
sizes = [bounds(o) for o in objs]
order = sorted(range(len(objs)), key=lambda i: -(sizes[i][1].z - sizes[i][0].z))
total_w = sum(sizes[i][1].x - sizes[i][0].x + 0.3 for i in order)
row_w = max(max(sizes[i][1].x - sizes[i][0].x for i in order), (total_w / cols) * 1.0 if cols < 0 else total_w / max(1, round((total_w / 3.0) ** 0.5 / 1.0)))
row_w = max(row_w, total_w / max(1, int((len(objs) / cols) + 0.999)) if cols > 0 else row_w)
x = 0; row = 0; row_h = 0; rows_h = []; placed = []
for i in order:
    lo, hi = sizes[i]; w = hi.x - lo.x; h = hi.z - lo.z; d = hi.y - lo.y
    if x > 0 and x + w > row_w:
        rows_h.append(row_h); x = 0; row += 1; row_h = 0
    placed.append((i, x - lo.x, row, lo, hi)); x += w + 0.3; row_h = max(row_h, h if ortho else d)
rows_h.append(row_h)
maxx = 0
for i, px, r, lo, hi in placed:
    o = objs[i]
    off = sum(rows_h[:r]) + 0.4 * r
    if ortho:
        o.location += __import__("mathutils").Vector((px, -lo.y, -lo.z + (sum(rows_h) + 0.4 * len(rows_h)) - off - rows_h[r]))
    else:
        o.location += __import__("mathutils").Vector((px, off - lo.y, -lo.z))
    maxx = max(maxx, px + hi.x)
W = maxx; Hh = sum(rows_h) + 0.4 * len(rows_h)
if not ortho:
    bpy.ops.mesh.primitive_plane_add(size=1, location=(W / 2, Hh / 2, 0))
    gp = bpy.context.object; gp.scale = (W * 4 + 10, Hh * 4 + 10, 1)
    gm = bpy.data.materials.new("ground"); gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.08, 0.08, 0.085, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.25 if dusk else 0.8
    gp.data.materials.append(gm)
cx = W / 2; cell = max(W, Hh) / 3
if ortho:
    bpy.ops.object.camera_add(location=(cx, -50, Hh / 2))
    cam = bpy.context.object; cam.rotation_euler = (math.radians(90), 0, 0)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = max(W * 1.06, Hh * 1.6 * 1.06)
else:
    from mathutils import Vector as V
    pts = []
    for o in objs:
        lo, hi = bounds(o); pts += [lo, hi]
    mn = V([min(p[i] for p in pts) for i in range(3)]); mx = V([max(p[i] for p in pts) for i in range(3)])
    ctr = (mn + mx) / 2; ctr.z = min(ctr.z, 0.8); rad = max(V((mx.x - mn.x, mx.y - mn.y, min(mx.z - mn.z, 3.0))).length / 2, 1.0)
    dirv = V((0.25, -0.85, 0.5)).normalized()
    dist = rad / math.sin(math.radians(17)) * 0.8
    bpy.ops.object.camera_add(location=ctr + dirv * dist)
    cam = bpy.context.object
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 50
    cell = rad / 2; cx = ctr.x
bpy.context.scene.camera = cam
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), math.radians(10), math.radians(-30)))
bpy.context.object.data.energy = 0.6 if dusk else 3.5
bpy.context.object.data.color = (0.6, 0.7, 1.0) if dusk else (1, 0.97, 0.92)
w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.07, 0.14, 1) if dusk else (0.5, 0.55, 0.65, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
if dusk:
    bpy.ops.object.light_add(type="POINT", location=(cx, -cell, cell * 1.5))
    bpy.context.object.data.energy = 300 * cell; bpy.context.object.data.color = (1, 0.7, 0.4)
sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1600, 1000
sc.view_settings.view_transform = "AgX"
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
