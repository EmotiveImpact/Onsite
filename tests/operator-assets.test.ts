import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
import * as THREE from 'three'
import {createOperatorVisual,setOperatorKit,OperatorAnimator} from '../src/onsite/OperatorVisual'
import {operatorFixture} from './operator-fixture'

async function source(){
 return (await operatorFixture()).scene
}

test('Original Blender operator keeps its metre scale, provenance, skin and bounded cost',async()=>{
 const bytes=readFileSync('public/models/onsite-operator.glb')
 const gltf=JSON.parse(bytes.toString('utf8',20,20+bytes.readUInt32LE(12)))
 const record=JSON.parse(readFileSync('public/models/onsite-operator.json','utf8'))
 assert.equal(createHash('sha256').update(bytes).digest('hex'),record.sha256)
 assert.equal(gltf.images?.length??0,2,'Only the two original embedded cotton maps')
 assert(gltf.images.every((image:any)=>image.bufferView!==undefined&&!image.uri),'All images travel inside the recorded GLB')
 for(const texture of record.textures)assert.equal(createHash('sha256').update(readFileSync(texture.file)).digest('hex'),texture.sha256)
 assert.equal(gltf.animations?.length??0,0,'Motion is original runtime pose logic')
 assert.equal(gltf.skins.length,1)
 assert.equal(gltf.skins[0].joints.length,20)
 assert(record.allVariantTriangles<20000)
 assert(gltf.materials.length<=7)
 const scene=await source(),box=new THREE.Box3().setFromObject(scene)
 assert(Math.abs(box.min.y)<.004,'Sole stays at ground level')
 assert(Math.abs(box.max.y-1.75)<.004,'Hood remains at authored 1.75m')
 for(const name of ['Pelvis','Thigh_L','Shin_L','Foot_L','Chest','Hand_L','MuzzleSocket'])assert(scene.getObjectByName(name),name)
 const {model,muzzle}=createOperatorVisual(scene)
 model.updateMatrixWorld(true)
 const p=muzzle.getWorldPosition(new THREE.Vector3())
 assert(p.z<-.8&&p.y>1.2&&p.y<1.3,'Muzzle points along bot forward -Z at the actual barrel')
})

test('Separate bots have independent bones and kit geometry without duplicating materials',async()=>{
 const src=await source(),a=createOperatorVisual(src),b=createOperatorVisual(src)
 const aBone=a.model.getObjectByName('Shin_L')!,bBone=b.model.getObjectByName('Shin_L')!
 assert.notEqual(aBone,bBone)
 const before=bBone.quaternion.clone()
 const anim=new OperatorAnimator(a.model)
 for(let i=0;i<30;i++)anim.update(1/60,3,1,0,.4,.2,i/60)
 assert(aBone.quaternion.angleTo(before)>.01,'Knee bends at its own joint')
 assert.deepEqual(bBone.quaternion.toArray(),before.toArray(),'Second actor skeleton stays independent')
 setOperatorKit(a.model,{trainers:'high',hood:'down'})
 assert(a.model.getObjectByName('Trainers_high')!.visible)
 assert(!a.model.getObjectByName('Trainers_court')!.visible)
 assert(a.model.getObjectByName('Hood_down')!.visible)
 assert(b.model.getObjectByName('Trainers_court')!.visible)
 assert(b.model.getObjectByName('Hood_up')!.visible)
 const aSkins:THREE.SkinnedMesh[]=[],bSkins:THREE.SkinnedMesh[]=[]
 a.model.traverse(o=>{if(o instanceof THREE.SkinnedMesh)aSkins.push(o)})
 b.model.traverse(o=>{if(o instanceof THREE.SkinnedMesh)bSkins.push(o)})
 assert(aSkins.length>0)
 aSkins.forEach((skin,i)=>{
  assert.equal(skin.material,bSkins[i].material,'Kit selection never mutates shared materials')
  assert.notEqual(skin.skeleton,bSkins[i].skeleton)
  assert(skin.skeleton.bones.includes(aBone as THREE.Bone),'The rendered skin uses this actor\'s animated joints')
  assert(!skin.skeleton.bones.includes(bBone as THREE.Bone))
 })
 anim.die(0,0,false)
 for(let i=0;i<60;i++)anim.update(1/60,0,0,0,0,0,0)
 assert(a.model.getObjectByName('Root')!.quaternion.angleTo(b.model.getObjectByName('Root')!.quaternion)>1)
 anim.reset()
 assert.deepEqual(aBone.quaternion.toArray(),before.toArray(),'Reset restores the authored pose')
})

test('Rifle socket follows the held weapon through aim and recoil without moving its actor',async()=>{
 const src=await source(),{model,muzzle}=createOperatorVisual(src),anim=new OperatorAnimator(model)
 const origin=model.position.clone(),start=muzzle.getWorldPosition(new THREE.Vector3())
 anim.fire();anim.update(1/60,0,0,0,.3,.3,0);model.updateMatrixWorld(true)
 const aimed=muzzle.getWorldPosition(new THREE.Vector3())
 assert(aimed.distanceTo(start)>.04)
 assert.deepEqual(model.position.toArray(),origin.toArray())
 const weapon=model.getObjectByName('Weapon')!,relative=weapon.worldToLocal(aimed.clone())
 anim.update(1/60,0,0,0,-.3,-.3,.1);model.updateMatrixWorld(true)
 assert(weapon.worldToLocal(muzzle.getWorldPosition(new THREE.Vector3())).distanceTo(relative)<1e-5)
})
