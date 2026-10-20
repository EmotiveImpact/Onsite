import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import {correctFoliageWinding,correctGrassWinding} from '../src/onsite/heronGrassGeometry.ts'
import {loadHeronReachKits,type HeronReachMaterials} from '../src/onsite/heronReachArt.ts'

const counts={GRASS_CLUMP_A:140,GRASS_CLUMP_B:168,GRASS_CLUMP_C:196,GRASS_CLUMP_D:84}

/** Keep the shipped compressed geometry/transforms; omit image decoding in Node only. */
async function loadFoliageScene(){
 const original=readFileSync('public/models/heron-reach/heron-reach-foliage.glb'),length=original.readUInt32LE(12)
 const json=JSON.parse(original.subarray(20,20+length).toString())
 json.materials=json.materials.map((m:{name:string;doubleSided?:boolean})=>({name:m.name,doubleSided:m.doubleSided}))
 delete json.images;delete json.textures;delete json.samplers
 for(const key of ['extensionsUsed','extensionsRequired'])if(json[key])json[key]=json[key].filter((s:string)=>s!=='EXT_texture_webp')
 const encoded=Buffer.from(JSON.stringify(json)),body=Buffer.alloc(Math.ceil(encoded.length/4)*4,32);encoded.copy(body)
 const tail=original.subarray(20+length),header=Buffer.alloc(20)
 header.writeUInt32LE(0x46546c67,0);header.writeUInt32LE(2,4);header.writeUInt32LE(20+body.length+tail.length,8)
 header.writeUInt32LE(body.length,12);header.writeUInt32LE(0x4e4f534a,16)
 const bytes=Uint8Array.from(Buffer.concat([header,body,tail]))
 const {scene}=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(bytes.buffer,'')
 scene.updateMatrixWorld(true)
 return scene
}
let loadedScene:ReturnType<typeof loadFoliageScene>|undefined
const foliageScene=()=>loadedScene??=loadFoliageScene()
async function loadClumps(){
 const scene=await foliageScene()
 return Object.entries(counts).map(([name,count])=>{
  const root=scene.getObjectByName(name);assert(root,`missing shipped root ${name}`)
  const meshes:THREE.Mesh[]=[];root.traverse(o=>{if(o instanceof THREE.Mesh)meshes.push(o)})
  assert.equal(meshes.length,1,`${name} has its actual grass mesh`)
  const mesh=meshes[0],local=new THREE.Matrix4().copy(root.matrixWorld).invert().multiply(mesh.matrixWorld)
  assert.equal(mesh.geometry.index!.count/3,count,`${name} shipped triangle count`)
  return {name,geometry:mesh.geometry,local}
 })
}
let loaded:ReturnType<typeof loadClumps>|undefined
const clumps=()=>loaded??=loadClumps()
const snapshot=(g:THREE.BufferGeometry)=>Object.fromEntries(Object.entries(g.attributes).map(([name,a])=>[name,a.array.slice()]))

/** Assess each triangle in the same root space used by GrassField, independently of the helper. */
function faceUp(geometry:THREE.BufferGeometry,local:THREE.Matrix4){
 const p=geometry.getAttribute('position'),index=geometry.index!,results:number[]=[]
 for(let i=0;i<index.count;i+=3){
  const ids=[index.getX(i),index.getX(i+1),index.getX(i+2)]
  const points=ids.map(id=>new THREE.Vector3().fromBufferAttribute(p,id).applyMatrix4(local))
  const face=new THREE.Triangle(points[0],points[1],points[2]).getNormal(new THREE.Vector3())
  results.push(face.y)
 }
 return results
}

test('actual 588 grass triangles face upward without mutating the source or authored vertex data',async()=>{
 let checked=0
 for(const {name,geometry,local} of await clumps()){
  const indices=geometry.index!.array.slice(),attributes=snapshot(geometry),originalUp=faceUp(geometry,local)
  const corrected=correctGrassWinding(geometry,local)
  assert.notEqual(corrected,geometry);assert.notEqual(corrected.index,geometry.index)
  assert.equal(corrected.index!.array.constructor,geometry.index!.array.constructor,'retain index representation')
  assert.deepEqual(geometry.index!.array,indices,`${name}: input index unchanged`)
  assert.deepEqual(snapshot(geometry),attributes,`${name}: input attributes unchanged`)
  assert.deepEqual(snapshot(corrected),attributes,`${name}: positions/normals/UVs/colours preserved byte-for-byte`)
  assert.deepEqual(corrected.groups,geometry.groups);assert.deepEqual(corrected.drawRange,geometry.drawRange)
  const result=faceUp(corrected,local)
  assert(result.every(y=>y>=0),`${name}: corrected upper blade surface is front-facing`)
  for(let i=0;i<indices.length;i+=3){
   const before=[indices[i],indices[i+1],indices[i+2]],after=[corrected.index!.getX(i),corrected.index!.getX(i+1),corrected.index!.getX(i+2)]
   assert.deepEqual([...after].sort((a,b)=>a-b),[...before].sort((a,b)=>a-b),`${name}: triangle vertices retained`)
   if(originalUp[i/3]>=0)assert.deepEqual(after,before,`${name}: upward triangle stays unchanged`)
   else assert.notDeepEqual(after,before,`${name}: downward winding corrected`)
   checked++
  }
 }
 assert.equal(checked,588)
})

test('a second pass leaves already-corrected grass indices and authored normals unchanged',async()=>{
 for(const {name,geometry,local} of await clumps()){
  const once=correctGrassWinding(geometry,local),indices=once.index!.array.slice(),attributes=snapshot(once)
  const twice=correctGrassWinding(once,local)
  assert.notEqual(twice,once)
  assert.deepEqual(twice.index!.array,indices,`${name}: no flip back on future corrected assets`)
  assert.deepEqual(once.index!.array,indices,`${name}: corrected input remains untouched`)
  assert.deepEqual(snapshot(twice),attributes,`${name}: authored lighting data remains unchanged`)
  assert(faceUp(twice,local).every(y=>y>=0))
 }
})

test('the mesh-to-root transform determines up while UVs, normals and colours remain intact',()=>{
 const source=new THREE.BufferGeometry()
 source.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,0,1,0,1,0,0],3))
 source.setAttribute('normal',new THREE.Float32BufferAttribute([0,0,1,0,0,1,0,0,1],3))
 source.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,0,1,1,0],2))
 source.setAttribute('color',new THREE.Float32BufferAttribute([.1,.2,.3,.4,.5,.6,.7,.8,.9],3))
 source.setIndex([0,1,2])
 const local=new THREE.Matrix4().makeRotationX(-Math.PI/2),attributes=snapshot(source)
 assert(faceUp(source,local)[0]<-.99,'source Z-down triangle becomes Y-down in asset-root space')
 const corrected=correctGrassWinding(source,local)
 assert(faceUp(corrected,local)[0]>.99)
 assert.deepEqual(snapshot(corrected),attributes)
 assert.deepEqual(source.index!.array,new Uint16Array([0,1,2]))
 assert.deepEqual(correctGrassWinding(corrected,local).index!.array,corrected.index!.array)
})

// The shipped A has 11 six-triangle rosette strips. B has six five-triangle
// blades and three two-triangle cards. C has five strips after its three cards.
const weedCounts=[
 {asset:'WEED_TUFT_A',material:'hr_weed',triangles:66,cards:0,corrected:66},
 {asset:'WEED_TUFT_B',material:'hr_weed',triangles:6,cards:6,corrected:0},
 {asset:'WEED_TUFT_B',material:'hr_grass_blade',triangles:30,cards:0,corrected:30},
 {asset:'WEED_TUFT_C',material:'hr_weed',triangles:36,cards:6,corrected:30},
] as const
async function weedParts(){
 const scene=await foliageScene()
 return weedCounts.map(expected=>{
  const root=scene.getObjectByName(expected.asset);assert(root)
  const meshes:THREE.Mesh[]=[]
  root.traverse(o=>{if(o instanceof THREE.Mesh&&!Array.isArray(o.material)&&o.material.name===expected.material)meshes.push(o)})
  assert.equal(meshes.length,1,`${expected.asset}/${expected.material}: actual primitive`)
  const mesh=meshes[0],geometry:THREE.BufferGeometry=mesh.geometry,local=new THREE.Matrix4().copy(root.matrixWorld).invert().multiply(mesh.matrixWorld)
  assert.equal(geometry.index!.count/3,expected.triangles)
  return {...expected,mesh,geometry,local}
 })
}
type WeedPart=Awaited<ReturnType<typeof weedParts>>[number]
const triangleIndices=(g:THREE.BufferGeometry,i:number)=>[g.index!.getX(i*3),g.index!.getX(i*3+1),g.index!.getX(i*3+2)]
function authoredNormalUp(g:THREE.BufferGeometry,local:THREE.Matrix4){
 const n=g.getAttribute('normal'),matrix=new THREE.Matrix3().getNormalMatrix(local)
 return Array.from({length:n.count},(_,i)=>new THREE.Vector3().fromBufferAttribute(n,i).applyNormalMatrix(matrix).y)
}
function assertWeedFaces(part:WeedPart,corrected:THREE.BufferGeometry){
 const originalUp=faceUp(part.geometry,part.local),result=faceUp(corrected,part.local),label=`${part.asset}/${part.material}`
 let flips=0
 for(let i=0;i<part.triangles;i++){
  const before=triangleIndices(part.geometry,i),after=triangleIndices(corrected,i)
  if(i<part.cards){assert.deepEqual(after,before,`${label}: upright card ${i} unchanged`);continue}
  assert(originalUp[i]<0,`${label}: actual strip/blade is down-wound`)
  assert(result[i]>=0,`${label}: upper leaf surface becomes front-facing`)
  assert.deepEqual([...after].sort((a,b)=>a-b),[...before].sort((a,b)=>a-b),`${label}: original triangle vertices`)
  assert.notDeepEqual(after,before);flips++
 }
 assert.equal(flips,part.corrected)
 if(part.cards)assert.equal(originalUp.slice(0,part.cards).filter(y=>y<0).length,2,'negative geometric Y alone must not select upright cards')
 return flips
}

test('actual weed geometry corrects 126 strip/blade triangles and retains all 12 upright card triangles',async()=>{
 let correctedCount=0,cardCount=0
 for(const part of await weedParts()){
  const {geometry,local,asset,material}=part,indices=geometry.index!.array.slice(),attributes=snapshot(geometry),normalUp=authoredNormalUp(geometry,local)
  if(asset!=='WEED_TUFT_B')for(let i=0;i<part.triangles;i++){
   const y=triangleIndices(geometry,i).map(id=>normalUp[id])
   assert(i<part.cards?y.every(v=>v<.98):y.every(v=>v>.98),`${asset}: authored strip/card normals remain separated`)
  }
  const corrected=correctFoliageWinding(geometry,local,asset,material)
  if(part.corrected){assert.notEqual(corrected,geometry);assert.notEqual(corrected.index,geometry.index)}
  else assert.equal(corrected,geometry,'B upright-card primitive retains its original geometry object')
  assert.equal(corrected.index!.array.constructor,geometry.index!.array.constructor)
  correctedCount+=assertWeedFaces(part,corrected);cardCount+=part.cards
  assert.deepEqual(geometry.index!.array,indices,'source indices unchanged')
  assert.deepEqual(snapshot(geometry),attributes,'source vertex attributes unchanged')
  assert.deepEqual(snapshot(corrected),attributes,'positions/normals/UVs/colours remain byte-identical')
  assert.deepEqual(corrected.groups,geometry.groups);assert.deepEqual(corrected.drawRange,geometry.drawRange)
  const twice=correctFoliageWinding(corrected,local,asset,material)
  assert.deepEqual(twice.index!.array,corrected.index!.array,'a future corrected source does not flip back')
  assert.deepEqual(snapshot(twice),attributes,'second pass keeps authored attributes')
 }
 assert.equal(correctedCount,126);assert.equal(cardCount,12)
})

test('foliage correction requires the exact supported asset/material pair',async()=>{
 const part=(await weedParts())[0],{geometry,local}=part
 for(const [asset,material]of [
  ['WEED_TUFT_A','hr_grass_blade'],['WEED_TUFT_B','hr_weed'],['WEED_TUFT_C','hr_bark_plane'],
  ['WEED_TUFT_A_extra','hr_weed'],['WEED_TUFT_D','hr_weed'],['SHRUB_A','hr_weed'],
  ['TREE_PLANE_A','hr_grass_blade'],['GRASS_CLUMP_E','hr_grass_blade'],['GRASS_PATCH_1M','hr_grass_blade'],
  ['GRASS_CLUMP_A','hr_weed'],['WEED_TUFT_A','hr_weed_extra'],
 ])assert.equal(correctFoliageWinding(geometry,local,asset,material),geometry,`${asset}/${material}: unrelated geometry unchanged`)
 assert.deepEqual(correctFoliageWinding(geometry,local,'WEED_TUFT_A','hr_weed.001').index!.array,
  correctFoliageWinding(geometry,local,'WEED_TUFT_A','hr_weed').index!.array,'Blender numeric material suffix is supported')
 let grassTriangles=0
 for(const {name,geometry,local}of await clumps()){
  const corrected=correctFoliageWinding(geometry,local,name,'hr_grass_blade')
  assert(faceUp(corrected,local).every(y=>y>=0));grassTriangles+=corrected.index!.count/3
  assert.deepEqual(snapshot(corrected),snapshot(geometry))
 }
 assert.equal(grassTriangles,588)
})

test('strip selection transforms normals to root space and requires every corner to be upward',()=>{
 const source=new THREE.BufferGeometry()
 source.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,0,1,0,1,0,0,2,0,0,2,1,0,3,0,0],3))
 source.setAttribute('normal',new THREE.Float32BufferAttribute([0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,Math.sqrt(1-.97**2),0,.97],3))
 source.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,0,1,1,0,0,0,0,1,1,0],2));source.setIndex([0,1,2,3,4,5])
 const local=new THREE.Matrix4().makeRotationX(-Math.PI/2),attributes=snapshot(source),normalUp=authoredNormalUp(source,local)
 assert(faceUp(source,local).every(y=>y<0));assert((normalUp[3]+normalUp[4]+normalUp[5])/3>.98,'averaging would wrongly select the mixed-normal face')
 const corrected=correctFoliageWinding(source,local,'WEED_TUFT_C','hr_weed')
 assert(faceUp(corrected,local)[0]>0,'root-up normals select the strip despite stored normal Y=0')
 assert.deepEqual(triangleIndices(corrected,1),[3,4,5],'one lower normal excludes the whole face')
 assert.deepEqual(source.index!.array,new Uint16Array([0,1,2,3,4,5]));assert.deepEqual(snapshot(corrected),attributes)
})

test('the kit loader emits corrected actual weed instances while retaining source material owners and card indices',async()=>{
 const scene=await foliageScene(),parts=await weedParts(),sources=parts.map(p=>({indices:p.geometry.index!.array.slice(),attributes:snapshot(p.geometry)}))
 const loader={loadAsync:async(url:string)=>({scene:url.endsWith('heron-reach-foliage.glb')?scene:new THREE.Group()})} as unknown as GLTFLoader
 const materials={ready:async()=>[],get:()=>{throw Error('weed kit should keep its existing material owner')}} as unknown as HeronReachMaterials
 const placements=['WEED_TUFT_A','WEED_TUFT_B','WEED_TUFT_C'].map((asset,i)=>({asset,x:30+i,y:.85,z:40,ry:.27,scale:1.3}))
 const group=await loadHeronReachKits(loader,materials,placements,new Set())
 assert.equal(group.children.length,4)
 let corrected=0
 for(const [i,part]of parts.entries()){
  const mesh=group.getObjectByName(`${part.asset}/${part.material}`);assert(mesh instanceof THREE.InstancedMesh)
  assert.equal(mesh.count,1);assert.equal(mesh.material,part.mesh.material,'reuse actual loaded material object')
  corrected+=assertWeedFaces(part,mesh.geometry)
  assert.deepEqual(snapshot(mesh.geometry),sources[i].attributes)
  assert.deepEqual(part.geometry.index!.array,sources[i].indices);assert.deepEqual(snapshot(part.geometry),sources[i].attributes)
 }
 assert.equal(corrected,126)
})
