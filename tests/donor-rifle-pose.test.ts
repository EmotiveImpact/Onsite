import test from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import * as THREE from 'three'
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js'
import {donorRifle} from '../src/onsite/DonorRifle'

// Decode the shipped geometry, skin weights, inverse bind matrices and sockets.
// Only image decoding is replaced: these are CPU pose checks, not render evidence.
const loader=new GLTFLoader();
loader.register(parser=>({name:'ONSITE_cpu_pose_textures',async beforeRoot(){
 parser.loadTextureImage=async()=>new THREE.Texture();
}}));
const bytes=readFileSync('public/models/onsite-carbine.glb');
const asset=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
assert.equal(asset.animations.length,0,'The shipped rifle must not acquire donor motion clips');

function fixture(tipped=false){
 const vm=donorRifle(asset.scene,new THREE.Texture(),new THREE.Texture());
 const camera=new THREE.PerspectiveCamera(52,1,.025,8),holder=new THREE.Group();
 camera.position.set(7,4,-11);camera.rotation.set(.2,-.7,.03);camera.add(holder);holder.add(vm.root);
 vm.root.position.copy(vm.hip!);vm.root.rotation.z=vm.hipRoll!;
 if(tipped){vm.root.position.set(.09,-.045,-.66);vm.root.rotation.set(.06,.35,-.26,'YXZ')}
 const bones:THREE.Bone[]=[],skins:THREE.SkinnedMesh[]=[];
 vm.root.traverse(o=>{if(o instanceof THREE.Bone)bones.push(o);if(o instanceof THREE.SkinnedMesh)skins.push(o)});
 assert(bones.length>30&&skins.length>0,'Exercise the actual articulated donor rig');
 const phase=(p:number)=>{vm.animatePose!(p);camera.updateMatrixWorld(true)};
 const points=()=>{
  const out=bones.map(b=>b.getWorldPosition(new THREE.Vector3()));
  for(const skin of skins){
   const positions=skin.geometry.getAttribute('position');
   for(let i=0;i<positions.count;i+=Math.max(1,Math.floor(positions.count/128))){
    const v=new THREE.Vector3().fromBufferAttribute(positions,i);
    out.push(skin.applyBoneTransform(i,v).applyMatrix4(skin.matrixWorld));
   }
  }
  return out;
 };
 const world=(name:string)=>vm.root.getObjectByName(name)!.getWorldPosition(new THREE.Vector3());
 return {vm,camera,bones,skins,phase,points,world};
}
const maxMovement=(a:THREE.Vector3[],b:THREE.Vector3[])=>Math.max(...a.map((p,i)=>p.distanceTo(b[i])));

test('actual carbine bones and skinned arms enter and leave reload continuously',()=>{
 const f=fixture();f.phase(-1);const rest=f.points();
 for(const p of [0,1,-1]){
  f.phase(.55);f.phase(p);
  assert(maxMovement(rest,f.points())<1e-8,`Endpoint ${p} must restore the authored arm pose`);
  assert(f.vm.mag!.position.distanceTo(f.vm.magRest!)<1e-10,'Magazine seats at its authored transform');
 }
 for(const p of [.0001,.9999]){
  f.phase(p);
  assert(maxMovement(rest,f.points())<.00005,`No skin or elbow snap near phase ${p}`);
 }
 let previous=rest;
 for(let frame=0;frame<=240;frame++){
  f.phase(frame/240);const current=f.points();
  assert(current.every(p=>p.toArray().every(Number.isFinite)),'Skinned vertices stay finite');
  for(const bone of f.bones)assert(bone.matrixWorld.elements.every(Number.isFinite),bone.name);
  assert(maxMovement(previous,current)<.025,`No >25mm arm jump in one reload sample at ${frame}/240`);
  previous=current;
 }
});

test('support hand stays on the moving magazine through extraction, insertion and seated hold',()=>{
 for(const tipped of [false,true]){
  const f=fixture(tipped);f.phase(-1);const rightRest=f.world('Hand_R');
  for(const p of [.18,.24,.35,.4,.46,.52,.55,.64,.70,.72,.75,.78]){
   f.phase(p);
   assert(f.world('Hand_L').distanceTo(f.world('MagazineGripSocket'))<.001,`Grip slipped at ${p}, tipped=${tipped}`);
   assert(f.world('Hand_R').distanceTo(rightRest)<.001,`Trigger hand slipped at ${p}`);
   assert(f.world('BoneTwist_01L_end').distanceTo(f.world('Hand_L'))<.001,'Forearm and separate wrist branch meet');
   if(p>=.72)assert(f.vm.mag!.position.distanceTo(f.vm.magRest!)<1e-8,'Seat before releasing support hand');
  }
 }
});

test('magazine and charging handle slow into their stops without changing travel or seating',()=>{
 const f=fixture();
 const magazine=(p:number)=>{f.phase(p);return f.vm.mag!.getWorldPosition(new THREE.Vector3())};
 const speed=(p:number)=>magazine(p+.0001).distanceTo(magazine(p-.0001))/.0002;
 const seated=magazine(-1),withdrawn=magazine(.45);
 assert(withdrawn.distanceTo(seated)>.24&&withdrawn.distanceTo(seated)<.27,'Retain complete, bounded magazine withdrawal');
 assert(speed(.399)<speed(.29)*.1,'Decelerate at the withdrawn stop');
 assert(speed(.719)<speed(.62)*.1,'Decelerate into the magazine well');
 const bolt=(p:number)=>{f.phase(p);return f.world('ChargingHandle')};
 const rest=bolt(-1);
 assert(bolt(.84).distanceTo(rest)>.039&&bolt(.84).distanceTo(rest)<.041,'Retain the existing handle travel');
 assert(bolt(.7801).distanceTo(rest)<.000001&&bolt(.8999).distanceTo(rest)<.000001,'Handle enters/leaves motion smoothly');
 assert(bolt(1).distanceTo(rest)<1e-10);
});

test('authored ADS sight alignment survives arbitrary reload seeking and interruption',()=>{
 const f=fixture();
 f.vm.root.position.set(f.vm.ads!.x,f.vm.ads!.y!,f.vm.ads!.z);f.vm.root.rotation.set(0,0,0);
 f.phase(-1);const rest=f.points();
 for(const p of [.55,.2,.86,.46,.999,.01]){f.phase(p);f.phase(-1)}
 assert(maxMovement(rest,f.points())<1e-8,'Interrupted or reverse-seek reload cannot accumulate bone drift');
 const sight=f.world('RearIronSight').project(f.camera);
 assert(Math.hypot(sight.x,sight.y)<.00001,'Keep the existing authored ADS centre');
});
