"""A1 vector construction drawings for the game environment, from the B01 contract."""
from pathlib import Path
import html
import json
import math
import textwrap

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/maps/heron-reach-32/blueprints'
D=json.loads((OUT.parent/'map.json').read_text())
B=json.loads((OUT/'build-spec.json').read_text())
INK='#18344e'; BLUE='#225b88'; CYAN='#008b9b'; LIGHT='#e6eff5'; GREY='#718392'; PALE='#f5f8fa'; AMBER='#b87822'; GREEN='#477257'
PAGES=[]


def esc(s):return html.escape(str(s),quote=True)
def text(x,y,s,size=3.1,colour=INK,anchor='start',bold=False):
    return f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" fill="{colour}" text-anchor="{anchor}" font-weight="{700 if bold else 400}">{esc(s)}</text>'
def rect(x,y,w,h,fill='none',stroke=INK,sw=.3):
    if w<=0 or h<=0:return ''
    return f'<rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def line(x,y,a,b,c=INK,sw=.25,dash=''):
    return f'<path d="M{x:.3f} {y:.3f}L{a:.3f} {b:.3f}" fill="none" stroke="{c}" stroke-width="{sw}" stroke-dasharray="{dash}"/>'
def circle(x,y,r,fill='none',stroke=INK,sw=.25):return f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{r:.3f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
def poly(pts,c=INK,sw=.3,dash=''):
    return ''.join(line(*a,*b,c,sw,dash) for a,b in zip(pts,pts[1:]))
def paragraph(x,y,s,width=75,size=3.1,leading=5):
    return ''.join(text(x,y+i*leading,t,size)for i,t in enumerate(textwrap.wrap(s,width)))
def dimh(x1,x2,base,y,label):
    a=line(x1,base,x1,y-2,GREY,.18)+line(x2,base,x2,y-2,GREY,.18)+line(x1,y,x2,y,BLUE,.2)
    for x in [x1,x2]:a+=line(x-1,y+1,x+1,y-1,BLUE,.35)
    return a+text((x1+x2)/2,y-1.5,label,2.8,BLUE,'middle')
def dimv(y1,y2,base,x,label):
    a=line(base,y1,x+2,y1,GREY,.18)+line(base,y2,x+2,y2,GREY,.18)+line(x,y1,x,y2,BLUE,.2)
    for y in [y1,y2]:a+=line(x-1,y+1,x+1,y-1,BLUE,.35)
    return a+f'<text x="{x-2}" y="{(y1+y2)/2}" font-size="2.8" fill="{BLUE}" text-anchor="middle" transform="rotate(-90 {x-2} {(y1+y2)/2})">{esc(label)}</text>'
def scale_bar(x,y,denom,metres):
    length=metres*1000/denom
    a=text(x,y-5,f'1:{denom} AT A1 / METRES',2.8,BLUE,bold=True)
    for i in range(4):a+=rect(x+i*length/4,y,length/4,2.2,INK if i%2==0 else 'white')
    return a+text(x,y+7,'0',2.8)+text(x+length/2,y+7,f'{metres/2:g}',2.8,anchor='middle')+text(x+length,y+7,f'{metres:g} m',2.8,anchor='end')
def heading(x,y,title,sub=''):
    return text(x,y,title,4.5,BLUE,bold=True)+(text(x,y+7,sub,3,GREY) if sub else '')
def table(x,y,columns,rows,widths,rowh=7):
    a='';yy=y
    for ri,row in enumerate([columns]+rows):
        xx=x
        for i,v in enumerate(row):
            a+=rect(xx,yy,widths[i],rowh,LIGHT if ri==0 else 'white',GREY,.18)+text(xx+2,yy+4.7,str(v),2.9,bold=ri==0);xx+=widths[i]
        yy+=rowh
    return a
def notes(items,x=650,y=70):
    a=''
    for title,body in items:
        a+=heading(x,y,title);y+=9
        lines=textwrap.wrap(body,68)
        for t in lines:a+=text(x,y,t,3);y+=4.8
        y+=11
    return a
def sheet(id,title,scale,subtitle):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="841mm" height="594mm" viewBox="0 0 841 594" role="img" aria-label="{esc(title)}"><defs><pattern id="hatch" width="3" height="3" patternUnits="userSpaceOnUse"><path d="M0 3L3 0" stroke="#a7b8c5" stroke-width=".18"/></pattern><pattern id="brick" width="6" height="2.5" patternUnits="userSpaceOnUse"><path d="M0 0H6M0 1.25H6M3 0V1.25M0 1.25V2.5M6 1.25V2.5" stroke="#b8c7d2" stroke-width=".13"/></pattern></defs><g font-family="Arial,Helvetica,sans-serif">',
        rect(0,0,841,594,'white','none'),rect(10,10,821,574),text(20,24,'ONSITE / HERON REACH',6,INK,bold=True),
        text(821,24,id+'  /  '+title,5,BLUE,'end',True),text(20,32,subtitle,3.1,GREY),line(20,37,821,37,GREY,.25),
        rect(10,552,821,32,'white'),line(370,552,370,584),line(630,552,630,584),line(748,552,748,584),
        text(20,562,'DIMENSIONED GAME-ENVIRONMENT DESIGN',3.5,BLUE,bold=True),text(20,570,'For Blender blockout / proposed / not an as-built playable',3),
        text(20,578,'Dimensions govern. All lengths in metres unless marked mm. Print A1 at 100%.',2.8),
        text(380,562,title,4,bold=True),text(380,571,'SCALE  '+scale+'   |   PAPER 841 × 594 mm',3),
        text(380,578,'MAP REV 01 + DETAIL ISSUE B01 / 18 OCTOBER 2026',2.8),
        text(640,563,'DRAWN FROM METRIC DATA',3,bold=True),text(640,572,'build-spec.json + map.json',3),text(640,579,'No networking / no runtime change',2.8),
        text(760,566,id,7,BLUE,bold=True),text(760,578,'B01  /  ONSITE',3)]
def finish(a,id,title,scale):
    filename=id.lower()+'-'+title.lower().replace(' / ','-').replace(' + ','-').replace(' ','-')
    a.append('</g></svg>');(OUT/(filename+'.svg')).write_text(''.join(a))
    PAGES.append(dict(id=id,title=title,scale=scale,file=filename))


class View:
    def __init__(self,x,y,scale,origin=(0,0)):
        self.x=x;self.y=y;self.s=1000/scale;self.origin=origin
    def p(self,x,z):return self.x+(x-self.origin[0])*self.s,self.y+(z-self.origin[1])*self.s
    def box(self,r,fill='none',stroke=INK,sw=.3):return rect(*self.p(*r[:2]),r[2]*self.s,r[3]*self.s,fill,stroke,sw)
    def label(self,x,z,s,size=3,c=INK):return text(*self.p(x,z),s,size,c,'middle')
    def ln(self,x,z,a,b,c=INK,sw=.3,dash=''):return line(*self.p(x,z),*self.p(a,b),c,sw,dash)


def wall_plan(v,w,show_tags=False):
    a='';start=w['start'];axis=w['axis'];at=w['at'];th=w['thickness']
    def wallpart(lo,hi):return v.box([lo,at,hi-lo,th]if axis=='x'else[at,lo,th,hi-lo],INK,INK,.15)
    for o in sorted(w['openings'],key=lambda o:o['centre']):
        lo=o['centre']-o['width']/2;hi=o['centre']+o['width']/2
        a+=wallpart(start,lo);start=hi
        if o['kind']=='window':
            if axis=='x':a+=v.box([lo,at,hi-lo,th],'white',BLUE,.22)+v.ln(lo,at+th/2,hi,at+th/2,BLUE,.18)
            else:a+=v.box([at,lo,th,hi-lo],'white',BLUE,.22)+v.ln(at+th/2,lo,at+th/2,hi,BLUE,.18)
        elif o['kind']=='door':
            # Door leaf and sweep are intent guides; blockout leaves are held open.
            sw=o.get('swing',1);width=o['width'];pp=(lo,at+th/2)if axis=='x'else(at+th/2,lo)
            qq=(lo,at+th/2+width*sw)if axis=='x'else(at+th/2+width*sw,lo)
            a+=v.ln(*pp,*qq,BLUE,.2)
            p=v.p(*( (hi,at+th/2) if axis=='x' else(at+th/2,hi)))
            q=v.p(*qq);r=width*v.s
            # Circular quadrant centred on hinge; sweep is mirrored with the instance.
            sweep=1 if (axis=='x'and sw>0)or(axis=='z'and sw<0)else 0
            a+=f'<path d="M{p[0]} {p[1]} A{r} {r} 0 0 {sweep} {q[0]} {q[1]}" stroke="{GREY}" stroke-width=".16" fill="none" stroke-dasharray="1 .7"/>'
        else:
            a+=v.ln(lo,at+th/2,hi,at+th/2,CYAN,.18,'1 .6') if axis=='x'else v.ln(at+th/2,lo,at+th/2,hi,CYAN,.18,'1 .6')
        if show_tags:
            x,z=(o['centre'],at-.15)if axis=='x'else(at+.2,o['centre'])
            a+=text(*v.p(x,z),o['id'],2.6,BLUE)
    a+=wallpart(start,w['end']);return a


def stair(v,st,labels=False,down=False):
    a='';fx=st['firstFlightX'];sx=st['secondFlightX'];z=st['flightZ'];run=st['flightRun'];w=st['flightWidth']
    a+=v.box(st['halfLanding'],LIGHT,BLUE,.25)+v.box(st['floorLanding'],LIGHT,BLUE,.25)
    for i in range(10):
        for xx in [fx,sx]:a+=v.ln(xx,z+i*.28,xx+w,z+i*.28,BLUE,.2)
    # In plan, first flight ascends toward local north, second returns south.
    pts=[v.p(fx+w/2,z+run),v.p(fx+w/2,z-.5),v.p(sx+w/2,z-.5),v.p(sx+w/2,z+run)]
    if down:pts.reverse()
    a+=poly(pts,CYAN,.45)
    ex,ey=pts[-1];a+=poly([(ex-1.3,ey-2),(ex,ey),(ex+1.3,ey-2)],CYAN,.45)
    if labels:
        a+=v.label(fx+w/2,z+run/2,'01–10',3)+v.label(sx+w/2,z+run/2,'11–20',3)
        a+=v.label(st['footprint'][0]/2,st['halfLanding'][1]+.65,'HALF +1.50',3.3)
        a+=v.label(st['footprint'][0]/2,st['floorLanding'][1]+.8,'FFL +3.00 / +0.00',3.3)
    return a


def home(v,module,labels=False,tags=False,furniture=False):
    m=B['modules'][module];a=v.box([0,0,9,8],'white',BLUE,.3)
    for r in m['rooms']:
        fill=LIGHT if 'HALL'in r['label']else'white'
        a+=v.box(r['rect'],fill,'none')
    if m['floorVoid']:a+=v.box(m['floorVoid'],'url(#hatch)',BLUE,.3)
    if module.startswith('H2'):
        vv=View(*v.p(6,2),1000/v.s);a+=stair(vv,B['stairs']['ST-H'],down=module=='H2-U')
        if labels:a+=vv.label(1.5,5.2,'DN TO +3'if module=='H2-U'else'UP TO +6',2.6,CYAN)
    for w in m['walls']:a+=wall_plan(v,w,tags)
    if furniture:
        for name,r in m['furniture']:
            a+=v.box(r,PALE,GREY,.2)
            if name=='bed':a+=v.box([r[0]+.1,r[1]+.1,r[2]-.2,.4],LIGHT,GREY,.2)
    if labels:
        for r in m['rooms']:
            if r['id']=='05'and module!='H1':continue
            x,z,w,d=r['rect'];size=3.1 if v.s>=20 else 2.5
            if 'HALL'in r['label']and w<2:
                px,py=v.p(x+w/2,z+d/2)
                a+=f'<text x="{px}" y="{py}" font-size="{size}" text-anchor="middle" fill="{BLUE}" transform="rotate(-90 {px} {py})">{esc(r["label"])} / 1.50 CLEAR</text>'
            else:
                a+=v.label(x+w/2,z+d/2,r['label'],size)
                a+=v.label(x+w/2,z+d/2+.23,f'{w:.2f} × {d:.2f} m',size-.25,GREY)
    return a


def instance_plan(v,ins,detail=False):
    a=f'<g transform="translate({v.p(ins["x"],ins["z"])[0]} {v.p(ins["x"],ins["z"])[1]})">'
    if ins['mirrorZ']:a+=f'<g transform="translate(0 {8*v.s}) scale(1 -1)">'
    a+=home(View(0,0,1000/v.s),ins['module'],False,False,detail)
    if ins['mirrorZ']:a+='</g>'
    a+='</g>'
    if detail:a+=v.label(ins['x']+4.5,ins['z']+8.7,ins['id'],3,BLUE)
    return a


def core_plan(v,c,level):
    y=next(l['y']for l in D['levels']if l['id']==level)
    if y not in c['levels']:return ''
    x,z,w,d=c['rect'];a=v.box(c['rect'],'white','none')
    px,pz=v.p(x,z)
    a+=f'<g transform="translate({px} {pz})'+(f' translate(0 {6*v.s}) scale(1 -1)'if c['mirrorZ']else'')+'">'
    a+=stair(View(0,0,1000/v.s),B['stairs']['ST-P'],down=y==c['levels'][-1])
    a+=core_walls(View(0,0,1000/v.s))
    a+='</g>'+v.label(x+3,z+3,c['id'],3,BLUE)
    direction='DN'if y==c['levels'][-1]else'UP'if y==c['levels'][0]else'UP/DN'
    a+=v.label(x+3,z+(5.7 if c['mirrorZ']else .6),f'{y:+.0f} {direction}',2.4,BLUE)
    return a


def core_walls(v):
    a=''
    for axis,at,start,end,ops in [('x',0,0,6,[]),('z',0,.2,5.8,[]),('z',5.8,.2,5.8,[]),('x',5.8,0,6,[dict(id='ENTRY',centre=3,width=1.5,kind='arch')])]:
        a+=wall_plan(v,dict(axis=axis,at=at,start=start,end=end,thickness=.2,openings=ops))
    return a


def site_grid(v):
    a=v.box([0,0,144,120],'white',BLUE,.5)
    for i,x in enumerate(range(0,145,12)):
        a+=v.ln(x,0,x,120,'#d6e1e9',.16,'2 2')+v.label(x,-1.5,f'{chr(65+i)} / {x}',2.5,GREY)
    for i,z in enumerate(range(0,121,12)):
        a+=v.ln(0,z,144,z,'#d6e1e9',.16,'2 2')+text(v.x-4,v.y+z*v.s+1,f'{i+1}/{z}',2.5,GREY,'end')
    a+=dimh(v.x,v.x+144*v.s,v.y,v.y-12,'144.000 m')+dimv(v.y,v.y+120*v.s,v.x,v.x-20,'120.000 m')
    a+=text(617,50,'N',3.5,BLUE,'middle',True)+line(617,58,617,52,BLUE,.4)+poly([(615.5,54),(617,51),(618.5,54)],BLUE,.4)
    return a


def site_plan(v,level,landscape=False,routes=False):
    a='';height=next(l['y']for l in D['levels']if l['id']==level)
    for b in D['blocks']:a+=v.box(b['rect'],PALE,GREY,.2)
    if level=='G':
        for p in D['planting']:a+=v.box(p['rect'],'#edf4ee',GREEN,.2)
    for s in D['surfaces']:
        if s['level']!=level or s['kind']=='home':continue
        a+=v.box(s['rect'],LIGHT if s['kind']in['gallery','service']else'#eef4ef'if s['kind']=='garden'else'white',BLUE,.3)
    for r in B['circulation']:
        if r['level']==level:a+=v.box(r['rect'],LIGHT,'none')
    for r in B['reserves']:
        if r['level']==level:a+=v.box(r['rect'],'url(#hatch)',GREY,.2)
    for ins in B['homeInstances']:
        if ins['y']==height:a+=instance_plan(v,ins)
    for c in B['cores']:a+=core_plan(v,c,level)
    if level=='G':
        for sh in B['shops']:
            a+=shop_plan(v,sh)
            x,z,w,d=sh['rect'];a+=v.label(x+w/2,z+d/2,sh['name'],2.5)
        a+=v.box([58,51,28,18],'none',GREY,.25)+v.ln(72,51,72,69,GREY,.25)+circle(*v.p(72,60),3*v.s,'none',GREY,.25)
        for s in D['spawns']:
            a+=v.box(s['rect'],'none',CYAN,.4)
            for i,p in enumerate(s['positions']):a+=circle(*v.p(p['x'],p['z']),.4*v.s,'none',CYAN,.3)
            a+=v.label(s['rect'][0]+8,46,s['team']+' / 16',2.8,CYAN)
        for o in D['objectives']:
            a+=circle(*v.p(o['x'],o['z']),5*v.s,'none',AMBER,.4)+v.label(o['x'],o['z']+.8,o['id'],5,AMBER)
    for c in D['cover']:
        if c['y']==height:a+=v.box(c['rect'],'#e8dfd0',AMBER,.25)
    if routes:
        nodes={n['id']:n for n in D['nodes']}
        for e in D['edges']:
            p,q=nodes[e['a']],nodes[e['b']]
            if p['y']!=height or q['y']!=height:continue
            pts=[[p['x'],p['z'],p['y']]]+e.get('via',[])+[[q['x'],q['z'],q['y']]]
            a+=poly([v.p(*pt[:2])for pt in pts],CYAN,.25,'1.5 1')
    if landscape:
        for t in D['trees']:
            a+=circle(*v.p(t['x'],t['z']),t['canopyRadius']*v.s,'none',GREEN,.4)+circle(*v.p(t['x'],t['z']),t['trunkRadius']*v.s,GREEN,GREEN,.2)
            a+=v.label(t['x'],t['z']-3,t['id'],2.8,GREEN)
        for p in D['wetAreas']:a+=v.box(p['rect'],'#cbe3eb',CYAN,.2)
        for l in D['lights']:
            a+=circle(*v.p(l['x'],l['z']),1.1,'white',AMBER,.4)+v.label(l['x']+2,l['z']+1,l['id'],2.6,AMBER)
    for b in D['blocks']:
        x,z,w,d=b['rect'];a+=v.label(x+w/2,z+(15 if z<60 else 2),b['name'],3.2)
    return a


def shop_plan(v,sh):
    x,z,w,d=sh['rect'];a=v.box(sh['rect'],'white',INK,.3)
    sides=[('N','x',z,x,x+w),('S','x',z+d-.2,x,x+w),('W','z',x,z+.2,z+d-.2),('E','z',x+w-.2,z+.2,z+d-.2)]
    for side,axis,at,start,end in sides:
        ops=[opening for opening in sh['doorOpenings']if opening['side']==side]
        opens=[dict(id=o['id'],centre=(x if axis=='x'else z)+o['offset'],width=o['width'],kind='arch')for o in ops]
        if side=='N':
            for i,(lo,hi)in enumerate(sh['glazing']['spans']):opens.append(dict(id=f'W0{i+1}',centre=x+(lo+hi)/2,width=hi-lo,kind='window'))
        a+=wall_plan(v,dict(axis=axis,at=at,start=start,end=end,thickness=.2,openings=opens))
    return a


# B000: issue cover, index, reconstruction contract.
a=sheet('B000','ISSUE INDEX','1:500 + NTS','A coordinated build brief for Claude / original ONSITE geometry / 32-player design target')
a.append(heading(30,60,'READ THIS ISSUE BEFORE MODELLING','All floor plans use the same surveyed-style site origin and level datums.'))
v=View(35,90,500);a.append(site_plan(v,'G',True));a.append(scale_bar(35,350,500,40))
a.append(table(360,60,['SHEET','TITLE','SCALE'],[
 ['B100','Site setting-out / coordinate schedule','1:250'],['B101','Ground floor / homes and shop portals','1:250'],['B102','Gallery level +3.00','1:250'],['B103','Upper homes +6.00','1:250'],['B104','Roof limits +9.00','1:250'],['B105','Undercroft -3.00','1:250'],['B200','Typical block: ground and gallery','1:125'],['B201','Typical block: upper and roof','1:125'],['B300','H1 through flat / clear room sizes','1:25'],['B301','H2 maisonette / both levels','1:50 / 1:25'],['B302','Public and private stair construction','1:25'],['B400','Home elevations / facade bay','1:50 / 1:25'],['B401','Building and stair sections','1:100 / 1:25'],['B500','Shops / court / openings','1:100'],['B600','Landscape / wetness / light positions','1:250'],['B700','Blender assembly / material details','1:25 / NTS']], [28,330,70],10))
a.append(notes([('WHAT IS FIXED','144 × 120 m site. Four 36 × 18 m blocks. Eight public stair cores. Eight H1 flats and eight H2 maisonettes. Existing block origins and site routes are retained.'),('WHAT B01 RESOLVES','Wall faces, clear halls, door and window apertures, stair nosings, upper slab holes, mirrored southern modules and object coordinates. These details supersede schematic Rev 01 massing.'),('WHAT CLAUDE MUST PROVE','Actual capsule movement, headroom, full route widths, bot floor selection, spawn visibility and measured GPU performance. The drawings are a game modelling specification, not evidence of a playable 32-person map.')],x=35,y=400))
a.append(notes([('MODEL SOURCE ORDER','map.json owns site placement; build-spec.json owns detailed modules. Use the separate blueprint guide .blend for setting-out. Preserve the earlier massing and current Heron Court game.'),('DIMENSION CONVENTION','Metres. Home dimensions are CLEAR inside faces; footprints are outside faces. Datum is finished floor level (FFL). Slabs lie below FFL. Dimensions govern over scaling an image.'),('COORDINATES','Map: x east, z south, y up. Blender: (x - 72, 60 - z, y). GLB: (x - 72, y, z - 60). Apply mirrors to all vertices and openings, then recalculate normals.')],x=360,y=280))
finish(a,'B000','ISSUE INDEX','1:500 + NTS')

a=sheet('B100','SITE SETTING OUT','1:250','Datum +0.00 = ground finished floor / origin NW corner / dimensions in metres')
v=View(40,60,250);a.append(site_grid(v));a.append(site_plan(v,'G'))
for b in D['blocks']:
    x,z,w,d=b['rect'];px,pz=v.p(x,z);a.append(dimh(px,px+w*v.s,pz,pz-5,'36.000'));a.append(v.label(x+18,z+11,f'({x}, {z}) / {w} × {d}',2.7,BLUE))
for x0,x1 in zip([0,24,60,84,120],[24,60,84,120,144]):a.append(dimh(*[v.p(x0,0)[0],v.p(x1,0)[0]],v.y,v.y-4,f'{x1-x0:.0f}'))
a.append(table(650,64,['BLOCK','X','Z','W × D'],[[b['id'],b['rect'][0],b['rect'][1],'36 × 18']for b in D['blocks']],[30,30,30,76]))
a.append(table(650,115,['CORE','X','Z','LEVELS'],[[c['id'],c['rect'][0],c['rect'][1],'/'.join(str(y)for y in c['levels'])]for c in B['cores']],[30,30,30,76]))
a.append(notes([('SETTING-OUT RULE','All rect arrays are [minimum x, minimum z, width, depth]. Core envelopes are 6 × 6. Home envelopes are 9 × 8. Origin pins are not mesh centres.'),('REPEATABLE GRID','Site grid A–M / 1–11 at 12 m. Facade subgrid 3 m. Core and doorway coordinates take precedence over a snapped decorative grid.'),('LEVEL DATUMS','B1 -3.00 / G 0.00 / L1 +3.00 / L2 +6.00 / R +9.00. Core roofs are +2.80 above their highest served FFL; they are not playable decks.')],y=200))
a.append(scale_bar(650,505,250,20));finish(a,'B100','SITE SETTING OUT','1:250')

floor_notes={
 'G':[('PLAYABLE GROUND','Continuous estate ground around the blocks. A Garden Court, B The Cage and C Washhouse Square are ground-only contest areas. Staging positions are initial placements, not dynamic respawns.'),('HOME AND SHOP OPENINGS','Eight H1 flats each have two through-hall exits. Six community/shop shells have explicit portals; B500 gives apertures. Windows are closed glazing, not player routes.'),('PUBLIC FLOOR','Pale blue means circulation. Hatched reserved strips are solid/service frontage. Ground cross-arcades remain open. Read H1 partitions at B300, not from this small-scale plan.')],
 'L1':[('CONNECTED GALLERY','Continuous north/south links and east/west runs at +3.00. Public stairs exit onto wrapping aprons. Gallery width is 3.00 clear between guard faces.'),('MAISONETTE ENTRANCES','Eight H2 lower entrances face their block concourse. Upper exits are on +6.00 rear landings. Do not add a second door through a closed lower rear wall.'),('SLAB OPENINGS','Remove every served core footprint before adding its landing and stairs. Never bridge a flight with a gallery slab. See B302 for exact stair voids; use the union of overlapping floor areas.')],
 'L2':[('FOUR UPPER ISLANDS','No cross-court deck exists at +6.00. Each block connects two public cores and two H2 upper exits via shared/rear halls. The gaps between blocks remain open sky.'),('PRIVATE STAIR VOIDS','H2 upper slabs have 2.68 × 3.84 openings in their local coordinates. The top landing remains solid. Mirror openings with the entire southern home; see B301.'),('RESERVED FRONTAGE','Hatched strips are non-traversable service frontage. Every required route stays in the drawn common halls, homes or external landing aprons.')],
 'R':[('LIMITED ROOF ACCESS','Rowan NW and Cedar SE terraces only. Two public core exits per terrace. Ash NE and Birch SW roofs remain closed; do not add nav surfaces or jump routes there.'),('GUARDS AND SCREENS','Guard all exposed edges to 1.20. Keep the existing 2.10 opaque outer side screens facing staging areas. Plant housings interrupt long views; placement remains a design target.'),('CORE OVERRUN','S1/S2/S7/S8 extend to a +11.80 cap above their +9.00 landing. No flight continues above +9.00. Other cores cap at +8.80; no fake route from them to a closed roof.')],
 'B1':[('PARTIAL UNDERCROFT','Only blue areas are floor at -3.00. White/grey site context is not an underground slab. Four exits use S2, S3, S6 and S7; no underground spawn room.'),('WALLS AND CEILING','Build 200 mm walls outside the union boundary. Floor -3.00, ceiling underside -0.20. No internal wall at overlapping rectangle joins. Keep services above 2.40 clear.'),('STAIR CONNECTIONS','Core entry aprons connect the service loop to the full-level landing. Delete ground slabs over flights to G. Avoid sealing an entrance with an imported terrain plane.')]
}
for i,level in enumerate(['G','L1','L2','R','B1'],101):
    lvl=next(l for l in D['levels']if l['id']==level);title={'G':'GROUND FLOOR','L1':'GALLERY FLOOR','L2':'UPPER HOMES','R':'ROOF PLAN','B1':'UNDERCROFT'}[level]
    a=sheet(f'B{i}',title,'1:250',f'Finished floor {lvl["y"]:+.2f} m / plans show proposed geometry / details B200–B500')
    v=View(40,60,250);a.append(site_grid(v));a.append(site_plan(v,level,routes=True))
    if level=='R':
        for b in D['blocks']:
            x,z,w,d=b['rect']
            if not b['roofPlayable']:a.append(v.box(b['rect'],'url(#hatch)',GREY,.3)+v.label(x+18,z+9,'CLOSED / NO NAV',4,GREY))
            else:
                for r in [[x+2,z+2,10,5],[x+21,z+10,9,5]]:a.append(v.box(r,'url(#hatch)',INK,.4))
                for xx in [x,x+w-.2]:a.append(v.box([xx,z,.2,d],INK,INK,.2))
    a.append(notes(floor_notes[level]));a.append(notes([('DRAWING KEY','Heavy navy: cut wall. Pale blue: circulation/slab. Dashed cyan: previous route intent only. Amber: cover/objective. Hatch: reserved/closed/void as labelled. Routes still need physical verification.')],y=380))
    a.append(scale_bar(650,505,250,20));finish(a,f'B{i}',title,'1:250')

# Enlarged block plans, northern type; southern installation is a z mirror.
for id,levels,title in [('B200',['G','L1'],'BLOCK GROUND AND GALLERY'),('B201',['L2','R'],'BLOCK UPPER AND ROOF')]:
    a=sheet(id,title,'1:125','ROWAN NW canonical block / north up / other block origins B100 / southern blocks mirror depth')
    for j,level in enumerate(levels):
        xx=65+j*405;v=View(xx,100,125,(24,18));height=next(l['y']for l in D['levels']if l['id']==level)
        a.append(heading(xx,60,f'NW / {level} / FFL {height:+.2f}', '36 × 18 block plus two cores and external landing aprons'))
        a.append(v.box([24,18,36,18],LIGHT,INK,.4))
        if level!='R':
            for r in B['reserves']:
                if r['level']==level and r['id'].startswith('NW'):a.append(v.box(r['rect'],'url(#hatch)',INK,.3))
            for h in B['homeInstances']:
                if h['id'].startswith('NW')and h['y']==height:a.append(instance_plan(v,h,True))
            a.append(v.label(45,25,'COMMON HALL',4,BLUE)+v.label(42,19.5,'REAR LANDING / 3.00',3,BLUE))
            a.append(v.label(42,32,'FRONT CONCOURSE / DO NOT FURNISH ACROSS ROUTES',3,BLUE))
        else:
            for r in [[26,20,10,5],[45,28,9,5]]:a.append(v.box(r,'url(#hatch)',INK,.4))
            for x in [24,59.8]:a.append(v.box([x,18,.2,18],INK,INK,.2))
            a.append(v.label(42,27,'ROOF TERRACE / FFL +9.00',4,BLUE))
        for s in D['surfaces']:
            if s['level']==level and s['id'].startswith(('S1','S2')):a.append(v.box(s['rect'],LIGHT,BLUE,.3))
        for c in B['cores'][:2]:a.append(core_plan(v,c,level))
        px,pz=v.p(24,18);a.append(dimh(px,px+36*v.s,pz,pz-10,'36.000'))
        for lo,hi in [(24,26),(26,35),(35,49),(49,58),(58,60)]:a.append(dimh(v.p(lo,18)[0],v.p(hi,18)[0],pz,pz-4,f'{hi-lo:.2f}'))
        a.append(dimv(pz,pz+18*v.s,px,px-12,'18.000'))
        for lo,hi in [(18,21),(21,29),(29,36)]:a.append(dimv(v.p(24,lo)[1],v.p(24,hi)[1],px,px-5,f'{hi-lo:.2f}'))
        a.append(scale_bar(xx,350,125,10))
    a.append(notes([('BLOCK ASSEMBLY','Set the block NW corner first. Homes sit at local (2,3) and (25,3), both 9 × 8. Front concourse starts local z=11; rear landing is z=0–3. Reserve only the two 2 × 8 side strips. Ground arcade at local x=18–24 stays clear.'),('SOUTHERN TRANSFORM','Birch/Cedar: world z = block z + 18 - local z. Home origins become local z=7, and home geometry mirrors within its 8 m footprint. Public stair origin is block z - 6; the stair entrance faces north. Do not rotate only the door labels.')],x=35,y=440))
    a.append(notes([('FACADE TREATMENT','The broad blue areas are common concourses/landings, not extra flats. Open edges receive guards, brick piers and soffits; use glazing only where scheduled. Keep both sides of every home exit connected.'),('PORTALS AND BRIDGES','No wall crosses a shared hall, stair apron or the ground arcade. At +3 the bridges connect between blocks. At +6 there is no inter-block bridge. All floor plates are unions with holes, not overlapping coplanar rectangles.')],x=445,y=440))
    finish(a,id,title,'1:125')

a=sheet('B300','H1 THROUGH FLAT','1:25','One-bedroom module / eight ground instances / 72 m² gross / clear dimensions between finished faces')
v=View(55,95,25);a.append(home(v,'H1',True,True,True))
a.append(dimh(55,415,95,76,'9.000 OUTSIDE'));a.append(dimv(95,415,55,35,'8.000 OUTSIDE'))
for lo,hi,label in [(.2,1.7,'1.50 clear'),(1.82,4.38,'2.56 clear'),(4.5,8.8,'4.30 clear')]:a.append(dimh(55+lo*40,55+hi*40,95,88,label))
for lo,hi,label in [(.2,3.03,'2.83'),(3.15,4.65,'1.50'),(4.77,7.8,'3.03')]:a.append(dimv(95+lo*40,95+hi*40,415,430,label))
a.append(scale_bar(55,445,25,5))
m=B['modules']['H1'];a.append(table(475,70,['ROOM','CLEAR W × D','AREA'],[[r['label'],f'{r["rect"][2]:.2f} × {r["rect"][3]:.2f}',f'{r["clearArea"]:.2f} m²']for r in m['rooms']],[135,105,76],9))
ops=[(w,o)for w in m['walls']for o in w['openings']]
a.append(table(475,155,['OPENING','WIDTH','HEAD / SILL'],[[o['id']+' / '+o['kind'],f'{o["width"]:.2f}',f'{o["sill"]+o["height"]:.2f} / {o["sill"]:.2f}']for w,o in ops],[135,55,126],8))
a.append(notes([('WALLS AND LEVELS','External shell 200 mm. Partitions 120 mm. FFL 0.00; clear ceiling +2.80, next FFL +3.00. Shell fits inside the 9 × 8 footprint. Slab top equals FFL; do not add slab thickness above it.'),('TWO REAL EXITS','D01/D02 are 1.10 clear and share a 1.50 clear hall. Hall centre is x=0.95; openings x=0.40–1.50. Door leaves are held open in the first blockout. Bedrooms/bathrooms are optional, not the through route.'),('MODELLING NOTES','Room dimensions exclude walls. Furniture is an allowance, not another collider owner. Preserve cross-hall and door sweeps. Window sill 0.90, head 2.25; closed glazing. Southern instances mirror every local z coordinate.')],x=475,y=280))
a.append(paragraph(55,485,'ROOM TAGS AND OPENINGS: use the local coordinates in build-spec.json. Each placed portal is listed in home-openings.csv with world position, width and head height. Door arcs are modelling guides; working-door gameplay is deferred.',105))
finish(a,'B300','H1 THROUGH FLAT','1:25')

a=sheet('B301','H2 MAISONETTE','1:50 + 1:25','Eight two-storey homes / 144 m² gross per home / lower gallery entrance and upper rear exit')
for j,mod in enumerate(['H2-L','H2-U']):
    x=45+j*250;v=View(x,85,50);a.append(heading(x,58,mod+' / '+('+3.00'if j==0 else'+6.00')))
    a.append(home(v,mod,True,True,True));a.append(dimh(x,x+180,85,75,'9.000'));a.append(dimv(85,245,x,x-10,'8.000'))
    a.append(text(x,258,'FRONT ENTRY +3.00'if j==0 else'REAR EXIT +6.00 / VOID HATCHED',3.2,BLUE,bold=True))
    a.append(scale_bar(x,275,50,5))
a.append(notes([('HALL AND DOORS','Hall x=4.50–6.00 = 1.50 clear. Lower exterior door only at z=8; upper exterior door only at z=0. Clear width 1.10. The opposite wall stays closed on each floor.'),('UPPER OPENING','Remove [6.12, 2.08, 2.68, 3.84] from upper slab in home-local x/z. Keep the top landing at z=5.92–7.80. Do not cut the whole 3 × 6 stair allocation out of the upper floor.'),('PRIVATE STAIR','ST-H: two 1.20 flights; 20 × 0.15 rises; 9 × 0.28 goings per half. Half landing 1.20. Upper and lower hall portals at z=6.50; both open onto solid full-level landing.')],x=565,y=60))
v=View(65,305,25);a.append(heading(45,292,'ST-H / 3 × 6 STAIR / 1:25'));a.append(v.box([0,0,3,6],'white',INK,.4));a.append(v.box(B['stairs']['ST-H']['floorVoid'],'url(#hatch)',BLUE,.25));a.append(stair(v,B['stairs']['ST-H'],True));a.append(v.ln(0,3.95,0,5.05,'white',.8));a.append(v.label(-.15,4.5,'HALL',2.4,CYAN))
a.append(dimh(65,185,305,299,'3.000'));a.append(dimv(305,545,65,53,'6.000'))
a.append(table(265,330,['ROOM','LOWER CLEAR','UPPER CLEAR'],[
 ['Kitchen / bedroom 1','4.18 × 2.68','4.18 × 3.18'],['Living / bedroom 2','4.18 × 4.80','4.18 × 4.30'],['Hall','1.50 × 7.60','1.50 × 7.60'],['WC / bath','2.68 × 1.68','2.68 × 1.68'],['Stair allocation','3.00 × 6.00 gross','same; slab void differs']],[115,125,145],9))
a.append(notes([('MIRROR AS ONE MODULE','For southern homes use world z = home.z + 8 - local z. This includes walls, windows, floors, floor hole, both flights and landing. Recalculate normals after baking the mirror.'),('EXACT NOSING POSITIONS','Home-local flight run z=3.40–5.92. Left flight x=6.18–7.38 rises north; right x=7.53–8.73 rises south. Half landing at +4.50. Top landing at +6.00. Stair tread/slab thickness 150 mm.'),('CLEARANCE','Leave at least 2.40 headroom; current repeated 3.00 storey / 0.20 slab gives 2.80 at landings. Place guards and rail posts outside the 1.20 clear flights. Test the actual capsule before adding art.')],x=265,y=405))
finish(a,'B301','H2 MAISONETTE','1:50 + 1:25')

a=sheet('B302','STAIR CONSTRUCTION','1:25','ST-P public core / all dimensions between designated faces / south instances mirror z / no slab across flights')
v=View(65,100,25);st=B['stairs']['ST-P'];a.append(heading(50,60,'ST-P / PLAN AT FULL LANDING','6 × 6 envelope / 1.50 clear flights / 200 mm outer shell'))
a.append(v.box([0,0,6,6],'white','none'));a.append(v.box(st['floorVoid'],'url(#hatch)',BLUE,.3));a.append(stair(v,st,True));a.append(core_walls(v))
a.append(dimh(65,305,100,83,'6.000'));a.append(dimv(100,340,65,48,'6.000'))
for lo,hi,label in [(.2,1.7,'1.50'),(1.7,4.22,'2.52 / 9 GOINGS'),(4.22,5.8,'1.58')]:a.append(dimv(100+lo*40,100+hi*40,305,318,label))
for lo,hi in [(.4,1.9),(4.1,5.6)]:a.append(dimh(65+lo*40,65+hi*40,340,355,'1.50 CLEAR'))
a.append(dimh(65+2.25*40,65+3.75*40,340,375,'1.50 PUBLIC ENTRY'))
a.append(heading(380,60,'UNFOLDED WALKING LINE / 1:25','Section follows both flights; no vertical exaggeration.'))
sx,sy,s=385,290,40
pts=[(sx,sy),(sx+1.5*s,sy)]
run=1.5
for i in range(9):
    pts.extend([(sx+run*s,sy-(i+1)*.15*s),(sx+(run+.28)*s,sy-(i+1)*.15*s)]);run+=.28
pts.extend([(sx+run*s,sy-1.5*s),(sx+(run+1.5)*s,sy-1.5*s)]);run+=1.5
for i in range(9):
    pts.extend([(sx+run*s,sy-(1.5+(i+1)*.15)*s),(sx+(run+.28)*s,sy-(1.5+(i+1)*.15)*s)]);run+=.28
pts.extend([(sx+run*s,sy-3*s),(sx+(run+1.5)*s,sy-3*s)])
a.append(poly(pts,INK,.7))
for y in [0,1.5,3]:a.append(line(sx,sy-y*s,800,sy-y*s,GREY,.2,'2 2')+text(805,sy-y*s+1,f'+{y:.2f}',3,BLUE))
a.append(dimv(sy-3*s,sy,sx,sx-12,'3.000 / 20 RISERS'))
a.append(paragraph(380,320,'Each flight: 10 risers × 150 mm = 1.500 m rise; 9 treads × 280 mm = 2.520 m run. The tenth rise terminates at a landing. Do not add a tenth independent tread and then another riser at the landing.',83))
a.append(table(380,370,['PART','LOCAL RECTANGLE / X, Z, W, D','TOP'],[
 ['Half landing','0.40, 0.20, 5.20, 1.50','FFL +1.50'],['Full-level landing','0.20, 4.22, 5.60, 1.58','FFL +0 / +3'],['Floor void','0.20, 0.20, 5.60, 4.02','every served slab'],['Left clear flight','x 0.40–1.90 / z 1.70–4.22','rises north'],['Right clear flight','x 4.10–5.60 / z 1.70–4.22','rises south'],['Front portal','x 2.25–3.75 / z 5.80–6.00','2.40 clear head']],[78,240,120],9))
a.append(notes([('LANDINGS / GUARDS','Guard flight voids at 1.20, handrail 1.00 above nosing line. Rail material must not reduce the specified clear width. Full-level landing connects to the external apron; no closed balustrade across that portal.'),('STACK AND CAP','Repeat at 3 m. Remove core volume from broad gallery floors and use this explicit slab opening/landing. Build no flight above the highest served level. Cap the top core at FFL +2.80; reserve 2.40 headroom below fittings.')],x=50,y=405))
a.append(scale_bar(50,520,25,5));finish(a,'B302','STAIR CONSTRUCTION','1:25')


def elevation(v,mod,side,base=0):
    m=B['modules'][mod];a=v.box([0,0,9,3],'url(#brick)',INK,.4)
    wall=next(w for w in m['walls']if w['id']==side)
    for op in wall['openings']:
        if op['kind']not in ['door','window']:continue
        x=op['centre']-op['width']/2;z=3-op['sill']-op['height']
        a+=v.box([x,z,op['width'],op['height']],LIGHT,BLUE,.3)
        if op['kind']=='window':a+=v.ln(op['centre'],z,op['centre'],z+op['height'],BLUE,.2)
        a+=v.label(op['centre'],z-.1,op['id'],2.6,BLUE)
    a+=v.box([0,0,9,.2],LIGHT,INK,.2)
    a+=v.label(9.6,3,f'{base:+.2f}',2.8,BLUE)+v.label(9.6,0,f'{base+3:+.2f}',2.8,BLUE)
    return a


a=sheet('B400','HOME ELEVATIONS','1:50 + 1:25','Canonical north-home local elevations / mirror the southern placements / all windows are closed glazing')
for j,side in enumerate(['N','S']):
    x=45+j*270;a.append(heading(x,60,'LOCAL '+('REAR / NORTH'if side=='N'else'FRONT / SOUTH')+' / 1:50'))
    for k,mod in enumerate(['H2-U','H2-L','H1']):a.append(elevation(View(x,90+k*60,50),mod,side,6-k*3))
    a.append(dimh(x,x+180,90,78,'9.000'))
    a.append(text(x,288,'H1 0–3 / H2 lower 3–6 / H2 upper 6–9',3,BLUE))
    a.append(scale_bar(x,310,50,5))
a.append(notes([('READ AS MODULE ELEVATIONS','These are the home faces behind shared landings/concourse, not a fabricated full-building facade. B200/201 locates them inside the 36 × 18 block. Keep public circulation visible and open at its connections.'),('FACADE KIT','Use 3.00 × 3.00 bay logic, stock brick, 200 mm shell, concrete floor band and 80–120 mm recessed frames. Repeat with instancing, vary curtains/wear rather than geometry dimensions.'),('NO NEW ROUTES FROM WINDOWS','Home glass stays closed and non-traversable. Staging-facing service strips and roof screens remain opaque. Any new overlooking window needs a gameplay visibility review.')],x=600,y=60))
a.append(heading(45,365,'F01 / TYPICAL 3 M WINDOW BAY / 1:25'))
v=View(65,390,25);a.append(v.box([0,0,3,3],'url(#brick)',INK,.4));a.append(v.box([.75,.75,1.5,1.35],LIGHT,BLUE,.4));a.append(v.ln(1.5,.75,1.5,2.1,BLUE,.25));a.append(v.box([0,0,3,.2],LIGHT,INK,.25))
a.append(dimh(65,185,390,380,'3.000'));a.append(dimv(390,510,65,50,'3.000'))
a.append(table(260,365,['COMPONENT','DIMENSION / DATUM','MATERIAL'],[
 ['Exterior wall','0.20 / within footprint','M01 stock brick'],['Window W01 H1','1.50 × 1.35 / sill +0.90','M05 frame + closed glass'],['Window W01 H2','2.00 × 1.35 / sill +0.90','same shared material'],['Home doorway','1.10 × 2.20 clear','M05 / held open initially'],['Floor edge','0.20 deep below FFL','M02 concrete'],['Parapet / guard','1.20 above deck','M02 + M05'],['Sign / number plate','0.30 × 0.18 / centre +1.55','shared text/decal atlas']],[125,225,170],10))
a.append(paragraph(260,465,'Frame recess, drip, sill and material joints belong to render geometry. Collision uses the simple wall aperture and closed glass plane. Do not let bevels, trims or dirt decals reduce clear doors, stairs or passage widths. Building lights are recreated in Three.js; Blender lamps are review-only.',100))
finish(a,'B400','HOME ELEVATIONS','1:50 + 1:25')

a=sheet('B401','SECTIONS AND DATUMS','1:100 + 1:25','A-A north block at x=27.00 / north to south / B-B private stair walking line / dimensions are true scale')
a.append(heading(45,60,'A-A / ROWAN + S1 / LOOK EAST / 1:100','Section x=27 passes through the H1 hall, H2 rooms, rear landing, concourse and central stair well.'))
x0,y0,s=65,270,10
for z0,z1,y in [(18,36,0),(18,36,3),(18,36,6),(18,36,9)]:a.append(rect(x0+(z0-18)*s,y0-y*s,(z1-z0)*s,2,LIGHT,INK,.3))
for y in [0,3,6]:
    for z in [21,28.8]:a.append(rect(x0+(z-18)*s,y0-(y+2.8)*s,2,6 if y==0 else 28,'url(#hatch)',INK,.3))
    a.append(text(x0+70,y0-(y+1.5)*s,'H1'if y==0 else'H2 LOWER'if y==3 else'H2 UPPER',3,BLUE,'middle'))
    a.append(text(x0+145,y0-(y+1.5)*s,'CONCOURSE',2.5,BLUE,'middle'))
    # x=27 section crosses middle of the well, not a flight. Show landings only.
    a.append(rect(x0+(36.2-18)*s,y0-(y+1.5)*s,15,1.5,LIGHT,INK,.3))
    a.append(rect(x0+(40.22-18)*s,y0-(y+3)*s,15.8,2,LIGHT,INK,.3))
a.append(rect(x0+(36-18)*s,y0-11.8*s,2,11.8*s,'url(#hatch)',INK,.3))
for y in [0,3,6,9]:a.append(rect(x0+(41.8-18)*s,y0-(y+2.8)*s,2,4,'url(#hatch)',INK,.3))
a.append(rect(x0+180,y0-11.8*s,60,2,LIGHT,INK,.3))
for y in [0,3,6,9,11.8]:a.append(line(40,y0-y*s,340,y0-y*s,GREY,.18,'2 1')+text(345,y0-y*s+1,f'{y:+.2f}',3,BLUE))
a.append(dimh(x0,x0+180,y0,y0+15,'18.000 BLOCK'));a.append(dimh(x0+180,x0+240,y0,y0+15,'6.000 CORE'))
a.append(scale_bar(45,325,100,10))
a.append(notes([('SECTION CUT DISCIPLINE','A-A is at map x=27, within the central well of S1. The cut shows half/full landings, not a fictitious straight flight through the well. Flights are dimensioned on B302.'),('CEILING / SLAB','Storey 3.00; slab 0.20 below FFL; clear room height 2.80. Public portal head 2.40. Stair treads/landing soffits must never intrude into the 2.40 minimum headroom envelope.'),('UNDERCROFT','B1 FFL -3.00. Ground slab underside -0.20. Clear 2.80 before services; services no lower than +2.40 relative to B1. Only the service union and exit cores are excavated in the model.')],x=400,y=65))
a.append(heading(45,380,'D01 / FLOOR EDGE + GUARD / 1:25'))
v=View(75,410,25);a.append(v.box([0,1.2,4,.2],LIGHT,INK,.3));a.append(v.box([0,0,.15,1.2],'url(#hatch)',INK,.3));a.append(v.ln(.15,0,3.15,0,CYAN,.3,'1 1'));a.append(dimh(81,201,410,395,'3.00 CLEAR FROM GUARD FACE'));a.append(dimv(410,458,75,63,'1.20 GUARD'))
a.append(text(85,479,'SLAB 200 mm BELOW FFL',3,BLUE));a.append(text(85,487,'Posts/trim outside walk polygon',3,GREY))
a.append(heading(400,380,'D02 / OPENING AND THRESHOLD / 1:25'))
a.append(table(400,400,['ELEMENT','REQUIRED CLEARANCE'],[['Home door','1.10 wide × 2.20 high'],['Public portal','1.50 wide × 2.40 high'],['Home hall','1.50 clear between finish faces'],['Public stair flight','1.50 clear between rail faces'],['Private stair flight','1.20 clear between rail faces'],['Threshold','0.02 maximum; flush preferred'],['Collision plan','Match structural faces; exclude tiny trims']],[140,260],10))
finish(a,'B401','SECTIONS AND DATUMS','1:100 + 1:25')

a=sheet('B500','SHOPS AND COURT','1:100','Six shell interiors / explicit public doorways / four open court gates / furniture follows route clearance')
for x,z,name,w,d,idx in [(45,100,'18 × 9 SHOP TYPE',18,9,0),(315,100,'6 × 18 SERVICE TYPE',6,18,4)]:
    sh=dict(B['shops'][idx]);sh['rect']=[0,0,w,d];v=View(x,z,100)
    a.append(heading(x,65,name));a.append(shop_plan(v,sh));a.append(dimh(x,x+w*10,z,z-12,f'{w:.3f}'));a.append(dimv(z,z+d*10,x,x-12,f'{d:.3f}'))
    a.append(v.ln(w/2,0,w/2,d,CYAN,.6,'2 1'));a.append(v.label(w/2,d/2,'CLEAR ROUTE',3,CYAN))
    if w<d:a.append(v.ln(w/2,d/2,w,d/2,CYAN,.6,'2 1'))
    a.append(text(x,z+d*10+15,'N: 2.00 × 2.40 / S: 1.50 × 2.40',3,BLUE))
a.append(heading(475,65,'THE CAGE / 30 × 20 / FOUR 4 M GATES'))
v=View(485,100,100);a.append(v.box([0,0,30,20],PALE,INK,.5));a.append(v.box([1,1,28,18],'none',BLUE,.3));a.append(v.ln(15,1,15,19,BLUE,.25));a.append(circle(*v.p(15,10),30,'none',BLUE,.25))
for x,z,w,d in [[13,-.1,4,.2],[13,19.9,4,.2],[-.1,8,.2,4],[29.9,8,.2,4]]:a.append(v.box([x,z,w,d],'white','white',.3))
for c in D['cover']:
    x,z,w,d=c['rect']
    if 57<x<87 and 50<z<70:a.append(v.box([x-57,z-50,w,d],'#e8dfd0',AMBER,.3))
a.append(dimh(485,785,100,85,'30.000'));a.append(dimv(100,300,485,472,'20.000'))
a.append(table(45,340,['INSTANCE','ORIGIN X / Z','SIZE','SIDE DOOR'],[[s['name'],f'{s["rect"][0]} / {s["rect"][1]}',f'{s["rect"][2]} × {s["rect"][3]}',next((o['side']for o in s['doorOpenings']if o['id']=='D03'),'—')]for s in B['shops']],[130,85,65,75],10))
a.append(notes([('INTERIOR BUILD RULE','200 mm shell, 2.80 clear ceiling. Keep a 2.40 continuous route between portals; use display racks/appliances around the perimeter. Door leaves held open initially. Side service doors face Washhouse Square.'),('SHOPFRONT','N-side display glass: sill 0.60, head 2.20. Spans from x=0.60 to centre-1.50 and centre+1.50 to width-0.60. Fascia and shutters are render details; do not seal the scheduled front door.')],x=45,y=435))
a.append(notes([('COURT ASSEMBLY','Map origin (57,50). Fence 2.60 high; four 4.00 gates at side midpoints. Paint rectangle inset 1.00. Mesh is visually porous; define bullet/collision behaviour explicitly. No physics for painted lines.'),('USEFUL COVER','Low cover height 1.00; tall screens 2.10. Exact cover placements stay in map.json / cover-placements.csv. Dirty edges and nets are cosmetic; use measured box collision for rigid cover.')],x=475,y=350))
a.append(scale_bar(475,510,100,10));finish(a,'B500','SHOPS AND COURT','1:100')

a=sheet('B600','LANDSCAPE AND LIGHT','1:250','20 trees / 10 soil-grass zones / 7 wet patches / 20 fixture intentions / five dressing zones')
v=View(40,60,250);a.append(site_grid(v));a.append(site_plan(v,'G',True))
for p in D['planting']:
    x,z,w,d=p['rect'];a.append(v.label(x+w/2,z+d/2,p['id'],3,GREEN))
for p in D['wetAreas']:
    x,z,w,d=p['rect'];a.append(v.label(x+w/2,z+d/2,p['id'],2.8,CYAN))
a.append(notes([('LONDON GROUND LAYERS','M03 asphalt to service lanes; M04 slabs to concourses. Dirt at drains/thresholds, moss on shaded concrete, leaves under trees, litter at shops and bin bays. Do not distribute grime uniformly.'),('TREE AND PLANTING CLEARANCE','Trunks use measured colliders. Canopies start 2.70 above ground. Shrubs at routes stay below 0.70. Keep final foliage outside stair entries and door sweeps; leaf cards never provide dependable ballistic cover.'),('LIGHTING DIRECTION','Cool blue-hour ambient; 2700 K door/shop/street fixture intent and 3000 K court fixtures. Warm thresholds reveal black clothing. Light positions/heights are in CSV; rebuild the lighting in Three.js.'),('WETNESS IS A MATERIAL LAYER','W1–W7 indicate shallow surface wetness. No extra collision. Use roughness variation and local puddle masks; preserve dry readable paths. Source texture packs are not all runtime-ready PBR.'),('DRESSING OWNERSHIP','Small paper/leaves/grass are render-only. Large bins, tree trunks and planters need explicit collision. Keep render, collision and navigation separate and use measured LOD/instancing budgets.')]))
a.append(scale_bar(650,505,250,20));finish(a,'B600','LANDSCAPE AND LIGHT','1:250')

a=sheet('B700','BLENDER ASSEMBLY','1:25 + NTS','Collection naming, pivots, materials and export contract / build the physical route before decoration')
a.append(table(35,60,['COLLECTION','CONTENT','EXPORT ROLE'],[
 ['00_DATUMS','Site bounds, grid, FFL markers, origin empties','guide only'],['10_GROUND / 11_UNDERCROFT','Union floors, explicit voids / tunnel shell','render and separate collision source'],['20_BLOCKS / 21_HOMES','Shared concourses; H1 and H2 placed modules','render chunks by block / storey'],['30_STAIRS / 31_GUARDS','ST-P and ST-H, mirrored with their instance','measured collision / floor links'],['40_SHOPS / 41_COURT','Door apertures, court fences and cover','render / rigid props collision'],['50_LANDSCAPE / 51_DECALS','Trees, grass, dirt, puddles, litter','render; trunks separately collidable'],['60_LIGHT_INTENT','Fixture emissive meshes + position empties','lights recreated in Three.js'],['90_COLLISION / 91_NAV_GUIDES','Simple solids / floor-aware portal labels','separate; not duplicate controllers']],[160,365,230],11))
a.append(notes([('PIVOTS AND AXES','Use one Blender unit = one metre. Site pivot is world centre at (0,0,0). Module pivot is local minimum x/z at FFL. Apply transforms and recalculate normals after mirroring; keep scale +1.0. Bake the coordinate conversion once.'),('EXPORT CONTRACT','Export efficient render GLBs per spatial chunk. Preserve module/instance IDs as custom properties. Keep physical geometry and nav links in separate data. The existing WWB runtime uses one Rapier world and one actor movement owner.'),('DONT SHIP THE GUIDE AS FINAL ART','The companion .blend is exact blockout guidance with solid colours and labelled openings. It is separate from the old massing. Do not overwrite manual work or bundle the research clones. Donor assets still need their individual provenance.')],x=35,y=190))
a.append(table(440,195,['ID','FAMILY','DETAIL / REUSE'],[
 ['M01','Stock brick','shared neutral base + local streak masks'],['M02','Concrete','gallery soffits, slab bands, nosings'],['M03','Asphalt','rain-dark base / isolated wetness'],['M04','Paving','slab joints and dirty drain edges'],['M05','Painted metal','railings, doors, frames, signs'],['M06','Soil / grass','beds and seams; alpha overdraw budget']],[28,100,250],10))
a.append(heading(440,295,'ENVIRONMENT FINISH / DETAIL STACK / NTS'))
a.append(paragraph(440,307,'1. Structural silhouette and openings. 2. Recessed frames, parapets and soffits. 3. Shared PBR materials with consistent scale. 4. Dirt/wetness masks placed by water and use. 5. Instanced vegetation and rubbish. 6. Local lighting rebuilt and measured in Three.js.',95))
a.append(heading(35,405,'D03 / GROUND EDGE / 1:25'))
v=View(55,440,25);a.append(v.box([0,.1,3,.15],LIGHT,INK,.3));a.append(v.box([3,0,.2,.4],'url(#hatch)',INK,.3));a.append(v.box([3.2,.08,2,.3],'#edf4ee',GREEN,.3));a.append(v.box([2.7,.08,.2,.02],INK,INK,.2));a.append(text(60,467,'PAVING / +0.00',3,BLUE));a.append(text(193,467,'SOIL -0.02',3,GREEN))
a.append(paragraph(35,485,'Drain slots, joints, moss and leaf litter follow edges. Kerbs stay outside primary walk polygons. Use flush transitions where the designed route crosses a change of material. Detail heights are render intent until capsule-tested.',110))
a.append(notes([('ACCEPTANCE BEFORE ART','Walk every home exit and every stair both directions with actual capsules. Verify floor-aware bot routes at overlapping x/z, no double floors, correct roof closures, reliable headroom and no spawn sightlines. Then compare a camera view to the original London artwork.'),('ACCEPTANCE BEFORE CLAIMING 32 PLAYERS','Measure frame time, memory and load with populated actors on a real GPU. Route checks and these drawings do not prove game balance or server capacity. Networking is a separate later milestone.')],x=440,y=390))
finish(a,'B700','BLENDER ASSEMBLY','1:25 + NTS')

(OUT/'sheets.json').write_text(json.dumps(PAGES,indent=2)+'\n')
print(f'{len(PAGES)} A1 vector blueprint sheets generated.')
