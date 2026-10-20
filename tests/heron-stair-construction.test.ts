import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import spec from '../docs/maps/heron-reach-32/blueprints/build-spec.json'
import {solids,OX,OZ} from '../src/onsite/heronReach.ts'
import {removeLegacyCoreStairs,loadStairArt} from '../src/onsite/heronStairArt.ts'
import type {HeronReachMaterials} from '../src/onsite/heronReachArt.ts'

const asset='public/models/heron-reach/stair-detail.glb'
const manifestPath='assets/blender/heron-reach/stair-detail-manifest.json'
type Core=typeof spec.cores[number]
type Point={x:number;y:number;z:number}
type Triangle={shape:THREE.Triangle;bounds:THREE.Box3;material:string;node:string}
const tolerance=.006
const hash=(path:string)=>createHash('sha256').update(readFileSync(path)).digest('hex')
const owns=(c:Core,x:number,z:number,inset=0)=>x>=c.rect[0]+inset&&x<=c.rect[0]+6-inset&&z>=c.rect[1]+inset&&z<=c.rect[1]+6-inset
const mapPoint=(c:Core,x:number,y:number,z:number):Point=>({x:c.rect[0]+x,y,z:c.rect[1]+(c.mirrorZ?6-z:z)})

/** Decode actual shipped meshopt buffers/transforms. Only image decoding is omitted in Node. */
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

/** Small x/z bins keep geometric tests local; they do not use the runtime navigation graph. */
function indexTriangles(scene:THREE.Object3D){
 const triangles:Triangle[]=[],cells=new Map<string,Triangle[]>(),materials=new Set<string>();let meshes=0
 scene.traverse(o=>{
  if(!(o instanceof THREE.Mesh))return
  meshes++
  const geometry=o.geometry,p=geometry.attributes.position,index=geometry.index
  const mats=Array.isArray(o.material)?o.material:[o.material]
  for(const mat of mats)materials.add(mat.name)
  for(let i=0;i<(index?.count??p.count);i+=3){
   const points=[0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld).add(new THREE.Vector3(OX,0,OZ)))
   const shape=new THREE.Triangle(points[0],points[1],points[2]),bounds=new THREE.Box3().setFromPoints(points)
   const group=geometry.groups.find(g=>i>=g.start&&i<g.start+g.count),material=mats[group?.materialIndex??0]?.name??''
   const triangle={shape,bounds,material,node:o.userData.name??o.name};triangles.push(triangle)
   for(let x=Math.floor(bounds.min.x);x<=Math.floor(bounds.max.x);x++)for(let z=Math.floor(bounds.min.z);z<=Math.floor(bounds.max.z);z++){
    const key=x+':'+z,list=cells.get(key);if(list)list.push(triangle);else cells.set(key,[triangle])
   }
  }
 })
 const near=(p:Point,radius=0)=>{
  const result=new Set<Triangle>()
  for(let x=Math.floor(p.x-radius);x<=Math.floor(p.x+radius);x++)for(let z=Math.floor(p.z-radius);z<=Math.floor(p.z+radius);z++)
   for(const triangle of cells.get(x+':'+z)??[])result.add(triangle)
  return [...result]
 }
 return {triangles,materials,meshes,near}
}
let decoded:Promise<ReturnType<typeof indexTriangles>>|undefined
const shipped=()=>decoded??=loadGeometry(asset).then(indexTriangles)

const publicTreads=solids.filter(s=>s.id==='stair'&&spec.cores.some(c=>owns(c,s.x+OX,s.z+OZ)))
const publicLandings=solids.filter(s=>s.id==='landing'&&spec.cores.some(c=>owns(c,s.x+OX,s.z+OZ)))
const pointAt=(s:typeof solids[number]):Point=>({x:s.x+OX,y:s.y+s.h/2,z:s.z+OZ})

function surfaceHeights(p:Point,triangles:Triangle[]){
 const ray=new THREE.Ray(new THREE.Vector3(p.x,p.y+.05,p.z),new THREE.Vector3(0,-1,0)),hit=new THREE.Vector3(),heights:number[]=[]
 for(const {shape} of triangles)if(ray.intersectTriangle(shape.a,shape.b,shape.c,false,hit)&&hit.y>=p.y-.05)heights.push(hit.y)
 return heights
}

test('all public stair treads retain their physical height and width in the compressed Blender asset',async()=>{
 const geometry=await shipped();assert.equal(publicTreads.length,432)
 for(const tread of publicTreads){
  const centre=pointAt(tread)
  for(const dx of [-.73,-.45,0,.45,.73]){
   const p={...centre,x:centre.x+dx},heights=surfaceHeights(p,geometry.near(p))
   assert(heights.some(y=>Math.abs(y-p.y)<=tolerance),`missing physical tread surface at ${JSON.stringify(p)}`)
   assert(heights.every(y=>y<=p.y+tolerance),`art rises above the unchanged tread at ${JSON.stringify(p)}`)
  }
 }
 for(const core of spec.cores){
  const count=publicTreads.filter(s=>owns(core,s.x+OX,s.z+OZ)).length
  assert.equal(count,(core.levels.length-1)*18,`${core.id} includes both flights on every served storey`)
 }
})

test('new stair construction stays inside all eight existing core volumes, including mirrored B1 routes',async()=>{
 const geometry=await shipped(),seen=new Set<string>(),manifest=JSON.parse(readFileSync(manifestPath,'utf8'))
 for(const t of geometry.triangles){
  const core=spec.cores.find(c=>owns(c,t.bounds.min.x,t.bounds.min.z,-tolerance)&&owns(c,t.bounds.max.x,t.bounds.max.z,-tolerance))
  assert(core,`stair geometry escapes public cores: ${t.node} ${t.bounds.min.toArray()}/${t.bounds.max.toArray()}`)
  assert(t.bounds.min.y>=core.levels[0]-.4-tolerance,`${core.id} below its foundation envelope`)
  assert(t.bounds.max.y<=core.levels.at(-1)!+2.8+tolerance,`${core.id} intersects the cap above the final storey`)
  assert([t.shape.a,t.shape.b,t.shape.c].every(v=>v.toArray().every(Number.isFinite)))
  seen.add(core.id)
 }
 assert.deepEqual([...seen].sort(),spec.cores.map(c=>c.id).sort())
 assert(geometry.triangles.some(t=>t.bounds.max.y<0),'actual undercroft construction')
 assert.equal(hash(asset),manifest.compressedGLBSHA256)
 assert.equal(readFileSync(asset).byteLength,manifest.compressedGLBBytes)
 assert.equal(hash(manifest.builder),manifest.builderSHA256)
 assert.equal(geometry.triangles.length,manifest.triangles)
 const source=readFileSync(asset),json=JSON.parse(source.subarray(20,20+source.readUInt32LE(12)).toString())
 assert.equal(json.images?.length??0,0,'new construction uses the existing material library, not unrecorded embedded images')
 const library=JSON.parse(readFileSync('public/materials/heron/runtime-materials.json','utf8'))
 for(const material of geometry.materials)assert(material==='hr_stair_concrete'||library[material],`unrecorded material ${material}`)
 assert(geometry.meshes<=28,'four culled estate quadrants, up to seven material batches each')
})

test('authored soffits and fittings preserve headroom and keep standing routes free of added render geometry',async()=>{
 const geometry=await shipped(),headroomSamples:Point[]=publicTreads.map(pointAt)
 // Sample the whole turn, not just the centre of its bounding box; one landing spans both flights.
 for(const landing of publicLandings){
  const centre=pointAt(landing)
  for(const dx of [-Math.max(0,landing.w/2-.5),0,Math.max(0,landing.w/2-.5)])headroomSamples.push({...centre,x:centre.x+dx})
 }
 // Door-to-flight lanes at every served level. North/south use the same mirrored design frame.
 for(const core of spec.cores)for(const y of core.levels)for(const x of [1.15,3,4.85])headroomSamples.push(mapPoint(core,x,y,5))
 const ray=new THREE.Ray(),hit=new THREE.Vector3(),up=new THREE.Vector3(0,1,0)
 for(const p of headroomSamples){
  ray.set(new THREE.Vector3(p.x,p.y+.03,p.z),up)
  for(const t of geometry.near(p))if(ray.intersectTriangle(t.shape.a,t.shape.b,t.shape.c,false,hit))
   assert(hit.y-p.y>=2.4-tolerance,`new art reduces headroom to ${(hit.y-p.y).toFixed(3)}m at ${JSON.stringify(p)} (${t.node})`)
  // Ignore the lowest 0.4m where adjacent risers legitimately meet a capsule's feet.
  // The upper standing body must not pass through a rail, column or decorative skin.
  const body=new THREE.Box3(new THREE.Vector3(p.x-.30,p.y+.4,p.z-.30),new THREE.Vector3(p.x+.30,p.y+1.8,p.z+.30))
  for(const t of geometry.near(p,.30))assert(!body.intersectsBox(t.bounds)||!body.intersectsTriangle(t.shape),`render-only obstruction in standing lane at ${JSON.stringify(p)} (${t.node})`)
 }
})

test('both flight handrails follow the real rise direction and solid separator walls remain visually closed',async()=>{
 const geometry=await shipped(),manifest=JSON.parse(readFileSync(manifestPath,'utf8'))
 const vertex=(v:number[]|Point)=>Array.isArray(v)?new THREE.Vector3(...v as [number,number,number]):new THREE.Vector3(v.x,v.y,v.z)
 let flights=0
 for(const authored of manifest.cores){
  const core=spec.cores.find(c=>c.id===authored.id);assert(core)
  assert.equal(authored.flights.length,(core.levels.length-1)*2)
  for(const flight of authored.flights){
   const expected=(flight.first?-1:1)*(core.mirrorZ?-1:1)*spec.stairs['ST-P'].rise/spec.stairs['ST-P'].going
   for(const [from,to]of [[flight.rail.start,flight.rail.end],[flight.rail.outerStart,flight.rail.outerEnd]]){
    const start=vertex(from),end=vertex(to),delta=end.clone().sub(start)
    assert(Math.abs(delta.y/delta.z-expected)<1e-5,`${core.id} ${flight.id} rail pitch opposes its physical flight`)
    // A long tube can have endpoint vertices only: sample its actual triangle surfaces
    // between the rings as well, including the outer handrail beside the wall.
    for(const fraction of [0,.25,.5,.75,1]){
     const point=start.clone().lerp(end,fraction),nearest=new THREE.Vector3()
     const candidates=geometry.near(point,.04).filter(t=>t.material==='hr_steel_black')
     assert(candidates.some(t=>t.shape.closestPointToPoint(point,nearest).distanceTo(point)<.025),`${core.id} missing exported rail surface at ${point.toArray()}`)
    }
   }
   flights++
  }
 }
 assert.equal(flights,48)
 const spines=solids.filter(s=>s.id.endsWith('-balustrade')&&spec.cores.some(c=>owns(c,s.x+OX,s.z+OZ)))
 assert.equal(spines.length,16)
 const ray=new THREE.Ray(),hit=new THREE.Vector3(),right=new THREE.Vector3(1,0,0)
 for(const spine of spines){
  const minY=spine.y-spine.h/2,maxY=spine.y+spine.h/2,x=spine.x+OX,z=spine.z+OZ
  for(let y=minY+.6;y<maxY-.15;y+=1.5)for(const dz of [-spine.d*.3,0,spine.d*.3]){
   const p={x,y,z:z+dz};ray.set(new THREE.Vector3(x-spine.w/2-.04,y,p.z),right)
   assert(geometry.near(p,.1).some(t=>ray.intersectTriangle(t.shape.a,t.shape.b,t.shape.c,false,hit)&&Math.abs(hit.x-x)<=spine.w/2+tolerance),`solid collision has an invisible gap at ${JSON.stringify(p)}`)
  }
 }
})

/** Fingerprint every triangle outside the public cores, plus protected inner walls/landings.
 * This compares actual before/after exports, not the retirement function's selection rules. */
function protectedGeometry(scene:THREE.Object3D){
 const outside=createHash('sha256'),walls=createHash('sha256'),landings=createHash('sha256')
 let total=0,outsideCount=0,wallCount=0,landingCount=0
 const point=new THREE.Vector3(),wallMaterials=new Set(['hr_brick_red','hr_brick_painted','hr_glass','hr_glass_blocks','hr_wired_glass'])
 scene.traverse(o=>{
  if(!(o instanceof THREE.Mesh))return
  const g=o.geometry,p=g.attributes.position,index=g.index,materials=Array.isArray(o.material)?o.material:[o.material]
  for(let i=0;i<(index?.count??p.count);i+=3){
   const group=g.groups.find(g=>i>=g.start&&i<g.start+g.count),material=materials[group?.materialIndex??0]?.name??''
   const coords=[0,1,2].flatMap(j=>point.fromBufferAttribute(p,index?index.getX(i+j):i+j).applyMatrix4(o.matrixWorld).add(new THREE.Vector3(OX,0,OZ)).toArray())
   const x0=Math.min(coords[0],coords[3],coords[6]),x1=Math.max(coords[0],coords[3],coords[6])
   const y0=Math.min(coords[1],coords[4],coords[7]),y1=Math.max(coords[1],coords[4],coords[7])
   const z0=Math.min(coords[2],coords[5],coords[8]),z1=Math.max(coords[2],coords[5],coords[8])
   const key=material+':'+coords.join(',')+';'
   const inside=spec.cores.some(c=>owns(c,x0,z0,-.02)&&owns(c,x1,z1,-.02))
   if(!inside){outside.update(key);outsideCount++}
   if(inside&&wallMaterials.has(material)){walls.update(key);wallCount++}
   if(inside&&['hr_concrete_cast','hr_concrete_board'].includes(material)&&publicLandings.some(s=>y0>=s.y-s.h/2-.02&&y1<=s.y+s.h/2+.02&&x0>=s.x+OX-s.w/2-.02&&x1<=s.x+OX+s.w/2+.02&&z0>=s.z+OZ-s.d/2-.02&&z1<=s.z+OZ+s.d/2+.02)){
    landings.update(key);landingCount++
   }
   total++
  }
 })
 return {total,outside:outside.digest('hex'),outsideCount,walls:walls.digest('hex'),wallCount,landings:landings.digest('hex'),landingCount}
}

test('legacy retirement removes the actual defective public stairs while preserving landings, glazing and private home geometry',async()=>{
 const scene=await loadGeometry('public/models/heron-reach/heron-reach-arch.glb'),before=protectedGeometry(scene)
 const sourceIndices=new Map<THREE.BufferGeometry,string>()
 scene.traverse(o=>{if(o instanceof THREE.Mesh&&o.geometry.index)sourceIndices.set(o.geometry,createHash('sha256').update(Buffer.from(o.geometry.index.array.buffer)).digest('hex'))})
 const report=removeLegacyCoreStairs(scene),after=protectedGeometry(scene)
 assert.equal(report.trianglesRemoved,35072,'known source asset retirement, excluding unrelated architecture')
 assert(report.treadTrianglesRemoved>4000&&report.railTrianglesRemoved>20000)
 assert.deepEqual(Object.keys(report.perCore).sort(),spec.cores.map(c=>c.id).sort())
 assert.equal(before.total-after.total,report.trianglesRemoved)
 for(const field of ['outside','outsideCount','walls','wallCount','landings','landingCount']as const)assert.equal(after[field],before[field],field+' remains exact')
 assert(before.wallCount>0&&before.outsideCount>0)
 assert.equal(before.landingCount,912,'all 864 landing triangles and 48 coincident lintel triangles remain protected, including soffits and edges')
 for(const [geometry,oldHash]of sourceIndices)assert.equal(createHash('sha256').update(Buffer.from(geometry.index!.array.buffer)).digest('hex'),oldHash,'source index remains reusable')
 assert.equal(removeLegacyCoreStairs(scene),report,'repeat load is idempotent')
 assert.deepEqual(protectedGeometry(scene),after)
})

test('stair loading shares existing textures, uses dry sheltered concrete and preserves old art when replacement loading fails',async()=>{
 const originalTexture=new THREE.Texture(),source=new THREE.MeshStandardMaterial({name:'hr_concrete_cast'})
 source.map=originalTexture;source.normalMap=originalTexture;source.roughnessMap=originalTexture
 source.onBeforeCompile=shader=>{shader.fragmentShader+='\n// outdoor wet treatment'}
 const imported=new THREE.MeshStandardMaterial({name:'hr_stair_concrete'}),replacement=new THREE.Group(),mesh=new THREE.Mesh(new THREE.BoxGeometry(),imported)
 const lensMaterial=new THREE.MeshStandardMaterial({name:'hr_core_strip'}),lens=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial({name:'hr_core_strip'}))
 replacement.add(mesh,lens)
 let ready=false;const requested:string[]=[]
 const library={get:(name:string)=>{requested.push(name);assert(['hr_concrete_cast','hr_core_strip'].includes(name));return name==='hr_concrete_cast'?source:lensMaterial},ready:async()=>{ready=true},shadow:new Map([['hr_concrete_cast',true],['hr_core_strip',false]])} as unknown as HeronReachMaterials
 const arch=new THREE.Group(),loader={loadAsync:async(url:string)=>{assert.equal(url,'/models/heron-reach/stair-detail.glb');return {scene:replacement}}} as unknown as GLTFLoader
 const result=await loadStairArt(loader,library,arch),dry=mesh.material as THREE.MeshStandardMaterial
 assert.equal(result,replacement);assert(ready);assert.deepEqual(requested,['hr_concrete_cast','hr_core_strip'])
 assert.equal(mesh.castShadow,true);assert.equal(lens.castShadow,false,'emitting lenses must not block their own fixture light')
 assert.notEqual(dry,source);assert.equal(dry.name,'hr_stair_concrete')
 assert.equal(dry.map,originalTexture);assert.equal(dry.normalMap,originalTexture);assert.equal(dry.roughnessMap,originalTexture)
 assert.equal(dry.roughness,.88);assert.equal(dry.metalness,0);assert.notEqual(dry.onBeforeCompile,source.onBeforeCompile)
 assert.equal(source.roughness,1,'shared outdoor source is not retuned')
 const failedArch=new THREE.Group(),failedLoader={loadAsync:async()=>{throw new Error('missing replacement')}} as unknown as GLTFLoader
 await assert.rejects(loadStairArt(failedLoader,library,failedArch),/missing replacement/)
 assert.equal(failedArch.userData.stairRetirement,undefined,'existing geometry is retained on asset failure')
 const badLibrary={...library,ready:async()=>{throw new Error('missing surface')}} as unknown as HeronReachMaterials
 await assert.rejects(loadStairArt(loader,badLibrary,failedArch),/missing surface/)
 assert.equal(failedArch.userData.stairRetirement,undefined,'existing geometry is retained on material failure')
})

