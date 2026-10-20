"""Original render-only shop backdrops and practical fittings, in the existing shop shells.

blender -b --python-exit-code 1 --python scripts/maps/art/build_heron_shop_detail.py
All paths through the shops and all collision remain owned by the TypeScript layout.
"""
from pathlib import Path
import sys,json
import bpy
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from heron_art_mesh import Builder

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system='METRIC'
bpy.context.scene.unit_settings.scale_length=1
col=bpy.data.collections.new('HR_SHOP_DETAIL');bpy.context.scene.collection.children.link(col)
B=Builder(lambda _:col)
spec=json.loads((ROOT/'docs/maps/heron-reach-32/blueprints/build-spec.json').read_text())
materials={}
def material(name):
    if name in materials:return materials[name]
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.75
    if name.startswith('hr_shop_image_'):
        texture='corner-shop-interior' if name.endswith('corner') else 'launderette-interior'
        im=bpy.data.images.load(str(ROOT/'public/materials/heron/shops'/(texture+'.webp')));im.pack()
        node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
        m.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
        m.node_tree.links.new(node.outputs['Color'],bs.inputs['Emission Color'])
        bs.inputs['Emission Strength'].default_value=.9
    elif name=='hr_shop_strip':
        bs.inputs['Base Color'].default_value=(.9,.8,.6,1)
        bs.inputs['Emission Color'].default_value=(1,.8,.5,1);bs.inputs['Emission Strength'].default_value=2
    else:
        bs.inputs['Base Color'].default_value=(.13,.15,.15,1);bs.inputs['Metallic'].default_value=.4
    materials[name]=m;return m

shops=[]
for shop in spec['shops']:
    if shop['name'] not in ['THE CORNER','LAUNDERETTE','WASHHOUSE']:continue
    x,z,w,d=shop['rect'];grp=shop['id']+'/interior'
    image='hr_shop_image_corner' if shop['name']=='THE CORNER' else 'hr_shop_image_laundry'
    # Cards sit against the actual back wall, facing into the room. The rear doorway stays clear.
    # The existing three-dimensional shelves/washers remain in front and supply parallax.
    for a,b in [(x+.26,x+w/2-1.05),(x+w/2+1.05,x+w-.26)]:
        if b-a<.4:continue
        zc=z+d-.205
        B.quad(grp,image,(b,.28,zc),(a,.28,zc),(a,2.67,zc),(b,2.67,zc),uv=[(1,0),(0,0),(0,1),(1,1)])
    # Practical fittings remain above 2.55 m clear head height, never across doorways.
    for u in [.25,.75]:
        cx=x+w*u
        B.box(grp,'hr_shop_fitting',cx-.7,cx+.7,2.65,2.75,z+.8,z+1.05)
        B.box(grp,'hr_shop_strip',cx-.64,cx+.64,2.635,2.65,z+.82,z+1.03,faces='-y')
    shops.append({'id':shop['id'],'rect':shop['rect'],'rearDoorClearWidth':2.1})

objects=B.build(material)
bpy.context.preferences.filepaths.save_version=0
folder=ROOT/'assets/blender/heron-reach'
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'shop-detail.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models/heron-reach/heron-reach-shops.raw.glb'),export_format='GLB',export_image_format='WEBP',export_apply=True,export_yup=True)
(folder/'shop-detail-manifest.json').write_text(json.dumps({'provenance':'Original ONSITE Blender geometry; backdrops from the project ChatGPT images, see public/materials/heron/shops/manifest.json.','builder':'scripts/maps/art/build_heron_shop_detail.py','blender':bpy.app.version_string,'units':'metres; Blender Z up; glTF Y up','collision':'None. Backdrops are against existing solid back walls, clear of rear exits.','shops':shops,'objects':len(objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects)},indent=2)+'\n')
