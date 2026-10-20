"""Original ONSITE low-relief ground meshes from the accepted render-only plan.

blender -b -t 1 --python scripts/maps/art/build_heron_ground_detail.py -- \
  --source-root /workspace/Onsite --output-root /tmp/onsite-ground-work

No collision/nav edits, new texture pixels or imported assets. The editable Blend keeps
existing PBR maps; the GLB exports named placeholders resolved to existing runtime materials.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
from collections import defaultdict

import bpy


def main():
    parser = argparse.ArgumentParser()
    default = Path(__file__).resolve().parents[3]
    parser.add_argument('--source-root', type=Path, default=default)
    parser.add_argument('--output-root', type=Path, default=default)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    source, output = args.source_root.resolve(), args.output_root.resolve()
    sys.path.insert(0, str(source / 'scripts/maps/art'))
    from heron_foliage_atlas import LITTER_CELLS, rect_uv
    plan_path = output / 'assets/blender/heron-reach/ground-plan.json'
    plan = json.loads(plan_path.read_text())
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 1
    groups = defaultdict(lambda: {'vertices': [], 'faces': [], 'uv': [], 'colour': [], 'patches': []})

    def mesh_group(patch, material):
        tile = f"{math.floor(patch['x']/24)}_{math.floor(patch['z']/24)}"
        return groups[(tile, material)]

    def face(g, coords, uv=None, colour=(1, 1, 1, 1)):
        # Map x/east,z/south,y/up -> Blender x/east,y/north,z/up.
        v = [(x-72, 60-z, y) for x, y, z in coords]
        normal_z = (v[1][0]-v[0][0])*(v[2][1]-v[0][1])-(v[1][1]-v[0][1])*(v[2][0]-v[0][0])
        if normal_z < 0:
            v.reverse()
            coords = list(reversed(coords))
            uv = list(reversed(uv)) if uv else None
        base = len(g['vertices'])
        g['vertices'].extend(v)
        g['faces'].append(tuple(range(base, base+len(v))))
        g['uv'].extend(uv if uv else [(p[0], p[2]) for p in coords])
        g['colour'].extend([colour]*len(v))

    def inside(x, z, poly):
        odd = False
        j = len(poly)-1
        for i, a in enumerate(poly):
            b = poly[j]
            if (a[1] > z) != (b[1] > z) and x < (b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:
                odd = not odd
            j = i
        return odd

    for p in plan['patches']:
        rng = random.Random(p['seed'])
        kind, poly, x, z, y = p['kind'], p['outline'], p['x'], p['z'], p['y']
        material = 'hr_ground_moss' if kind == 'moss' else 'hr_leaf_litter' if kind == 'leaves' else 'hr_soil'
        g = mesh_group(p, material)
        g['patches'].append(p['id'])
        if kind == 'leaves':
            # Twelve separated leaves per small drift, no new full square litter patches.
            count = 0
            for _ in range(400):
                px = x+rng.uniform(-.27, .27)
                pz = z+rng.uniform(-.14, .14)
                sz, angle = rng.uniform(.095, .155), rng.random()*math.tau
                u, v = (math.cos(angle), math.sin(angle)), (-math.sin(angle), math.cos(angle))
                corners = [(px+(a*u[0]+b*v[0])*sz, pz+(a*u[1]+b*v[1])*sz) for a, b in [(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]]
                if not all(inside(qx, qz, poly) for qx, qz in corners):
                    continue
                cell = rng.choice(LITTER_CELLS)
                uv = [rect_uv(cell['rect'], a, b) for a, b in [(0,1),(1,1),(1,0),(0,0)]]
                coords = [(qx,y+.001+(.0015 if i in (1,3) else 0),qz) for i,(qx,qz) in enumerate(corners)]
                face(g, coords, uv)
                count += 1
                if count == 12:
                    break
        elif kind == 'pit':
            # Low ragged soil ring around the exact existing trunk; no invented raised kerb.
            inner = [(x+(px-x)*.43,z+(pz-z)*.43) for px,pz in poly]
            for i, (px,pz) in enumerate(poly):
                j = (i+1) % len(poly)
                face(g, [(px,y,pz),(poly[j][0],y,poly[j][1]),(inner[j][0],y+.004,inner[j][1]),(inner[i][0],y+.004,inner[i][1])], colour=(.88,.87,.85,1))
        else:
            # Irregular outlines and a few millimetres of surface relief, merged per 24m tile.
            for i, (px,pz) in enumerate(poly):
                qx,qz = poly[(i+1) % len(poly)]
                c = .83+rng.random()*.17
                colour = (.55*c,.66*c,.45*c,1) if kind == 'moss' else (c,c,c,1)
                face(g, [(x,y+.003,z),(px,y,pz),(qx,y,qz)], colour=colour)

    materials = {}
    def material(name):
        if name in materials:
            return materials[name]
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        m.use_backface_culling = name != 'hr_leaf_litter'
        bsdf = m.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Roughness'].default_value = .9
        base = 'hr_grass_ground' if name == 'hr_ground_moss' else name
        path = source/'public/materials/heron'/('foliage/leaf-litter-color.webp' if name == 'hr_leaf_litter' else base+'-color.webp')
        image = bpy.data.images.load(str(path), check_existing=True)
        image.pack()
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = image
        nodes, links = m.node_tree.nodes, m.node_tree.links
        vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'
        mul = nodes.new('ShaderNodeMixRGB'); mul.blend_type = 'MULTIPLY'; mul.inputs[0].default_value = 1
        links.new(tex.outputs['Color'],mul.inputs[1]); links.new(vc.outputs['Color'],mul.inputs[2]); links.new(mul.outputs[0],bsdf.inputs['Base Color'])
        coord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeMapping')
        repeat = json.loads((source/'public/materials/heron/runtime-materials.json').read_text()).get(base,{}).get('repeat',1)
        mapping.inputs['Scale'].default_value = (repeat,repeat,1)
        links.new(coord.outputs['UV'],mapping.inputs['Vector']); links.new(mapping.outputs['Vector'],tex.inputs['Vector'])
        normal_path = path.with_name(path.name.replace('-color.webp','-normal.webp'))
        if normal_path.exists():
            normal = nodes.new('ShaderNodeTexImage'); normal.image = bpy.data.images.load(str(normal_path),check_existing=True); normal.image.colorspace_settings.name='Non-Color'; normal.image.pack()
            nm = nodes.new('ShaderNodeNormalMap'); links.new(mapping.outputs['Vector'],normal.inputs['Vector']); links.new(normal.outputs['Color'],nm.inputs['Color']); links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
        orm_path = path.with_name(path.name.replace('-color.webp','-orm.webp'))
        if orm_path.exists():
            orm=nodes.new('ShaderNodeTexImage');orm.image=bpy.data.images.load(str(orm_path),check_existing=True);orm.image.colorspace_settings.name='Non-Color';orm.image.pack()
            split=nodes.new('ShaderNodeSeparateColor');links.new(mapping.outputs['Vector'],orm.inputs['Vector']);links.new(orm.outputs['Color'],split.inputs['Color']);links.new(split.outputs['Green'],bsdf.inputs['Roughness']);links.new(split.outputs['Blue'],bsdf.inputs['Metallic'])
        if name == 'hr_leaf_litter':
            m.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
            if hasattr(m,'surface_render_method'):
                m.surface_render_method = 'DITHERED'
        materials[name] = m
        return m

    triangle_count = 0
    report = []
    for (tile, name), g in sorted(groups.items()):
        if not g['faces']:
            continue
        mesh = bpy.data.meshes.new(f'ground_{tile}_{name}')
        mesh.from_pydata(g['vertices'], [], g['faces'])
        mesh.materials.append(material(name))
        mesh.uv_layers.new(name='UVMap').data.foreach_set('uv', [c for uv in g['uv'] for c in uv])
        colours = mesh.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='POINT')
        colours.data.foreach_set('color',[c for colour in g['colour'] for c in colour])
        mesh.update()
        ob = bpy.data.objects.new(mesh.name,mesh)
        scene.collection.objects.link(ob)
        tris = sum(len(f)-2 for f in g['faces'])
        triangle_count += tris
        report.append({'name':ob.name,'material':name,'triangles':tris,'patches':g['patches']})
    out_dir = output/'assets/blender/heron-reach'
    out_dir.mkdir(parents=True,exist_ok=True)
    blend_path = out_dir/'ground-detail.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    # Preserve names/geometry/UV/vertex colours without embedding duplicated texture images.
    for name, m in materials.items():
        m.node_tree.nodes.clear()
        bsdf = m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (.15,.12,.08,1)
        out = m.node_tree.nodes.new('ShaderNodeOutputMaterial')
        m.node_tree.links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    glb = output/'public/models/heron-reach/heron-reach-ground-detail.glb'
    glb.parent.mkdir(parents=True,exist_ok=True)
    raw = glb.with_name(glb.stem+'.raw.glb')
    bpy.ops.export_scene.gltf(filepath=str(raw),export_format='GLB',export_materials='EXPORT',export_vertex_color='ACTIVE',export_yup=True)
    flags = ['-cc','-kn','-km','-kv','-vpf','-vtf']
    subprocess.run([str(source/'node_modules/.bin/gltfpack'),'-i',str(raw),'-o',str(glb),*flags],check=True)
    package = source/'node_modules/gltfpack'
    tool = {'name':'gltfpack','version':json.loads((package/'package.json').read_text())['version'],'flags':flags,
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(package.glob('*')) if p.suffix in ('.wasm','.js') or p.name=='package.json'}}
    manifest = {'provenance':'Original ONSITE deterministic geometry; existing hr_soil, hr_grass_ground and original foliage leaf atlas. No donor source or new pixels.',
                'planSha256':hashlib.sha256(plan_path.read_bytes()).hexdigest(),'blender':bpy.app.version_string,
                'builderSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'glbSha256':hashlib.sha256(glb.read_bytes()).hexdigest(),
                'rawBytes':raw.stat().st_size,'rawSha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
                'meshes':len(report),'triangles':triangle_count,'plantTriangles':plan['stats']['plantTriangles'],
                'treeTriangles':plan['stats']['treeTriangles'],'glbBytes':glb.stat().st_size,'tool':tool,'groups':report,
                'limitations':'Low relief ground detail only; no geometric holes, physical shadow ownership, collision or nav changes.'}
    (out_dir/'ground-detail-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert triangle_count+plan['stats']['plantTriangles'] <= 30000
    print(json.dumps({k:v for k,v in manifest.items() if k!='groups'}))


if __name__ == '__main__':
    main()
