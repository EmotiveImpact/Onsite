"""Build a NEW B01 guide file; never overwrite the earlier massing/playable.
blender -b --python-exit-code 1 --python scripts/maps/build_heron_blueprint_guides.py
These are modelling references, not runtime collision or finished art.
"""
import bpy
import hashlib
import json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/maps/heron-reach-32/blueprints'
B=json.loads((OUT/'build-spec.json').read_text())
D=json.loads((OUT.parent/'map.json').read_text())
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['purpose']='B01 dimensioned blueprint guides; not final art, shipped geometry or tested collision'
scene['build_spec_sha256']=hashlib.sha256((OUT/'build-spec.json').read_bytes()).hexdigest()
scene['source_map_sha256']=B['sourceSha256']
cols={}
for name in ['00_DATUMS','B1_UNDERCROFT','G_GROUND','L1_GALLERIES','L2_UPPER','R_ROOFS','90_OPENING_LABELS']:
    c=bpy.data.collections.new(name);scene.collection.children.link(c);cols[name]=c
levels={l['id']:l['y']for l in D['levels']}
levelcols={'B1':'B1_UNDERCROFT','G':'G_GROUND','L1':'L1_GALLERIES','L2':'L2_UPPER','R':'R_ROOFS'}
materials={}
for name,colour in [('floor',(.39,.55,.66,1)),('wall',(.65,.73,.77,1)),('stair',(.25,.49,.59,1)),('reserve',(.26,.29,.32,1)),('cover',(.62,.42,.2,1))]:
    m=bpy.data.materials.new(name);m.diffuse_color=colour;materials[name]=m
boxes=[]


def box(name,r,y,h,col,mat='wall',role='guide',**props):
    x,z,w,d=r
    if min(w,d,h)<=1e-7:return None
    mesh=bpy.data.meshes.new(name)
    verts=[(-w/2,-d/2,-h/2),(w/2,-d/2,-h/2),(w/2,d/2,-h/2),(-w/2,d/2,-h/2),(-w/2,-d/2,h/2),(w/2,-d/2,h/2),(w/2,d/2,h/2),(-w/2,d/2,h/2)]
    mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    mesh.materials.append(materials[mat]);o=bpy.data.objects.new(name,mesh)
    o.location=(x+w/2-72,60-z-d/2,y+h/2);cols[col].objects.link(o)
    o['role']=role
    for k,v in props.items():o[k]=v
    boxes.append(dict(name=name,rect=r,y=y,height=h,role=role,**props))
    return o


def empty(name,x,z,y,**props):
    o=bpy.data.objects.new(name,None);cols['90_OPENING_LABELS'].objects.link(o)
    o.location=(x-72,60-z,y);o.empty_display_type='CUBE';o.empty_display_size=.15;o.show_name=True
    for k,v in props.items():o[k]=v
    return o


def transform_rect(r,x,z,depth,mirror):
    u,v,w,d=r
    return [x+u,z+(depth-v-d if mirror else v),w,d]


def wall_solids(w,origin,y,col,instance,depth=8,mirror=False):
    axis,at,th=w['axis'],w['at'],w['thickness']
    def part(lo,hi,sill,height,suffix):
        r=[lo,at,hi-lo,th]if axis=='x'else[at,lo,th,hi-lo]
        return box(instance+'-'+w['id']+'-'+suffix,transform_rect(r,*origin,depth,mirror),y+sill,height,col,instance=instance,role='wall')
    cursor=w['start']
    for op in sorted(w['openings'],key=lambda o:o['centre']):
        lo=op['centre']-op['width']/2;hi=op['centre']+op['width']/2
        part(cursor,lo,0,2.8,'solid-'+op['id']);cursor=hi
        if op['sill']>0:part(lo,hi,0,op['sill'],'sill-'+op['id'])
        head=op['sill']+op['height']
        part(lo,hi,head,2.8-head,'header-'+op['id'])
        u,v=(op['centre'],at+th/2)if axis=='x'else(at+th/2,op['centre'])
        if mirror:v=depth-v
        empty(instance+'-'+op['id'],origin[0]+u,origin[1]+v,y+op['sill'],width=op['width'],height=op['height'],kind=op['kind'],axis=axis)
    part(cursor,w['end'],0,2.8,'solid-end')


def cells(rects,holes):
    """Union rectangles minus holes, then merge adjoining cells (no coplanar duplicates)."""
    if not rects:return []
    xs=sorted(set(v for r in rects+holes for v in [r[0],r[0]+r[2]]))
    zs=sorted(set(v for r in rects+holes for v in [r[1],r[1]+r[3]]))
    def inside(x,z,rs):return any(r[0]<x<r[0]+r[2] and r[1]<z<r[1]+r[3]for r in rs)
    runs=[]
    for za,zb in zip(zs,zs[1:]):
        run=None
        for xa,xb in zip(xs,xs[1:]):
            x,z=(xa+xb)/2,(za+zb)/2
            if inside(x,z,rects)and not inside(x,z,holes):
                if run is None:run=[xa,za,xb-xa,zb-za]
                else:run[2]=xb-run[0]
            elif run is not None:runs.append(run);run=None
        if run is not None:runs.append(run)
    merged=[]
    for r in runs:
        prev=next((p for p in reversed(merged)if abs(p[0]-r[0])<1e-6 and abs(p[2]-r[2])<1e-6 and abs(p[1]+p[3]-r[1])<1e-6),None)
        if prev is not None:prev[3]+=r[3]
        else:merged.append(r)
    return merged


for lid,y in levels.items():
    rs=[[0,0,144,120]]if lid=='G'else[s['rect']for s in D['surfaces']if s['level']==lid]
    holes=[c['rect']for c in B['cores']if y in c['levels']]
    if lid=='L2':
        for h in B['homeInstances']:
            if h['module']=='H2-U':holes.append(transform_rect(B['modules']['H2-U']['floorVoid'],h['x'],h['z'],8,h['mirrorZ']))
    for i,r in enumerate(cells(rs,holes)):box(f'{lid}-FLOOR-{i:03}',r,y-.2,.2,levelcols[lid],'floor','floor',floor=lid)

for ins in B['homeInstances']:
    lid=next(k for k,y in levels.items()if y==ins['y'])
    for w in B['modules'][ins['module']]['walls']:
        wall_solids(w,(ins['x'],ins['z']),ins['y'],levelcols[lid],ins['id'],mirror=ins['mirrorZ'])


def stair_instance(id,st,x,z,lo,col,depth,mirror):
    def sb(label,r,y,h):return box(id+'-'+label,transform_rect(r,x,z,depth,mirror),lo+y,h,col,'stair','stair',instance=id)
    run=st['flightRun'];zz=st['flightZ'];w=st['flightWidth'];g=st['going'];t=st['stairSlab']
    for i in range(9):
        top=(i+1)*.15
        sb(f'A-T{i+1:02}',[st['firstFlightX'],zz+run-(i+1)*g,w,g],top-t,t)
        top=1.5+(i+1)*.15
        sb(f'B-T{i+1:02}',[st['secondFlightX'],zz+i*g,w,g],top-t,t)
    sb('HALF-LANDING',st['halfLanding'],1.5-t,t)
    sb('TOP-LANDING',st['floorLanding'],3-.2,.2)


for c in B['cores']:
    x,z,w,d=c['rect'];low,high=c['levels'][0],c['levels'][-1]
    # Base landing has no descent; higher landings come from each preceding stair.
    lid=next(k for k,y in levels.items()if y==low)
    box(c['id']+'-BASE',c['rect'],low-.2,.2,levelcols[lid],'floor','floor',floor=lid)
    for y in c['levels']:
        lid=next(k for k,v in levels.items()if v==y);col=levelcols[lid]
        for wall in [dict(id='N',axis='x',at=0,start=0,end=6,thickness=.2,openings=[]),
                     dict(id='W',axis='z',at=0,start=.2,end=5.8,thickness=.2,openings=[]),
                     dict(id='E',axis='z',at=5.8,start=.2,end=5.8,thickness=.2,openings=[]),
                     dict(id='S',axis='x',at=5.8,start=0,end=6,thickness=.2,openings=[dict(id='D01',centre=3,width=1.5,sill=0,height=2.4,kind='arch')])]:
            wall_solids(wall,(x,z),y,col,c['id']+f'@{y:+}',depth=6,mirror=c['mirrorZ'])
        if y<high:stair_instance(c['id']+f'@{y:+}',B['stairs']['ST-P'],x,z,y,col,6,c['mirrorZ'])
    lid=next(k for k,y in levels.items()if y==high)
    box(c['id']+'-CAP-NONPLAYABLE',c['rect'],high+2.8,.2,levelcols[lid],'reserve','closed-roof')

for h in D['homes']:
    if h['type']!='H2':continue
    # Translate ST-H origin into the home FIRST, then mirror across the complete home.
    # Equivalent mirrored ST-H origin moves to home local z=0 (8 - 2 - 6).
    z=h['z'] if h['flipZ']else h['z']+2
    stair_instance(h['id']+'-PRIVATE',B['stairs']['ST-H'],h['x']+6,z,3,'L1_GALLERIES',6,h['flipZ'])

for r in B['reserves']:
    box(r['id'],r['rect'],levels[r['level']],r['height'],levelcols[r['level']],'reserve','reserved-solid')
for c in D['cover']:
    lid=next(k for k,y in levels.items()if y==c['y'])
    box(c['id'],c['rect'],c['y'],c['height'],levelcols[lid],'cover','cover-guide')

for b in D['blocks']:
    if not b['roofPlayable']:box(b['id']+'-CLOSED-ROOF',b['rect'],8.8,.2,'R_ROOFS','reserve','closed-roof')

for sh in B['shops']:
    x,z,w,d=sh['rect']
    for side,axis,at,start,end in [('N','x',0,0,w),('S','x',d-.2,0,w),('W','z',0,.2,d-.2),('E','z',w-.2,.2,d-.2)]:
        ops=[dict(id=o['id'],centre=o['offset'],width=o['width'],sill=0,height=o['height'],kind='arch')for o in sh['doorOpenings']if o['side']==side]
        if side=='N':
            for i,(lo,hi)in enumerate(sh['glazing']['spans']):ops.append(dict(id=f'W{i+1:02}',centre=(lo+hi)/2,width=hi-lo,sill=.6,height=1.6,kind='window'))
        wall_solids(dict(id=side,axis=axis,at=at,start=start,end=end,thickness=.2,openings=ops),(x,z),0,'G_GROUND',sh['id'],depth=d)
    box(sh['id']+'-ROOF',sh['rect'],2.8,.2,'G_GROUND','floor','closed-roof')

for lid,y in levels.items():
    o=bpy.data.objects.new('DATUM '+lid+f' / FFL {y:+.2f}',None);cols['00_DATUMS'].objects.link(o)
    o.location=(-72,60,y);o.empty_display_type='ARROWS';o.empty_display_size=3;o.show_name=True
for x,z in [(0,0),(144,0),(144,120),(0,120)]:
    o=bpy.data.objects.new(f'SITE CORNER map {x},{z}',None);cols['00_DATUMS'].objects.link(o);o.location=(x-72,60-z,0);o.empty_display_size=2;o.show_name=True
cols['90_OPENING_LABELS'].hide_viewport=True;cols['90_OPENING_LABELS'].hide_render=True
for lid in ['B1','L1','L2','R']:cols[levelcols[lid]].hide_viewport=True
# This intentional omission is named in the handoff: the file resolves floors,
# home walls and stair geometry; guards, exterior hall facades, tunnel walls and
# art are built by Claude from the drawing contract, not silently claimed here.
scene['guide_omissions']='No final guards, common-hall facade kit, undercroft perimeter walls, landscape or lighting. These are specified on sheets, not built in this guide.'
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=130
        area.spaces.active.region_3d.view_location=(0,0,0)
        area.spaces.active.shading.color_type='MATERIAL'
bpy.context.view_layer.update()

# Inspect actual built guide solids at every home door aperture, not only the spec.
aperture_checks=0;blocked=[]
for ins in B['homeInstances']:
    for w in B['modules'][ins['module']]['walls']:
        for op in w['openings']:
            if op['kind']=='window':continue
            u,v=(op['centre'],w['at']+w['thickness']/2)if w['axis']=='x'else(w['at']+w['thickness']/2,op['centre'])
            if ins['mirrorZ']:v=8-v
            p=Vector((ins['x']+u-72,60-ins['z']-v,ins['y']+1))
            # World-space point in each actual mesh's transformed bounds.
            for obj in cols[levelcols[next(k for k,y in levels.items()if y==ins['y'])]].objects:
                if obj.type!='MESH' or obj.get('role')!='wall':continue
                q=obj.matrix_world.inverted()@p;vs=[Vector(v)for v in obj.bound_box]
                if all(min(v[j]for v in vs)+1e-5<q[j]<max(v[j]for v in vs)-1e-5 for j in range(3)):
                    blocked.append([ins['id'],op['id'],obj.name])
            aperture_checks+=1
assert not blocked,blocked[:10]
blend=ROOT/'assets/blender/maps/heron-reach-32-B01-guides.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
report=dict(scope='Modelling guide geometry, not physics/nav or final art',issue='B01',
            buildSpecSha256=scene['build_spec_sha256'],sourceMapSha256=B['sourceSha256'],
            source=str(blend.relative_to(ROOT)),meshObjects=sum(o.type=='MESH'for o in scene.objects),
            openingLabels=len(cols['90_OPENING_LABELS'].objects),homeApertureCentresChecked=aperture_checks,
            blockedHomeApertureCentres=blocked,units='metres; Blender Z up',
            startupView='Ground visible; enable B1/L1/L2/R collection for other levels',
            omissions=scene['guide_omissions'],bytes=blend.stat().st_size)
(OUT/'blender-guide-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
