"""Resolve the Heron Reach proposal into a B01 modelling contract.

Placements stay in map.json. This additive issue supplies local geometry; it does
not modify that proposal, the earlier massing model, or the playable level.
"""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / 'docs/maps/heron-reach-32/map.json'
OUT = MAP.parent / 'blueprints'
OUT.mkdir(exist_ok=True)
D = json.loads(MAP.read_text())


def opening(id, centre, width, kind='door', sill=0, height=2.2, swing=1):
    return dict(id=id, centre=centre, width=width, kind=kind, sill=sill,
                height=height, swing=swing)


def wall(id, axis, at, start, end, thickness, openings=()):
    # Axis x: runs in x at fixed z; axis z: runs in z at fixed x.
    return dict(id=id, axis=axis, at=at, start=start, end=end,
                thickness=thickness, height=2.8, openings=list(openings))


def shell(typ, upper=False):
    doors_n = [opening('D01', .95, 1.1)] if typ == 'H1' else ([opening('D01', 5.25, 1.1)] if upper else [])
    doors_s = [opening('D02', .95, 1.1, swing=-1)] if typ == 'H1' else ([] if upper else [opening('D01', 5.25, 1.1, swing=-1)])
    wx, ww = (7.5, 1.5) if typ == 'H1' else (2.25, 2)
    return [wall('N', 'x', 0, 0, 9, .2, doors_n + [opening('W01', wx, ww, 'window', .9, 1.35)]),
            wall('S', 'x', 7.8, 0, 9, .2, doors_s + [opening('W02', wx, ww, 'window', .9, 1.35)]),
            wall('W', 'z', 0, .2, 7.8, .2), wall('E', 'z', 8.8, .2, 7.8, .2)]


def room(id, label, rect):
    return dict(id=id, label=label, rect=rect, clearArea=round(rect[2]*rect[3], 3))


H1 = dict(id='H1', name='One-bedroom through flat', footprint=[9, 8], levels=[0],
          floorVoid=None, grossArea=72, walls=shell('H1') + [
              wall('P1', 'z', 1.7, .2, 7.8, .12, [opening('A01', 3.9, 1.2, 'arch')]),
              wall('P2', 'x', 3.03, 1.82, 8.8, .12, [opening('D03', 3, .9, swing=-1), opening('D04', 6.5, .9, swing=-1)]),
              wall('P3', 'x', 4.65, 1.82, 8.8, .12, [opening('D05', 3, 1), opening('D06', 6.5, 1.1)]),
              wall('P4', 'z', 4.38, .2, 3.03, .12),
              wall('P5', 'z', 4.38, 4.77, 7.8, .12, [opening('A02', 6, 1.5, 'arch')])],
          rooms=[room('01', 'THROUGH HALL', [.2, .2, 1.5, 7.6]),
                 room('02', 'BATH / UTILITY', [1.82, .2, 2.56, 2.83]),
                 room('03', 'BEDROOM', [4.5, .2, 4.3, 2.83]),
                 room('04', 'CROSS HALL', [1.82, 3.15, 6.98, 1.5]),
                 room('05', 'KITCHEN', [1.82, 4.77, 2.56, 3.03]),
                 room('06', 'LIVING / DINING', [4.5, 4.77, 4.3, 3.03])],
          furniture=[['bed', [6.8, .4, 1.6, 2]], ['bath', [1.95, .35, 1.7, .75]],
                     ['counter', [1.95, 5.9, .6, 1.5]], ['sofa', [5, 7, 2.4, .7]],
                     ['table', [7, 5.2, 1.1, .7]]])


def h2(upper):
    module = dict(id='H2-U' if upper else 'H2-L', name='Maisonette upper' if upper else 'Maisonette lower',
                  footprint=[9, 8], levels=[6 if upper else 3], grossArea=72,
                  floorVoid=[6.12, 2.08, 2.68, 3.84] if upper else None,
                  walls=shell('H2', upper) + [
                      wall('P1', 'z', 4.38, .2, 7.8, .12, [opening('D02', 1.5, .9, swing=-1), opening('D03', 5, .9 if upper else 1.1, swing=-1)]),
                      wall('P2', 'z', 6, .2, 7.8, .12, [opening('D04', 1.1, .8), opening('A01', 6.5, 1.1, 'arch')]),
                      wall('P3', 'x', 3.38 if upper else 2.88, .2, 4.38, .12),
                      wall('P4', 'x', 1.88, 6.12, 8.8, .12)],
                  rooms=[room('01', 'CLEAR HALL', [4.5, .2, 1.5, 7.6]),
                         room('02', 'BEDROOM 1' if upper else 'KITCHEN', [.2, .2, 4.18, 3.18 if upper else 2.68]),
                         room('03', 'BEDROOM 2' if upper else 'LIVING / DINING', [.2, 3.5 if upper else 3, 4.18, 4.3 if upper else 4.8]),
                         room('04', 'BATH' if upper else 'WC / STORE', [6.12, .2, 2.68, 1.68]),
                         room('05', 'STAIR / LANDING', [6.12, 2, 2.68, 5.8])],
                  furniture=([['bed', [.4, .4, 1.6, 2]], ['bed', [.4, 5.3, 1.6, 2]], ['bath', [7.95, .25, .75, 1.5]]] if upper else
                             [['counter', [.3, .3, 3.6, .6]], ['sofa', [.3, 4.5, .8, 2.4]], ['table', [2.2, 6, 1.5, .8]]]))
    return module


# Ten risers have NINE independent treads. The tenth rise terminates on a landing.
# The older massing counted ten tread boxes: this issue defines the exact nosings.
stairs = {
    'ST-P': dict(id='ST-P', footprint=[6, 6], flightWidth=1.5, rise=.15,
                 risersPerFlight=10, treadsPerFlight=9, going=.28, storey=3,
                 firstFlightX=.4, secondFlightX=4.1, flightZ=1.7, flightRun=2.52,
                 halfLanding=[.4, .2, 5.2, 1.5], floorLanding=[.2, 4.22, 5.6, 1.58],
                 floorVoid=[.2, .2, 5.6, 4.02], slab=.2, stairSlab=.15,
                 entry=[3, 6], entryWidth=1.5, outerWall=.2,
                 note='North cores enter from local south. South cores mirror local z across 6 m.'),
    'ST-H': dict(id='ST-H', footprint=[3, 6], localOriginInHome=[6, 2], flightWidth=1.2,
                 rise=.15, risersPerFlight=10, treadsPerFlight=9, going=.28, storey=3,
                 firstFlightX=.18, secondFlightX=1.53, flightZ=1.4, flightRun=2.52,
                 halfLanding=[.18, .2, 2.55, 1.2], floorLanding=[.12, 3.92, 2.68, 1.88],
                 floorVoid=[.12, .08, 2.68, 3.84], slab=.2, stairSlab=.15,
                 entry=[0, 4.5], entryWidth=1.1, outerWall=.12,
                 note='H2 local x/z. Mirror the complete home, void AND stairs in southern blocks.')
}

modules = {'H1': H1, 'H2-L': h2(False), 'H2-U': h2(True)}
instances = []
for h in D['homes']:
    for y in h['levels']:
        instances.append(dict(id=h['id'] + ('-L' if y == 3 else '-U' if y == 6 else ''),
                              homeId=h['id'], module='H1' if y == 0 else 'H2-L' if y == 3 else 'H2-U',
                              x=h['x'], z=h['z'], y=y, mirrorZ=h['flipZ']))

circulation = []
reserves = []
for b in D['blocks']:
    x,z,_,_=b['rect']
    for level in ['G', 'L1', 'L2']:
        # These rectangles resolve the old undifferentiated whole-block slabs.
        for name,r in [('rear',[0,0,36,3]), ('common',[11,3,14,8]), ('front',[0,11,36,7])]:
            rx,rz,w,d=r
            if z > 60: rz=18-rz-d
            circulation.append(dict(id=f'{b["id"]}-{level}-{name}', level=level, rect=[x+rx,z+rz,w,d]))
        for i,r in enumerate([[0,3,2,8],[34,3,2,8]]):
            rx,rz,w,d=r
            if z>60:rz=18-rz-d
            reserves.append(dict(id=f'{b["id"]}-{level}-reserve-{i+1}',level=level,rect=[x+rx,z+rz,w,d],height=2.8))

shops=[]
for s in D['surfaces']:
    if s['kind']!='shop':continue
    x,z,w,d=s['rect'];side=w<d
    # Small square shops have a side arcade door toward C; all also have N/S exits.
    openings=[dict(id='D01',side='N',offset=w/2,width=2,height=2.4),
              dict(id='D02',side='S',offset=w/2,width=1.5,height=2.4)]
    if side:openings.append(dict(id='D03',side='E' if x<72 else 'W',offset=d/2,width=1.5,height=2.4))
    shops.append(dict(id=s['id'],name=s['name'],rect=s['rect'],wall=.2,height=3,
                      doorOpenings=openings,glazing=dict(side='N',sill=.6,height=1.6,
                      spans=[[.6,w/2-1.5],[w/2+1.5,w-.6]]),
                      furnishing='Keep a 2.4 m continuous path between exits; perimeter fixtures only.'))

spec = dict(schema=1, issue='B01', date='2026-10-18', project='ONSITE / HERON REACH',
    status='DIMENSIONED GAME-ENVIRONMENT DESIGN / FOR BLENDER BLOCKOUT',
    sourceMap='../map.json', sourceSha256=hashlib.sha256(MAP.read_bytes()).hexdigest(),
    sourceCommit='4ddf69b2bfe2ee480f0d610fcf0ea857832724a2', units='metres',
    paper=dict(size='A1 landscape',mm=[841,594],print='100%; do not fit to page'),
    coordinates=dict(map='x east; z south; y up; NW site corner = (0,0,0)',
                     blender='(X,Y,Z) = (x-72, 60-z, y)',
                     glb='(X,Y,Z) = (x-72, y, z-60)',
                     homeMirror='world z = instance z + 8 - local z; apply to every vertex and portal',
                     normals='Bake mirroring into coordinates and recalculate normals; no negative object scale'),
    standards=dict(externalWall=.2,partition=.12,slab=.2,storey=3,clearCeiling=2.8,
                   doorHead=2.2,publicDoorHead=2.4,windowSill=.9,windowHead=2.25,
                   guard=1.2,handrail=1.0,clearHall=1.5,thresholdMax=.02,
                   minimumStairHeadroom=2.4,clearGallery=3),
    precedence=['map.json: site footprint, block/home/core placements, floors, route intent and landscape positions',
                'build-spec.json B01: wall faces, clear openings, stairs, slab voids and home internals',
                'B01 SVG/PDF: drawings of this contract; dimensions govern over image measurement',
                'Rev 01 massing remains reference; its placeholder partitions/windows/rails are not build instructions'],
    changes=[
        'Resolved 200 mm shells, 120 mm partitions and 200 mm slabs; room dimensions are now clear face-to-face.',
        'H1 door centres shift from local x=0.75 to x=0.95 for jamb room; old graph endpoints still fall within the opening.',
        'H1 clear hall is 1.50 m after wall thickness; side window omitted where it would face reserved solid frontage.',
        'H2 only has a +3 front door and +6 rear door, with a 1.10 m opening into the stair landing on both floors.',
        'Stairs use 10 risers / 9 goings per flight: 2.52 m run, not the old 10 tread-box massing.',
        'H2 upper void stops at the top landing. Southern home stairs, voids and portals must all mirror together.',
        'Public core interior slabs are cut at every served level; topmost core has a roof at FFL+2.8 and no stair above it.',
        'Common floors and reserved solid strips are identified inside the former broad block floor plates.',
        'Shop portals and side doors to Washhouse Square are explicit; no inferred holes from decorative windows.'
    ], modules=modules, stairs=stairs, homeInstances=instances,
    cores=[dict(**c,mirrorZ=c['rect'][1]>60,module='ST-P') for c in D['cores']],
    circulation=circulation,reserves=reserves,shops=shops,
    surfaceRules=dict(ground='G is continuous site slab except core holes leading to B1. B1 is enclosed below it.',
                      gallery='Union overlapping rectangles before meshing; subtract served core footprint, then add its explicit landing.',
                      homes='Do not stack home slabs on the same block slab. Subtract H2-U voids from the union once.',
                      guards='1.2 m guards on every exposed walkable edge; omit only scheduled door/core/bridge joins.',
                      topCore='Core enclosure and cap continue 2.8 m above highest served FFL; highest cap never walkable.',
                      railWidth='Measure gallery and flight width BETWEEN guard/rail faces. Place posts outside clear walk polygon.'),
    buildOrder=['setting-out and datums','ground + one block shell','ST-P core + slab openings','gallery + rear landings',
                'H1 and H2 modules + mirrored placements','undercroft + roof limits','shops + court',
                'single Rapier collision / floor-aware nav verification','PBR modules + lighting rebuild in Three.js','landscape and dressing'],
    limits=['This package is not an as-built playable, final art or a real-world construction document.',
            'No room-level collision/navigation or 32-actor gameplay has been verified.',
            'Doors are held open in the first blockout; no working-door state/networking is specified.',
            'Window glazing is closed and non-traversable; sightline/bullet behaviour must be explicit in gameplay.',
            'Roofs need spawn sightline tests; lighting ranges are art intentions, not measured lux.'])
(OUT/'build-spec.json').write_text(json.dumps(spec,indent=2)+'\n')

# Coordinates of every home opening for Blender empties and later portal checks.
rows=[]
for ins in instances:
    for w in modules[ins['module']]['walls']:
        for op in w['openings']:
            x,z=(op['centre'],w['at']+w['thickness']/2) if w['axis']=='x' else (w['at']+w['thickness']/2,op['centre'])
            if ins['mirrorZ']:z=8-z
            rows.append(dict(id=ins['id']+'-'+op['id'],instance=ins['id'],kind=op['kind'],wall=w['id'],
                             x=round(ins['x']+x,4),z=round(ins['z']+z,4),y=ins['y']+op['sill'],
                             width=op['width'],height=op['height'],runsAlong=w['axis']))
with (OUT/'home-openings.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
for filename, rows in [('home-instances',instances),('core-instances',spec['cores']),('tree-placements',D['trees']),
                        ('light-placements',D['lights']),('cover-placements',D['cover'])]:
    with (OUT/(filename+'.csv')).open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
print(f'B01 contract: {len(instances)} home storeys, {len(spec["cores"])} cores, {len(rows)} cover placements.')
