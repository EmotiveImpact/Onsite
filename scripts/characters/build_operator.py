"""Original ONSITE operator, authored in metres with an editable weighted rig.

blender -b --python-exit-code 1 --python scripts/characters/build_operator.py
No donor character, clothing, rifle, texture, skeleton or animation is used.
The separate old hooded-opponent.blend/GLB is intentionally preserved.
"""
import bpy, math, json, hashlib, random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'assets/blender/characters'
OUT = ROOT/'public/models'
SOURCE.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1

def material(name, colour, roughness=.8, metallic=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*colour,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*colour,1)
    p.inputs['Roughness'].default_value=roughness
    p.inputs['Metallic'].default_value=metallic
    return m

mats={
 'cotton': material('ONSITE / washed black cotton',(.025,.029,.034),.93),
 'rib': material('ONSITE / black knit and reinforced panels',(.012,.015,.019),.86),
 'seam': material('ONSITE / charcoal stitching',(.055,.061,.068),.86),
 'rubber': material('ONSITE / black rubber and gloves',(.009,.011,.014),.73),
 'steel': material('ONSITE / worn black gunmetal',(.04,.048,.055),.43,.65),
 'skin': material('ONSITE / brown skin',(.21,.09,.043),.72),
 'eye': material('ONSITE / eye catchlight',(.42,.35,.29),.3),
}

# Original small tile: woven cotton, no photograph or downloaded image pixels.
TEXTURES=ROOT/'assets/textures/operators';TEXTURES.mkdir(parents=True,exist_ok=True)
texture_records=[]
for normal in [False,True]:
    name='black-cotton-normal' if normal else 'black-cotton-colour'
    image=bpy.data.images.new(name,width=128,height=128,alpha=False)
    if normal:image.colorspace_settings.name='Non-Color'
    rng=random.Random(714);pixels=[]
    for y in range(128):
        for x in range(128):
            a=math.sin(x*math.pi/2);b=math.sin(y*math.pi/2)
            if normal:pixels.extend((.5+a*.055,.5+b*.055,1,1))
            else:
                shade=.17+.007*a*b+rng.uniform(-.005,.005);pixels.extend((shade,shade*1.08,shade*1.17,1))
    image.pixels=pixels;image.filepath_raw=str(TEXTURES/(name+'.png'));image.file_format='PNG';image.save()
    texture_records.append({'file':str(Path(image.filepath_raw).relative_to(ROOT)),'sha256':hashlib.sha256(Path(image.filepath_raw).read_bytes()).hexdigest(),'source':'Original deterministic weave/noise in scripts/characters/build_operator.py'})
    for key in ['cotton','rib']:
        nodes=mats[key].node_tree.nodes;links=mats[key].node_tree.links
        tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='REPEAT'
        bsdf=nodes.get('Principled BSDF')
        if normal:
            nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.14
            links.new(tex.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bsdf.inputs['Normal'])
        else:
            # Black pigment is baked into the small original tile, avoiding a node
            # multiply that Blender's glTF exporter would silently omit.
            links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])

# Anatomical joints are authored in Blender's Z-up, forward -Y convention.
# The GLB is Y-up, forward +Z. The WWB adapter turns the model by PI to -Z.
joints={
 'Root': ((0,0,0),(0,0,.15),None),
 'Pelvis': ((0,0,.89),(0,0,1.03),'Root'),
 'Spine': ((0,0,1.03),(0,0,1.22),'Pelvis'),
 'Chest': ((0,0,1.22),(0,0,1.42),'Spine'),
 'Neck': ((0,0,1.42),(0,0,1.5),'Chest'),
 'Head': ((0,0,1.5),(0,0,1.69),'Neck'),
 'Thigh_L': ((-.115,0,.89),(-.12,-.015,.50),'Pelvis'),
 'Shin_L': ((-.12,-.015,.50),(-.12,0,.13),'Thigh_L'),
 'Foot_L': ((-.12,0,.13),(-.12,-.18,.08),'Shin_L'),
 'Thigh_R': ((.115,0,.89),(.12,-.015,.50),'Pelvis'),
 'Shin_R': ((.12,-.015,.50),(.12,0,.13),'Thigh_R'),
 'Foot_R': ((.12,0,.13),(.12,-.18,.08),'Shin_R'),
 'UpperArm_L': ((-.225,0,1.37),(-.189,-.261,1.206),'Chest'),
 'Forearm_L': ((-.189,-.261,1.206),(.015,-.49,1.245),'UpperArm_L'),
 'Hand_L': ((.015,-.49,1.245),(.055,-.51,1.265),'Forearm_L'),
 'UpperArm_R': ((.225,0,1.37),(.28,-.02,1.12),'Chest'),
 'Forearm_R': ((.28,-.02,1.12),(.105,-.255,1.185),'UpperArm_R'),
 'Hand_R': ((.105,-.255,1.185),(.095,-.30,1.22),'Forearm_R'),
 'Weapon': ((.085,-.27,1.265),(.085,-.75,1.265),'Chest'),
 'MuzzleSocket': ((.085,-.835,1.265),(.085,-.86,1.265),'Weapon'),
}
arm=bpy.data.armatures.new('ONSITE operator / original anatomical rig')
rig=bpy.data.objects.new('ONSITE_OperatorRig',arm);scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,(head,tail,parent) in joints.items():
    bone=arm.edit_bones.new(name);bone.head=head;bone.tail=tail
    if parent:bone.parent=arm.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
rig.show_in_front=True
parts={name:[] for name in ['OperatorBody','Hood_up','Hood_down','Trainers_court','Trainers_runner','Trainers_high']}

def finish(o,name,mat,bone,part='OperatorBody',smooth=True):
    # Variant meshes add at most three draws: one hood material, two trainer materials.
    if part.startswith('Hood_'):mat='cotton'
    if part.startswith('Trainers_') and mat in ['rib','seam']:mat='cotton'
    o.name=name;o.data.materials.append(mats[mat])
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    # Applying transforms before weighting gives an editable mesh in rig space.
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Metric cloth UV')
    for polygon in o.data.polygons:
        major=max(range(3),key=lambda i:abs(polygon.normal[i]));axes=[i for i in range(3) if i!=major]
        for li in polygon.loop_indices:
            p=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(p[axes[0]]*12,p[axes[1]]*12)
    if bone:
        group=o.vertex_groups.new(name=bone);group.add(list(range(len(o.data.vertices))),1,'REPLACE')
    parts[part].append(o);o.select_set(False);return o

def sphere(name,p,s,mat,bone,part='OperatorBody',seg=12,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=p)
    o=bpy.context.object;o.scale=s;return finish(o,name,mat,bone,part)

def box(name,p,s,mat,bone,part='OperatorBody',bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.dimensions=s
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        m=o.modifiers.new('Rounded manufactured edge','BEVEL');m.width=bevel;m.segments=2
        bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
    return finish(o,name,mat,bone,part,False)

def line(name,a,b,r,mat,bone,part='OperatorBody',vertices=6):
    a,b=Vector(a),Vector(b);d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d.length,location=(a+b)*.5)
    o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y')
    return finish(o,name,mat,bone,part)

def loft(name,rows,mat,bone,part='OperatorBody',segments=16,cut=None):
    # Rows are (height, centre x, centre y, halfwidth, halfdepth).
    verts=[];faces=[]
    for k,(z,x,y,rx,ry) in enumerate(rows):
        for i in range(segments):
            a=i*math.tau/segments
            # Subtle asymmetric folds are silhouette geometry, not painted stripes.
            fold=1+.025*math.sin(i*3.7+k*1.8)
            verts.append((x+rx*math.sin(a)*fold,y-ry*math.cos(a)*fold,z))
    for k in range(len(rows)-1):
        for i in range(segments):
            a=(i+.5)*math.tau/segments
            if cut and cut(k,a):continue
            j=(i+1)%segments
            faces.append((k*segments+i,k*segments+j,(k+1)*segments+j,(k+1)*segments+i))
    if not cut:
        faces.extend([tuple(reversed(range(segments))),tuple((len(rows)-1)*segments+i for i in range(segments))])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o)
    return finish(o,name,mat,bone,part)

# Joggers: real hip/knee/ankle ownership, tapered legs, cuffs and reinforced seams.
loft('Jogger seat',[(.78,0,.018,.185,.12),(.835,0,.012,.23,.145),(.91,0,0,.23,.147),(.975,0,0,.208,.14)],'cotton','Pelvis',segments=24)
for side,x in [('L',-.12),('R',.12)]:
    leg=loft('Continuous jogger leg '+side,[(.15,x,0,.061,.058),(.22,x,.006,.066,.066),(.37,x,-.012,.08,.075),(.45,x,-.014,.087,.086),(.50,x,-.014,.09,.092),(.55,x,-.008,.095,.098),(.66,x,.002,.101,.108),(.80,x,.008,.104,.119),(.93,x,0,.107,.125)],'cotton',None,segments=24)
    thigh=leg.vertex_groups.new(name='Thigh_'+side);shin=leg.vertex_groups.new(name='Shin_'+side)
    for v in leg.data.vertices:
        t=max(0,min(1,(v.co.z-.43)/.14));thigh.add([v.index],t,'REPLACE');shin.add([v.index],1-t,'REPLACE')
    loft('Elastic cuff '+side,[(.14,x,0,.06,.061),(.185,x,0,.063,.063)],'rib','Shin_'+side)
    outer=x+(.09 if x>0 else -.09)
    line('Trouser side seam '+side,(outer,.02,.55),(outer,.015,.86),.003,'seam','Thigh_'+side)
    line('Pocket welt '+side,(outer,-.035,.80),(outer-.015*(1 if x>0 else -1),-.086,.91),.006,'rib','Thigh_'+side)

# Fuse the three overlapping trouser volumes into one actual garment surface.
# This removes open hip joins and coplanar intersections without moving any joint.
pants=[o for o in parts['OperatorBody'] if o.name=='Jogger seat' or o.name.startswith('Continuous jogger leg')]
bpy.ops.object.select_all(action='DESELECT')
for o in pants:o.select_set(True);parts['OperatorBody'].remove(o)
bpy.context.view_layer.objects.active=pants[0];bpy.ops.object.join();pants=bpy.context.object
remesh=pants.modifiers.new('Continuous trouser fabric surface','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.016;remesh.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth=pants.modifiers.new('Relax garment silhouette','SMOOTH');smooth.factor=.65;smooth.iterations=3;bpy.ops.object.modifier_apply(modifier=smooth.name)
decimate=pants.modifiers.new('Efficient garment topology','DECIMATE');decimate.ratio=.60;bpy.ops.object.modifier_apply(modifier=decimate.name)
pants.vertex_groups.clear()
groups={n:pants.vertex_groups.new(name=n) for n in ['Pelvis','Thigh_L','Thigh_R','Shin_L','Shin_R']}
for v in pants.data.vertices:
    side='L' if v.co.x<0 else 'R';z=v.co.z
    if z>.76:
        t=max(0,min(1,(z-.76)/.15));groups['Pelvis'].add([v.index],t,'REPLACE');groups['Thigh_'+side].add([v.index],1-t,'REPLACE')
    else:
        t=max(0,min(1,(z-.43)/.14));groups['Thigh_'+side].add([v.index],t,'REPLACE');groups['Shin_'+side].add([v.index],1-t,'REPLACE')
finish(pants,'Continuous weighted joggers','cotton',None)

# Hoodie torso has continuous weighted rows across the spine, avoiding floating body pieces.
torso=loft('Hoodie body',[(.92,0,0,.22,.151),(.99,0,0,.225,.153),(1.08,0,0,.219,.15),(1.16,0,0,.225,.155),(1.26,0,0,.23,.153),(1.34,0,.005,.225,.146),(1.41,0,.008,.19,.12),(1.44,0,.01,.10,.085)],'cotton',None,segments=32)
groups={name:torso.vertex_groups.new(name=name) for name in ['Pelvis','Spine','Chest']}
for v in torso.data.vertices:
    z=v.co.z
    if z<1.03:
        t=max(0,min(1,(z-.94)/.14));groups['Pelvis'].add([v.index],1-t,'REPLACE');groups['Spine'].add([v.index],t,'REPLACE')
    else:
        t=max(0,min(1,(z-1.08)/.20));groups['Spine'].add([v.index],1-t,'REPLACE');groups['Chest'].add([v.index],t,'REPLACE')
loft('Hoodie ribbed waistband',[(.905,0,0,.230,.161),(.96,0,0,.232,.163)],'rib','Pelvis',segments=24)
loft('Balaclava neck and hoodie collar',[(1.37,0,.007,.098,.085),(1.43,0,.006,.09,.082),(1.50,0,0,.081,.078),(1.54,0,0,.081,.08)],'rib','Neck',segments=24)
# A shaped kangaroo pocket and zipper-free hood preserve a recognisable everyday hoodie.
box('Kangaroo pocket',(0,-.152,1.02),(.27,.018,.115),'rib','Spine',bevel=.018)
for sign in [-1,1]:
    line('Pocket opening',(sign*.09,-.168,1.06),(sign*.13,-.16,1.0),.004,'seam','Spine')
    line('Drawcord',(sign*.047,-.126,1.40),(sign*.054,-.159,1.235),.0035,'rib','Chest')
    line('Drawcord aglet',(sign*.054,-.159,1.235),(sign*.054,-.159,1.216),.004,'steel','Chest')
    line('Shoulder stitched seam',(sign*.085,-.07,1.403),(sign*.222,-.025,1.364),.003,'seam','Chest')

for side in ['L','R']:
    a,b,_=joints['UpperArm_'+side];c=joints['Forearm_'+side][1]
    # Sleeves follow authored shoulder and elbow pivots; the cuff belongs to the forearm.
    def sleeve(name,start,end,r1,r2,bone):
        start,end=Vector(start),Vector(end);axis=(end-start).normalized()
        right=axis.cross(Vector((0,1,0))).normalized();up=axis.cross(right).normalized()
        verts=[];faces=[];n=20
        for k in range(5):
            t=k/4;centre=start.lerp(end,t);radius=r1*(1-t)+r2*t
            radius*=1+.04*math.sin(k*2.3)
            for i in range(n):
                angle=i*math.tau/n;p=centre+right*math.cos(angle)*radius+up*math.sin(angle)*radius*.93
                verts.append(p)
        for k in range(4):
            for i in range(n):faces.append((k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i))
        mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);scene.collection.objects.link(o)
        finish(o,name,'cotton',bone)
    sleeve('Upper sleeve '+side,a,b,.103,.082,'UpperArm_'+side)
    sphere('Rounded shoulder fabric '+side,a,(.101,.10,.099),'cotton','UpperArm_'+side,seg=16,rings=8)
    sphere('Elbow fabric '+side,b,(.084,.082,.084),'cotton','Forearm_'+side,seg=12,rings=6)
    sleeve('Lower sleeve '+side,b,c,.082,.051,'Forearm_'+side)
    sleeve('Rib cuff '+side,Vector(b).lerp(Vector(c),.89),c,.054,.05,'Forearm_'+side)
    # Compact sculpted glove volumes wrap around the existing grip/handguard.
    hand=Vector(c);sphere('Black glove palm '+side,hand,(.049,.054,.039),'rubber','Hand_'+side)
    for finger in range(4):
        off=Vector(((finger-1.5)*.017,-.027,.012))
        sphere('Glove finger '+side+str(finger),hand+off,(.011,.033,.012),'rubber','Hand_'+side,seg=8,rings=6)
    sphere('Glove thumb '+side,hand+Vector((.035,-.005,-.018)),(.018,.03,.018),'rubber','Hand_'+side,seg=8,rings=6)

# Balaclava with a genuine eye slit, brown skin behind it, and small eyes.
sphere('Head under mask',(0,-.005,1.596),(.093,.095,.121),'skin','Head',seg=16,rings=12)
headrows=[(1.46,0,0,.075,.072),(1.52,0,-.003,.09,.092),(1.59,0,-.006,.096,.101),(1.609,0,-.006,.097,.102),(1.642,0,-.004,.093,.10),(1.69,0,0,.072,.08),(1.717,0,.005,.025,.032)]
loft('Balaclava shell',headrows,'rib','Head',segments=24,cut=lambda k,a:k==3 and (a<.79 or a>math.tau-.79))
for x in [-.037,.037]:
    sphere('Eye visible through mask',(x,-.097,1.627),(.011,.007,.0045),'eye','Head',seg=10,rings=6)
    sphere('Eye pupil',(x,-.103,1.627),(.0065,.003,.0045),'rubber','Head',seg=8,rings=6)
line('Mask brow seam',(-.066,-.085,1.647),(.066,-.085,1.647),.003,'seam','Head')
line('Mask bridge seam',(0,-.104,1.60),(0,-.105,1.551),.003,'cotton','Head')
sphere('Mask over nose',(0,-.103,1.582),(.018,.011,.025),'rib','Head',seg=12,rings=8)
sphere('Closed balaclava crown',(0,.005,1.705),(.040,.047,.019),'rib','Head',seg=16,rings=8)

# Separate selectable hood states; both remain rigged and use the same original cotton.
hoodrows=[(1.41,0,.024,.14,.12),(1.48,0,.025,.15,.145),(1.59,0,.026,.148,.15),(1.68,0,.025,.137,.135),(1.735,0,.022,.085,.086),(1.75,0,.02,.012,.014)]
loft('Hood raised shell',hoodrows,'cotton','Head','Hood_up',segments=24,cut=lambda k,a:k<4 and (a<.85 or a>math.tau-.85))
for sign in [-1,1]:
    p=[(sign*.105,-.056,1.415),(sign*.113,-.071,1.49),(sign*.11,-.071,1.61),(sign*.10,-.064,1.68),(sign*.064,-.042,1.73)]
    for a,b in zip(p,p[1:]):line('Raised hood stitched edge',a,b,.006,'rib','Head','Hood_up')
loft('Hood folded collar',[(1.36,0,.056,.153,.105),(1.405,0,.061,.16,.12),(1.46,0,.071,.126,.095)],'cotton','Chest','Hood_down',segments=20,cut=lambda k,a:a<1.0 or a>math.tau-1.0)
for z in [1.385,1.415]:
    line('Folded hood crease',(-.115,.125,z),(.115,.125,z+.005),.007,'rib','Chest','Hood_down')

# Three genuinely different, unbranded all-black trainer silhouettes.
for kind in ['court','runner','high']:
    part='Trainers_'+kind
    for side,x in [('L',-.12),('R',.12)]:
        bone='Foot_'+side
        sole=.032 if kind=='court' else .045
        outline=[(-.049,.085),(.049,.085),(.076,.05),(.082,-.06),(.077,-.16),(.059,-.216),(.025,-.23),(-.025,-.23),(-.059,-.216),(-.077,-.16),(-.082,-.06),(-.076,.05)]
        verts=[];faces=[];n=len(outline)
        for z,scale in [(0,.96),(sole,1)]:
            verts.extend((x+px*scale,py,z) for px,py in outline)
        for i in range(n):faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
        faces.extend([tuple(reversed(range(n))),tuple(range(n,2*n))])
        mesh=bpy.data.meshes.new('Shaped trainer outsole');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(kind+' outsole '+side,mesh);scene.collection.objects.link(o);finish(o,o.name,'rubber',bone,part)
        verts=[];faces=[]
        for layer in range(3):
            for px,py in outline:
                scale=[.98,.94,.64][layer]
                z=sole if layer==0 else .07 if layer==1 else .09+max(0,min(1,(py+.2)/.2))*.045
                verts.append((x+px*scale,py+(.02 if layer==2 else 0),z))
        for layer in range(2):
            for i in range(n):faces.append((layer*n+i,layer*n+(i+1)%n,(layer+1)*n+(i+1)%n,(layer+1)*n+i))
        faces.append(tuple(range(n*2,n*3)))
        mesh=bpy.data.meshes.new('Shaped trainer upper');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(kind+' upper '+side,mesh);scene.collection.objects.link(o);finish(o,o.name,'cotton',bone,part)
        if kind=='high':
            loft('High trainer padded collar '+side,[(.07,x,.012,.076,.08),(.13,x,.013,.07,.072),(.205,x,.013,.063,.063)],'rib',bone,part,segments=12)
            box('High trainer heel tab '+side,(x,.082,.167),(.032,.013,.062),'rubber',bone,part,.004)
        else:
            loft('Low trainer padded collar '+side,[(.075,x,.02,.072,.072),(.134,x,.025,.063,.056)],'rib',bone,part,segments=12)
        if kind=='runner':
            for z,dx in [(.045,-.054),(.05,.054)]:
                line('Runner raised sole rail '+side,(x+dx,-.19,z),(x+dx,.059,z),.009,'rib',bone,part)
            for j in range(4):
                box('Runner sole segmentation '+side,(x,-.176+j*.073,.022),(.179,.01,.021),'rib',bone,part,.003)
        # Toe bumper, quarters, tongue and flat laces are recognisable at menu distance.
        box('Trainer tongue '+side,(x,-.065,.12),(.06,.115,.013),'rib',bone,part,.006)
        for i in range(4 if kind!='high' else 5):
            y=-.12+i*.026;z=.118+i*.001
            line('Flat lace '+side+str(i),(x-.029,y,z),(x+.029,y+.012,z),.003,'seam',bone,part)
        line('Toe cap stitching '+side,(x-.055,-.164,.09),(x+.055,-.164,.09),.003,'seam',bone,part)
        line('Quarter seam '+side,(x-.08,-.13,.07),(x-.069,.025,.105),.003,'rib',bone,part)

# Original, unbranded compact carbine prop, with actual muzzle and grounded grip positions.
box('Carbine receiver',(.085,-.31,1.265),(.073,.28,.095),'steel','Weapon',bevel=.01)
box('Carbine handguard',(.085,-.56,1.265),(.067,.24,.075),'rubber','Weapon',bevel=.008)
box('Carbine stock',(.085,-.095,1.255),(.058,.18,.095),'rubber','Weapon',bevel=.01)
box('Carbine grip',(.097,-.275,1.19),(.046,.065,.095),'rubber','Weapon',bevel=.006)
box('Carbine magazine',(.085,-.40,1.167),(.048,.078,.15),'steel','Weapon',bevel=.008)
line('Carbine barrel',(.085,-.67,1.265),(.085,-.83,1.265),.016,'steel','Weapon',vertices=10)
line('Carbine muzzle collar',(.085,-.805,1.265),(.085,-.835,1.265),.022,'steel','Weapon',vertices=10)
for j in range(5):
    box('Handguard rib '+str(j),(.085,-.47-j*.036,1.309),(.069,.012,.015),'steel','Weapon')
for x in [.05,.12]:box('Sight wing',(x,-.34,1.345),(.012,.036,.07),'steel','Weapon',bevel=.003)
box('Sight roof',(.085,-.34,1.379),(.082,.036,.011),'steel','Weapon')

# Join by kit part, retaining material slots and bone weights: one skin, six mesh nodes.
meshes=[]
for name,objects in parts.items():
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=name
    # Join retains duplicate slots; deduplicate to avoid unnecessary primitives.
    slots=list(o.data.materials);unique=[];remap={}
    for i,m in enumerate(slots):
        if m not in unique:unique.append(m)
        remap[i]=unique.index(m)
    indices=[remap[p.material_index] for p in o.data.polygons]
    o.data.materials.clear()
    for m in unique:o.data.materials.append(m)
    for p,i in zip(o.data.polygons,indices):p.material_index=i
    mod=o.modifiers.new('Original ONSITE weighted joints','ARMATURE');mod.object=rig
    o.parent=rig;o['ONSITE_part']=name;meshes.append(o)
    o.select_set(False)

scene['ONSITE_source']='Original procedural Blender authoring; no external models, images, clips or fonts.'
scene['ONSITE_units']='Metres; standing sole at 0m, hood at 1.75m. Blender forward -Y -> GLB +Z.'
scene['ONSITE_runtime']='Visual only. The existing WWB capsule, combat and navigation remain authoritative.'
scene['ONSITE_kit']='Trainers court/runner/high; hood up/down; black cotton, balaclava and gloves fixed.'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'onsite-operator.blend'))
path=OUT/'onsite-operator.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_yup=True,export_animations=False,export_extras=True,export_skins=True,export_all_influences=False)
triangles={o.name:sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes}
report={
 'asset':'/models/onsite-operator.glb','source':'assets/blender/characters/onsite-operator.blend',
 'generator':'scripts/characters/build_operator.py','author':'Original ONSITE project authoring',
 'provenance':'All geometry, anatomical skeleton, woven cotton maps, materials and kit shapes are original; no donor images or animation clips.',
 'units':'metres','height':1.75,'forward':'+Z in GLB, rotated PI by the bot adapter',
 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,
 'trianglesByPart':triangles,'allVariantTriangles':sum(triangles.values()),
 'materials':len(mats),'bones':len(joints),'animations':0,
 'textures':texture_records,
 'variants':{'hood':['up','down'],'trainers':['court','runner','high']},
 'physics':'No collision/nav data. Existing WWB capsule remains unchanged.',
}
(OUT/'onsite-operator.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
