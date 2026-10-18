"""Original ONSITE residential expansion, informed by South London photo studies.
Idempotent Blender pass; retains the working estate and adds a collision-backed flat.
Photograph pixels are never used. Geometry, metre UVs and domestic props are original.
"""
import bpy,math,json,random,sys
from pathlib import Path
from mathutils import Vector
REVISION=1

def build_homes(root,force=False):
    scene=bpy.context.scene
    if scene.get('onsite_homes_revision')==REVISION and not force:return
    parent=bpy.data.collections['01_RENDER / Heron Estate'];name='07_HOMES / South London residential'
    old=bpy.data.collections.get(name)
    if old:
        for o in list(old.all_objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(old)
    col=bpy.data.collections.new(name);parent.children.link(col);rng=random.Random(15101)
    # Replace the old thin upper window boxes, not the actual physical lower floors.
    prefixes=('Residential bay /','Window /','Side elevation /','Side window /','Facade / slab edge','Roof / parapet','Roof / felt','Estate entry / teal panel','Door /')
    for o in list(parent.objects):
        if o.name.startswith(prefixes)or o.name.startswith('Structure / home-'):bpy.data.objects.remove(o,do_unlink=True)
    for n,c,r in [('plaster',(.72,.68,.57),.92),('fabric',(.42,.43,.37),.98),('roof',(.10,.13,.15),.9),('wood',(.15,.10,.07),.85)]:
        m=bpy.data.materials.get(n)or bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=r
    def cube(name,x,y,z,w,h,d,mat='concrete',tint=(1,1,1),bevel=0):
        vs=[(a*w/2,b*d/2,c*h/2)for c in [-1,1]for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]]
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new('Homes / '+name,me);col.objects.link(o);o.location=(x,-z,y);me.materials.append(bpy.data.materials[mat])
        me.uv_layers.new(name='UVMap');me.color_attributes.new(name='DetailTint',type='FLOAT_COLOR',domain='CORNER')
        # Reacquire both RNA handles after layer allocation; otherwise writing UVs
        # can alias a moved colour layer and produce coloured stripes on facades.
        uv=me.uv_layers['UVMap'];colors=me.color_attributes['DetailTint']
        coverage=1.05 if mat=='stock'else .65 if mat=='brick'else 2
        for p in me.polygons:
            axis=max(range(3),key=lambda a:abs(p.normal[a]));axes=[a for a in range(3)if a!=axis]
            for li in p.loop_indices:
                v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]/coverage,v[axes[1]]/coverage);colors.data[li].color=(*tint,1)
        if bevel:
            b=o.modifiers.new('Domestic edge bevel','BEVEL');b.width=min(bevel,min(w,h,d)*.2);b.segments=2
        return o
    def bar(name,a,b,r=.018,mat='trim'):
        a=Vector((a[0],-a[2],a[1]));b=Vector((b[0],-b[2],b[1]));v=b-a
        bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.name='Homes / '+name;o.rotation_mode='QUATERNION';o.rotation_quaternion=v.to_track_quat('Z','Y')
        for c in list(o.users_collection):c.objects.unlink(o)
        col.objects.link(o);o.data.materials.append(bpy.data.materials[mat]);return o
    def face(axis,side,origin,depth):
        def f(name,u,y,q,w,h,d,mat='stock',tint=(1,1,1),bevel=0):
            x,z=(origin+u,side*(depth-q))if axis=='x'else(side*(depth-q),origin+u)
            return cube(name,x,y,z,w if axis=='x'else d,h,d if axis=='x'else w,mat,tint,bevel)
        return f
    windows=balconies=0
    def window(f,u,y,width=2.15,height=1.65,seed=0):
        nonlocal windows
        windows+=1
        f('recessed glass',u,y,-.11,width,height,.035,'lit'if seed%11==0 else'glass')
        for dx in [-width/2,0,width/2]:f('white uPVC mullion',u+dx,y,.035,.055,height+.1,.085,'trim')
        for dy in [-height/2,height*.16,height/2]:f('white uPVC transom',u,y+dy,.035,width+.1,.055,.085,'trim')
        f('projecting window sill',u,y-height/2-.07,.06,width+.28,.13,.32,'concrete')
        # Opaque folded curtains sit behind the frame, varied per home, not identical glowing cards.
        if seed%4!=0:
            tint=[(.70,.76,.77),(.8,.7,.53),(.55,.67,.60),(.88,.85,.75)][seed%4]
            for side in [-1,1]:
                for k in range(4):f('curtain fold',u+side*(width/2-.08-k*.065),y,-.055+(.016 if k%2 else 0),.07,height-.08,.025,'fabric',tint)
        if seed%5==0:
            for k in range(7):f('venetian blind',u,y+.48-k*.11,-.035,width-.10,.025,.025,'trim',(.82,.80,.72))
    def rear_window(f,y):
        # Closed exterior elevations use a simpler frame than the court-facing homes.
        f('rear glazing',0,y,-.08,1.75,1.55,.03,'glass')
        for u in [-.9,0,.9]:f('rear white mullion',u,y,0,.05,1.65,.06,'trim')
        for dy in [-.8,.8]:f('rear white transom',0,y+dy,0,1.85,.05,.06,'trim')
        f('rear sill',0,y-.9,.03,2.0,.12,.24,'concrete')
    # Wider/deeper upper homes: stepped massing, paired openings, private projecting balconies.
    for side in [-1,1]:
        for i in range(12):
            x=-16.5+3*i;floors=[2,3,4,4,3,2][i//2];f=face('x',side,x,9)
            for row in range(floors):
                base=6+row*3;y=base+1.6
                for u in [-1.33,1.33]:f('stock brick window pier',u,base+1.5,-1.5,.34,3,3.0)
                f('stock brick sill course',0,base+.37,-1.5,2.32,.74,3.0)
                f('stock brick lintel course',0,base+2.75,-1.5,2.32,.5,3.0)
                f('horizontal concrete band',0,base+.07,.035,3,.14,.18,'concrete')
                f('home floor slab',0,base-.025,-1.5,3,.13,3,'concrete')
                f('rear home wall',0,base+1.5,-3.08,3,3,.18,'stock')
                rear_window(face('x',-side,x,-12.36),y)
                window(f,0,y,2.18,1.65,i+row*7+(side+1)*3)
                if i%2==0 and row%2==0:
                    balconies+=1;f('private balcony slab',0,base-.04,.63,2.8,.18,1.5,'concrete')
                    f('private balcony brick breast',0,base+.49,1.33,2.8,.85,.16,'stock')
                    f('balcony coping',0,base+.94,1.33,2.88,.08,.24,'concrete')
                    for u in [-1.38,1.38]:f('balcony side screen',u,base+.56,.66,.10,1.2,1.4,'concrete')
                    for u in [-1.2,0,1.2]:f('balcony rail upright',u,base+1.05,1.33,.028,.28,.028,'dark')
                    f('balcony handrail',0,base+1.2,1.33,2.85,.035,.04,'dark')
                    if (i+row)%4==0:
                        f('window box planter',.75,base+.25,.62,.65,.35,.35,'paint');f('window box greenery',.75,base+.48,.62,.70,.16,.4,'leaves')
                    if (i+row)%6==0:
                        f('drying rail',-.35,base+1.18,.8,1.15,.025,.025,'trim')
                        for k in range(3):f('laundry on balcony',-.75+k*.35,base+.88,.80,.28,.55,.018,'fabric',[(.8,.76,.66),(.35,.4,.5),(.55,.6,.63)][k])
                elif i%3==1:
                    f('ribbed concrete spandrel',0,base+.38,.05,2.22,.67,.10,'concrete')
                    for k in range(15):f('exposed aggregate rib',-1.05+k*.15,base+.38,.13,.045,.65,.08,'concrete',(.78,.78,.74))
            f('roof felt',0,6+floors*3,-1.5,3,.12,3,'roof')
            f('stock parapet',0,6+floors*3+.27,.0,3,.54,.24,'stock');f('parapet coping',0,6+floors*3+.56,.0,3.06,.09,.34,'concrete')
        for i in range(6):
            f=face('z',side,-7.5+i*3,12)
            for row in range(3):
                base=6+row*3
                for u in [-1.3,1.3]:f('side window pier',u,base+1.5,-1.5,.4,3,3,'stock')
                f('side sill course',0,base+.37,-1.5,2.2,.74,3,'stock')
                f('side lintel course',0,base+2.75,-1.5,2.2,.5,3,'stock')
                f('side rear wall',0,base+1.5,-3.08,3,3,.18,'stock')
                f('side floor slab',0,base-.025,-1.5,3,.13,3,'concrete')
                rear_window(face('z',-side,-7.5+i*3,-15.36),base+1.6)
                window(f,0,base+1.6,2.0,1.65,i+row*4)
                f('side sill band',0,base+.14,.08,3,.28,.25,'concrete')
            f('side parapet',0,15.2,0,3,.4,.24,'stock')
        for x in range(-15,16,3):
            for y in [1.6,4.6]:rear_window(face('x',-side,x,-15.35),y)
    # Individual front doors and external services on the playable floors.
    for side in [-1,1]:
        for floor in [0,3]:
            for index,x in enumerate([-4.5,-1.5,1.5,4.5]):
                f=face('x',side,x,8.84);t=[(.6,.75,.8),(.75,.52,.4),(.42,.59,.45),(.7,.72,.68)][index]
                f('home front door',0,1.03+floor,0,.94,2.06,.07,'paint',t,.015)
                for u in [-.51,.51]:f('door casing',u,1.07+floor,.025,.07,2.15,.12,'trim')
                f('door head casing',0,2.15+floor,.025,1.09,.07,.12,'trim')
                f('letter plate',0,1.08+floor,.065,.25,.05,.03,'rubbish_metal')
                f('door handle',.3,.94+floor,.09,.025,.14,.06,'rubbish_metal')
                f('number plaque',.0,1.7+floor,.07,.18,.12,.025,'trim')
                f('door mat',0,.023+floor,.36,.82,.025,.46,'fabric',(.3,.28,.24))
                f('entry bell',.61,1.3+floor,.025,.055,.09,.03,'dark')
    # Flat 01 wall finishes and original furniture inside existing north-west room.
    cube('flat laminate floor',-12,.008,-12,11.65,.014,5.65,'wood',(1.7,1.6,1.35))
    for i in range(17):cube('floor board joint',-17.5+i*.67,.018,-12,.006,.005,5.65,'dark')
    cube('flat plaster ceiling',-12,2.74,-12,11.65,.035,5.65,'plaster')
    cube('flat rear plaster',-12,1.38,-14.83,11.65,2.72,.025,'plaster')
    cube('flat west plaster',-17.83,1.38,-12,.025,2.72,5.65,'plaster')
    for x,w in [(-13.88,7.76),(-7.1,1.75)]:cube('flat entrance return',x,1.38,-9.15,w,2.72,.025,'plaster')
    for x in [-17.73,-12.12]:cube('flat skirting',x,.08,-12,.055,.14,5.5,'trim')
    cube('rear skirting',-12,.08,-14.72,11.5,.14,.055,'trim')
    layout=json.loads((root/'docs/development/evidence/layout.json').read_text())
    guides=bpy.data.collections['02_COLLISION / Rapier source solids']
    for o in list(guides.objects):
        if o.get('solid_id','').startswith('home-'):bpy.data.objects.remove(o,do_unlink=True)
    for s in layout['solids']:
        if not s['id'].startswith('home-'):continue
        o=cube('collision source / '+s['id'],*[s[k]for k in ['x','y','z','w','h','d']],s['mat']);col.objects.unlink(o);guides.objects.link(o);o.name='COLLIDER / '+s['id'];o.display_type='WIRE';o.hide_render=True;o['solid_id']=s['id']
        if 'divider'in s['id']:cube('bedroom partition',*[s[k]for k in ['x','y','z','w','h','d']],'plaster')
    # Kitchen, L-shaped domestic work area. Clear centre and south circulation.
    for i in range(5):
        x=-9.65+i*.61;cube('kitchen cabinet',x,.45,-14.45,.59,.87,.62,'plaster',(.7,.79,.72),.014)
        cube('cabinet drawer line',x,.65,-14.12,.55,.016,.012,'dark');cube('cabinet pull',x,.58,-14.10,.18,.018,.025,'rubbish_metal')
    cube('worktop',-8.4,.92,-14.45,3.2,.055,.7,'concrete',(.48,.47,.43),.012)
    cube('tile splashback',-8.4,1.2,-14.79,3.3,.5,.03,'trim')
    for i in range(17):cube('tile grout vertical',-10+i*.2,1.2,-14.77,.009,.5,.015,'concrete')
    for y in [1,1.2,1.4]:cube('tile grout horizontal',-8.4,y,-14.77,3.3,.009,.015,'concrete')
    cube('sink rim',-9.7,.956,-14.42,.47,.025,.4,'rubbish_metal');cube('sink basin',-9.7,.973,-14.42,.36,.015,.28,'dark')
    bar('mixer tap stem',(-9.7,.95,-14.7),(-9.7,1.18,-14.7),.02,'rubbish_metal');bar('mixer tap spout',(-9.7,1.18,-14.7),(-9.7,1.18,-14.48),.02,'rubbish_metal')
    cube('hob',-8.2,.956,-14.43,.59,.02,.47,'dark')
    for x in [-8.36,-8.05]:
        for z in [-14.55,-14.3]:cube('hob plate',x,.974,z,.17,.01,.15,'rubbish_metal')
    cube('fridge cabinet',-6.75,.95,-13.65,.7,1.9,.7,'trim',(.82,.84,.78),.035)
    cube('fridge freezer seam',-6.75,1.35,-13.286,.64,.024,.015,'dark');cube('fridge handle',-6.98,1.06,-13.26,.035,.36,.04,'rubbish_metal')
    # Sofa faces the room; seams, arms and three cushions rather than a solid block.
    cube('sofa base',-10.7,.28,-13.3,.88,.43,2.18,'fabric',(.25,.36,.36),.09)
    cube('sofa back',-11.04,.67,-13.3,.22,.6,2.18,'fabric',(.25,.36,.36),.07)
    for z in [-14.32,-12.28]:cube('sofa arm',-10.7,.58,z,.9,.38,.18,'fabric',(.28,.39,.39),.05)
    for z in [-13.94,-13.3,-12.66]:cube('sofa cushion',-10.55,.53,z,.58,.18,.60,'fabric',(.35,.46,.45),.045)
    cube('coffee table top',-8,.74,-12.1,1.1,.045,.65,'wood',(1.5,1.3,1.1),.015)
    for x in [-8.45,-7.55]:
        for z in [-12.35,-11.85]:cube('table leg',x,.36,z,.045,.72,.045,'wood')
    cube('paperback',-8.2,.78,-12.12,.3,.045,.22,'fabric',(.7,.65,.43));cube('cup',-7.75,.83,-12.05,.08,.13,.08,'trim',(.82,.65,.44),.025)
    # Bedroom: full-size bed, separate duvet, pillows, bedside cabinet and wardrobe.
    cube('bed base',-16.2,.24,-13.2,1.6,.4,2.1,'wood',(.65,.6,.55),.035)
    cube('mattress',-16.2,.49,-13.2,1.58,.2,2.05,'fabric',(.92,.9,.83),.07)
    cube('duvet',-16.2,.62,-12.94,1.62,.18,1.6,'fabric',(.55,.63,.69),.07)
    for x in [-16.63,-15.8]:cube('pillow',x,.66,-13.93,.62,.16,.4,'fabric',(.9,.85,.74),.07)
    cube('bed headboard',-16.2,.8,-14.26,1.7,.85,.08,'wood',(1.6,1.3,1))
    cube('bedside cabinet',-14.9,.3,-13.95,.48,.6,.48,'wood',(1.6,1.3,1),.02)
    cube('wardrobe',-17.35,1.05,-10.5,.65,2.1,1.6,'wood',(1.8,1.6,1.2),.02)
    for z in [-10.85,-10.15]:cube('wardrobe door',-17.01,1.05,z,.03,2.03,.68,'wood',(1.9,1.7,1.3));cube('wardrobe pull',-16.97,1.05,z+.2,.025,.16,.02,'rubbish_metal')
    # Closed residential windows facing the outside; collision remains solid behind glazing.
    for x in [-16.1,-9.1]:
        f=face('x',-1,x,14.65);window(f,0,1.65,1.85,1.25,int(abs(x)))
        f('radiator panel',0,.46,.14,1.5,.58,.10,'trim')
        for k in range(14):f('radiator fins',-.65+k*.10,.46,.20,.015,.52,.025,'plaster')
    # Wider neighbourhood, visual only: two contemporary point blocks and six older houses.
    cube('neighbourhood ground',0,-.12,0,82,.12,78,'asphalt')
    cube('residential footway',0,.015,20,50,.10,1.6,'paving')
    for z in [19.05,19.19]:cube('double yellow edge line',0,.055,z,48,.012,.06,'paint_worn')
    for x in [-8.7,-16]:cube('flat ceiling diffuser',x,2.68,-12.5,.34,.06,.34,'lit')
    for x,z,height in [(-30,-22,27),(29,21,30)]:
        cube('neighbouring point block',x,height/2,z,8,height,9,'concrete',(.8,.83,.81))
        for row in range(int(height/3)):
            y=1.5+row*3
            for u in [-2.4,0,2.4]:
                cube('point block window',x+u,y,z+(4.55 if z<0 else-4.55),1.6,1.65,.08,'glass')
                cube('point block sill',x+u,y-.95,z+(4.6 if z<0 else-4.6),1.8,.13,.25,'trim')
            cube('point block slab',x,y-1.5,z,8.1,.16,9.1,'concrete')
        cube('roof service enclosure',x,height+1.1,z,3.8,2.2,4,'roof')
    for i in range(6):
        x=-16+6*i;z=25
        cube('terraced house body',x,3.15,z,5.8,6.3,7,'stock'if i%2 else'brick')
        for y in [1.65,4.6]:
            for u in [-1.4,1.2]:window(face('x',1,x,21.29),u,y,1.35,1.6,i)
        # Two pitched roof planes modelled as thick rotated slabs; separate chimney stacks.
        for side in [-1,1]:
            o=cube('slate pitched roof',x,7.15,z+side*1.75,6.1,.16,4.1,'roof');o.rotation_euler.x=side*math.radians(29)
        cube('chimney stack',x+2.2,8.3,z,1.05,1.8,.9,'brick')
        for u in [-.23,.23]:cube('chimney pot',x+2.2+u,9.38,z,.2,.4,.2,'brick')
        cube('front garden wall',x,.42,20.95,5.5,.84,.15,'brick')
        for edge in [-2.85,2.85]:cube('garden dividing wall',x+edge,.42,22.4,.15,.84,2.8,'brick')
    scene['onsite_homes_revision']=REVISION
    scene['onsite_homes_counts']=json.dumps(dict(objects=len(col.all_objects),windows=windows,privateBalconies=balconies,accessibleHomes=1,backgroundHouses=6,backgroundTowers=2))
    print('Homes built:',scene['onsite_homes_counts'],flush=True)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'scripts'));bpy.ops.wm.open_mainfile(filepath=str(root/'assets/blender/onsite-heron-court.blend'));build_homes(root,True)
    from prepare_estate_materials import prepare_materials
    prepare_materials(root);bpy.ops.wm.save_as_mainfile(filepath=str(root/'assets/blender/onsite-heron-court.blend'))
    from export_estate import export_estate
    export_estate(root,bpy.data.collections['01_RENDER / Heron Estate'])
