"""Original dimensional shop stock inside the existing furniture collision footprints.

blender -b --python-exit-code 1 --python scripts/maps/art/build_heron_shop_depth.py
The old photo cards and four Corner shelf render placements are hidden by the runtime.
This source never edits collision/navigation, and never opens an older Blender file.
"""
from pathlib import Path
import hashlib,json,math,random,subprocess,sys
import bpy
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];sys.path.insert(0,str(HERE))
from heron_art_mesh import Builder

layout_path=ROOT/'assets/blender/heron-reach/layout.json'
L=json.loads(layout_path.read_text())
atlas_path=ROOT/'public/materials/heron/lived/shop-lived-color.webp'
atlas=json.loads((atlas_path.parent/'atlas.json').read_text())['cells']
WHITE,BLACK,GALV,PRINT='hr_upvc_white','hr_steel_black','hr_steel_galv','hr_lived_atlas'
PACKS=['package_oats','package_tea','package_rice','package_biscuits','package_flakes']
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
col=bpy.data.collections.new('HR_SHOP_DEPTH');bpy.context.scene.collection.children.link(col)
B=Builder(lambda _:col);rng=random.Random(214819);features=[];mats={}

def box(group,mat,x0,x1,y0,y1,z0,z1,shade=1):
    # Contact darkening and darker undersides are vertex colours, not per-frame effects.
    def colour(p):
        h=(p[1]-y0)/max(y1-y0,.001)
        k=shade*(.62+.38*h)
        return (k,k*.985,k*.95,1)
    B.box(group,mat,x0,x1,y0,y1,z0,z1,col=colour)

def face(group,cell,x0,x1,y0,y1,z,north=True):
    u0,v0,u1,v1=atlas[cell]['uv_rect']
    pts=[(x1,y0,z),(x0,y0,z),(x0,y1,z),(x1,y1,z)] if north else [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
    B.quad(group,PRINT,*pts,uv=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)])

def package(group,cell,x,y,z,w,d,h):
    box(group,PRINT,x-w/2,x+w/2,y,y+h,z-d/2,z+d/2,shade=rng.uniform(.88,1))
    a=B.acc(group,PRINT);u0,v0,u1,v1=atlas[cell]['uv_rect']
    # Full label on front/back; narrow edge colour on sides and cap fold on top/bottom.
    for k in [-6,-5]:
        a.uvs[k]=[(u0,v0),(u0+(u1-u0)*.09,v0),(u0+(u1-u0)*.09,v1),(u0,v1)]
    for k in [-4,-3]:
        a.uvs[k]=[(u0,v1-(v1-v0)*.05),(u1,v1-(v1-v0)*.05),(u1,v1),(u0,v1)]
    for k in [-2,-1]:a.uvs[k]=[(u0,v0),(u1,v0),(u1,v1),(u0,v1)]

def tin(group,cell,x,y,z,r,h):
    # Eight-sided tins: actual silhouettes/lids with contact shading, one atlas texture.
    a=B.acc(group,PRINT);start=len(a.faces)
    B.cylinder(group,PRINT,(x,y+.003,z),(x,y+h-.005,z),r,8,caps=False)
    u0,v0,u1,v1=atlas[cell]['uv_rect']
    for k in range(start,len(a.faces)):
        a.uvs[k]=[(u0+(u1-u0)*u/(math.tau*r),v0+(v1-v0)*v/(h-.008)) for u,v in a.uvs[k]]
        a.cols[k]=[(.57,.56,.54,1),(.57,.56,.54,1),(.94,.93,.90,1),(.94,.93,.90,1)]
    B.cylinder(group,GALV,(x,y,z),(x,y+.009,z),r*1.015,8,col=(.42,.43,.40,1))
    B.cylinder(group,GALV,(x,y+h-.009,z),(x,y+h,z),r*1.015,8,col=(.72,.74,.68,1))

def points_since(before):
    return [(v[0]+72,v[2],60-v[1]) for key,a in B.groups.items() for v in a.verts[before.get(key,0):]]

def record(name,before,bounds,notes):
    pts=points_since(before)
    lo=[min(p[i] for p in pts)for i in range(3)];hi=[max(p[i]for p in pts)for i in range(3)]
    assert all(lo[i]>=bounds[0][i]-1e-5 and hi[i]<=bounds[1][i]+1e-5 for i in range(3)),(name,lo,hi,bounds)
    features.append({'name':name,'mapBounds':{'min':lo,'max':hi},'allowedBounds':bounds,'notes':notes})

shelves=[p for p in L['dressing'] if p['asset']=='SHOP_SHELF_UNIT' and 102<p['x']<120 and 48<p['z']<57]
assert len(shelves)==4
for p in shelves:
    before={k:len(v.verts)for k,v in B.groups.items()}
    x,z=p['x'],p['z'];middle=abs(z-52.5)<.1;group='depth/corner'
    # Original footprint: x±.6,z±.25,y0..2.07. No growth or hidden new cover.
    for xx in [x-.585,x+.585]:
        box(group,WHITE,xx-.015,xx+.015,.015,2.07,z-.24,z+.24,.78)
    back_z=z if middle else z+.229
    box(group,WHITE,x-.57,x+.57,.08,2.055,back_z-.009,back_z+.009,.78)
    for h in [.14,.52,.90,1.28,1.66]:
        box(group,WHITE,x-.575,x+.575,h,h+.022,z-.24,z+.24,.88)
        # Dim undersides create a thin contact/shadow edge at every real shelf.
        box(group,BLACK,x-.57,x+.57,h-.006,h,z-.23,z+.23,.64)
    box(group,WHITE,x-.59,x+.59,2.035,2.07,z-.24,z+.24,.84)
    directions=[-1,1] if middle else [-1]
    for side in directions:
        north=side<0;edge=z+side*.241
        for row,h in enumerate([.162,.542,.922,1.302,1.682]):
            # Intentionally uneven groups/gaps, with real shelf depth and repeatable stock.
            count=7 if row in [1,3] else 5
            for k in range(count):
                if (row+k+(1 if side>0 else 0))%11==7:continue
                cx=x-.47+k*(.94/(count-1))
                if row in [1,3]:
                    tin(group,PACKS[(row+k)%5],cx,h,z+side*.123,.051,.20 if row==1 else .24)
                else:
                    w=.145+rng.random()*.018;hh=.21+rng.random()*.075
                    if row==4:hh=min(hh,.205)
                    package(group,PACKS[(row+k)%5],cx,h,z+side*.132,w,.15,hh)
            face(group,'price_strip',x-.558,x+.558,h-.032,h-.008,edge,north)
        face(group,'groceries' if x<111 else 'household',x-.54,x+.54,1.90,2.025,z+side*.242,north)
    # Small dark foot pads stay under the exact uprights.
    for xx in [x-.575,x+.575]:
        for zz in [z-.215,z+.215]:box(group,BLACK,xx-.023,xx+.023,0,.022,zz-.025,zz+.025,.60)
    record('Corner replacement shelf at %.2f,%.2f'%(x,z),before,
           [[x-.6,0,z-.25],[x+.6,2.07,z+.25]],
           'Double-sided centre gondola' if middle else 'North-facing rear-wall shelving')

# Original washer/dryer meshes remain. Only small detergent stock and folded linens are new.
laundry_shops=[s for s in L['shops']if s['name']in ['LAUNDERETTE','WASHHOUSE']]
for shop in laundry_shops:
    sx,sz,sw,sd=shop['rect']
    washers=[p for p in L['dressing'] if p['asset']=='WASHING_MACHINE' and sx<p['x']<sx+sw and sz<p['z']<sz+sd]
    for i,p in enumerate(washers):
        before={k:len(v.verts)for k,v in B.groups.items()};x,z=p['x'],p['z'];group='depth/laundry'
        # Match each authoritative dress collider by its centre.
        candidates=[b for b in L['boxes']if b['id']=='dress' and b['x0']<x<b['x1'] and b['z0']<z<b['z1'] and abs(b['y1']-1.1)<.01]
        assert len(candidates)==1,(shop['name'],p,candidates)
        bound=candidates[0];x0,x1,z0,z1=bound['x0'],bound['x1'],bound['z0'],bound['z1']
        # A supported folded stack; width is kept under 0.26m even in rotated machines.
        for k in range(3):
            box(group,WHITE,x-.12,x+.12,1.101+k*.028,1.125+k*.028,z-.12,z+.10,
                [.79,.68,.88][k])
        # Small unbranded laundry bottle, with an actual shoulder/neck and dark screw cap.
        B.cylinder(group,WHITE,(x+.19,1.101,z-.04),(x+.19,1.215,z-.04),.037,8,col=(.76,.81,.72,1))
        B.cylinder(group,WHITE,(x+.19,1.215,z-.04),(x+.19,1.25,z-.04),.037,8,r2=.017,col=(.87,.91,.81,1))
        B.cylinder(group,BLACK,(x+.19,1.25,z-.04),(x+.19,1.275,z-.04),.019,8)
        record(shop['name']+' washer-top detail %d'%i,before,[[x0,1.10,z0],[x1,1.29,z1]],
               'Small folded goods and sealed supplies rest on the existing 1.10m washer top; x/z collider footprint unchanged')

# No generated polygon may cross the established Corner door/aisle route volumes.
routes=[('front',[110.14,.035,47.55],[111.86,2.4,50.15]),
        ('centre aisle',[110,.035,50.15],[112,2.4,55.8]),
        ('rear',[110.31,.035,55.8],[111.69,2.4,57.45])]
for a in B.groups.values():
    for f in a.faces:
        pts=[(a.verts[i][0]+72,a.verts[i][2],60-a.verts[i][1])for i in f]
        lo=[min(p[j]for p in pts)for j in range(3)];hi=[max(p[j]for p in pts)for j in range(3)]
        for name,p0,p1 in routes:
            assert not all(hi[j]>p0[j]+1e-5 and lo[j]<p1[j]-1e-5 for j in range(3)),(name,lo,hi)

def material(name):
    if name in mats:return mats[name]
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True
    nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.78
    vc=nt.nodes.new('ShaderNodeVertexColor');vc.layer_name='Col'
    mix=nt.nodes.new('ShaderNodeMix');mix.data_type='RGBA';mix.blend_type='MULTIPLY';mix.inputs['Factor'].default_value=1
    nt.links.new(vc.outputs['Color'],mix.inputs['B']);nt.links.new(mix.outputs['Result'],bs.inputs['Base Color'])
    if name==PRINT:
        im=bpy.data.images.load(str(atlas_path));im.pack();im.colorspace_settings.name='sRGB'
        tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im
        nt.links.new(tex.outputs['Color'],mix.inputs['A']);nt.links.new(tex.outputs['Color'],bs.inputs['Emission Color'])
        bs.inputs['Emission Strength'].default_value=.08
    else:
        mix.inputs['A'].default_value={WHITE:(.70,.70,.68,1),BLACK:(.025,.03,.025,1),GALV:(.45,.46,.44,1)}[name]
        bs.inputs['Metallic'].default_value=.7 if name in [BLACK,GALV]else 0
    mats[name]=m;return m

objects=B.build(material)
tris=sum(sum(len(p.vertices)-2 for p in o.data.polygons)for o in objects)
assert tris<20000 and len(objects)<=10
folder=ROOT/'assets/blender/heron-reach';out=ROOT/'public/models/heron-reach'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'shop-depth.blend'),compress=True)
raw=out/'heron-reach-shop-depth.raw.glb';packed=out/'heron-reach-shop-depth.glb'
bpy.ops.export_scene.gltf(filepath=str(raw),export_format='GLB',export_image_format='WEBP',export_apply=True,export_yup=True)
subprocess.run(['npx','--no-install','gltfpack','-i',str(raw),'-o',str(packed),'-cc','-kn','-km','-kv','-vtf'],cwd=ROOT,check=True)
manifest={'provenance':'Original ONSITE procedural shelf/stock geometry; reuses original lived atlas with its existing font/art provenance.',
 'builder':str(Path(__file__).relative_to(ROOT)),'builderSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'blender':bpy.app.version_string,'coordinates':'Map metres, glTF world x=mapX-72,y=mapY,z=mapZ-60. No loader offset.',
 'layoutSHA256':hashlib.sha256(layout_path.read_bytes()).hexdigest(),'collision':'No changes. New shelving is contained within four existing collider boxes.',
 'triangles':tris,'materialBatches':len(objects),'sharedMaterials':[WHITE,BLACK,GALV],
 'embeddedMaterial':PRINT,'textureSHA256':hashlib.sha256(atlas_path.read_bytes()).hexdigest(),
 'reuseAtlasMaterial':'Reuse the same hr_lived_atlas material instance as the lived kit where possible to avoid a second decoded texture allocation.',
 'hideOriginalShelfRenderPlacements':shelves,
 'hideCardNodes':['E-shop/interior / hr_shop_image_corner','W-shops/interior / hr_shop_image_laundry','C-store/interior / hr_shop_image_laundry'],
 'features':features,'routeChecks':'passed','footprintChecks':'passed','protectedRoutes':routes,
 'rawGLBBytes':raw.stat().st_size,'compressedGLBBytes':packed.stat().st_size,'compressedGLBSHA256':hashlib.sha256(packed.read_bytes()).hexdigest()}
(folder/'shop-depth-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('SHOP_DEPTH',tris,'triangles;',len(objects),'batches;',packed.stat().st_size,'bytes; route and footprint checks passed')
