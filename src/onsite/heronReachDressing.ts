// Heron Reach dressing plan: where the Blender kits' lamps, street furniture, shop fit-outs, Cage
// panels, cars, trees and litter stand. Deterministic, generated from the same layout as the shell.
// Anything big enough to stop a player gets an explicit box collider from the props manifest, and
// placements keep door arcs, spawn positions, stair entries and objective rings clear. Render-only
// items (litter, wall fittings, the street beyond the boundary) never collide.
import kit from '../../assets/blender/heron-reach/props-manifest.json'

type Rect=[number,number,number,number]
export type DressBox={id:string;x0:number;x1:number;y0:number;y1:number;z0:number;z1:number;mat:string}
/** One instance, in map coordinates (x east, z south, y up). ry turns the asset's front (+z, south) about y. */
export type Placement={asset:string;x:number;y:number;z:number;ry:number;sx?:number;collide:boolean}
export type Anchor={x:number;y:number;z:number;kind:string}
export type DressingInput={
 site:Rect;boxes:DressBox[];floorsG:Rect[];
 cores:{id:string;rect:Rect;mirror:boolean;levels:number[]}[];
 doors:{x:number;z:number;y:number;axis:'x'|'z';normal:1|-1;width:number;height:number;wall:number;owner:string}[];
 shops:{id:string;name:string;rect:Rect;wall:number;doorOpenings:{side:string;offset:number;width:number}[]}[];
 blocks:{id:string;rect:Rect;roofPlayable:boolean;arcade?:Rect}[];
 lights:{id:string;x:number;y:number;z:number;kind:string}[];
 trees:{id:string;x:number;z:number}[];cage:{rect:Rect;height:number;gate:number};
 planting:{id:string;rect:Rect}[];objectives:{x:number;z:number;radius:number}[];
 spawns:{rect:Rect;positions:{x:number;z:number}[]}[];stairs:Rect[];
 wetAreas:{rect:Rect}[];undercroftWalls:{x0:number;z0:number;x1:number;z1:number;nx:number;nz:number}[];
}
export type DecalPlan={kind:'puddle'|'graffiti';x:number;y:number;z:number;w:number;h:number;ry:number;cell?:number}

type Collider={type:string;size?:number[];radius?:number;height?:number;center:number[]}
const assets=new Map((kit.assets as {name:string;collider:Collider|Collider[]|null;needsCollision:boolean}[]).map(a=>[a.name,a]));

function rng(seed:number){let s=seed>>>0;return()=>{s=(s+0x6d2b79f5)>>>0;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296}}

/** Box colliders for a placement. Blender +Y is map -z; rotation is about y in quarter turns only. */
export function collidersFor(p:Placement,id:string):DressBox[]{
 const a=assets.get(p.asset);if(!a||!p.collide||!a.collider)return [];
 const list=Array.isArray(a.collider)?a.collider:[a.collider],q=Math.round(p.ry/(Math.PI/2))&3,out:DressBox[]=[];
 for(const c of list){
  let [w,d]=c.type==='cylinder'?[c.radius!*2,c.radius!*2]:[c.size![0]*(p.sx??1),c.size![1]],h=c.type==='cylinder'?c.height!:c.size![2];
  let [ox,oz]=[c.center[0]*(p.sx??1),-c.center[1]];const oy=c.center[2];
  for(let i=0;i<q;i++){[ox,oz]=[oz,-ox];[w,d]=[d,w]}
  out.push({id,x0:p.x+ox-w/2,x1:p.x+ox+w/2,y0:p.y+oy-h/2,y1:p.y+oy+h/2,z0:p.z+oz-d/2,z1:p.z+oz+d/2,mat:'steel'});
 }
 return out;
}

export function planDressing(L:DressingInput){
 const R=rng(1938),items:Placement[]=[],anchors:Anchor[]=[],blockers:DressBox[]=[];
 const [SX,SZ,SW,SD]=L.site;
 const solid=L.boxes.filter(b=>!['ground','slab','landing','stair'].includes(b.id));
 const hits=(x0:number,x1:number,y0:number,y1:number,z0:number,z1:number,list:DressBox[])=>list.some(b=>b.x0<x1&&b.x1>x0&&b.y0<y1&&b.y1>y0&&b.z0<z1&&b.z1>z0);
 const keepClear:{x:number;z:number;y:number;r:number}[]=[
  ...L.doors.map(d=>({x:d.x+(d.axis==='x'?0:d.normal*1),z:d.z+(d.axis==='x'?d.normal*1:0),y:d.y,r:d.width/2+1.1})),
  ...L.doors.map(d=>({x:d.x-(d.axis==='x'?0:d.normal*1),z:d.z-(d.axis==='x'?d.normal*1:0),y:d.y,r:d.width/2+1.1})),
  ...L.objectives.map(o=>({x:o.x,z:o.z,y:0,r:o.radius+1.2})),
  ...L.spawns.flatMap(s=>s.positions.map(p=>({x:p.x,z:p.z,y:0,r:1.4}))),
 ];
 const onFloor=(x:number,z:number,y:number)=>y!==0||L.floorsG.some(r=>x>r[0]&&x<r[0]+r[2]&&z>r[1]&&z<r[1]+r[3]);
 /** Try to place a colliding item; it must clear walls, other props, doors, spawns, stairs and objectives. */
 const tryPlace=(p:Placement,margin=.35,gap=.6)=>{
  const boxes=collidersFor(p,'dress');
  if(p.collide){
   if(!onFloor(p.x,p.z,p.y))return false;
   for(const b of boxes){
    if(hits(b.x0-margin,b.x1+margin,b.y0+.05,b.y1,b.z0-margin,b.z1+margin,solid))return false;
    if(hits(b.x0-gap,b.x1+gap,b.y0,b.y1,b.z0-gap,b.z1+gap,blockers))return false;
    if(L.stairs.some(r=>b.x0<r[0]+r[2]+.8&&b.x1>r[0]-.8&&b.z0<r[1]+r[3]+.8&&b.z1>r[1]-.8&&p.y<=.1))return false;
    if(keepClear.some(k=>Math.abs(k.y-p.y)<1&&Math.max(b.x0-k.x,k.x-b.x1,0)**2+Math.max(b.z0-k.z,k.z-b.z1,0)**2<k.r*k.r))return false;
    if(b.x0<SX+.4||b.x1>SX+SW-.4||b.z0<SZ+.4||b.z1>SZ+SD-.4)return false;
   }
   blockers.push(...boxes);
  }
  items.push(p);return true;
 };
 const deco=(asset:string,x:number,y:number,z:number,ry=0,sx?:number)=>items.push({asset,x,y,z,ry,collide:false,...(sx?{sx}:{})});
 const face=(nx:number,nz:number)=>Math.atan2(nx,nz); // ry turning the front (+z) towards (nx, nz)

 // --- lamps: the plan's street and court lights, a perimeter ring, and a lamp over every exterior door ---
 const lamp=(x:number,z:number,kind:string)=>{
  for(const [dx,dz]of [[0,0],[1,0],[-1,0],[0,1],[0,-1],[1.5,1.5],[-1.5,-1.5]])if(tryPlace({asset:'LAMP_COLUMN',x:x+dx,y:0,z:z+dz,ry:0,collide:true},.25)){anchors.push({x:x+dx,y:4.75,z:z+dz,kind});return true}
  return false;
 };
 for(const l of L.lights)if(['street','court','garden'].includes(l.kind))lamp(l.x,l.z,l.kind==='garden'?'street':l.kind);
 for(let x=SX+10;x<SX+SW-4;x+=17){lamp(x,SZ+2.2,'street');lamp(x,SZ+SD-2.2,'street')}
 for(let z=SZ+19;z<SZ+SD-10;z+=17){lamp(SX+2.2,z,'street');lamp(SX+SW-2.2,z,'street')}
 for(const d of L.doors){
  const ox=d.axis==='x'?0:d.normal*(d.wall/2+.01),oz=d.axis==='x'?d.normal*(d.wall/2+.01):0,y=d.y+d.height+.32;
  deco('WALL_LAMP',d.x+ox,y,d.z+oz,face(d.axis==='x'?0:d.normal,d.axis==='x'?d.normal:0));
  anchors.push({x:d.x+ox*8,y:y-.1,z:d.z+oz*8,kind:'wall'});
 }
 // Covered ground under the L1 deck (arcades, cross arcades) gets ceiling strip lights every 9 m.
 for(const b of L.blocks)for(let x=b.rect[0]+4.5;x<b.rect[0]+b.rect[2];x+=9)for(let z=b.rect[1]+4.5;z<b.rect[1]+b.rect[3];z+=9){
  if(!hits(x-.4,x+.4,.3,2.6,z-.4,z+.4,solid)&&hits(x-.2,x+.2,2.7,3.01,z-.2,z+.2,L.boxes))anchors.push({x,y:2.72,z,kind:'ceiling'});
 }

 // The undercroft gets the same strips, on a 9 m grid over its floor slabs.
 for(const b of L.boxes.filter(b=>b.id==='slab'&&Math.abs(b.y1+3)<.01))for(let x=b.x0+4.5;x<b.x1;x+=9)for(let z=b.z0+4.5;z<b.z1;z+=9){
  if(!hits(x-.4,x+.4,-2.7,-.4,z-.4,z+.4,solid))anchors.push({x,y:-.48,z,kind:'ceiling'});
 }

 // --- core entrances: CCTV, intercom and a notice board on every ground-floor core ---
 for(const c of L.cores){
  const [cx,cz,cw,cd]=c.rect,south=c.mirror,wz=south?cz:cz+cd,n=south?-1:1;
  const g=L.doors.find(d=>d.owner===c.id&&d.y===Math.max(0,c.levels[0])&&d.y===0);
  deco('CCTV',cx+cw-.15,2.75,wz+n*.01,face(0,n));
  if(g){deco('INTERCOM',g.x+g.width/2+.35,1.2,wz+n*.01,face(0,n));
   for(const off of [-2.2,2.2])if(tryPlace({asset:'NOTICE_BOARD',x:g.x+off*1.1,y:0,z:wz+n*.25,ry:face(0,n),collide:true},.05))break}
 }

 // --- benches and bins ringing Garden Court and Washhouse Square, outside the capture circles ---
 for(const o of L.objectives){
  for(const [nx,nz]of [[0,-1],[0,1],[-1,0],[1,0]]){
   const r=o.radius+3.4,x=o.x+nx*r,z=o.z+nz*r,ry=face(-nx,-nz);
   if(tryPlace({asset:'BENCH',x,y:0,z,ry,collide:true}))tryPlace({asset:'LITTER_BIN',x:x+(nz?1.5:0),y:0,z:z+(nx?1.5:0),ry,collide:true},.2);
  }
 }

 // --- bollards across arcade mouths, so the deck edges read as estate paths ---
 for(const b of L.blocks)if(b.arcade){const [ax,az,aw,ad]=b.arcade;for(const z of [az-.7,az+ad+.7])for(let x=ax+1;x<ax+aw;x+=2)tryPlace({asset:'BOLLARD',x,y:0,z,ry:0,collide:true},.2)}

 // --- shops: a fit-out per use, along the walls without doors or glazing ---
 const fit:Record<string,{wall:string[];middle?:string[]}>={
  'LAUNDERETTE':{wall:['WASHING_MACHINE','WASHING_MACHINE','WASHING_MACHINE','WASHING_MACHINE','TUMBLE_DRYER','TUMBLE_DRYER'],middle:['LAUNDRY_CAGE']},
  'CYCLE WORKSHOP':{wall:['WORK_BENCH','WORK_BENCH'],middle:['BIKE']},
  'THE CORNER':{wall:['SHOP_FRIDGE','SHOP_FRIDGE','SHOP_FRIDGE','SHOP_SHELF_UNIT','SHOP_SHELF_UNIT'],middle:['SHOP_SHELF_UNIT','SHOP_SHELF_UNIT']},
  'YOUTH ROOM':{wall:['YOUTH_SOFA','YOUTH_SOFA','TABLE_FOLDING'],middle:['POOL_TABLE']},
  'WASHHOUSE':{wall:['WASHING_MACHINE','WASHING_MACHINE','WASHING_MACHINE','TUMBLE_DRYER','LAUNDRY_CAGE']},
  'ESTATE OFFICE':{wall:['ESTATE_OFFICE_DESK','ESTATE_OFFICE_DESK','NOTICE_BOARD']},
 };
 const depthOf=(a:string)=>{const c=assets.get(a)?.collider as Collider|undefined;return c?.size?c.size[1]:.6},widthOf=(a:string)=>{const c=assets.get(a)?.collider as Collider|undefined;return c?.size?c.size[0]:.6};
 for(const sh of L.shops){
  const f=fit[sh.name];if(!f)continue;const [x,z,w,d]=sh.rect,t=sh.wall,doorSides=new Set(sh.doorOpenings.map(o=>o.side));
  // Inner faces: N (z+t, facing south), S (z+d-t, facing north), W, E.
  const sides=[['S',x+t,z+d-t,1,0,w-2*t,0,-1],['N',x+t,z+t,1,0,w-2*t,0,1],['W',x+t,z+t,0,1,d-2*t,1,0],['E',x+w-t,z+t,0,1,d-2*t,-1,0]] as const;
  let queue=[...f.wall];
  for(const [side,sx,sz,ux,uz,len,nx,nz]of sides){
   if(side==='N')continue; // N is the shopfront glazing
   const doors=sh.doorOpenings.filter(o=>o.side===side).map(o=>o.offset);
   let u=.3;
   while(queue.length&&u<len-.3){
    const a=queue[0],wd=widthOf(a),dp=depthOf(a);
    if(u+wd>len-.3)break;
    const c=u+wd/2;if(doors.some(o=>Math.abs(o-c-t)<wd/2+1.2)){u+=.5;continue}
    const px=sx+ux*c+nx*(dp/2+.03),pz=sz+uz*c+nz*(dp/2+.03),ry=face(nx,nz);
    if(tryPlace({asset:a,x:px,y:0,z:pz,ry,collide:a!=='BIKE'},0,.01))queue.shift();
    u+=wd+.08;
   }
   if(!doorSides.has(side)&&!queue.length)break;
  }
  if(f.middle){const mx=x+w/2,mz=z+d/2;f.middle.forEach((a,i)=>{const off=(i-(f.middle!.length-1)/2)*3.2;tryPlace({asset:a,x:mx+(w>d?off:0),y:0,z:mz+(w>d?0:off),ry:w>d?0:Math.PI/2,collide:a!=='BIKE'},.0)})}
  if(sh.name==='THE CORNER')deco('SHOP_SIGN_CORNER',x+w/2,2.25,z-.03,Math.PI);
  if(sh.name==='CYCLE WORKSHOP')for(let i=0;i<3;i++){const px=x+2.2+i*1.3;tryPlace({asset:'CYCLE_HOOP',x:px,y:0,z:z-1.3,ry:0,collide:true},.1)&&i<2&&deco('BIKE',px+.35,0,z-1.3,Math.PI/2)}
 }
 // Service lane bins between the paired shops (behind the back doors).
 for(const sh of L.shops.filter(s=>s.rect[2]>s.rect[3]&&s.rect[1]<60)){
  const [x,z,w,d]=sh.rect,lz=z+d+.75;
  for(const [a,u]of [['EURO_BIN_1100',1.2],['EURO_BIN_1100',2.8],['WHEELIE_BIN_240',w-1.2],['WHEELIE_BIN_240_GREEN',w-2]] as const)tryPlace({asset:a,x:x+u,y:0,z:lz,ry:Math.PI,collide:true},.05);
  for(let i=0;i<5;i++)deco(['BIN_BAG','BIN_BAG_B','BIN_BAG_C'][i%3],x+3.8+R()*1.4,0,lz-.3+R()*.5,R()*6.28);
  deco('CARDBOARD_FLAT',x+w-3.4,0,lz+.2,R()*6.28);
 }

 // --- roofs: water tanks and vents on the playable terraces, units on the closed roofs ---
 for(const b of L.blocks){
  const [x,z,w,d]=b.rect,y=9;
  if(b.roofPlayable){tryPlace({asset:'ROOF_TANK',x:x+w-3,y,z:z+3,ry:0,collide:true});for(const u of [.25,.5,.75])tryPlace({asset:'ROOF_VENT',x:x+w*u,y,z:z+d-2.2,ry:0,collide:true})}
  else for(const u of [.2,.4,.6,.8])deco('AC_UNIT',x+w*u,y,z+d/2,R()<.5?0:Math.PI);
 }

 // --- the Cage: weld-mesh panels and posts over the fence colliders, goals and a ball ---
 {
  const [x,z,w,d]=L.cage.rect,g=L.cage.gate/2,mx=x+w/2,mz=z+d/2;
  const run=(x0:number,z0:number,x1:number,z1:number)=>{
   const len=Math.hypot(x1-x0,z1-z0),n=Math.max(1,Math.round(len/2.5)),sx=len/(n*2.5),ry=Math.abs(x1-x0)>Math.abs(z1-z0)?0:Math.PI/2;
   for(let i=0;i<n;i++){const k=(i+.5)/n;deco('CAGE_PANEL_2_5M',x0+(x1-x0)*k,0,z0+(z1-z0)*k,ry,sx)}
   for(let i=0;i<=n;i++){const k=i/n;deco('CAGE_POST',x0+(x1-x0)*k,0,z0+(z1-z0)*k,0)}
  };
  for(const zz of [z,z+d]){run(x,zz,mx-g,zz);run(mx+g,zz,x+w,zz)}
  for(const xx of [x,x+w]){run(xx,z,xx,mz-g);run(xx,mz+g,xx,z+d)}
  for(const [gx,gz]of [[mx,z],[mx,z+d]])deco('CAGE_GATE_4M',gx,0,gz,0);
  for(const [gx,gz]of [[x,mz],[x+w,mz]])deco('CAGE_GATE_4M',gx,0,gz,Math.PI/2);
  deco('GOAL_FIVE_A_SIDE',x+.62,0,mz-5.5,Math.PI/2);deco('GOAL_FIVE_A_SIDE',x+w-.62,0,mz+5.5,-Math.PI/2);
  deco('BALL',mx+3.2,0,mz-1.4,0);
 }

 // --- trees from the plan, alternating planes and birches ---
 const species=['TREE_PLANE_A','TREE_BIRCH_A','TREE_PLANE_B','TREE_BIRCH_B'];
 L.trees.forEach((t,i)=>deco(species[i%4],t.x,0,t.z,R()*6.283));

 // --- planting beds: shrubs and weeds under the 0.7 m limit, leaf litter under trees ---
 for(const p of L.planting){const [x,z,w,d]=p.rect,n=Math.round(w*d*.06);for(let i=0;i<n;i++)deco(['SHRUB_A','SHRUB_B','SHRUB_C','WEED_TUFT_B','WEED_TUFT_C'][Math.floor(R()*5)],x+.5+R()*(w-1),0,z+.5+R()*(d-1),R()*6.28)}
 for(const t of L.trees)for(let i=0;i<4;i++){const a=R()*6.28,r=.8+R()*2.6;deco(['LEAF_LITTER_A','LEAF_LITTER_B','LEAF_LITTER_C'][i%3],t.x+Math.cos(a)*r,.004,t.z+Math.sin(a)*r,R()*6.28)}

 // --- litter: cans and packets where people stop, a cone or two and a trolley ---
 const scatter=(x:number,z:number,y:number,r:number,n:number)=>{for(let i=0;i<n;i++){const a=R()*6.28,d=R()*r;deco(R()<.5?'CRISP_PACKET':'CRUSHED_CAN',x+Math.cos(a)*d,y+.002,z+Math.sin(a)*d,R()*6.28)}};
 for(const o of L.objectives)scatter(o.x,o.z,0,o.radius+4,10);
 for(const s of L.shops)scatter(s.rect[0]+s.rect[2]/2,s.rect[1]-1.5,0,2.5,4);
 for(const [x,z]of [[60,58],[84,63],[56,40]])deco('TRAFFIC_CONE',x,-3,z,R()*6.28);
 tryPlace({asset:'SHOPPING_TROLLEY',x:118,y:0,z:45.6,ry:.0,collide:true});
 deco('MATTRESS_DUMPED',40.5,0,58.2,0.3);

 // --- the street beyond the boundary: parked cars and vans, render-only ---
 const park=(x:number,z:number,ry:number)=>deco(R()<.22?'VAN_DELIVERY':'CAR_HATCHBACK',x,0,z,ry+(R()-.5)*.04);
 for(let x=SX+6;x<SX+SW;x+=5.6+R()*2.5){if(R()<.5)park(x,SZ-4.2,Math.PI/2);if(R()<.5)park(x,SZ+SD+4.2,-Math.PI/2)}
 for(let z=SZ+6;z<SZ+SD;z+=5.6+R()*2.5){if(R()<.5)park(SX-4.2,z,0);if(R()<.5)park(SX+SW+4.2,z,Math.PI)}
 for(let x=SX+3;x<SX+SW;x+=9)for(const z of [SZ-1.4,SZ+SD+1.4])deco('LAMP_COLUMN',x,0,z,0),anchors.push({x,y:4.75,z,kind:'street'});

 // --- decals: puddles where water collects, tags in the undercroft and on core flanks ---
 const decals:DecalPlan[]=[];
 for(const w of L.wetAreas){const [x,z,ww,d]=w.rect;decals.push({kind:'puddle',x:x+ww/2,y:0,z:z+d/2,w:ww+1.5,h:d+1.5,ry:0})}
 for(let i=0,tries=0;i<70&&tries<2000;tries++){
  const x=SX+3+R()*(SW-6),z=SZ+3+R()*(SD-6),w=1.2+R()*3.2,h=w*(.5+R()*.6);
  if(!onFloor(x,z,0)||hits(x-w/2,x+w/2,.02,2,z-h/2,z+h/2,solid)||hits(x-w/2,x+w/2,.02,2,z-h/2,z+h/2,blockers))continue;
  decals.push({kind:'puddle',x,y:0,z,w,h,ry:R()*Math.PI});i++;
 }
 for(let i=0;i<18&&i<L.undercroftWalls.length;i++){
  const u=L.undercroftWalls[Math.floor(R()*L.undercroftWalls.length)],len=Math.hypot(u.x1-u.x0,u.z1-u.z0);if(len<3)continue;
  const k=.2+R()*.6,w=1.6+R()*1.4;decals.push({kind:'graffiti',x:u.x0+(u.x1-u.x0)*k+u.nx*.012,y:-3+1.2+R()*.4,z:u.z0+(u.z1-u.z0)*k+u.nz*.012,w,h:w*.55,ry:face(u.nx,u.nz),cell:Math.floor(R()*4)});
 }
 for(const c of L.cores){const [cx,cz,cw,cd]=c.rect;if(R()<.5)continue;const side=R()<.5?-1:1,x=side<0?cx-.012:cx+cw+.012;decals.push({kind:'graffiti',x,y:1.3,z:cz+cd/2,w:2.2,h:1.2,ry:face(side,0),cell:Math.floor(R()*4)})}

 return {items,anchors,colliders:blockers,decals};
}
