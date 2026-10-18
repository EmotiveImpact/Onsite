"""Independent coordination checks, including clear-path sampling with wall thickness.
This is an offline 2D design check; never call it a Rapier or 32-player test.
"""
from collections import deque
from pathlib import Path
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/maps/heron-reach-32/blueprints'
B=json.loads((OUT/'build-spec.json').read_text());D=json.loads((OUT.parent/'map.json').read_text())
checks=[];metrics={}
def check(ok,name):
    assert ok,name
    checks.append(name)
def contained(r,outer):
    x,z,w,d=r;a,b,c,e=outer
    return a-1e-7<=x and b-1e-7<=z and x+w<=a+c+1e-7 and z+d<=b+e+1e-7
def overlap(a,b):
    return min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0])>1e-7 and min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1])>1e-7
def distance_to_rect(x,z,r):return math.hypot(max(r[0]-x,0,x-r[0]-r[2]),max(r[1]-z,0,z-r[1]-r[3]))

check(B['sourceSha256']==hashlib.sha256((OUT.parent/'map.json').read_bytes()).hexdigest(),'B01 pins the unchanged source map')
check(len(B['homeInstances'])==24 and len({h['homeId']for h in B['homeInstances']})==16,'16 homes / 24 storeys; no missing upper home')
check(len(B['cores'])==8 and all(c['rect']==next(x['rect']for x in D['cores']if x['id']==c['id'])for c in B['cores']),'Eight core origins preserve the site proposal')

for mid,m in B['modules'].items():
    check(all(contained(r['rect'],[0,0,9,8])for r in m['rooms']),mid+': every room fits within the 9 × 8 envelope')
    check(not any(overlap(a['rect'],b['rect'])for i,a in enumerate(m['rooms'])for b in m['rooms'][i+1:]),mid+': clear room rectangles do not overlap')
    ids=[o['id']for w in m['walls']for o in w['openings']]
    check(len(ids)==len(set(ids)),mid+': unique opening IDs')
    solids=[]
    for w in m['walls']:
        ops=sorted(w['openings'],key=lambda o:o['centre'])
        check(all(w['start']<=o['centre']-o['width']/2 and o['centre']+o['width']/2<=w['end']for o in ops),mid+'/'+w['id']+': openings lie inside their wall')
        check(all(a['centre']+a['width']/2<=b['centre']-b['width']/2 for a,b in zip(ops,ops[1:])),mid+'/'+w['id']+': opening spans do not overlap')
        check(all(o['sill']+o['height']<=2.8 for o in ops),mid+'/'+w['id']+': lintel/head below ceiling')
        # Build a 2D body-height obstacle slice: windows are blocked; doors/arches pass.
        cursor=w['start']
        for o in ops+[dict(centre=w['end'],width=0,kind='arch')]:
            if o['kind']=='window':continue
            lo=o['centre']-o['width']/2
            if lo>cursor:solids.append([cursor,w['at'],lo-cursor,w['thickness']]if w['axis']=='x'else[w['at'],cursor,w['thickness'],lo-cursor])
            cursor=o['centre']+o['width']/2
    # Verify full body-radius route to every room with the planned furniture included.
    obstacles=solids+[r for _,r in m['furniture']]+([m['floorVoid']]if m['floorVoid']else[])
    radius=.35;grid=.1
    valid=set()
    for i in range(91):
        for j in range(81):
            x,z=i*grid,j*grid
            if radius<=x<=9-radius and radius<=z<=8-radius and all(distance_to_rect(x,z,r)>=radius-1e-7 for r in obstacles):valid.add((i,j))
    start=(10,5)if mid=='H1'else(53,75)if mid=='H2-L'else(53,5)
    check(start in valid,mid+': entry has a 0.35 m radius clear position')
    visited={start};q=deque([start])
    while q:
        x,z=q.popleft()
        for n in [(x-1,z),(x+1,z),(x,z-1),(x,z+1)]:
            if n in valid and n not in visited:visited.add(n);q.append(n)
    reachable=[]
    for r in m['rooms']:
        x,z,w,d=r['rect']
        reachable.append(any(x+.35<=i*.1<=x+w-.35 and z+.35<=j*.1<=z+d-.35 for i,j in visited))
    check(all(reachable),mid+': all rooms connect to the entry with 0.70 m body diameter and planned furniture')
    goal=(10,75)if mid=='H1'else(75,67)
    check(goal in visited,mid+': second exit / private stair landing is connected')
    metrics[mid]=dict(sampleSpacing=grid,bodyRadius=radius,validCentres=len(valid),reachableCentres=len(visited),roomsReached=len(reachable))
    # Door swing quadrants: furniture must not intrude into the swept quarter-circle.
    clashes=[]
    for w in m['walls']:
        for o in w['openings']:
            if o['kind']!='door':continue
            lo=o['centre']-o['width']/2;sw=o['swing'];axis=w['axis'];at=w['at']+w['thickness']/2
            for _,r in m['furniture']:
                for i in range(21):
                    for j in range(21):
                        x,z=r[0]+r[2]*i/20,r[1]+r[3]*j/20
                        u,v=(x-lo,(z-at)*sw)if axis=='x'else(z-lo,(x-at)*sw)
                        if u>0 and v>0 and math.hypot(u,v)<o['width']-1e-6:clashes.append(o['id'])
    check(not clashes,mid+': planned furniture clears door swing quadrants')

for id,s in B['stairs'].items():
    check(s['risersPerFlight']*s['rise']*2==s['storey']==3,id+': 20 rises total exactly 3 metres')
    check(s['treadsPerFlight']==s['risersPerFlight']-1 and abs(s['going']*s['treadsPerFlight']-s['flightRun'])<1e-8,id+': nine 280 mm goings; landing is the tenth rise')
    for key in ['halfLanding','floorLanding','floorVoid']:
        check(contained(s[key],[0,0,*s['footprint']]),id+': '+key+' fits allocated envelope')
    check(not overlap(s['floorVoid'],s['floorLanding']),id+': upper slab hole does not remove full landing')
    check(s['floorLanding'][3]>=s['flightWidth']and s['halfLanding'][3]>=s['flightWidth'],id+': both landing depths meet the clear flight width')
    check(3-max(s['slab'],s['stairSlab'])>=B['standards']['minimumStairHeadroom'],id+': repeated-level vertical clearance >= 2.40 m before fixtures')

private=B['stairs']['ST-H'];void=B['modules']['H2-U']['floorVoid']
check(all(abs(a-b)<1e-8 for a,b in zip(void,[private['floorVoid'][0]+6,private['floorVoid'][1]+2,*private['floorVoid'][2:]])),'H2 upper void matches stair-local hole after offset')
for ins in B['homeInstances']:
    base=next(h for h in D['homes']if h['id']==ins['homeId'])
    check(ins['x']==base['x']and ins['z']==base['z']and ins['mirrorZ']==base['flipZ'],ins['id']+': placement and mirror retained')
    if ins['module']=='H2-U':
        transformed=[ins['x']+void[0],ins['z']+(8-void[1]-void[3]if ins['mirrorZ']else void[1]),void[2],void[3]]
        check(contained(transformed,[ins['x'],ins['z'],9,8]),ins['id']+': mirrored floor void stays inside its own home')

rows=list(csv.DictReader((OUT/'home-openings.csv').open()))
check(len(rows)==len(set(r['id']for r in rows)),'World opening schedule contains no duplicate IDs')
check(len(rows)==sum(len(w['openings'])for i in B['homeInstances']for w in B['modules'][i['module']]['walls']),'World opening schedule includes every home opening')
check(all(0<=float(r['x'])<=144 and 0<=float(r['z'])<=120 for r in rows),'Every scheduled home opening is inside the site')
sheets=json.loads((OUT/'sheets.json').read_text())
check(len(sheets)==17 and len({s['id']for s in sheets})==17,'17 unique technical sheets')
for s in sheets:
    root=ET.parse(OUT/(s['file']+'.svg')).getroot()
    check(root.attrib['width']=='841mm'and root.attrib['height']=='594mm'and root.attrib['viewBox']=='0 0 841 594',s['id']+': exact A1 millimetre viewport')
report=dict(scope='Offline design coordination and 2D clear-path sampling; not runtime collision, headroom sweep or multiplayer testing',
            passed=len(checks),checks=checks,roomClearanceSampling=metrics,
            buildSpecSha256=hashlib.sha256((OUT/'build-spec.json').read_bytes()).hexdigest(),sourceMapSha256=B['sourceSha256'],
            unverified=['Real Rapier capsule sweeps and stair traversal','All common-hall/landscape route widths','3D rail, door leaf and furniture final collisions','Bots across floors','Spawn visibility and 32-person balance','Runtime rendering and real-GPU performance'])
(OUT/'coordination-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=len(checks),roomClearanceSampling=metrics),indent=2))
