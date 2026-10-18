// Heron Reach B01, step 1: Rowan House (NW block), public cores S1/S2 and their H1/H2 homes.
// Generated from the dimensioned contract, not hand-placed: build-spec.json owns walls, openings,
// stairs and voids; map.json owns gallery/apron rectangles, cover and lights. Map coordinates are
// metres (x east, z south, NW site corner at 0); solids are exported in Three.js space
// (x-72, y, z-60). Render meshes are made from these same boxes, so collision cannot drift.
import spec from '../../docs/maps/heron-reach-32/blueprints/build-spec.json'
import map from '../../docs/maps/heron-reach-32/map.json'
import type {Solid} from './level'

type Rect=[number,number,number,number] // x, z, width, depth
type Box={id:string;x0:number;x1:number;y0:number;y1:number;z0:number;z1:number;mat:string}
type Opening={id:string;kind:string;centre:number;width:number;sill:number;height:number}
type Wall={id:string;axis:string;at:number;start:number;end:number;thickness:number;height:number;openings:Opening[]}

export const BLOCK='NW',OX=72,OZ=60;
/** Step-1 site pad around Rowan House; everything outside is unbuilt. */
export const PAD:Rect=[12,6,54,42];
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

// --- local module frames. Southern instances mirror local z (B01 homeMirror rule). ---
type Frame={x:number;z:number;y:number;depth:number;mirror:boolean};
function place(f:Frame,id:string,lx0:number,lx1:number,y0:number,y1:number,lz0:number,lz1:number,mat:string){
 const [z0,z1]=f.mirror?[f.z+f.depth-lz1,f.z+f.depth-lz0]:[f.z+lz0,f.z+lz1];
 box(id,f.x+lx0,f.x+lx1,f.y+y0,f.y+y1,z0,z1,mat);
}
const localRect=(f:Frame,r:Rect):Rect=>[f.x+r[0],f.mirror?f.z+f.depth-r[1]-r[3]:f.z+r[1],r[2],r[3]];

/** A wall split around its openings: solid below sills, closed glass in windows, lintels above. */
function wall(f:Frame,w:Wall,mat:string,litWindows=false){
 const along=(a0:number,a1:number,y0:number,y1:number,m:string,id:string)=>w.axis==='x'
  ?place(f,id,a0,a1,y0,y1,w.at,w.at+w.thickness,m):place(f,id,w.at,w.at+w.thickness,y0,y1,a0,a1,m);
 let a=w.start;
 for(const o of [...w.openings].sort((p,q)=>p.centre-q.centre)){
  const o0=o.centre-o.width/2,o1=o.centre+o.width/2;along(a,o0,0,w.height,mat,`wall-${w.id}`);
  if(o.kind==='window'){along(o0,o1,0,o.sill,mat,`sill-${o.id}`);along(o0,o1,o.sill,o.sill+o.height,litWindows&&o.id.endsWith('1')?'lit':'glass',`glass-${o.id}`)}
  along(o0,o1,o.sill+o.height,w.height,mat,`lintel-${o.id}`);a=o1;
 }
 along(a,w.end,0,w.height,mat,`wall-${w.id}`);
}

const STOREY=spec.standards.storey,SLAB=spec.standards.slab,GUARD=spec.standards.guard;
type Flight={stair:typeof spec.stairs['ST-P'];f:Frame;fromY:number};
/** Dogleg storey: 9 treads up to a half landing, 9 more to the floor above (10th rise is the landing). */
function flights({stair:s,f,fromY}:Flight,id:string){
 const t=s.stairSlab+s.rise,n=s.treadsPerFlight,z1=s.flightZ+s.flightRun;
 for(let i=1;i<=n;i++){const y=fromY+i*s.rise;place(f,'stair',s.firstFlightX,s.firstFlightX+s.flightWidth,y-t,y,z1-i*s.going,z1-(i-1)*s.going,'concrete')}
 const [hx,hz,hw,hd]=s.halfLanding,hy=fromY+s.risersPerFlight*s.rise;place(f,'landing',hx,hx+hw,hy-s.stairSlab,hy,hz,hz+hd,'concrete');
 for(let i=1;i<=n;i++){const y=hy+i*s.rise;place(f,'stair',s.secondFlightX,s.secondFlightX+s.flightWidth,y-t,y,s.flightZ+(i-1)*s.going,s.flightZ+i*s.going,'concrete')}
}

// --- public cores (ST-P). B1 is not built yet, so S2 starts at G with the ground closed. ---
export const deviations:string[]=['S2 serves B1 in B01; the undercroft is not built in step 1, so S2 starts at G and the ground inside the core stays closed.'];
const cores=spec.cores.filter(c=>c.block===BLOCK);
const coreRects=cores.map(c=>c.rect as Rect);
for(const c of cores){
 const s=spec.stairs['ST-P'],levels=c.levels.filter(y=>y>=0),base=levels[0],top=levels.at(-1)!,[cx,cz]=c.rect,f:Frame={x:cx,z:cz,y:0,depth:6,mirror:c.mirrorZ};
 const [ex,ez]=s.entry,door:Opening={id:'D',kind:'door',centre:ex,width:s.entryWidth,sill:0,height:spec.standards.publicDoorHead};
 for(const y of [...levels]){
  const band={...f,y},h=y===top?STOREY:levels[levels.indexOf(y)+1]-y;
  wall(band,{id:`${c.id}-N`,axis:'x',at:0,start:0,end:6,thickness:s.outerWall,height:h,openings:[]},'brick');
  wall(band,{id:`${c.id}-S`,axis:'x',at:ez-s.outerWall,start:0,end:6,thickness:s.outerWall,height:h,openings:[door]},'brick');
  for(const x of [0,6-s.outerWall])wall(band,{id:`${c.id}-side`,axis:'z',at:x,start:s.outerWall,end:6-s.outerWall,thickness:s.outerWall,height:h,openings:[]},'brick');
  if(y>base){const [lx,lz,lw,ld]=s.floorLanding;place(band,'landing',lx,lx+lw,-SLAB,0,lz,lz+ld,'concrete');place(band,'landing',ex-s.entryWidth/2,ex+s.entryWidth/2,-SLAB,0,ez-s.outerWall,ez,'concrete')}// landing + door threshold
  if(y<top)flights({stair:s,f,fromY:y},c.id);
  // Guard the open well edge at the floor landing; at the top storey the whole flight-1 side is open.
  if(y>base)place(band,`${c.id}-guard`,y===top?s.floorLanding[0]:s.firstFlightX+s.flightWidth,s.secondFlightX,0,GUARD,s.flightZ+s.flightRun-.06,s.flightZ+s.flightRun,'steel');
 }
 // Balustrades between flights run the full height of the well; the cap above the top storey is not walkable.
 for(const x of [s.firstFlightX+s.flightWidth,s.secondFlightX-.06])place({...f,y:base},`${c.id}-balustrade`,x,x+.06,0,top-base+GUARD,s.flightZ,s.flightZ+s.flightRun,'steel');
 place({...f,y:top},`${c.id}-cap`,0,6,spec.standards.clearCeiling,STOREY,0,6,'concrete');
}

// --- homes: H1 at G, H2 maisonettes at +3/+6 with private ST-H stairs ---
const homes=spec.homeInstances.filter(h=>h.id.startsWith(BLOCK+'-'));
const voids:Rect[]=[];
const furnitureHeight:Record<string,[number,string]>={bed:[.55,'fabric'],bath:[.6,'trim'],counter:[.9,'paint'],sofa:[.85,'fabric'],table:[.75,'wood']};
for(const h of homes){
 const m=spec.modules[h.module as 'H1'],f:Frame={x:h.x,z:h.z,y:h.y,depth:m.footprint[1],mirror:h.mirrorZ};
 for(const w of m.walls as Wall[])wall(f,w,['N','S','W','E'].includes(w.id)?'stock':'plaster',['N','S'].includes(w.id));
 for(const [kind,[x,z,wd,d]]of m.furniture as [string,Rect][]){const [ht,mat]=furnitureHeight[kind];place(f,`home-${kind}`,x,x+wd,0,ht,z,z+d,mat)}
 if(m.floorVoid)voids.push(localRect(f,m.floorVoid as Rect));
 if(h.module==='H2-L'){
  const s=spec.stairs['ST-H'],[ox,oz]=s.localOriginInHome,sf:Frame={...f,x:f.x+ox,z:f.mirror?f.z:f.z+oz,depth:f.mirror?f.depth-oz:6};
  flights({stair:s as unknown as typeof spec.stairs['ST-P'],f:sf,fromY:0},`${h.homeId}-private`);
  const x1=s.firstFlightX+s.flightWidth,zEnd=s.flightZ+s.flightRun;
  place(sf,`${h.homeId}-divider`,x1,s.secondFlightX,0,STOREY+GUARD,s.flightZ,zEnd,'plaster');
  place({...sf,y:sf.y+STOREY},`${h.homeId}-guard`,s.floorLanding[0],x1,0,GUARD,zEnd-.06,zEnd,'steel');
 }
}

// --- floors: unioned rectangles, cores and H2 voids subtracted once ---
const surfaces=map.surfaces as unknown as {id:string;level:string;rect:Rect}[];
const pick=(level:string,test:(id:string)=>boolean)=>surfaces.filter(s=>s.level===level&&test(s.id)).map(s=>s.rect);
const ours=(id:string)=>id.startsWith(BLOCK+'-')||/^S[12]-/.test(id);
const blockRect=(map.blocks.find(b=>b.id===BLOCK)!.rect) as Rect;
const northGallery=pick('L1',id=>id==='gallery-north').map(r=>[r[0],r[1],63-r[0],r[3]] as Rect);
deviations.push('The L1 north gallery stops at x=63 (end of the S2 apron) with a temporary guard; the 24 m bridge to Ash House and the west gallery spur are later steps.');
const reserves=(spec.reserves as {id:string;level:string;rect:Rect;height:number}[]).filter(r=>r.id.startsWith(BLOCK+'-'));
const levelY:Record<string,number>={G:0,L1:3,L2:6,R:9};
export const floors:Record<string,Rect[]>={};
for(const level of ['L1','L2','R']){
 const rects=[blockRect,...(level==='L1'?northGallery:[]),...pick(level,id=>ours(id)&&id.includes('apron'))];
 floors[level]=subtractAll(union(rects),[...coreRects,...(level==='L2'?voids:[])]);
 for(const r of floors[level])rectBox('slab',r,levelY[level]-SLAB,levelY[level],'concrete');
 // 1.2 m guards on every exposed edge, outside the clear walk polygon. Edges facing a core,
 // an H2 void or another floor rectangle are joins, not drops.
 const blocked=(x:number,z:number)=>floors[level].some(r=>inside(r,x,z))||coreRects.some(r=>inside(r,x,z))||voids.some(r=>inside(r,x,z));
 const y=levelY[level],step=.05,t=.08;
 for(const [x,z,w,d]of floors[level])for(const [ax,az,dx,dz,nx,nz,len]of [[x,z,1,0,0,-1,w],[x,z+d,1,0,0,1,w],[x,z,0,1,-1,0,d],[x+w,z,0,1,1,0,d]]){
  let run:number|null=null;
  for(let u=0;u<=len+1e-6;u+=step){
   const m=Math.min(u+step/2,len-1e-3),open=u<len-1e-6&&!blocked(ax+dx*m+nx*.04,az+dz*m+nz*.04);
   if(open&&run===null)run=u;
   if(!open&&run!==null){const u0=run-t,u1=u+t;box('guard',dx?ax+u0:(nx>0?ax:ax-t),dx?ax+u1:(nx>0?ax+t:ax),y,y+GUARD,dz?az+u0:(nz>0?az:az-t),dz?az+u1:(nz>0?az+t:az),'steel');run=null}
  }
 }
}
for(const r of reserves)rectBox('reserve',r.rect,levelY[r.level],levelY[r.level]+r.height,'brick');
const padContains=(r:Rect)=>r[0]>=PAD[0]&&r[1]>=PAD[1]&&r[0]+r[2]<=PAD[0]+PAD[2]&&r[1]+r[3]<=PAD[1]+PAD[3];
for(const c of map.cover as {id:string;rect:Rect;height:number;y:number;kind:string}[])if(padContains(c.rect))rectBox(`cover-${c.id}`,c.rect,c.y,c.y+c.height,c.kind.includes('planter')?'concrete':c.kind.includes('privacy')?'stock':'brick');
rectBox('ground',PAD,-.4,0,'asphalt');
// Temporary hoarding around the step-1 pad: the rest of the 144 x 120 m site is not built yet.
for(const [x0,x1,z0,z1]of [[PAD[0]-.3,PAD[0],PAD[1],PAD[1]+PAD[3]],[PAD[0]+PAD[2],PAD[0]+PAD[2]+.3,PAD[1],PAD[1]+PAD[3]],[PAD[0]-.3,PAD[0]+PAD[2]+.3,PAD[1]-.3,PAD[1]],[PAD[0]-.3,PAD[0]+PAD[2]+.3,PAD[1]+PAD[3],PAD[1]+PAD[3]+.3]])box('hoarding',x0,x1,0,2.4,z0,z1,'paint');
deviations.push('A 2.4 m site hoarding closes the step-1 pad; it is removed as neighbouring blocks are built.');

const toSolid=(b:Box):Solid=>({id:b.id,x:(b.x0+b.x1)/2-OX,y:(b.y0+b.y1)/2,z:(b.z0+b.z1)/2-OZ,w:b.x1-b.x0,h:b.y1-b.y0,d:b.z1-b.z0,mat:b.mat});
export const solids:Solid[]=boxes.map(toSolid);
/** Ids whose top faces are floors. Everything else is wall, guard, furniture or cap. */
export const surfaceIds=['ground','slab','stair','landing'];
const at=(x:number,y:number,z:number)=>({x:x-OX,y,z:z-OZ});
export const bounds={minX:PAD[0]-OX,minZ:PAD[1]-OZ,maxX:PAD[0]+PAD[2]-OX,maxZ:PAD[1]+PAD[3]-OZ};
export const spawn={...at(36,0,46),y:.04};
export const botSpawns=[at(42,3.04,19.5),at(42,6.04,32.5),at(36,9.04,27)];
/** Temporary objective in Rowan's ground arcade; floor-aware so the galleries above never count. */
export const capture={...at(42,0,25),radius:3.5,minY:-.5,maxY:1.5,label:'ROWAN ARCADE'};
export const lights=(map.lights as {id:string;x:number;z:number;y:number;kind:string}[]).filter(l=>padContains([l.x,l.z,0,0])).map(l=>({...at(l.x,l.y,l.z),kind:l.kind}));
export const signs=[{text:'ROWAN HOUSE',...at(42,2.5,39.02),w:4},{text:'S1 / LEVELS G—R',...at(27,2.65,42.02),w:1.6},{text:'S2 / LEVELS G—R',...at(57,2.65,42.02),w:1.6}];
export const overview={from:at(14,17,60),to:at(40,3,28)};
export const toMap=(x:number,y:number,z:number)=>({x:x+OX,y,z:z+OZ});
export {at as fromMap};
