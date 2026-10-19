"""Small, original render details fitted to The Corner's existing architecture and props.

blender -b --python-exit-code 1 --python scripts/maps/art/build_heron_lived_detail.py
npx gltfpack -i public/models/heron-reach/heron-reach-lived.raw.glb \
  -o public/models/heron-reach/heron-reach-lived.glb -cc -kn -km -kv -vtf

Map coordinates are metres, x east / y up / z south. Builder performs the only axis/origin
conversion. Never opens an existing .blend or changes layout, collision, or navigation.
"""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
import math
import random
import subprocess
import sys

import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from heron_art_mesh import Builder

LAYOUT_PATH = ROOT / 'assets/blender/heron-reach/layout.json'
ATLAS_DIR = ROOT / 'public/materials/heron/lived'
L = json.loads(LAYOUT_PATH.read_text())
ATLAS = json.loads((ATLAS_DIR / 'atlas.json').read_text())
CORNER = next(s for s in L['shops'] if s['name'] == 'THE CORNER')
assert CORNER['rect'] == [102, 48, 18, 9], 'Recheck every attachment after a layout change'
SHELVES = [p for p in L['dressing'] if p['asset'] == 'SHOP_SHELF_UNIT'
           and 102 < p['x'] < 120 and 48 < p['z'] < 57]
assert len(SHELVES) == 4

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1
collection = bpy.data.collections.new('HR_LIVED_DETAIL')
bpy.context.scene.collection.children.link(collection)
B = Builder(lambda _: collection)
GROUP = 'lived/corner-and-service'
BLACK, AGED, GALV, RUBBER, PRINT = (
    'hr_steel_black', 'hr_steel_aged', 'hr_steel_galv', 'hr_rubber', 'hr_lived_atlas')
features = []
materials = {}
rng = random.Random(191026)


def box(mat, x0, x1, y0, y1, z0, z1, **kw):
    B.box(GROUP, mat, x0, x1, y0, y1, z0, z1, **kw)


def tube(mat, a, b, r, seg=8):
    B.cylinder(GROUP, mat, a, b, r, seg)


def uv_rect(name):
    # Metadata keeps the texture generator independent of the geometry authoring.
    cell = ATLAS.get('cells', ATLAS.get('regions', ATLAS))[name]
    return cell['uv_rect']


def print_face(name, x0, x1, y0, y1, z, north=True):
    u0, v0, u1, v1 = uv_rect(name)
    if north:
        pts = [(x1, y0, z), (x0, y0, z), (x0, y1, z), (x1, y1, z)]
    else:
        pts = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    B.quad(GROUP, PRINT, *pts, uv=[(u0, v0), (u1, v0), (u1, v1), (u0, v1)])


def printed_box(name, x0, x1, y0, y1, z0, z1):
    # The atlas edge is continued onto package sides/top rather than adding a material batch.
    box(PRINT, x0, x1, y0, y1, z0, z1)
    acc = B.acc(GROUP, PRINT)
    u0, v0, u1, v1 = uv_rect(name)
    for i in range(-6, 0):
        acc.uvs[i] = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    # Explicitly oriented front/back labels make the text readable from both shop approaches.
    print_face(name, x0, x1, y0, y1, z0 - .0005)
    print_face(name, x0, x1, y0, y1, z1 + .0005, north=False)


def sign(name, x, y, z, width, height, north=True, frame=True):
    x0, x1 = x-width/2, x+width/2
    y0, y1 = y-height/2, y+height/2
    depth = .008
    box(BLACK, x0-.012, x1+.012, y0-.012, y1+.012, z-depth/2, z+depth/2)
    print_face(name, x0, x1, y0, y1, z + (-.005 if north else .005), north)
    if frame:
        for cx in [x0+.012, x1-.012]:
            for cy in [y0+.012, y1-.012]:
                tube(GALV, (cx,cy,z-.006), (cx,cy,z-.009), .004, 6)


def map_point(p):
    return (p[0]+72, p[2], 60-p[1])


@contextmanager
def feature(name, support, notes):
    previous = {key: len(acc.verts) for key, acc in B.groups.items()}
    yield
    points = [map_point(p) for key, acc in B.groups.items()
              for p in acc.verts[previous.get(key, 0):]]
    lo = [round(min(p[i] for p in points), 5) for i in range(3)]
    hi = [round(max(p[i] for p in points), 5) for i in range(3)]
    features.append({'name': name, 'support': support, 'mapBounds': {'min': lo, 'max': hi},
                     'needsCollision': False, 'notes': notes})


with feature('Recessed window trim and raised shutter housings', 'Existing north wall and window frames',
             'Both glazing bays retain their open views. Door housing starts above the 2.4 m portal.'):
    for left, right in [(102.6,109.5),(112.5,119.4)]:
        # Existing frames are z=48.06..48.14. Added outer beads recess the glazing behind a
        # thin shadow line, without closing a window or extending into the doorway.
        for x in [left, right]:
            box(BLACK, x-.027, x+.027, .605, 2.205, 47.978, 48.065)
            box(AGED, x-.028, x-.018, .65, 2.17, 47.974, 47.985)
        box(BLACK, left-.03, right+.03, .612, .645, 47.965, 48.07)
        box(GALV, left+.04, right-.04, .642, .651, 47.962, 48.01,
            col=(.32,.33,.30,1))
        box(BLACK, left-.05, right+.05, 2.205, 2.39, 47.84, 48.08)
        box(AGED, left-.04, right+.04, 2.207, 2.225, 47.829, 47.85)
        box(BLACK, left-.065, right+.065, 2.387, 2.41, 47.80, 48.11)
        # Shutter access-panel seams and six small fasteners, no lowered shutter.
        for x in [left+.06, (left+right)/2, right-.06]:
            box(GALV,x-.004,x+.004,2.25,2.355,47.833,47.839,col=(.17,.18,.16,1))
            for y in [2.242,2.363]:
                tube(GALV,(x,y,47.837),(x,y,47.828),.007,6)
        for x in [left+(right-left)/3, left+(right-left)*2/3]:
            box(AGED,x-.032,x-.018,.69,2.15,48.048,48.059,col=(.45,.49,.45,1))
        # A few scuffed metal edge fragments, deliberately uneven and kept on the trim.
        for _ in range(10):
            x = rng.uniform(left+.08,right-.12)
            box(AGED,x,x+rng.uniform(.025,.10),.613,.620,47.961,47.968,
                col=(.55,.53,.45,1))
    box(BLACK,109.95,112.05,2.405,2.49,47.87,48.15)
    # Guides sit on the solid jambs, entirely outside x=110..112 opening.
    for x in [109.955,112.045]:
        box(BLACK,x-.025,x+.025,.03,2.405,47.97,48.11)
        box(GALV,x-.008,x+.008,.08,2.37,47.958,47.97,col=(.22,.24,.21,1))

with feature('Shop window notices', 'Existing closed north glazing, z=48.10',
             'Small opaque printed cards cover under 10 percent of the two glazing bays. No portal signs.'):
    sign('daily_essentials',108.46,1.29,48.072,.64,.811)
    sign('open_hours',112.91,1.69,48.072,.43,.43)
    sign('services',116.65,1.10,48.072,1.10,1.10/2.3)
    sign('value_prices',103.48,1.12,48.072,.80,.80/2.875)
    # Tape corners are slim, irregular cream tabs on the same glazing; they remain behind trim.
    for x,y in [(108.14,1.69),(108.78,.89),(112.70,1.90),(113.12,1.48)]:
        box(GALV,x-.026,x+.026,y-.012,y+.012,48.061,48.066,
            col=(.58,.56,.43,1),faces='-z')

with feature('Occupied shelf backs, category strips and top stock', 'Four existing SHOP_SHELF_UNIT colliders',
             'Notice faces stay inside shelf footprints; screwheads extend 3 mm beyond the north edge. Small packages stand on the 2.07 m top rail; maximum height 2.30 m.'):
    package_names = ['package_oats','package_tea','package_rice','package_biscuits','package_flakes']
    for idx, p in enumerate(SHELVES):
        x,z = p['x'],p['z']
        middle = abs(z-52.5)<.1
        # The existing centre units face south, so their blank back boards face the entry.
        if middle:
            # The 12 mm back board is centred at local +Y=.238, giving an exposed
            # map z-.244 face. Print at z-.249 clears it by 5 mm, including quantisation.
            # Tiny screwheads reach z-.253: only 3 mm beyond the existing collider.
            sign('daily_essentials' if idx%2==0 else 'fresh_daily', x, 1.22, z-.244,
                 .82, 1.038 if idx%2==0 else .82/2.3)
            if idx%2:
                sign('value_prices',x,.69,z-.244,.82,.82/2.875)
            sign('groceries' if idx%2==0 else 'household',x,1.92,z-.244,1.04,1.04/5.75)
        else:
            # Existing rear units face north. These replace no stock and attach to the four
            # narrow shelf lips, avoiding the bottles, tins, and products already modelled.
            for h in [.52,.88,1.24,1.58]:
                print_face('price_strip',x-.55,x+.55,h-.021,h+.010,z-.181)
            sign('groceries' if idx%2==0 else 'household',x,2.027,z-.239,1.05,.065)
        # A restrained line of small overspill boxes on the existing top rail. Every pack
        # stays at least 6 cm inside the collider edge; no new furniture footprint is added.
        for k in range(5):
            cx = x-.40+k*.19
            width = [.13,.12,.14,.15,.13][k]
            height = [.215,.18,.22,.16,.225][(idx+k)%5]
            printed_box(package_names[(idx+k)%5],cx-width/2,cx+width/2,
                        2.071,2.071+height,z-.08,z+.075)
        # Folded shipping tray under the packages, on top of the same support beam.
        box(AGED,x-.51,x+.51,2.071,2.088,z-.095,z+.09,col=(.55,.47,.34,1))

with feature('Rear display mounting rails', 'Existing rear-wall image panels, z=56.795',
             'Thin perimeter fixings identify the existing flush wall panels; maximum projection 45 mm from the existing inner wall. The rear doorway remains clear.'):
    # The old shop cards already sit 5 mm in front of the inner masonry at z=56.80.
    # Their hard, unsupported edges could read as floating. These narrow perimeter
    # rails attach them visually to the wall, without adding furniture or false depth.
    for x0,x1 in [(102.26,109.95),(112.05,119.74)]:
        for x in [x0,x1]:
            box(BLACK,x-.015,x+.015,.265,2.685,56.760,56.795)
        for y in [.28,2.67]:
            box(BLACK,x0-.015,x1+.015,y-.015,y+.015,56.760,56.795)
        box(AGED,x0-.015,x1+.015,2.678,2.688,56.755,56.77,
            col=(.35,.37,.32,1))

with feature('Open door pushbar and security conduit', 'Existing north door leaf and solid north-east jamb',
             'Pushbar hugs the pre-existing leaf at x=110.06..110.105; new geometry ends at x=110.130. The central doorway stays clear.'):
    # Existing leaf is held 92 degrees open along z=48.22..50.10.
    tube(GALV,(110.121,1.02,48.51),(110.121,1.02,49.76),.009)
    for z in [48.51,49.76]:
        tube(GALV,(110.106,1.02,z),(110.121,1.02,z),.009)
    # Surface cabling sits on solid wall either side of the entrance, not across glass.
    tube(BLACK,(112.26,.15,47.965),(112.26,2.20,47.965),.012)
    box(BLACK,112.18,112.34,1.28,1.46,47.93,48.012)
    box(GALV,112.195,112.325,1.295,1.445,47.922,47.931,col=(.18,.20,.17,1))
    for h in [.26,.91,1.64,2.12]:
        box(AGED,112.232,112.288,h-.014,h+.014,47.941,47.974)

with feature('Front rainwater pipe and flush pavement drains', 'Existing north-east brick pier and ground at y=0',
             'Pipe is 90 mm across and hugs the solid end pier. Grates are 5 mm above the existing paving, away from the portal.'):
    tube(BLACK,(119.72,.12,47.94),(119.72,2.73,47.94),.045,10)
    for h in [.28,1.22,2.34]:
        tube(AGED,(119.72,h-.024,47.94),(119.72,h+.024,47.94),.051,10)
        box(AGED,119.64,119.80,h-.017,h+.017,47.97,48.018)
    tube(BLACK,(119.72,.12,47.94),(119.72,.055,47.78),.046,10)
    for x,z,w,d in [(119.72,47.61,.36,.42),(105.02,47.52,.48,.30),(117.56,57.34,.42,.30)]:
        box(RUBBER,x-w/2,x+w/2,.001,.003,z-d/2,z+d/2,faces='+y')
        for a,b,c,e in [(x-w/2,x+w/2,z-d/2,z-d/2+.018),
                        (x-w/2,x+w/2,z+d/2-.018,z+d/2),
                        (x-w/2,x-w/2+.018,z-d/2,z+d/2),
                        (x+w/2-.018,x+w/2,z-d/2,z+d/2)]:
            box(AGED,a,b,.003,.005,c,e,faces='+y')
        count = int(w/.045)
        for i in range(1,count):
            px=x-w/2+i*w/count
            box(GALV,px-.006,px+.006,.003,.005,z-d/2+.018,z+d/2-.018,
                faces='+y',col=(.16,.18,.15,1))

with feature('Rear service ventilation, electrical box and access notices', 'Existing solid south wall, clear of the rear door',
             'Ventilator/box projection is at most 11 cm. All are east of x=113.60, rear opening is x=110.25..111.75.'):
    # A shallow louvred grille against the existing rear masonry, not a floating appliance.
    box(BLACK,115.40,116.36,1.86,2.46,56.986,57.075)
    for i in range(10):
        h=1.90+i*.052
        box(GALV,115.435,116.325,h,h+.024,57.071,57.097,col=(.30,.32,.28,1))
        box(AGED,115.435,116.325,h-.006,h,57.094,57.102,col=(.45,.39,.29,1))
    box(BLACK,117.02,117.40,1.38,1.91,56.992,57.090)
    box(GALV,117.035,117.385,1.395,1.895,57.09,57.108,col=(.34,.38,.32,1))
    tube(BLACK,(117.21,1.91,57.045),(117.21,2.57,57.045),.012)
    tube(BLACK,(115.90,2.57,57.045),(119.30,2.57,57.045),.012)
    tube(BLACK,(115.90,2.46,57.045),(115.90,2.57,57.045),.012)
    for x in [116.1,117.3,118.5]:
        box(AGED,x-.014,x+.014,2.54,2.60,57.028,57.066)
    sign('keep_clear',113.98,1.68,57.020,.73,.73/2.875,north=False)
    sign('deliveries',117.21,1.70,57.115,.25,.25/2.0909,north=False,frame=False)


# Geometric assertion, independent of physics: no new polygon crosses the protected existing
# route. The narrowest rear frame defines 1.38 m; the central furniture aisle remains 2.00 m.
protected = [
    {'name':'front portal between existing open leaf and opposite frame',
     'min':[110.14,.035,47.55], 'max':[111.86,2.40,50.15]},
    {'name':'central aisle between existing shelf colliders',
     'min':[110.0,.035,50.15], 'max':[112.0,2.40,55.80]},
    {'name':'rear portal between existing frames',
     'min':[110.31,.035,55.80], 'max':[111.69,2.40,57.45]},
]
for acc in B.groups.values():
    for polygon in acc.faces:
        points=[map_point(acc.verts[i]) for i in polygon]
        lo=[min(p[i] for p in points) for i in range(3)]
        hi=[max(p[i] for p in points) for i in range(3)]
        for route in protected:
            assert not all(hi[i]>route['min'][i]+.00001 and lo[i]<route['max'][i]-.00001
                           for i in range(3)), f'New detail crosses {route["name"]}: {lo}, {hi}'


def material(name):
    if name in materials:
        return materials[name]
    mat=bpy.data.materials.new(name)
    mat.use_nodes=True
    mat.use_backface_culling=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    vcol=mat.node_tree.nodes.new('ShaderNodeVertexColor');vcol.layer_name='Col'
    multiply=mat.node_tree.nodes.new('ShaderNodeMix')
    multiply.data_type='RGBA';multiply.blend_type='MULTIPLY'
    multiply.inputs['Factor'].default_value=1
    mat.node_tree.links.new(vcol.outputs['Color'],multiply.inputs['B'])
    mat.node_tree.links.new(multiply.outputs['Result'],bs.inputs['Base Color'])
    settings={BLACK:((.025,.030,.025,1),.55,.62),
              AGED:((.23,.15,.095,1),.72,.45),
              GALV:((.46,.48,.43,1),.46,.80),
              RUBBER:((.015,.018,.016,1),.96,0)}
    if name==PRINT:
        path=ATLAS_DIR/'shop-lived-color.webp'
        im=bpy.data.images.load(str(path));im.pack()
        im.colorspace_settings.name='sRGB'
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im
        mat.node_tree.links.new(tex.outputs['Color'],multiply.inputs['A'])
        mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Emission Color'])
        bs.inputs['Emission Strength'].default_value=.08
        bs.inputs['Roughness'].default_value=.78
    else:
        col,rough,metal=settings[name]
        multiply.inputs['A'].default_value=col
        bs.inputs['Roughness'].default_value=rough
        bs.inputs['Metallic'].default_value=metal
    materials[name]=mat
    return mat


objects=B.build(material)
triangles=sum(sum(len(p.vertices)-2 for p in obj.data.polygons) for obj in objects)
assert triangles<35000
assert len(objects)<=12
assert len(materials)==5
bpy.context.preferences.filepaths.save_version=0
folder=ROOT/'assets/blender/heron-reach'
out=ROOT/'public/models/heron-reach'
bpy.ops.wm.save_as_mainfile(filepath=str(folder/'lived-detail.blend'),compress=True)
bpy.ops.export_scene.gltf(filepath=str(out/'heron-reach-lived.raw.glb'),export_format='GLB',
                          export_image_format='WEBP',export_apply=True,export_yup=True)
compression_command=['npx','--no-install','gltfpack','-i',str(out/'heron-reach-lived.raw.glb'),
                     '-o',str(out/'heron-reach-lived.glb'),'-cc','-kn','-km','-kv','-vtf']
subprocess.run(compression_command,cwd=ROOT,check=True)
packed=out/'heron-reach-lived.glb'
manifest={
    'provenance':'Original ONSITE procedural geometry and original Pillow/numpy printed artwork; no external asset downloads. Fonts and artwork sources recorded in public/materials/heron/lived/manifest.json.',
    'builder':'scripts/maps/art/build_heron_lived_detail.py',
    'builderSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'blender':bpy.app.version_string,
    'units':'metres; authoring x east, y up, z south; glTF world x=mapX-72, y=mapY, z=mapZ-60',
    'layoutSHA256':hashlib.sha256(LAYOUT_PATH.read_bytes()).hexdigest(),
    'collection':'HR_LIVED_DETAIL', 'collision':'None; additions fit existing walls, glazing, open leaf, shelf footprints and ground.',
    'sharedRuntimeMaterials':[BLACK,AGED,GALV,RUBBER],
    'embeddedMaterials':{PRINT:{'texture':'public/materials/heron/lived/shop-lived-color.webp',
        'colourSpace':'sRGB','roughness':.78,'metalness':0,'emissiveStrength':.08,
        'alphaMode':'OPAQUE','doubleSided':False,
        'estimatedRGBA8MipBytes':int(1024*1024*4*4/3)}},
    'textureSHA256':hashlib.sha256((ATLAS_DIR/'shop-lived-color.webp').read_bytes()).hexdigest(),
    'materialBatches':len(objects),'triangles':triangles,'features':features,
    'protectedRoutes':protected,'protectedRoutePolygonCheck':'passed',
    'existingShelfPlacements':SHELVES,
    'rawGLBBytes':(out/'heron-reach-lived.raw.glb').stat().st_size,
    'compressedGLBBytes':packed.stat().st_size,
    'compressedGLBSHA256':hashlib.sha256(packed.read_bytes()).hexdigest(),
    'compression':{'tool':'npm gltfpack','version':json.loads((ROOT/'node_modules/gltfpack/package.json').read_text())['version'],
                   'flags':['-cc','-kn','-km','-kv','-vtf'],
                   'lockfileSHA256':hashlib.sha256((ROOT/'package-lock.json').read_bytes()).hexdigest()},
}
(folder/'lived-detail-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('LIVED_DETAIL',triangles,'triangles;',len(objects),'material batches; route checks passed')
