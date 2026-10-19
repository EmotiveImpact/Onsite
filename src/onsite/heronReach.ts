// Heron Reach B01: the full 144 x 120 m estate shell. Four blocks, eight public cores (S2/S3/S6/S7
// reach the B1 undercroft), sixteen H1/H2 homes, the continuous +3 gallery with its two bridges,
// four +6 islands, the NW and SE roof terraces, six shops, the Cage and the landscape colliders.
// Generated from the dimensioned contract, not hand-placed: build-spec.json owns walls, openings,
// stairs and voids; map.json owns blocks, gallery/apron rectangles, cover, trees and lights. Map
// coordinates are metres (x east, z south, NW site corner at 0); solids are exported in Three.js
// space (x-72, y, z-60). The Blender art is built around these boxes and never replaces them.
import spec from '../../docs/maps/heron-reach-32/blueprints/build-spec.json'
import map from '../../docs/maps/heron-reach-32/map.json'
import type {Solid} from './level'
import {planDressing} from './heronReachDressing'

type Rect=[number,number,number,number] // x, z, width, depth
type Box={id:string;x0:number;x1:number;y0:number;y1:number;z0:number;z1:number;mat:string}
type Opening={id:string;kind:string;centre:number;width:number;sill:number;height:number}
type Wall={id:string;axis:string;at:number;start:number;end:number;thickness:number;height:number;openings:Opening[]}
type P3={x:number;y:number;z:number}

export const OX=72,OZ=60;
export const SITE:Rect=[0,0,map.bounds[0],map.bounds[1]];
const boxes:Box[]=[];
const box=(id:string,x0:number,x1:number,y0:number,y1:number,z0:number,z1:number,mat:string)=>{if(x1-x0>.001&&y1-y0>.001&&z1-z0>.001)boxes.push({id,x0,x1,y0,y1,z0,z1,mat})};
const rectBox=(id:string,r:Rect,y0:number,y1:number,mat:string)=>box(id,r[0],r[0]+r[2],y0,y1,r[1],r[1]+r[3],mat);

// --- rectangle algebra for floor unions, core cut-outs and voids ---
const overlaps=(a:Rect,b:Rect)=>a[0]<b[0]+b[2]-1e-6&&b[0]<a[0]+a[2]-1e-6&&a[1]<b[1]+b[3]-1e-6&&b[1]<a[1]+a[3]-1e-6;
function subtract(a:Rect,b:Rect):Rect[]{
 if(!overlaps(a,b))return [a];
 const [ax,az,aw,ad]=a,ax1=ax+aw,az1=az+ad,bx0=Math.max(ax,b[0]),bx1=Math.min(ax1,b[0]+b[2]),bz0=Math.max(az,b[1]),bz1=Math.min(az1,b[1]+b[3]);
 return ([[ax,az,aw,bz0-az],[ax,bz1,aw,az1-bz1],[ax,bz0,bx0-ax,bz1-bz0],[bx1,bz0,ax1-bx1,bz1-bz0]] as Rect[]).filter(r=>r[2]>1e-6&&r[3]>1e-6);
}
const subtractAll=(rects:Rect[],holes:Rect[])=>holes.reduce((acc,h)=>acc.flatMap(r=>subtract(r,h)),rects);
/** Disjoint union: later rectangles lose the area earlier ones already cover. */
const union=(rects:Rect[])=>rects.reduce<Rect[]>((acc,r)=>[...acc,...subtractAll([r],acc)],[]);
const inside=(r:Rect,x:number,z:number)=>x>r[0]&&x<r[0]+r[2]&&z>r[1]&&z<r[1]+r[3];

// --- semantic record for the Blender art build (same coordinates as the boxes) ---
type ArtOpening={kind:string;x:number;z:number;y:number;axis:'x'|'z';normal:1|-1;width:number;sill:number;height:number;wall:number;owner:string;lit?:boolean};
export const art={openings:[] as ArtOpening[],guards:[] as {level:string;y:number;x0:number;z0:number;x1:number;z1:number;nx:number;nz:number}[],
 columns:[] as {x:number;z:number;size:number;height:number}[],cores:[] as {id:string;rect:Rect;mirror:boolean;levels:number[]}[],
 homes:[] as {id:string;module:string;x:number;z:number;y:number;mirror:boolean}[],undercroftWalls:[] as {x0:number;z0:number;x1:number;z1:number;nx:number;nz:number}[]};

// --- local module frames. Southern instances mirror local z (B01 homeMirror rule). ---
type Frame={x:number;z:number;y:number;depth:number;mirror:boolean};
const worldZ=(f:Frame,lz:number)=>f.mirror?f.z+f.depth-lz:f.z+lz;
function place(f:Frame,id:string,lx0:number,lx1:number,y0:number,y1:number,lz0:number,lz1:number,mat:string){
 const [z0,z1]=f.mirror?[f.z+f.depth-lz1,f.z+f.depth-lz0]:[f.z+lz0,f.z+lz1];
 box(id,f.x+lx0,f.x+lx1,f.y+y0,f.y+y1,z0,z1,mat);
}
const localRect=(f:Frame,r:Rect):Rect=>[f.x+r[0],f.mirror?f.z+f.depth-r[1]-r[3]:f.z+r[1],r[2],r[3]];

/** A wall split around its openings: solid below sills, closed glass in windows, lintels above. */
function wall(f:Frame,w:Wall,mat:string,owner:string,exterior=false,litWindows=false,width=9){
 const along=(a0:number,a1:number,y0:number,y1:number,m:string,id:string)=>w.axis==='x'
  ?place(f,id,a0,a1,y0,y1,w.at,w.at+w.thickness,m):place(f,id,w.at,w.at+w.thickness,y0,y1,a0,a1,m);
 // Outward normal in world space: walls in the first half of the module face local -axis.
 const span=w.axis==='x'?f.depth:width,outward=(w.at<span/2?-1:1)*(w.axis==='x'&&f.mirror?-1:1) as 1|-1;
 let a=w.start;
 for(const o of [...w.openings].sort((p,q)=>p.centre-q.centre)){
  const o0=o.centre-o.width/2,o1=o.centre+o.width/2;along(a,o0,0,w.height,mat,`wall-${w.id}`);
  const lit=litWindows&&o.id.endsWith('1');
  if(o.kind==='window'){along(o0,o1,0,o.sill,mat,`sill-${o.id}`);along(o0,o1,o.sill,o.sill+o.height,lit?'lit':'glass',`glass-${o.id}`)}
  along(o0,o1,o.sill+o.height,w.height,mat,`lintel-${o.id}`);a=o1;
  const mid=w.at+w.thickness/2,c={x:w.axis==='x'?f.x+o.centre:f.x+mid,z:w.axis==='x'?worldZ(f,mid):worldZ(f,o.centre)};
  art.openings.push({kind:exterior?o.kind:`inner-${o.kind}`,...c,y:f.y,axis:w.axis as 'x'|'z',normal:outward,width:o.width,sill:o.sill,height:o.height,wall:w.thickness,owner,lit});
 }
 along(a,w.end,0,w.height,mat,`wall-${w.id}`);
}

const STOREY=spec.standards.storey,SLAB=spec.standards.slab,GUARD=spec.standards.guard,CEIL=spec.standards.clearCeiling;
export const levelY:Record<string,number>={B1:-3,G:0,L1:3,L2:6,R:9};
type Flight={stair:typeof spec.stairs['ST-P'];f:Frame;fromY:number};
/** Dogleg storey: 9 treads up to a half landing, 9 more to the floor above (10th rise is the landing). */
function flights({stair:s,f,fromY}:Flight){
 const t=s.stairSlab+s.rise,n=s.treadsPerFlight,z1=s.flightZ+s.flightRun;
 for(let i=1;i<=n;i++){const y=fromY+i*s.rise;place(f,'stair',s.firstFlightX,s.firstFlightX+s.flightWidth,y-t,y,z1-i*s.going,z1-(i-1)*s.going,'concrete')}
 const [hx,hz,hw,hd]=s.halfLanding,hy=fromY+s.risersPerFlight*s.rise;place(f,'landing',hx,hx+hw,hy-s.stairSlab,hy,hz,hz+hd,'concrete');
 for(let i=1;i<=n;i++){const y=hy+i*s.rise;place(f,'stair',s.secondFlightX,s.secondFlightX+s.flightWidth,y-t,y,s.flightZ+(i-1)*s.going,s.flightZ+i*s.going,'concrete')}
}

export const deviations:string[]=[];
const cores=spec.cores;
const coreRect=(id:string)=>cores.find(c=>c.id===id)!.rect as Rect;
const coresAt=(y:number)=>cores.filter(c=>c.levels.includes(y)).map(c=>c.rect as Rect);
/** Every door portal at ground level; columns keep clear of them. */
const groundDoors:{x:number;z:number}[]=[];

// --- public cores (ST-P), every served storey from B1 or G to the top ---
for(const c of cores){
 const s=spec.stairs['ST-P'],levels=c.levels,base=levels[0],top=levels.at(-1)!,[cx,cz]=c.rect,f:Frame={x:cx,z:cz,y:0,depth:6,mirror:c.mirrorZ};
 const [ex,ez]=s.entry,door:Opening={id:'D',kind:'door',centre:ex,width:s.entryWidth,sill:0,height:spec.standards.publicDoorHead};
 art.cores.push({id:c.id,rect:c.rect as Rect,mirror:c.mirrorZ,levels});
 groundDoors.push({x:cx+ex,z:worldZ(f,ez)});
 for(const y of levels){
  const band={...f,y},h=y===top?STOREY:levels[levels.indexOf(y)+1]-y;
  wall(band,{id:`${c.id}-N`,axis:'x',at:0,start:0,end:6,thickness:s.outerWall,height:h,openings:[]},'brick',c.id,true,false,6);
  wall(band,{id:`${c.id}-S`,axis:'x',at:ez-s.outerWall,start:0,end:6,thickness:s.outerWall,height:h,openings:[door]},'brick',c.id,true,false,6);
  for(const x of [0,6-s.outerWall])wall(band,{id:`${c.id}-side`,axis:'z',at:x,start:s.outerWall,end:6-s.outerWall,thickness:s.outerWall,height:h,openings:[]},'brick',c.id,true,false,6);
  if(y>base){const [lx,lz,lw,ld]=s.floorLanding;place(band,'landing',lx,lx+lw,-SLAB,0,lz,lz+ld,'concrete');place(band,'landing',ex-s.entryWidth/2,ex+s.entryWidth/2,-SLAB,0,ez-s.outerWall,ez,'concrete')}// landing + door threshold
  if(y<top)flights({stair:s,f,fromY:y});
  // Guard the open well edge at the floor landing; at the top storey the whole flight-1 side is open.
  if(y>base)place(band,`${c.id}-guard`,y===top?s.floorLanding[0]:s.firstFlightX+s.flightWidth,s.secondFlightX,0,GUARD,s.flightZ+s.flightRun-.06,s.flightZ+s.flightRun,'steel');
 }
 // Balustrades between flights run the full height of the well; the cap above the top storey is not walkable.
 for(const x of [s.firstFlightX+s.flightWidth,s.secondFlightX-.06])place({...f,y:base},`${c.id}-balustrade`,x,x+.06,0,top-base+GUARD,s.flightZ,s.flightZ+s.flightRun,'steel');
 place({...f,y:top},`${c.id}-cap`,0,6,CEIL,STOREY,0,6,'concrete');
}

// --- homes: H1 at G, H2 maisonettes at +3/+6 with private ST-H stairs; southern blocks mirror ---
const voids:Rect[]=[];
const furnitureHeight:Record<string,[number,string]>={bed:[.55,'fabric'],bath:[.6,'trim'],counter:[.9,'paint'],sofa:[.85,'fabric'],table:[.75,'wood']};
for(const h of spec.homeInstances){
 const m=spec.modules[h.module as 'H1'],f:Frame={x:h.x,z:h.z,y:h.y,depth:m.footprint[1],mirror:h.mirrorZ};
 art.homes.push({id:h.id,module:h.module,x:h.x,z:h.z,y:h.y,mirror:h.mirrorZ});
 for(const w of m.walls as Wall[]){const ext=['N','S','W','E'].includes(w.id);wall(f,w,ext?'stock':'plaster',h.homeId,ext,['N','S'].includes(w.id))}
 if(h.y===0)for(const w of m.walls as Wall[])if(['N','S'].includes(w.id))for(const o of w.openings)if(o.kind==='door')groundDoors.push({x:f.x+o.centre,z:worldZ(f,w.at+w.thickness/2)});
 for(const [kind,[x,z,wd,d]]of m.furniture as [string,Rect][]){const [ht,mat]=furnitureHeight[kind];place(f,`home-${kind}`,x,x+wd,0,ht,z,z+d,mat)}
 if(m.floorVoid)voids.push(localRect(f,m.floorVoid as Rect));
 if(h.module==='H2-L'){
  const s=spec.stairs['ST-H'],[ox,oz]=s.localOriginInHome,sf:Frame={...f,x:f.x+ox,z:f.mirror?f.z:f.z+oz,depth:f.mirror?f.depth-oz:6};
  flights({stair:s as unknown as typeof spec.stairs['ST-P'],f:sf,fromY:0});
  const x1=s.firstFlightX+s.flightWidth,zEnd=s.flightZ+s.flightRun;
  place(sf,`${h.homeId}-divider`,x1,s.secondFlightX,0,STOREY+GUARD,s.flightZ,zEnd,'plaster');
  place({...sf,y:sf.y+STOREY},`${h.homeId}-guard`,s.floorLanding[0],x1,0,GUARD,zEnd-.06,zEnd,'steel');
 }
}

// --- shops and service buildings: 2.8 m shells with explicit portals, closed shopfront glazing ---
type Shop=typeof spec.shops[number];
const shopRects=spec.shops.map(s=>s.rect as Rect);
const galleryRects=(map.surfaces as unknown as {id:string;level:string;rect:Rect}[]).filter(s=>s.level==='L1'&&s.id.startsWith('gallery-')).map(s=>s.rect);
for(const sh of spec.shops as Shop[]){
 const [x,z,w,d]=sh.rect as Rect,t=sh.wall,f:Frame={x,z,y:0,depth:d,mirror:false};
 const sides:Record<string,{axis:'x'|'z';at:number;len:number}>={N:{axis:'x',at:0,len:w},S:{axis:'x',at:d-t,len:w},W:{axis:'z',at:0,len:d},E:{axis:'z',at:w-t,len:d}};
 for(const [side,{axis,at,len}]of Object.entries(sides)){
  const openings:Opening[]=sh.doorOpenings.filter(o=>o.side===side).map(o=>({id:o.id,kind:'door',centre:o.offset,width:o.width,sill:0,height:o.height}));
  if(sh.glazing.side===side)sh.glazing.spans.forEach(([a,b],i)=>openings.push({id:`G${i+1}`,kind:'window',centre:(a+b)/2,width:b-a,sill:sh.glazing.sill,height:sh.glazing.height}));
  const start=axis==='z'?t:0,end=axis==='z'?len-t:len;
  // Shop walls run to the underside of the roof slab; the 3.0 m total matches B500.
  wall(f,{id:`${sh.id}-${side}`,axis,at,start,end,thickness:t,height:CEIL,openings},'brick',sh.id,true,true,w);
  for(const o of openings)if(o.kind==='door')groundDoors.push(axis==='x'?{x:x+o.centre,z:z+at+t/2}:{x:x+at+t/2,z:z+o.centre});
 }
 for(const r of subtractAll([sh.rect as Rect],galleryRects))rectBox('roof',r,CEIL,STOREY,'concrete');
}
deviations.push('Shop and service shells are 2.8 m walls under a 0.2 m roof slab (3.0 m overall, as B500). Where the +3 west and east galleries pass over a shop, the gallery slab is the roof.');

// --- floors: unioned rectangles, cores and H2 voids subtracted once ---
const surfaces=map.surfaces as unknown as {id:string;level:string;rect:Rect;kind:string}[];
const pick=(level:string)=>surfaces.filter(s=>s.level===level).map(s=>s.rect);
const blocks=map.blocks as unknown as {id:string;name:string;rect:Rect;roofPlayable:boolean}[];
const blockRects=blocks.map(b=>b.rect);
export const floors:Record<string,Rect[]>={};
floors.B1=union(pick('B1'));
floors.L1=subtractAll(union([...blockRects,...pick('L1')]),coresAt(3));
floors.L2=subtractAll(union([...blockRects,...pick('L2')]),[...coresAt(6),...voids]);
floors.R=subtractAll(union([...blocks.filter(b=>b.roofPlayable).map(b=>b.rect),...pick('R')]),coresAt(9));
const b1Cores=cores.filter(c=>c.levels[0]<0).map(c=>c.rect as Rect);
floors.G=subtractAll([SITE],b1Cores);
// The ground is one 200 mm slab over the undercroft, holed only where a core descends to B1.
for(const r of floors.G)rectBox('ground',r,-SLAB,0,'asphalt');
for(const r of floors.B1)rectBox('slab',r,levelY.B1-SLAB,levelY.B1,'concrete');
for(const level of ['L1','L2','R'])for(const r of floors[level])rectBox('slab',r,levelY[level]-SLAB,levelY[level],'concrete');
// Non-playable roofs (Ash, Birch) close the top of their blocks; nothing reaches them.
for(const b of blocks.filter(b=>!b.roofPlayable))for(const r of subtractAll([b.rect],coresAt(9)))rectBox('roof',r,levelY.R-SLAB,levelY.R,'concrete');

/** Exposed edges of a floor set, sampled every 5 cm and tested 4 cm outside the edge. */
function exposedRuns(rects:Rect[],blocked:(x:number,z:number)=>boolean){
 const runs:{u0:number;u1:number;ax:number;az:number;dx:number;dz:number;nx:number;nz:number}[]=[],step=.05;
 for(const [x,z,w,d]of rects)for(const [ax,az,dx,dz,nx,nz,len]of [[x,z,1,0,0,-1,w],[x,z+d,1,0,0,1,w],[x,z,0,1,-1,0,d],[x+w,z,0,1,1,0,d]]){
  let run:number|null=null;
  for(let u=0;u<=len+1e-6;u+=step){
   const m=Math.min(u+step/2,len-1e-3),open=u<len-1e-6&&!blocked(ax+dx*m+nx*.04,az+dz*m+nz*.04);
   if(open&&run===null)run=u;
   if(!open&&run!==null){runs.push({u0:run,u1:Math.min(u,len),ax,az,dx,dz,nx,nz});run=null}
  }
 }
 return runs;
}
const insideAny=(rs:Rect[],x:number,z:number)=>rs.some(r=>inside(r,x,z));
// 1.2 m guards on every exposed upper edge, outside the clear walk polygon. Edges facing a core,
// an H2 void or another floor rectangle are joins, not drops.
const allCores=cores.map(c=>c.rect as Rect);
for(const level of ['L1','L2','R']){
 const y=levelY[level],t=.08,blocked=(x:number,z:number)=>insideAny(floors[level],x,z)||insideAny(allCores,x,z)||insideAny(voids,x,z);
 for(const r of exposedRuns(floors[level],blocked)){
  const {u0:a,u1:b,ax,az,dx,dz,nx,nz}=r,u0=a-t,u1=b+t;
  box('guard',dx?ax+u0:(nx>0?ax:ax-t),dx?ax+u1:(nx>0?ax+t:ax),y,y+GUARD,dz?az+u0:(nz>0?az:az-t),dz?az+u1:(nz>0?az+t:az),'steel');
  art.guards.push({level,y,x0:ax+dx*a,z0:az+dz*a,x1:ax+dx*b,z1:az+dz*b,nx,nz});
  // Columns carry exposed +3 edges down to open ground, on a 6 m grid, clear of every G doorway.
  if(level==='L1'){
   const len=b-a,spots=new Set<number>();if(len>=2){spots.add(a+.25);spots.add(b-.25)}
   for(let u=Math.ceil((dx?ax+a:az+a)/6)*6-(dx?ax:az);u<b-1;u+=6)if(u>a+1)spots.add(u);
   for(const u of spots){
    const cx=ax+dx*u-nx*.25,cz=az+dz*u-nz*.25,bridge=(cz>36&&cz<39||cz>81&&cz<84)&&cx>60&&cx<84;
    // Core aprons cantilever from their cores, so nothing stands within 3.2 m of a core.
    const nearCore=allCores.some(([x,z,w,d])=>cx>x-3.2&&cx<x+w+3.2&&cz>z-3.2&&cz<z+d+3.2);
    if(art.columns.some(c=>Math.hypot(c.x-cx,c.z-cz)<2.4)||bridge||nearCore||insideAny(shopRects,cx,cz)||groundDoors.some(p=>Math.hypot(p.x-cx,p.z-cz)<1.8))continue;
    box('column',cx-.2,cx+.2,0,CEIL,cz-.2,cz+.2,'concrete');art.columns.push({x:cx,z:cz,size:.4,height:CEIL});
   }
  }
 }
}
deviations.push('Concrete columns (0.4 m square, 6 m grid) carry the exposed +3 slab edges down to open ground. They are not drawn in B01; each has collision, none sits within 1.8 m of a ground doorway, core aprons cantilever, and the two 24 m bridges stay column-free.');
// The undercroft is enclosed: 200 mm walls outside the B1 union, from FFL to the underside of the ground slab.
{
 const t=.2,blocked=(x:number,z:number)=>insideAny(floors.B1,x,z)||insideAny(b1Cores,x,z);
 for(const {u0,u1,ax,az,dx,dz,nx,nz}of exposedRuns(floors.B1,blocked)){
  box('wall-B1',dx?ax+u0-t:(nx>0?ax:ax-t),dx?ax+u1+t:(nx>0?ax+t:ax),levelY.B1,-SLAB,dz?az+u0-t:(nz>0?az:az-t),dz?az+u1+t:(nz>0?az+t:az),'concrete');
  art.undercroftWalls.push({x0:ax+dx*u0,z0:az+dz*u0,x1:ax+dx*u1,z1:az+dz*u1,nx,nz});
 }
}

// --- reserves, cover, trees, the Cage and the site boundary ---
const reserves=spec.reserves as {id:string;level:string;rect:Rect;height:number}[];
for(const r of reserves)rectBox('reserve',r.rect,levelY[r.level],levelY[r.level]+r.height,'brick');
export const cover=map.cover as unknown as {id:string;rect:Rect;height:number;y:number;kind:string}[];
for(const c of cover)rectBox(`cover-${c.id}`,c.rect,c.y,c.y+c.height,c.kind.includes('planter')?'concrete':c.kind.includes('privacy')?'stock':'brick');
export const trees=map.trees as unknown as {id:string;x:number;z:number;canopyRadius:number;trunkRadius:number;height:number;canopyBase:number}[];
// Trunks are measured colliders (square inscribed in the 0.22 m trunk plus bark); canopies are cosmetic.
for(const t of trees)box('tree',t.x-.2,t.x+.2,0,4,t.z-.2,t.z+.2,'wood');
// The Cage: 30 x 20 m, 2.6 m weld-mesh fence with 4 m gates at the side midpoints. The mesh blocks
// movement but is visually porous; Encounter tags 'fence' so bullets and bot sight pass through.
export const cage={rect:[57,50,30,20] as Rect,height:2.6,gate:4};
{
 const [x,z,w,d]=cage.rect,h=cage.height,g=cage.gate/2,t=.06,mx=x+w/2,mz=z+d/2;
 for(const zz of [z,z+d]){box('fence',x,mx-g,0,h,zz-t/2,zz+t/2,'steel');box('fence',mx+g,x+w,0,h,zz-t/2,zz+t/2,'steel')}
 for(const xx of [x,x+w]){box('fence',xx-t/2,xx+t/2,0,h,z,mz-g,'steel');box('fence',xx-t/2,xx+t/2,0,h,mz+g,z+d,'steel')}
 // Five-a-side goals stand against the end fences beside the end gates, rotationally symmetric.
 for(const [gx,gz]of [[x+.06,mz-5.5],[x+w-1.26,mz+5.5]])box('goal',gx,gx+1.2,0,1.25,gz-1.85,gz+1.85,'steel');
}
deviations.push('Two five-a-side goals stand against the Cage end fences, offset 5.5 m from the end gates so the B500 gate routes stay open.');
// Site boundary: a 3 m brick wall with railings just outside the 144 x 120 m site.
{const [x,z,w,d]=SITE,t=.3;for(const [x0,x1,z0,z1]of [[x-t,x,z-t,z+d+t],[x+w,x+w+t,z-t,z+d+t],[x,x+w,z-t,z],[x,x+w,z+d,z+d+t]])box('boundary',x0,x1,0,3,z0,z1,'stock')}
deviations.push('A 3 m boundary wall with railings encloses the 144 x 120 m site; the street and skyline beyond are render-only.');
deviations.push('The Cage fence (2.6 m, four 4 m gates) blocks movement but not bullets or bot sight, matching the B500 note that the mesh is visually porous.');

// Dressing: kit placements from the same layout; large props add their own box colliders.
export const dressing=planDressing({site:SITE,boxes,floorsG:floors.G,cores:art.cores,
 doors:art.openings.filter(o=>o.kind==='door'),shops:spec.shops as unknown as Parameters<typeof planDressing>[0]['shops'],blocks:blocks as unknown as Parameters<typeof planDressing>[0]['blocks'],
 lights:map.lights as {id:string;x:number;y:number;z:number;kind:string}[],trees,cage,planting:map.planting as unknown as {id:string;rect:Rect}[],
 objectives:map.objectives as {x:number;z:number;radius:number}[],spawns:map.spawns as unknown as {rect:Rect;positions:{x:number;z:number}[]}[],stairs:art.cores.map(c=>c.rect),
 wetAreas:map.wetAreas as unknown as {rect:Rect}[],undercroftWalls:art.undercroftWalls});
boxes.push(...dressing.colliders);
deviations.push(`Dressing adds ${dressing.colliders.length} prop colliders (lamps, bollards, benches, bins and bin stores, shop fittings, roof plant, a fenced substation, sign posts, grit bins, a dumped sofa and washing airers); door arcs, spawns, stair entries and objective rings stay clear.`);

const toSolid=(b:Box):Solid=>({id:b.id,x:(b.x0+b.x1)/2-OX,y:(b.y0+b.y1)/2,z:(b.z0+b.z1)/2-OZ,w:b.x1-b.x0,h:b.y1-b.y0,d:b.z1-b.z0,mat:b.mat});
export const solids:Solid[]=boxes.map(toSolid);
/** Ids whose top faces are floors. Everything else is wall, guard, furniture, roof or cap. */
export const surfaceIds=['ground','slab','stair','landing'];
const at=(x:number,y:number,z:number):P3=>({x:x-OX,y,z:z-OZ});
export const bounds={minX:SITE[0]-OX,minZ:SITE[1]-OZ,maxX:SITE[0]+SITE[2]-OX,maxZ:SITE[1]+SITE[3]-OZ};
// Bots first: the player stages in the west yard; opponents hold the east yard, objectives and upper routes.
export const spawn={...at(8,0,60),y:.04,yaw:-Math.PI/2};
export const botSpawns=[at(134,.04,56),at(80,.04,66),at(72,3.04,37.5),at(72,.04,24),at(102,9.04,93),at(72,-2.96,63)];
export const botNames=['EAST YARD','THE CAGE','NORTH BRIDGE','GARDEN COURT','CEDAR ROOF','UNDERCROFT'];
export const objectives=(map.objectives as {id:string;name:string;x:number;z:number;radius:number}[]).map(o=>({...at(o.x,0,o.z),id:o.id,radius:o.radius,minY:-.5,maxY:1.5,label:o.name}));
/** The Cage is the round's capture; floor-aware so the undercroft below it never counts. */
export const capture=objectives.find(o=>o.id==='B')!;
/** Every lamp, wall light and ceiling strip from the dressing plan, for the runtime light pool. */
export const lampAnchors=dressing.anchors.map(a=>({...at(a.x,a.y,a.z),kind:a.kind}));
export const lights=(map.lights as {id:string;x:number;z:number;y:number;kind:string}[]).map(l=>({...at(l.x,l.y,l.z),kind:l.kind}));
export const signs=[
 ...blocks.map(b=>{const south=b.rect[1]>60,z=south?b.rect[1]-.02:b.rect[1]+b.rect[3]+.02;return {text:b.name,...at(b.rect[0]+b.rect[2]/2,2.5,z),w:4,ry:south?Math.PI:0}}),
 // Shop fascias over the north shopfronts.
 ...(spec.shops as unknown as {name:string;rect:Rect}[]).map(sh=>({text:sh.name,...at(sh.rect[0]+sh.rect[2]/2,2.52,sh.rect[1]-.03),w:Math.min(5.2,sh.rect[2]-.8),ry:Math.PI})),
 ...cores.map(c=>{const [cx,cz]=c.rect,south=c.mirrorZ,levels=c.levels.map(y=>Object.keys(levelY).find(k=>levelY[k]===y)).join(' / ');return {text:`${c.id} / ${levels}`,...at(cx+3,2.65,south?cz-.02:cz+6.02),w:1.6,ry:south?Math.PI:0}}),
];
export const overview={from:at(-14,34,128),to:at(70,0,58)};
export const toMap=(x:number,y:number,z:number)=>({x:x+OX,y,z:z+OZ});
export {at as fromMap};
export const layout={site:SITE,levelY,floors,voids,cores:art.cores,homes:art.homes,openings:art.openings,guards:art.guards,columns:art.columns,undercroftWalls:art.undercroftWalls,
 shops:spec.shops,blocks,cover,trees,cage,planting:map.planting,wetAreas:map.wetAreas,detailZones:map.detailZones,lights:map.lights,objectives:map.objectives,spawns:map.spawns,reserves,
 surfaces:map.surfaces,stairs:spec.stairs,deviations,dressing:dressing.items,anchors:dressing.anchors};
