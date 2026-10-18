"""Original ONSITE prototype meshes, generated with Blender 4.3+. No external assets.
Run: blender -b --python scripts/build-assets.py
"""
import bpy, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'public/models'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'assets/blender';SOURCE.mkdir(parents=True,exist_ok=True)
def material(name,color,rough=.7,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    return m
black=material('Black cotton',(.018,.022,.028));rubber=material('Black rubber',(.009,.011,.015));steel=material('Painted steel',(.035,.045,.055),.35,.65);skin=material('Brown skin',(.19,.085,.045));amber=material('Warm diffuser',(1,.55,.17));wood=material('Weathered timber',(.15,.11,.075));concrete=material('Concrete',(.25,.27,.29))
def clear():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def cube(name,loc,size,mat,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=2
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def sphere(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o
def cylinder(name,loc,r,depth,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o
def export(name):
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(name+'.blend')))
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',export_yup=True)
clear()
cylinder('Pole',(0,0,2),.055,4,steel)
cube('Base',(0,0,.13),(.3,.3,.26),steel)
cube('Lantern canopy',(0,0,4.12),(.58,.58,.12),steel)
cube('Lantern diffuser',(0,0,3.94),(.35,.35,.25),amber)
export('estate-lamp')
clear()
for x in [-.65,.65]:
    cube('Bench support',(x,0,.23),(.12,.55,.46),steel)
for y in [-.24,0,.24]:cube('Seat slat',(0,y,.5),(1.8,.19,.09),wood)
for z in [.8,1.02]:cube('Back slat',(0,.28,z),(1.8,.08,.17),wood)
export('estate-bench')
clear()
# Stylised placeholder opponent. Z up in Blender, forward -Y; exported forward +Z.
# Named components allow a lightweight walk cycle; this is not a finished skinned character.
sphere('Hoodie torso',(0,0,1.15),(.29,.19,.36),black)
cube('Hoodie hem',(0,0,.92),(.46,.31,.12),black)
sphere('Hood',(0,.01,1.62),(.23,.21,.27),black)
sphere('Mask',(0,-.155,1.63),(.16,.07,.18),rubber)
cube('Eye opening',(0,-.216,1.7),(.23,.02,.045),skin,.008)
for x in [-.065,.065]:sphere('Eye',(x,-.23,1.7),(.012,.008,.011),rubber)
for side,x in [('L',-.145),('R',.145)]:
    sphere('Leg_'+side,(x,0,.5),(.13,.145,.43),black)
    cube('Trainer_'+side,(x,-.07,.09),(.24,.4,.17),rubber,.055)
    arm=sphere('Arm_'+side,(x*2,-.08,1.12),(.12,.13,.31),black);arm.rotation_euler[0]=-.65
    sphere('Glove_'+side,(x*1.8,-.23,1.02),(.095,.11,.12),rubber)
cube('Opponent prop',(0,-.36,1.1),(.12,.55,.13),steel)
export('hooded-opponent')
clear()
# Fictional compact game weapon; simple original silhouette, no imported model or branding.
cube('Receiver',(0,0,0),(.12,.42,.15),steel)
cube('Handguard',(0,-.34,.015),(.11,.33,.12),rubber)
cube('Stock',(0,.3,-.025),(.11,.25,.14),rubber)
cube('Grip',(0,.08,-.14),(.09,.1,.22),rubber)
cube('Magazine',(0,-.13,-.15),(.08,.14,.24),steel)
barrel=cylinder('Barrel',(0,-.57,.02),.028,.2,steel);barrel.rotation_euler[0]=math.pi/2
for x in [-.065,.065]:cube('Sight side',(x,-.08,.16),(.018,.04,.15),steel,.008)
cube('Sight top',(0,-.08,.235),(.15,.04,.018),steel,.008)
for x in [-.11,.11]:
    sphere('Glove',(x,.05,-.14),(.065,.13,.08),rubber)
    sphere('Sleeve',(x*1.5,.27,-.2),(.09,.24,.1),black)
export('first-person-prop')
