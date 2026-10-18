"""ONSITE estate, authored in Blender in metres. Original architecture, donor dressing.

Run npm run evidence:layout first, then blender -b --python scripts/build-estate.py.
Editable objects and separate COLLISION/NAVIGATION collections remain in the .blend.
Only the render collection is exported. Rapier still owns the collision data in level.ts.
Material UVs are metric; the runtime supplies the existing small PBR texture library.
"""
import bpy, math, json, random, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/models'; OUT.mkdir(parents=True,exist_ok=True)
layout=json.loads((ROOT/'docs/development/evidence/layout.json').read_text())
rng=random.Random(1830)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.name != 'Collection': bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'; scene.unit_settings.scale_length=1
def collection(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
render=collection('01_RENDER / Heron Estate')
collision=collection('02_COLLISION / Rapier source solids')
nav=collection('03_NAVIGATION / stairs and spawns')
dressing=collection('04_DRESSING / credited donor props')
preview=collection('05_PREVIEW / lighting and cameras, not exported')
def move(o,c):
    for old in list(o.users_collection):old.objects.unlink(o)
    c.objects.link(o)
def mat(name,color,rough=.8,metal=0,emission=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    if emission: b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emission
    return m
mats={n:mat(n,c,r,m,e)for n,c,r,m,e in [
    ('brick',(.32,.17,.10),.9,0,0),('stock',(.37,.32,.23),.9,0,0),
    ('concrete',(.33,.36,.37),.9,0,0),('asphalt',(.07,.085,.09),.48,0,0),
    ('paving',(.32,.34,.33),.8,0,0),('steel',(.10,.13,.14),.55,.65,0),
    ('dark',(.023,.034,.041),.65,.2,0),('glass',(.065,.13,.18),.17,.65,0),
    ('lit',(.8,.42,.12),.5,0,1.5),('trim',(.36,.39,.37),.7,.1,0),
    ('soil',(.045,.035,.023),1,0,0),('leaves',(.08,.13,.045),.95,0,0),
    ('wood',(.11,.075,.045),.85,0,0),('paint',(.055,.095,.105),.85,0,0),
    ('wet',(.05,.07,.08),.1,.45,0),('amber',(.64,.35,.075),.8,0,0)]}
def xyz(x,y,z):return (x,-z,y) # game Y-up -> Blender Z-up
def finish(o,name,material,col=render):
    o.name=name;move(o,col);o.data.materials.append(mats[material]);return o
def cube(name,x,y,z,w,h,d,material='concrete',bevel=0,col=render):
    bpy.ops.mesh.primitive_cube_add(size=1,location=xyz(x,y,z));o=bpy.context.object
    o.dimensions=(w,d,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,material,col)
    # Box projection in metres. Used unchanged by Three's repeated PBR maps.
    uv=o.data.uv_layers.active
    coverage=.65 if material in ['brick','stock'] else 2
    for p in o.data.polygons:
        axis=max(range(3),key=lambda a:abs(p.normal[a]));axes=[a for a in range(3)if a!=axis]
        for li in p.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(v[axes[0]]/coverage,v[axes[1]]/coverage)
    if bevel:
        mod=o.modifiers.new('Edge wear / bevel','BEVEL');mod.width=min(bevel,min(w,h,d)*.2);mod.segments=2
        o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
    return o
def bar(name,a,b,r=.025,material='dark',col=render):
    a,b=Vector(xyz(*a)),Vector(xyz(*b));delta=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=delta.length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_quaternion=delta.to_track_quat('Z','Y');o.rotation_mode='QUATERNION'
    # Set mode before rotation assignment (Euler-to-quaternion conversion otherwise resets it).
    o.rotation_quaternion=delta.to_track_quat('Z','Y');return finish(o,name,material,col)
def rail(x,y,z,w,d):
    along=w>d;length=max(w,d)
    for i in range(math.ceil(length/.16)+1):
        t=-length/2+i*length/math.ceil(length/.16)
        bar('Gallery / steel baluster',(x+(t if along else 0),y-.52,z+(0 if along else t)),(x+(t if along else 0),y+.50,z+(0 if along else t)),.014)
    for h in [-.47,.51]:
        bar('Gallery / continuous handrail',(x-(length/2 if along else 0),y+h,z-(0 if along else length/2)),(x+(length/2 if along else 0),y+h,z+(0 if along else length/2)),.028)

for i,s in enumerate(layout['solids']):
    if s['id'].startswith('dress-'):continue # donor collider is instantiated by runtime, not rendered twice
    args=[s[k]for k in ['x','y','z','w','h','d']]
    co=cube('COLLIDER %03d / %s'%(i,s['id']),*args,'concrete',col=collision)
    co.display_type='WIRE';co.hide_render=True;co['collision_source']='src/onsite/level.ts';co['solid_id']=s['id']
    if s['mat']=='rail':rail(s['x'],s['y'],s['z'],s['w'],s['d']);continue
    if s['id']=='low-cover':
        x,z,w,d=s['x'],s['z'],s['w'],s['d']
        cube('Raised brick planter',x,.45,z,w,.9,d,'brick',.035)
        cube('Planter stone coping',x,.93,z,w+.06,.14,d+.06,'concrete',.03)
        cube('Inset dark soil',x,1.006,z,w-.28,.015,d-.28,'soil')
        for j in range(16):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=xyz(x+rng.uniform(-w*.38,w*.38),1.05+rng.uniform(0,.15),z+rng.uniform(-d*.3,d*.3)))
            o=bpy.context.object;o.scale=(rng.uniform(.17,.3),rng.uniform(.17,.3),rng.uniform(.10,.24));finish(o,'Low planting / soft foliage','leaves')
        continue
    material='brick' if s['id']=='central-screen' else s['mat']
    cube('Structure / '+s['id'],*args,material,.012 if s['h']>.1 else 0)
    if s['id']=='stair':
        cube('Stair nosing / anti slip',s['x'],s['y']+s['h']/2+.006,s['z'],s['w']-.06,.012,.045,'dark')

# Residential elevations step up behind the open galleries. Uneven roofline, repeated 3m bays.
for side in [-1,1]:
    for col in range(12):
        x=-16.5+col*3; floors=3 if col<4 else 4 if col<8 else 2
        for row in range(floors):
            y=7.45+row*2.9;z=side*10.3
            cube('Residential bay / brick',x,y,z,3,2.9,2.6,'brick',.016)
            front=side*8.96
            cube('Window / recess',x,y,front,1.6,1.83,.08,'dark')
            cube('Window / glazing',x,y,front-side*.055,1.43,1.64,.03,'lit' if (row*7+col)%7==0 else 'glass')
            for dx in [-.75,0,.75]:cube('Window / frame',x+dx,y,front-side*.09,.045,1.75,.055,'trim')
            for dy in [-.85,.28,.85]:cube('Window / transom',x,y+dy,front-side*.09,1.55,.045,.055,'trim')
            cube('Window / sill',x,y-.96,front-side*.12,1.85,.14,.40,'concrete',.02)
            cube('Facade / slab edge',x,y-1.45,side*9,3,.16,.28,'concrete',.012)
        roof=6+floors*2.9
        cube('Roof / parapet',x,roof+.23,side*9,3,.46,.25,'concrete',.018)
        cube('Roof / felt',x,roof+.03,side*10.3,3,.06,2.6,'dark')
    for col in range(6):
        z=-7.5+col*3
        for row in range(3):
            y=7.45+row*2.9;x=side*13.4
            cube('Side elevation / stock brick',x,y,z,2.6,2.9,3,'stock',.016)
            cube('Side window / recess',side*12.06,y,z,.08,1.83,1.6,'dark')
            cube('Side window / glazing',side*12.01,y,z,.03,1.64,1.43,'lit' if (col+row)%6==0 else 'glass')
            for dz in [-.75,0,.75]:cube('Side window / frame',side*11.97,y,z+dz,.055,1.75,.045,'trim')
            cube('Side window / sill',side*11.92,y-.96,z,.4,.14,1.85,'concrete',.02)
    # Slab covers all service rooms; court remains open.
    cube('Roof / perimeter room cap',0,6.06,side*12,36,.12,6,'concrete')
    cube('Roof / side room cap',side*15,6.06,0,6,.12,18,'concrete')
    for floor in [0,3]:
        for x in [-10.5,-4.5,4.5,10.5]:
            cube('Gallery / chamfered pier',x,1.38+floor,side*8.7,.28,2.76,.32,'concrete',.025)
        cube('Gallery / fascia',0,2.75+floor,side*8.8,24,.2,.36,'concrete',.012)
        for x in [-6,0,6]:
            bar('Gallery / surface conduit',(x-2.8,2.57+floor,side*8.81),(x+2.8,2.57+floor,side*8.81),.018,'dark')
            cube('Gallery / bulkhead case',x,2.45+floor,side*8.73,.6,.16,.14,'dark',.02)
            cube('Gallery / amber diffuser',x,2.44+floor,side*8.63,.45,.085,.05,'lit',.01)
    for x in [-10.7,-4.4,4.4,10.7]:
        bar('Rainwater downpipe',(x,.12,side*8.73),(x,13.5,side*8.73),.047,'dark')
        for y in [1,4,7,10,13]:cube('Downpipe bracket',x,y,side*8.78,.16,.08,.17,'steel')
    # Doors stay open. Recessed panels are confined to the wall bays, never over a real opening.
    for floor in [0,3]:
        for x in [-4.5,-1.5,1.5,4.5]:
            cube('Estate entry / teal panel',x,1.03+floor,side*8.86,.94,2.06,.045,'paint',.015)
            cube('Door / letterbox',x,1.05+floor,side*8.82,.26,.055,.025,'steel')
            cube('Door / handle',x+.31,.95+floor,side*8.8,.025,.13,.05,'trim')
            cube('Door / step',x,.04+floor,side*8.78,1.03,.08,.35,'concrete',.018)

# Both dogleg stairs gain continuous metal handrails, landing rails and wall-mounted fluorescent fixtures.
for sign in [-1,1]:
    for u in [-1.7,-.3,.3,1.7]:
        x=sign*(-15+u)
        if u<0:a=(x,.95,sign*(-3.8));b=(x,2.48,sign*(-6.65))
        else:a=(x,2.58,sign*(-6.55));b=(x,3.95,sign*(-4.0))
        bar('Stair / inclined handrail',a,b,.031)
        for t in [0,.5,1]:
            p=Vector(a).lerp(Vector(b),t);bar('Stair / rail post',(p.x,p.y-.85,p.z),tuple(p),.021)
    cube('Stair / upper bulkhead',sign*-15,5.65,sign*-7.8,1.6,.1,.25,'dark',.025)
    cube('Stair / fluorescent strip',sign*-15,5.59,sign*-7.8,1.4,.025,.17,'lit')
    cube('Stair / wall service panel',sign*-17.78,1.4,sign*-5,.08,.9,.65,'steel',.015)
    for y in [.3,2.3,5.3]:bar('Stair / service pipe',(sign*-17.7,y,sign*-8.8),(sign*-17.7,y,sign*-3.2),.022,'steel')

# Court paving follows the galleries. Low cover and kiosk still use the exact shared colliders.
for z in [-7.5,7.5]:cube('Court / raised paving strip',0,.012,z,24,.025,3,'paving')
for x in [-10.5,10.5]:cube('Court / raised paving strip',x,.012,0,3,.025,12,'paving')
cube('Service kiosk / overhanging roof',0,2.13,0,3.12,.08,3.12,'dark',.02)
for x in [-1.42,1.42]:cube('Kiosk / corner post',x,1.05,-1.49,.13,2.1,.10,'concrete',.012)
for z in [-5.8,5.8]:
    cube('Drain channel',0,.025,z,17,.035,.18,'dark')
    for i in range(68):cube('Drain grate',-8.4+i*.25,.05,z,.035,.02,.18,'steel')
# Small geometric puddles: environment reflection only, not screen-space reflections.
for x,z,rx,rz in [(-3,2,1.3,.55),(3,-2,1.1,.4),(-7,6.1,1.8,.34),(3,6.2,1.2,.3),(-10,-.8,.4,1.3)]:
    pts=[xyz(x+math.cos(a*math.tau/16)*rx*rng.uniform(.8,1.1),.031,z+math.sin(a*math.tau/16)*rz*rng.uniform(.8,1.1))for a in range(16)]
    mesh=bpy.data.meshes.new('Puddle boundary');mesh.from_pydata(pts,[],[list(range(16))]);o=bpy.data.objects.new('Rain / shallow puddle',mesh);render.objects.link(o);o.data.materials.append(mats['wet'])
# Bike rails in the cycle store and small bollards aligned with walls.
for x in [-4,-3.2,-2.4,-1.6]:
    for z in [11.7,12.3]:bar('Cycle store / hoop leg',(x,0,z),(x,.85,z),.026,'steel')
    bar('Cycle store / hoop',(x,.85,11.7),(x,.85,12.3),.026,'steel')

# Reference-only collision and nav objects are editable in the .blend but excluded from the GLB.
for i,route in enumerate(layout['stairRoutes']):
    for a,b in zip(route,route[1:]):bar('NAV / stair %s'%i,(a['x'],a['y']+.08,a['z']),(b['x'],b['y']+.08,b['z']),.025,'amber',nav)
for name,p in [('PLAYER',layout['spawn'])]+[('BOT %s'%i,p)for i,p in enumerate(layout['botSpawns'])]:
    bpy.ops.object.empty_add(type='ARROWS',location=xyz(p['x'],p['y'],p['z']));o=bpy.context.object;o.name=name;move(o,nav)
collision.hide_render=True;nav.hide_render=True
collision.hide_viewport=True;nav.hide_viewport=True

# Licensed donor meshes are assembled here for editing; streamed separately to preserve instancing/maps.
placements=[
    dict(asset='covered_car',x=7,y=0,z=-1.3,height=1.35,ry=0,collision=True),
    dict(asset='rollershutter_door',x=0,y=.04,z=1.515,height=1.95,ry=math.pi,collision=False),
    dict(asset='metal_trash_can',x=-11.3,y=0,z=.95,height=.95,ry=0,collision=True),
    dict(asset='metal_trash_can',x=-11.3,y=0,z=1.9,height=.95,ry=.3,collision=True),
    dict(asset='trashbag',x=-11.15,y=.02,z=2.75,height=.48,ry=.2,collision=False),
    dict(asset='exterior_aircon_unit',x=-4.6,y=4.8,z=-8.75,height=.65,ry=0,collision=False),
    dict(asset='exterior_aircon_unit',x=4.6,y=4.8,z=-8.75,height=.65,ry=0,collision=False),
    dict(asset='concrete_road_barrier_02',x=10.25,y=3,z=0,height=.75,ry=math.pi/2,collision=True),
    dict(asset='street_lamp_01',x=-8,y=0,z=-4.9,height=4.2,ry=0,collision=False),
    dict(asset='street_lamp_01',x=8,y=0,z=4.9,height=4.2,ry=math.pi,collision=False),
    dict(asset='trashbag',x=-11.2,y=.03,z=3.1,height=.62,ry=1.7,collision=False),
    dict(asset='trashbag',x=-10.8,y=.03,z=2.65,height=.42,ry=-.8,collision=False),
    dict(asset='trashbag',x=-11.5,y=.03,z=3.6,height=.5,ry=.6,collision=False),
    dict(asset='trashbag',x=10.7,y=.03,z=-7.8,height=.48,ry=2.4,collision=False),
    dict(asset='cardboard_box_01',x=-10.9,y=.03,z=3.8,height=.43,ry=.24,collision=False),
    dict(asset='cardboard_box_01',x=10.8,y=.03,z=-8.2,height=.55,ry=1.1,collision=False),
    dict(asset='old_tyre',x=8.4,y=.03,z=-3.5,height=.3,ry=.45,collision=False),
    dict(asset='rusted_wheel_rim_01',x=8.8,y=.03,z=-3.9,height=.24,ry=-.8,collision=False),
    dict(asset='cement_bag',x=-10.8,y=.03,z=-7.8,height=.23,ry=.4,collision=False),
    dict(asset='wooden_crate_02',x=10,y=.04,z=0,height=.65,ry=0,collision=False),
]
for p in placements:
    file=OUT/'donors'/(p['asset']+'.glb')
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(file))
    added=set(bpy.data.objects)-before;roots=[o for o in added if o.parent not in added]
    meshes=[o for o in added if o.type=='MESH'];bpy.context.view_layer.update()
    pts=[o.matrix_world@Vector(v)for o in meshes for v in o.bound_box]
    lo=Vector([min(v[i]for v in pts)for i in range(3)]);hi=Vector([max(v[i]for v in pts)for i in range(3)])
    k=p['height']/(hi.z-lo.z);center=(lo+hi)/2
    root=bpy.data.objects.new('DONOR / '+p['asset'],None);dressing.objects.link(root)
    shift=Matrix.Translation((-center.x*k,-center.y*k,-lo.z*k))@Matrix.Scale(k,4)
    for o in roots:o.matrix_world=shift@o.matrix_world;o.parent=root
    for o in added:move(o,dressing)
    root.location=xyz(p['x'],p['y'],p['z']);root.rotation_euler.z=p['ry']
    # Record game-space dimensions before yaw; collider shares these actual bounds.
    p['size']=[round((hi.x-lo.x)*k,4),p['height'],round((hi.y-lo.y)*k,4)]
    p['source']='public/models/donors/provenance.json'
(ROOT/'src/onsite/dressing.json').write_text(json.dumps(placements,indent=2)+'\n')

# Blender-only review camera/light. Three.js constructs the actual runtime lighting.
bpy.ops.object.camera_add(location=(25,-29,23));cam=bpy.context.object;move(cam,preview);cam.name='Review / complete estate';cam.rotation_euler=(Vector((0,0,3))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=30;scene.camera=cam
bpy.ops.object.light_add(type='SUN',location=(10,-10,25));sun=bpy.context.object;move(sun,preview);sun.rotation_euler=(.4,-.5,-.6);sun.data.energy=2
scene.world.color=(.12,.17,.24)
scene['ONSITE']='Heron Estate / metres / two physical floors, upper elevations render-only'
scene['DONORS']='IRONLINE props credited individually in public/models/donors/provenance.json'
scene['COLLISION']='src/onsite/level.ts + dressing.json. Do not derive navigation from render facade/foliage.'
import sys
sys.path.insert(0,str(ROOT/'scripts'))
from dress_foliage import dress_foliage
dress_foliage()
from dress_estate import dress_estate
dress_estate(ROOT,True)
from prepare_estate_materials import prepare_materials
from build_homes import build_homes
build_homes(ROOT,True)
prepare_materials(ROOT)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/onsite-heron-court.blend'))

import sys
sys.path.insert(0,str(ROOT/'scripts'))
from export_estate import export_estate
export_estate(ROOT,render)
