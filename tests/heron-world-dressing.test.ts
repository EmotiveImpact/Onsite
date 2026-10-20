import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import {dressing,layout,solids} from '../src/onsite/heronReach.ts'
import {collidersFor,type Placement} from '../src/onsite/heronReachDressing.ts'
import groundPlan from '../public/models/heron-reach/ground-plan.json'
import {buildHeronWorldDressing,worldReplacementKey,type WorldAssetBounds,type WorldDressingInput} from '../src/onsite/heronWorldDressing.ts'
import {worldAssetKits} from '../src/onsite/heronWorldArt.ts'

type Transform={x:number;y:number;z:number;ry:number;rx?:number;sx?:number;scale?:number}
type SurfaceTriangle={triangle:THREE.Triangle;material:string}
type DecodedGeometry={vertices:THREE.Vector3[];triangles:SurfaceTriangle[];bounds:THREE.Box3}

/**
 * Decode the shipped buffers and all node transforms, including Meshopt. Only
 * material image references are removed so these placement tests need no DOM.
 */
async function decodeKit(filename:string){
 const original=readFileSync(new URL(`../public/models/heron-reach/${filename}`,import.meta.url))
 assert.equal(original.readUInt32LE(0),0x46546c67)
 const length=original.readUInt32LE(12),json=JSON.parse(original.subarray(20,20+length).toString())
 json.materials=(json.materials??[]).map((material:{name?:string})=>({name:material.name}))
 delete json.images;delete json.textures;delete json.samplers
 for(const key of ['extensionsUsed','extensionsRequired']){
  if(json[key])json[key]=json[key].filter((extension:string)=>extension!=='EXT_texture_webp')
 }
 const encoded=Buffer.from(JSON.stringify(json)),body=Buffer.alloc(Math.ceil(encoded.length/4)*4,32)
 encoded.copy(body)
 const tail=original.subarray(20+length),header=Buffer.alloc(20)
 header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4)
 header.writeUInt32LE(20+body.length+tail.length,8)
 header.writeUInt32LE(body.length,12);header.writeUInt32LE(0x4e4f534a,16)
 const bytes=Uint8Array.from(Buffer.concat([header,body,tail]))
 const {scene}=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer,'')
 scene.updateMatrixWorld(true)
 return scene
}
const kits=new Map<string,ReturnType<typeof decodeKit>>()
function kit(filename:string){
 let result=kits.get(filename)
 if(!result){result=decodeKit(filename);kits.set(filename,result)}
 return result
}
function root(scene:THREE.Object3D,name:string){
 const result=scene.getObjectByName(name)
 assert(result,`shipped kit is missing ${name}`)
 return result
}
// Runtime transform in map coordinates, omitting the common (-72,0,-60) offset.
function mapMatrix(p:Transform){
 const scale=p.scale??1
 return new THREE.Matrix4().makeTranslation(p.x,p.y,p.z)
  .multiply(new THREE.Matrix4().makeRotationY(p.ry))
  .multiply(new THREE.Matrix4().makeRotationX(p.rx??0))
  .scale(new THREE.Vector3(scale*(p.sx??1),scale,scale))
}
function geometry(asset:THREE.Object3D,transform=new THREE.Matrix4(),material?:string):DecodedGeometry{
 const inverse=asset.matrixWorld.clone().invert(),vertices:THREE.Vector3[]=[],triangles:SurfaceTriangle[]=[]
 asset.traverse(object=>{
  if(!(object instanceof THREE.Mesh))return
  assert(!Array.isArray(object.material),`${asset.name}: expected one material per exported primitive`)
  if(material&&object.material.name!==material)return
  const source:THREE.BufferGeometry=object.geometry,position=source.getAttribute('position'),index=source.index
  const matrix=transform.clone().multiply(inverse).multiply(object.matrixWorld)
  const points=Array.from({length:position.count},(_,i)=>new THREE.Vector3().fromBufferAttribute(position,i).applyMatrix4(matrix))
  vertices.push(...points)
  for(let i=0;i<(index?.count??position.count);i+=3){
   const vertex=(offset:number)=>points[index?index.getX(i+offset):i+offset]
   triangles.push({triangle:new THREE.Triangle(vertex(0),vertex(1),vertex(2)),material:object.material.name})
  }
 })
 assert(vertices.length>0,`${asset.name}: actual decoded geometry is empty`)
 return {vertices,triangles,bounds:new THREE.Box3().setFromPoints(vertices)}
}
function horizontalSurface(source:DecodedGeometry,material:string,expectedY:number,searchTolerance=.001){
 const triangles=source.triangles.filter(({triangle:t,material:m})=>m===material&&
  [t.a,t.b,t.c].every(p=>Math.abs(p.y-expectedY)<searchTolerance)&&
  Math.max(t.a.y,t.b.y,t.c.y)-Math.min(t.a.y,t.b.y,t.c.y)<1e-6&&t.getArea()>1e-8)
 assert(triangles.length>0,`${material}: no exported horizontal surface at ${expectedY} m`)
 const vertices=triangles.flatMap(({triangle:t})=>[t.a,t.b,t.c])
 return {triangles,bounds:new THREE.Box3().setFromPoints(vertices),height:vertices[0].y}
}
function supportedAt(surface:ReturnType<typeof horizontalSurface>,x:number,z:number){
 const point=new THREE.Vector3(x,surface.height,z)
 return surface.triangles.some(({triangle})=>triangle.containsPoint(point))
}
function footprintCorners(box:THREE.Box3){
 return [[box.min.x,box.min.z],[box.min.x,box.max.z],[box.max.x,box.min.z],[box.max.x,box.max.z]] as const
}
function assertSupported(box:THREE.Box3,surface:ReturnType<typeof horizontalSurface>,label:string){
 // Existing packed props quantize source positions by less than 0.5 mm.
 assert(Math.abs(box.min.y-surface.height)<.001,`${label}: bottom must meet the actual exported support`)
 for(const [x,z]of footprintCorners(box))assert(supportedAt(surface,x,z),`${label}: footprint overhangs the actual support`)
}
function colliderBoxes(host:Placement){
 const result=collidersFor(host,'existing-host').map(b=>new THREE.Box3(
  new THREE.Vector3(b.x0,b.y0,b.z0),new THREE.Vector3(b.x1,b.y1,b.z1)))
 assert(result.length>0,`${host.asset}: missing original collision envelope`)
 return result
}
function assertInsideCollider(box:THREE.Box3,host:Placement,label:string){
 assert(colliderBoxes(host).some(collider=>collider.containsBox(box)),`${label}: extends outside the unchanged host collider`)
}
function assertClearOfGeometry(box:THREE.Box3,source:DecodedGeometry,label:string,clearance=0){
 const envelope=box.clone().expandByScalar(clearance)
 assert(!source.triangles.some(({triangle})=>envelope.intersectsTriangle(triangle)),`${label}: intersects existing exported geometry`)
}
const digest=(value:unknown)=>createHash('sha256').update(JSON.stringify(value)).digest('hex')
const input:WorldDressingInput={
 placements:dressing.items,solids,doors:layout.openings,blocks:layout.blocks,
 groundPlants:groundPlan.plants,planters:layout.cover,potSoilSurfaceY:.185,
}
function asBox(bounds:WorldAssetBounds){
 return new THREE.Box3(new THREE.Vector3(...bounds.min),new THREE.Vector3(...bounds.max))
}
function solidBox(s:(typeof solids)[number]){
 return new THREE.Box3(new THREE.Vector3(s.x+72-s.w/2,s.y-s.h/2,s.z+60-s.d/2),
  new THREE.Vector3(s.x+72+s.w/2,s.y+s.h/2,s.z+60+s.d/2))
}
function assertVerticesInside(vertices:THREE.Vector3[],bounds:WorldAssetBounds,label:string){
 const box=asBox(bounds).expandByScalar(1e-7)
 for(const vertex of vertices)assert(box.containsPoint(vertex),`${label}: actual geometry exceeds the planned envelope`)
}
async function actualWorld(){
 const catalog=new Map<string,WorldAssetBounds>(),roots=new Map<string,THREE.Object3D>()
 for(const definition of worldAssetKits){
  const scene=await kit(definition.url.split('/').at(-1)!)
  assert.deepEqual(scene.children.map(child=>child.name).sort(),[...definition.roots].sort(),`${definition.url}: export only the declared runtime roots`)
  for(const name of definition.roots){
   const asset=root(scene,name),bounds=geometry(asset).bounds
   assert([...bounds.min,...bounds.max].every(Number.isFinite),`${name}: decoded root or geometry contains a non-finite transform`)
   roots.set(name,asset);catalog.set(name,{min:bounds.min.toArray(),max:bounds.max.toArray()})
  }
 }
 const pot=roots.get('WORLD_CLAY_POT')!
 const worldInput:WorldDressingInput={...input,potSoilSurfaceY:pot.userData.soilSurfaceY,potSoilRadius:pot.userData.soilRadius,
  fernStemXZ:new Map([...roots].filter(([name])=>name.startsWith('WORLD_FERN_')).map(([name,asset])=>[name,asset.userData.stemXZ])),
  fernStemBasalY:new Map([...roots].filter(([name])=>name.startsWith('WORLD_FERN_')).map(([name,asset])=>[name,asset.userData.stemBasalY]))}
 return {catalog,roots,input:worldInput,plan:buildHeronWorldDressing(worldInput,catalog)}
}
let loadedWorld:ReturnType<typeof actualWorld>|undefined
const world=()=>loadedWorld??=actualWorld()
const originalInput=digest(input)

test('actual bin-store and workshop exports expose the expected solid supports',async()=>{
 const structures=await kit('heron-reach-sl-structures.glb'),props=await kit('heron-reach-props.glb')
 const store=geometry(root(structures,'hr_prop_bin_store_3bay')),bench=geometry(root(props,'WORK_BENCH'))
 const slab=horizontalSurface(store,'mat_concrete_cast',.1)
 const shelf=horizontalSurface(bench,'hr_prop_formica_grey',.219)
 const top=horizontalSurface(bench,'hr_timber',.9)
 assert.equal(store.triangles.length,888,'the existing bin store is only its slab, brickwork, coping and rear buffer')
 assert.equal(geometry(root(structures,'hr_prop_bin_store_gate_leaf')).triangles.length,204)
 assert.equal(bench.triangles.length,2992,'the workbench retains its authored vice, toolbox, wheel and tools')
 for(const [x,z]of [[-1.4,-.5],[1.4,.7]])assert(supportedAt(slab,x,z),'bin-store floor has usable supported interior')
 for(const [x,z]of [[-.8,-.25],[.8,.25]])assert(supportedAt(shelf,x,z),'workbench lower shelf is a real surface')
 assert(supportedAt(top,0,0),'workbench tabletop is a real surface')
 assert(Math.abs(shelf.height-.219)<.001)
 assert(Math.abs(top.height-.9)<.001)
 assert.equal(dressing.items.filter(p=>p.asset==='hr_prop_bin_store_3bay').length,4)
 assert.equal(dressing.items.filter(p=>p.asset==='WORK_BENCH').length,2)
})

test('replacement identity includes the exact original scale and mirror, without category-wide hiding',()=>{
 const source={asset:'WEED_TUFT_A',x:10,y:.85,z:20,ry:.7,scale:2.8}
 assert.notEqual(worldReplacementKey(source),worldReplacementKey({...source,scale:3}))
 assert.notEqual(worldReplacementKey(source),worldReplacementKey({...source,sx:-1}))
 assert.notEqual(worldReplacementKey(source),worldReplacementKey({...source,x:10.001}))
 const {scale:_scale,...unscaled}=source
 assert.equal(worldReplacementKey(unscaled),worldReplacementKey({...unscaled,scale:1,sx:1}))
})

test('missing or invalid optional assets preserve all original dressing and ground planting',()=>{
 const empty=buildHeronWorldDressing(input,new Map())
 assert.deepEqual(empty.placements,[])
 assert.equal(empty.replacementKeys.size,0);assert.equal(empty.groundReplacementKeys.size,0)
 const invalid:WorldAssetBounds[]=[
  {min:[0,0,0],max:[Infinity,1,1]},
  {min:[NaN,0,0],max:[1,1,1]},
  {min:[0,0,0],max:[1,0,1]},
  {min:[1,0,0],max:[0,1,1]},
 ]
 for(const bounds of invalid){
  const catalog=new Map(worldAssetKits.flatMap(k=>k.roots).map(name=>[name,bounds]))
  const plan=buildHeronWorldDressing(input,catalog)
  assert.deepEqual(plan.placements,[])
  assert.equal(plan.replacementKeys.size,0);assert.equal(plan.groundReplacementKeys.size,0)
 }
 assert.equal(digest(input),originalInput,'failure paths cannot mutate the source plan or collision geometry')
})

test('the actual additive roots retain finite metre-scale geometry, centred footprints and base origins',async()=>{
 const {catalog,roots}=await world()
 assert.equal(catalog.size,11)
 for(const [name,bounds]of catalog){
  const asset=roots.get(name)!
  assert(asset.matrixWorld.elements.every(Number.isFinite),`${name}: invalid exported node transform`)
  assert(Math.abs(bounds.min[1])<.0001,`${name}: exported base is not at zero`)
  for(const axis of [0,2])assert(Math.abs(bounds.min[axis]+bounds.max[axis])<.0001,`${name}: footprint is not centred`)
  for(const axis of [0,1,2])assert(bounds.max[axis]>bounds.min[axis]&&bounds.max[axis]-bounds.min[axis]<3,`${name}: invalid metre scale`)
 }
})

test('the loaded dressing plan is deterministic, preserves inputs and retires only successfully emitted originals',async()=>{
 const {catalog,roots,input:worldInput,plan}=await world()
 assert.deepEqual(buildHeronWorldDressing(worldInput,catalog),plan)
 assert.equal(digest(input),originalInput,'original dressing, ground plants, doors and physics remain unchanged')
 assert.equal(plan.placements.length,103)
 assert.deepEqual(plan.stats,{replacements:18,storeContents:16,workshopContents:4,ferns:53,tableArrangements:4})
 const originalKeys=new Set(dressing.items.map(worldReplacementKey))
 const groundKeys=new Set(groundPlan.plants.map(worldReplacementKey))
 for(const key of plan.replacementKeys){
  assert(originalKeys.has(key),'replacement key must identify an actual original instance')
  assert(plan.placements.some(p=>p.replacementKey===key),'no original is hidden without its replacement')
 }
 for(const key of plan.groundReplacementKeys){
  assert(groundKeys.has(key),'ground replacement key must identify an actual original clump')
  assert(plan.placements.some(p=>p.replacementKey===key&&p.role==='planter-fern'))
 }
 for(const p of plan.placements){
  const actual=geometry(roots.get(p.asset)!,mapMatrix(p))
  assert([...actual.bounds.min,...actual.bounds.max,p.scale].every(Number.isFinite))
  assert(p.scale>0);assertVerticesInside(actual.vertices,p.bounds,p.asset)
  if(p.enclosure)assertVerticesInside(actual.vertices,p.enclosure,`${p.asset}: existing enclosure`)
  const supportedY=p.role==='table-fern'?p.y+roots.get(p.asset)!.userData.stemBasalY*p.scale:actual.bounds.min.y
  assert(Math.abs(supportedY-p.support.y)<.001,`${p.asset}: supported base meets the declared surface`)
  for(const door of layout.openings.filter(d=>d.kind.includes('door'))){
   if(p.bounds.max[1]<=door.y+.02||p.bounds.min[1]>=door.y+door.height)continue
   // Check the specified portal envelope independently of the planner's helper,
   // including home inner doors as well as exterior entrances.
   const halfWidth=door.width/2+.3,halfDepth=.85
   const dx=door.axis==='x'?halfWidth:halfDepth,dz=door.axis==='x'?halfDepth:halfWidth
   const overlaps=p.bounds.min[0]<door.x+dx-.001&&p.bounds.max[0]>door.x-dx+.001&&
    p.bounds.min[2]<door.z+dz-.001&&p.bounds.max[2]>door.z-dz+.001
   assert(!overlaps,`${p.asset}/${p.role}: blocks ${door.kind} at ${door.x},${door.z}`)
  }
 }
 // Losing any single optional root cannot retire its corresponding original.
 for(const name of ['WORLD_TRASH_BAG','WORLD_AIRCON_RUST']){
  const missing=new Map(catalog);missing.delete(name)
  const fallback=buildHeronWorldDressing(worldInput,missing)
  const affected=plan.placements.filter(p=>p.asset===name&&p.replacementKey).map(p=>p.replacementKey!)
  for(const key of affected)assert(!fallback.replacementKeys.has(key),`${name}: unavailable asset must retain its source instance`)
 }
 const noFerns=new Map([...catalog].filter(([name])=>!name.startsWith('WORLD_FERN_')))
 const fallback=buildHeronWorldDressing(worldInput,noFerns)
 assert.equal(fallback.groundReplacementKeys.size,0)
 assert.equal(fallback.stats.tableArrangements,0,'never emit an empty pot when its fern cannot load')
})

test('contents require their existing host collider, and absent planting/support metadata preserves the original art',async()=>{
 const {catalog,input:worldInput,plan}=await world()
 const withoutColliders=buildHeronWorldDressing({...worldInput,solids:solids.filter(s=>s.id!=='dress')},catalog)
 assert.equal(withoutColliders.stats.storeContents,0)
 assert.equal(withoutColliders.stats.workshopContents,0)
 assert.deepEqual(withoutColliders.replacementKeys,plan.replacementKeys,'unrelated supported replacements remain available')
 for(const missing of [{groundPlants:undefined},{planters:undefined}]){
  const fallback=buildHeronWorldDressing({...worldInput,...missing},catalog)
  assert.equal(fallback.groundReplacementKeys.size,0)
 }
 const originalWeed=groundPlan.plants.find(p=>p.asset==='WEED_TUFT_A'&&p.source?.startsWith('planter:'));assert(originalWeed)
 const malformed=[undefined,null,17,{},['planter:K07']].map(source=>({...originalWeed,source}))
 const before=digest(malformed)
 const malformedPlan=buildHeronWorldDressing({...worldInput,groundPlants:malformed as unknown as WorldDressingInput['groundPlants']},catalog)
 assert.equal(malformedPlan.groundReplacementKeys.size,0,'malformed source metadata retains the original ground plants')
 assert.equal(digest(malformed),before)
 for(const missing of [{potSoilSurfaceY:undefined},{potSoilRadius:undefined},{fernStemXZ:undefined},{fernStemBasalY:undefined}]){
  const fallback=buildHeronWorldDressing({...worldInput,...missing},catalog)
  assert.equal(fallback.stats.tableArrangements,0)
  assert(!fallback.placements.some(p=>p.role==='table-pot'||p.role==='table-fern'),'never emit an unsupported partial arrangement')
 }
})

test('bin-store contents rest on the actual slab, clear both exported gates and stay inside existing collision',async()=>{
 const {roots,plan}=await world(),structures=await kit('heron-reach-sl-structures.glb')
 const source=root(structures,'hr_prop_bin_store_3bay'),gate=root(structures,'hr_prop_bin_store_gate_leaf')
 const slab=horizontalSurface(geometry(source),'mat_concrete_cast',.1)
 const hosts=dressing.items.filter(p=>p.asset==='hr_prop_bin_store_3bay'),contents=plan.placements.filter(p=>p.role==='bin-store')
 assert.equal(hosts.length,4);assert.equal(contents.length,16)
 for(const host of hosts){
  const inverse=mapMatrix(host).invert(),mine=contents.filter(p=>p.support.host===worldReplacementKey(host))
  assert.equal(mine.length,4,'three bins and one bag in each existing store')
  const gates=dressing.items.filter(p=>p.asset==='hr_prop_bin_store_gate_leaf'&&Math.hypot(p.x-host.x,p.z-host.z)<2)
  assert.equal(gates.length,2,'validate the actual mirrored and swung gate placements')
  const occupied:THREE.Box3[]=[]
  for(const p of mine){
   const actual=geometry(roots.get(p.asset)!,mapMatrix(p))
   const local=geometry(roots.get(p.asset)!,inverse.clone().multiply(mapMatrix(p)))
   assertSupported(local.bounds,slab,p.asset)
   assertInsideCollider(actual.bounds,host,p.asset)
   // Contact with the floor is intentional; every surface above it must remain clear.
   const aboveFloor={...geometry(source),triangles:geometry(source).triangles.filter(({triangle:t})=>
    Math.max(t.a.y,t.b.y,t.c.y)>.102)}
   assertClearOfGeometry(local.bounds,aboveFloor,`${p.asset}: brickwork, piers or rear buffer`,.01)
   for(const leaf of gates)assertClearOfGeometry(actual.bounds,geometry(gate,mapMatrix(leaf)),`${p.asset}: existing gate`,.015)
   for(const other of occupied)assert(!local.bounds.intersectsBox(other),`${p.asset}: contents overlap`)
   occupied.push(local.bounds)
  }
 }
})

test('workshop stock rests on the actual lower shelf and clears the tabletop, legs, tools and original collider',async()=>{
 const {roots,plan}=await world(),props=await kit('heron-reach-props.glb')
 const source=geometry(root(props,'WORK_BENCH')),shelf=horizontalSurface(source,'hr_prop_formica_grey',.219)
 const underside=horizontalSurface(source,'hr_timber',.855)
 const obstructions={...source,triangles:source.triangles.filter(({triangle:t})=>Math.max(t.a.y,t.b.y,t.c.y)>shelf.height+.002)}
 const contents=plan.placements.filter(p=>p.role==='workshop-shelf'),hosts=dressing.items.filter(p=>p.asset==='WORK_BENCH')
 assert.equal(contents.length,4)
 for(const host of hosts){
  const mine=contents.filter(p=>p.support.host===worldReplacementKey(host)),inverse=mapMatrix(host).invert(),occupied:THREE.Box3[]=[]
  assert.equal(mine.length,2)
  for(const p of mine){
   const actual=geometry(roots.get(p.asset)!,mapMatrix(p)),local=geometry(roots.get(p.asset)!,inverse.clone().multiply(mapMatrix(p)))
   assertSupported(local.bounds,shelf,p.asset)
   assert(local.bounds.max.y<underside.height-.01,`${p.asset}: must fit below the actual tabletop`)
   assertInsideCollider(actual.bounds,host,p.asset)
   assertClearOfGeometry(local.bounds,obstructions,`${p.asset}: existing bench geometry`,.005)
   for(const other of occupied)assert(!local.bounds.intersectsBox(other),`${p.asset}: stock overlaps`)
   occupied.push(local.bounds)
  }
 }
})

test('planter ferns replace only exact selected weeds, retain soil contact and remain below low-cover height',async()=>{
 const {roots,plan}=await world(),ferns=plan.placements.filter(p=>p.role==='planter-fern')
 assert(ferns.length>0);assert.equal(ferns.length,plan.groundReplacementKeys.size)
 assert(new Set(ferns.map(p=>p.asset)).size>=3,'retain several natural fern variants')
 for(const p of ferns){
  const old=groundPlan.plants.find(plant=>worldReplacementKey(plant)===p.replacementKey)
  assert(old);assert.equal(old.asset,'WEED_TUFT_A')
  assert(old.source?.startsWith('planter:'))
  assert.equal(p.ry,old.ry,'fern retains the selected clump rotation')
  const bed=layout.cover.find(b=>`planter:${b.id}`===old.source);assert(bed)
  const [x,z,w,d]=bed.rect,soil=bed.y+bed.height-.15,actual=geometry(roots.get(p.asset)!,mapMatrix(p))
  assert(Math.abs(actual.bounds.min.y-soil)<.001)
  assert(actual.bounds.max.y<=1.25)
  assert(actual.bounds.min.x>=x+.12&&actual.bounds.max.x<=x+w-.12,'fern clears the actual planter X rims')
  assert(actual.bounds.min.z>=z+.12&&actual.bounds.max.z<=z+d-.12,'fern clears the actual planter Z rims')
 }
 const protectedPlants=groundPlan.plants.filter(p=>p.asset!=='WEED_TUFT_A'||!p.source?.startsWith('planter:'))
 for(const p of protectedPlants)assert(!plan.groundReplacementKeys.has(worldReplacementKey(p)),'other ground and planter plants remain')
})

test('review cameras have standing capsule clearance against every existing solid',()=>{
 const plan=buildHeronWorldDressing(input,new Map()),radius=.34,height=1.8
 for(const [name,x,y,z]of plan.reviewViews){
  const bottom=y+radius,top=y+height-radius
  for(const s of solids){
   const box=solidBox(s)
   const dx=Math.max(box.min.x-x,x-box.max.x,0),dz=Math.max(box.min.z-z,z-box.max.z,0)
   const dy=Math.max(box.min.y-top,bottom-box.max.y,0)
   assert(Math.hypot(dx,dy,dz)>=radius-.001,`${name}: camera capsule overlaps ${s.id} at ${s.x+72},${s.y},${s.z+60}`)
  }
 }
})

test('additional growth fills spare planter soil and preserves existing plant centres',async()=>{
 const {roots,plan}=await world(),infill=plan.placements.filter(p=>p.role==='planter-infill')
 assert.equal(infill.length,31)
 assert(new Set(infill.map(p=>p.support.host)).size>=7,'fill the large beds; the smallest bed already has closely spaced planting')
 for(const bed of layout.cover.filter(b=>b.kind.includes('planter'))){
  const host='planter:'+bed.id,[x,z,w,d]=bed.rect,soil=bed.y+bed.height-.15
  if(w*d>=8)assert(infill.some(p=>p.support.host===host),`${bed.id}: large bed retains spare soil for supported growth`)
  const occupied=groundPlan.plants.filter(p=>p.source===host).map(p=>[p.x,p.z])
  for(const p of infill.filter(p=>p.support.host===host)){
   const actual=geometry(roots.get(p.asset)!,mapMatrix(p)),centre=actual.bounds.getCenter(new THREE.Vector3())
   assert(Math.abs(actual.bounds.min.y-soil)<.001)
   assert(actual.bounds.max.y<=1.25)
   assert(actual.bounds.min.x>=x+.12&&actual.bounds.max.x<=x+w-.12)
   assert(actual.bounds.min.z>=z+.12&&actual.bounds.max.z<=z+d-.12)
   assert(occupied.every(([px,pz])=>Math.hypot(px-centre.x,pz-centre.z)>=.449),'new clumps leave space around existing shrub roots')
   assert.equal(p.replacementKey,undefined,'infill does not hide existing planting')
   occupied.push([centre.x,centre.z])
  }
 }
})

test('four home arrangements stand on decoded tabletops and put each fern stem inside the actual pot soil cap',async()=>{
 const {roots,plan}=await world()
 const arch=geometry(await kit('heron-reach-arch.glb'),new THREE.Matrix4().makeTranslation(72,0,60),'hr_wood_furniture')
 const pots=plan.placements.filter(p=>p.role==='table-pot'),ferns=plan.placements.filter(p=>p.role==='table-fern')
 assert.equal(pots.length,4);assert.equal(ferns.length,4);assert.equal(plan.stats.tableArrangements,4)
 assert.equal(new Set(pots.map(p=>p.support.host)).size,4,'one arrangement in each home quadrant')
 for(const pot of pots){
  const fern=ferns.find(p=>p.support.host===pot.support.host);assert(fern)
  const host=solids.find(s=>s.id==='home-table'&&solidBox(s).containsPoint(new THREE.Vector3(pot.x,pot.support.y,pot.z)));assert(host)
  const hostBounds=solidBox(host),nativePot=roots.get(pot.asset)!,nativeFern=roots.get(fern.asset)!
  const potGeometry=geometry(nativePot,mapMatrix(pot)),fernGeometry=geometry(nativeFern,mapMatrix(fern))
  // The unchanged architecture uses a 15.0148775 mm position grid: tabletop
  // edges differ from source bounds by up to 5.91 mm, and source Y=.75 exports
  // as .7489127325. Only the X/Z lookup window is expanded; support contact
  // uses the actual triangles and the same 1 mm placement tolerance.
  const tableSource={...arch,triangles:arch.triangles.filter(({triangle:t})=>
   [t.a,t.b,t.c].every(v=>v.x>=hostBounds.min.x-.008&&v.x<=hostBounds.max.x+.008&&v.z>=hostBounds.min.z-.008&&v.z<=hostBounds.max.z+.008))}
  const tabletop=horizontalSurface(tableSource,'hr_wood_furniture',pot.support.y)
  assert(Math.abs(tabletop.height-.7489127325)<1e-9,'unchanged architecture tabletop geometry')
  assertSupported(potGeometry.bounds,tabletop,pot.support.host)
  for(const bounds of [potGeometry.bounds,fernGeometry.bounds]){
   for(const [x,z]of footprintCorners(bounds))assert(x>=hostBounds.min.x&&x<=hostBounds.max.x&&z>=hostBounds.min.z&&z<=hostBounds.max.z,
    `${pot.support.host}: arrangement extends beyond the existing table collision footprint`)
  }
  assert(fernGeometry.bounds.max.y<=1.30,'table plants remain below the authored presentation height')
  const soilHeight=nativePot.userData.soilSurfaceY,soilRadius=nativePot.userData.soilRadius,stem=nativeFern.userData.stemXZ,stemY=nativeFern.userData.stemBasalY
  assert.equal(typeof soilHeight,'number');assert(Math.abs(soilHeight-.185)<.001)
  assert.equal(typeof soilRadius,'number');assert(soilRadius>0&&soilRadius<.12)
  assert(Array.isArray(stem)&&stem.length===2&&stem.every(Number.isFinite),'use the actual stem anchor, not the frond bounds centre')
  assert.equal(typeof stemY,'number');assert(Number.isFinite(stemY)&&stemY>=0&&stemY<.01)
  const soilMaterial=potGeometry.triangles.find(({material})=>material.toLowerCase().includes('soil'))?.material
  assert(soilMaterial,'the pot must contain an exported soil surface')
  const soil=horizontalSurface(potGeometry,soilMaterial,pot.y+soilHeight*pot.scale)
  const stemPosition=new THREE.Vector3(stem[0],stemY,stem[1]).applyMatrix4(mapMatrix(fern))
  assert(Math.abs(stemPosition.y-soil.height)<.001,'fern stem meets the actual pot soil, not its rim or the tabletop')
  assert(supportedAt(soil,stemPosition.x,stemPosition.z),'fern stem lies inside an actual exported soil triangle')
  assert(Math.hypot(stemPosition.x-pot.x,stemPosition.z-pot.z)<soilRadius*pot.scale-.002,'fern stem clears the soil edge')
 }
})
