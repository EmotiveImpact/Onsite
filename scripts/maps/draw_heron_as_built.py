"""Render the Heron Reach as-built plan (five floors) from the runtime collision/nav dump."""
import json,sys
from PIL import Image,ImageDraw,ImageFont
src=sys.argv[1] if len(sys.argv)>1 else 'test-results/heron-reach/as-built.json'
dst=sys.argv[2] if len(sys.argv)>2 else 'docs/maps/heron-reach-32/as-built/heron-reach-as-built.png'
d=json.load(open(src));S=7;W,H=d['site'][2],d['site'][3];gap=36;top=110
panels=[('B1 / FFL -3.00',-3),('G / FFL +0.00',0),('L1 / FFL +3.00',3),('L2 / FFL +6.00',6),('R / FFL +9.00',9)]
cols=3;pw,ph=W*S,H*S;img=Image.new('RGB',(cols*pw+(cols+1)*gap,top+2*ph+3*gap+30+18*len(d['deviations'])),'#f4f6f7');g=ImageDraw.Draw(img)
try:
 F=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14);FB=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',22);FS=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
except OSError:F=FB=FS=ImageFont.load_default()
g.text((gap,30),'ONSITE / HERON REACH AS-BUILT',font=FB,fill='#16324a')
g.text((gap,62),f"Drawn from runtime collision boxes and the layered navigation graph. North up, grid 6 m. {len(d['solids'])} solids, {len(d['nodes'])} nav nodes.",font=F,fill='#4b6275')
for i,(title,y) in enumerate(panels):
 ox=gap+(i%cols)*(pw+gap);oy=top+(i//cols)*(ph+gap)
 P=lambda x,z:(ox+x*S,oy+z*S)
 g.rectangle([ox,oy,ox+pw,oy+ph],fill='#ffffff',outline='#9fb2c1')
 for m in range(0,W+1,6):g.line([P(m,0),P(m,H)],fill='#eef2f5')
 for m in range(0,H+1,6):g.line([P(0,m),P(W,m)],fill='#eef2f5')
 for id,mat,x,z,w,dd,b,t in d['solids']:
  if id in d['surfaceIds'] and abs(t-y)<.01 and id!='ground':g.rectangle([P(x,z),P(x+w,z+dd)],fill='#cfe0ee')
 for id,mat,x,z,w,dd,b,t in d['solids']:
  if id=='stair' and y<t<y+3:g.rectangle([P(x,z),P(x+w,z+dd)],fill='#7aa7c7')
 for x,z,ny in d['nodes']:
  if abs(ny-y)<.01:px,pz=P(x,z);g.point((px,pz),fill='#2e8b57')
 for id,mat,x,z,w,dd,b,t in d['solids']:
  if id in d['surfaceIds'] or id.endswith('-cap') or id=='roof':continue
  if b<=y+1.05<=t:
   c='#d2691e' if mat=='steel' else '#5fa8d3' if mat in('glass','lit') else '#b9a27a' if id.startswith('home') else '#7d5a3a' if id=='tree' else '#1d2b36'
   g.rectangle([P(x,z),P(x+w,z+dd)],fill=c)
 g.text((ox+10,oy+8),title,font=FB,fill='#16324a')
lx=gap+2*(pw+gap);ly=top+ph+gap+20
for k,(c,label) in enumerate([('#1d2b36','wall or solid cut at FFL+1.05'),('#d2691e','1.2 m guard, rail or fence'),('#5fa8d3','closed glazing'),('#cfe0ee','floor at this FFL'),('#7aa7c7','stair treads rising to next FFL'),('#2e8b57','walkable nav node'),('#7d5a3a','tree trunk collider')]):
 g.rectangle([lx,ly+k*26,lx+14,ly+k*26+14],fill=c);g.text((lx+22,ly+k*26),label,font=F,fill='#1d2b36')
dy=top+2*ph+2*gap+10
for k,t in enumerate(d['deviations']):g.text((gap,dy+k*18),f'Deviation {k+1}: {t}',font=FS,fill='#4b6275')
img.save(dst,optimize=True);print('wrote',dst,img.size)
