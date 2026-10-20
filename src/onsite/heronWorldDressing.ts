import type {Solid} from './level'

export type WorldVector=[number,number,number]
export type WorldAssetBounds={min:WorldVector;max:WorldVector}
export type WorldSourcePlacement={asset:string;x:number;y:number;z:number;ry:number;sx?:number;scale?:number;source?:string;collide?:boolean}
type Rect=readonly number[]
type Door={x:number;y:number;z:number;axis:string;width:number;height:number;kind?:string}
type Planter={id:string;rect:Rect;y:number;height:number;kind:string}
export type WorldDressingInput={
 placements:readonly WorldSourcePlacement[];solids:readonly Solid[];doors:readonly Door[]
 blocks?:readonly {rect:Rect;roofPlayable:boolean}[]
 groundPlants?:readonly WorldSourcePlacement[];planters?:readonly Planter[]
 /** Authored WORLD_CLAY_POT soil cap height in its unscaled native root. */
 potSoilSurfaceY?:number
 potSoilRadius?:number;fernStemXZ?:ReadonlyMap<string,readonly [number,number]>
 fernStemBasalY?:ReadonlyMap<string,number>
}
export type WorldSupport={kind:'ground'|'roof'|'shelf'|'plinth'|'soil'|'table'|'pot';y:number;bounds:WorldAssetBounds;host:string}
export type WorldPropPlacement={
 asset:string;x:number;y:number;z:number;ry:number;rx:number;scale:number
 support:WorldSupport;bounds:WorldAssetBounds;enclosure?:WorldAssetBounds
 replacementKey?:string;role:string
}
export type WorldDressingPlan={
 placements:WorldPropPlacement[];replacementKeys:Set<string>;groundReplacementKeys:Set<string>
 stats:{replacements:number;storeContents:number;workshopContents:number;ferns:number;tableArrangements:number}
 reviewViews:readonly (readonly [string,number,number,number,number,number,number])[]
}

/** Exact original transform identity. Filter originals only after the new kit has loaded. */
export function worldReplacementKey(p:WorldSourcePlacement):string {
 return JSON.stringify([p.asset,p.x,p.y,p.z,p.ry,p.sx??1,p.scale??1])
}

const OX=72,OZ=60,EPS=.001
const finiteBounds=(b:WorldAssetBounds|undefined):b is WorldAssetBounds=>!!b&&
 [...b.min,...b.max].every(Number.isFinite)&&b.min.every((v,i)=>b.max[i]-v>1e-5)
const corners=(b:WorldAssetBounds)=>[b.min[0],b.max[0]].flatMap(x=>[b.min[1],b.max[1]].flatMap(y=>[b.min[2],b.max[2]].map(z=>[x,y,z] as WorldVector)))
function boundsOf(points:WorldVector[]):WorldAssetBounds {
 return {min:[0,1,2].map(i=>Math.min(...points.map(p=>p[i]))) as WorldVector,max:[0,1,2].map(i=>Math.max(...points.map(p=>p[i]))) as WorldVector}
}
function rotate([x,y,z]:WorldVector,ry:number,rx=0):WorldVector {
 const yy=y*Math.cos(rx)-z*Math.sin(rx),zz=y*Math.sin(rx)+z*Math.cos(rx)
 return [x*Math.cos(ry)+zz*Math.sin(ry),yy,-x*Math.sin(ry)+zz*Math.cos(ry)]
}
export function worldPlacementBounds(asset:WorldAssetBounds,p:Pick<WorldPropPlacement,'x'|'y'|'z'|'ry'|'rx'|'scale'>):WorldAssetBounds {
 return boundsOf(corners(asset).map(v=>rotate(v,p.ry,p.rx).map((c,i)=>c*p.scale+[p.x,p.y,p.z][i]) as WorldVector))
}
function contains(outer:WorldAssetBounds,inner:WorldAssetBounds,margin=0){
 return outer.min.every((v,i)=>inner.min[i]>=v+margin-EPS&&inner.max[i]<=outer.max[i]-margin+EPS)
}
function footprintContains(outer:WorldAssetBounds,inner:WorldAssetBounds,margin=0){
 return [0,2].every(i=>inner.min[i]>=outer.min[i]+margin-EPS&&inner.max[i]<=outer.max[i]-margin+EPS)
}
const box=(x0:number,x1:number,y0:number,y1:number,z0:number,z1:number):WorldAssetBounds=>({min:[x0,y0,z0],max:[x1,y1,z1]})
const solidBounds=(s:Solid)=>box(s.x+OX-s.w/2,s.x+OX+s.w/2,s.y-s.h/2,s.y+s.h/2,s.z+OZ-s.d/2,s.z+OZ+s.d/2)
function localBox(p:WorldSourcePlacement,b:WorldAssetBounds):WorldAssetBounds {
 return worldPlacementBounds(b,{...p,rx:0,scale:1})
}
function pointIn(b:WorldAssetBounds,x:number,z:number){
 return x>=b.min[0]-EPS&&x<=b.max[0]+EPS&&z>=b.min[2]-EPS&&z<=b.max[2]+EPS
}
function clearDoors(b:WorldAssetBounds,doors:readonly Door[]){
 return !doors.some(d=>{
  if(d.kind&&!d.kind.includes('door'))return false
  if(b.max[1]<=d.y+.02||b.min[1]>=d.y+d.height)return false
  const w=d.width/2+.3,depth=.85
  const portal=d.axis==='x'?box(d.x-w,d.x+w,d.y,d.y+d.height,d.z-depth,d.z+depth):box(d.x-depth,d.x+depth,d.y,d.y+d.height,d.z-w,d.z+w)
  return b.min.every((v,i)=>v<portal.max[i]-EPS&&b.max[i]>portal.min[i]+EPS)
 })
}
function floorSupported(b:WorldAssetBounds,y:number,solids:readonly Solid[]){
 const floors=solids.filter(s=>['ground','slab','roof','landing'].includes(s.id)&&Math.abs(s.y+s.h/2-y)<.005).map(solidBounds)
 // Same explicit storey at all corners, edge midpoints and centre; never snap to a different floor.
 return [b.min[0],(b.min[0]+b.max[0])/2,b.max[0]].every(x=>[b.min[2],(b.min[2]+b.max[2])/2,b.max[2]].every(z=>floors.some(f=>pointIn(f,x,z))))
}
function hostCollider(p:WorldSourcePlacement,expected:WorldAssetBounds,solids:readonly Solid[]){
 const target=localBox(p,expected)
 return solids.some(s=>s.id==='dress'&&contains(solidBounds(s),target)&&contains(target,solidBounds(s)))?target:undefined
}

/** Once-only, bounds-driven render plan. It never mutates dressing or creates physics.
 * Matrix contract: T(x-72,y,z-60) * Ry(ry) * Rx(rx) * S(scale). Translation already
 * accounts for rotated native bounds, including the bottom; do not normalise again.
 * Asset bounds come from successfully loaded roots. Missing/invalid roots leave originals.
 */
export function buildHeronWorldDressing(input:WorldDressingInput,assets:ReadonlyMap<string,WorldAssetBounds>):WorldDressingPlan {
 const placements:WorldPropPlacement[]=[],replacementKeys=new Set<string>(),groundReplacementKeys=new Set<string>()
 const stats={replacements:0,storeContents:0,workshopContents:0,ferns:0,tableArrangements:0}
 const fit=(asset:string,cx:number,cz:number,support:WorldSupport,limit:WorldVector,ry:number,role:string,options:{rx?:number;minHeight?:number;enclosure?:WorldAssetBounds;replace?:string;maxScale?:number;stem?:readonly [number,number];stemY?:number}={}):WorldPropPlacement|undefined=>{
  const native=assets.get(asset);if(!finiteBounds(native))return
  const rx=options.rx??0,rotated=boundsOf(corners(native).map(v=>rotate(v,ry,rx)))
  const size=rotated.max.map((v,i)=>v-rotated.min[i]),scale=Math.min(options.maxScale??1,...limit.map((v,i)=>v/size[i]))
  if(!Number.isFinite(scale)||scale<=0||size[1]*scale<(options.minHeight??0))return
  const p:WorldPropPlacement={asset,x:cx-(rotated.min[0]+rotated.max[0])*scale/2,y:support.y-rotated.min[1]*scale,z:cz-(rotated.min[2]+rotated.max[2])*scale/2,ry,rx,scale,support,bounds:box(0,1,0,1,0,1),role,...(options.enclosure?{enclosure:options.enclosure}:{}),...(options.replace?{replacementKey:options.replace}:{})}
  if(options.stem){const anchor=rotate([options.stem[0],options.stemY??0,options.stem[1]],ry,rx);p.x=cx-anchor[0]*scale;p.y=support.y-anchor[1]*scale;p.z=cz-anchor[2]*scale}
  p.bounds=worldPlacementBounds(native,p)
  if(!footprintContains(support.bounds,p.bounds,.005)||!clearDoors(p.bounds,input.doors))return
  if(options.enclosure&&!contains(options.enclosure,p.bounds))return
  return p
 }
 const add=(p:WorldPropPlacement|undefined)=>{if(p)placements.push(p);return !!p}
 const localFit=(asset:string,host:WorldSourcePlacement,lx:number,lz:number,y:number,localSupport:WorldAssetBounds,limit:WorldVector,role:string,enclosure:WorldAssetBounds,extraYaw=0)=>{
  const q=rotate([lx,0,lz],host.ry),support={kind:(role==='bin-store'?'plinth':'shelf') as WorldSupport['kind'],y:host.y+y,bounds:localBox(host,localSupport),host:worldReplacementKey(host)}
  return fit(asset,host.x+q[0],host.z+q[2],support,limit,host.ry+extraYaw,role,{enclosure})
 }

 // Existing service-lane bags are already cosmetic. New scans stay inside their old envelope.
 const bagBoxes:Record<string,WorldAssetBounds>={
  BIN_BAG:box(-.271,.276,0,.658,-.234,.24),BIN_BAG_B:box(-.31,.243,0,.52,-.236,.232),
  BIN_BAG_C:box(-.487,.489,0,.656,-.373,.281),
 }
 for(const source of input.placements){
  const original=bagBoxes[source.asset]
  if(original&&source.y===0){
   const envelope=localBox(source,original),key=worldReplacementKey(source),batch:WorldPropPlacement[]=[]
   const slots=source.asset==='BIN_BAG_C'?[[-.23,-.1,.41,.42,.31],[.23,-.1,.41,.46,.31],[0,.10,.38,.38,.31]]:[[(original.min[0]+original.max[0])/2,(original.min[2]+original.max[2])/2,original.max[0]-original.min[0]-.02,original.max[1]-.02,original.max[2]-original.min[2]-.02]]
   for(const [dx,dz,w,h,d] of slots){
    const offset=rotate([dx,0,dz],source.ry)
    const p=fit('WORLD_TRASH_BAG',source.x+offset[0],source.z+offset[2],{kind:'ground',y:source.y,bounds:envelope,host:key},[w,h,d],source.ry,'bag-replacement',{enclosure:envelope,replace:key})
    if(p&&floorSupported(p.bounds,source.y,input.solids))batch.push(p)
   }
   if(batch.length===slots.length){placements.push(...batch);replacementKeys.add(key);stats.replacements++}
  }
  if(source.asset==='AC_UNIT'&&source.y===9&&input.blocks?.some(b=>!b.roofPlayable&&source.x>b.rect[0]&&source.x<b.rect[0]+b.rect[2]&&source.z>b.rect[1]&&source.z<b.rect[1]+b.rect[3])){
   const envelope=localBox(source,box(-.4,.475,0,.6,-.02,.35)),key=worldReplacementKey(source)
   const p=fit('WORLD_AIRCON_RUST',(envelope.min[0]+envelope.max[0])/2,(envelope.min[2]+envelope.max[2])/2,{kind:'roof',y:9,bounds:envelope,host:key},[envelope.max[0]-envelope.min[0]-.01,.6,envelope.max[2]-envelope.min[2]-.01],source.ry,'roof-replacement',{enclosure:envelope,replace:key})
   if(p&&floorSupported(p.bounds,9,input.solids)){placements.push(p);replacementKeys.add(key);stats.replacements++}
  }
  if(source.asset==='hr_prop_bin_store_3bay'){
   const enclosure=hostCollider(source,box(-1.95,1.95,0,1.77,-1.1,1),input.solids);if(!enclosure)continue
   // Authored slab top .10; stock stays behind the inward-swinging right gate.
   const support=box(-1.46,1.46,.1,.1,-.585,.8)
   for(const lx of [-1,0,1])if(add(localFit('WORLD_BIN_RUST',source,lx,-.17,.1,support,[.68,1.2,.58],'bin-store',enclosure)))stats.storeContents++
   if(add(localFit('WORLD_TRASH_BAG',source,-.92,.49,.1,support,[.4,.46,.4],'bin-store',enclosure)))stats.storeContents++
  }
  if(source.asset==='WORK_BENCH'){
   const enclosure=hostCollider(source,box(-.91,.91,0,1.86,-.36,.36),input.solids);if(!enclosure)continue
   // Empty lower shelf top=.219, tabletop underside=.855. Existing tools remain above.
   const support=box(-.86,.86,.219,.219,-.30,.30)
   const leftAsset=source.x<26?'WORLD_WOODEN_CRATE':'WORLD_CARDBOARD_BOX'
   for(const [asset,x,z,limit,yaw] of [
    [leftAsset,-.43,0,[.68,.44,.5],0],
    ['WORLD_TYRE',.45,0,[.48,.16,.48],0],
   ] as const)if(add(localFit(asset,source,x,z,.219,support,[...limit], 'workshop-shelf',enclosure,yaw)))stats.workshopContents++
  }
 }

 const fernNames=['WORLD_FERN_A','WORLD_FERN_B','WORLD_FERN_C','WORLD_FERN_D'].filter(name=>finiteBounds(assets.get(name)))
 const planters=input.planters?.filter(p=>p.kind.includes('planter'))??[]
 for(const [i,old] of (input.groundPlants??[]).entries()){
  if(old.asset!=='WEED_TUFT_A'||typeof old.source!=='string'||!old.source.startsWith('planter:')||!fernNames.length)continue
  const bed=planters.find(b=>'planter:'+b.id===old.source);if(!bed)continue
  const [x,z,w,d]=bed.rect,y=bed.y+bed.height-.15,inner=box(x+.12,x+w-.12,y,1.25,z+.12,z+d-.12)
  const dx=Math.min(old.x-inner.min[0],inner.max[0]-old.x),dz=Math.min(old.z-inner.min[2],inner.max[2]-old.z)
  const key=worldReplacementKey(old)
  let p:WorldPropPlacement|undefined
  for(let j=0;j<fernNames.length&&!p;j++)p=fit(fernNames[(i+j)%fernNames.length],old.x,old.z,{kind:'soil',y,bounds:inner,host:old.source},[Math.min(.85,2*dx-.03),.38,Math.min(.85,2*dz-.03)],old.ry,'planter-fern',{minHeight:.18,maxScale:1,enclosure:inner,replace:key})
  if(add(p)){groundReplacementKeys.add(key);stats.ferns++}
 }

 // Fill the large bare soil gaps with low, staggered fern clumps. Existing shrub
 // centres remain clear, and every canopy stays inside the same planter/cover envelope.
 if(input.groundPlants&&fernNames.length)for(const [bedIndex,bed] of planters.entries()){
  const [x,z,w,d]=bed.rect,y=bed.y+bed.height-.15,host='planter:'+bed.id
  const inner=box(x+.12,x+w-.12,y,1.25,z+.12,z+d-.12)
  const occupied=input.groundPlants.filter(p=>p.source===host).map(p=>[p.x,p.z])
  const nx=Math.max(2,Math.floor((w-.8)/.65)),nz=Math.max(2,Math.floor((d-.8)/.65))
  const candidates=Array.from({length:nx*nz},(_,i)=>{
   const ix=i%nx,iz=Math.floor(i/nx),phase=i*2.39996+bedIndex*.83
   return {cx:x+.5+(w-1)*(ix+.5)/nx+Math.sin(phase)*.07,cz:z+.5+(d-1)*(iz+.5)/nz+Math.cos(phase)*.07,phase,order:Math.sin(phase*1.73)}
  }).sort((a,b)=>a.order-b.order)
  let count=0
  for(const [i,{cx,cz,phase}]of candidates.entries()){
   if(count>=Math.min(10,Math.round(w*d*.7)))break
   if(occupied.some(([px,pz])=>Math.hypot(px-cx,pz-cz)<.45))continue
   const dx=Math.min(cx-inner.min[0],inner.max[0]-cx),dz=Math.min(cz-inner.min[2],inner.max[2]-cz)
   let p:WorldPropPlacement|undefined
   for(let j=0;j<fernNames.length&&!p;j++)p=fit(fernNames[(i+j+bedIndex)%fernNames.length],cx,cz,
    {kind:'soil',y,bounds:inner,host},[Math.min(1.05,2*dx-.03),.38,Math.min(1.05,2*dz-.03)],
    phase,'planter-infill',{minHeight:.18,enclosure:inner})
   if(add(p)){occupied.push([cx,cz]);count++;stats.ferns++}
  }
 }

 // One restrained potted fern in four existing H1 homes. Empty tabletops are already colliding.
 const potNative=assets.get('WORLD_CLAY_POT'),soil=input.potSoilSurfaceY
 if(finiteBounds(potNative)&&fernNames.length&&soil!==undefined&&soil>potNative.min[1]&&soil<potNative.max[1]&&Number.isFinite(input.potSoilRadius)&&input.potSoilRadius!>0){
  const tables=input.solids.filter(s=>s.id==='home-table'&&Math.abs(s.y-s.h/2)<EPS).map(solidBounds)
  for(const [quadrant,qx,qz] of [['NW',false,false],['NE',true,false],['SW',false,true],['SE',true,true]] as const){
   const table=tables.find(b=>(b.min[0]>=72)===qx&&(b.min[2]>=60)===qz);if(!table)continue
   // The clear outer end is farther from the inner doorway than the table centre.
   // The existing packed arch exports these .75 m tables at .7489127325 m.
   // Seat 13 micrometres into that rendered top; physical tabletop stays unchanged.
   const cx=table.max[0]-.32,cz=(table.min[2]+table.max[2])/2,y=table.max[1]-.0011,host='home-table:'+quadrant
   const support={kind:'table' as const,y,bounds:table,host}
   const pot=fit('WORLD_CLAY_POT',cx,cz,support,[.23,.20,.23],0,'table-pot')
   if(!pot)continue
   const soilY=pot.y+soil*pot.scale
   let fern:WorldPropPlacement|undefined
   for(let j=0;j<fernNames.length&&!fern;j++){
    const fernName=fernNames[(stats.tableArrangements+j)%fernNames.length],stem=input.fernStemXZ?.get(fernName),stemY=input.fernStemBasalY?.get(fernName)
    const native=assets.get(fernName)!
    if(!stem||!stem.every(Number.isFinite)||stemY===undefined||!Number.isFinite(stemY)||stemY<native.min[1]||stemY>native.max[1])continue
    fern=fit(fernName,cx,cz,{kind:'pot',y:soilY,bounds:table,host},[.56,.32,.54],.35+stats.tableArrangements*.7,'table-fern',{minHeight:.18,stem,stemY})
    if(fern&&fern.bounds.max[1]>1.30)fern=undefined
   }
   if(!fern)continue
   placements.push(pot,fern);stats.tableArrangements++
  }
 }
 return {placements,replacementKeys,groundReplacementKeys,stats,reviewViews:[
  ['cycle-workshop-stock',26.4,0,67.5,0,1,-.18],
  ['north-bin-store',48,0,5.1,0,-1,-.06],
  ['corner-service-stock',107.5,0,60.5,-.8,-2.85,-.45],
  ['northwest-home-table',31.2,0,27.15,2.58,-.6,-.35],
  ['garden-ground-close',67.5,0,22,-3,-4,-.23],
 ]}
}
