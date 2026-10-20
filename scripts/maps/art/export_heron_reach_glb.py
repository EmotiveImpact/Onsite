"""Export the authored Heron Reach art file for the browser.

    python3 scripts/maps/art/export_heron_reach_glb.py

Joins the authored objects per export chunk and material, then writes
public/models/heron-reach/heron-reach-arch.raw.glb without images. The runtime assigns materials
by name from public/materials/heron/runtime-materials.json, so textures are shared with the kits
and never duplicated inside the model. `npm run assets:heron-reach` runs the whole chain and compresses the result with gltfpack.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy  # noqa: E402
from heron_art_materials import ROOT, PLAIN, EMIT, COVERAGE, DEFAULT_COVERAGE, texture_set  # noqa: E402

SRC = os.path.join(ROOT, os.environ.get('ONSITE_ARCH_BLEND', 'assets/blender/heron-reach/heron-reach.blend'))
OUT_DIR = os.path.join(ROOT, 'public', 'models', 'heron-reach')
MATS = os.path.join(ROOT, 'public', 'materials', 'heron', 'runtime-materials.json')

# Runtime-only hints: alpha cutouts, double-sided cards, materials that never cast shadows.
DOUBLE = set()  # window cards are single-sided so homes can see out
# Damp ground: roughness multiplier on top of the ORM map, so lamps and sky read in the paving.
WET = {'hr_asphalt': .42, 'hr_paving': .5, 'hr_pavers_red': .5, 'hr_court': .45, 'hr_concrete_cast': .8, 'hr_roof_felt': .6}
NO_SHADOW = {'hr_core_strip', 'hr_glass_blocks', 'hr_wired_glass', 'hr_tower_elev', 'hr_tower_elev_b', 'hr_glass', 'hr_glass_lit', 'hr_window_interior', 'hr_window_dark', 'hr_lamp_emit'}


def rel(path):
    return '/' + os.path.relpath(path, os.path.join(ROOT, 'public')).replace(os.sep, '/') if path else None


def runtime_material(name):
    entry = {'shadow': name not in NO_SHADOW}
    tex = texture_set(name)
    if tex:
        c, n, o = tex
        cov = COVERAGE.get(name, DEFAULT_COVERAGE.get(name, 2.0))
        entry.update(map=rel(c), normalMap=rel(n), ormMap=rel(o), repeat=round(1 / cov, 5))
        if name in PLAIN:
            entry['roughness'] = PLAIN[name][1]
            entry['metalness'] = PLAIN[name][2]
    elif name in EMIT:
        col, strength = EMIT[name]
        entry.update(color=list(col), emissive=list(col), emissiveIntensity=strength, roughness=.4, metalness=0)
    else:
        col, rough, metal = PLAIN.get(name, ((.5, .1, .5), .5, 0))
        entry.update(color=list(col), roughness=rough, metalness=metal)
    if name.startswith('hr_window_interior'):
        atlas = os.path.join(ROOT, 'public', 'materials', 'heron', 'windows')
        kind = 'interiors-photo' if os.path.exists(os.path.join(atlas, 'interiors-photo-color.webp')) else 'interiors'
        if os.path.exists(os.path.join(atlas, f'{kind}-color.webp')):
            entry.update(map=rel(os.path.join(atlas, f'{kind}-color.webp')), emissiveMap=rel(os.path.join(atlas, f'{kind}-emit.webp')),
                         color=[1, 1, 1], emissive=[1, .8, .6], emissiveIntensity=2.2, repeat=1)
            entry['shadow']=False
            if name.endswith('_dim'):
                entry.update(emissive=[1,.56,.27],emissiveIntensity=.45)
            elif name.endswith('_cool'):
                entry.update(emissive=[.65,.8,1],emissiveIntensity=.8)
    if name in ('hr_tower_elev', 'hr_tower_elev_b'):
        back = os.path.join(ROOT, 'public', 'materials', 'heron', 'backdrop')
        v = 'b' if name.endswith('_b') else 'a'
        entry.update(map=rel(os.path.join(back, f'tower-elevation-{v}-color.webp')), emissiveMap=rel(os.path.join(back, f'tower-elevation-{v}-emit.webp')),
                     normalMap=None, ormMap=None, color=[1, 1, 1], emissive=[1, .85, .7], emissiveIntensity=1.8, roughness=.9, metalness=0, repeat=1)
    if name == 'hr_glass':
        entry['opacity'] = .28
    if name == 'hr_glass_blocks':
        # The lit stairwell glows through the blocks at dusk.
        entry.update(color=[.28,.42,.43],emissiveMap=entry['map'],emissive=[.6,.78,.85],emissiveIntensity=.24,roughness=.24,metalness=.08)
    if name == 'hr_wired_glass':
        entry['opacity'] = .62
    if name in WET:
        entry['wet'] = WET[name]
    if name in DOUBLE:
        entry['doubleSided'] = True
    return entry


def main():
    bpy.ops.wm.open_mainfile(filepath=SRC)
    groups = {}
    for o in bpy.data.objects:
        if o.type != 'MESH' or ' / ' not in o.name:
            continue
        group, mat = o.name.split(' / ', 1)
        chunk = group.split('/', 1)[0]
        groups.setdefault((chunk, mat), []).append(o)
    out = bpy.data.collections.new('EXPORT')
    bpy.context.scene.collection.children.link(out)
    for (chunk, mat), objs in sorted(groups.items()):
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:
            for c in o.users_collection:
                c.objects.unlink(o)
            out.objects.link(o)
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        if len(objs) > 1:
            bpy.ops.object.join()
        joined = bpy.context.view_layer.objects.active
        joined.name = joined.data.name = f'{chunk}|{mat}'
    # Only the export collection is visible to the exporter.
    for c in bpy.context.scene.collection.children:
        if c is not out:
            bpy.context.view_layer.layer_collection.children[c.name].exclude = True
    os.makedirs(OUT_DIR, exist_ok=True)
    raw = os.path.join(OUT_DIR, 'heron-reach-arch.raw.glb')
    bpy.ops.export_scene.gltf(filepath=raw, export_format='GLB', use_visible=True, export_image_format='NONE',
                              export_materials='EXPORT', export_vertex_color='ACTIVE', export_normals=True,
                              export_texcoords=True, export_apply=True, export_yup=True, export_extras=False)
    # Every known shared material, so the kits can swap their placeholders for the same library.
    names = sorted({m for _, m in groups} | set(PLAIN) | set(EMIT) | set(COVERAGE))
    library = {n: runtime_material(n) for n in names}
    with open(MATS, 'w') as f:
        json.dump(library, f, indent=1)
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in out.objects)
    print(f'exported {len(out.objects)} meshes, {tris} triangles, {len(names)} materials -> {raw}')


if __name__ == '__main__':
    main()
