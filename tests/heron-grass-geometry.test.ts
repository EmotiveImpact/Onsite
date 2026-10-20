import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js'
import {correctGrassWinding} from '../src/onsite/heronGrassGeometry.ts'

const counts={GRASS_CLUMP_A:140,GRASS_CLUMP_B:168,GRASS_CLUMP_C:196,GRASS_CLUMP_D:84}

/** Keep the shipped compressed geometry/transforms; omit image decoding in Node only. */
async function loadClumps(){
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
