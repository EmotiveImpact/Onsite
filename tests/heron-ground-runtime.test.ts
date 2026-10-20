import test,{type TestContext} from 'node:test'
import assert from 'node:assert/strict'
import {createHash} from 'node:crypto'
import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {GrassField,loadHeronReachKits,type HeronReachMaterials,type KitPlacement} from '../src/onsite/heronReachArt.ts'
import {loadHeronGroundPlan} from '../src/onsite/heronGroundRuntime.ts'
import {loadHeronGroundArt} from '../src/onsite/heronGroundArt.ts'

const cells={cell:2,cells:[[60,30],[62,30],[80,30],[82,30],[100,30],[102,30]]}
// Recorded from the actual pre-mask GrassField using this fixture, not a copied RNG algorithm.
const originalMatrixHash='05bcf2daf6d2e396601fa1dbaff112df40a6fa644b3bee9ee39182dae438d696'
type Instance={part:string;matrix:number[]}
type GrassOptions=NonNullable<Parameters<GrassField['build']>[2]>

function grassScene(){
 const scene=new THREE.Group()
 for(const suffix of ['A','B','C','D']){
  const root=new THREE.Group();root.name='GRASS_CLUMP_'+suffix;root.position.set(2,0,-3);root.rotation.y=.13
  for(let i=0;i<2;i++){
   const geometry=new THREE.BufferGeometry();geometry.name=suffix+'_'+i
   geometry.setAttribute('position',new THREE.Float32BufferAttribute([0,0,0,.1,0,0,0,0,.1],3))
   geometry.setAttribute('normal',new THREE.Float32BufferAttribute([0,1,0,0,1,0,0,1,0],3))
   geometry.setAttribute('uv',new THREE.Float32BufferAttribute([0,0,1,0,0,1],2));geometry.setIndex([0,1,2])
   const mesh=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({name:'hr_grass_blade'}))
   mesh.position.set(.02+i*.09,.03-i*.01,-.01+i*.08);mesh.rotation.z=i*.04;mesh.scale.set(1-i*.2,1+i*.1,1)
   root.add(mesh)
  }
  scene.add(root)
 }
 return scene
}

function grassFixture(t:TestContext){
 t.mock.method(globalThis,'fetch',async(url:string)=>{
  assert.equal(url,'/models/heron-reach/grass-cells.json')
  return new Response(JSON.stringify(cells),{headers:{'Content-Type':'application/json'}})
 })
 const loader={loadAsync:async(url:string)=>{
  assert.equal(url,'/models/heron-reach/heron-reach-foliage.glb');return{scene:grassScene()}
 }} as unknown as GLTFLoader
 return async(options?:GrassOptions)=>{
  const field=new GrassField(),group=await field.build(loader,2,options)
  return{field,group,records:instances(group)}
 }
}

function instances(group:THREE.Object3D):Instance[]{
 const records:Instance[]=[]
 group.traverse(o=>{
  if(!(o instanceof THREE.InstancedMesh))return
  for(let i=0;i<o.count;i++){
   const matrix=new THREE.Matrix4();o.getMatrixAt(i,matrix)
   records.push({part:o.geometry.name,matrix:matrix.elements})
  }
 })
 return records
}
const hash=(records:Instance[])=>createHash('sha256').update(JSON.stringify(records)).digest('hex')

test('unmasked and full-density grass retain the original exact RNG transforms across parts and tiles',async t=>{
 const build=grassFixture(t),baseline=await build(),full=await build({densityMask:()=>1})
 assert.equal(baseline.records.length,96)
 assert.equal(baseline.group.children.length,24)
 assert.equal(hash(baseline.records),originalMatrixHash,'unmasked transforms match the pre-change runtime')
 assert.deepEqual(full.records,baseline.records,'mask acceptance must not consume the original RNG sequence')
})

test('a partial mask only removes instances; retained matrices and unaffected later tiles are exact',async t=>{
 const build=grassFixture(t),baseline=await build(),masked=await build({densityMask:(x:number)=>x<70?.35:1})
 assert(masked.records.length>0&&masked.records.length<baseline.records.length,'fixture actually removes some grass')
 const originals=new Set(baseline.records.map(record=>JSON.stringify(record)))
 for(const record of masked.records)assert(originals.has(JSON.stringify(record)),'a retained instance moved, rotated, changed species or changed scale')
 // The mask affects only the first tile. Mesh-local offsets are below .2m, far from this cut.
 const later=(records:Instance[])=>records.filter(record=>record.matrix[12]+72>75)
 assert.deepEqual(later(masked.records),later(baseline.records),'filtering an early tile cannot perturb later tiles')
 const repeat=await build({densityMask:Promise.resolve((x:number)=>x<70?.35:1)})
 assert.deepEqual(repeat.records,masked.records,'asynchronous mask readiness preserves deterministic placement')
})

test('missing and rejected mask data preserve every baseline grass instance',async t=>{
 const build=grassFixture(t),baseline=await build()
 t.mock.method(console,'warn',()=>{})
 const missing=await build({densityMask:Promise.resolve(undefined)})
 const failed=await build({densityMask:Promise.reject(new Error('optional ground plan unavailable'))})
 assert.deepEqual(missing.records,baseline.records)
 assert.deepEqual(failed.records,baseline.records)
})

test('a fully rejected field creates no empty instance batches or invalid culling spheres',async t=>{
 const build=grassFixture(t),result=await build({densityMask:()=>0})
 assert.equal(result.records.length,0)
 result.group.traverse(o=>{
  if(!(o instanceof THREE.InstancedMesh))return
  assert(o.count>0,'do not retain zero-count batches')
  const sphere=o.boundingSphere;assert(sphere)
  assert([...sphere.center.toArray(),sphere.radius].every(Number.isFinite))
  assert(sphere.radius>=0)
 })
 assert.doesNotThrow(()=>result.field.update(new THREE.PerspectiveCamera()))
})

function kitFixture(options:{missingLeaf?:boolean;missingGroundKit?:boolean}={}){
 const bark=new THREE.MeshStandardMaterial({name:'hr_bark_plane',map:new THREE.Texture(),vertexColors:true})
 const leaf=new THREE.MeshStandardMaterial({name:'hr_leaf_plane',map:new THREE.Texture(),alphaTest:.5,side:THREE.DoubleSide})
 const placeholders=[new THREE.MeshStandardMaterial({name:bark.name}),new THREE.MeshStandardMaterial({name:leaf.name})]
 const scenes=new Map<string,THREE.Group>(),requests:string[]=[]
 const add=(scene:THREE.Group,name:string,materials:THREE.Material[])=>{
  const root=new THREE.Group();root.name=name
  materials.forEach((material,i)=>{
   const geometry=new THREE.BoxGeometry(.2,1,.2);geometry.name=name+'_'+i
   const mesh=new THREE.Mesh(geometry,material);mesh.position.set(.1,.2,.3);root.add(mesh)
  })
  scene.add(root)
 }
 const winter=new THREE.Group();add(winter,'TREE_PLANE_A',options.missingLeaf?[bark]:[bark,leaf]);scenes.set('winter',winter)
 const ground=new THREE.Group();add(ground,'TREE_PLANE_A_LOD1',placeholders);scenes.set('ground-trees',ground)
 const props=new THREE.Group();add(props,'BENCH',[new THREE.MeshStandardMaterial({name:'hr_steel_black'})]);scenes.set('props',props)
 const loader={loadAsync:async(url:string)=>{
  requests.push(url)
  const key=url.replace('/models/heron-reach/heron-reach-','').replace('.glb','')
  if(key==='ground-trees'&&options.missingGroundKit)throw Error('optional tree kit unavailable')
  return{scene:scenes.get(key)??new THREE.Group()}
 }} as unknown as GLTFLoader
 const mats={ready:async()=>[],get:()=>{throw Error('winter materials must be reused directly')}} as unknown as HeronReachMaterials
 return{loader,mats,bark,leaf,placeholders,requests}
}
const bench:KitPlacement={asset:'BENCH',x:77,y:0,z:60,ry:0,sx:-1}
const lod:KitPlacement={asset:'TREE_PLANE_A_LOD1',x:72,y:0,z:60,ry:0,sx:-1,scale:1.8}

test('optional LOD trees reuse exact winter material objects and scale uniformly while retaining sx mirroring',async()=>{
 const f=kitFixture(),group=await loadHeronReachKits(f.loader,f.mats,[bench,lod],new Set())
 const tree=group.children.filter(o=>o.name.startsWith('TREE_PLANE_A_LOD1/')) as THREE.InstancedMesh[]
 assert.equal(tree.length,2)
 assert.deepEqual(new Set(tree.map(mesh=>mesh.material)),new Set([f.bark,f.leaf]))
 assert(tree.every(mesh=>mesh.material===f.bark||mesh.material===f.leaf),'reuse the original material objects, including their texture owners')
 assert(tree.every(mesh=>!f.placeholders.includes(mesh.material as THREE.MeshStandardMaterial)),'texture-free placeholders never render')
 const expected=new THREE.Matrix4().makeScale(-1.8,1.8,1.8).multiply(new THREE.Matrix4().makeTranslation(.1,.2,.3))
 for(const mesh of tree){
  const actual=new THREE.Matrix4();mesh.getMatrixAt(0,actual)
  assert(actual.determinant()<0,'the original sx mirror survives uniform scaling')
  actual.elements.forEach((value,i)=>assert(Math.abs(value-expected.elements[i])<1e-6))
 }
 const legacy=group.children.find(o=>o.name.startsWith('BENCH/')) as THREE.InstancedMesh
 assert(legacy)
 const matrix=new THREE.Matrix4();legacy.getMatrixAt(0,matrix)
 assert.equal(matrix.elements[0],-1);assert.equal(matrix.elements[5],1);assert.equal(matrix.elements[10],1)
 assert.equal(f.requests.filter(url=>url.endsWith('heron-reach-ground-trees.glb')).length,1)
})

test('the optional tree kit is not requested without LOD placements',async()=>{
 const f=kitFixture(),group=await loadHeronReachKits(f.loader,f.mats,[bench],new Set())
 assert.equal(group.children.length,1)
 assert(!f.requests.some(url=>url.endsWith('heron-reach-ground-trees.glb')))
})

test('missing winter material or optional LOD kit omits the whole new tree and preserves other placements',async t=>{
 t.mock.method(console,'warn',()=>{})
 for(const options of [{missingLeaf:true},{missingGroundKit:true}]){
  const f=kitFixture(options),group=await loadHeronReachKits(f.loader,f.mats,[bench,lod],new Set())
  assert.equal(group.children.length,1,'failed optional trees must not leave a partial or placeholder tree')
  assert(group.children[0].name.startsWith('BENCH/'))
  assert.equal((group.children[0] as THREE.InstancedMesh).count,1)
 }
})

test('ground-plan HTTP, JSON and validation failures return null with a readable fallback warning',async t=>{
 const warn=t.mock.method(console,'warn',()=>{})
 const invalidPlan={version:2,patches:[],plants:[],perimeterTrees:[]}
 const failures=[
  async()=>new Response('not found',{status:404}),
  async()=>new Response('{broken JSON'),
  async()=>new Response(JSON.stringify(invalidPlan)),
  async()=>new Response(JSON.stringify({version:1,patches:[{kind:'soil',x:null,y:0,z:0,outline:[]}],plants:[],perimeterTrees:[]})),
  async()=>{throw new Error('network unavailable')},
 ]
 for(const failure of failures){
  const before=warn.mock.callCount()
  const fetchPlan=(async(url:string)=>{assert.equal(url,'/models/heron-reach/ground-plan.json');return failure()}) as typeof fetch
  assert.equal(await loadHeronGroundPlan(fetchPlan),null)
  assert.equal(warn.mock.callCount(),before+1)
  assert.match(String(warn.mock.calls.at(-1)!.arguments[0]),/Ground plan unavailable.*original planting and grass/)
 }
 const valid={version:1,patches:[],plants:[],perimeterTrees:[],stats:{patches:0,plantTriangles:0,groundTriangleBudget:0,treeTriangles:0,rejected:{}}}
 const before=warn.mock.callCount()
 const loaded=await loadHeronGroundPlan((async()=>new Response(JSON.stringify(valid))) as typeof fetch)
 assert.deepEqual(loaded,valid,'valid optional data remains available to the caller')
 assert.equal(warn.mock.callCount(),before,'successful loads do not report fallback')
})

function groundAssetFixture(hasSoil=true){
 const scene=new THREE.Group(),kits=new THREE.Group()
 const soil=new THREE.MeshStandardMaterial({name:'hr_soil',map:new THREE.Texture()})
 const leaves=new THREE.MeshStandardMaterial({name:'hr_leaf_litter',map:new THREE.Texture(),alphaTest:.5,side:THREE.DoubleSide})
 const sourceLeaf=new THREE.Mesh(new THREE.PlaneGeometry(1,1),leaves);kits.add(sourceLeaf)
 const placeholders:THREE.Material[]=[]
 for(const name of hasSoil?['hr_soil','hr_leaf_litter']:['hr_leaf_litter']){
  const material=new THREE.MeshStandardMaterial({name});placeholders.push(material)
  const mesh=new THREE.Mesh(new THREE.PlaneGeometry(1,1),material);mesh.name=name;scene.add(mesh)
 }
 const mats={get:(name:string)=>{assert.equal(name,'hr_soil');return soil},ready:async()=>[]} as unknown as HeronReachMaterials
 const loader={loadAsync:async(url:string)=>{assert.equal(url,'/models/heron-reach/heron-reach-ground-detail.glb');return{scene}}} as unknown as GLTFLoader
 return{scene,kits,soil,leaves,placeholders,mats,loader}
}

test('ground-art success reports loaded true and reuses the existing soil and leaf material owners',async()=>{
 const f=groundAssetFixture(),disposed=new Set<THREE.Material>()
 for(const material of f.placeholders)material.addEventListener('dispose',()=>disposed.add(material))
 const result=await loadHeronGroundArt(f.loader,f.mats,f.kits)
 assert.equal(result.loaded,true);assert.equal(result.group,f.scene)
 const soil=result.group.getObjectByName('hr_soil') as THREE.Mesh,leaves=result.group.getObjectByName('hr_leaf_litter') as THREE.Mesh
 assert.equal(soil.material,f.soil);assert.equal(leaves.material,f.leaves)
 assert.equal(disposed.size,2,'unused exported placeholders are disposed')
 assert(soil.receiveShadow&&leaves.receiveShadow)
 assert(!soil.castShadow&&!leaves.castShadow)
 assert(leaves.visible,'the existing leaf material keeps cutout detail visible')
})

test('missing ground GLB or missing soil reports loaded false so callers retain the unmasked field',async t=>{
 const warn=t.mock.method(console,'warn',()=>{})
 const f=groundAssetFixture(),missing={loadAsync:async()=>{throw new Error('ground GLB unavailable')}} as unknown as GLTFLoader
 const missingSoil=groundAssetFixture(false)
 for(const [loader,fixture] of [[missing,f],[missingSoil.loader,missingSoil]] as const){
  const result=await loadHeronGroundArt(loader,fixture.mats,fixture.kits)
  assert.equal(result.loaded,false,'failure cannot signal the grass-mask activation gate')
  assert.equal(result.group.children.length,0,'no incomplete replacement is published')
  assert.match(String(warn.mock.calls.at(-1)!.arguments[0]),/Ground detail unavailable.*existing ground and grass/)
  assert.equal((fixture.kits.children[0] as THREE.Mesh).material,fixture.leaves,'existing kit owner survives failure')
 }
 assert.equal(warn.mock.callCount(),2)
})
