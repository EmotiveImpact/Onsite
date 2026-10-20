"""Import two individually cleared Poly Haven scans as additive Heron Reach art.

GLTFPACK=/path/to/gltfpack blender -b --python-exit-code 1 \
    --python scripts/maps/art/import_heron_scanned_detail.py

The preserved IRONLINE derivatives in assets/reference/polyhaven-scanned are the
only source models. This builds a separate .blend; it never opens/rebuilds another
authored collection. No lights, collision or navigation are exported.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import struct
import subprocess
import tempfile

import bmesh
import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'assets/reference/polyhaven-scanned'
FOLDER = ROOT / 'assets/blender/heron-reach'
BLEND = FOLDER / 'scanned-detail.blend'
OUTPUT = ROOT / 'public/models/heron-reach/heron-reach-scanned.glb'
MANIFEST = FOLDER / 'scanned-detail-manifest.json'
UPSTREAM = 'https://github.com/cktang88/3d-fps'
COMMIT = '130ac2a5c856401ec36e7d35afcfefe40c5801f4'
ASSETS = {
    'water_manhole_cover': {
        'author': 'Raunox',
        'sha256': '04f305364c9e0ffcff0ba453f02c41de91bf1ab1b84bfcb904f695eb465be0f3',
        'originalFilesHash': '88b0825bb7daa072702c8238ed1f245321008fc5',
    },
    'mounted_fluorescent_lights': {
        'author': 'Ulan Cabanilla',
        'sha256': '8852f9cad1005d4a01f29d98e2af4508f93abfec927cc43e09e134d76f4052ad',
        'originalFilesHash': '0f8286f500f15e7c1476596bec518a25695012c5',
    },
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounds(obj):
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return [[min(p[i] for p in points) for i in range(3)],
            [max(p[i] for p in points) for i in range(3)]]


def map_bounds(obj):
    lo, hi = bounds(obj)
    return {'x0': lo[0] + 72, 'x1': hi[0] + 72,
            'y0': lo[2], 'y1': hi[2], 'z0': 60 - hi[1], 'z1': 60 - lo[1]}


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def apply_world(obj):
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    obj.data.update()


def load(asset):
    path = SOURCE / (asset + '.glb')
    assert path.exists(), f'Missing preserved source: {path}'
    assert digest(path) == ASSETS[asset]['sha256'], f'Unexpected source revision: {path}'
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = set(bpy.data.objects) - before
    meshes = [o for o in imported if o.type == 'MESH']
    assert len(meshes) == 1, f'Unexpected source assembly for {asset}'
    obj = meshes[0]
    apply_world(obj)
    for other in imported - {obj}:
        bpy.data.objects.remove(other, do_unlink=True)
    original = {'blenderBoundsXYZ': bounds(obj), 'triangles': triangles(obj),
                'materials': [m.name for m in obj.data.materials]}
    return obj, original


def place(template, name, x, z, top, collection):
    obj = template.copy()
    obj.data = template.data.copy()
    obj.name = name
    collection.objects.link(obj)
    lo, hi = bounds(obj)
    # A footprint-centred origin, with the authored upper face at the requested
    # height. Preserve the original +Z-facing cover / -Z-facing fluorescent tube.
    offset = Vector((x - 72 - (lo[0] + hi[0]) / 2,
                     60 - z - (lo[1] + hi[1]) / 2, top - hi[2]))
    obj.data.transform(Matrix.Translation(offset))
    obj['collision'] = 'none'
    obj['source'] = template['source']
    obj['licence'] = 'CC0-1.0'
    obj['purpose'] = 'Additive render-only detail; physical layout remains authoritative.'
    obj.data.update()
    return obj


def verify_placement(obj, layout, cover, gallery=False):
    b = map_bounds(obj)
    if cover:
        assert b['y1'] <= .020 and b['y0'] < 0, 'Cover must be embedded, <=20mm proud'
        floors = [s for s in layout['boxes'] if s['x0'] <= b['x0'] and s['x1'] >= b['x1']
                  and s['z0'] <= b['z0'] and s['z1'] >= b['z1']
                  and abs(s['y1']) < .001]
        assert floors, f'No authoritative ground beneath {obj.name}'
        blockers = [s['id'] for s in layout['boxes']
                    if s['x0'] < b['x1'] and s['x1'] > b['x0']
                    and s['z0'] < b['z1'] and s['z1'] > b['z0']
                    and s['y0'] < 2.4 and s['y1'] > .02]
        assert not blockers, f'Cover intersects above-ground solid: {blockers}'
        for d in layout['openings']:
            if d['kind'] == 'door' and d['y'] == 0:
                cx, cz = (b['x0'] + b['x1']) / 2, (b['z0'] + b['z1']) / 2
                assert (cx-d['x'])**2 + (cz-d['z'])**2 > 2.0**2, 'Cover near threshold'
    elif gallery:
        assert b['y0'] - 3 >= 2.4, 'Gallery fixture reduces clear head height'
        support = [s for s in layout['boxes'] if s['id'] == 'slab'
                   and s['x0'] <= b['x0'] and s['x1'] >= b['x1']
                   and s['z0'] <= b['z0'] and s['z1'] >= b['z1']
                   and abs(b['y1'] - (s['y0'] + .01)) < .0001]
        floor = [s for s in layout['boxes'] if s['id'] == 'slab'
                 and s['x0'] <= b['x0'] and s['x1'] >= b['x1']
                 and s['z0'] <= b['z0'] and s['z1'] >= b['z1'] and s['y1'] == 3]
        assert support and floor, 'Gallery fixture lacks full soffit/floor support'
        blockers = [s['id'] for s in layout['boxes']
                    if s['x0'] < b['x1'] and s['x1'] > b['x0']
                    and s['z0'] < b['z1'] and s['z1'] > b['z0']
                    and s['y0'] < b['y0'] and s['y1'] > 3.01]
        assert not blockers, f'Gallery fixture intersects wall/route: {blockers}'
    else:
        assert 2.65 <= b['y0'] < b['y1'] <= 2.75001
        assert 102.2 < b['x0'] < b['x1'] < 119.8
        assert 48.2 < b['z0'] < b['z1'] < 56.8
    return b


def main():
    pack = os.environ.get('GLTFPACK') or shutil.which('gltfpack')
    assert pack, 'Set GLTFPACK to the native gltfpack executable.'
    # Guard authored work: a reproducible first build is additive; later rebuilds
    # keep an existing .blend in a temporary checkpoint before writing the result.
    checkpoint = None
    if BLEND.exists():
        checkpoint = Path(tempfile.mkdtemp(prefix='onsite-scanned-checkpoint-')) / BLEND.name
        shutil.copy2(BLEND, checkpoint)
        print(f'Preserved previous authored source: {checkpoint}')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    collection = bpy.data.collections.new('HR_SCANNED_DETAIL / individually cleared Poly Haven')
    scene.collection.children.link(collection)
    layout_path = FOLDER / 'layout.json'
    layout = json.loads(layout_path.read_text())
    sources, objects, placements = [], [], []

    cover, cover_info = load('water_manhole_cover')
    cover['source'] = 'https://polyhaven.com/a/water_manhole_cover'
    cover.data.materials[0].name = 'hr_scanned_manhole'
    for name, x, z in [('scanned_manhole_corner', 108, 45), ('scanned_manhole_cage', 92, 61)]:
        obj = place(cover, name, x, z, .0185, collection)
        objects.append(obj)
        placements.append({'name': name, 'sourceAsset': 'water_manhole_cover',
                           'mapBounds': verify_placement(obj, layout, True),
                           'triangles': triangles(obj), 'needsCollision': False})
    bpy.data.objects.remove(cover, do_unlink=True)

    lamp, lamp_info = load('mounted_fluorescent_lights')
    lamp['source'] = 'https://polyhaven.com/a/mounted_fluorescent_lights'
    # The upstream model is a seven-variant strip catalogue. Its first complete
    # fixture spans world Blender Y [-.320085, -.279915]. The next begins at -.2203.
    # Keep all body/glass faces for that one strip; do not place the whole catalogue.
    bm = bmesh.new()
    bm.from_mesh(lamp.data)
    discard = [v for v in bm.verts if v.co.y > -.25]
    bmesh.ops.delete(bm, geom=discard, context='VERTS')
    bm.to_mesh(lamp.data)
    bm.free()
    lamp.data.update()
    assert triangles(lamp) == 162, 'Selected fluorescent variant changed'
    lamp_info['selectedVariantBlenderBoundsXYZ'] = bounds(lamp)
    lamp_info['selectedVariantTriangles'] = triangles(lamp)
    for mat in lamp.data.materials:
        if mat.name.endswith('_glass'):
            mat.name = 'hr_scanned_fluorescent_tube'
            bs = mat.node_tree.nodes.get('Principled BSDF')
            assert bs.inputs['Emission Color'].is_linked, 'Preserve the source emissive mask'
            bs.inputs['Emission Strength'].default_value = 1.4
        else:
            mat.name = 'hr_scanned_fluorescent_housing'
    for name, x in [('scanned_corner_strip_west', 106.5), ('scanned_corner_strip_east', 115.5)]:
        obj = place(lamp, name, x, 48.9, 2.75, collection)
        objects.append(obj)
        placements.append({'name': name, 'sourceAsset': 'mounted_fluorescent_lights',
                           'mapBounds': verify_placement(obj, layout, False),
                           'triangles': triangles(obj), 'needsCollision': False})
    for name, x in [('scanned_gallery_strip_west', 52), ('scanned_gallery_strip_east', 61)]:
        z = 38.1
        # The initial east proposal at x60 straddled the S2 wall (x59.8..60).
        # Centre at x61 instead, wholly beneath the x60..63 slab. The rendering
        # builder uses this exact physical slab's underside, y5.8, without offset.
        soffits = [s for s in layout['boxes'] if s['id'] == 'slab'
                   and s['x0'] <= x-.46 and s['x1'] >= x+.46
                   and s['z0'] <= z-.03 and s['z1'] >= z+.03 and 5.5 < s['y0'] < 6]
        assert len(soffits) == 1, 'Ambiguous gallery soffit'
        underside = soffits[0]['y0']
        obj = place(lamp, name, x, z, underside + .01, collection)
        objects.append(obj)
        placements.append({'name': name, 'sourceAsset': 'mounted_fluorescent_lights',
                           'mapBounds': verify_placement(obj, layout, False, gallery=True),
                           'triangles': triangles(obj), 'needsCollision': False,
                           'soffitUnderside': underside, 'floorY': 3,
                           'soffitEmbedDepth': .01})
    bpy.data.objects.remove(lamp, do_unlink=True)

    for asset, info in [('water_manhole_cover', cover_info), ('mounted_fluorescent_lights', lamp_info)]:
        path = SOURCE / (asset + '.glb')
        sources.append({'id': asset, 'author': ASSETS[asset]['author'], 'licence': 'CC0-1.0',
                        'sourceURL': 'https://polyhaven.com/a/' + asset,
                        'licenceURL': 'https://polyhaven.com/license',
                        'originalMetadataURL': 'https://api.polyhaven.com/info/' + asset,
                        'originalFilesHash': ASSETS[asset]['originalFilesHash'],
                        'checked': '2026-10-19', 'donorRepository': UPSTREAM, 'donorCommit': COMMIT,
                        'donorPath': f'public/assets/models/props/{asset}/{asset}.glb',
                        'preservedSource': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                        'sha256': digest(path), 'inspection': info})

    # Preserve every imported colour/normal/ORM/emission image in the editable blend.
    # No runtime remapping to shared hr_* placeholder materials is required.
    for im in bpy.data.images:
        if im.type == 'IMAGE':
            # glTF already packs the original WebP bytes. Blender 4.3's pack()
            # called again on these images clears their packed_file: keep the
            # original packed data, and force decoding while the import is live.
            assert im.size[0] > 0 and im.size[1] > 0, f'Image failed to decode: {im.name}'
            assert im.packed_file and len(im.packed_file.data) > 0, f'Image not packed: {im.name}'
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
    total_triangles = sum(triangles(o) for o in objects)
    assert total_triangles < 15000
    with tempfile.TemporaryDirectory(prefix='onsite-scanned-export-') as tmp:
        raw = Path(tmp) / 'scanned.raw.glb'
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.export_scene.gltf(filepath=str(raw), export_format='GLB', use_selection=True,
                                  export_image_format='WEBP', export_image_quality=88,
                                  export_apply=True, export_yup=True, export_extras=True,
                                  export_lights=False, export_cameras=False)
        command = [str(pack), '-i', str(raw), '-o', str(OUTPUT), '-c', '-kn', '-km', '-ke', '-vp', '16', '-vt', '14']
        subprocess.run(command, check=True)
    blob = OUTPUT.read_bytes()
    exported = json.loads(blob[20:20+struct.unpack_from('<I', blob, 12)[0]])
    assert len(blob) < 1_500_000, 'Runtime delivery budget exceeded'
    assert 'KHR_lights_punctual' not in exported.get('extensionsUsed', [])
    assert len(exported.get('images', [])) == 7, 'Lost embedded scan texture images'
    for texture in exported['textures']:
        image_index = texture.get('source', texture.get('extensions', {}).get('EXT_texture_webp', {}).get('source'))
        assert image_index is not None and image_index < len(exported['images']), 'Texture has no image source'
    assert not [item for kind in ('images', 'buffers') for item in exported.get(kind, []) if item.get('uri')]
    for i, material in enumerate(exported['materials']):
        assert 'baseColorTexture' in material.get('pbrMetallicRoughness', {}), f'Material {i} lost colour texture'
        assert 'normalTexture' in material, f'Material {i} lost normal texture'
    manifest = {
        'builder': str(Path(__file__).relative_to(ROOT)), 'blender': bpy.app.version_string,
        'units': 'metres; Blender (X=x-72,Y=60-z,Z=y); glTF (X=x-72,Y=y,Z=z-60)',
        'sources': sources, 'placements': placements, 'objects': len(objects),
        'triangles': total_triangles, 'collision': 'None. No physical solids/navigation changed.',
        'modifications': [
            'Source IRONLINE derivatives already simplified and converted to embedded WebP; preserved byte-for-byte.',
            'Original metre scale, normals, UVs and texture/material assignment retained.',
            'Manhole frame embedded below ground with highest relief 18.5mm proud.',
            'Extracted first complete strip variant from the seven-variant fluorescent catalogue; placed twice in Corner and twice under the northern L2 slab.',
            'Gallery strips embed their upper 10mm in verified y5.8 soffits; minimum head clearance 2.77486m above the y3 floor. East strip moves to x61 to clear the x59.8..60 core wall.',
            'Fluorescent tube uses original emission texture at strength 1.4; no light objects.',
            'Baked world placements; original embedded WebP bytes retained in Blender and GLB; meshopt geometry compression.',
        ],
        'layoutSHA256': digest(layout_path),
        'blend': {'path': str(BLEND.relative_to(ROOT)), 'bytes': BLEND.stat().st_size, 'sha256': digest(BLEND)},
        'runtime': {'path': str(OUTPUT.relative_to(ROOT)), 'bytes': len(blob), 'sha256': digest(OUTPUT),
                    'extensionsRequired': exported.get('extensionsRequired', []),
                    'materials': [m['name'] for m in exported['materials']]},
        'compression': {'tool': 'gltfpack 0.22 native', 'sha256': digest(Path(pack)),
                        'options': '-c -kn -km -ke -vp 16 -vt 14'},
        'runtimeIntegration': {
            'load': '/models/heron-reach/heron-reach-scanned.glb', 'rootTransform': 'identity',
            'materialPolicy': 'Keep embedded PBR maps/emission; do not replace with shared HeronReachMaterials.',
            'replaceExistingGroupsWhenLoaded': ['E-shop/interior / hr_shop_fitting', 'E-shop/interior / hr_shop_strip'],
            'shadows': 'Ground covers receive shadows; optional casting disabled for these small decorative pieces.',
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'output': str(OUTPUT), 'bytes': len(blob), 'triangles': total_triangles,
                      'placements': placements, 'checkpoint': str(checkpoint) if checkpoint else None}, indent=2))


if __name__ == '__main__':
    main()
