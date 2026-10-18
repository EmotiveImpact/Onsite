"""Blender finishing for the credited M4/arms: extend open shoulder sleeves behind the view.
Input is a decoded copy of the unchanged licensed donor GLB. Geometry at fingers/grips is preserved.
"""
import bpy,bmesh,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath='/tmp/onsite-rifle-unpacked.glb')
changes=[]
for o in bpy.data.objects:
 if o.type!='MESH' or 'arms' not in [m.name for m in o.data.materials]:continue
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0002)
 edges=[e for e in bm.edges if e.is_boundary];before=len(bm.verts)
 # One short transition ring and one full sleeve continuation. The gun is K=2 scale,
 # so the 0.8-unit extension is 40 cm in the playable. All new vertices inherit skin weights.
 for distance,drop in [(.23,.035),(.57,.065)]:
  result=bmesh.ops.extrude_edge_only(bm,edges=edges)
  new=[v for v in result['geom']if isinstance(v,bmesh.types.BMVert)]
  for v in new:v.co.y-=distance;v.co.z-=drop
  nset=set(new);edges=[e for e in bm.edges if e.is_boundary and all(v in nset for v in e.verts)]
 bm.normal_update();bm.to_mesh(o.data);bm.free();o.data.update();changes.append({'mesh':o.name,'newVertices':len(o.data.vertices)-before,'purpose':'Continue the open upper sleeves behind the camera; preserve authored hands/grip.'})
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file:image.pack()
 if image.source=='FILE':assert image.size[0]>0 and image.size[1]>0,'Empty packed image: '+image.name
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene['ONSITE']='Licensed M4/hands finishing; K=2 donor rig, runtime scale .5; no imported motion clips.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/onsite-carbine.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/onsite-carbine.glb'),export_format='GLB',export_animations=False,export_yup=True,export_cameras=False,export_lights=False)
p=ROOT/'public/models/onsite-carbine.glb'
(ROOT/'public/models/onsite-carbine.json').write_text(json.dumps({'source':'assets/blender/onsite-carbine.blend','donor':'public/models/donors/m4a1-hands.glb','donorSHA256':hashlib.sha256((ROOT/'public/models/donors/m4a1-hands.glb').read_bytes()).hexdigest(),'license':'CC-BY-4.0','notices':'public/licenses/DONOR-ASSETS.md','changes':changes,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n')
print(changes,flush=True)
