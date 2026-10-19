"""Shared helpers for the South London gap-fill props (Blender 5.2 bpy module, headless).

Conventions used until the main build's CONVENTIONS.md says otherwise:
- metres, Blender Z-up in source, exported glTF is Y-up
- each prop's origin sits at its base centre on the ground (wall items: back centre)
- object and node names: hr_prop_<thing>[_<variant>], materials: mat_<surface>
- tiling surfaces get world-space box UVs at 1 UV unit = 1 metre
"""
import math
from pathlib import Path
import bmesh
import bpy
from mathutils import Vector

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = "METRIC"
    s.unit_settings.scale_length = 1.0

_MATS = {}

def mat(name, color=(0.5, 0.5, 0.5), rough=0.7, metal=0.0, image=None, emissive=None, strength=1.0, alpha=None):
    if name in _MATS and _MATS[name].name in bpy.data.materials:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if image:
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(image))
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        if alpha == "image":
            nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
            m.surface_render_method = "BLENDED" if hasattr(m, "surface_render_method") else None
    if emissive:
        b.inputs["Emission Color"].default_value = (*emissive, 1)
        b.inputs["Emission Strength"].default_value = strength
    _MATS[name] = m
    return m

def _link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj

def mesh_obj(name, verts, faces, material=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) for v in verts], [], faces)
    me.update()
    ob = _link(bpy.data.objects.new(name, me))
    if material:
        ob.data.materials.append(material)
    return ob

def box(name, size, loc=(0, 0, 0), material=None, rot=(0, 0, 0)):
    """Box of size (x, y, z) whose centre is at loc."""
    sx, sy, sz = (s / 2 for s in size)
    v = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
         (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_obj(name, v, f, material)
    ob.location = loc
    ob.rotation_euler = rot
    return ob

def cyl(name, r, depth, loc=(0, 0, 0), material=None, verts=12, rot=(0, 0, 0), cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, segments=verts, radius1=r, radius2=r, depth=depth)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = _link(bpy.data.objects.new(name, me))
    if material:
        ob.data.materials.append(material)
    ob.location = loc; ob.rotation_euler = rot
    return ob

def tube(name, pts, r, material=None, verts=8):
    """Straight segments between points, one cylinder per segment, joined."""
    parts = []
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = Vector(a), Vector(b)
        d = b - a
        c = cyl(name, r, d.length, (a + b) / 2, material, verts)
        c.rotation_mode = "QUATERNION"
        c.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
        parts.append(c)
    return join(parts, name)

def join(objs, name):
    objs = [o for o in objs if o]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(objs) > 1:
        bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name; ob.data.name = name
    return ob

def world_uv(ob, scale=1.0, skip_materials=()):
    """Box-project UVs in world metres (1 UV unit = 1 m / scale)."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    mw = ob.matrix_world
    skip = {i for i, m in enumerate(me.materials) if m and m.name in skip_materials}
    for p in me.polygons:
        if p.material_index in skip:
            continue
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            if ax == 0:
                u, v = co.y * math.copysign(1, n.x), co.z
            elif ax == 1:
                u, v = -co.x * math.copysign(1, n.y), co.z
            else:
                u, v = co.x, co.y * math.copysign(1, n.z)
            uv[li].uv = (u / scale, v / scale)

def set_origin_base(ob, mode="base"):
    """Move mesh so origin is base centre (mode base) or back centre at y max (mode back)."""
    me = ob.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    if mode == "base":
        off = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    else:
        off = Vector(((min(xs) + max(xs)) / 2, max(ys), (min(zs) + max(zs)) / 2))
    for v in me.vertices:
        v.co -= off
    ob.location = (0, 0, 0)

def smooth_by_angle(ob, deg=35):
    for p in ob.data.polygons:
        p.use_smooth = False

def export(path, objects=None, blend=None):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in (objects or bpy.context.scene.objects):
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True,
                              export_yup=True, export_apply=True, export_image_format="AUTO")
    if blend:
        Path(blend).parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))

def stats():
    tris = 0
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
    return tris
