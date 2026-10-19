"""Export the Heron Reach props and foliage kits for instancing in the browser.

    python3 scripts/maps/art/export_heron_kits_glb.py [props|foliage ...]

Each kit asset becomes one root node named after the asset (origin at its footprint centre on the
ground, front facing glTF +Z), so the runtime can instance it from the dressing plan. Kit-specific
materials keep their WebP textures inside the kit GLB; shared hr_* surfaces are swapped at runtime
for the texture kit's library by name. LOD1 meshes are left out for now.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from heron_art_materials import ROOT  # noqa: E402

KITS = {'props': 'props-kit.blend', 'foliage': 'foliage-kit.blend'}


def export(kit):
    src = os.path.join(ROOT, 'assets', 'blender', 'heron-reach', KITS[kit])
    manifest = json.load(open(os.path.join(ROOT, 'assets', 'blender', 'heron-reach', f'{kit}-manifest.json')))
    bpy.ops.wm.open_mainfile(filepath=src)
    scene = bpy.context.scene
    roots, report = [], {}
    for a in manifest['assets']:
        col = bpy.data.collections.get(a.get('collection', a['name']))
        if col is None:
            report[a['name']] = 'missing collection'
            continue
        objs = [o for o in col.all_objects if o.type == 'MESH' and 'LOD1' not in o.name and 'lod1' not in o.name.lower()]
        tops = [o for o in objs if o.parent is None or o.parent not in objs]
        if not tops:
            report[a['name']] = 'no meshes'
            continue
        origin = Vector(tops[0].matrix_world.translation)
        clash = bpy.data.objects.get(a['name'])
        if clash is not None:
            clash.name = a['name'] + '_mesh'  # the root node carries the asset name
        root = bpy.data.objects.new(a['name'], None)
        scene.collection.objects.link(root)
        root.location = origin
        bpy.context.view_layer.update()
        for o in tops:
            mw = o.matrix_world.copy()
            o.parent = root
            o.matrix_world = mw
        root.location = (0, 0, 0)
        roots.append(root)
        report[a['name']] = len(objs)
    bpy.ops.object.select_all(action='DESELECT')
    for r in roots:
        r.select_set(True)
        for c in r.children_recursive:
            c.select_set(True)
    out = os.path.join(ROOT, 'public', 'models', 'heron-reach', f'heron-reach-{kit}.raw.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', use_selection=True, export_image_format='WEBP',
                              export_materials='EXPORT', export_vertex_color='ACTIVE', export_apply=True, export_yup=True)
    print(kit, json.dumps(report))
    print('wrote', out)


if __name__ == '__main__':
    for k in sys.argv[1:] or list(KITS):
        export(k)
