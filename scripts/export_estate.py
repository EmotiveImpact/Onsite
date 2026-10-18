"""Export Blender estate architecture only, with local vertex occlusion."""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def export_estate(ROOT, render):
    OUT=ROOT/'public/models'
    scene=bpy.context.scene
    # Runtime materials are assigned by name; do not embed another copy of the PBR images.
    for material in {o.data.materials[0] for o in render.objects if o.type=='MESH'}:
        for node in list(material.node_tree.nodes):
            if node.type not in ['BSDF_PRINCIPLED','OUTPUT_MATERIAL']:material.node_tree.nodes.remove(node)
    # Apply modifiers to export copies, join by material to limit draw calls, bake local occlusion into vertices.
    bpy.ops.object.select_all(action='DESELECT')
    deps=bpy.context.evaluated_depsgraph_get();groups={}
    for o in list(render.objects):
        if o.type!='MESH':continue
        mesh=bpy.data.meshes.new_from_object(o.evaluated_get(deps));mesh.transform(o.matrix_world)
        copy=bpy.data.objects.new('export-'+o.name,mesh);scene.collection.objects.link(copy)
        groups.setdefault(o.data.materials[0].name,[]).append(copy)
    export=[]
    for name,objects in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='Estate / '+name;export.append(o)
    vertices=[];faces=[]
    for o in export:
        offset=len(vertices);vertices.extend(v.co.copy()for v in o.data.vertices);faces.extend([offset+i for i in p.vertices]for p in o.data.polygons)
    bvh=BVHTree.FromPolygons(vertices,faces)
    for o in export:
        mesh=o.data;colors=mesh.color_attributes.new(name='EstateOcclusion',type='FLOAT_COLOR',domain='CORNER')
        for poly in mesh.polygons:
            n=poly.normal;side=n.cross(Vector((0,0,1)))
            if side.length<.1:side=n.cross(Vector((1,0,0)))
            side.normalize();up=n.cross(side).normalized()
            for li in poly.loop_indices:
                v=mesh.vertices[mesh.loops[li].vertex_index].co;origin=v+n*.035
                visible=0
                for k in range(5):
                    a=k*math.tau/5;direction=(n*.72+(side*math.cos(a)+up*math.sin(a))*.69).normalized()
                    hit=bvh.ray_cast(origin,direction,2.5)[0];visible+=hit is None
                ao=.55+.45*visible/5
                colors.data[li].color=(ao,ao,ao,1)
        print('AO',o.name,len(mesh.vertices),flush=True)
    bpy.ops.object.select_all(action='DESELECT')
    for o in export:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/'onsite-heron-court.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=False,export_cameras=False,export_lights=False,export_vertex_color='ACTIVE')
    manifest=dict(source='assets/blender/onsite-heron-court.blend',builder='scripts/build-estate.py',metres=True,
        renderObjects=len(render.objects),runtimeMeshes=len(export),vertices=len(vertices),
        collisionSource='src/onsite/level.ts',navigationSource='src/onsite/navigation.ts',
        layoutSha256=hashlib.sha256((ROOT/'docs/development/evidence/layout.json').read_bytes()).hexdigest(),
        glbBytes=(OUT/'onsite-heron-court.glb').stat().st_size,
        notes='Original Blender architecture; separate credited donor prop GLBs. Local vertex occlusion bake. Runtime lights rebuilt in Three.js.')
    (OUT/'onsite-heron-court.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest),flush=True)

if __name__=='__main__':
    ROOT=Path(__file__).resolve().parents[1]
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/onsite-heron-court.blend'))
    import sys
    sys.path.insert(0,str(ROOT/'scripts'))
    from dress_foliage import dress_foliage
    dress_foliage()
    from prepare_estate_materials import prepare_materials
    prepare_materials(ROOT)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/onsite-heron-court.blend'))
    export_estate(ROOT,bpy.data.collections['01_RENDER / Heron Estate'])
