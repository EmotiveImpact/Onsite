"""Build an additive, editable cage kit using the project's original prop generators.

blender -b --python-exit-code 1 --python scripts/maps/art/build_heron_cage_detail.py
No existing .blend is opened or replaced. Compatible with this session's Blender 4.3.
The runtime substitutes these render parts at existing placements; no collider is consumed.
"""
import sys
import json
import hashlib
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import heron_props_cage as cage
import heron_props_materials as materials
import heron_props_lib as lib
from make_heron_props import set_backface_culling

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1
mats=materials.build_all(str(ROOT))
parent=bpy.data.collections.new('HR_CAGE_DETAIL')
bpy.context.scene.collection.children.link(parent)
entries=[];objects=[]
for build in [*cage.BUILDERS,cage.floodlight,cage.markings]:
    asset=build();ob=asset.build(mats,parent);objects.append(ob)
    stats=lib.stats(ob)
    entries.append({'name':asset.name,'triangles':stats['triangles'],'bounds':{'min':stats['bounds_min'],'max':stats['bounds_max']},'needsCollision':False,'notes':asset.meta.get('notes','')})
set_backface_culling(objects)
for m in list(bpy.data.materials):
    if m.users==0:bpy.data.materials.remove(m)
for im in list(bpy.data.images):
    if im.users==0:bpy.data.images.remove(im)
bpy.context.preferences.filepaths.save_version=0
folder=ROOT/'assets/blender/heron-reach'
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'cage-detail.blend'),compress=True)
# One node per asset, preserving the existing kit loader's root naming convention.
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/heron-reach/heron-reach-cage.raw.glb'),export_format='GLB',export_image_format='WEBP',export_apply=True,export_yup=True)
textures=ROOT/'public/materials/heron/props'
manifest={'provenance':'Original ONSITE procedural Blender geometry, derived from the existing project prop generators. No external assets.', 'builder':'scripts/maps/art/build_heron_cage_detail.py','blender':bpy.app.version_string,'units':'metres; Blender Z up, glTF Y up','collision':'Render replacements only. Existing runtime solids and navigation are unchanged.','assets':entries,'textures':{n:hashlib.sha256((textures/n).read_bytes()).hexdigest() for n in ['cage_mesh-color.webp','goal_net-color.webp']}}
(folder/'cage-detail-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('CAGE_DETAIL',sum(e['triangles'] for e in entries),'triangles')
