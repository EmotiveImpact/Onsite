"""Original Blender set dressing: accumulated litter, weeds, grass and weathering.
Rebuilds only the named detail collection. Metres. Decorative pieces do not own physics.
"""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
REVISION=4

def dress_estate(root,force=False):
    scene=bpy.context.scene
    if scene.get('onsite_dressing_revision')==REVISION and not force:return
    parent=bpy.data.collections['01_RENDER / Heron Estate'];name='06_DETAIL / grass litter weather'
    old=bpy.data.collections.get(name)
    if old:
        for o in list(old.all_objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(old)
    detail=bpy.data.collections.new(name);parent.children.link(detail);rng=random.Random(80183)
    def material(name,color,rough=1,metal=0):
        m=bpy.data.materials.get(name)or bpy.data.materials.new(name);m.use_nodes=True
        b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
        return m
    for n,c,r,m in [('grass',(.19,.24,.085),.95,0),('litter',(.45,.38,.25),1,0),('rubbish_metal',(.16,.19,.18),.6,.7),('mud',(.25,.21,.16),.9,0),('leak',(.14,.17,.09),.95,0),('paint_worn',(.65,.55,.27),1,0),('contact',(.025,.026,.02),1,0)]:material(n,c,r,m)
    def mesh(name,vs,fs,mat,tints=None,uvs=None):
        me=bpy.data.meshes.new(name);me.from_pydata([(x,-z,y)for x,y,z in vs],[],fs);me.update()
        ob=bpy.data.objects.new(name,me);detail.objects.link(ob);me.materials.append(bpy.data.materials[mat]);ob['detail_kind']=name.split('/')[0].strip()
        uv=me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                vi=me.loops[li].vertex_index;uv.data[li].uv=uvs[vi]if uvs else(vs[vi][0]/2,vs[vi][2]/2)
        if tints:
            col=me.color_attributes.new(name='DetailTint',type='FLOAT_COLOR',domain='CORNER')
            for li in range(len(me.loops)):col.data[li].color=tints[me.loops[li].vertex_index]
        return ob
    def cube(name,x,y,z,w,h,d,mat='litter',yaw=0):
        bpy.ops.mesh.primitive_cube_add(size=1,location=(x,-z,y));o=bpy.context.object;o.name=name;o.dimensions=(w,d,h);o.rotation_euler.z=yaw
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        for c in list(o.users_collection):c.objects.unlink(o)
        detail.objects.link(o);o.data.materials.append(bpy.data.materials[mat]);b=o.modifiers.new('Worn edges','BEVEL');b.width=min(.012,min(w,h,d)*.12);b.segments=1
        return o
    def patch(name,x,z,rx,rz,mat,y=.034):
        count=24;vs=[(x,y,z)];cols=[(1,1,1,.65)];fs=[]
        for ring in [0.6,1]:
            for i in range(count):
                a=i*math.tau/count;k=rng.uniform(.85,1.12)*ring;vs.append((x+math.cos(a)*rx*k,y,z+math.sin(a)*rz*k));cols.append((1,1,1,.65 if ring<1 else 0))
        for i in range(count):
            n=(i+1)%count;fs.extend([(0,1+i,1+n),(1+i,1+count+i,1+count+n,1+n)])
        return mesh(name,vs,fs,mat,cols)
    # Real 600mm paving units, with gaps and chipped corners, replace the four flat strips.
    for ob in list(parent.objects):
        if ob.name.startswith('Court / raised paving strip'):bpy.data.objects.remove(ob,do_unlink=True)
    slabs=0
    for ix in range(40):
        for iz in range(30):
            x=-11.7+ix*.6;z=-8.7+iz*.6
            if abs(x)<9 and abs(z)<6:continue
            top=.026+rng.uniform(-.002,.002);w=.582;d=.582;edge=rng.uniform(.015,.045)
            pts=[(-w/2+edge,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2),(-w/2,-d/2+edge)]
            vs=[(x+u,y,z+v)for y in [-.005,top]for u,v in pts];fs=[tuple(reversed(range(5,10))),tuple(range(5))]+[(i+5,(i+1)%5+5,(i+1)%5,i)for i in range(5)]
            tone=rng.uniform(.68,1.0);ob=mesh('Paving / individual chipped 600mm slab',vs,fs,'paving',[(tone,tone,tone,1)]*10)
            bevel=ob.modifiers.new('Stone arris','BEVEL');bevel.width=.004;bevel.segments=1;slabs+=1
    # Fine branching cracks, worn tar repairs and irregular dirt across the open court.
    for cx,cz in [(-4,1),(2.5,4.8),(4,-3),(-6.8,-1.2),(8,2.3)]:
        patch('Dirt / broken asphalt shoulder',cx,cz,.8,.55,'mud',.035)
        for branch in range(3):
            pts=[(cx,cz)];angle=rng.uniform(0,math.tau)
            for j in range(7):
                angle+=rng.uniform(-.5,.5);x,z=pts[-1];pts.append((x+math.cos(angle)*.22,z+math.sin(angle)*.22))
            vs=[];fs=[]
            for i,(x,z)in enumerate(pts):
                width=.006*(1-i/len(pts))+.002;vs +=[(x-width,.038,z),(x+width,.038,z)]
                if i:fs.append((2*i-2,2*i-1,2*i+1,2*i))
            fs=[f if(Vector(vs[f[1]])-Vector(vs[f[0]])).cross(Vector(vs[f[2]])-Vector(vs[f[0]])).y>0 else tuple(reversed(f))for f in fs]
            mesh('Asphalt / hairline fracture',vs,fs,'dark')
    for p in json.loads((root/'src/onsite/dressing.json').read_text()):
        if p['y']>.1 or p['asset']in ['street_lamp_01','rollershutter_door']:continue
        sx,sy,sz=p['size'];patch('Dirt / prop contact',p['x'],p['z'],sx*.58,sz*.58,'contact',.036)
    # Soil/moss collects beside walls, planters and drains rather than carpet-bombing clear paths.
    patches=[(-11.3,z,.65,1.15)for z in [-7,-2,1.5,5.8]]+[(11.3,z,.5,1.3)for z in [-7,-3,2.8,7]]
    patches += [(x,z,1.7,.48)for z in [-8.4,8.4]for x in [-7,-3.8,0,3.8,7]]
    patches += [(-5,-4,2,1.2),(5,-5,2,1.2),(-6,4,2,1.2),(6,4,2,1.2),(7,-1.3,1.5,2.4)]
    for x,z,rx,rz in patches:patch('Dirt / accumulated grit',x,z,rx,rz,'mud')
    # Bladed grass. Curved taper, multiple colours, dried tips, no billboard spheres.
    grass_vs=[];grass_fs=[];grass_cols=[]
    clumps=[]
    for x,z,rx,rz in patches:
        for j in range(7):clumps.append((x+rng.uniform(-rx*.75,rx*.75),z+rng.uniform(-rz*.75,rz*.75),rng.uniform(.08,.27)))
    for z in [-5.8,5.8]:
        for i in range(24):clumps.append((-8.5+i*.72+rng.uniform(-.2,.2),z+rng.uniform(-.09,.09),rng.uniform(.045,.13)))
    for x,z,h in clumps:
        for blade in range(rng.randint(11,22)):
            angle=rng.uniform(0,math.tau);tx,tz=math.cos(angle),math.sin(angle);px,pz=x+rng.uniform(-.085,.085),z+rng.uniform(-.085,.085)
            height=h*rng.uniform(.55,1.4);width=rng.uniform(.004,.012);bend=rng.uniform(.15,.65)*height;base=len(grass_vs)
            grass_vs +=[(px-tz*width,.035,pz+tx*width),(px+tz*width,.035,pz-tx*width),(px+tx*bend*.35+tz*width*.4,.035+height*.6,pz+tz*bend*.35-tx*width*.4),(px+tx*bend*.35-tz*width*.4,.035+height*.6,pz+tz*bend*.35+tx*width*.4),(px+tx*bend,.035+height,pz+tz*bend)]
            grass_fs +=[(base,base+1,base+2,base+3),(base+3,base+2,base+4)]
            tint=rng.choice([(0.9,1,.72,1),(1,.85,.52,1),(.55,.78,.42,1),(.75,.84,.55,1)])
            grass_cols +=[(*[v*.55 for v in tint[:3]],1),(*[v*.55 for v in tint[:3]],1),tint,tint,(min(1,tint[0]*1.15),tint[1]*.9,tint[2]*.65,1)]
    mesh('Grass / cracks drains and wall edges',grass_vs,grass_fs,'grass',grass_cols)
    # Rubbish clusters: folded paper, torn cardboard, drinks cans and bottle shards.
    zones=[(-10.8,2.1),(10.8,-6.8),(-3.5,8.35),(8.7,6.8),(-7.2,-8.35)]
    for zone,(cx,cz)in enumerate(zones):
        for j in range(13):
            x,z=cx+rng.uniform(-.85,.85),cz+rng.uniform(-.65,.65);w,h=rng.uniform(.06,.26),rng.uniform(.08,.32);a=rng.uniform(0,math.tau)
            pts=[(-w,-h,0),(0,-h,.012),(w,-h,.003),(-w,h,.01),(0,h,.035),(w,h,.005)]
            vs=[(x+u*math.cos(a)-v*math.sin(a),.039+t,z+u*math.sin(a)+v*math.cos(a))for u,v,t in pts]
            c=rng.choice([(.85,.85,.76,1),(.52,.38,.2,1),(.36,.42,.36,1),(.75,.67,.5,1)])
            mesh('Litter / folded paper and torn card',vs,[(0,1,4,3),(1,2,5,4)],'litter',[c]*6,[(0,0),(.5,0),(1,0),(0,1),(.5,1),(1,1)])
            # Dark print bands, physically on the folded sheet; no trademarks/text atlas.
            if j%3==0:
                for v in [-.35,0,.35]:
                    u1,u2=-w*.7,w*.7;vv=h*v
                    vs2=[(x+u*math.cos(a)-vv*math.sin(a),.073,z+u*math.sin(a)+vv*math.cos(a))for u in [u1,u2]]
                    mesh('Litter / faded printed strip',[vs2[0],vs2[1],(vs2[1][0],.073,vs2[1][2]+.008),(vs2[0][0],.073,vs2[0][2]+.008)],[(0,1,2,3)],'dark')
        for j in range(4):
            x,z=cx+rng.uniform(-.8,.8),cz+rng.uniform(-.6,.6);vs=[];fs=[]
            for y,r in [(0,.03),(.02,.035),(.075,.024),(.11,.031)]:
                for i in range(10):
                    a=i*math.tau/10;rr=r*rng.uniform(.75,1.15);vs.append((x+math.cos(a)*rr,.04+y,z+math.sin(a)*rr))
            for j in range(3):
                for i in range(10):fs.append((j*10+i,j*10+(i+1)%10,(j+1)*10+(i+1)%10,(j+1)*10+i))
            fs.append(tuple(range(30,40)));mesh('Rubbish / crushed drinks can',vs,fs,'rubbish_metal')
    # Individual fallen leaves read as organic scatter at player height.
    vs=[];fs=[];cs=[]
    for i in range(240):
        cx,cz=zones[i%len(zones)];x,z=cx+rng.uniform(-1.5,1.5),cz+rng.uniform(-1,1);a=rng.uniform(0,math.tau);l=rng.uniform(.035,.09);w=l*.45;bi=len(vs)
        for u,v,y in [(-l,0,0),(0,-w,0),(l,0,0),(0,w,0),(0,0,.012)]:vs.append((x+u*math.cos(a)-v*math.sin(a),.037+y,z+u*math.sin(a)+v*math.cos(a)))
        fs +=[(bi,bi+1,bi+4),(bi+1,bi+2,bi+4),(bi+2,bi+3,bi+4),(bi+3,bi,bi+4)];t=rng.choice([(.6,.38,.13,1),(.45,.34,.19,1),(.7,.52,.21,1)]);cs +=[t]*5
    mesh('Leaves / autumn litter',vs,fs,'litter',cs)
    # Damp streaks stay on solid wall bays; no opaque quads across doors.
    layout=json.loads((root/'docs/development/evidence/layout.json').read_text())
    for i,s in enumerate(layout['solids']):
        if s['id'] not in ['court-door-jamb','side-door-jamb'] or s['y']>2 or (s['w']<1 and s['d']<1):continue
        x,y,z,w,d=s['x'],s['y'],s['z'],s['w'],s['d'];h=rng.uniform(.5,1.45)
        if w>d:
            facing=-1 if z>0 else 1;zz=z-facing*-d/2+facing*.008
            coords=[(x-w/2,.04,zz),(x+w/2,.04,zz),(x+w/2,h,zz),(x-w/2,h,zz)]
        else:
            facing=-1 if x>0 else 1;xx=x+facing*(w/2+.008)
            coords=[(xx,.04,z-d/2),(xx,.04,z+d/2),(xx,h,z+d/2),(xx,h,z-d/2)]
        mesh('Weather / rising damp and runoff',coords,[(0,1,2,3)],'leak',uvs=[(0,0),(1,0),(1,1),(0,1)])
    # Faded safety paint on asphalt beside the service kiosk.
    for z in [-2.1,2.1]:
        for i in range(8):
            x=-1.8+i*.5;cube('Paint / broken maintenance bay line',x,.038,z,.28,.004,.045,'paint_worn')
    # Extra roofline variety / satellite dishes, original geometry; no navigation impact.
    for x,y,z,ang in [(-5,8.5,-8.65,.1),(6,11.4,-8.65,-.1),(-8,8.4,8.65,3.1),(11.8,8.2,2,1.6)]:
        seg=16;vs=[(x,y,z)];fs=[]
        for i in range(seg):
            a=i*math.tau/seg;u,v=math.cos(a)*.32,math.sin(a)*.37
            vs.append((x+u*math.cos(ang),y+v,z+u*math.sin(ang)-.075))
        for i in range(seg):fs.append((0,i+1,(i+1)%seg+1))
        mesh('Facade / satellite dish',vs,fs,'dark');cube('Facade / dish bracket',x,y-.1,z+.08,.04,.4,.12,'steel')
    # Dressed materials packed in the editable source, bound by name in Three.js.
    for matname,asset in [('mud','Ground110'),('leak','Leaking003')]:
        mat=bpy.data.materials[matname];nodes=mat.node_tree.nodes;links=mat.node_tree.links;b=nodes.get('Principled BSDF')
        filename=f'{asset}-{"ColorA"if matname=="leak"else"Color"}.webp'
        path=root/'public/materials/detail'/filename
        im=bpy.data.images.load(str(path),check_existing=True);im.pack();im.colorspace_settings.name='sRGB';node=nodes.new('ShaderNodeTexImage');node.image=im;links.new(node.outputs['Color'],b.inputs['Base Color'])
        if matname=='leak':links.new(node.outputs['Alpha'],b.inputs['Alpha']);mat.surface_render_method='DITHERED'
    scene['onsite_dressing_revision']=REVISION
    scene['onsite_dressing_counts']=json.dumps({'objects':len(detail.objects),'pavingSlabs':slabs,'grassClumps':len(clumps),'grassBlades':len(grass_vs)//5,'paper':65,'cans':20,'leaves':240,'dirtPatches':len(patches)+5})
    print('DETAIL',scene['onsite_dressing_counts'],flush=True)

if __name__=='__main__':
    ROOT=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/onsite-heron-court.blend'))
    dress_estate(ROOT,True);bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/onsite-heron-court.blend'))
