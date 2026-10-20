import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import spec from '../docs/maps/heron-reach-32/blueprints/build-spec.json'
import {layout,solids,OX,OZ} from '../src/onsite/heronReach.ts'
import {CONFIG} from '../src/wwb/game/config.ts'
import {Physics,RAPIER,initPhysics} from '../src/wwb/engine/physics.ts'
import {loadBuildingArt,removeLegacyPrivateStairs,removeLegacyNarrowJoinery,removeLegacyAdjacentLeaves,removeLegacyUpperEntryLeaves} from '../src/onsite/heronBuildingArt.ts'
import {removeLegacyCoreStairs} from '../src/onsite/heronStairArt.ts'
import type {HeronReachMaterials} from '../src/onsite/heronReachArt.ts'

const asset='public/models/heron-reach/building-detail.glb'
const manifestPath='assets/blender/heron-reach/building-detail-manifest.json'
const architecturePath='public/models/heron-reach/heron-reach-arch.glb'
const homes=spec.homeInstances.filter(h=>h.module==='H2-L')
const narrowDoors=layout.openings.filter(o=>o.kind==='inner-door'&&o.width===.8)
type Point={x:number;y:number;z:number}
type Triangle={shape:THREE.Triangle;bounds:THREE.Box3;material:string}
type Home=typeof homes[number]
const epsilon=.006
const hash=(path:string)=>createHash('sha256').update(readFileSync(path)).digest('hex')
const manifest=()=>JSON.parse(readFileSync(manifestPath,'utf8'))
const owns=(h:Home,x:number,z:number,margin=0)=>x>=h.x-margin&&x<=h.x+9+margin&&z>=h.z-margin&&z<=h.z+8+margin
const point=(h:Home,x:number,y:number,z:number):Point=>({x:h.x+x,y,z:h.z+(h.mirrorZ?8-z:z)})
const vector=(p:Point)=>new THREE.Vector3(p.x,p.y,p.z)
const box=(b:{min:number[];max:number[]})=>new THREE.Box3(new THREE.Vector3(...b.min as [number,number,number]),new THREE.Vector3(...b.max as [number,number,number]))

/** Decode the actual compressed geometry; omit image decoding only in this Node fixture. */
async function loadGeometry(path:string){
 const original=readFileSync(path),length=original.readUInt32LE(12)
 const json=JSON.parse(original.subarray(20,20+length).toString())
 json.materials=json.materials?.map((m:{name:string})=>({name:m.name,doubleSided:true}))
 delete json.images;delete json.textures;delete json.samplers
 for(const field of ['extensionsUsed','extensionsRequired'])if(json[field])json[field]=json[field].filter((s:string)=>s!=='EXT_texture_webp')
 const encoded=Buffer.from(JSON.stringify(json)),body=Buffer.alloc(Math.ceil(encoded.length/4)*4,32);encoded.copy(body)
 const tail=original.subarray(20+length),header=Buffer.alloc(20)
 header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(20+body.length+tail.length,8)
 header.writeUInt32LE(body.length,12);header.writeUInt32LE(0x4e4f534a,16)
 const bytes=Uint8Array.from(Buffer.concat([header,body,tail]))
 const {scene}=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer,'')
 scene.updateMatrixWorld(true);return scene
}

function triangles(scene:THREE.Object3D,visit:(t:Triangle)=>void){
 scene.traverse(o=>{
  if(!(o instanceof THREE.Mesh))return
  const g=o.geometry,p=g.attributes.position,index=g.index,materials=Array.isArray(o.material)?o.material:[o.material]
  for(let i=0;i<(index?.count??p.count);i+=3){
   const vertices=[0,1,2].map(k=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+k):i+k).applyMatrix4(o.matrixWorld).add(new THREE.Vector3(OX,0,OZ)))
   const group=g.groups.find(group=>i>=group.start&&i<group.start+group.count)
   visit({shape:new THREE.Triangle(vertices[0],vertices[1],vertices[2]),bounds:new THREE.Box3().setFromPoints(vertices),material:materials[group?.materialIndex??0]?.name??''})
  }
 })
}
function indexGeometry(scene:THREE.Object3D,accept=(t:Triangle)=>true){
 const all:Triangle[]=[],cells=new Map<string,Triangle[]>(),materials=new Set<string>();let meshes=0
 scene.traverse(o=>{if(o instanceof THREE.Mesh)meshes++})
 triangles(scene,t=>{
  if(!accept(t))return
  all.push(t);materials.add(t.material)
  for(let x=Math.floor(t.bounds.min.x);x<=Math.floor(t.bounds.max.x);x++)for(let z=Math.floor(t.bounds.min.z);z<=Math.floor(t.bounds.max.z);z++){
   const key=x+':'+z,list=cells.get(key);if(list)list.push(t);else cells.set(key,[t])
  }
 })
 const near=(p:Point,radius=0)=>{
  const result=new Set<Triangle>()
  for(let x=Math.floor(p.x-radius);x<=Math.floor(p.x+radius);x++)for(let z=Math.floor(p.z-radius);z<=Math.floor(p.z+radius);z++)for(const t of cells.get(x+':'+z)??[])result.add(t)
  return [...result]
 }
 return {all,meshes,materials,near}
}
let originalPromise:Promise<THREE.Group>|undefined,newPromise:Promise<THREE.Group>|undefined,geometryPromise:Promise<ReturnType<typeof indexGeometry>>|undefined
const original=()=>originalPromise??=loadGeometry(architecturePath)
const replacement=()=>newPromise??=loadGeometry(asset)
const shipped=()=>geometryPromise??=replacement().then(scene=>indexGeometry(scene))
let compositePromise:Promise<ReturnType<typeof indexGeometry>>|undefined
const composite=()=>compositePromise??=(async()=>{
 const scene=(await original()).clone(true)
 removeLegacyPrivateStairs(scene);removeLegacyNarrowJoinery(scene);removeLegacyAdjacentLeaves(scene);removeLegacyUpperEntryLeaves(scene)
 scene.add((await replacement()).clone(true));scene.updateMatrixWorld(true)
 return indexGeometry(scene,t=>homes.some(h=>owns(h,t.bounds.min.x,t.bounds.min.z,.1)&&owns(h,t.bounds.max.x,t.bounds.max.z,.1)))
})()
const privateTreads=solids.filter(s=>s.id==='stair'&&homes.some(h=>owns(h,s.x+OX,s.z+OZ)))
const privateLandings=solids.filter(s=>s.id==='landing'&&homes.some(h=>owns(h,s.x+OX,s.z+OZ)))
const top=(s:typeof solids[number]):Point=>({x:s.x+OX,y:s.y+s.h/2,z:s.z+OZ})
function hitsAt(p:Point,list:Triangle[],direction:THREE.Vector3){
 const ray=new THREE.Ray(vector(p),direction),hit=new THREE.Vector3(),hits:{triangle:Triangle;point:THREE.Vector3;distance:number}[]=[]
 for(const t of list)if(ray.intersectTriangle(t.shape.a,t.shape.b,t.shape.c,false,hit))hits.push({triangle:t,point:hit.clone(),distance:hit.distanceTo(ray.origin)})
 return hits.sort((a,b)=>a.distance-b.distance)
}

test('compressed building construction has recorded provenance, shared materials and bounded geometry costs',async()=>{
 const geometry=await shipped(),m=manifest(),bytes=readFileSync(asset)
 assert.equal(hash(asset),m.compressedGLBSHA256);assert.equal(bytes.byteLength,m.compressedGLBBytes)
 assert.equal(hash(m.builder),m.builderSHA256);assert.equal(hash('assets/blender/heron-reach/layout.json'),m.layoutSHA256)
 assert.equal(geometry.all.length,m.triangles);assert.equal(geometry.meshes,m.materialBatches)
 assert(geometry.all.length<=60_000);assert(geometry.meshes<=52);assert(bytes.byteLength<1_000_000)
 // Four spatial glass batches are the explicit cost of keeping the eight upper
 // entrance panes; the original twelve materials still use at most 48 batches.
 let glassBatches=0;(await replacement()).traverse(o=>{if(o instanceof THREE.Mesh&&(o.material as THREE.Material).name==='hr_glass')glassBatches++})
 assert.equal(glassBatches,4);assert(geometry.meshes-glassBatches<=48)
 const json=JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)).toString())
 assert.equal(json.images?.length??0,0)
 const library=JSON.parse(readFileSync('public/materials/heron/runtime-materials.json','utf8'))
 for(const name of geometry.materials)assert(name==='hr_stair_concrete'||library[name],`unrecorded surface ${name}`)
 assert.deepEqual([...geometry.materials].sort(),[...m.sharedMaterials].sort())
 const allowed=m.features.map((f:any)=>box(f.mapBounds).expandByScalar(epsilon)) as THREE.Box3[]
 for(const h of homes)allowed.push(new THREE.Box3(new THREE.Vector3(h.x-epsilon,h.y-.16,h.z-epsilon),new THREE.Vector3(h.x+9+epsilon,h.y+5.8,h.z+8+epsilon)))
 assert.equal(m.upperEntryLeaves.length,8)
 for(const leaf of m.upperEntryLeaves){
  for(const bounds of [leaf.newLeafBounds,leaf.newGlassBounds])allowed.push(box(bounds).expandByScalar(epsilon))
  for(const hinge of leaf.hinges){
   allowed.push(box(hinge.framePlateBounds).expandByScalar(epsilon),box(hinge.leafPlateBounds).expandByScalar(epsilon))
   allowed.push(new THREE.Box3().setFromPoints([new THREE.Vector3(...hinge.start as [number,number,number]),new THREE.Vector3(...hinge.end as [number,number,number])]).expandByScalar(hinge.radius+epsilon))
  }
  const support=box(leaf.supportWallBounds)
  assert(solids.some(s=>new THREE.Box3(new THREE.Vector3(s.x+OX-s.w/2,s.y-s.h/2,s.z+OZ-s.d/2),new THREE.Vector3(s.x+OX+s.w/2,s.y+s.h/2,s.z+OZ+s.d/2)).expandByScalar(epsilon).containsBox(support)),`${leaf.id} has no physical backing wall`)
  assert(Math.abs(leaf.newGlassBounds.min[2]-leaf.opening.z)<=.167+epsilon&&Math.abs(leaf.newGlassBounds.max[2]-leaf.opening.z)<=.167+epsilon,`${leaf.id} exceeds its bounded exterior projection`)
 }
 for(const t of geometry.all){
  assert([t.shape.a,t.shape.b,t.shape.c].every(v=>v.toArray().every(Number.isFinite)))
  assert(allowed.some(b=>b.containsBox(t.bounds)),`unrecorded construction volume ${t.material} ${t.bounds.min.toArray()}/${t.bounds.max.toArray()}`)
 }
 assert.equal(m.privateStairs.length,8);assert.equal(m.narrowDoorJoinery.length,16)
})

test('all 144 private treads preserve physical height and the full 1.2 metre flight width',async()=>{
 const geometry=await shipped();assert.equal(privateTreads.length,144)
 for(const tread of privateTreads)for(const dx of [-.58,0,.58]){
  const p=top(tread);p.x+=dx
  const hits=hitsAt({...p,y:p.y+.04},geometry.near(p),new THREE.Vector3(0,-1,0)).filter(h=>Math.abs(h.point.y-p.y)<.05)
  assert(hits.some(h=>Math.abs(h.point.y-p.y)<=epsilon),`missing tread surface ${JSON.stringify(p)}`)
  assert(hits.every(h=>h.point.y<=p.y+epsilon),`added raised surface at ${JSON.stringify(p)}`)
 }
 for(const h of homes)assert.equal(privateTreads.filter(s=>owns(h,s.x+OX,s.z+OZ)).length,18,h.id)
})

test('combined private stair geometry clears both mirrored routes and leaves the real floor void open',async()=>{
 const geometry=await composite(),samples=privateTreads.map(top)
 assert.equal(privateLandings.length,8)
 for(const landing of privateLandings)for(const dx of [-.675,0,.675]){const p=top(landing);p.x+=dx;samples.push(p)}
 for(const h of homes)for(const [x,y,z]of [[6.78,3,6.5],[8.13,6,6.5]])samples.push(point(h,x,y,z))
 for(const p of samples){
  for(const hit of hitsAt({...p,y:p.y+.025},geometry.near(p),new THREE.Vector3(0,1,0)))assert(hit.point.y-p.y>=2.4-epsilon,`render headroom ${(hit.point.y-p.y).toFixed(3)}m at ${JSON.stringify(p)} (${hit.triangle.material})`)
  const body=new THREE.Box3(new THREE.Vector3(p.x-.38,p.y+.4,p.z-.38),new THREE.Vector3(p.x+.38,p.y+1.8,p.z+.38))
  for(const t of geometry.near(p,.38))assert(!body.intersectsBox(t.bounds)||!body.intersectsTriangle(t.shape),`body intersects render geometry at ${JSON.stringify(p)} (${t.material})`)
 }
 // Test actual floor/ceiling surfaces over the void and around it, not merely a
 // manifest declaration that the original full-home cards were retired.
 for(const h of homes)for(const [material,y]of [['hr_ceiling',5.795],['hr_floor_laminate',6.004]] as const){
  for(const x of [6.3,7.4,8.6])for(const z of [2.3,3.9,5.7]){
   const p=point(h,x,y+.03,z)
   assert(!hitsAt(p,geometry.near(p).filter(t=>t.material===material),new THREE.Vector3(0,-1,0)).some(hit=>Math.abs(hit.point.y-y)<.015),`${h.id} ${material} still bridges the stair void`)
  }
  for(const [x,z]of [[3,4],[7,1],[7,7]]){
   const p=point(h,x,y+.03,z)
   assert(hitsAt(p,geometry.near(p).filter(t=>t.material===material),new THREE.Vector3(0,-1,0)).some(hit=>Math.abs(hit.point.y-y)<epsilon),`${h.id} lost surrounding ${material}`)
  }
 }
})

test('private solid dividers and guards are visible and handrails follow both actual flight directions',async()=>{
 const geometry=await shipped(),m=manifest()
 for(const authored of m.privateStairs){
  const h=homes.find(h=>h.id===authored.id);assert(h)
  for(const flight of authored.flights){
   const expected=(flight.first?-1:1)*(h.mirrorZ?-1:1)*spec.stairs['ST-H'].rise/spec.stairs['ST-H'].going
   for(const [from,to,inner]of [[flight.rail.start,flight.rail.end,true],[flight.rail.outerStart,flight.rail.outerEnd,false]]as const){
    const start=new THREE.Vector3(...from as [number,number,number]),end=new THREE.Vector3(...to as [number,number,number]),delta=end.clone().sub(start)
    assert(Math.abs(delta.y/delta.z-expected)<1e-5)
    for(const fraction of [.2,.5,.8]){
     const centre=start.clone().lerp(end,fraction),direction=new THREE.Vector3((flight.first?1:-1)*(inner?1:-1),0,0)
     const origin=centre.clone().addScaledVector(direction,-.12)
     const hit=hitsAt(origin,geometry.near(centre,.15),direction)[0]
     assert(hit&&hit.distance<.15,`${flight.id} has no exposed handrail beside its route`)
     assert.equal(hit?.triangle.material,'hr_steel_black',`${flight.id} handrail is buried or absent at ${centre.toArray()}`)
    }
   }
  }
  const divider=solids.find(s=>s.id===authored.homeId+'-divider');assert(divider)
  for(const y of [3.6,4.8,6.6])for(const localZ of [3.7,4.6,5.6]){
   const p=point(h,7.3,y,localZ),hit=hitsAt(p,geometry.near(p,.3),new THREE.Vector3(1,0,0))[0]
   assert(hit&&hit.distance<.25,`${h.id} has invisible solid divider at ${JSON.stringify(p)}`)
  }
  const guard=solids.find(s=>s.id===authored.homeId+'-guard');assert(guard)
  for(const x of [6.3,6.75,7.2]){
   const p=point(h,x,6.6,6.1),hit=hitsAt(p,geometry.near(p,.4),new THREE.Vector3(0,0,h.mirrorZ?1:-1))[0]
   assert(hit&&hit.distance<.3,`${h.id} has an invisible solid landing guard`)
  }
 }
})

test('new building detail and replaced narrow joinery preserve full standing doorway approaches',async()=>{
 const addition=await shipped(),combined=await composite(),radius=CONFIG.player.radius,height=2*(CONFIG.player.halfHeight+radius)
 assert.equal(radius,.38);assert.equal(narrowDoors.length,16)
 await initPhysics();const physics=new Physics(),capsule=new RAPIER.Capsule(CONFIG.player.halfHeight,radius)
 for(const s of solids)physics.addStaticBox(new THREE.Vector3(s.x,s.y,s.z),new THREE.Vector3(s.w,s.h,s.d))
 physics.step(1/60)
 let narrowSamples=0;const obstructed:string[]=[]
 try{for(const o of layout.openings.filter(o=>o.kind==='door'||o.kind==='inner-door'||o.kind==='inner-arch')){
  const narrow=narrowDoors.includes(o),geometry=narrow?combined:addition
  // Cover the open leaf's entire depth, not just the plane through its jambs.
  for(const depth of [-.85,-.45,0,.45,.85]){
   const centre={x:o.x+(o.axis==='z'?o.normal*depth:0),y:o.y,z:o.z+(o.axis==='x'?o.normal*depth:0)}
   const physicalHit=physics.world.intersectionWithShape({x:centre.x-OX,y:o.y+height/2+.04,z:centre.z-OZ},{x:0,y:0,z:0,w:1},capsule)
   if(narrow){assert.equal(physicalHit,null,`${o.owner} narrow-door fixture must be a physically clear standing approach`);narrowSamples++}
   // Other door approaches can require a turn or a stair step. Those positions
   // do not define a valid level standing capsule and are not art-clearance probes.
   if(physicalHit)continue
   const body=new THREE.Box3(new THREE.Vector3(centre.x-radius,o.y+.04,centre.z-radius),new THREE.Vector3(centre.x+radius,o.y+height+.04,centre.z+radius))
   const obstruction=geometry.near(centre,radius).find(t=>body.intersectsBox(t.bounds)&&body.intersectsTriangle(t.shape))
   if(obstruction)obstructed.push(`${o.owner} ${o.kind} ${o.width}m at ${o.x}/${o.z}/${o.y} approach ${depth} intersects ${obstruction.material} ${obstruction.bounds.min.toArray()}/${obstruction.bounds.max.toArray()}`)
  }
 }}finally{physics.world.free()}
 assert.equal(narrowSamples,80,'all five real standing approach positions for each of the sixteen narrow doors')
 assert.equal(obstructed.length,0,`${obstructed.length} physically clear doorway approaches intersect render geometry:\n${obstructed.join('\n')}`)
})

function preservedFingerprint(scene:THREE.Object3D){
 const outside=createHash('sha256'),walls=createHash('sha256'),partitions=createHash('sha256'),landings=createHash('sha256'),doorCaps=createHash('sha256'),wideFrames=createHash('sha256')
 let total=0,outsideCount=0,wallCount=0,partitionCount=0,landingCount=0,doorCapCount=0,wideFrameCount=0,upperLeafGlassCount=0
 const plasterWalls=solids.filter(b=>b.mat==='plaster'&&/^(wall-|sill-|lintel-)/.test(b.id))
 const boxContains=(t:Triangle,s:typeof solids[number])=>t.bounds.min.x>=s.x+OX-s.w/2-.02&&t.bounds.max.x<=s.x+OX+s.w/2+.02&&t.bounds.min.y>=s.y-s.h/2-.02&&t.bounds.max.y<=s.y+s.h/2+.02&&t.bounds.min.z>=s.z+OZ-s.d/2-.02&&t.bounds.max.z<=s.z+OZ+s.d/2+.02
 triangles(scene,t=>{
  total++;const vertices=[t.shape.a,t.shape.b,t.shape.c],key=t.material+':'+vertices.flatMap(v=>v.toArray()).join(',')+';'
  const inside=homes.some(h=>owns(h,t.bounds.min.x,t.bounds.min.z,.02)&&owns(h,t.bounds.max.x,t.bounds.max.z,.02))
  if(!inside){outside.update(key);outsideCount++}
  // Exempt only the eight retired door inserts, not the other home windows.
  const upperLeafGlass=t.material==='hr_glass'&&homes.some(h=>vertices.every(p=>{
   const x=p.x-h.x,z=h.mirrorZ?8-(p.z-h.z):p.z-h.z
   return x>=5.685&&x<=5.75&&z>=.332&&z<=1.088&&p.y>=6.955&&p.y<=7.998
  }))
  if(upperLeafGlass)upperLeafGlassCount++
  if(inside&&!upperLeafGlass&&['hr_brick_stock','hr_brick_red','hr_brick_painted','hr_glass','hr_window_interior','hr_window_dark'].includes(t.material)){walls.update(key);wallCount++}
  if(t.material==='hr_plaster'&&plasterWalls.some(b=>vertices.every(p=>p.x>=b.x+OX-b.w/2-.008&&p.x<=b.x+OX+b.w/2+.008&&p.y>=b.y-b.h/2-.008&&p.y<=b.y+b.h/2+.008&&p.z>=b.z+OZ-b.d/2-.008&&p.z<=b.z+OZ+b.d/2+.008))){partitions.update(key);partitionCount++}
  if(['hr_concrete_cast','hr_concrete_board'].includes(t.material)&&privateLandings.some(s=>boxContains(t,s))){landings.update(key);landingCount++}
  if(t.material==='hr_timber'&&narrowDoors.some(o=>{
   const u=vertices.map(p=>o.axis==='x'?p.x-o.x:p.z-o.z),d=vertices.map(p=>o.normal*(o.axis==='x'?p.z-o.z:p.x-o.x)),y=vertices.map(p=>p.y-o.y)
   // End faces of the retained head and threshold have zero width along u.
   return Math.max(...u)-Math.min(...u)<.001&&Math.abs(Math.abs(u[0])-.4)<.008&&Math.max(...d)-Math.min(...d)>.1&&Math.max(...y)-Math.min(...y)<.07&&(Math.max(...y)<.025||Math.min(...y)>2.13)
  })){doorCaps.update(key);doorCapCount++}
  if(t.material==='hr_timber'&&homes.some(h=>[3,6].some(y=>{
   const centre=point(h,4.44,y,1.5)
   return vertices.every(p=>Math.abs(p.x-centre.x)<=.068&&Math.abs(p.z-centre.z)<=.458&&p.y>=y-.008&&p.y<=y+2.208)
  }))){wideFrames.update(key);wideFrameCount++}
 })
 return {total,outside:outside.digest('hex'),outsideCount,walls:walls.digest('hex'),wallCount,partitions:partitions.digest('hex'),partitionCount,landings:landings.digest('hex'),landingCount,doorCaps:doorCaps.digest('hex'),doorCapCount,wideFrames:wideFrames.digest('hex'),wideFrameCount,upperLeafGlassCount}
}

test('actual legacy retirement preserves public architecture, half landings and original narrow door head/threshold caps',async()=>{
 const source=await original(),scene=source.clone(true),before=preservedFingerprint(scene),indices=new Map<THREE.BufferGeometry,string>()
 source.traverse(o=>{if(o instanceof THREE.Mesh&&o.geometry.index)indices.set(o.geometry,createHash('sha256').update(Buffer.from(o.geometry.index.array.buffer)).digest('hex'))})
 const stairs=removeLegacyPrivateStairs(scene),doors=removeLegacyNarrowJoinery(scene),adjacent=removeLegacyAdjacentLeaves(scene),upper=removeLegacyUpperEntryLeaves(scene),after=preservedFingerprint(scene)
 assert.equal(stairs.trianglesRemoved,3616);assert.equal(doors.trianglesRemoved,576)
 assert.deepEqual(stairs.perMaterial,{hr_concrete_board:288,hr_concrete_cast:1440,hr_steel_black:1088,hr_ceiling:16,hr_floor_laminate:16,hr_rubber:768})
 assert.equal(Object.keys(stairs.perHome).length,8);assert(Object.values(stairs.perHome).every(n=>n===452))
 assert.equal(doors.jambTrianglesRemoved,384);assert.equal(doors.leafTrianglesRemoved,192)
 assert.equal(Object.keys(doors.perDoor).length,16);assert(Object.values(doors.perDoor).every(n=>n===36))
 assert.equal(adjacent.trianglesRemoved,192);assert.equal(Object.keys(adjacent.perDoor).length,16);assert(Object.values(adjacent.perDoor).every(n=>n===12))
 assert.equal(upper.trianglesRemoved,192);assert.equal(upper.paintTrianglesRemoved,96);assert.equal(upper.glassTrianglesRemoved,96)
 assert.equal(before.upperLeafGlassCount,96);assert.equal(after.upperLeafGlassCount,0)
 assert.equal(Object.keys(upper.perDoor).length,8);assert(Object.values(upper.perDoor).every(n=>n===24))
 assert.equal(before.total-after.total,4576);assert.equal(before.doorCapCount,128);assert.equal(before.landingCount,96);assert.equal(before.wideFrameCount,768)
 for(const key of ['outside','outsideCount','walls','wallCount','partitions','partitionCount','landings','landingCount','doorCaps','doorCapCount','wideFrames','wideFrameCount']as const)assert.equal(after[key],before[key],key+' preserved exactly')
 assert(before.outsideCount>0&&before.wallCount>0&&before.partitionCount>0)
 for(const [geometry,expected]of indices)assert.equal(createHash('sha256').update(Buffer.from(geometry.index!.array.buffer)).digest('hex'),expected)
 assert.equal(removeLegacyPrivateStairs(scene),stairs);assert.equal(removeLegacyNarrowJoinery(scene),doors);assert.equal(removeLegacyAdjacentLeaves(scene),adjacent);assert.equal(removeLegacyUpperEntryLeaves(scene),upper)
 assert.deepEqual(preservedFingerprint(scene),after)
 assert.equal(removeLegacyCoreStairs(scene).trianglesRemoved,35072,'public retirement remains independent after both private replacements')
})

test('building loading waits for shared materials and never retires old art on replacement failure',async()=>{
 const texture=new THREE.Texture(),source=new THREE.MeshStandardMaterial({name:'hr_concrete_cast'})
 source.map=texture;source.normalMap=texture;source.roughnessMap=texture;source.onBeforeCompile=shader=>{shader.fragmentShader+='\n// exterior wet surface'}
 const scene=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial({name:'hr_stair_concrete'}));scene.add(mesh)
 let ready=false;const requested:string[]=[]
 const materials={get:(name:string)=>{requested.push(name);assert.equal(name,'hr_concrete_cast');return source},ready:async()=>{ready=true},shadow:new Map([['hr_concrete_cast',true]])} as unknown as HeronReachMaterials
 const loader={loadAsync:async(url:string)=>{assert.equal(url,'/models/heron-reach/building-detail.glb');return{scene}}} as unknown as GLTFLoader
 const arch=new THREE.Group(),result=await loadBuildingArt(loader,materials,arch),dry=mesh.material as THREE.MeshStandardMaterial
 assert.equal(result,scene);assert(ready);assert.deepEqual(requested,['hr_concrete_cast'])
 assert.notEqual(dry,source);assert.equal(dry.name,'hr_stair_concrete');assert.equal(dry.roughness,.88);assert.equal(dry.metalness,0)
 assert.equal(dry.map,texture);assert.equal(dry.normalMap,texture);assert.equal(dry.roughnessMap,texture);assert.notEqual(dry.onBeforeCompile,source.onBeforeCompile)
 assert.equal(source.roughness,1);assert(arch.userData.privateStairRetirement);assert(arch.userData.narrowJoineryRetirement);assert(arch.userData.adjacentLeafRetirement);assert(arch.userData.upperEntryLeafRetirement)
 const old=new THREE.Group(),bad={loadAsync:async()=>{throw Error('missing construction')}} as unknown as GLTFLoader
 await assert.rejects(loadBuildingArt(bad,materials,old),/missing construction/)
 await assert.rejects(loadBuildingArt(loader,{...materials,ready:async()=>{throw Error('missing material')}} as HeronReachMaterials,old),/missing material/)
 assert.equal(old.userData.privateStairRetirement,undefined);assert.equal(old.userData.narrowJoineryRetirement,undefined);assert.equal(old.userData.adjacentLeafRetirement,undefined);assert.equal(old.userData.upperEntryLeafRetirement,undefined)
})
