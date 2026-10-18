"""Render coordinated design sheets from map.json. No game/runtime files are changed."""
from pathlib import Path
import json, html, textwrap

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/maps/heron-reach-32'
D=json.loads((OUT/'map.json').read_text())
W,H=1600,1200
C={'bg':'#10191f','panel':'#18272e','grid':'#293c44','ink':'#eeeade','muted':'#a0b5bc','amber':'#e9af54','cyan':'#62d2da','home':'#534b43','gallery':'#31565e','garden':'#304b3d','shop':'#62523c','service':'#414758','roof':'#514b60','court':'#2e4548','low':'#748c8b','tall':'#b18a57','pink':'#ce9eae'}
X,Y,S=80,220,6.5
def esc(v):return html.escape(str(v),quote=True)
def text(x,y,s,size=16,fill=None,anchor='start',weight=400):return f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{fill or C["ink"]}" text-anchor="{anchor}" font-weight="{weight}">{esc(s)}</text>'
def rect(x,y,w,h,fill,stroke='none',sw=1,rx=0,extra=''):return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
def line(x,y,u,v,stroke,sw=1,dash=''):return f'<path d="M{x:g},{y:g} L{u:g},{v:g}" fill="none" stroke="{stroke}" stroke-width="{sw}" '+(f'stroke-dasharray="{dash}" 'if dash else '')+'/>'
def circle(x,y,r,fill,stroke='none',sw=1,extra=''):return f'<circle cx="{x:g}" cy="{y:g}" r="{r:g}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'
def pxy(x,z):return X+x*S,Y+z*S
def box(r,fill,stroke='none',sw=1,extra=''):
 x,z,w,h=r;return rect(*pxy(x,z),w*S,h*S,fill,stroke,sw,extra=extra)
def mtext(x,z,s,size=13,fill=None,anchor='middle',weight=500):return text(*pxy(x,z),s,size,fill,anchor,weight)
def para(x,y,s,width=51,size=17,colour=None,spacing=26):
 result=''
 for i,t in enumerate(textwrap.wrap(s,width)):result+=text(x,y+i*spacing,t,size,colour)
 return result
def tag(x,y,s,colour=None):return rect(x,y-22,len(s)*8.2+22,30,colour or C['amber'],rx=3)+text(x+11,y,s,13,C['bg'],weight=800)
def base(number,title,subtitle):
 return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(title)}"><defs><pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M0,8L8,0" stroke="#75808a" stroke-width="1" opacity=".3"/></pattern><radialGradient id="lamp"><stop offset="0" stop-color="#ffc675" stop-opacity=".48"/><stop offset="1" stop-color="#ffc675" stop-opacity="0"/></radialGradient></defs><g font-family="Arial,Helvetica,sans-serif">',rect(0,0,W,H,C['bg']),text(64,70,'ONSITE',42,weight=800),text(64,117,'HERON REACH  /  '+title,28,weight=700),text(66,151,subtitle,17,C['muted']),tag(1125,67,'32 PLAYERS · DESIGN 01'),text(1515,115,number,36,C['amber'],'end',700),line(64,177,1536,177,C['grid']),text(64,1150,'PROPOSED DESIGN · METRE SCALE · NOT YET COLLISION-TESTED OR PLAYTESTED',13,C['amber'],weight=700),text(1536,1150,'ONSITE / HERON REACH / REV 01','13',C['muted'],'end')]
def sidebar(parts):
 out=rect(1060,205,475,824,C['panel'],rx=12);y=245
 for title,body in parts:
  out+=text(1084,y,title,19,C['amber'],weight=700);y+=33
  out+=para(1084,y,body,43,16,spacing=24);y+=len(textwrap.wrap(body,43))*24+36
 return out
def grid(ghost=True):
 a=box([0,0,144,120],C['panel'],C['muted'],1.3)
 for n in range(0,145,12):
  x,_=pxy(n,0);a+=line(x,Y,x,Y+120*S,C['grid'],.6);a+=text(x,Y-13,str(n),12,C['muted'],'middle')
 for n in range(0,121,12):
  _,z=pxy(0,n);a+=line(X,z,X+144*S,z,C['grid'],.6);a+=text(X-15,z+4,str(n),12,C['muted'],'end')
 a+=text(X+72*S,Y-38,'144 m',17,C['ink'],'middle')+text(X-14,Y+120*S+27,'0',12,C['muted'])
 a+=text(X+144*S,Y+120*S+27,'120 m N–S',12,C['muted'],'end')
 a+=text(1035,192,'N ↑',16,C['cyan'],'end',700)
 if ghost:
  for b in D['blocks']:a+=box(b['rect'],'#243038','#53616a',1)+box(b['rect'],'url(#hatch)')
 return a
def layer(name,content):return f'<g data-layer="{name}">'+content+'</g>'
def trees():
 a=''
 for p in D['planting']:a+=box(p['rect'],C['garden'])
 for t in D['trees']:
  x,z=pxy(t['x'],t['z']);r=t['canopyRadius']*S
  a+=circle(x,z,r,'#345848','#6e9372',1.2)+line(x-r*.5,z,x+r*.5,z,'#83a58c',.8)+line(x,z-r*.5,x,z+r*.5,'#83a58c',.8)+circle(x,z,2.5,'#aab38d')
 return a
def core(c,level):
 y=next(l['y']for l in D['levels']if l['id']==level)
 if y not in c['levels']:return ''
 x,z,w,h=c['rect'];a=box(c['rect'],'#263b43',C['cyan'],1.5)
 for k in range(10):
  zz=z+.9+k*.4
  for xx in [x+.55,x+3.45]:a+=line(*pxy(xx,zz),*pxy(xx+2,zz),C['muted'],.8)
 a+=mtext(x+3,z+3.4,c['id'],13,C['amber'],weight=800)
 a+=mtext(x+3,z+5.6,('↕'if len(c['levels'])>2 else '↑'),12,C['cyan'])
 return a
def home_inset(h,level):
 y=next(l['y']for l in D['levels']if l['id']==level)
 if y not in h['levels']:return ''
 x,z=h['x'],h['z'];a=box([x,z,9,8],'#6c6255',C['ink'],.7)
 hall=.75 if h['type']=='H1'else 5.25
 a+=box([x+hall-.75,z,1.5,8],'#31565e')
 doors=[z,z+8]if h['type']=='H1'else[(z if h['flipZ']else z+8)if y==3 else(z+8 if h['flipZ']else z)]
 for zz in doors:a+=line(*pxy(x+hall-.55,zz),*pxy(x+hall+.55,zz),C['cyan'],2.2)
 a+=mtext(x+4.5,z+4.8,h['type'],10,C['ink'],weight=700)
 return a
def floors(level,detail=True):
 a=''
 for s in D['surfaces']:
  if s['level']!=level:continue
  a+=box(s['rect'],C[s['kind']],'none'if s['kind']=='service'else C['ink']if s['kind']in['home','shop']else C['cyan'],1)
  x,z,w,h=s['rect']
  if s['kind']=='shop':
   words=s['name'].split();mid=len(words)//2 if len(s['name'])>16 else 0
   if mid:a+=mtext(x+w/2,z+h/2-.7,' '.join(words[:mid]),10)+mtext(x+w/2,z+h/2+1.3,' '.join(words[mid:]),10)
   else:a+=mtext(x+w/2,z+h/2+.6,s['name'],10 if w<10 else 11)
  if s['kind']=='court':
   a+=box([x+1,z+1,w-2,h-2],'none','#a1b6ad',1)+line(*pxy(x+w/2,z+1),*pxy(x+w/2,z+h-1),'#a1b6ad',1)+circle(*pxy(x+w/2,z+h/2),S*3,'none','#a1b6ad',1)
   for xx in [x,x+w]:a+=line(*pxy(xx,z+h/2-2),*pxy(xx,z+h/2+2),C['cyan'],5)
   for zz in [z,z+h]:a+=line(*pxy(x+w/2-2,zz),*pxy(x+w/2+2,zz),C['cyan'],5)
 if level=='B1':
  # Outline the union of service floors: rectangle joins are not interior walls.
  rs=[s['rect']for s in D['surfaces']if s['level']=='B1'];xs=sorted(set(v for r in rs for v in [r[0],r[0]+r[2]]));zs=sorted(set(v for r in rs for v in [r[1],r[1]+r[3]]));cells=set()
  for i in range(len(xs)-1):
   for j in range(len(zs)-1):
    mx,mz=(xs[i]+xs[i+1])/2,(zs[j]+zs[j+1])/2
    if any(r[0]<mx<r[0]+r[2]and r[1]<mz<r[1]+r[3]for r in rs):cells.add((i,j))
  for i,j in cells:
   for neighbor,p,q in [((i-1,j),(xs[i],zs[j]),(xs[i],zs[j+1])),((i+1,j),(xs[i+1],zs[j]),(xs[i+1],zs[j+1])),((i,j-1),(xs[i],zs[j]),(xs[i+1],zs[j])),((i,j+1),(xs[i],zs[j+1]),(xs[i+1],zs[j+1]))]:
    if neighbor not in cells:a+=line(*pxy(*p),*pxy(*q),C['cyan'],1)
 for b in D['blocks']:
  x,z,w,h=b['rect']
  if level in ['G','L1','L2']:
   if level=='G':a+=box(b['arcade'],'#31565e')+box(b['crossArcade'],'#31565e')
   if detail:
    for home in D['homes']:
     if home['id'].startswith(b['id']):a+=home_inset(home,level)
   labelz=z+16 if z<60 else z+3
   a+=mtext(x+18,labelz,b['name'],12,C['ink'],weight=700)
  if level=='R'and b['roofPlayable']:
   a+=box([x+2,z+2,10,5],'#333e49',C['muted'])+box([x+21,z+10,9,5],'#333e49',C['muted'])
   a+=mtext(x+18,z+9,'TWO-EXIT TERRACE',12,weight=700)
 if level=='L1':
  for z in [36,81]:a+=box([60,z,24,3],'#80643f',C['amber'],1.5)
 for c in D['cores']:a+=core(c,level)
 return a
N={n['id']:n for n in D['nodes']}
def edge_points(e):
 a,b=N[e['a']],N[e['b']]
 return [[a['x'],a['z'],a['y']]]+e.get('via',[])+[[b['x'],b['z'],b['y']]]
def routes(level,homes=False):
 y=next(l['y']for l in D['levels']if l['id']==level);a=''
 for e in D['edges']:
  if N[e['a']]['y']!=y or N[e['b']]['y']!=y:continue
  if not homes and e['kind']=='home':continue
  points=edge_points(e);s=' '.join(f'{X+p[0]*S:g},{Y+p[1]*S:g}'for p in points)
  a+=f'<polyline points="{s}" fill="none" stroke="{C["amber"]if e["kind"]=="home"else C["cyan"]}" stroke-width="{1.4 if e["kind"]=="home"else 2}" stroke-dasharray="6 5" stroke-linejoin="round" opacity=".85"/>'
 return a
def covers(level):
 y=next(l['y']for l in D['levels']if l['id']==level);a=''
 for k in D['cover']:
  if k['y']==y:a+=box(k['rect'],C['low']if k['height']<1.5 else C['tall'],C['ink'],.7)
 return a
def objectives():
 a=''
 for o in D['objectives']:
  x,z=pxy(o['x'],o['z']);a+=circle(x,z,o['radius']*S,'none',C['amber'],1.5,extra='stroke-dasharray="4 4"')+circle(x,z,16,C['bg'],C['amber'],2)+text(x,z+6,o['id'],18,C['amber'],'middle',800)
 return a
def spawns(slots=False):
 a=''
 for s in D['spawns']:
  a+=box(s['rect'],'#253d4e',C['cyan'],1.5)
  x,z,w,h=s['rect'];a+=mtext(x+w/2,z+4,s['team'],13,C['cyan'],weight=700)
  if slots:
   for i,p in enumerate(s['positions']):a+=circle(*pxy(p['x'],p['z']),4,'none',C['cyan'],1.3)
  else:a+=mtext(x+w/2,z+h/2,'16',28,C['cyan'],weight=700)
 return a
def legend(items):
 a='';x=80
 for name,col in items:
  a+=rect(x,1061,18,13,col)+text(x+27,1073,name,14,C['muted']);x+=len(name)*8+66
 a+=line(80,1100,236,1100,C['ink'],3)+line(80,1095,80,1105,C['ink'],2)+line(236,1095,236,1105,C['ink'],2)+text(80,1123,'0',12,C['muted'])+text(236,1123,'24 m',12,C['muted'],'end')
 return a
def finish(a,name):
 a.append('</g></svg>');(OUT/(name+'.svg')).write_text(''.join(a));return name

pages=[]
notes={
'G':[('THREE DIFFERENT FIGHTS','A / Garden Court: planting and low walls. B / The Cage: exposed multi-use court. C / Washhouse Square: close shopfront and service routes.'),('WAYS AROUND','Public arcades cut through four blocks. Eight ground flats have two exits. Corner shop, cycle workshop and youth room sit around covered passages.'),('32 INITIAL POSITIONS','16 west + 16 east, each with three exits and offset screens. Dynamic respawn safety still needs runtime implementation and visibility testing.'),('READABLE DEPTH','Primary routes 4 m; public doors 1.5 m. Private halls 1.5 m and doors 1.1 m make homes slower, smaller-team choices.')],
'L1':[('ONE CONNECTED LOOP','3 m wide galleries link all eight public cores. North and south bridges cross the 24 m gaps between blocks.'),('HOMES AS ALTERNATIVES','Eight maisonettes enter here. Private stairs rise to +6 m and leave through rear landings, avoiding the public gallery choke.'),('HEIGHT HAS A COST','Exposed bridge crossings and warm stair exits reveal movement. Privacy screens limit cross-court views; every strong position has another approach.'),('NO INVISIBLE FLOORS','The centre is open to the court below. Only coloured surfaces and stair landings have a proposed walking floor.')],
'L2':[('FOUR RESIDENTIAL ISLANDS','Upper maisonettes and rear landings at +6 m. There is no upper bridge or continuous floor over the central void.'),('TWO PUBLIC EXITS EACH','Each block connects to two public cores. Eight private maisonette stairs give additional routes down to the +3 m gallery.'),('LIMITED OVERLOOKS','Selected windows and screened landings cover short sectors. Rear walls facing spawns remain opaque. Roof access is only in Rowan and Cedar.'),('GROUND OUTLINE IS CONTEXT','Hatched/grey areas show buildings below. They are not walking routes at this height.')],
'R':[('TWO SMALL ROOF AREAS','Only Rowan House (north-west) and Cedar House (south-east) are accessible at +9 m. Two stair exits on each; no ladders or mandatory jumps.'),('NO MAP-WIDE SNIPER PERCH','Plant rooms and 2.1 m screens break roof views. Selected court-facing bays only; opaque parapet screens face the spawn areas.'),('FAIR COUNTER-ROUTES','Roof access costs extra travel. Both stair exits stay contestable. No rooftop capture objective, so the main fight remains downstairs.'),('OTHER ROOFS ARE CLOSED','No traversable roof over Ash or Birch. Do not turn background towers into reachable sniper positions during art dressing.')],
'B1':[('PARTIAL UNDERCROFT','A service loop under the central blocks and court. Four stairs connect it to ground and the gallery system: S2, S3, S6, S7.'),('SLOWER, HIDDEN CHOICE','A dogleg middle cross-link adds options. No dead-end spawn room or one-way drop. Warm exit markers contrast with cool service lighting.'),('SOUND IS THE TRADEOFF','Grilles, concrete and metal doors give clear footsteps. Stealth comes from broken sightlines and timing, not blacked-out character visibility.'),('DESIGN GRAPH ONLY','The linework proves planned connections. Headroom, support columns, wall offsets and actual Rapier traversal must be validated in the blockout.')]
}
for i,level in enumerate(['G','L1','L2','R','B1']):
 spec=next(l for l in D['levels']if l['id']==level)
 a=base(f'{i+1:02}',spec['title'],f'{spec["y"]:+.2f} m  ·  {spec["description"]}')
 a.append(grid());
 if level=='G':a.append(layer('landscape',trees()))
 a.append(floors(level));
 if level=='G':a.append(spawns(True))
 a.append(layer('cover',covers(level)));a.append(layer('routes',routes(level,True)))
 if level=='G':a.append(objectives())
 if level in ['L1','L2','R']:a.append(mtext(72,59,'OPEN TO COURT BELOW',17,C['muted'],weight=700))
 if level=='B1':a.append(mtext(72,48,'SOLID GROUND ABOVE',15,C['muted']))
 a.append(sidebar(notes[level]));a.append(legend([('Homes / enclosed',C['home']),('Gallery / routes',C['cyan']),('Stair / objective',C['amber']),('Scenery only','#243038')]))
 pages.append(finish(a,f'{i+1:02}-{level.lower()}'))

# Overview: cleaner key plan with three strategic bands and exact main dimensions.
a=base('00','32-PLAYER MASTERPLAN','16v16 design target  ·  144 × 120 m estate  ·  five heights  ·  no networking expansion')
a.append(grid());a.append(layer('landscape',trees()));a.append(floors('G',False));a.append(spawns());a.append(layer('cover',covers('G')));a.append(layer('routes',routes('G')));a.append(objectives())
for x,z,label in [(72,9,'A · GARDEN COURT'),(72,41,'B · THE CAGE'),(72,113,'C · WASHHOUSE SQUARE')]:a.append(mtext(x,z,label,14,C['amber'],weight=700))
a.append(sidebar([('A LONDON ESTATE, NOT AN ARENA BOX','Wet stock brick, warm entrances, planted edges and linked concrete galleries. Three places to recognise; multiple paths between them.'),('LAYERED PLAY','-3 m undercroft / 0 m street / +3 m galleries / +6 m maisonettes / +9 m two roofs. Eight stair cores and sixteen enterable homes.'),('SNEAK WITHOUT GETTING LOST','Through flats, private stairs, covered arcades and a service loop reconnect to familiar landmarks. No compulsory crawl tunnels or dead-end routes.'),('BUILDABLE NEXT STEP','One metric definition drives every sheet and the separate Blender massing model. This is a proposal for blockout and 32-player testing, not proof of balance.')]))
a.append(legend([('Homes',C['home']),('Public / flank route',C['cyan']),('Tall cover',C['tall']),('Planting',C['garden']),('Capture area',C['amber'])]))
pages.insert(0,finish(a,'00-masterplan'))

# Domestic layouts: consistent dimensional plans, furniture and actual door openings.
def house_plan(typ,upper,x,y,scale=41):
 h=D['homeTypes'][typ];a='';labels='';rooms=h.get('upperRooms')if upper else h['rooms']
 def r(rx,rz,rw,rh,fill,stroke=C['ink'],sw=1):return rect(x+rx*scale,y+rz*scale,rw*scale,rh*scale,fill,stroke,sw)
 def t(rx,rz,s,size=12):return text(x+rx*scale,y+rz*scale,s,size,C['ink'],'middle',600)
 for name,rx,rz,rw,rh in rooms:
  a+=r(rx,rz,rw,rh,'#31535c'if'HALL'in name else '#393f40')
  words=textwrap.wrap(name,max(7,int(rw*5)))
  lx,lz=rx+rw/2,rz+rh/2+.14
  if typ=='H1'and name=='BEDROOM':lx,lz=6.75,2.65
  if typ=='H1'and name=='KITCHEN':lx,lz=3.35,6.9
  if typ=='H2'and name=='LIVING / DINING':lx,lz=2.7,4.2
  if typ=='H2'and name=='BEDROOM 1':lx,lz=3.05,2.9
  if typ=='H2'and name=='BEDROOM 2':lx,lz=3.05,7.5
  for k,w in enumerate(words):labels+=t(lx,lz+k*.34,w,11)
 a+=r(0,0,9,8,'none',C['ink'],4)
 for dx,dz,ori,width in h['roomDoors']:
  if ori=='v':
   a+=line(x+dx*scale,y+(dz-width/2)*scale,x+dx*scale,y+(dz+width/2)*scale,C['bg'],5)
   a+=line(x+dx*scale,y+(dz-width/2)*scale,x+(dx-.65)*scale,y+(dz-width/2+.65)*scale,C['cyan'],1)
  else:
   a+=line(x+(dx-width/2)*scale,y+dz*scale,x+(dx+width/2)*scale,y+dz*scale,C['bg'],5)
   a+=line(x+(dx-width/2)*scale,y+dz*scale,x+(dx-width/2+.65)*scale,y+(dz-.65)*scale,C['cyan'],1)
 doors=h['doors']if typ=='H1'else[h['doors'][1 if upper else 0]]
 for dx,dz,width in doors:
  a+=line(x+(dx-width/2)*scale,y+dz*scale,x+(dx+width/2)*scale,y+dz*scale,C['cyan'],6)
 for dx,dz,width in h['windows']:
  if dx==9:a+=line(x+dx*scale,y+(dz-width/2)*scale,x+dx*scale,y+(dz+width/2)*scale,C['cyan'],3)
  else:a+=line(x+(dx-width/2)*scale,y+dz*scale,x+(dx+width/2)*scale,y+dz*scale,C['cyan'],3)
 # Furniture footprints deliberately remain outside the clear hall and door swings.
 if typ=='H1':
  a+=r(6.3,.4,1.6,2,'#737e79')+r(6.4,.5,1.4,.4,'#a0aaa1')+r(4.7,.2,1.2,.55,'#62716d')
  a+=r(1.7,4.8,.6,2.6,'#b29c76')+r(1.8,.3,1.7,.75,'#768d8d')+r(4.8,7.1,2.5,.65,'#70858a')+r(6.8,5,1.4,.8,'#8d7e63')
 else:
  if upper:
   for rz in [.3,4.8]:a+=r(.3,rz,1.6,2,'#737e79')+r(.4,rz+.1,1.4,.4,'#a0aaa1')
   a+=r(6.25,.25,1.7,.75,'#768d8d')
  else:a+=r(.2,.2,3.9,.6,'#b29c76')+r(.2,5, .7,2.5,'#70858a')+r(2,5.5,1.4,.8,'#8d7e63')
  for k in range(10):
   for xx in [6.2,7.65]:a+=line(x+xx*scale,y+(3+k*.28)*scale,x+(xx+1.15)*scale,y+(3+k*.28)*scale,C['muted'],.8)
  a+=t(7.5,7.6,'DN'if upper else'UP',12)
 a+=line(x,y-22,x+9*scale,y-22,C['muted'])+text(x+4.5*scale,y-32,'9.00 m',16,C['ink'],'middle')
 a+=text(x-13,y+4*scale,'8 m',13,C['muted'],'end')
 hall=.75 if typ=='H1'else 5.25
 a+=line(x+hall*scale,y+10,x+hall*scale,y+8*scale-10,C['cyan'],2,'6 4')
 return a+labels
a=base('06','HOME DESIGNS','H1: eight through flats  ·  H2: eight two-storey maisonettes  ·  9 × 8 m gross footprint each')
for x,typ,upper,title,subtitle in [(105,'H1',False,'H1 / THROUGH FLAT','GROUND  ±0.00 m'),(610,'H2',False,'H2 / LOWER FLOOR','GALLERY  +3.00 m'),(1115,'H2',True,'H2 / UPPER FLOOR','REAR LANDING  +6.00 m')]:
 a.append(text(x,230,title,21,C['amber'],weight=700)+text(x,262,subtitle,15,C['muted']))
 a.append(house_plan(typ,upper,x,335))
 desc= D['homeTypes'][typ]['description'] if not upper else 'Two bedrooms, bathroom and a separate hall. Exit to the rear landing; bedrooms never need to become the public circulation route.'
 a.append(para(x,720,desc,35,16,spacing=25))
 a.append(text(x,850,'72 m² gross'+(' per storey / 144 m² total'if typ=='H2'else' / one bedroom'),15,C['cyan'],weight=700))
a.append(rect(65,915,1470,170,C['panel'],rx=12))
a.append(text(90,952,'ROOMS THAT CAN BE LIVED IN — AND READ IN PLAY',20,C['amber'],weight=700))
a.append(para(90,988,'Kitchen, bath, storage, bed and living space are dimensioned. Keep halls clear: 1.5 m; home doors 1.1 m. Public doors are 1.5 m. Furniture footprints are planning allowances, not final props.',98,17,spacing=27))
a.append(text(90,1060,'Private stair: 1.2 m flights · 20 × 0.15 m risers · 0.28 m going · 1.2 m landings. Test headroom and carry the opening through both floors.',15,C['muted']))
pages.append(finish(a,'06-homes'))

a=base('07','LANDSCAPE + LIGHTING','A coordinated dressing layer  ·  blue-hour sky / warm entrances / rain-darkened materials')
a.append(grid());a.append(floors('G',False));a.append(layer('landscape',trees()));a.append(layer('cover',covers('G')))
wet=''
for p in D['wetAreas']:wet+=box(p['rect'],'#547d87','#97bbc2',.8)
a.append(layer('wet',wet));lamps=''
for l in D['lights']:
 x,z=pxy(l['x'],l['z']);lamps+=circle(x,z,l['radius']*S,'url(#lamp)')+circle(x,z,3.5,C['amber'])
a.append(layer('lighting',lamps));a.append(layer('routes',routes('G')))
a.append(sidebar([('COOL AIR / WARM THRESHOLDS','Blue-hour ambient light with 2700 K doors and shopfronts, 3000 K court lights. Stair faces stay readable. Light circles show intent, not measured lux or runtime light counts.'),('PLANTING HAS STRUCTURE','20 tree positions: trunks collide, canopies start at 2.7 m. Ten grass/soil zones; shrubs below 0.7 m by main routes. Leaves provide visual texture, not dependable ballistic cover.'),('DIRT BELONGS SOMEWHERE','Litter at shopfronts and bin bays; moss at shaded slab joints; soil under planting; puddles at drains and low edges. Keep steps, doorway swings and cover gaps clear.'),('SIX BASE MATERIAL FAMILIES','Stock brick, board concrete, asphalt, paving, painted steel and soil/grass. Share PBR sets; use local grime/wetness masks, instancing and LODs.')]))
a.append(legend([('Planting / trees',C['garden']),('Wet edges','#547d87'),('Warm light intent',C['amber']),('Routes kept clear',C['cyan'])]))
pages.append(finish(a,'07-landscape-lighting'))

# Actual map-coordinate sections; schematic heights have a separate vertical scale.
a=base('08','LEVELS + SECTIONS','Sections through the metric design  ·  height is exaggerated for readability; dimensions remain explicit')
a.append(text(80,225,'A—A  /  NORTH–SOUTH AT x = 72 m',20,C['amber'],weight=700))
sx,sy,hs,vs=100,470,10,20
for y in [-3,0,3,6,9]:a.append(line(sx,sy-y*vs,1500,sy-y*vs,C['grid'],1,'4 4')+text(75,sy-y*vs+5,f'{y:+} m',14,C['muted'],'end'))
a.append(rect(sx,sy,120*hs,10,C['home']))
for s in D['surfaces']:
 x,z,w,h=s['rect']
 if s['level']=='B1'and x<72<x+w:a.append(rect(sx+z*hs,sy+3*vs,h*hs,8,C['service']))
for z in [36,81]:a.append(rect(sx+z*hs,sy-3*vs,3*hs,7,C['amber']))
for z,label in [(24,'GARDEN'),(60,'CAGE'),(96,'WASHHOUSE')]:a.append(text(sx+z*hs,sy+45,label,15,C['ink'],'middle',700))
a.append(text(sx+55*hs,sy+110,'PARTIAL SERVICE ROUTES AT −3 m',15,C['muted']))
a.append(text(80,660,'B—B  /  EAST–WEST AT z = 24 m',20,C['amber'],weight=700))
sx,sy,hs,vs=100,930,9,20
for y in [-3,0,3,6,9]:a.append(line(sx,sy-y*vs,1500,sy-y*vs,C['grid'],1,'4 4')+text(75,sy-y*vs+5,f'{y:+} m',14,C['muted'],'end'))
for x in [24,84]:
 for y in [0,3,6]:a.append(rect(sx+x*hs,sy-y*vs,36*hs,6,C['home'],C['ink'],.7))
 a.append(line(sx+x*hs,sy,sx+x*hs,sy-9*vs,C['ink'],3)+line(sx+(x+36)*hs,sy,sx+(x+36)*hs,sy-9*vs,C['ink'],3))
 a.append(rect(sx+x*hs,sy-9*vs,36*hs,6,C['roof']if x==24 else '#27353b',C['ink'],.8))
 for xx in [x+2,x+25]:
  a.append(rect(sx+xx*hs,sy-3*vs,9*hs,3*vs,'#6c6255',C['muted'],.5))
  a.append(rect(sx+xx*hs,sy-9*vs,9*hs,6*vs,'#4c5552',C['muted'],.5))
 for yy in [0,3]:a.append(line(sx+x*hs,sy-yy*vs,sx+(x+36)*hs,sy-yy*vs,C['ink'],3))
 for lo,hi in [(x,x+8),(x+11,x+31),(x+34,x+36)]:a.append(line(sx+lo*hs,sy-6*vs,sx+hi*hs,sy-6*vs,C['ink'],3))
 a.append(text(sx+(x+18)*hs,sy+42,'ROWAN HOUSE'if x==24 else'ASH HOUSE',16,C['ink'],'middle',700))
a.append(text(sx+72*hs,sy-10,'GARDEN / OPEN SKY',14,C['cyan'],'middle'))
a.append(text(sx+42*hs,sy-9*vs-20,'ROOF OPEN / 2 EXITS',14,C['amber'],'middle'))
a.append(text(sx+102*hs,sy-9*vs-20,'ROOF CLOSED',14,C['muted'],'middle'))
a.append(para(80,1040,'Public cores: 6 × 6 m · 1.5 m flights and landings · 20 risers per 3 m storey · 0.15 m rise / 0.28 m going. Target clear headroom 2.4 m; slab and stair openings must be tested in the runtime blockout.',140,17,spacing=25))
pages.append(finish(a,'08-sections'))

# An interactive, dependency-free review book; print exports every sheet, not just the selection.
buttons=''.join(f'<button data-page="{i}" aria-pressed="{str(i==0).lower()}">{name[3:].replace("-"," ").upper()}</button>'for i,name in enumerate(pages))
sheets=''.join(f'<article data-page="{i}" '+('class="active"'if i==0 else'')+'>'+ (OUT/(name+'.svg')).read_text()+'</article>'for i,name in enumerate(pages))
viewer='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ONSITE — Heron Reach map design</title><style>
*{box-sizing:border-box}body{margin:0;background:#10191f;color:#eeeade;font:15px Arial,sans-serif}header{padding:20px 24px;border-bottom:1px solid #3c5057}h1{margin:0 0 8px;letter-spacing:2px;font-size:24px}p{margin:8px 0;color:#a0b5bc}nav,.layers{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}button{padding:10px 14px;border:1px solid #56717c;background:#18272e;color:#eeeade;border-radius:4px;cursor:pointer}button[aria-pressed=true]{background:#e9af54;color:#10191f;border-color:#e9af54}button:focus-visible,input:focus-visible{outline:3px solid #62d2da;outline-offset:3px}.layers label{padding:8px;cursor:pointer}article{display:none}article.active{display:block}article svg{width:100%;height:auto;display:block}a{color:#62d2da}.foot{padding:16px 24px}.off{display:none}@page{size:400mm 300mm;margin:0}@media print{header,.foot{display:none}article{display:block!important;break-after:page;height:300mm}article:last-child{break-after:auto}article svg{width:400mm;height:300mm}.off{display:initial}}
</style><header><h1>ONSITE / HERON REACH</h1><p>32-player design target · 16v16 · proposed map, not a playtested or network-enabled build</p><nav>'''+buttons+'''</nav><div class="layers">'''+''.join(f'<label><input type="checkbox" data-layer="{l}" checked> {label}</label>'for l,label in [('routes','Routes'),('cover','Cover'),('landscape','Planting'),('lighting','Light intent'),('wet','Wet ground')])+'''<button id="print">Print all sheets / PDF</button></div></header><main>'''+sheets+'''</main><div class="foot"><a href="README.md">Design and Claude implementation notes</a> · <a href="map.json">Metric definition</a> · <a href="validation.json">Connectivity report</a></div><script>
for(const b of document.querySelectorAll('button[data-page]')) b.addEventListener('click',()=>{for(const t of document.querySelectorAll('button[data-page]'))t.setAttribute('aria-pressed',String(t===b));for(const p of document.querySelectorAll('article'))p.classList.toggle('active',p.dataset.page===b.dataset.page);});
for(const c of document.querySelectorAll('input[data-layer]')) c.addEventListener('change',()=>{for(const g of document.querySelectorAll('g[data-layer="'+c.dataset.layer+'"]'))g.classList.toggle('off',!c.checked)});
document.querySelector('#print').addEventListener('click',()=>window.print());
</script></html>'''
(OUT/'index.html').write_text(viewer)
(OUT/'sheets.json').write_text(json.dumps(pages,indent=2)+'\n')
print('Rendered',len(pages),'coordinated sheets and standalone review book.')
