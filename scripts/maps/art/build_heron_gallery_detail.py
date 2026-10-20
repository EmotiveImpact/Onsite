"""Original Blender supports and existing ONSITE generated pigeon-net artwork.

Render-only panels above the existing gallery parapets; doors/stair connections stay open.
Run with Blender 4.3+: blender -b --python-exit-code 1 --python <this file>
"""
from pathlib import Path
import sys,json,hashlib
import bpy
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(HERE))
from heron_art_mesh import Builder

source=ROOT/'docs/maps/heron-reach-32/art/generated/decals/hr_decal_pigeon_net.png'
texture=ROOT/'public/materials/heron/decals/pigeon-net.webp'
Image.open(source).convert('RGBA').resize((512,512),Image.Resampling.LANCZOS).save(texture,quality=92,method=6)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
col=bpy.data.collections.new('HR_GALLERY_DETAIL');bpy.context.scene.collection.children.link(col)
B=Builder(lambda _:col)
materials={}
def material(name):
    if name in materials:return materials[name]
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.8
    if name=='hr_pigeon_net':
        im=bpy.data.images.load(str(texture));im.pack();node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
        m.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(node.outputs['Alpha'],bs.inputs['Alpha'])
        m.surface_render_method='DITHERED';m.use_backface_culling=False
    else:bs.inputs['Base Color'].default_value=(.025,.03,.028,1);bs.inputs['Metallic'].default_value=.6
    materials[name]=m;return m

panels=[]
for z in [38.96,81.04]:
    for x in [48,51,54,90,93,96]:
        width=2.85;y0=4.12;y1=5.75
        # Sagged upper cable; mesh follows it. Bottom sits on the existing parapet.
        for a,b in [(0,width/2),(width/2,width)]:
            ha=y1-(.06 if a==width/2 else 0);hb=y1-(.06 if b==width/2 else 0)
            B.quad('gallery/net','hr_pigeon_net',(x+a,y0,z),(x+b,y0,z),(x+b,hb,z),(x+a,ha,z),uv=[(a*2.5,0),(b*2.5,0),(b*2.5,(hb-y0)*2.5),(a*2.5,(ha-y0)*2.5)])
            B.cylinder('gallery/frame','hr_net_support',(x+a,ha,z),(x+b,hb,z),.009,6)
        for px in [x,x+width]:B.cylinder('gallery/frame','hr_net_support',(px,4.02,z),(px,5.8,z),.018,6)
        panels.append({'x':x,'z':z,'minY':y0,'maxY':y1,'width':width})
objects=B.build(material)
bpy.context.preferences.filepaths.save_version=0
folder=ROOT/'assets/blender/heron-reach'
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'gallery-detail.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/heron-reach/heron-reach-gallery.raw.glb'),export_format='GLB',export_image_format='WEBP',export_apply=True,export_yup=True)
(folder/'gallery-detail-manifest.json').write_text(json.dumps({'provenance':'Supports: original ONSITE Blender geometry. Net: existing ONSITE ChatGPT-generated artwork, encoding/resizing only; source retained.',
    'source':str(source.relative_to(ROOT)),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'textureSHA256':hashlib.sha256(texture.read_bytes()).hexdigest(),
    'blender':bpy.app.version_string,'units':'metres; Blender Z up, glTF Y up','collision':'None; above existing solid gallery parapets, away from door/stair openings.',
    'panels':panels,'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects)},indent=2)+'\n')
