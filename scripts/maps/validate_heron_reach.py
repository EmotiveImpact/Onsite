"""Design coordination checks. These are not game collision or 32-client tests."""
from pathlib import Path
import json, math, heapq, hashlib

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/maps/heron-reach-32'
d=json.loads((OUT/'map.json').read_text());nodes={n['id']:n for n in d['nodes']};checks=[]
def check(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
check(len(nodes)==len(d['nodes']),'Every design node has a unique ID')
def points(e):
 a,b=nodes[e['a']],nodes[e['b']]
 return [[a['x'],a['z'],a['y']]]+e.get('via',[])+[[b['x'],b['z'],b['y']]]
def length(e):return sum(math.dist(a,b)for a,b in zip(points(e),points(e)[1:]))
def graph(exclude_core=None):
 g={k:[]for k in nodes}
 for e in d['edges']:
  if exclude_core and e['kind']=='stairs'and e['a'].startswith(exclude_core+'@'):continue
  v=length(e);g[e['a']].append((e['b'],v));g[e['b']].append((e['a'],v))
 return g
def distances(g,source):
 dist={source:0};queue=[(0,source)];prev={}
 while queue:
  v,k=heapq.heappop(queue)
  if v>dist[k]:continue
  for q,w in g[k]:
   if v+w<dist.get(q,math.inf):dist[q]=v+w;prev[q]=k;heapq.heappush(queue,(v+w,q))
 return dist,prev
g=graph();dist,_=distances(g,'Wspawn')
check(len(dist)==len(nodes),'All proposed floors, homes and objectives are connected')
for c in d['cores']:
 reach,_=distances(graph(c['id']),'Wspawn')
 check(len(reach)==len(nodes),f'Blocking stair flights in {c["id"]} does not isolate a floor or home')
check(all(len(g[o])>=4 for o in ['A','B','C']),'Each capture area has at least four design-graph approaches')
check(len(d['spawns'])==2 and all(len(s['positions'])==16 for s in d['spawns']),'32 initial placements: 16 per side')
pos=[(p['x'],p['z'])for s in d['spawns']for p in s['positions']]
check(min(math.dist(a,b)for i,a in enumerate(pos)for b in pos[i+1:])>=2,'Initial actor centres are separated by at least 2 m')
check(all(len(g[s+'spawn'])>=3 for s in ['W','E']),'Each staging area has three independent initial route branches')
check(all(0<=n['x']<=144 and 0<=n['z']<=120 for n in nodes.values()),'All route nodes fit the declared 144 × 120 m bounds')
for c in d['cores']:
 check(c['risers']*c['rise']==3 and c['risers']//2*c['going']+2*c['landing']<=c['rect'][3],f'{c["id"]}: 3 m rise and folded flight/landing dimensions fit 6 m depth')
for h in d['homes']:
 b=next(b for b in d['blocks']if b['id']==h['id'].split('-')[0]);x,z,w,t=b['rect']
 check(x<=h['x'] and z<=h['z'] and h['x']+9<=x+w and h['z']+8<=z+t,f'{h["id"]} fits its residential block')
def inside(p,r):return r[0]-.01<=p[0]<=r[0]+r[2]+.01 and r[1]-.01<=p[1]<=r[1]+r[3]+.01
# Independently sample every above/below-ground horizontal route against declared floor areas.
byheight={l['y']:l['id']for l in d['levels']};samples=0;bad=[]
for e in d['edges']:
 a,b=nodes[e['a']],nodes[e['b']]
 if a['y']!=b['y']or a['y']==0:continue
 y=a['y'];areas=[s['rect']for s in d['surfaces']if s['level']==byheight[y]]+[c['rect']for c in d['cores']if y in c['levels']]
 for u,v in zip(points(e),points(e)[1:]):
  count=max(1,math.ceil(math.dist(u,v)/.25))
  for i in range(count+1):
   p=[u[k]+(v[k]-u[k])*i/count for k in range(3)];samples+=1
   if not any(inside(p,r)for r in areas):bad.append({'edge':[e['a'],e['b']],'point':p})
check(not bad,f'{samples} sampled upper/service-route points have a declared floor; failures: {bad[:3]}')
void_crossings=[]
for e in d['edges']:
 a,b=nodes[e['a']],nodes[e['b']]
 if a['y']!=b['y']or a['y']<=0:continue
 for u,v in zip(points(e),points(e)[1:]):
  count=max(1,math.ceil(math.dist(u,v)/.25))
  for i in range(count+1):
   x,z,y=[u[k]+(v[k]-u[k])*i/count for k in range(3)]
   for c in d['cores']:
    cx,cz,w,h=c['rect']
    if cx+.01<x<cx+w-.01 and cz+.01<z<cz+h-.01:
     landing=(z>=cz+4.5-.01)if cz<60 else(z<=cz+1.5+.01)
     if not landing:void_crossings.append([e['a'],e['b'],c['id']])
check(not void_crossings,f'Upper horizontal routes avoid public stair flight/half-landing voids; failures: {void_crossings[:3]}')
blocked=[];treeblocked=[]
for e in d['edges']:
 a,b=nodes[e['a']],nodes[e['b']]
 if a['y']!=b['y']:continue
 for u,v in zip(points(e),points(e)[1:]):
  count=max(1,math.ceil(math.dist(u,v)/.25))
  for i in range(count+1):
   x,z,y=[u[k]+(v[k]-u[k])*i/count for k in range(3)]
   for c in d['cover']:
    cx,cz,w,h=c['rect']
    if c['y']==y and cx-.35<x<cx+w+.35 and cz-.35<z<cz+h+.35:blocked.append([e['a'],e['b'],c['id']])
   if y==0:
    for t in d['trees']:
     if math.hypot(x-t['x'],z-t['z'])<t['trunkRadius']+.35:treeblocked.append([e['a'],e['b'],t['id']])
check(not blocked,f'Route centrelines retain 0.35 m clearance from planned hard cover; failures: {blocked[:3]}')
check(not treeblocked,f'Ground route centrelines clear planned trunks by a 0.35 m capsule radius; failures: {treeblocked[:3]}')
metrics={}
for side in ['W','E']:
 ds,prev=distances(g,side+'spawn');metrics[side]={}
 for o in ['A','B','C']:
  path=[o]
  while path[-1]!=side+'spawn':path.append(prev[path[-1]])
  metrics[side][o]={'metres':round(ds[o],2),'walkSeconds':round(ds[o]/4.6,2),'sprintSeconds':round(ds[o]/6.8,2),'path':path[::-1]}
maxdiff=max(abs(metrics['W'][o]['metres']-metrics['E'][o]['metres'])for o in ['A','B','C'])
check(maxdiff<8,'Side-to-objective shortest-path difference stays below 8 m in the design graph')
check(sum(b['roofPlayable']for b in d['blocks'])==2,'Only two roof islands are designated accessible')
check(len([h for h in d['homes']if h['type']=='H1'])==8 and len([h for h in d['homes']if h['type']=='H2'])==8,'Eight through flats and eight split-level homes are placed')
report={'scope':d['validationBoundary'],'passed':len(checks),'checks':checks,'nodes':len(nodes),'edges':len(d['edges']),'cycleRank':len(d['edges'])-len(nodes)+1,'floorSamples':samples,'spawnToObjective':metrics,'largestSideDifferenceMetres':round(maxdiff,2),'sourceSha256':hashlib.sha256((OUT/'map.json').read_bytes()).hexdigest(),'unverified':['Actual capsule collision / stair headroom','Dynamic respawn line of sight','32 simultaneous humans or clients','Real-GPU frame time / streaming / memory','Sound propagation / stealth readability','Combat balance / objective contest time','All physical route widths around final props']}
(OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':len(checks),'nodes':len(nodes),'edges':len(d['edges']),'floorSamples':samples,'travel':metrics,'maxSideDifference':maxdiff},indent=2))
