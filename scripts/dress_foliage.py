"""Original small curved leaves for the estate planters, authored in Blender."""
import bpy,random,math
from mathutils import Vector

def dress_foliage():
    rng=random.Random(1938)
    for o in bpy.data.objects:
        if not o.name.startswith('Low planting / soft foliage') or o.get('onsite_leaf_detail'):continue
        verts=[];faces=[]
        for i in range(56):
            normal=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-.45,1))).normalized()
            point=normal*rng.uniform(.45,.95)
            q=Vector((0,0,1)).rotation_difference(normal)
            k=rng.uniform(.75,1.25);base=len(verts)
            for v in [(-.28,0,0),(0,-.12,0),(.28,0,0),(0,.12,0),(0,0,.045)]:
                verts.append(point+q@(Vector(v)*k))
            for a,b in [(0,1),(1,2),(2,3),(3,0)]:faces.append((base+a,base+b,base+4))
        mesh=bpy.data.meshes.new('Hedge / individual curved leaves');mesh.from_pydata(verts,[],faces);mesh.materials.append(o.data.materials[0]);mesh.update()
        o.data=mesh;o['onsite_leaf_detail']=True
