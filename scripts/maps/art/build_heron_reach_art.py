"""Build the authored Heron Reach art file from the generator's layout.

    npx tsx scripts/maps/export-heron-layout.ts      # layout.json from src/onsite/heronReach.ts
    python3 scripts/maps/art/build_heron_reach_art.py

Writes assets/blender/heron-reach/heron-reach.blend. The file is generated: hand edits belong in
the kit .blend files or in these scripts, because a rebuild replaces the HR_ARCH collections.
Collision and navigation stay in the TypeScript generator; nothing here feeds back into them.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import bpy  # noqa: E402
from heron_art_mesh import Builder  # noqa: E402
from heron_art_arch import Arch  # noqa: E402
from heron_art_context import Context  # noqa: E402
from heron_art_materials import Library, ROOT  # noqa: E402

LAYOUT = os.path.join(ROOT, 'assets', 'blender', 'heron-reach', 'layout.json')
OUT = os.path.join(ROOT, os.environ.get('ONSITE_ARCH_BLEND', 'assets/blender/heron-reach/heron-reach.blend'))


def main():
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    L = json.load(open(LAYOUT))

    root = bpy.data.collections.new('HR_ARCH')
    scene.collection.children.link(root)
    kinds = {}

    def collection_for(group):
        kind = group.split('/', 1)[1]
        if kind not in kinds:
            c = bpy.data.collections.new(f'HR_{kind}')
            root.children.link(c)
            kinds[kind] = c
        return kinds[kind]

    mats = Library()
    builder = Builder(collection_for)
    arch = Arch(L, builder)
    arch.build_all()
    Context(L, builder).build_all()
    faces = sum(len(a) for a in builder.groups.values())
    objs = builder.build(mats, smooth_groups=('/columns',))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)

    # Lit windows and other light anchors for the runtime and the dressing planner.
    meta = {'windows': arch.windows, 'materials': mats.report, 'objects': len(objs), 'faces': faces, 'triangles': tris}
    with open(os.path.join(ROOT, 'assets', 'blender', 'heron-reach', 'arch-build.json'), 'w') as f:
        json.dump(meta, f, indent=1)

    grass = os.path.join(ROOT, 'public', 'models', 'heron-reach', 'grass-cells.json')
    os.makedirs(os.path.dirname(grass), exist_ok=True)
    with open(grass, 'w') as f:
        json.dump({'cell': 2, 'cells': [[round(x, 2), round(z, 2)] for x, z in arch.grass_cells]}, f, separators=(',', ':'))

    with open(os.path.join(ROOT, 'public', 'models', 'heron-reach', 'facade-dressing.json'), 'w') as f:
        json.dump([{k: (round(v, 3) if isinstance(v, float) else v) for k, v in it.items()} for it in arch.facade_items], f, separators=(',', ':'))

    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
    print(f'built {len(objs)} objects, {tris} triangles, {len(mats.report)} materials in {time.time() - t0:.1f}s -> {OUT}')
    missing = [k for k, v in mats.report.items() if not v.get('textured') and k not in ('hr_glass',)]
    print('untextured:', ' '.join(sorted(missing)))


if __name__ == '__main__':
    main()
