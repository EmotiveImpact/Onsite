import {test} from 'node:test'
import assert from 'node:assert/strict'
import * as THREE from 'three'
import type {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {buildWorldArt,loadWorldAssetLibrary,worldArtMatrix,worldAssetKits} from '../src/onsite/heronWorldArt'

function root(name:string){
 const root=new THREE.Group();root.name=name
 const mesh=new THREE.Mesh(new THREE.BoxGeometry(1,2,1),new THREE.MeshStandardMaterial())
 mesh.position.y=1;root.add(mesh);return root
}
function completeKit(names:readonly string[]){
 const scene=new THREE.Group()
 for(const name of names)scene.add(root(name))
 return scene
}
const fakeLoader=(load:(url:string)=>Promise<{scene:THREE.Group}>)=>({loadAsync:load} as unknown as Pick<GLTFLoader,'loadAsync'>)

test('world assets retain native local bounds despite transformed kit containers',async()=>{
 const scenes=worldAssetKits.map(k=>completeKit(k.roots))
 scenes.forEach(s=>{s.position.set(100,40,-25);s.rotation.y=.7})
 const pot=scenes[1].getObjectByName('WORLD_CLAY_POT')!
 pot.userData.soilSurfaceY=1.8;pot.userData.soilRadius=.4
 scenes[1].getObjectByName('WORLD_FERN_A')!.userData.stemXZ=[.15,-.12]
 scenes[1].getObjectByName('WORLD_FERN_A')!.userData.stemBasalY=.004
 const library=await loadWorldAssetLibrary(fakeLoader(async url=>({scene:scenes[worldAssetKits.findIndex(k=>k.url===url)]})))
 assert.equal(library.size,11)
 const bounds=library.get('WORLD_TRASH_BAG')!.bounds
 for(const [actual,expected]of [...bounds.min,...bounds.max].map((v,i)=>[v,[-.5,0,-.5,.5,2,.5][i]]))assert(Math.abs(actual-expected)<1e-12)
 assert.equal(library.get('WORLD_CLAY_POT')!.soilSurfaceY,1.8)
 assert.equal(library.get('WORLD_CLAY_POT')!.soilRadius,.4)
 assert.deepEqual(library.get('WORLD_FERN_A')!.stemXZ,[.15,-.12])
 assert.equal(library.get('WORLD_FERN_A')!.stemBasalY,.004)
})

test('a failed world kit keeps the independent kit available and exposes no replacement assets',async t=>{
 const warnings:string[]=[];t.mock.method(console,'warn',(...args:unknown[])=>warnings.push(String(args[0])))
 const library=await loadWorldAssetLibrary(fakeLoader(async url=>{
  if(url===worldAssetKits[0].url)throw new Error('network unavailable')
  return {scene:completeKit(worldAssetKits[1].roots)}
 }))
 assert.equal(library.size,5)
 assert(!library.has('WORLD_TRASH_BAG'));assert(library.has('WORLD_FERN_A'))
 assert.equal(warnings.length,1);assert.match(warnings[0],/World dressing kit unavailable/)
})

test('empty or unsupported world roots cannot suppress the original assets',async t=>{
 t.mock.method(console,'warn',()=>{})
 const scenes=worldAssetKits.map(k=>completeKit(k.roots))
 const empty=scenes[0].getObjectByName('WORLD_TRASH_BAG')!;empty.clear()
 const unsupported=scenes[0].getObjectByName('WORLD_BIN_RUST')!.children[0] as THREE.Mesh
 unsupported.material=[new THREE.MeshStandardMaterial()]
 const pot=scenes[1].getObjectByName('WORLD_CLAY_POT')!
 pot.userData.soilSurfaceY=1000;pot.userData.soilRadius=-1
 scenes[1].getObjectByName('WORLD_FERN_A')!.userData.stemXZ=[1e9,0]
 scenes[1].getObjectByName('WORLD_FERN_A')!.userData.stemBasalY=NaN
 const library=await loadWorldAssetLibrary(fakeLoader(async url=>({scene:scenes[worldAssetKits.findIndex(k=>k.url===url)]})))
 assert(!library.has('WORLD_TRASH_BAG'));assert(!library.has('WORLD_BIN_RUST'))
 assert.equal(library.get('WORLD_CLAY_POT')!.soilSurfaceY,undefined)
 assert.equal(library.get('WORLD_CLAY_POT')!.soilRadius,undefined)
 assert.equal(library.get('WORLD_FERN_A')!.stemXZ,undefined)
 assert.equal(library.get('WORLD_FERN_A')!.stemBasalY,undefined)
 assert(library.has('WORLD_AIRCON_RUST'))
})

test('world instances share resources and split spatial tiles and floors without changing placement matrices',async()=>{
 const scenes=worldAssetKits.map(k=>completeKit(k.roots))
 const library=await loadWorldAssetLibrary(fakeLoader(async url=>({scene:scenes[worldAssetKits.findIndex(k=>k.url===url)]})))
 const placements=[
  {asset:'WORLD_TRASH_BAG',x:10,y:0,z:12,ry:Math.PI/2,rx:Math.PI/2,scale:.5},
  {asset:'WORLD_TRASH_BAG',x:12,y:0,z:13,ry:0,scale:.4},
  {asset:'WORLD_TRASH_BAG',x:35,y:0,z:12,ry:0,scale:.5},
  {asset:'WORLD_TRASH_BAG',x:10,y:3,z:12,ry:0,scale:.5},
 ]
 const group=buildWorldArt(library,placements),source=library.get('WORLD_TRASH_BAG')!.primitives[0]
 assert.equal(group.children.length,3);assert.equal(group.userData.placementCount,4)
 const first=group.children[0] as THREE.InstancedMesh,matrix=new THREE.Matrix4()
 assert.equal(first.count,2);first.getMatrixAt(0,matrix)
 const expected=worldArtMatrix(placements[0]).multiply(source.local)
 matrix.elements.forEach((v,i)=>assert(Math.abs(v-expected.elements[i])<1e-6))
 for(const child of group.children){
  const mesh=child as THREE.InstancedMesh
  assert.equal(mesh.geometry,source.geometry);assert.equal(mesh.material,source.material)
  assert(mesh.boundingBox&&!mesh.boundingBox.isEmpty());assert(mesh.boundingSphere)
 }
 assert.equal(buildWorldArt(library,[{...placements[0],scale:NaN},{...placements[0],asset:'absent'}]).children.length,0)
})
