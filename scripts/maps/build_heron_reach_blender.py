"""Separate metric DESIGN model. Does not overwrite the current playable estate.
Run: blender -b --python-exit-code 1 --python scripts/maps/build_heron_reach_blender.py
"""
import bpy, json, math, hashlib, random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/maps/heron-reach-32'
D=json.loads((OUT/'map.json').read_text());rng=random.Random(32)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['purpose']='ONSITE Heron Reach / design massing, not the shipped playable or production collision'
scene['map_sha256']=hashlib.sha256((OUT/'map.json').read_bytes()).hexdigest()
collections={}
for name in ['00_SITE','01_GROUND','02_GALLERIES','03_UPPER_HOMES','04_ROOFS','05_PUBLIC_STAIRS','06_LANDSCAPE','07_LIGHT_INTENT','08_ROUTE_GUIDES','09_UNDERCROFT']:
 c=bpy.data.collections.new(name);scene.collection.children.link(c);collections[name]=c
def mat(name,c,rough=.8,emission=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True;n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*c,1);n.inputs['Roughness'].default_value=rough
 if emission:n.inputs['Emission Color'].default_value=(*c,1);n.inputs['Emission Strength'].default_value=emission
 return m
M={'brick':mat('Stock brick / massing placeholder',(.28,.22,.14)),'concrete':mat('Weathered concrete / massing',(.28,.31,.31)),'ground':mat('Asphalt / massing',(.055,.072,.083),.72),'court':mat('Court surface proxy',(.065,.14,.17),.7),'grass':mat('Grass zone / placement only',(.075,.14,.09)),'soil':mat('Soil zone',(.09,.075,.055)),'leaf':mat('Tree proxy foliage',(.10,.22,.13)),'wood':mat('Trunk',(.12,.085,.05)),'glass':mat('Cool window proxy',(.08,.17,.22),.25),'warm':mat('Warm window / emissive intent',(1,.48,.12),.4,2),'cover':mat('Hard cover guide',(.35,.32,.24)),'service':mat('Undercroft floor guide',(.18,.2,.29)),'cyan':mat('Route guide',(.05,.65,.73),.5,1),'roof':mat('Roof floor guide',(.17,.19,.23)),'wet':mat('Wet patch intent',(.10,.16,.19),.12),'plaster':mat('Home partition guide',(.50,.51,.47))}
def assign(obj,col,material):
 for old in list(obj.users_collection):old.objects.unlink(obj)
 collections[col].objects.link(obj)
 if material:obj.data.materials.append(M[material])
 return obj
def box(name,x,z,y,w,d,h,material='concrete',col='01_GROUND'):
 # Direct data creation avoids a scene dependency update for every design box.
 mesh=bpy.data.meshes.new(name)
 verts=[(-w/2,-d/2,-h/2),(w/2,-d/2,-h/2),(w/2,d/2,-h/2),(-w/2,d/2,-h/2),(-w/2,-d/2,h/2),(w/2,-d/2,h/2),(w/2,d/2,h/2),(-w/2,d/2,h/2)]
 mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.materials.append(M[material]);o=bpy.data.objects.new(name,mesh);o.location=(x+w/2-72,60-z-d/2,y+h/2);collections[col].objects.link(o);return o
def cyl(name,x,z,y,r,h,material,col='06_LANDSCAPE',vertices=10):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=h,location=(x-72,60-z,y+h/2));o=bpy.context.object;o.name=name;return assign(o,col,material)
def wallx(name,x,z,y,w,opens,col):
 # Openings are floor-to-head height. Headers preserve a 2.4 m clearance target.
 spans=[];cursor=x
 for centre,width in sorted(opens):
  lo=max(x,centre-width/2);hi=min(x+w,centre+width/2)
  if hi<=x or lo>=x+w:continue
  if lo>cursor:spans.append((cursor,lo-cursor))
  if hi>lo:box(name+' lintel',lo,z,y+2.4,hi-lo,.22,.4,'brick',col)
  cursor=max(cursor,hi)
 if cursor<x+w:spans.append((cursor,x+w-cursor))
 for start,width in spans:box(name,start,z,y,width,.22,2.8,'brick',col)
def floor_with_holes(name,r,y,holes,col,material='concrete'):
 x,z,w,d=r;xs=sorted(set([x,x+w]+[v for h in holes for v in [h[0],h[0]+h[2]]if x<v<x+w]));zs=sorted(set([z,z+d]+[v for h in holes for v in [h[1],h[1]+h[3]]if z<v<z+d]))
 for a,b in zip(xs,xs[1:]):
  for c,e in zip(zs,zs[1:]):
   mx,mz=(a+b)/2,(c+e)/2
   if any(h[0]<mx<h[0]+h[2] and h[1]<mz<h[1]+h[3]for h in holes):continue
   box(name,a,c,y-.2,b-a,e-c,.2,material,col)
def stairs(name,x,z,lo,flight=1.5,core=True,col='05_PUBLIC_STAIRS'):
 # 20 risers, 2.8 m run per flight, two 1.5 m landings in a 6 m depth.
 left=.6 if core else .15;right=3.9 if core else 1.65;land=1.5 if core else 1.2
 start=4.5 if core else 5.7;run=2.8;mid=start-run-land
 def stairbox(label,bx,bz,by,bw,bd,bh):
  if core and z>60:bz=z+6-(bz-z)-bd
  return box(label,bx,bz,by,bw,bd,bh,'concrete',col)
 for i in range(10):
  height=(i+1)*.15
  stairbox(name+f' flight A tread {i+1}',x+left,z+start-(i+1)*.28,lo,flight,.28,height)
  stairbox(name+f' flight B tread {i+1}',x+right,z+start-run+i*.28,lo+1.5,flight,.28,height)
 stairbox(name+' mid landing',x+left,z+mid,lo+1.35,right-left+flight,land,.15)
 stairbox(name+' top landing',x if core else x+left,z+start,lo+2.85,6 if core else right-left+flight,land,.15)

floor_with_holes('144 × 120 m site / B1 core openings',[0,0,144,120],-.05,[c['rect']for c in D['cores']if -3 in c['levels']],'00_SITE','ground')
for s in D['surfaces']:
 level=s['level'];r=s['rect'];y=next(l['y']for l in D['levels']if l['id']==level)
 col={'G':'01_GROUND','L1':'02_GALLERIES','L2':'03_UPPER_HOMES','R':'04_ROOFS','B1':'09_UNDERCROFT'}[level]
 if s['kind']=='home':
  holes=[]
  if level=='L2':
   for h in D['homes']:
    if h['type']=='H2'and h['id'].startswith(s['id'].split('-')[0]):holes.append([h['x']+6,h['z']+2,3,6])
  floor_with_holes(s['id'],r,y,holes,col)
 elif s['kind']=='shop':
  x,z,w,d=r;box(s['name']+' floor',x,z,-.1,w,d,.1,'concrete',col);wallx(s['name']+' front',x,z,0,w,[(x+w/2,2)],col);wallx(s['name']+' rear',x,z+d-.22,0,w,[(x+w/2,1.5)],col)
  for xx in [x,x+w-.22]:box(s['name']+' side',xx,z,0,.22,d,2.8,'brick',col)
  box(s['name']+' roof',x,z,2.8,w,d,.2,'concrete',col)
  box(s['name']+' shop glow',x+.5,z-.03,1.0,max(1,w/3),.04,1.0,'warm',col)
 else:
  matname={'garden':'grass','court':'court','gallery':'concrete','service':'service','roof':'roof'}[s['kind']]
  if level=='L1':floor_with_holes(s['id'],r,y,[c['rect']for c in D['cores']],col,matname)
  else:box(s['id'],r[0],r[1],y-.18,r[2],r[3],.18,matname,col)
# Four clear court gates and recognisable markings; no chain-link texture claim.
for z in [50,70]:
 for x,w in [(57,13),(74,13)]:box('Court fence top rail',x,z,2.5,w,.06,.06,'concrete')
 for x in [57,60,63,66,70,74,78,81,84,87]:box('Court fence post',x,z,0,.08,.08,2.6,'concrete')
for x in [57,87]:
 for z,h in [(50,8),(62,8)]:box('Court fence top rail',x,z,2.5,.06,h,.06,'concrete')
 for z in [50,54,58,62,66,70]:box('Court fence post',x,z,0,.08,.08,2.6,'concrete')
for z in [51,69]:box('Court paint',58,z,.01,28,.08,.006,'plaster')
for x in [58,72,86]:box('Court paint',x,51,.01,.08,18,.006,'plaster')
for b in D['blocks']:
 x,z,w,d=b['rect']
 for y,col in [(0,'01_GROUND'),(3,'02_GALLERIES'),(6,'03_UPPER_HOMES')]:
  homes=[h for h in D['homes']if h['id'].startswith(b['id'])and y in h['levels']]
  opens=[(x+21,6)]if y==0 else[]
  for h in homes:opens.append((h['x']+(.75 if h['type']=='H1'else 5.25),1.1))
  for zz in [z,z+d-.22]:
   coredoors=[(c['rect'][0]+7.5 if c['rect'][0]==x else c['rect'][0]-1.5,1.5)for c in D['cores']if c['block']==b['id']]if (z<60 and zz>z)or(z>60 and zz==z)else[]
   wallx(b['name']+' facade',x,zz,y,w,opens+coredoors,col)
  # Side walls leave the ground cross-arcade open.
  for xx in [x,x+w-.22]:
   zz=z if z<60 else z+6;depth=12 if y==0 else d
   if y!=0:zz=z
   box(b['name']+' flank',xx,zz,y,.22,depth,2.8,'brick',col)
  # External window details are presentation markers, not new sightline permissions.
  for xx in [x+3,x+7,x+11,x+15,x+28,x+32]:
   for zz in [z-.03,z+d+.01]:box('Window intent',xx,zz,y+.9,1.3,.06,1.35,'warm'if rng.random()<.32 else'glass',col)
 # Roof screens; only two terraces are accessible.
 if b['roofPlayable']:
  box(b['name']+' roof plant',x+2,z+2,9,10,5,2.1,'cover','04_ROOFS')
  box(b['name']+' roof plant',x+21,z+10,9,9,5,2.1,'cover','04_ROOFS')
  for xx in [x,x+w-.2]:box('Opaque spawn-facing roof screen',xx,z,9,.2,d,2.1,'brick','04_ROOFS')
 else:
  box(b['name']+' CLOSED non-playable roof',x,z,8.8,w,d,.2,'roof','04_ROOFS')
for c in D['cores']:
 x,z,_,_=c['rect']
 for lo,hi in zip(c['levels'],c['levels'][1:]):stairs(c['id'],x,z,lo)
for h in D['homes']:
 y=h['y'];col='01_GROUND'if y==0 else'02_GALLERIES'
 # Interior low partitions reveal the module plan in cutaway; unfinished art is explicit.
 for ry in h['levels']:
  hc='01_GROUND'if ry==0 else'02_GALLERIES'if ry==3 else'03_UPPER_HOMES'
  hx=h['x']+1.5 if h['type']=='H1'else h['x']+4.5
  for zz,dd in [(h['z'],2),(h['z']+4.5,1)]:box(h['id']+' hall partition guide',hx,zz,ry,.12,dd,1.0,'plaster',hc)
 if h['type']=='H2':stairs(h['id']+' PRIVATE',h['x']+6,h['z']+1.0,3,1.2,False,col)
# Gallery rails have gaps at core entries; supports at the two long link spans.
for z in [36,84]:
 for x in range(30,115,6):
  if any(c['rect'][0]<=x<=c['rect'][0]+6 for c in D['cores']if abs(c['rect'][1]-(36 if z==36 else 78))<1):continue
  box('Gallery parapet',x,z,3,3,.15,1.2,'concrete','02_GALLERIES')
 for x in [66,78]:box('Link support',x,z,-.1,.4,.4,3.1,'concrete','01_GROUND')
for c in D['cover']:box(c['id']+' '+c['kind'],c['rect'][0],c['rect'][1],c['y'],c['rect'][2],c['rect'][3],c['height'],'cover','01_GROUND'if c['y']==0 else'02_GALLERIES')
for p in D['planting']:box(p['id']+' planted soil',p['rect'][0],p['rect'][1],.015,p['rect'][2],p['rect'][3],.035,'grass','06_LANDSCAPE')
for t in D['trees']:
 cyl(t['id']+' trunk',t['x'],t['z'],0,t['trunkRadius'],4.5,'wood')
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=t['canopyRadius'],location=(t['x']-72,60-t['z'],5.4));o=bpy.context.object;o.name=t['id']+' canopy PROXY';o.scale.z=.9;assign(o,'06_LANDSCAPE','leaf')
for p in D['wetAreas']:box(p['id']+' wetness intent',p['rect'][0],p['rect'][1],.055,p['rect'][2],p['rect'][3],.006,'wet','06_LANDSCAPE')
for z in D['detailZones']:
 if z['name']=='undercroft':continue
 x,zz,w,d=z['rect']
 for i in range(10):box(z['name']+' litter PROXY',x+rng.uniform(.5,w-.5),zz+rng.uniform(.5,d-.5),.065,.2,.15,.015,'plaster','06_LANDSCAPE')
for l in D['lights']:
 cyl(l['id']+' pole',l['x'],l['z'],0,.06,l['y'],'concrete','07_LIGHT_INTENT')
 box(l['id']+' warm fixture',l['x']-.2,l['z']-.15,l['y'],.4,.3,.12,'warm','07_LIGHT_INTENT')
 data=bpy.data.lights.new(l['id']+' review-only lamp','AREA');data.energy=160 if l['kind']=='door'else 400;data.color=(1,.55,.25);data.shape='DISK';data.size=1.3
 o=bpy.data.objects.new(data.name,data);collections['07_LIGHT_INTENT'].objects.link(o);o.location=(l['x']-72,60-l['z'],l['y'])
# Route guides are editable but hidden from render/export, never used as runtime navigation.
nodes={n['id']:n for n in D['nodes']}
for e in D['edges']:
 a,b=nodes[e['a']],nodes[e['b']];pts=[[a['x'],a['z'],a['y']]]+e.get('via',[])+[[b['x'],b['z'],b['y']]]
 curve=bpy.data.curves.new(e['a']+' → '+e['b'],'CURVE');curve.dimensions='3D';curve.bevel_depth=.06;curve.bevel_resolution=0;sp=curve.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,v in zip(sp.points,pts):p.co=(v[0]-72,60-v[1],v[2]+.2,1)
 o=bpy.data.objects.new(curve.name,curve);collections['08_ROUTE_GUIDES'].objects.link(o);curve.materials.append(M['cyan'])
collections['08_ROUTE_GUIDES'].hide_render=True;collections['08_ROUTE_GUIDES'].hide_viewport=True
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.32,.52,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
sun=bpy.data.lights.new('Review blue-hour key','SUN');sun.energy=1.1;sun.angle=.3;sun.color=(.65,.78,1);o=bpy.data.objects.new(sun.name,sun);collections['07_LIGHT_INTENT'].objects.link(o);o.rotation_euler=(.5,-.4,-.8)
cam=bpy.data.cameras.new('Metric overview');o=bpy.data.objects.new('Metric overview',cam);scene.collection.objects.link(o);o.location=(135,-160,175);o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler();cam.type='ORTHO';cam.ortho_scale=214;scene.camera=o
# This cloud Blender build has no OpenImageDenoise support. Use ordinary CPU samples.
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=64;scene.cycles.use_denoising=False;scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.render.image_settings.file_format='PNG'
blend=ROOT/'assets/blender/maps/heron-reach-32.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH'and not any(c.name=='08_ROUTE_GUIDES'for c in o.users_collection):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'heron-reach-32-massing.glb'),export_format='GLB',use_selection=True,export_extras=True,export_yup=True)
stats={'scope':'Separate design massing; not game collision, final art or runtime performance evidence','mapSha256':scene['map_sha256'],'meshObjects':sum(o.type=='MESH'for o in scene.objects),'publicStairFlights':sum((len(c['levels'])-1)*2 for c in D['cores']),'homeStairFlights':16,'source':str(blend.relative_to(ROOT)),'glbBytes':(OUT/'heron-reach-32-massing.glb').stat().st_size,'render':'Cycles CPU, 64 samples without denoising, 1400×1100; review lighting only'}
(OUT/'blender-build.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps(stats))
scene.render.filepath=str(OUT/'09-blender-massing.png');bpy.ops.render.render(write_still=True)
